# -*- coding:utf-8 -*-
# @Time : 2022/01/05
# @Author : huxin
# @File : DataLakeObsUtils.py
'''
此脚本用于以数据湖s3接口标准访问obs资源。
'''
import boto3,urllib3
from botocore.client import Config
from botocore.exceptions import ClientError
import logging
import xarray as xr
from PIL import Image
import io,os
from datetime import datetime,timedelta
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from com.nriet.utils.result.ResponseResultUtils import build_response_dict
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config,look_for_obs_connection_config


class DataLakeObsUtils:

    def __create_client(self):
        """
        创建datalake客户端实例
        :return: datalake客户端实例
        """
        # 创建data_lake_client实例
        obs_conn_dict = look_for_obs_connection_config()
        data_lake_client = boto3.client('s3',use_ssl=True,verify=False,
            aws_access_key_id=obs_conn_dict.get('obs_ak'),
            aws_secret_access_key=obs_conn_dict.get('obs_sk'),
            endpoint_url=''.join(["https://",obs_conn_dict.get('obs_endpoint')]),
            config=Config(signature_version='s3')
        )
        return data_lake_client

    def upload_file(self,bucket_name: str, object_name: str, content: bytes = None, expire: int = None,authority: str = 'public-read-write',contentType :str ='application/octet-stream'):
        '''
        文件上传，此方法目前只支持文件流的方式上传文件。
        :param bucket_name:桶名称
        :param object_name:对象名称：文件夹路径+文件名称（带文件类型）
        :param content:二进制流，务必是bytes类型
        :param expire:文件有效期限，默认1天
        :param authority:对象权限，不再赘述
        :return:返回上传文件结果
        '''
        logging.info("             uploading file to datalake. bucket named %s, file named %s" % (bucket_name, object_name))
        obs_expire = int(expire if expire else look_for_single_global_config("OBS_DEFAULT_EXPIRE"))
        data_lake_client = self.__create_client()
        data_lake_response = data_lake_client.put_object(ACL=authority,
                                 Body=content,
                                 Bucket=bucket_name,
                                 Key=object_name,
                                 Expires=datetime.now() + timedelta(days=obs_expire),
                                 ContentType=contentType
                                 )
        # 构造返回结果
        result_dict = build_response_dict()
        if data_lake_response['ResponseMetadata']['HTTPStatusCode'] < 300:
            logging.info("             uploaded file to datalake success! requestId %s" % data_lake_response['ResponseMetadata']['RequestId'])
            result_dict['requestId'] = data_lake_response['ResponseMetadata']['RequestId']
        else:
            logging.info("             uploaded file to datalake failed! errorCode %s, errorMessage %s" % (data_lake_response['ResponseMetadata']['HTTPStatusCode'], data_lake_response['ResponseMetadata']['HTTPStatusCode']))
            result_dict = build_response_dict(response_dict=result_dict, response_code=data_lake_response['ResponseMetadata']['HTTPStatusCode'],
                                              response_msg=data_lake_response['ResponseMetadata']['HTTPStatusCode'])

        return result_dict

    def download_file(self,bucket_name: str, object_name: str, load_stream_in_memory: bool = True):
        '''
        下载文件，此方法目前暂时只支持二进制下载文件，而非流式下载，以免资源
        :param bucket_name:桶名称
        :param object_name:对象名称：文件夹路径+文件名称（带文件类型）
        :param load_stream_in_memory:
            设置loadStreamInMemory 参数为True进行二进制式下载，对象的内容将被包含在返回结果中的body.buffer字段。
            设置loadStreamInMemory 参数为False进行流式下载，返回结果中的body.response字段是一个可读流，通过该可读流可将对象的内容读取到本地文件或者内存中。
            body.response获取的可读流一定要显式关闭，否则会造成资源泄露。
        :return: 返回下载文件（内存形式）
        '''
        logging.info("downloading file from datalake. bucket named %s, file named %s" % (bucket_name, object_name))

        # 1.下载数据
        data_lake_client = self.__create_client()
        data_lake_response = data_lake_client.get_object(Bucket=bucket_name, Key=object_name)

        # 2.构造返回结果
        result_dict = build_response_dict()
        if data_lake_response['ResponseMetadata']['HTTPStatusCode'] < 300:
            logging.info("downloading file from datalake success! requestId %s,size %s " % (data_lake_response['ResponseMetadata']['RequestId'],data_lake_response['ContentLength']))
            result_dict['requestId'] = data_lake_response['ResponseMetadata']['RequestId']
            result_dict['content'] = data_lake_response['Body']._raw_stream.data
        else:
            logging.info("downloading file from datalake failed! errorCode %s, errorMessage %s" % (data_lake_response['ResponseMetadata']['HTTPStatusCode'], data_lake_response['ResponseMetadata']['HTTPStatusCode']))
            result_dict = build_response_dict(response_dict=result_dict, response_code=data_lake_response['ResponseMetadata']['HTTPStatusCode'],
                                              response_msg=data_lake_response['ResponseMetadata']['HTTPStatusCode'],)

        return result_dict
    def check_object_exist(self,bucket_name: str, object_name: str):
        """
        获取对象的元数据信息
        Args:
            bucket_name: 桶名
            object_name: 对象名

        Returns: OBS元数据信息对象

        """

        data_lake_client = self.__create_client()
        try:
            data_lake_client.head_object(Bucket=bucket_name, Key=object_name)
        except ClientError as e:
            return int(e.response['Error']['Code']) != 404
        return True

    def img_save_to_obs(self,im, output_img_name, output_img_type,expire=None):
        """
        图片保存至obs
        :param im: PIL打开的图片对象Image
        :param output_img_name: 图片名称
        :param output_img_type: 图片类型
        :param expire: 保存期限 不传默认1天
        :return: 保存结果
        """
        # 1.转换成io流，i0流里头拿字节流也就是bytes
        img_byte = io.BytesIO()
        im.save(img_byte, format=output_img_type)
        binary_str2 = img_byte.getvalue()

        # 2.读取配置文件获取桶名
        obs_bucket_name = look_for_single_global_config("OBS_BUCKET_NAME")
        obs_expire = int(look_for_single_global_config("OBS_DEFAULT_EXPIRE") if expire is None else expire)

        # 3.保存至obs
        storage_result = self.upload_file(obs_bucket_name, output_img_name + '.' + output_img_type, binary_str2,obs_expire,contentType='image/png')
        return storage_result

    def upload_imgs_by_dir(self,dir_name,image_type='png'):
        data_lake_client = self.__create_client()

        def is_image_file(filename):
            return any(filename.endswith(extension) for extension in [image_type])

        image_filenames = [''.join([dir_name, x]) for x in os.listdir(dir_name) if is_image_file(x)]

        for image_filename in image_filenames:
            print(" upload image: %s" % image_filename)
            im = Image.open(image_filename)
            img_byte = io.BytesIO()
            im.save(img_byte, format=image_type)
            binary_str2 = img_byte.getvalue()

            resp = data_lake_client.upload_file("cipas", os.path.basename(image_filename), content=binary_str2,expire=180)

        print(" upload image by dir finished!")
        return None
    
if __name__ == '__main__':
    backet_name = "cipas"
    raw_object_name = "/nfsshare1/cdbdata/data/NOAA/olr/day/test1_2020_05.nc"
    object_name = "test20220105.nc"
    xarray_data = xr.open_dataset(raw_object_name)
    bytes_data = xarray_data.to_netcdf()
    utils = DataLakeObsUtils()
    result_dict = utils.upload_file(backet_name, object_name, bytes_data, 1)

    print(111)