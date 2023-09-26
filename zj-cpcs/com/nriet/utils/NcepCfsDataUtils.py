#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/03/09
# @Author : shiys
# @File : NcepCfsDataUtils.py


import numpy as np
import xarray as xr
from com.nriet.utils import DateUtils
import os
import logging
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import FILE_NOT_FOUND_ERROR_CODE,PARAMETER_VALUE_ERROR_CODE


class NcepCfsDataUtils:
    """获取EC模式数据工具类
     根据传入的站点文件的路径、时间尺度、时间访问、要素、站号等实时获取出相关的站点数据
    """
    def get_cfs_mean_data(dataInPutPathFore, forecastTime, startTime, endTime, var, startLat, endLat, startLon, endLon, whetherMakeup):

        # 根据起报时间替换数据路径里的占位符
        # 替换路径里的时间占位符 "#YYYY#  #MM# #DD#"
        dataInPutPathFore_y = dataInPutPathFore.replace("#YYYY#", forecastTime[0:4]).replace("#MM#", forecastTime[4:6])
        # 替换文件名中的起报时间
        dataInputForeFile = dataInPutPathFore_y.replace("#YYYYMMDD#", forecastTime)
        # 判断文件是否存在,不存在抛异常退出
        if os.system("ls " + dataInputForeFile.replace("#HH#_#NM#", "*")) != 0:
            error_str = " %s Nc file not found !" % dataInputForeFile
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 获取模式预报的起止时间
        foreStartTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 1)
        foreEndTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 44)
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
        endIndex = 43
        if endTime in time_list:
            endIndex = time_list.index(endTime)

        # 获取四个时次的数据
        hours = ['00', '06', '12', '18']
        members = ["01", "02", "03", "04"]
        resdata = []
        dim = 'ens'
        for hh in hours:
            dataInputForeFile_hh = dataInputForeFile.replace("#HH#", hh)
            for mb in members:
                dataInputForeFile_mb = dataInputForeFile_hh.replace("#NM#", mb)
                # logging.info(os.path.isfile(dataInputForeFile_mb))
                # logging.info(dataInputForeFile_mb)
                if not os.path.isfile(dataInputForeFile_mb):
                    continue
                ds = xr.open_dataset(dataInputForeFile_mb)
                lat = ds.lat
                lon = ds.lon
                tmpdata = ds[var]
                # 截取指定区域范围的数据
                lon_range = lon[(lon >= startLon) & (lon <= endLon)]
                # 处理 单经度取数据报错的问题（修改为取邻近点的经度）
                if len(lon_range) == 0 and startLon == endLon:
                    lon_t = abs(lon.values - startLon)
                    i1 = np.argsort(lon_t)[0]
                    lon_range = lon[i1:i1 + 1]
                lat_range = lat[(lat >= startLat) & (lat <= endLat)]
                tmpdata = tmpdata.sel(lon=lon_range, lat=lat_range)
                # 截取指定时间范围的数据
                tmpdata1 = tmpdata[startIndex:endIndex + 1]
                # 重置时间维信息
                tmpdata1['time'] = time_list[startIndex:endIndex + 1]
                # 将数组扩维，并设置维度信息
                newdata = tmpdata1.expand_dims(dim)
                newdata[dim] = [hh+mb]
                resdata.append(newdata)
        if len(resdata) == 0:
            error_str = " %s Nc file not found ! forecastTime: %s" % (dataInPutPathFore,forecastTime)
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 将时间维合并
        cfsData = xr.concat(resdata, dim=dim)
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "day")
            data_time_list = cfsData.time.values
            # 筛选超出预报范围的时间
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            want_dims = cfsData.dims
            shape = list(cfsData.shape)
            want_coords = []
            for ii, dm in enumerate(want_dims):
                if dm == "time":
                    shape[ii] = len(diff_time_list)
                    want_coords.append(diff_time_list)
                else:
                    want_coords.append(cfsData[dm])
            nan_data = np.full(shape, np.nan)
            makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
            cfsData = xr.concat([cfsData, makeup_data], dim='time')

        # 将合并后的数据按时间进行排序，重新整合数据
        b = sorted(enumerate(cfsData.time.values), key=lambda x: x[1])
        time_index = [x[0] for x in b]
        cfsData = cfsData.isel(time=time_index)
        return cfsData

    def get_cfs_mn_mean_data(dataInPutPathFore, forecastTime, startTime, endTime, var, startLat, endLat, startLon, endLon, whetherMakeup):
        # 根据起报时间替换数据路径里的占位符
        # 替换路径里的时间占位符 "#YYYY#  #MM# #DD#"
        dataInPutPathFore_y = dataInPutPathFore.replace("#YYYY#", forecastTime[0:4]).replace("#MM#", forecastTime[4:6])
        # 替换文件名中的起报时间
        dataInputForeFile = dataInPutPathFore_y.replace("#YYYYMMDD#", forecastTime)
        if not os.path.isfile(dataInputForeFile):
            error_str = " %s Nc file not found ! forecastTime: %s" % (dataInputForeFile,forecastTime)
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 获取模式预报的起止时间
        foreStartTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 1)
        foreEndTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 44)
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
        endIndex = 43
        if endTime in time_list:
            endIndex = time_list.index(endTime)

        ds = xr.open_dataset(dataInputForeFile)
        lat = ds.lat
        lon = ds.lon
        tmpdata = ds[var]
        # 截取指定区域范围的数据
        lon_range = lon[(lon >= startLon) & (lon <= endLon)]
        # 处理 单经度取数据报错的问题（修改为取邻近点的经度）
        if len(lon_range) == 0 and startLon == endLon:
            lon_t = abs(lon.values - startLon)
            i1 = np.argsort(lon_t)[0]
            lon_range = lon[i1:i1 + 1]
        lat_range = lat[(lat >= startLat) & (lat <= endLat)]
        tmpdata = tmpdata.sel(lon=lon_range, lat=lat_range)
        # 截取指定时间范围的数据
        cfsData = tmpdata[startIndex:endIndex + 1]
        # 重置时间维信息
        cfsData['time'] = time_list[startIndex:endIndex + 1]
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "day")
            data_time_list = cfsData.time.values
            # 筛选超出预报范围的时间
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            want_dims = cfsData.dims
            shape = list(cfsData.shape)
            want_coords = []
            for ii, dm in enumerate(want_dims):
                if dm == "time":
                    shape[ii] = len(diff_time_list)
                    want_coords.append(diff_time_list)
                else:
                    want_coords.append(cfsData[dm])
            nan_data = np.full(shape, np.nan)
            makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
            cfsData = xr.concat([cfsData, makeup_data], dim='time')
        # 将合并后的数据按时间进行排序，重新整合数据
        b = sorted(enumerate(cfsData.time.values), key=lambda x: x[1])
        time_index = [x[0] for x in b]
        cfsData = cfsData.isel(time=time_index)
        return cfsData

    # 获取模式的预测气候态数据
    def get_cfs_ltm_data(dataInPutPathFore, forecastTime, startTime, endTime, var, startLat, endLat, startLon, endLon, whetherMakeup):
        # 替换文件名中的起报时间
        forecastTime = str(forecastTime)
        dataInputForeFile_mmdd = dataInPutPathFore.replace("#MMDD#", forecastTime[4:])
        # 判断文件是否存在,不存在抛异常退出
        if os.system("ls " + dataInputForeFile_mmdd.replace("_#HH#_#NM#", "*")) != 0:
            error_str = " %s Nc file not found ! " % dataInputForeFile_mmdd
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 获取模式预报的起止时间
        foreStartTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 1)
        foreEndTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 44)
        # 获取模式预报起止时间内所有预报时间
        time_list = DateUtils.get_time_list([foreStartTime, foreEndTime], "day")
        if whetherMakeup == "False":
            if startTime not in time_list:
                error_str = "Parameter startTime: %s is not in the actual forecastPeriod [ %s ,  %s ] " % (
                startTime, foreStartTime, foreEndTime)
                raise AlgorithmException(response_code=PARAMETER_VALUE_ERROR_CODE, response_msg=error_str)
            if endTime not in time_list:
                error_str = "Parameter endTime: %s is not in the actual forecastPeriod [ %s ,  %s ] " % (
                endTime, foreStartTime, foreEndTime)
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
        endIndex = 43
        if endTime in time_list:
            endIndex = time_list.index(endTime)

        # 获取四个时次的数据
        hours = ['00', '06', '12', '18']
        members = ["01", "02", "03", "04"]
        resdata = []
        dim = 'ens'
        for hh in hours:
            dataInputForeFile_hh = dataInputForeFile_mmdd.replace("#HH#", hh)
            for mb in members:
                dataInputForeFile_mb = dataInputForeFile_hh.replace("#NM#", mb)
                if not os.path.isfile(dataInputForeFile_mb):
                    continue
                ds = xr.open_dataset(dataInputForeFile_mb)
                lat = ds.lat
                lon = ds.lon
                tmpdata = ds[var]
                # 截取指定区域范围的数据
                lon_range = lon[(lon >= startLon) & (lon <= endLon)]
                # 处理 单经度取数据报错的问题（修改为取邻近点的经度）
                if len(lon_range) == 0 and startLon == endLon:
                    lon_t = abs(lon.values - startLon)
                    i1 = np.argsort(lon_t)[0]
                    lon_range = lon[i1:i1 + 1]
                lat_range = lat[(lat >= startLat) & (lat <= endLat)]
                tmpdata = tmpdata.sel(lon=lon_range, lat=lat_range)
                # 截取指定时间范围的数据
                tmpdata1 = tmpdata[startIndex:endIndex + 1]
                # 重置时间维信息
                tmpdata1['time'] = time_list[startIndex:endIndex + 1]
                # 将数组扩维，并设置维度信息
                newdata = tmpdata1.expand_dims(dim)
                newdata[dim] = [mb]
                resdata.append(newdata)
        if len(resdata) == 0:
            error_str = " %s Nc file not found ! forecastTime: %s" % (dataInPutPathFore, forecastTime)
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 将时间维合并
        cfsLtmData = xr.concat(resdata, dim=dim)
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "day")
            data_time_list = cfsLtmData.time.values
            # 筛选超出预报范围的时间
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            want_dims = cfsLtmData.dims
            shape = list(cfsLtmData.shape)
            want_coords = []
            for ii, dm in enumerate(want_dims):
                if dm == "time":
                    shape[ii] = len(diff_time_list)
                    want_coords.append(diff_time_list)
                else:
                    want_coords.append(cfsLtmData[dm])
            nan_data = np.full(shape, np.nan)
            makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
            cfsLtmData = xr.concat([cfsLtmData, makeup_data], dim='time')
        # 将合并后的数据按时间进行排序，重新整合数据
        b = sorted(enumerate(cfsLtmData.time.values), key=lambda x: x[1])
        time_index = [x[0] for x in b]
        cfsLtmData = cfsLtmData.isel(time=time_index)
        return cfsLtmData


    # dataInputPath = '/nfsshare/cdbdata/data/NCEP/cfs_day/tmp/day/#YYYY#/#MM#/#YYYYMMDD#_#HH#_#NM#.nc'
    # dataInputPath2 = '/nfsshare/cdbdata/data/EC1_45/tmp/ltm/#MMDD#_#HH#.nc'
    # foreTime = '20200310'
    # stime = '20200314'
    # etime = '20200415'
    # var = 'tmp'
    # startLat = 0
    # endLat = 60
    # startLon = 70
    # endLon = 140
    # xdata = get_cfs_mean_data(dataInputPath, foreTime, stime, etime, var, startLat, endLat, startLon, endLon)
    # logging.info(xdata)
    # # ldata = get_cfs_ltm_data(dataInputPath2, foreTime, stime, etime, var, startLat, endLat, startLon, endLon)
    # # logging.info(ldata)