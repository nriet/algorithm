# -*- coding:utf-8 -*-
# @Time : 2022/01/05
# @Author : huxin
# @File : ObsUtils.py
'''
此脚本用于读写OBS资源，兼容新老方式（OBS库和Boto3库）
'''
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
from com.nriet.utils.obs.DataLakeObsUtils import DataLakeObsUtils
from com.nriet.utils.obs.HuaweiObsUtils import HuaweiObsUtils

class ObsUtils:
    def __init__(self):
        data_lake_switch = look_for_single_global_config('SAVE_TO_OBS_BY_DATA_LAKE_SWITCH')
        if data_lake_switch =='1':
            self.__implement = DataLakeObsUtils()
        else:
            self.__implement = HuaweiObsUtils()

    def get_implement(self):
        return self.__implement

    def __create_client(self):
        pass

    def upload_file(self,bucket_name: str, object_name: str, content: bytes = None, expire: int = None):
        return self.__implement.upload_file(bucket_name,object_name,content,expire)

    def download_file(self,bucket_name: str, object_name: str, load_stream_in_memory: bool = True):
        return self.__implement.download_file(bucket_name,object_name)

    def delete_file(self):
        pass

    def img_save_to_obs(self,im, output_img_name, output_img_type,expire: int = None):
        return self.__implement.img_save_to_obs(im, output_img_name, output_img_type,expire)

    def upload_imgs_by_dir(self,dir_name,image_type='png'):
        return self.__implement.upload_imgs_by_dir(dir_name,image_type)

    def check_object_exist(self,bucket_name: str, object_name: str):
        return self.__implement.check_object_exist(bucket_name,object_name)