#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/03/09
# @Author : shiys
# @File : EcDataUtils.py


import numpy as np
import os
import xarray as xr
from datetime import datetime
from com.nriet.utils import  DateUtils
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import FILE_NOT_FOUND_ERROR_CODE,PARAMETER_VALUE_ERROR_CODE

class EcWeekDataUtils:
    """获取EC模式数据工具类
     根据传入的站点文件的路径、时间尺度、时间访问、要素、站号等实时获取出相关的站点数据
    """
    def get_ecweek_mean_data(dataInPutPathFore, forecastTime, startTime, endTime, var, startLat, endLat, startLon, endLon, whetherMakeup):
        # 根据起报时间替换数据路径里的占位符
        # 替换路径里的时间占位符 "#YYYY#  #MM# #DD#"
        dataInPutPathFore_y = dataInPutPathFore.replace("#YYYY#", forecastTime[0:4]).replace("#MM#",forecastTime[4:6])
        # 替换文件名中的起报时间
        dataInputForeFile = dataInPutPathFore_y.replace("#YYYYMMDD#", forecastTime)

        foreStartTime = int(startTime)
        foreEndTime = int(endTime)
        resdata = []
        dim = 'time'
        for ftime in range(foreStartTime,foreEndTime+1):
            weekEndDay = DateUtils.day2Week(forecastTime, ftime)[1]
            ybTime = DateUtils.time_increase(DateUtils.strToDate(weekEndDay,"%Y%m%d" ), 1)
            dataInputForeFile_md = dataInputForeFile.replace("#MMDD#", ybTime[4:])
            if not os.path.isfile(dataInputForeFile_md):
                continue
            print(dataInputForeFile_md)
            ds = xr.open_dataset(dataInputForeFile_md)
            lat = ds.lat
            lon = ds.lon
            tmpdata = ds[var]
            # 截取指定区域范围的数据
            lon_range = lon[(lon >= startLon) & (lon <= endLon)]
            lat_range = lat[(lat >= startLat) & (lat <= endLat)]
            tmpdata = tmpdata.sel(lon=lon_range, lat=lat_range)
            # 将数组扩维，并设置维度信息
            newdata = tmpdata.expand_dims(dim, 1)
            newdata[dim] = [ybTime]
            resdata.append(newdata)
            print(forecastTime,ybTime)
        if len(resdata) == 0:
            error_str = " %s Nc file not found ! forecastTime: %s" % (dataInPutPathFore,forecastTime)
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 将时间维合并
        ecWeekData = xr.concat(resdata, dim=dim)
        return ecWeekData

    # dataInputPath = "/nfsshare/cdbdata/data/ECMWF/2t/day/2022/02/20220221_0314.nc"
    # dataInputPath = "/nfsshare/cdbdata/data/ECMWF/2t/day/#YYYY#/#MM#/#YYYYMMDD#_#MMDD#.nc"
    # ltmdataInputPath = "/nfsshare/cdbdata/data/ECMWF/2t/ltm/#YYYY#/#MM#/#YYYYMMDD#_#MMDD#.nc"
    # foreTime = '20220221'
    # stime = '1'
    # etime = '4'
    # var = '2t'
    # startLat = 0
    # endLat = 60
    # startLon = 70
    # endLon = 140
    # xdata_mean = get_ecweek_mean_data(dataInputPath, foreTime, stime, etime, var, startLat, endLat, startLon, endLon,"True")
    # xdata_ltm = get_ecweek_mean_data(ltmdataInputPath, foreTime, stime, etime, var, startLat, endLat, startLon, endLon, "True")
    # print(xdata_mean)
    # print(xdata_ltm)


