#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2019/10/21
# @Author : xulh
# @File : NcData.py

import numpy as np
import Nio
import xarray as xr

from com.nriet.algorithm.common.inputData.InputDataComponent import InputDataComponent
from com.nriet.utils.decorator.TimerDecorator import timer_with_param
from com.nriet.utils.fileUtils import convert_data
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.utils.GridDataUtils import GridDataUtils
from com.nriet.config.ResponseCodeAndMsgEum import DATA_OUT_OF_SCALE_CODE,DATA_OUT_OF_SCALE_MSG,FILE_NOT_FOUND_ERROR_CODE

class NcData(InputDataComponent):

    def __init__(self, sub_local_params, algorithm_input_data):
        """
        :param sub_local_params:流程参数，算法运算返回结果
        :param algorithm_input_data:流程数据
        """
        # 初始化获取格点数据的工具类
        self.gdUtils = GridDataUtils()
        # 数据路径
        self.dataInputPaths = sub_local_params.get("dataInputPaths")
        # 数据文件名
        self.dataInputName = sub_local_params.get("dataInputName")
        # 气候态数据
        self.ltmDataInputPaths = sub_local_params.get("ltmDataInputPaths")
        # 数据计算时间范围
        self.timeRanges = sub_local_params.get("timeRanges")
        # 数据计算时间类型
        self.timeTypes = sub_local_params.get("timeType")
        # 数据要素
        self.elements = sub_local_params["elements"]
        self.level = sub_local_params.get("levels")
        self.regions = sub_local_params.get("regions")
        # 单位转化 （转化方式_转化值）
        self.unit_convert = sub_local_params.get("unitConvert")
        # 气候态
        self.ltm = sub_local_params.get("ltm")
        self.output_data = None

    # 获取nc数据
    @timer_with_param("          get Nc file")
    def execute(self):
        outputData = {}
        data_list = []
        startTime, endTime = [str(time) for time in self.timeRanges]
        # 获取实况
        if self.dataInputPaths :
            grid_mean_data = self.gdUtils.get_grid_mean_data(self.dataInputPaths,self.timeTypes,startTime,endTime,self.elements,self.regions,self.level)
            # 无数据时抛异常
            if grid_mean_data is None:
                raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE, response_msg=DATA_OUT_OF_SCALE_MSG)
            # 单位处理
            if self.unit_convert:
                convert_type, convert_value = self.unit_convert.split("_")
                grid_mean_data = convert_data(grid_mean_data, convert_type, convert_value)
            data_list.append(grid_mean_data)
        # 获取常年值
        if self.ltmDataInputPaths:
            #设置默认常年值
            if self.ltm is None or self.ltm=="":
                self.ltm = "1981-2010"
            grid_ltm_data = self.gdUtils.get_grid_ltm_data(self.ltmDataInputPaths, self.timeTypes, startTime, endTime,  self.elements, self.regions, self.level,self.ltm)
            # 无数据时抛异常
            if grid_ltm_data is None:
                error_str = "file ["+self.ltmDataInputPaths + self.timeTypes +"_"+self.ltm+".nc] not exist!"
                raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
            # 单位处理
            if self.unit_convert:
                convert_type, convert_value = self.unit_convert.split("_")
                grid_ltm_data = convert_data(grid_ltm_data, convert_type, convert_value)
            data_list.append(grid_ltm_data)
        outputData["outputData"] = data_list
        self.output_data = outputData
