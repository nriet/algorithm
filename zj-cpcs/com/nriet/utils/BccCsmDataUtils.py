#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/03/09
# @Author : shiys
# @File : BccCsmDataUtils.py


import numpy as np
import xarray as xr
from com.nriet.utils import DateUtils
import os

from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import FILE_NOT_FOUND_ERROR_CODE,PARAMETER_VALUE_ERROR_CODE


class BccCsmDataUtils:
    """获取EC模式数据工具类
     根据传入的站点文件的路径、时间尺度、时间访问、要素、站号等实时获取出相关的站点数据
    """
    def get_bcccsm_mn_mean_data(dataInPutPathFore, forecastTime, startTime, endTime, var, startLat, endLat, startLon, endLon, whetherMakeup):
        # 根据起报时间替换数据路径里的占位符
        # 替换文件名中的起报时间
        dataInputForeFile = dataInPutPathFore.replace("#YYYYMM#", forecastTime)
        # 判断文件是否存在,不存在抛异常退出
        if not os.path.exists(dataInputForeFile):
            error_str = " %s Nc file not found !" % dataInputForeFile
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 获取模式预报的起止时间
        foreStartTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), 0)
        foreEndTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), 12)
        # 获取模式预报起止时间内所有预报时间
        time_list = DateUtils.get_time_list([foreStartTime, foreEndTime], "mon")
        if whetherMakeup == "False":
            if startTime not in time_list:
                error_str = "Parameter startTime: %s is not in the actual forecastPeriod [ %s ,  %s ] " % ( startTime, foreStartTime, foreEndTime)
                raise AlgorithmException(response_code=PARAMETER_VALUE_ERROR_CODE, response_msg=error_str)
            if endTime not in time_list:
                error_str = "Parameter endTime: %s is not in the actual forecastPeriod [ %s ,  %s ] " % (endTime,foreStartTime,foreEndTime)
                raise AlgorithmException(response_code=PARAMETER_VALUE_ERROR_CODE, response_msg=error_str)
        # 计算需要获得的预报数据的起止下标
        startIndex = 0
        if startTime in time_list:
            startIndex = time_list.index(startTime)
        endIndex = 12
        if endTime in time_list:
            endIndex = time_list.index(endTime)

        ds = xr.open_dataset(dataInputForeFile)
        lat = ds.lat
        lon = ds.lon
        try:
            tmpdata = ds[var]
        except KeyError:
            tmpdata = ds["ts"]
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
        bcccsmMeanData = tmpdata[startIndex:endIndex + 1]
        # 重置时间维信息
        bcccsmMeanData['time'] = time_list[startIndex:endIndex + 1]
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "mon")
            data_time_list = bcccsmMeanData.time.values
            # 筛选超出预报范围的时间
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            want_dims = bcccsmMeanData.dims
            shape = list(bcccsmMeanData.shape)
            want_coords = []
            for ii, dm in enumerate(want_dims):
                if dm == "time":
                    shape[ii] = len(diff_time_list)
                    want_coords.append(diff_time_list)
                else:
                    want_coords.append(bcccsmMeanData[dm])
            nan_data = np.full(shape, np.nan)
            makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
            bcccsmMeanData = xr.concat([bcccsmMeanData, makeup_data], dim='time')

        # 将合并后的数据按时间进行排序，重新整合数据
        b = sorted(enumerate(bcccsmMeanData.time.values), key=lambda x: x[1])
        time_index = [x[0] for x in b]
        bcccsmMeanData = bcccsmMeanData.isel(time=time_index)
        return bcccsmMeanData

    def get_bcccsm_mn_ltm_data(dataInPutPathFore, forecastTime, startTime, endTime, var, startLat, endLat, startLon, endLon, whetherMakeup):
        # 根据起报时间替换数据路径里的占位符
        # 替换文件名中的起报时间
        dataInputForeFile = dataInPutPathFore.replace("#MM#", forecastTime[4:])
        # 判断文件是否存在,不存在抛异常退出
        if not os.path.exists(dataInputForeFile):
            error_str = " %s Nc file not found !" % dataInputForeFile
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 获取模式预报的起止时间
        foreStartTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), 0)
        foreEndTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), 12)
        # 获取模式预报起止时间内所有预报时间
        time_list = DateUtils.get_time_list([foreStartTime, foreEndTime], "mon")
        if whetherMakeup == "False":
            if startTime not in time_list:
                error_str = "Parameter startTime: %s is not in the actual forecastPeriod [ %s ,  %s ] " % ( startTime, foreStartTime, foreEndTime)
                raise AlgorithmException(response_code=PARAMETER_VALUE_ERROR_CODE, response_msg=error_str)
            if endTime not in time_list:
                error_str = "Parameter endTime: %s is not in the actual forecastPeriod [ %s ,  %s ] " % (endTime,foreStartTime,foreEndTime)
                raise AlgorithmException(response_code=PARAMETER_VALUE_ERROR_CODE, response_msg=error_str)
        # 计算需要获得的预报数据的起止下标
        startIndex = 0
        if startTime in time_list:
            startIndex = time_list.index(startTime)
        endIndex = 12
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
        bcccsmLtmData = tmpdata[startIndex:endIndex + 1]
        # 重置时间维信息
        bcccsmLtmData['time'] = time_list[startIndex:endIndex + 1]
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "mon")
            data_time_list = bcccsmLtmData.time.values
            # 筛选超出预报范围的时间
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            want_dims = bcccsmLtmData.dims
            shape = list(bcccsmLtmData.shape)
            want_coords = []
            for ii, dm in enumerate(want_dims):
                if dm == "time":
                    shape[ii] = len(diff_time_list)
                    want_coords.append(diff_time_list)
                else:
                    want_coords.append(bcccsmLtmData[dm])
            nan_data = np.full(shape, np.nan)
            makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
            bcccsmLtmData = xr.concat([bcccsmLtmData, makeup_data], dim='time')

        # 将合并后的数据按时间进行排序，重新整合数据
        b = sorted(enumerate(bcccsmLtmData.time.values), key=lambda x: x[1])
        time_index = [x[0] for x in b]
        bcccsmLtmData = bcccsmLtmData.isel(time=time_index)
        return bcccsmLtmData

    def get_bcccsm_ens_mean_data(dataInPutPathFore, forecastTime, startTime, endTime, var, startLat, endLat, startLon, endLon, whetherMakeup):

        # 获取模式预报的起止时间
        foreStartTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), 0)
        foreEndTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), 12)
        # 获取模式预报起止时间内所有预报时间
        time_list = DateUtils.get_time_list([foreStartTime, foreEndTime], "mon")
        # 根据起报时间替换数据路径里的占位符
        # 替换文件名中的起报时间
        dataInputForeFile = dataInPutPathFore.replace("#YYYYMM#", forecastTime).replace("#FEYM#", foreEndTime)
        # 判断文件是否存在,不存在抛异常退出
        if not os.path.exists(dataInputForeFile):
            error_str = " %s Nc file not found !" % dataInputForeFile
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)

        if whetherMakeup == "False":
            if startTime not in time_list:
                error_str = "Parameter startTime: %s is not in the actual forecastPeriod [ %s ,  %s ] " % ( startTime, foreStartTime, foreEndTime)
                raise AlgorithmException(response_code=PARAMETER_VALUE_ERROR_CODE, response_msg=error_str)
            if endTime not in time_list:
                error_str = "Parameter endTime: %s is not in the actual forecastPeriod [ %s ,  %s ] " % (endTime,foreStartTime,foreEndTime)
                raise AlgorithmException(response_code=PARAMETER_VALUE_ERROR_CODE, response_msg=error_str)
        # 计算需要获得的预报数据的起止下标
        startIndex = 0
        if startTime in time_list:
            startIndex = time_list.index(startTime)
        endIndex = 12
        if endTime in time_list:
            endIndex = time_list.index(endTime)

        ds = xr.open_dataset(dataInputForeFile, decode_times=False)
        ds = ds.rename({"lev": "ens"})
        # # 设置原始数据的样本、经度和纬度维的数据类型 double -> float
        # ds["lat"].values = list(np.asarray(ds["lat"].values,dtype=np.float32))
        # ds["lon"].values = list(np.asarray(ds["lon"].values, dtype=np.float32))
        # ds["ens"].values =  list(np.asarray(ds["ens"].values, dtype=np.float32))
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
        bcccsmMeanData = tmpdata[startIndex:endIndex + 1]
        # 重置时间维信息
        bcccsmMeanData['time'] = time_list[startIndex:endIndex + 1]
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "mon")
            data_time_list = bcccsmMeanData.time.values
            # 筛选超出预报范围的时间
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            want_dims = bcccsmMeanData.dims
            shape = list(bcccsmMeanData.shape)
            want_coords = []
            for ii, dm in enumerate(want_dims):
                if dm == "time":
                    shape[ii] = len(diff_time_list)
                    want_coords.append(diff_time_list)
                else:
                    want_coords.append(bcccsmMeanData[dm])
            nan_data = np.full(shape, np.nan)
            makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
            bcccsmMeanData = xr.concat([bcccsmMeanData, makeup_data], dim='time')

        # 将合并后的数据按时间进行排序，重新整合数据
        b = sorted(enumerate(bcccsmMeanData.time.values), key=lambda x: x[1])
        time_index = [x[0] for x in b]
        bcccsmMeanData = bcccsmMeanData.isel(time=time_index)
        # 维度转置
        bcccsmMeanData = bcccsmMeanData.transpose('ens', ...)
        return bcccsmMeanData


    # dataInputPath = '/nfsshare/cdbdata/data/MODESV2/MODES_data/MODESdatasetV2/NCC_CSM11/MODESv2_ncc_csm11_#YYYYMM#_monthly_em.nc'
    # dataInputPath2 = '/nfsshare/cdbdata/data/MODESV2/MODES_data/MODESdatasetV2_ltm/NCC_CSM11/MODESv2_ncc_csm11_#MM#_monthly_ltm.nc'
    # dataInputPath3 = '/nfsshare/cdbdata/data/MODESV2/data_origin/ncc_csm11/#YYYYMM#01.atm.PREC.#YYYYMM#-#FEYM#_sfc_member.nc'
    # foreTime = '202105'
    # stime = '202105'
    # etime = '202205'
    # var = 'precsfc'
    # var2 = 'PREC'
    # startLat = 0
    # endLat = 60
    # startLon = 70
    # endLon = 140
    # whetherMakeup = "True"
    # # xdata = get_bcccsm_mn_mean_data(dataInputPath, foreTime, stime, etime, var, startLat, endLat, startLon, endLon,whetherMakeup)
    # # print(xdata)
    # # ldata =  get_bcccsm_mn_ltm_data(dataInputPath2, foreTime, stime, etime, var, startLat, endLat, startLon, endLon,whetherMakeup)
    # # print(ldata)
    #
    # edata = get_bcccsm_ens_mean_data(dataInputPath3, foreTime, stime, etime, var2, startLat, endLat, startLon, endLon,whetherMakeup)
    # print(edata)