# -*- coding:utf-8 -*-
# @Time : 2020/09/01
# @Author : huxin
# @File : huaweiObsUtils.py

from obs import ObsClient
from obs import StorageClass
from obs import HeadPermission
from obs import CreateBucketHeader
from obs import PutObjectHeader
from com.nriet.utils.result.ResponseResultUtils import build_response_dict
import xarray as xr
import io,logging,os
from PIL import Image
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config,look_for_obs_connection_config


class HuaweiObsUtils:

    def __create_client(self):
        """
        创建OBS客户端实例
        :return: OBS客户端实例
        """
        # 创建ObsClient实例
        obs_conn_dict = look_for_obs_connection_config()
        obs_client = ObsClient(
            access_key_id=obs_conn_dict.get('obs_ak'),
            secret_access_key=obs_conn_dict.get('obs_sk'),
            server=obs_conn_dict.get('obs_endpoint')
        )
        return obs_client

    def create_bucket(self,bucket_name: str, authority: str = HeadPermission.PUBLIC_READ_WRITE,
                      store_class: str = StorageClass.STANDARD):
        '''
        创建桶操作.默认权限是公共读写，存储类型为标准存储。
        :param bucket_name:桶名称，全局唯一。
            ● 3～63个字符，数字或字母开头，支持小写字母、数字、“-”、“.”。
            ● 禁止使用类IP地址。
            ● 禁止以“-”或“.”开头及结尾。
            ● 禁止两个“.”相邻（如：“my..bucket”）。
            ● 禁止“.”和“-”相邻（如：“my-.bucket”和“my.-bucket”）
        :param authority:桶权限
            ● PRIVATE = 'private' 桶或对象的所有者拥有完全控制的权限，其他任何人都没有访问权限
            ● PUBLIC_READ = 'public-read' 设在桶上，所有人可以获取该桶内对象列表、桶内多段任务、桶的元数据、桶的多版本。设在对象上，所有人可以获取该对象内容和元数据
            ● PUBLIC_READ_WRITE = 'public-read-write' 设在桶上，所有人可以获取该桶内对象列表、桶内多段任务、桶的元数据、上传对象删除对象、初始化段任务、上传段、合并段、拷贝段、取消多段上传任务。设在对象上，所有人可以获取该对象内容和元数据。
            ● PUBLIC_READ_DELIVERED = 'public-read-delivered' 设在桶上，所有人可以获取该桶内对象列表、桶内多段任务、桶的元数据，可以获取该桶内对象的内容和元数据。 不能应用于对象。
            ● PUBLIC_READ_WRITE_DELIVERED = 'public-read-write-delivered' 设在桶上，所有人可以获取该桶内对象列表、桶内多段任务、桶的元数据、上传对象、删除对象、初始化段任务、上传段、合并段、拷贝段、取消多段上传任务，可以获取该桶内对象的内容和元数据。不能应用于对象。
            ● AUTHENTICATED_READ = 'authenticated-read' 暂不知
            ● BUCKET_OWNER_READ = 'bucket-owner-read' 暂不知
            ● BUCKET_OWNER_FULL_CONTROL = 'bucket-owner-full-control' 暂不知
            ● LOG_DELIVERY_WRITE = 'log-delivery-write' 暂不知
        :param store_class: 存储类型
            ● STANDARD = 'STANDARD' 标准存储 标准存储拥有低访问时延和较高的吞吐量，适用于有大量热点对象（平均一个月多次）或小对象（<1MB），且需要频繁访问数据的业务场景。
            ● WARM = 'WARM' 低频访问存储 低频访问存储适用于不频繁访问（平均一年少于12次）但在需要时也要求能够快速访问数据的业务场景。
            ● COLD = 'COLD' 归档存储 归档存储适用于很少访问（平均一年访问一次）数据的业务场景。
            ● 上传对象时，对象的存储类别默认继承桶的存储类别；
            ● 修改桶的存储类别，桶内已有对象的存储类别不会修改，新上传对象时的默认对象存储类别随之修改。
        :return: 返回创建桶结果
        '''
        logging.info("creating obs bucket named : %s" % bucket_name)

        # 1.设置请求头信息
        header = CreateBucketHeader()
        header.aclControl = authority
        header.storageClass = store_class

        # 2.创建桶
        obsClient = self.__create_client()
        resp = obsClient.createBucket(bucket_name)

        # 3.构造返回结果
        result_dict = build_response_dict()
        if resp.status < 300:
            logging.info("created obs bucket named : %s success! requestId %s" % (bucket_name, resp.requestId))
            result_dict['requestId'] = resp.requestId
        else:
            logging.info("created obs bucket named : %s failed! errorCode %s  errorMessage %s " % (
                bucket_name, resp.errorCode, resp.errorMessage))
            result_dict = build_response_dict(response_dict=result_dict, response_code=resp.errorCode,
                                              response_msg=resp.errorMessage)

        return result_dict


    def delete_bucket(self,bucket_name):
        '''
        删除桶
        :param bucket_name: 桶名
        :return: 返回删除桶结果
        '''
        logging.info("deleting obs bucket named %s" % bucket_name)

        # 1.删除桶操作
        obsClient = self.__create_client()
        resp = obsClient.deleteBucket(bucket_name)

        # 2.构造返回结果
        result_dict = build_response_dict()
        if resp.status < 300:
            logging.info("deleted obs bucket named : %s success! requestId %s" % (bucket_name, resp.requestId))
            result_dict['requestId'] = resp.requestId
        else:
            logging.info("deleted obs bucket named : %s failed! errorCode %s  errorMessage %s " % (
                bucket_name, resp.errorCode, resp.errorMessage))
            result_dict = build_response_dict(response_dict=result_dict, response_code=resp.errorCode,
                                              response_msg=resp.errorMessage)

        return result_dict


    def upload_file(self,bucket_name: str, object_name: str, content: bytes = None, expire: int = None,authority: str = HeadPermission.PUBLIC_READ_WRITE):
        '''
        文件上传，此方法目前只支持文件流的方式上传文件。
        :param bucket_name:桶名称
        :param object_name:对象名称：文件夹路径+文件名称（带文件类型）
        :param content:二进制流，务必是bytes类型
        :param expire:文件有效期限，默认1天
        :param authority:对象权限，不再赘述
        :return:返回上传文件结果
        '''

        logging.info("             uploading file to obs. bucket named %s, file named %s" % (bucket_name, object_name))

        # 1.构造请求头
        headers = PutObjectHeader()


        headers.expires = int(expire if expire else look_for_single_global_config("OBS_DEFAULT_EXPIRE"))
        # 设置对象访问权限为公共读
        headers.acl = authority
        # 2.上传文件
        obsClient = self.__create_client()
        resp = obsClient.putContent(bucket_name, object_name, content=content, headers=headers)

        # 3.构造返回结果
        result_dict = build_response_dict()
        if resp.status < 300:
            logging.info("             uploaded file to obs success! requestId %s" % resp.requestId)
            result_dict['requestId'] = resp.requestId
        else:
            logging.info("             uploaded file to obs failed! errorCode %s, errorMessage %s" % (resp.errorCode, resp.errorMessage))
            result_dict = build_response_dict(response_dict=result_dict, response_code=resp.errorCode,
                                              response_msg=resp.errorMessage)

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

        logging.info("downloading file from obs. bucket named %s, file named %s" % (bucket_name, object_name))

        # 1.下载数据
        obsClient = self.__create_client()
        resp = obsClient.getObject(bucket_name, object_name, loadStreamInMemory = load_stream_in_memory)

        # 2.构造返回结果
        result_dict = build_response_dict()
        if resp.status < 300:
            logging.info("downloading file from obs success! requestId %s,size %s " % (resp.requestId,resp.body.size))
            result_dict['requestId'] = resp.requestId
            result_dict['content'] = resp.body.buffer
        else:
            logging.info("downloading file from obs failed! errorCode %s, errorMessage %s" % (resp.errorCode, resp.errorMessage))
            result_dict = build_response_dict(response_dict=result_dict, response_code=resp.errorCode,
                                              response_msg=resp.errorMessage)

        return result_dict


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
        storage_result = self.upload_file(obs_bucket_name, output_img_name + '.' + output_img_type, binary_str2,obs_expire)
        return storage_result


    def delete_file(self):
        pass

    def check_object_exist(self,bucket_name: str, object_name: str):
        """
        获取对象的元数据信息
        Args:
            bucket_name: 桶名
            object_name: 对象名

        Returns: OBS元数据信息对象

        """
        obsClient = self.__create_client()
        check_resp = obsClient.check_object_exist(bucket_name, object_name)
        if check_resp.status == 200:
            return True
        return False

    def upload_imgs_by_dir(self,dir_name,image_type='png'):
        obsClient = self.__create_client()

        def is_image_file(filename):
            return any(filename.endswith(extension) for extension in [image_type])

        image_filenames = [''.join([dir_name, x]) for x in os.listdir(dir_name) if is_image_file(x)]

        for image_filename in image_filenames:
            print(" upload image: %s" % image_filename)
            im = Image.open(image_filename)
            img_byte = io.BytesIO()
            im.save(img_byte, format=image_type)
            binary_str2 = img_byte.getvalue()

            headers = PutObjectHeader()
            headers.expires = 180
            # 设置对象访问权限为公共读
            headers.acl = HeadPermission.PUBLIC_READ_WRITE
            resp = obsClient.putContent("cipas", os.path.basename(image_filename), content=binary_str2, headers=headers)

        print(" upload image by dir finished!")
        return None
        
