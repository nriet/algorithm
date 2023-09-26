#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/02/09
# @Author : xulh
# @File : StatisticsDataOutput.py
import os,logging
from com.nriet.algorithm.common.outputData.OutputDataComponent import OutputDataComponent
import numpy as np
import xarray as xr
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import PARAMETER_VALUE_MISSING_CODE
from com.nriet.utils.obs.ObsUtils import ObsUtils
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config



class StatisticsDataOutput(OutputDataComponent):

    def __init__(self, sub_local_params, algorithm_input_data):
        """
        :param sub_local_params:流程参数，算法运算返回结果
        :param algorithm_input_data:流程数据
        """
        logging.info("          StatisticsDataOutput init method")
        self.filePath = sub_local_params.get("outPutPath")
        self.fileName = sub_local_params.get("outPutName")
        self.expire = sub_local_params.get("expire")

        input_data_proc_flag = sub_local_params.get("input_data_proc_flag", False)
        if input_data_proc_flag:
            algorithm_input_data = algorithm_input_data[0]
        self.data = algorithm_input_data
        self.data_dims = sub_local_params.get("data_dims")
        self.output_data = None
        self.saveToObs = sub_local_params.get("saveToObs")
        self.saveToNfsshare = sub_local_params.get("saveToNfsshare")
        # self.data = [input_data["outputData"] for input_data in algorithm_input_data]
        # self.dims = algorithm_input_data[0]["ncData"]["dims"]

    def execute(self):
        logging.info("          StatisticsDataOutput execute method")
        # dims = self.data[0]["outputData"].dims
        #logging.info(self.filePath)
        save_to_nfsshare_switch = look_for_single_global_config("SAVE_TO_NFSSHARE_SWITCH")
        save_to_obs_switch = look_for_single_global_config("SAVE_TO_OBS_SWITCH")
        output_data = {}

        if int(save_to_nfsshare_switch) or int(self.saveToNfsshare):
            if not os.path.isdir(self.filePath):
                os.makedirs(self.filePath)
        encoding = {}
        for i, data_dim in enumerate(self.data_dims):
            if isinstance(data_dim, list):
                for j, dim in enumerate(data_dim):
                    output_data[dim] = self.data[i][j]["outputData"]
                    encoding[dim] = {'dtype': 'float32', '_FillValue': 999999.0}
                    #ncFile.createDimension(dim, len(self.data[i][j]["outputData"]))
                    #ncFile.createVariable(dim, np.double, dims)
            else:
                output_data[data_dim] = self.data[i]["outputData"]
                encoding[data_dim] = {'dtype': 'float32', '_FillValue': 999999.0}
                # ncFile.createDimension(data_dim, len(self.data[i]["outputData"]))
                # ncFile.createVariable(data_dim, np.double, dims)

        data_set = xr.Dataset(output_data)
        if "time" in data_set.dims:
            data_set.time.values = np.asarray(data_set.time.values,dtype=np.int8)
        if "lat" in data_set.dims:
            encoding['lat'] = {'dtype': 'float32'}
        if "lon" in data_set.dims:
            encoding['lon'] = {'dtype': 'float32'}
        # 生成nc文件

        #缺测判断
        is_all_missing_value = True
        for key,value in output_data.items():
          if not np.isnan(np.nanmean(value.values)):
              is_all_missing_value = False
              break

        if is_all_missing_value:
            raise AlgorithmException(response_code=PARAMETER_VALUE_MISSING_CODE, response_msg='All Missing Values')

        # 是否上传nfsshare

        if int(save_to_nfsshare_switch) or self.saveToNfsshare: #saveToNfsshare优先级高
            data_set.to_netcdf(self.filePath + self.fileName, encoding=encoding)
        # 是否上传至obs
        if int(save_to_obs_switch) or self.saveToObs: # saveToNfsshare优先级高
            obs_bucket_name = look_for_single_global_config("OBS_BUCKET_NAME")
            bytes_data = data_set.to_netcdf(format='NETCDF3_CLASSIC', encoding=encoding)
            storage_result = ObsUtils().upload_file(obs_bucket_name, self.fileName, bytes_data,self.expire)

        self.output_data = self.data

        # return storage_result

