#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/02/21
# @Author : Eldan
# @File : StationInfoData.py

from com.nriet.algorithm.business.BusComponent import BusComponent
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import PARAMETER_VALUE_ERROR_CODE
import logging
from com.nriet.utils.fileUtils import file_exists
import pandas as pd
import numpy as np
import xarray as xr

class StationInfoData(BusComponent):
    def __init__(self, sub_local_params, algorithm_input_data):
        """
                :param sub_local_params:流程参数，算法运算返回结果
                :param algorithm_input_data:流程数据
                """
        # 源数据文件的存放路径
        self.txtFilePath = sub_local_params["txtFilePath"]
        self.output_data = None

    def execute(self):
        if not file_exists(self.txtFilePath):
            error_str ="["+self.txtFilePath+"] not found !"
            logging.info(error_str)
            raise AlgorithmException(response_code=PARAMETER_VALUE_ERROR_CODE,response_msg=error_str)
        out_data = {}
        data = pd.read_table(self.txtFilePath, header=None, encoding='utf-8', sep=" ")
        stationInfo = np.array(data)
        locs = ['station', 'lat', 'lon', 'province', 'area']
        stations = stationInfo[:, 0]
        stationInfoData = xr.DataArray(stationInfo, coords=[stations, locs], dims=['station', 'space'])
        out_data["outputData"] = stationInfoData
        self.output_data = out_data
