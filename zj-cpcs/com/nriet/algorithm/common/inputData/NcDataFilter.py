#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2019/10/21
# @Author : xulh
# @File : NcDataFilter.py

import numpy as np
import logging
import xarray as xr

from com.nriet.algorithm.common.inputData.InputDataComponent import InputDataComponent
from com.nriet.utils.decorator.TimerDecorator import timer_with_param
from com.nriet.utils.fileUtils import convert_data
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.utils.GridDataUtils import GridDataUtils


class NcDataFilter(InputDataComponent):

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
        # 需要掩盖的经纬度范围
        self.latRanges = sub_local_params.get("latRanges")
        self.lonRanges = sub_local_params.get("lonRanges")
        logging.info(self.regions)
        logging.info(self.latRanges)
        logging.info(self.lonRanges)
        
        # 单位转化 （转化方式_转化值）
        self.unit_convert = sub_local_params.get("unitConvert")
        self.output_data = None
    
    def maskdata(self, data):
        start_lat, end_lat = [float(lat1) for lat1 in self.latRanges]
        start_lon, end_lon = [float(lon1) for lon1 in self.lonRanges]
        lon = data["lon"]
        lat = data["lat"]
        mask_lon = lon[(lon >= start_lon) & (lon <= end_lon)]
        mask_lat = lat[(lat >= start_lat) & (lat <= end_lat)]
        logging.info(len(mask_lat),len(lat))
      
        if len(mask_lat) != len(lat) and len(mask_lon) == len(lon):
            diff_lat = list(set(lat.values).difference(set(mask_lat.values)))
            diff_data = data.sel(lat=diff_lat)
            mask_data = data.sel(lat=mask_lat)
            mask_data.values = np.where(np.isnan(mask_data),mask_data.values,np.nan)
            res_data = xr.concat([diff_data, mask_data], dim="lat")
            sort_lat = res_data.lat.values
            # 将合并后的数据按纬度进行排序，重新整合数据
            b = sorted(enumerate(sort_lat), key=lambda x: x[1])
            lat_index = [x[0] for x in b]
            res_data = res_data.isel(lat=lat_index)
        if len(mask_lat) == len(lat) and len(mask_lon) != len(lon):
            diff_lon = list(set(lon.values).difference(set(mask_lon.values)))
            diff_data = data.sel(lon=diff_lon)
            mask_data = data.sel(lon=mask_lon)
            mask_data.values = np.where(np.isnan(mask_data),mask_data.values,np.nan)
            res_data = xr.concat([diff_data, mask_data], dim="lon")
            sort_lon = res_data.lon.values
            # 将合并后的数据按经度进行排序，重新整合数据
            b = sorted(enumerate(sort_lon), key=lambda x: x[1])
            lon_index = [x[0] for x in b]
            res_data = res_data.isel(lon=lon_index)
        logging.info(res_data)
        return res_data
        
    # 获取nc数据
    @timer_with_param("          get Nc file")
    def execute(self):
        outputData = {}
        data_list = []
        startTime, endTime = [str(time) for time in self.timeRanges]
        # 获取实况
        if self.dataInputPaths :
            logging.info(self.level)
            grid_mean_data = self.gdUtils.get_grid_mean_data(self.dataInputPaths,self.timeTypes,startTime,endTime,self.elements,self.regions,self.level)
            # 无数据时抛异常
            if grid_mean_data is None:
                error_str = "data out of range!"
                raise AlgorithmException(response_code='9800', response_msg=error_str)
            # 单位处理
            if self.unit_convert:
                convert_type, convert_value = self.unit_convert.split("_")
                grid_mean_data = convert_data(grid_mean_data, convert_type, convert_value)
            grid_mean_data = self.maskdata(grid_mean_data)
            data_list.append(grid_mean_data)
        # 获取常年值
        if self.ltmDataInputPaths:
            grid_ltm_data = self.gdUtils.get_grid_ltm_data(self.ltmDataInputPaths, self.timeTypes, startTime, endTime,  self.elements, self.regions, self.level,"1981-2010")
            # 无数据时抛异常
            if grid_ltm_data is None:
                error_str = "file ["+self.ltmDataInputPaths + self.timeTypes +"_1981-2010.nc] not exist!"
                raise AlgorithmException(response_code='9800', response_msg=error_str)
            # 单位处理
            if self.unit_convert:
                convert_type, convert_value = self.unit_convert.split("_")
                grid_ltm_data = convert_data(grid_ltm_data, convert_type, convert_value)
            grid_ltm_data = self.maskdata(grid_ltm_data)
            data_list.append(grid_ltm_data)
        outputData["outputData"] = data_list
        self.output_data = outputData
