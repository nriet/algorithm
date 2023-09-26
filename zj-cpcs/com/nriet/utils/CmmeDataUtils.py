#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/03/09
# @Author : shiys
# @File : DerfDataUtils.py
import os

import numpy as np
import xarray as xr
import pandas as pd
from com.nriet.utils import DateUtils
import re

# Derf2.0模式数据获取
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import FILE_NOT_FOUND_ERROR_CODE,PARAMETER_VALUE_ERROR_CODE

class CmmeDataUtils:
    # 获取模式的预测实况数据
    def get_cmme_mean_data(dataInPutPathFore, forecastTime, startTime, endTime, var, startLat, endLat, startLon, endLon, dataSource,level, whetherMakeup):
        # 替换文件中起报时间的占位符 "#YYYYMM#"
        dataInputForeFile = dataInPutPathFore.replace("#YYYYMM#", forecastTime)
        print(dataInputForeFile)
        if not os.path.isfile(dataInputForeFile):
            error_str = " %s Nc file not found !" % dataInputForeFile
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        #FGOALSF
        if dataSource in ["FGOALSF", "FGOALSS2", "PCCSM4", "CMMEV2"]:
            fStartMon = 1
            fEndMon = 6
        foreStartTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), fStartMon)
        foreEndTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), fEndMon)
        # 获取模式预报起止时间内所有预报时间
        time_list = DateUtils.get_time_list([foreStartTime, foreEndTime], "mon")
        if whetherMakeup == "False":
            if startTime not in time_list:
                error_str = "Parameter startTime: %s is not in the actual forecastPeriod [ %s ,  %s ] " % (startTime,foreStartTime,foreEndTime)
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
        startIndex = 1
        if startTime in time_list:
            startIndex = time_list.index(startTime)
        if dataSource in ["FGOALSF", "FGOALSS2", "PCCSM4", "CMMEV2"]:
            endIndex = 6
        if endTime in time_list:
            endIndex = time_list.index(endTime)
        ds = xr.open_dataset(dataInputForeFile, decode_times=False)
        # print(ds)
        lat = ds.lat
        lon = ds.lon
        tmpdata = ds[var]
        # 位势高度数据特殊处理
        if dataSource in [ "FGOALSS2", "PCCSM4"] and "lev" in ds.dims:
            lev = ds.lev
            lev_range = lev[(lev >= float(level)) & (lev <= float(level))]
            tmpdata = tmpdata.sel(lev=lev_range)
            tmpdata = tmpdata.mean(dim=["lev"])
        # 截取指定区域范围的数据
        lon_range = lon[(lon >= startLon) & (lon <= endLon)]
        lat_range = lat[(lat >= startLat) & (lat <= endLat)]
        tmpdata = tmpdata.sel(lon=lon_range, lat=lat_range)
        # print(tmpdata)
        cmmedata = tmpdata[startIndex:endIndex+1]
        # 重置时间维信息
        cmmedata['time'] = time_list[startIndex:endIndex+1]
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "mon")
            data_time_list = cmmedata.time.values
            # 筛选超出预报范围的时间
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            want_dims = cmmedata.dims
            shape = list(cmmedata.shape)
            want_coords = []
            for ii, dm in enumerate(want_dims):
                if dm == "time":
                    shape[ii] = len(diff_time_list)
                    want_coords.append(diff_time_list)
                else:
                    want_coords.append(cmmedata[dm])
            nan_data = np.full(shape, np.nan)
            makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
            cmmedata = xr.concat([cmmedata, makeup_data], dim='time')
            # 将合并后的数据按时间进行排序，重新整合数据
            b = sorted(enumerate(cmmedata.time.values), key=lambda x: x[1])
            time_index = [x[0] for x in b]
            cmmedata = cmmedata.isel(time=time_index)
        return cmmedata

    # 获取模式的预测气候态数据
    def get_cmme_ltm_data(dataInPutPathFore, forecastTime, startTime, endTime, var, startLat, endLat, startLon, endLon, dataSource,level, whetherMakeup):
        # 替换文件中起报月的占位符 "#MM#"
        if dataSource == "CMMEV2":
            dataInputForeFile = dataInPutPathFore.replace("#MM#", str(int(forecastTime[4:6])))
        else:
            dataInputForeFile = dataInPutPathFore.replace("#MM#", forecastTime[4:6])
        print(dataInputForeFile)
        if not os.path.isfile(dataInputForeFile):
            error_str = " %s Nc file not found !" % dataInputForeFile
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        #FGOALSF
        if dataSource in ["FGOALSF", "FGOALSS2", "PCCSM4", "CMMEV2"]:
            fStartMon = 1
            fEndMon = 6
        foreStartTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), fStartMon)
        foreEndTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), fEndMon)
        # 获取模式预报起止时间内所有预报时间
        time_list = DateUtils.get_time_list([foreStartTime, foreEndTime], "mon")
        if whetherMakeup == "False":
            if startTime not in time_list:
                error_str = "Parameter startTime: %s is not in the actual forecastPeriod [ %s ,  %s ] " % (startTime,foreStartTime,foreEndTime)
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
        startIndex = 1
        if startTime in time_list:
            startIndex = time_list.index(startTime)
        if dataSource in ["FGOALSF", "FGOALSS2", "PCCSM4", "CMMEV2"]:
            endIndex = 6
        if endTime in time_list:
            endIndex = time_list.index(endTime)
        ds = xr.open_dataset(dataInputForeFile, decode_times=False)
        # print(ds)
        lat = ds.lat
        lon = ds.lon
        tmpdata = ds[var]
        # 位势高度数据特殊处理
        if dataSource in [ "FGOALSS2", "PCCSM4"] and "lev" in ds.dims:
            lev = ds.lev
            lev_range = lev[(lev >= float(level)) & (lev <= float(level))]
            tmpdata = tmpdata.sel(lev=lev_range)
            tmpdata = tmpdata.mean(dim=["lev"])
        # 截取指定区域范围的数据
        lon_range = lon[(lon >= startLon) & (lon <= endLon)]
        lat_range = lat[(lat >= startLat) & (lat <= endLat)]
        tmpdata = tmpdata.sel(lon=lon_range, lat=lat_range)
        # print(tmpdata)
        cmmedata = tmpdata[startIndex:endIndex+1]
        # 重置时间维信息
        cmmedata['time'] = time_list[startIndex:endIndex+1]
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "mon")
            data_time_list = cmmedata.time.values
            # 筛选超出预报范围的时间
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            want_dims = cmmedata.dims
            shape = list(cmmedata.shape)
            want_coords = []
            for ii, dm in enumerate(want_dims):
                if dm == "time":
                    shape[ii] = len(diff_time_list)
                    want_coords.append(diff_time_list)
                else:
                    want_coords.append(cmmedata[dm])
            nan_data = np.full(shape, np.nan)
            makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
            cmmedata = xr.concat([cmmedata, makeup_data], dim='time')
            # 将合并后的数据按时间进行排序，重新整合数据
            b = sorted(enumerate(cmmedata.time.values), key=lambda x: x[1])
            time_index = [x[0] for x in b]
            cmmedata = cmmedata.isel(time=time_index)
        return cmmedata

    # # dataSource = "FGOALSF"
    # # dataInputPath = '/nfsshare1/cdbdata/ftpdata/CMME/FGOALS-f/fcst/PSL.anom.mon.fcst.6m.from.#YYYYMM#20.FGOALS-f.nc'
    # # dataSource = "FGOALSS2"
    # # dataInputPath = '/nfsshare1/cdbdata/ftpdata/CMME/FGOALS-s2/fcst/PSL.anom.mon.fcst.6m.#YYYYMM#20.FGOALS-s2.nc'
    # dataSource = "PCCSM4"
    # dataInputPath = '/nfsshare1/cdbdata/ftpdata/CMME/PCCSM4/fcst/PSL.anom.mon.fcst.6m.#YYYYMM#20.PCCSM4.nc'
    # foreTime = '202203'
    # stime = '202204'
    # etime = '202206'
    # var = 'PSL'
    # startLat = 0
    # endLat = 60
    # startLon = 70
    # endLon = 140
    # xdata = get_cmme_mean_data(dataInputPath, foreTime, stime, etime, var, startLat, endLat, startLon, endLon,dataSource,"True")
    # print(xdata)