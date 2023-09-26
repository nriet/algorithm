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

class ModesDataUtils:
    # 获取模式的预测数据
    def get_modes_mean_data(dataInPutPathFore, forecastTime, startTime, endTime, var, startLat, endLat, startLon, endLon, dataSource, whetherMakeup):
        # 替换文件中起报时间的占位符 "#YYYYMM#"
        dataInputForeFile = dataInPutPathFore.replace("#YYYYMM#", forecastTime)
        if dataSource == "NCCCSM3":
            dataInputForeFile = dataInPutPathFore.replace("#YYYY_MM#", forecastTime[:4]+"_"+forecastTime[4:])
        # print(dataInputForeFile)
        if not os.path.isfile(dataInputForeFile):
            error_str = " %s Nc file not found !" % dataInputForeFile
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        #NCEP_CFS2
        if dataSource == "CFS2" or dataSource == "MODESCFS":
            fStartMon = 0
            fEndMon = 9
        #JMA_CPS2
        if dataSource == "JMA2":
            fStartMon = 1
            fEndMon = 6
        # JMA_CPS3
        if dataSource == "JMA3":
            fStartMon = 1
            fEndMon = 6
        # CPSV3MON
        if dataSource == "CPSV3MON":
            fStartMon = 1
            fEndMon = 6
        # ECMWF_SYSTEM5
        if dataSource == "ECMWF5" or dataSource == "MODESEC" or dataSource == "EC5":
            fStartMon = 1
            fEndMon = 6
        # UKMO_GLOSEA5
        if dataSource == "UKMO5":
            fStartMon = 1
            fEndMon = 5
        if dataSource == "NCCCSM" or dataSource == "NCC":
            fStartMon = 0
            fEndMon = 12
        if dataSource == "NCCCSM3":
            fStartMon = 0
            fEndMon = 6
        foreStartTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), fStartMon)
        foreEndTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), fEndMon)
        # print(forecastTime,foreStartTime,foreEndTime)

        # 获取模式预报起止时间内所有预报时间
        time_list = DateUtils.get_time_list([foreStartTime, foreEndTime], "mon")
        # print(time_list)

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
        startIndex = 0
        if startTime in time_list:
            startIndex = time_list.index(startTime)

        if dataSource == "CFS2" or dataSource == "MODESCFS":
            endIndex = 9
        #JMA_CPS2
        if dataSource == "JMA2":
            endIndex = 5
        # JMA_CPS3
        if dataSource == "JMA3":
            endIndex = 5
        # CPSV3MON
        if dataSource == "CPSV3MON":
            endIndex = 5
        # ECMWF_SYSTEM5
        if dataSource == "ECMWF5" or dataSource == "MODESEC":
            endIndex = 5
        # UKMO_GLOSEA5
        if dataSource == "UKMO5":
            endIndex = 4
        if dataSource == "NCCCSM":
            endIndex = 12
        if dataSource == "NCCCSM3":
            endIndex = 6
        if endTime in time_list:
            endIndex = time_list.index(endTime)
        # print(foreStartTime,startIndex, foreEndTime,endIndex)
        ds = xr.open_dataset(dataInputForeFile)
        # ECMWF_SYSTEM5
        if dataSource == "ECMWF5" or dataSource == "MODESEC" or dataSource == "EC5":
            ds = ds.rename({"latitude": "lat","longitude": "lon"})
        lat = ds.lat
        lon = ds.lon
        try:
            tmpdata = ds[var]
        except KeyError:
            error_str = " %s not in %s !" % (var,dataInputForeFile)
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 截取指定区域范围的数据
        lon_range = lon[(lon >= startLon) & (lon <= endLon)]
        lat_range = lat[(lat >= startLat) & (lat <= endLat)]
        tmpdata = tmpdata.sel(lon=lon_range, lat=lat_range)
        # print(tmpdata)
        modedata = tmpdata[startIndex:endIndex+1]
        # 重置时间维信息
        modedata['time'] = time_list[startIndex:endIndex+1]
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "mon")
            data_time_list = modedata.time.values
            # 筛选超出预报范围的时间
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            want_dims = modedata.dims
            shape = list(modedata.shape)
            want_coords = []
            for ii, dm in enumerate(want_dims):
                if dm == "time":
                    shape[ii] = len(diff_time_list)
                    want_coords.append(diff_time_list)
                else:
                    want_coords.append(modedata[dm])
            nan_data = np.full(shape, np.nan)
            makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
            modedata = xr.concat([modedata, makeup_data], dim='time')
            # 将合并后的数据按时间进行排序，重新整合数据
            b = sorted(enumerate(modedata.time.values), key=lambda x: x[1])
            time_index = [x[0] for x in b]
            modedata = modedata.isel(time=time_index)

        return modedata

    # 获取模式的预测气候态数据
    def get_modes_ltm_data(dataInPutPathFore, forecastTime, startTime, endTime, var, startLat, endLat, startLon, endLon, dataSource, whetherMakeup):
        # 替换文件中起报时间的占位符 "#YYYYMM#"
        forecastTime = str(forecastTime)
        dataInputForeFile = dataInPutPathFore.replace("#YYYYMM#", forecastTime)
        dataInputForeFile = dataInputForeFile.replace("#MM#", forecastTime[4:6])
        # print(dataInputForeFile)
        if not os.path.isfile(dataInputForeFile):
            error_str = " %s Nc file not found !" % dataInputForeFile
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # NCEP_CFS2
        if dataSource == "CFS2" or dataSource == "MODESCFS":
            fStartMon = 0
            fEndMon = 9
        # JMA_CPS2
        if dataSource == "JMA2":
            fStartMon = 1
            fEndMon = 6
        # JMA_CPS3
        if dataSource == "JMA3":
            fStartMon = 1
            fEndMon = 6
        # CPSV3MON
        if dataSource == "CPSV3MON":
            fStartMon = 1
            fEndMon = 6
        # ECMWF_SYSTEM5
        if dataSource == "ECMWF5" or dataSource == "MODESEC" or dataSource == "EC5":
            fStartMon = 1
            fEndMon = 6
        # UKMO_GLOSEA5
        if dataSource == "UKMO5":
            fStartMon = 1
            fEndMon = 5
        if dataSource == "NCCCSM" or dataSource == "NCC":
            fStartMon = 0
            fEndMon = 12
        if dataSource == "NCCCSM3":
            fStartMon = 0
            fEndMon = 6
        foreStartTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), fStartMon)
        foreEndTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), fEndMon)
        # print(foreStartTime,foreEndTime)
        # 获取模式预报起止时间内所有预报时间
        time_list = DateUtils.get_time_list([foreStartTime, foreEndTime], "mon")
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
        if dataSource == "CFS2" or dataSource == "MODESCFS":
            endIndex = 9
        # JMA_CPS2
        if dataSource == "JMA2":
            endIndex = 5
        # JMA_CPS3
        if dataSource == "JMA3":
            endIndex = 5
        # CPSV3MON
        if dataSource == "CPSV3MON":
            endIndex = 5
        # ECMWF_SYSTEM5
        if dataSource == "ECMWF5" or dataSource == "MODESEC" or dataSource == "EC5":
            endIndex = 5
        # UKMO_GLOSEA5
        if dataSource == "UKMO5":
            endIndex = 4
        if dataSource == "NCCCSM" or dataSource == "NCC":
            endIndex = 12
        if dataSource == "NCCCSM3":
            endIndex = 6
        if endTime in time_list:
            endIndex = time_list.index(endTime)
        ds = xr.open_dataset(dataInputForeFile)
        if dataSource == "ECMWF5" or dataSource == "MODESEC" or dataSource == "EC5":
            ds = ds.rename({"latitude": "lat","longitude": "lon"})
        lat = ds.lat
        lon = ds.lon
        tmpdata = ds[var]

        # 截取指定区域范围的数据
        lon_range = lon[(lon >= startLon) & (lon <= endLon)]
        lat_range = lat[(lat >= startLat) & (lat <= endLat)]
        tmpdata = tmpdata.sel(lon=lon_range, lat=lat_range)
        # print(tmpdata)
        mode_ltm_data = tmpdata[startIndex:endIndex + 1]
        # 重置时间维信息
        mode_ltm_data['time'] = time_list[startIndex:endIndex + 1]
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "mon")
            data_time_list = mode_ltm_data.time.values
            # 筛选超出预报范围的时间
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            want_dims = mode_ltm_data.dims
            shape = list(mode_ltm_data.shape)
            want_coords = []
            for ii, dm in enumerate(want_dims):
                if dm == "time":
                    shape[ii] = len(diff_time_list)
                    want_coords.append(diff_time_list)
                else:
                    want_coords.append(mode_ltm_data[dm])
            nan_data = np.full(shape, np.nan)
            makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
            mode_ltm_data = xr.concat([mode_ltm_data, makeup_data], dim='time')
            # 将合并后的数据按时间进行排序，重新整合数据
            b = sorted(enumerate(mode_ltm_data.time.values), key=lambda x: x[1])
            time_index = [x[0] for x in b]
            mode_ltm_data = mode_ltm_data.isel(time=time_index)
        return mode_ltm_data

    # 获取模式(BCC_CSM1.1m)的预测数据
    def get_bcccms11m_mean_data(dataInPutPathFore, forecastTime, startTime, endTime, var, startLat, endLat, startLon,endLon, dataSource, whetherMakeup):
        # 替换文件中起报时间的占位符 "#YYYYMM#"
        dataInputForeFile = dataInPutPathFore.replace("#YYYY_MM#", forecastTime[0:4]+"_"+forecastTime[4:])
        # print(dataInputForeFile)
        if not os.path.isfile(dataInputForeFile):
            error_str = " %s Nc file not found !" % dataInputForeFile
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # NCEP_CFS2
        fStartMon = 0
        fEndMon = 12
        foreStartTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), fStartMon)
        foreEndTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), fEndMon)
        # print(foreStartTime,foreEndTime)

        # 获取模式预报起止时间内所有预报时间
        time_list = DateUtils.get_time_list([foreStartTime, foreEndTime], "mon")
        # print(time_list)
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
        endIndex = 12
        if endTime in time_list:
            endIndex = time_list.index(endTime)
        # print(foreStartTime,startIndex, foreEndTime,endIndex)
        ds = xr.open_dataset(dataInputForeFile,decode_times=False)
        lat = ds.lat
        lon = ds.lon
        tmpdata = ds[var]
        # 截取指定区域范围的数据
        lon_range = lon[(lon >= startLon) & (lon <= endLon)]
        lat_range = lat[(lat >= startLat) & (lat <= endLat)]
        tmpdata = tmpdata.sel(lon=lon_range, lat=lat_range)
        # print(tmpdata)
        bcccmsMeanData = tmpdata[startIndex:endIndex + 1]
        # 重置时间维信息
        bcccmsMeanData['time'] = time_list[startIndex:endIndex + 1]
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "mon")
            data_time_list = bcccmsMeanData.time.values
            # 筛选超出预报范围的时间
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            want_dims = bcccmsMeanData.dims
            shape = list(bcccmsMeanData.shape)
            want_coords = []
            for ii, dm in enumerate(want_dims):
                if dm == "time":
                    shape[ii] = len(diff_time_list)
                    want_coords.append(diff_time_list)
                else:
                    want_coords.append(bcccmsMeanData[dm])
            nan_data = np.full(shape, np.nan)
            makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
            bcccmsMeanData = xr.concat([bcccmsMeanData, makeup_data], dim='time')
            # 将合并后的数据按时间进行排序，重新整合数据
            b = sorted(enumerate(bcccmsMeanData.time.values), key=lambda x: x[1])
            time_index = [x[0] for x in b]
            bcccmsMeanData = bcccmsMeanData.isel(time=time_index)
        return bcccmsMeanData

    # 获取模式(BCC_CSM1.1m)的预测数据
    def get_bcccms11m_ltm_data(dataInPutPathFore, forecastTime, startTime, endTime, var, startLat, endLat, startLon, endLon, dataSource, whetherMakeup):
        # 替换文件中起报时间的占位符 "#YYYYMM#"
        dataInputForeFile = dataInPutPathFore
        # print(dataInputForeFile)
        if not os.path.isfile(dataInputForeFile):
            error_str = " %s Nc file not found !" % dataInputForeFile
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # NCEP_CFS2
        fStartMon = 0
        fEndMon = 12
        foreStartTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), fStartMon)
        foreEndTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), fEndMon)
        # print(foreStartTime, foreEndTime)

        # 获取模式预报起止时间内所有预报时间
        time_list = DateUtils.get_time_list([foreStartTime, foreEndTime], "mon")
        # print(time_list)
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
        endIndex = 12
        if endTime in time_list:
            endIndex = time_list.index(endTime)
        # print(foreStartTime,startIndex, foreEndTime,endIndex)
        ds = xr.open_dataset(dataInputForeFile, decode_times=False)
        print(ds)
        if "forcast_time" in ds[var].dims:
            ds = ds.rename({"time":"fore_mon","forcast_time":"time"})
        if "fortime" in ds[var].dims:
            ds = ds.rename({"fortime": "fore_mon"})
        lat = ds.lat
        lon = ds.lon
        tmpdata = ds[var]
        # 截取指定区域范围的数据
        lon_range = lon[(lon >= startLon) & (lon <= endLon)]
        lat_range = lat[(lat >= startLat) & (lat <= endLat)]
        tmpdata = tmpdata.sel(lon=lon_range, lat=lat_range)
        foreMonIndex = int(forecastTime[4:])-1
        bcccmsLtmData = tmpdata[foreMonIndex:foreMonIndex+1,startIndex:endIndex + 1]
        bcccmsLtmData = bcccmsLtmData.mean(dim="fore_mon")
        # 重置时间维信息
        bcccmsLtmData['time'] = time_list[startIndex:endIndex + 1]
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "mon")
            data_time_list = bcccmsLtmData.time.values
            # 筛选超出预报范围的时间
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            want_dims = bcccmsLtmData.dims
            shape = list(bcccmsLtmData.shape)
            want_coords = []
            for ii, dm in enumerate(want_dims):
                if dm == "time":
                    shape[ii] = len(diff_time_list)
                    want_coords.append(diff_time_list)
                else:
                    want_coords.append(bcccmsLtmData[dm])
            nan_data = np.full(shape, np.nan)
            makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
            bcccmsLtmData = xr.concat([bcccmsLtmData, makeup_data], dim='time')
            # 将合并后的数据按时间进行排序，重新整合数据
            b = sorted(enumerate(bcccmsLtmData.time.values), key=lambda x: x[1])
            time_index = [x[0] for x in b]
            bcccmsLtmData = bcccmsLtmData.isel(time=time_index)
        return bcccmsLtmData
    # # dataSource = "CFS2"
    # # dataInputPath = '/nfsshare/cdbdata/data/MODESV2/MODES_data/MODESdatasetV2/NCEP_CFS2/MODESv2_ncep_cfs2_#YYYYMM#_monthly_em.nc'
    # # dataInputPath2 = '/nfsshare/cdbdata/data/MODESV2/MODES_data/MODESdatasetV2_ltm/NCEP_CFS2/MODESv2_ncep_cfs2_#MM#_monthly_ltm.nc'
    # # dataSource = "JMA2"
    # # dataInputPath = '/nfsshare/cdbdata/data/MODESV2/MODES_data/MODESdatasetV2/JMA_CPS2/MODESv2_jma_cps2_#YYYYMM#_monthly_em.nc'
    # # dataInputPath2 = '/nfsshare/cdbdata/data/MODESV2/MODES_data/MODESdatasetV2_ltm/JMA_CPS2/MODESv2_jma_cps2_#MM#_monthly_ltm.nc'
    # dataSource = "ECMWF5"
    # dataInputPath = '/nfsshare/cdbdata/data/MODESV2/MODES_data/MODESdatasetV2/ECMWF_SYSTEM5/MODESv2_ecmwf_system5_#YYYYMM#_monthly_em.nc'
    # dataInputPath2 = '/nfsshare/cdbdata/data/MODESV2/MODES_data/MODESdatasetV2_ltm/ECMWF_SYSTEM5/MODESv2_ecmwf_system5_#MM#_monthly_ltm.nc'
    #
    # # dataSource = "UKMO5"
    # # dataInputPath = '/nfsshare/cdbdata/data/MODESV2/MODES_data/MODESdatasetV2/UKMO_GLOSEA5/MODESv2_ukmo_glosea5_#YYYYMM#_monthly_em.nc'
    # # dataInputPath2 = '/nfsshare/cdbdata/data/MODESV2/MODES_data/MODESdatasetV2_ltm/UKMO_GLOSEA5/MODESv2_ukmo_glosea5_#MM#_monthly_ltm.nc'
    #
    #
    #
    # foreTime = '202110'
    # stime = '202110'
    # etime = '202206'
    # var = 't2m'
    # startLat = 0
    # endLat = 60
    # startLon = 70
    # endLon = 140
    # xdata = get_modes_mean_data(dataInputPath, foreTime, stime, etime, var, startLat, endLat, startLon, endLon,dataSource,"True")
    # print(xdata)
    # ldata = get_modes_ltm_data(dataInputPath2, foreTime, stime, etime, var, startLat, endLat, startLon, endLon,dataSource,"True")
    # print(ldata)