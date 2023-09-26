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
import logging
# Derf2.0模式数据获取
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import FILE_NOT_FOUND_ERROR_CODE,PARAMETER_VALUE_ERROR_CODE

class DerfDataUtils:
    # 获取模式的预测数据
    def get_derf_mean_data(dataInPutPathFore, forecastTime, startTime, endTime, var, startLat, endLat, startLon, endLon, whetherMakeup):
        # 根据起报时间替换数据路径里的占位符
        # 替换路径里的时间占位符 "#YYYY#  #MM# "
        dataInPutPathFore_y = dataInPutPathFore.replace("#YYYY#", forecastTime[0:4]).replace("#MM#", forecastTime[4:6])
        # 替换文件名中的起报时间
        dataInputForeFile = dataInPutPathFore_y.replace("#YYYYMMDD#", forecastTime)
        # 判断文件是否存在,不存在抛异常退出
        if os.system("ls " +dataInputForeFile.replace("#HH#", "*")) != 0:
            error_str = " %s Nc file not found !" % dataInputForeFile
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 获取模式预报的起止时间
        foreStartTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 0)
        foreEndTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 55)
        if "BCC_CPSv3" in dataInputForeFile.split("/"):
            foreEndTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 59)
        # 获取模式预报起止时间内所有预报时间
        time_list = DateUtils.get_time_list([foreStartTime, foreEndTime], "day")
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
        endIndex = 55
        if "BCC_CPSv3" in dataInputForeFile.split("/"):
            endIndex = 59
        if endTime in time_list:
            endIndex = time_list.index(endTime)

        # 获取四个时次的数据
        hours = ["00", "06", "12", "18"]
        if "BCC_CPSv3" in dataInputForeFile.split("/"):
            hours = ["01", "02", "03", "04"]
        if "BCC_S2S" in dataInputForeFile.split("/"):
            hours = ["01", "02", "03", "04"]
        if "BCCCSM1.2" in dataInputForeFile.split("/"):
            hours = ["01", "02", "03", "04"]
        resdata = []
        for hh in hours:
            tt1 = DateUtils.getTimeStamp()
            dataInputForeFile_hh = dataInputForeFile.replace("#HH#", hh)
            if not os.path.isfile(dataInputForeFile_hh):
                continue
            # print(dataInputForeFile_hh)
            ds = xr.open_dataset(dataInputForeFile_hh)
            if "BCC_CPSv3" in dataInputForeFile.split("/") and ds.get("level"):
                ds = ds.drop_vars("level")
            lat = ds.lat
            lon = ds.lon
            tmpdata = ds[var]
            # 截取指定区域范围的数据
            lon_range = lon[(lon >= startLon) & (lon <= endLon)]
            # 处理开始结束经度一样时取不到数据的问题
            if len(lon_range) == 0 and startLon == endLon:
                lon_t = abs(lon.values - startLon)
                i1 = np.argsort(lon_t)[0]
                lon_range = lon[i1:i1 + 1]
            lat_range = lat[(lat >= startLat) & (lat <= endLat)]
            tmpdata = tmpdata.sel(lon=lon_range, lat=lat_range)
            # 截取指定时间范围的数据
            if "BCC_CPSv3" in dataInputForeFile.split("/"):
                # print(tmpdata.time.values)
                data_time_list = time_list
            if "BCC_S2S" in dataInputForeFile.split("/"):
                # print(tmpdata.time.values)
                data_time_list = []
                data_time = list(tmpdata.time.values)
                for ti in data_time:
                    new_t = "".join(re.findall("\d+",str(ti))[:3])
                    data_time_list.append(new_t)
            if "BCCCSM1.2" in dataInputForeFile.split("/"):
                data_time_list = time_list
            if "DERF2.0" in dataInputForeFile.split("/"):
                # data_time_list = list(pd.to_datetime(tmpdata.time.values).strftime('%Y%m%d').values)
                data_time_list = time_list
            startIndex1 = 0
            if startTime in data_time_list:
                startIndex1 = data_time_list.index(startTime)
            endIndex1 = len(data_time_list)-1
            if endTime in data_time_list:
                endIndex1 = data_time_list.index(endTime)
            tmpdata1 = tmpdata[startIndex1:endIndex1+1]
            # 重置时间维信息
            # tmpdata1['time'] = time_list[startIndex:endIndex+1]
            tmpdata1['time'] = data_time_list[startIndex1:endIndex1+1]
            if "BCCCSM1.2" in dataInputForeFile.split("/"):
                tmpdata1 = tmpdata1.sel(level=200)
            # 将数组扩维，并设置维度信息
            dim = 'ens'
            newdata = tmpdata1.expand_dims(dim)
            newdata['ens'] = [hh]
            resdata.append(newdata)
            tt2 = DateUtils.getTimeStamp()
            # print("read file ["+dataInputForeFile_hh+"] 耗时："+str(tt2-tt1)+"ms")
        if len(resdata) == 0:
            error_str = " %s Nc file not found ! forecastTime: %s" % (dataInPutPathFore,forecastTime)
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 将时次维合并
        derfdata = xr.concat(resdata, dim='ens')
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "day")
            data_time_list = derfdata.time.values
            # 筛选超出预报范围的时间
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            if len(diff_time_list) > 0:
                want_dims = derfdata.dims
                shape = list(derfdata.shape)
                want_coords = []
                for ii, dm in enumerate(want_dims):
                    if dm == "time":
                        shape[ii] = len(diff_time_list)
                        want_coords.append(diff_time_list)
                    else:
                        want_coords.append(derfdata[dm])
                nan_data = np.full(shape, np.nan)
                makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
                derfdata = xr.concat([derfdata, makeup_data], dim='time')
                # 将合并后的数据按时间进行排序，重新整合数据
                b = sorted(enumerate(derfdata.time.values), key=lambda x: x[1])
                time_index = [x[0] for x in b]
                derfdata = derfdata.isel(time=time_index)
        return derfdata

    # 获取模式的预测气候态数据
    def get_derf_ltm_data(dataInPutPathFore, forecastTime, startTime, endTime, var, startLat, endLat, startLon, endLon, whetherMakeup):
        # 判断文件是否存在,不存在抛异常退出
        forecastTime = str(forecastTime) #胡玉恒添加，将forecastTime强制转为str类型
        if os.system("ls " + dataInPutPathFore.replace("#MMDD#", forecastTime[4:]).replace("#HH#", "*")) != 0:
            error_str = " %s Nc file not found ! " % dataInPutPathFore.replace("#MMDD#", forecastTime[4:])
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 获取模式预报的起止时间
        foreStartTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 0)
        # 东亚冬季风常年值数据特殊处理
        if dataInPutPathFore.find("ltm_djf") != -1:
            foreEndTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 49)
        else:
            foreEndTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 55)
        if "BCC_CPSv3" in dataInPutPathFore.split("/") :
            foreEndTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 59)
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
        # 东亚冬季风常年值数据特殊处理
        if dataInPutPathFore.find("ltm_djf") != -1:
            endIndex = 49
        else:
            endIndex = 55
        if "BCC_CPSv3" in dataInPutPathFore.split("/") :
            endIndex = 59
        if endTime in time_list:
            endIndex = time_list.index(endTime)

        #替换文件名中的起报时间(月日)
        dataInputForeFile = dataInPutPathFore.replace("#MMDD#", forecastTime[4:])
        # 获取四个时次的数据
        hours = ["00", "06", "12", "18"]
        if "BCC_S2S" in dataInputForeFile.split("/") or "BCC_CPSv3" in dataInputForeFile.split("/"):
            hours = ["01", "02", "03", "04"]
        resdata = []
        for hh in hours:
            dataInputForeFile_hh = dataInputForeFile.replace("#HH#", hh)
            logging.info(dataInputForeFile_hh)
            ds = xr.open_dataset(dataInputForeFile_hh)
            lat = ds.lat
            lon = ds.lon
            tmpdata = ds[var]
            # 截取指定区域范围的数据
            lon_range = lon[(lon >= startLon) & (lon <= endLon)]
            # 处理开始结束经度一样时取不到数据的问题
            if len(lon_range) == 0 and startLon == endLon:
                lon_t = abs(lon.values - startLon)
                i1 = np.argsort(lon_t)[0]
                lon_range = lon[i1:i1 + 1]
            lat_range = lat[(lat >= startLat) & (lat <= endLat)]
            tmpdata = tmpdata.sel(lon=lon_range, lat=lat_range)
            # 截取指定时间范围的数据
            tmpdata1 = tmpdata[startIndex:endIndex+1]
            wt_list = time_list[startIndex:endIndex + 1]
            # 东亚冬季风常年值数据特殊处理
            if dataInPutPathFore.find("ltm_djf") != -1:
                xx = [i for i, x in enumerate(wt_list) if x[4:] == '0229']
                if len(xx) == 1:
                   wt_list.pop(xx[0])
            # 重置时间维信息
            tmpdata1['time'] = wt_list
            # 将数组扩维，并设置维度信息
            dim = 'ens'
            newdata = tmpdata1.expand_dims(dim)
            newdata['ens'] = [hh]
            resdata.append(newdata)
        # 将时次维合并
        derf_ltm_data = xr.concat(resdata, dim='ens')
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "day")
            data_time_list = derf_ltm_data.time.values
            # 筛选超出预报范围的时间
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            if len(diff_time_list) > 0:
                want_dims = derf_ltm_data.dims
                shape = list(derf_ltm_data.shape)
                want_coords = []
                for ii, dm in enumerate(want_dims):
                    if dm == "time":
                        shape[ii] = len(diff_time_list)
                        want_coords.append(diff_time_list)
                    else:
                        want_coords.append(derf_ltm_data[dm])
                nan_data = np.full(shape, np.nan)
                makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
                derf_ltm_data = xr.concat([derf_ltm_data, makeup_data], dim='time')
                # 将合并后的数据按时间进行排序，重新整合数据
                b = sorted(enumerate(derf_ltm_data.time.values), key=lambda x: x[1])
                time_index = [x[0] for x in b]
                derf_ltm_data = derf_ltm_data.isel(time=time_index)
        return derf_ltm_data

    # 获取模式的预测数据(样本平均)
    def get_derf_mn_mean_data(dataInPutPathFore, forecastTime, startTime, endTime, var, startLat, endLat, startLon,
                           endLon, whetherMakeup):
        # 根据起报时间替换数据路径里的占位符
        # 替换路径里的时间占位符 "#YYYY#  #MM# "
        dataInPutPathFore_y = dataInPutPathFore.replace("#YYYY#", forecastTime[0:4]).replace("#MM#", forecastTime[4:6])
        # 替换文件名中的起报时间
        dataInputForeFile = dataInPutPathFore_y.replace("#YYYYMMDD#", forecastTime)
        # 判断文件是否存在,不存在抛异常退出
        if not os.path.isfile(dataInputForeFile):
            error_str = " %s Nc file not found !" % dataInputForeFile
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 获取模式预报的起止时间
        foreStartTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 0)
        foreEndTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 55)
        if "BCC_CPSv3" in dataInputForeFile.split("/") :
            foreStartTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 0)
            foreEndTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 59)
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
        tt1 = DateUtils.getTimeStamp()
        # print(dataInputForeFile)
        ds = xr.open_dataset(dataInputForeFile, decode_times=False)
        if "BCC_CPSv3" in dataInputForeFile.split("/") and ds.get("level"):
            ds = ds.drop_vars("level")
        lat = ds.lat
        lon = ds.lon
        tmpdata = ds[var]
        # 截取指定区域范围的数据
        lon_range = lon[(lon >= startLon) & (lon <= endLon)]
        # 处理开始结束经度一样时取不到数据的问题
        if len(lon_range) == 0 and startLon == endLon:
            lon_t = abs(lon.values - startLon)
            i1 = np.argsort(lon_t)[0]
            lon_range = lon[i1:i1 + 1]
        lat_range = lat[(lat >= startLat) & (lat <= endLat)]
        tmpdata = tmpdata.sel(lon=lon_range, lat=lat_range)
        # 截取指定时间范围的数据
        if "BCC_CPSv3" in dataInputForeFile.split("/"):
            # print(tmpdata.time.values)
            data_time_list = time_list
        if "BCC_S2S" in dataInputForeFile.split("/"):
            # print(tmpdata.time.values)
            data_time_list = []
            data_time = list(tmpdata.time.values)
            for ti in data_time:
                new_t = "".join(re.findall("\d+", str(ti))[:3])
                data_time_list.append(new_t)
        if "BCCCSM1.2" in dataInputForeFile.split("/"):
            data_time_list = time_list
        if "DERF2.0" in dataInputForeFile.split("/"):
            # data_time_list = list(pd.to_datetime(tmpdata.time.values).strftime('%Y%m%d').values)
            data_time_list = time_list
        # print(data_time_list)
        startIndex1 = 0
        if startTime in data_time_list:
            startIndex1 = data_time_list.index(startTime)
        endIndex1 = len(data_time_list) - 1
        if endTime in data_time_list:
            endIndex1 = data_time_list.index(endTime)
        derfdata = tmpdata[startIndex1:endIndex1 + 1]
        # 重置时间维信息
        # tmpdata1['time'] = time_list[startIndex:endIndex+1]
        derfdata['time'] = data_time_list[startIndex1:endIndex1 + 1]
        if "BCCCSM1.2" in dataInputForeFile.split("/"):
            derfdata = derfdata.sel(level=200)
        # 将数组扩维，并设置维度信息
        tt2 = DateUtils.getTimeStamp()
        # print("read file [" + dataInputForeFile + "] 耗时：" + str(tt2 - tt1) + "ms")
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "day")
            data_time_list = derfdata.time.values
            # 筛选超出预报范围的时间
            t21 = DateUtils.getTimeStamp()
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            t22 = DateUtils.getTimeStamp()
            # print(diff_time_list)
            # print("筛选超出预报范围的时间 耗时：" + str(t22 - t21) + "ms")
            if len(diff_time_list) > 0:
                want_dims = derfdata.dims
                shape = list(derfdata.shape)
                want_coords = []
                for ii, dm in enumerate(want_dims):
                    if dm == "time":
                        shape[ii] = len(diff_time_list)
                        want_coords.append(diff_time_list)
                    else:
                        want_coords.append(derfdata[dm])
                nan_data = np.full(shape, np.nan)
                makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
                t23 = DateUtils.getTimeStamp()
                # print("组装缺测数据 耗时：" + str(t23 - t22) + "ms")
                derfdata = xr.concat([derfdata, makeup_data], dim='time')
                t24 = DateUtils.getTimeStamp()
                # print("合并数据 耗时：" + str(t24 - t23) + "ms")
                # 将合并后的数据按时间进行排序，重新整合数据
                b = sorted(enumerate(derfdata.time.values), key=lambda x: x[1])
                time_index = [x[0] for x in b]
                derfdata = derfdata.isel(time=time_index)
                t25 = DateUtils.getTimeStamp()
                # print("合并后的数据按时间进行排序 耗时：" + str(t25 - t24) + "ms")
                # print("补全数据总耗时耗时：" + str(t25 - t21) + "ms")
        tt3 = DateUtils.getTimeStamp()
        # print("补全数据 耗时：" + str(tt3 - tt2) + "ms")
        return derfdata

    # 获取模式的预测气候态数据(样本平均)
    def get_derf_mn_ltm_data(dataInPutPathFore, forecastTime, startTime, endTime, var, startLat, endLat, startLon,endLon, whetherMakeup):
        # 判断文件是否存在,不存在抛异常退出
        forecastTime = str(forecastTime)  # 胡玉恒添加，将forecastTime强制转为str类型
        # 替换文件名中的起报时间(月日)
        dataInputForeFile = dataInPutPathFore.replace("#MMDD#", forecastTime[4:])
        if not os.path.isfile(dataInputForeFile):
            error_str = " %s Nc file not found ! " % dataInputForeFile
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 获取模式预报的起止时间
        foreStartTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 0)
        # 东亚冬季风常年值数据特殊处理
        if dataInputForeFile.find("ltm_djf") != -1:
            foreEndTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 49)
        else:
            foreEndTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 55)
        if "BCC_CPSv3" in dataInPutPathFore.split("/") :
            foreEndTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 59)
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
        # 计算需要获得的预报数据的起止下标
        startIndex = 0
        if startTime in time_list:
            startIndex = time_list.index(startTime)
        # 东亚冬季风常年值数据特殊处理
        if dataInputForeFile.find("ltm_djf") != -1:
            endIndex = 49
        else:
            endIndex = 55
        if "BCC_CPSv3" in dataInPutPathFore.split("/") :
            endIndex = 59
        if endTime in time_list:
            endIndex = time_list.index(endTime)
        # logging.info(dataInputForeFile)
        ds = xr.open_dataset(dataInputForeFile,decode_times=False)
        lat = ds.lat
        lon = ds.lon
        tmpdata = ds[var]
        # 截取指定区域范围的数据
        lon_range = lon[(lon >= startLon) & (lon <= endLon)]
        # 处理开始结束经度一样时取不到数据的问题
        if len(lon_range) == 0 and startLon == endLon:
            lon_t = abs(lon.values - startLon)
            i1 = np.argsort(lon_t)[0]
            lon_range = lon[i1:i1 + 1]
        lat_range = lat[(lat >= startLat) & (lat <= endLat)]
        tmpdata = tmpdata.sel(lon=lon_range, lat=lat_range)
        # 截取指定时间范围的数据
        derf_ltm_data = tmpdata[startIndex:endIndex + 1]
        wt_list = time_list[startIndex:endIndex + 1]
        # 东亚冬季风常年值数据特殊处理
        if dataInputForeFile.find("ltm_djf") != -1:
            xx = [i for i, x in enumerate(wt_list) if x[4:] == '0229']
            if len(xx) == 1:
                wt_list.pop(xx[0])
        # 重置时间维信息
        derf_ltm_data['time'] = wt_list
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "day")
            data_time_list = derf_ltm_data.time.values
            # 筛选超出预报范围的时间
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            if len(diff_time_list) > 0:
                want_dims = derf_ltm_data.dims
                shape = list(derf_ltm_data.shape)
                want_coords = []
                for ii, dm in enumerate(want_dims):
                    if dm == "time":
                        shape[ii] = len(diff_time_list)
                        want_coords.append(diff_time_list)
                    else:
                        want_coords.append(derf_ltm_data[dm])
                nan_data = np.full(shape, np.nan)
                makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
                derf_ltm_data = xr.concat([derf_ltm_data, makeup_data], dim='time')
                # 将合并后的数据按时间进行排序，重新整合数据
                b = sorted(enumerate(derf_ltm_data.time.values), key=lambda x: x[1])
                time_index = [x[0] for x in b]
                derf_ltm_data = derf_ltm_data.isel(time=time_index)
        return derf_ltm_data

    # 获取模式订正的站点预测数据（多样本）
    def get_cpsv3_dz_mean_data(dataInPutPathFore, forecastTime, startTime, endTime, var, station_range, whetherMakeup):
        # 根据起报时间替换数据路径里的占位符
        # 替换路径里的时间占位符 "#YYYY#  #MM# "
        dataInPutPathFore_y = dataInPutPathFore.replace("#YYYY#", forecastTime[0:4]).replace("#MM#",forecastTime[4:6])
        # 替换文件名中的起报时间
        dataInputForeFile = dataInPutPathFore_y.replace("#YYYYMMDD#", forecastTime)
        # 判断文件是否存在,不存在抛异常退出
        if os.system("ls " + dataInputForeFile.replace("#HH#", "*")) != 0:
            error_str = " %s Nc file not found !" % dataInputForeFile
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 获取模式预报的起止时间
        foreStartTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 0)
        foreEndTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 60)
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

        # 计算需要获得的预报数据的起止下标
        startIndex = 0
        if startTime in time_list:
            startIndex = time_list.index(startTime)
        endIndex = 59
        if endTime in time_list:
            endIndex = time_list.index(endTime)

        # 获取四个时次的数据
        hours = ["01", "02", "03", "04"]
        resdata = []
        for hh in hours:
            tt1 = DateUtils.getTimeStamp()
            dataInputForeFile_hh = dataInputForeFile.replace("#HH#", hh)
            if not os.path.isfile(dataInputForeFile_hh):
                continue
            # print(dataInputForeFile_hh)
            ds = xr.open_dataset(dataInputForeFile_hh)
            tmpdata = ds[var]
            # 筛选站点
            file_station = list(ds.station.values)
            inner_station = list(set(file_station).intersection(set(station_range)))
            if len(inner_station) == len(station_range):
                tmpdata = tmpdata.sel(station=station_range)
            else:
                tmpdata1 = tmpdata.sel(station=inner_station)
                diff_station = list(set(station_range).difference(inner_station))
                want_dims1 = tmpdata1.dims
                shape1 = list(tmpdata1.shape)
                want_coords1 = []
                for ii, dm in enumerate(want_dims1):
                    if dm == "station":
                        shape1[ii] = len(diff_station)
                        want_coords1.append(diff_station)
                    else:
                        want_coords1.append(tmpdata1[dm])
                nan_data1 = np.full(shape1, np.nan)
                makeup_data1 = xr.DataArray(nan_data1, coords=want_coords1, dims=want_dims1)
                tmpdata = xr.concat([tmpdata1, makeup_data1], dim='station')
                tmpdata = tmpdata.sel(station=station_range)
            # 截取指定时间范围的数据
            data_time_list = time_list
            # print(data_time_list)
            startIndex1 = 0
            if startTime in data_time_list:
                startIndex1 = data_time_list.index(startTime)
            endIndex1 = len(data_time_list) - 1
            if endTime in data_time_list:
                endIndex1 = data_time_list.index(endTime)
            tmpdata1 = tmpdata[startIndex1:endIndex1 + 1]
            # 重置时间维信息
            # tmpdata1['time'] = time_list[startIndex:endIndex+1]
            tmpdata1['time'] = data_time_list[startIndex1:endIndex1 + 1]
            # 将数组扩维，并设置维度信息
            dim = 'ens'
            newdata = tmpdata1.expand_dims(dim)
            newdata['ens'] = [hh]
            resdata.append(newdata)
            tt2 = DateUtils.getTimeStamp()
            # print("read file ["+dataInputForeFile_hh+"] 耗时："+str(tt2-tt1)+"ms")
        if len(resdata) == 0:
            error_str = " %s Nc file not found ! forecastTime: %s" % (dataInPutPathFore, forecastTime)
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 将时次维合并
        cpsv3dzdata = xr.concat(resdata, dim='ens')
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "day")
            data_time_list = cpsv3dzdata.time.values
            # 筛选超出预报范围的时间
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            if len(diff_time_list) > 0:
                want_dims = cpsv3dzdata.dims
                shape = list(cpsv3dzdata.shape)
                want_coords = []
                for ii, dm in enumerate(want_dims):
                    if dm == "time":
                        shape[ii] = len(diff_time_list)
                        want_coords.append(diff_time_list)
                    else:
                        want_coords.append(cpsv3dzdata[dm])
                nan_data = np.full(shape, np.nan)
                makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
                cpsv3dzdata = xr.concat([cpsv3dzdata, makeup_data], dim='time')
                # 将合并后的数据按时间进行排序，重新整合数据
                b = sorted(enumerate(cpsv3dzdata.time.values), key=lambda x: x[1])
                time_index = [x[0] for x in b]
                cpsv3dzdata = cpsv3dzdata.isel(time=time_index)
        return cpsv3dzdata

    # 获取模式订正的站点预测数据(样本平均)
    def get_cpsv3_dz_mn_mean_data(dataInPutPathFore, forecastTime, startTime, endTime, var, station_range, whetherMakeup):
        # 根据起报时间替换数据路径里的占位符
        # 替换路径里的时间占位符 "#YYYY#  #MM# "
        dataInPutPathFore_y = dataInPutPathFore.replace("#YYYY#", forecastTime[0:4]).replace("#MM#",forecastTime[4:6])
        # 替换文件名中的起报时间
        dataInputForeFile = dataInPutPathFore_y.replace("#YYYYMMDD#", forecastTime)
        # 判断文件是否存在,不存在抛异常退出
        if not os.path.isfile(dataInputForeFile):
            error_str = " %s Nc file not found !" % dataInputForeFile
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 获取模式预报的起止时间
        foreStartTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 0)
        foreEndTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"), 60)
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
        tt1 = DateUtils.getTimeStamp()
        # print(dataInputForeFile)
        ds = xr.open_dataset(dataInputForeFile)
        tmpdata = ds[var]
        # 筛选站点
        file_station = list(ds.station.values)
        inner_station = list(set(file_station).intersection(set(station_range)))
        if len(inner_station) == len(station_range):
            tmpdata = tmpdata.sel(station=station_range)
        else:
            tmpdata1 = tmpdata.sel(station=inner_station)
            diff_station = list(set(station_range).difference(inner_station))
            want_dims1 = tmpdata1.dims
            shape1 = list(tmpdata1.shape)
            want_coords1 = []
            for ii, dm in enumerate(want_dims1):
                if dm == "station":
                    shape1[ii] = len(diff_station)
                    want_coords1.append(diff_station)
                else:
                    want_coords1.append(tmpdata1[dm])
            nan_data1 = np.full(shape1, np.nan)
            makeup_data1 = xr.DataArray(nan_data1, coords=want_coords1, dims=want_dims1)
            tmpdata = xr.concat([tmpdata1, makeup_data1], dim='station')
            tmpdata = tmpdata.sel(station=station_range)
        # 截取指定时间范围的数据
        data_time_list = time_list
        # print(data_time_list)
        startIndex1 = 0
        if startTime in data_time_list:
            startIndex1 = data_time_list.index(startTime)
        endIndex1 = len(data_time_list) - 1
        if endTime in data_time_list:
            endIndex1 = data_time_list.index(endTime)
        cpsv3dzdata = tmpdata[startIndex1:endIndex1 + 1]
        # 重置时间维信息
        # tmpdata1['time'] = time_list[startIndex:endIndex+1]
        cpsv3dzdata['time'] = data_time_list[startIndex1:endIndex1 + 1]
        tt2 = DateUtils.getTimeStamp()
        # print("read file [" + dataInputForeFile + "] 耗时：" + str(tt2 - tt1) + "ms")
        # 补全数据
        if whetherMakeup == "True":
            want_time_list = DateUtils.get_time_list([startTime, endTime], "day")
            data_time_list = cpsv3dzdata.time.values
            # 筛选超出预报范围的时间
            t21 = DateUtils.getTimeStamp()
            diff_time_list = []
            for want_time in want_time_list:
                if want_time not in data_time_list:
                    diff_time_list.append(want_time)
            t22 = DateUtils.getTimeStamp()
            # print(diff_time_list)
            # print("筛选超出预报范围的时间 耗时：" + str(t22 - t21) + "ms")
            if len(diff_time_list) > 0:
                want_dims = cpsv3dzdata.dims
                shape = list(cpsv3dzdata.shape)
                want_coords = []
                for ii, dm in enumerate(want_dims):
                    if dm == "time":
                        shape[ii] = len(diff_time_list)
                        want_coords.append(diff_time_list)
                    else:
                        want_coords.append(cpsv3dzdata[dm])
                nan_data = np.full(shape, np.nan)
                makeup_data = xr.DataArray(nan_data, coords=want_coords, dims=want_dims)
                t23 = DateUtils.getTimeStamp()
                # print("组装缺测数据 耗时：" + str(t23 - t22) + "ms")
                cpsv3dzdata = xr.concat([cpsv3dzdata, makeup_data], dim='time')
                t24 = DateUtils.getTimeStamp()
                # print("合并数据 耗时：" + str(t24 - t23) + "ms")
                # 将合并后的数据按时间进行排序，重新整合数据
                b = sorted(enumerate(cpsv3dzdata.time.values), key=lambda x: x[1])
                time_index = [x[0] for x in b]
                cpsv3dzdata = cpsv3dzdata.isel(time=time_index)
                t25 = DateUtils.getTimeStamp()
                # print("合并后的数据按时间进行排序 耗时：" + str(t25 - t24) + "ms")
                # print("补全数据总耗时耗时：" + str(t25 - t21) + "ms")
        tt3 = DateUtils.getTimeStamp()
        # print("补全数据 耗时：" + str(tt3 - tt2) + "ms")
        return cpsv3dzdata