if __name__ == '__main__':
    backet_name = "cipas"
    # raw_object_name = "/nfsshare1/cdbdata/data/NOAA/olr/day/test1_2020_05.nc"
    # object_name = "test1_2020_05_2.nc"
    # file_path = "/nfsshare1/cdbdata/data/NOAA/olr/day/test2_2020_05.nc"

    # 1.读取nc文件，转换成Xarray.DataSet对象 ()
    # xarray_data = xr.open_dataset(raw_object_name)
    # content = open(raw_object_name,'rb')
    # result_dict = upload_file(backet_name, object_name, content, 180)

    # 2.保存前.务必转换成bytes类型
    # bytes_data=xarray_data.to_netcdf()

    # 3.调用接口上传文件保存
    # result_dict = self.upload_file(backet_name,object_name,bytes_data,180)

    # 4.调用接口下载文件，数据以bytes类型返回，结果在content属性下
    # result_dict = download_file(backet_name,object_name)
    # return_xarray_data_1 = xr.open_dataset(result_dict['content'])

    # 5.调用原生接口下载文件，并落盘保存
    # obsClient.getObject(backet_name,object_name,downloadPath=file_path)
    # return_xarray_data_2 = xarray_data = xr.open_dataset(file_path)

    # 6. 查看桶权限以及对象权限
    # resp = obsClient.getBucketPolicy("cipas")
    # resp1 = obsClient.getObjectAcl("cipas",object_name)
    #
    # resp2 = obsClient.headBucket("cipas")
    # resp3 = obsClient.listObjects("cipas")
    #
    # resp4 = obsClient.listBuckets(isQueryLocation=True)
    #
    # resp5 =  obsClient.getBucketMetadata('cipas', '10.40.18.27', 'x-obs-header')
    # obsClient =self.__create_client()
    # aaa =obsClient.getObjectMetadata('cipas', 'PREP_CHCC_RSINC_WJS_U200_CFSV2_EASTCH_DAY_0200_PM_20210103.png')

    # upload_imgs_by_dir("/nfsshare/uploadImg/")
    obsUtils = HuaweiObsUtils()
    resp = obsUtils.create_bucket('cipas')

    logging.info(resp)
