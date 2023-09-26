#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/07/09
# @Author : Shiys
# @File : DataLoaderUtils.py


import xarray as xr

import calendar,datetime
import os,logging
import numpy as np
from com.nriet.utils import DateUtils
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import FILE_NOT_FOUND_ERROR_CODE,DATA_OUT_OF_SCALE_CODE

class DataLoaderUtils:
    # 获取输入的月日是一年中的第几天
    def get_day_of_year(self, year, month, day):
        return int(datetime.datetime(year, month, day).strftime("%j"))

    # 解析BCC_CSM月数据
    def parse_bcccsm_raw_data(self, dataConfig, startTime, endTime):
        logging.info("parse_bcccsm_raw_data")
        # 获取源数据的输入位置
        dataInputPath = dataConfig.get("dataInputPath")
        # 加载文件
        ds = xr.open_dataset(dataInputPath)
        # 获取时间维
        time = ds['time'].values
        # 获取文件的开始时间
        nc_start_time = np.datetime_as_string(time[0])[0:8].replace('-', "")
        # 获取文件的结束时间
        nc_end_time = np.datetime_as_string(time[-1])[0:8].replace('-', "")
        if startTime > nc_end_time or endTime < nc_start_time:
           return None
        # 计算nc文件的所有时间
        nc_time_list = DateUtils.get_time_list([nc_start_time, nc_end_time], 'mon', "%Y%m")
        # 获取解析的开始时间在文件中的下标
        startIndex = nc_time_list.index(startTime)
        # 获取解析的结束时间在文件中的下标
        endIndex = nc_time_list.index(endTime)
        # 根据要素获取数据
        var_data = ds[dataConfig.get("var")]
        # logging.info(var_data)
        # 根据时间范围筛选数据
        var_data = var_data.isel(time=range(startIndex, endIndex + 1))
        # 重置时间维
        nc_time_list_int = list(np.asarray(nc_time_list, np.int))
        var_data['time'] = nc_time_list_int[startIndex:endIndex + 1]
        # logging.info(var_data)
        return var_data

    # 解析CPC月数据
    def parse_cpc_raw_data(self, dataConfig, startTime, endTime):
        logging.info("parse_cpc_raw_data")
        result_data = []
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                # 计算当月的天数
                monDays = calendar.monthrange(year, mon)[1]
                # 计算当月的起止日
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                # 计算当月的起止日在一年中的位置
                startDayIndex = self.get_day_of_year(year, mon, tmpStartDay)
                endDayIndex = self.get_day_of_year(year, mon, tmpEndDay)

                # 获取源数据的输入位置
                dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year))
                if os.path.exists(dataInputPath):
                    # 加载数据
                    ds = xr.open_dataset(dataInputPath)
                    data_all = ds[dataConfig.get("var")]
                    if startDayIndex > len(data_all.time.values):
                       continue
                    if endDayIndex > len(data_all.time.values):
                        continue
                        # endDayIndex = len(data_all.time.values)
                    # 筛选数据
                    data = data_all.isel(time=range(startDayIndex - 1, endDayIndex))
                    # 重置时间维的数值
                    tmp_start_time = str(year)+"{0:02d}".format(mon)+"{0:02d}".format(tmpStartDay)
                    tmp_end_time = str(year)+"{0:02d}".format(mon)+"{0:02d}".format(tmpEndDay)
                    data.time.values = list(np.asarray(DateUtils.get_time_list([tmp_start_time,tmp_end_time],"day"),np.int))
                    result_data.append(data)
        if len(result_data)==0:
           return None
        var_data = xr.concat(result_data, dim="time")
        return var_data

    # 读取CRA40日数据
    def parse_cra_raw_data_day(self, dataConfig, startTime, endTime):
        logging.info("parse_cra_raw_data_day")
        result_data = []
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            # logging.info(tmpStartMon,tmpEndMon)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                monDays = calendar.monthrange(year, mon)[1]
                # 计算当月的起止日
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                for day in range(tmpStartDay, tmpEndDay + 1):  # 循环日
                    ymd = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(day)
                    dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace(
                        "#YYYYMMDD#", ymd)
                    logging.info(dataInputPath)
                    if os.path.exists(dataInputPath):
                        ds = xr.open_dataset(dataInputPath, engine='pynio')
                        # logging.info(ds)
                        # 重置变量名和维的名称
                        if dataConfig.get("original").get("var"):
                            ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                        if dataConfig.get("original").get("level"):
                            ds = ds.rename({dataConfig.get("original").get("level"): "level"})
                            ds['level'] = ds['level'] * 0.01
                            ds['level'].attrs['units'] = "hPa"
                        if dataConfig.get("original").get("lat"):
                            ds = ds.rename({dataConfig.get("original").get("lat"): "lat"})
                        if dataConfig.get("original").get("lon"):
                            ds = ds.rename({dataConfig.get("original").get("lon"): "lon"})
                        data = ds[dataConfig.get("var")]
                        data.expand_dims(dim="time", axis=0)
                        data["time"] = int(ymd)
                        result_data.append(data)
        if len(result_data) == 0:
           return None
        var_data = xr.concat(result_data, dim="time")
        return var_data

    # 读取CRA40月数据
    def parse_cra_raw_data_mon(self, dataConfig, startTime, endTime):
        logging.info("parse_cra_raw_data_mon")
        result_data = []
        # 计算开始年 开始月
        startYear, startMon = int(str(startTime)[0:4]), int(str(startTime)[4:6])
        # 计算结束年 结束月
        endYear, endMon = int(str(endTime)[0:4]), int(str(endTime)[4:6])
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon+1):
                ym = str(year)+"{0:02d}".format(mon)
                # logging.info(ym)
                dataInputPath =  dataConfig.get("dataInputPath").replace("#YYYY#",str(year)).replace("#YYYYMM#",ym)
                if os.path.exists(dataInputPath):
                    ds = xr.open_dataset(dataInputPath, engine='pynio')
                    # 重置变量名和维的名称
                    if dataConfig.get("original").get("var"):
                        ds = ds.rename({ dataConfig.get("original").get("var"): dataConfig.get("var")})
                    if dataConfig.get("original").get("level"):
                        ds = ds.rename({ dataConfig.get("original").get("level"): "level"})
                        ds['level'] = ds['level']*0.01
                        ds['level'].attrs['units'] = "hPa"
                        # logging.info(ds['level'])
                        # exit()
                    if dataConfig.get("original").get("lat"):
                        ds = ds.rename({dataConfig.get("original").get("lat"): "lat"})
                    if dataConfig.get("original").get("lon"):
                        ds = ds.rename({dataConfig.get("original").get("lon"): "lon"})
                    data = ds[dataConfig.get("var")]
                    data.expand_dims(dim="time", axis=0)
                    data["time"] = int(ym)
                    result_data.append(data)
        if len(result_data) == 0:
            return None
        var_data = xr.concat(result_data, dim="time")
        return var_data

    # 解析规整后的月尺度数据
    def parse_month_regular_data(self, dataConfig, startTime, endTime):
        # 获取起止年、月
        startYear, startMon = int(startTime[0:4]), int(startTime[4:6])
        endYear, endMon = int(endTime[0:4]), int(endTime[4:6])
        res_get_data_list = []
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            dataInputFile = dataConfig.get("dataInputPath").replace("#YYYY#", str(year))
            if os.path.exists(dataInputFile):
                ds = xr.open_dataset(dataInputFile)
                var_data = ds[dataConfig.get("var")]
                # 重置时间维属性
                st = year * 100 + 1
                et = year * 100 + 12
                file_time = DateUtils.get_time_list([st, et], "mon")
                # logging.info(file_time)
                var_data['time'] = file_time
                # 截取时间维
                data = var_data.isel(time=range(tmpStartMon - 1, tmpEndMon))
                res_get_data_list.append(data)
        if len(res_get_data_list) == 0:
               return None
        var_data = xr.concat(res_get_data_list, dim="time")
        return var_data