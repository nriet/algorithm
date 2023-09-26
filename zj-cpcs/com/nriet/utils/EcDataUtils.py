#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/03/09
# @Author : shiys
# @File : EcDataUtils.py


import numpy as np
import os
import xarray as xr
from com.nriet.utils import  DateUtils
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import FILE_NOT_FOUND_ERROR_CODE,PARAMETER_VALUE_ERROR_CODE
import logging

class EcDataUtils:
    """获取EC模式数据工具类
     根据传入的站点文件的路径、时间尺度、时间访问、要素、站号等实时获取出相关的站点数据
    """
    def get_ec_mean_data(dataInPutPathFore, forecastTime, startTime, endTime, var, startLat, endLat, startLon, endLon, whetherMakeup):
        # 获取模式预报的起止时间
        foreStartTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 1)
        foreEndTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 45)
        # 获取模式预报起止时间内所有预报时间
        time_list = DateUtils.get_time_list([foreStartTime, foreEndTime], "day")
        if whetherMakeup == "False":
            if startTime not in time_list:
                error_str = "Parameter startTime: %s is not in the actual forecastPeriod [ %s ,  %s ] " % ( startTime, foreStartTime, foreEndTime)
                raise AlgorithmException(response_code=PARAMETER_VALUE_ERROR_CODE, response_msg=error_str)
            if endTime not in time_list:
                error_str = "Parameter endTime: %s is not in the actual forecastPeriod [ %s ,  %s ] " % (endTime,foreStartTime,foreEndTime)
                raise AlgorithmException(response_code=PARAMETER_VALUE_ERROR_CODE, response_msg=error_str)
        # 补全数据为真且预测的起止时间都不在数据的预报时段内，需抛出异常
        if whetherMakeup == "True" and startTime not in time_list and endTime not in time_list:
            error_str = "Parameter startTime: %s and endTime: %s is not in the actual forecastPeriod [ %s ,  %s ] " % (
            startTime, endTime, foreStartTime, foreEndTime)
            raise AlgorithmException(response_code=PARAMETER_VALUE_ERROR_CODE, response_msg=error_str)
        # 计算需要获得的预报数据的起止下标
        startIndex = 0
        if startTime in time_list:
            startIndex = time_list.index(startTime)
        endIndex = 44
        if endTime in time_list:
            endIndex = time_list.index(endTime)
        # 根据起报时间替换数据路径里的占位符
        # 替换路径里的时间占位符 "#YYYY#  #MM# #DD#"
        dataInPutPathFore_y = dataInPutPathFore.replace("#YYYY#", forecastTime[0:4]).replace("#MM#", forecastTime[4:6]).replace("#DD#", forecastTime[6:])
        #替换文件名中的起报时间
        dataInputForeFile = dataInPutPathFore_y.replace("#YYYYMMDD#", forecastTime)
        # 获取四个时次的数据
        want_times = time_list[startIndex:endIndex+1]
        resdata = []
        dim = 'time'
        for tt in want_times:
            dataInputForeFile_md = dataInputForeFile.replace("#MMDD#", tt[4:])
            if not os.path.isfile(dataInputForeFile_md):
                continue
            # logging.info(dataInputForeFile_md)
            ds = xr.open_dataset(dataInputForeFile_md)
            if "ensemble" in ds.dims:
                ds = ds.rename({"ensemble":"ens"})
            lat = ds.lat
            lon = ds.lon
            tmpdata = ds[var]
            # 截取指定区域范围的数据
            lon_range = lon[(lon >= startLon) & (lon <= endLon)]
            lat_range = lat[(lat >= startLat) & (lat <= endLat)]
            tmpdata = tmpdata.sel(lon=lon_range, lat=lat_range)
            # 将数组扩维，并设置维度信息
            newdata = tmpdata.expand_dims(dim,1)
            newdata[dim] = [tt]
            # newdata["ensemble"].name = "ens"
            # logging.info(newdata)
            # exit()
            resdata.append(newdata)
        if len(resdata) == 0:
            error_str = " %s Nc file not found ! forecastTime: %s" % (dataInPutPathFore,forecastTime)
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 将时间维合并
        ecData = xr.concat(resdata, dim=dim)
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "day")
            data_time_list = ecData.time.values
            # 筛选超出预报范围的时间
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            want_dims = ecData.dims
            shape = list(ecData.shape)
            want_coords = []
            for ii, dm in enumerate(want_dims):
                if dm == "time":
                    shape[ii] = len(diff_time_list)
                    want_coords.append(diff_time_list)
                else:
                    want_coords.append(ecData[dm])
            nan_data = np.full(shape, np.nan)
            makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
            ecData = xr.concat([ecData, makeup_data], dim='time')
            # 将合并后的数据按时间进行排序，重新整合数据
            b = sorted(enumerate(ecData.time.values), key=lambda x: x[1])
            time_index = [x[0] for x in b]
            ecData = ecData.isel(time=time_index)
        return ecData

    # 获取模式的预测气候态数据
    def get_ec_ltm_data(dataInPutPathFore, forecastTime, startTime, endTime, var, startLat, endLat, startLon, endLon, whetherMakeup):
        # 根据起报时间替换数据路径里的占位符
        # 替换路径里的时间占位符 "#YYYY#  #MM# #DD#"
        dataInPutPathFore_y = dataInPutPathFore.replace("#YYYY#", forecastTime[0:4]).replace("#MM#", forecastTime[4:6]).replace("#DD#", forecastTime[6:])
        # 替换文件名中的起报时间
        dataInputForeFile = dataInPutPathFore_y.replace("#YYYYMMDD#", forecastTime)
        # logging.info(dataInputForeFile)
        # 获取需要获取的预报时段
        want_times = DateUtils.get_time_list([startTime, endTime], "day")
        resdata = []
        dim = 'time'
        for tt in want_times:
            dataInputForeFile_md = dataInputForeFile.replace("#MMDD#", tt[4:])
            # logging.info(dataInputForeFile_md)
            if os.path.isfile(dataInputForeFile_md):
                ds = xr.open_dataset(dataInputForeFile_md)
                lat = ds.lat
                lon = ds.lon
                tmpdata = ds[var]
                # 截取指定区域范围的数据
                lon_range = lon[(lon >= startLon) & (lon <= endLon)]
                lat_range = lat[(lat >= startLat) & (lat <= endLat)]
                tmpdata = tmpdata.sel(lon=lon_range, lat=lat_range)
                # 将数组扩维，并设置维度信息
                newdata = tmpdata.expand_dims(dim, 0)
                newdata[dim] = [tt]
                resdata.append(newdata)
        if len(resdata)==0:
            error_str = " %s Nc file not found ! forecastTime: %s" % (dataInPutPathFore, forecastTime)
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 将时间维合并
        ec_ltm_data = xr.concat(resdata, dim=dim)
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "day")
            data_time_list = ec_ltm_data.time.values
            # 筛选超出预报范围的时间
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            want_dims = ec_ltm_data.dims
            shape = list(ec_ltm_data.shape)
            want_coords = []
            for ii, dm in enumerate(want_dims):
                if dm == "time":
                    shape[ii] = len(diff_time_list)
                    want_coords.append(diff_time_list)
                else:
                    want_coords.append(ec_ltm_data[dm])
            nan_data = np.full(shape, np.nan)
            makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
            ec_ltm_data = xr.concat([ec_ltm_data, makeup_data], dim='time')

        # 将合并后的数据按时间进行排序，重新整合数据
        b = sorted(enumerate(ec_ltm_data.time.values), key=lambda x: x[1])
        time_index = [x[0] for x in b]
        ec_ltm_data = ec_ltm_data.isel(time=time_index)
        # 增加样本维
        ec_ltm_data = ec_ltm_data.expand_dims({"ens": range(1, 52)}, 0)
        return ec_ltm_data

