#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/03/09
# @Author : shiys
# @File : GridDataUtils.py


import os
import xarray as xr
import numpy as np
import calendar

from com.nriet.config.ResponseCodeAndMsgEum import FILE_NOT_FOUND_ERROR_CODE
from com.nriet.utils import DateUtils
import logging
logger = logging.getLogger(__name__)
logger.root.setLevel(level=logging.INFO)
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException


class GridDataUtils:
    # 根据指定的经纬度范围和层次裁剪数据
    def partitioned_data(self, par_data,regions,level):
        nc_data = par_data
        if level is not None and level !="":
            if not level.__contains__(","):
                level = level + "," + level
            start_level, end_level = [float(level) for level in level.split(",")]
            level = par_data["level"]
            level = level[(level >= start_level) & (level <= end_level)]
            nc_data = nc_data.sel(level=level)
        if regions is not None:
            start_lon, end_lon, start_lat, end_lat = [float(region) for region in regions.split(",")]
            lon = par_data["lon"]
            lat = par_data["lat"]
            lon = lon[(lon >= start_lon) & (lon <= end_lon)]
            lat = lat[(lat >= start_lat) & (lat <= end_lat)]
            nc_data = nc_data.sel(lon=lon, lat=lat)
        return nc_data

    # 根据时间维补全数据
    def makeup_data_by_time(self, acquired_data, startTime, endTime,timeType):
        request_time_list = DateUtils.get_time_list([startTime,endTime],timeType)
        acquired_time_list = acquired_data.time.values
        time_diff_list = list(set(request_time_list).difference(set(acquired_time_list)))
        if len(time_diff_list) != 0:
            # logging.info("xxxxxxxxxxxxxxx")
            result_data_want = acquired_data
            want_dims = result_data_want.dims
            want_shape = list(result_data_want.shape)
            want_coords = []
            for ii, dm in enumerate(want_dims):
                if dm == "time":
                    want_shape[ii] = len(time_diff_list)
                    want_coords.append(time_diff_list)
                else:
                    want_coords.append(result_data_want[dm])
            result_data_m = xr.DataArray(np.full(want_shape, np.nan, dtype=np.float32), coords=want_coords,
                                         dims=want_dims)
            tmp_result_data = xr.concat([result_data_want, result_data_m], dim="time")
            # 前冬排序特殊处理 04改为00进行排序
            if timeType == "season":
                sort_time = []
                sort_time_tmp = tmp_result_data.time.values
                for ii,s_time in enumerate(sort_time_tmp):
                    if s_time[4:6] == '04':
                        sort_time.append(s_time[0:4]+"00")
                    else:
                        sort_time.append(s_time)
            else:
                sort_time = tmp_result_data.time.values
            # 将合并后的数据按时间进行排序，重新整合数据
            b = sorted(enumerate(sort_time), key=lambda x: x[1])
            time_index = [x[0] for x in b]
            tmp_result_data = tmp_result_data.isel(time=time_index)
        else:
            tmp_result_data = acquired_data
        return  tmp_result_data
    # 获取格点实况数据  日尺度
    def get_day_mean_data(self,dataInputPath, timeType, startTime, endTime, var, regions, level):
        # 获取起止年、月、日
        startYear, startMon, startDay = int(startTime[0:4]), int(startTime[4:6]), int(startTime[6:8])
        endYear, endMon, endDay = int(endTime[0:4]), int(endTime[4:6]), int(endTime[6:8])
        res_get_data_list = []
        nofile_list = []
        for year in range(startYear,endYear+1):    #循环年份
            # 计算当年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon+1):   # 循环月份
                mon_days = calendar.monthrange(year, mon)[1]  # 计算当前月的总天数
                # 计算当前月的起止日
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, mon_days)
                yyyy_mm = str(year)+"_{0:02d}".format(mon)
                dataInputFile = dataInputPath + str(year) + "_{0:02d}".format(mon) + ".nc"
                if os.path.exists(dataInputFile):
                    ds = xr.open_dataset(dataInputFile,decode_times=False,cache=False)
                    var_data = ds[var]
                    if mon == 2 and not calendar.isleap(year):
                        var_data = var_data[:28,...]

                    # 重置时间维属性
                    st = year * 10000 + mon * 100 + 1
                    et = year * 10000 + mon * 100 + mon_days
                    file_time = DateUtils.get_time_list([st, et], timeType)
                    if len(file_time) != len(var_data['time']):
                        var_data = var_data.isel(time=range(1,29))
                    var_data['time'] = file_time
                    # 截取时间维
                    data = var_data.isel(time=range(tmpStartDay-1,tmpEndDay))
                    # logging.info(data)
                    #
                    # 根据经纬度范围及高度层截取数据
                    data = self.partitioned_data(data,regions,level)
                    res_get_data_list.append(data)
                else:
                    nofile_list.append(dataInputFile)
                    logging.info("file [%s] does not exist!" % dataInputFile)
        if len(res_get_data_list) !=0:
            result_data = xr.concat(res_get_data_list, dim="time")
            # 补全数据
            result_data = self.makeup_data_by_time(result_data, startTime, endTime, timeType)
        else:
            result_data = None
            error_str = "file [%s] does not exist!" % ",".join(nofile_list)
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        return result_data

    # 获取格点实况数据  候尺度
    def get_five_mean_data(self, dataInputPath, timeType, startTime, endTime, var, regions, level):
        # 获取起止年、月、候
        startYear, startMon, startFive = int(startTime[0:4]), int(startTime[4:6]), int(startTime[6:8])
        endYear, endMon, endFive = int(endTime[0:4]), int(endTime[4:6]), int(endTime[6:8])
        res_get_data_list = []
        nofile_list = []
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当年的起止候
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpStartFive = np.where(year == startYear and tmpStartMon == startMon, startFive, 1)
            startFiveIndex = (tmpStartMon - 1) * 6 + tmpStartFive
            tmpEndMon = np.where(year == endYear, endMon, 12)
            tmpEndFive = np.where(year == endYear and tmpEndMon == endMon, endFive, 6)
            endFiveIndex = (tmpEndMon - 1) * 6 + tmpEndFive
            # logging.info(year, tmpStartMon, tmpStartFive, startFiveIndex)
            # logging.info(year, tmpEndMon, tmpEndFive, endFiveIndex)
            # exit()
            dataInputFile = dataInputPath + str(year) + ".nc"
            if os.path.exists(dataInputFile):
                ds = xr.open_dataset(dataInputFile,decode_times=False,cache=False)
                var_data = ds[var]
                # 重置时间维属性
                st = year * 10000 + 1 * 100 + 1
                et = year * 10000 + 12 * 100 + 6
                file_time = DateUtils.get_time_list([st, et], timeType)
                # logging.info(file_time)
                var_data['time'] = file_time
                # 截取时间维
                data = var_data.isel(time=range(startFiveIndex - 1, endFiveIndex))
                # 根据经纬度范围及高度层截取数据
                data = self.partitioned_data(data, regions, level)
                res_get_data_list.append(data)
            else:
                nofile_list.append(dataInputFile)
                logging.info("file [%s] does not exist!" % dataInputFile)
        if len(res_get_data_list) != 0:
            result_data = xr.concat(res_get_data_list, dim="time")
            # 补全数据
            result_data = self.makeup_data_by_time(result_data, startTime, endTime, timeType)
        else:
            result_data = None
            error_str = "file [%s] does not exist!" % ",".join(nofile_list)
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        return result_data
    # 获取格点实况数据  旬尺度
    def get_ten_mean_data(self, dataInputPath, timeType, startTime, endTime, var, regions, level):
        # 获取起止年、月、旬
        startYear, startMon, startTen = int(startTime[0:4]), int(startTime[4:6]), int(startTime[6:8])
        endYear, endMon, endTen = int(endTime[0:4]), int(endTime[4:6]), int(endTime[6:8])
        res_get_data_list = []
        nofile_list = []
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当年的起止旬
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpStartTen = np.where(year == startYear and tmpStartMon == startMon, startTen, 1)
            startTenIndex = (tmpStartMon - 1) * 3 + tmpStartTen
            tmpEndMon = np.where(year == endYear, endMon, 12)
            tmpEndTen = np.where(year == endYear and tmpEndMon == endMon, endTen, 3)
            endTenIndex = (tmpEndMon - 1) * 3 + tmpEndTen
            # logging.info(year,tmpStartMon,tmpStartTen,startTenIndex)
            # logging.info(year,tmpEndMon,tmpEndTen,endTenIndex)
            # exit()
            dataInputFile = dataInputPath + str(year) + ".nc"
            if os.path.exists(dataInputFile):
                with xr.open_dataset(dataInputFile,decode_times=False,cache=False) as ds:
                    var_data = ds[var]
                    # 重置时间维属性
                    st = year * 10000 + 1 * 100 + 1
                    et = year * 10000 + 12 * 100 + 3
                    file_time = DateUtils.get_time_list([st, et], timeType)
                    # logging.info(file_time)
                    var_data['time'] = file_time
                    # 截取时间维
                    data = var_data.isel(time=range(startTenIndex - 1, endTenIndex))
                    # 根据经纬度范围及高度层截取数据
                    data = self.partitioned_data(data, regions, level)
                    res_get_data_list.append(data)
            else:
                nofile_list.append(dataInputFile)
                logging.info("file [%s] does not exist!" % dataInputFile)
        if len(res_get_data_list) != 0:
            result_data = xr.concat(res_get_data_list, dim="time")
            # 补全数据
            result_data = self.makeup_data_by_time(result_data, startTime, endTime, timeType)
        else:
            result_data = None
            error_str = "file [%s] does not exist!" % ",".join(nofile_list)
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        return result_data
    # 获取格点实况数据  月尺度
    def get_mon_mean_data(self, dataInputPath, timeType, startTime, endTime, var, regions, level):
        # 获取起止年、月
        startYear, startMon = int(startTime[0:4]), int(startTime[4:6])
        endYear, endMon = int(endTime[0:4]), int(endTime[4:6])
        res_get_data_list = []
        nofile_list = []
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            dataInputFile = dataInputPath + str(year) + ".nc"
            if os.path.exists(dataInputFile):
                with xr.open_dataset(dataInputFile,decode_times=False,cache=False) as ds:
                    var_data = ds[var]
                    # 重置时间维属性
                    st = year * 100 + 1
                    et = year * 100 + 12
                    file_time = DateUtils.get_time_list([st, et], timeType)
                    # logging.info(file_time)
                    var_data['time'] = file_time
                    # 截取时间维
                    data = var_data.isel(time=range(tmpStartMon - 1, tmpEndMon))
                    # 根据经纬度范围及高度层截取数据
                    data = self.partitioned_data(data, regions, level)
                    res_get_data_list.append(data)
            else:
                nofile_list.append(dataInputFile)
                logging.info("file [%s] does not exist!" % dataInputFile)
        if len(res_get_data_list) != 0:
            result_data = xr.concat(res_get_data_list, dim="time")
            # 补全数据
            result_data = self.makeup_data_by_time(result_data, startTime, endTime, timeType)
        else:
            result_data = None
            error_str = "file [%s] does not exist!" % ",".join(nofile_list)
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        return result_data

    # 获取格点实况数据  国际候尺度 （胡玉恒 20201106添加）
    def get_fiveYear_mean_data(self, dataInputPath, timeType, startTime, endTime, var, regions, level):
        logging.info(dataInputPath)
        if not os.path.exists(dataInputPath):
            dataInputPath = dataInputPath.replace(timeType,"five")
            logging.info(dataInputPath)
        # 获取起止年、月
        startYear, startFive = int(startTime[0:4]), int(startTime[4:6])
        endYear, endFive = int(endTime[0:4]), int(endTime[4:6])
        res_get_data_list = []
        nofile_list = []
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当年的起止月份
            tmpStartFive = np.where(year == startYear, startFive, 1)
            tmpEndFive = np.where(year == endYear, endFive, 73)
            dataInputFile = dataInputPath + str(year) + ".nc"
            if os.path.exists(dataInputFile):
                with xr.open_dataset(dataInputFile,decode_times=False,cache=False) as ds:
                    var_data = ds[var]
                    # 重置时间维属性
                    st = year * 100 + 1
                    et = year * 100 + 73
                    # file_time = np.arange(st,et+1)
                    # file_time = file_time.tolist()
                    file_time = DateUtils.get_time_list([st, et], timeType)
                    var_data['time'] = file_time
                    # 截取时间维
                    data = var_data.isel(time=range(tmpStartFive - 1, tmpEndFive))
                    # 根据经纬度范围及高度层截取数据
                    data = self.partitioned_data(data, regions, level)
                    res_get_data_list.append(data)
            else:
                nofile_list.append(dataInputFile)
                logging.info("file [%s] does not exist!" % dataInputFile)
        if len(res_get_data_list) != 0:
            result_data = xr.concat(res_get_data_list, dim="time")
            # 补全数据( 此部分未完善 )
            result_data = self.makeup_data_by_time(result_data, startTime, endTime, timeType)
        else:
            result_data = None
            error_str = "file [%s] does not exist!" % ",".join(nofile_list)
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        return result_data

    # 获取格点实况数据  季尺度
    def get_season_mean_data(self, dataInputPath, timeType, startTime, endTime, var, regions, level):
        # 获取起止年、月
        startYear, startSeason = int(startTime[0:4]), int(startTime[4:6])
        endYear, endSeason = int(endTime[0:4]), int(endTime[4:6])
        res_get_data_list = []
        nofile_list = []
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当年的起止季
            tmpStartSeason = np.where(year == startYear, startSeason, 4)
            if tmpStartSeason == 4:
                tmpStartSeason = 0
            tmpEndSeason = np.where(year == endYear, endSeason, 3)
            if tmpEndSeason == 4:
                tmpEndSeason = 0
            # logging.info(tmpStartSeason,tmpEndSeason)
            dataInputFile = dataInputPath + str(year) + ".nc"
            if os.path.exists(dataInputFile):
                with xr.open_dataset(dataInputFile,decode_times=False,cache=False) as ds:
                    var_data = ds[var]
                    # 重置时间维属性
                    st = year * 100 + 4
                    et = year * 100 + 3
                    file_time_t = DateUtils.get_time_list([st, et], timeType)
                    b = sorted(enumerate(file_time_t), key=lambda x: x[1])
                    file_time = [x[1] for x in b]
                    var_data['time'] = file_time
                    # 截取时间维
                    data = var_data.isel(time=range(tmpStartSeason - 1, tmpEndSeason))
                    # 根据经纬度范围及高度层截取数据
                    data = self.partitioned_data(data, regions, level)
                    res_get_data_list.append(data)
            else:
                nofile_list.append(dataInputFile)
                logging.info("file [%s] does not exist!" % dataInputFile)
        if len(res_get_data_list) != 0:
            result_data = xr.concat(res_get_data_list, dim="time")
            # 补全数据
            result_data = self.makeup_data_by_time(result_data, startTime, endTime, timeType)
        else:
            result_data = None
            error_str = "file [%s] does not exist!" % ",".join(nofile_list)
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        return result_data

    # 获取格点实况数据  年尺度
    def get_year_mean_data(self, dataInputPath, timeType, startTime, endTime, var, regions, level):
        # 获取起止年
        startYear = int(startTime[0:4])
        endYear = int(endTime[0:4])
        res_get_data_list = []
        nofile_list = []
        for year in range(startYear, endYear + 1):  # 循环年份
            dataInputFile = dataInputPath + str(year) + ".nc"
            if os.path.exists(dataInputFile):
                with xr.open_dataset(dataInputFile,decode_times=False,cache=False) as ds:
                    data = ds[var]
                    # 重置时间维属性
                    data['time'] = [str(year)]
                    # 根据经纬度范围及高度层截取数据
                    data = self.partitioned_data(data, regions, level)
                    res_get_data_list.append(data)
            else:
                nofile_list.append(dataInputFile)
                logging.info("file [%s] does not exist!" % dataInputFile)
        if len(res_get_data_list) != 0:
            result_data = xr.concat(res_get_data_list, dim="time")
            # 补全数据
            result_data = self.makeup_data_by_time(result_data, startTime, endTime, timeType)
        else:
            result_data = None
            error_str = "file [%s] does not exist!" % ",".join(nofile_list)
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        return result_data
    # 获取格点实况数据
    def get_grid_mean_data(self,dataInputPath, timeType, startTime, endTime, var, regions, level):
        # 判断文件是否存在
        if timeType == "day":
           grid_data =  self.get_day_mean_data(dataInputPath, timeType, startTime, endTime, var, regions, level)
        if timeType == "five":
           grid_data =  self.get_five_mean_data(dataInputPath, timeType, startTime, endTime, var, regions, level)
        if timeType == "ten":
           grid_data =  self.get_ten_mean_data(dataInputPath, timeType, startTime, endTime, var, regions, level)
        if timeType == "mon":
           grid_data =  self.get_mon_mean_data(dataInputPath, timeType, startTime, endTime, var, regions, level)
        if timeType == "fiveYear":
           grid_data =  self.get_fiveYear_mean_data(dataInputPath, timeType, startTime, endTime, var, regions, level)
        if timeType == "season":
            grid_data = self.get_season_mean_data(dataInputPath, timeType, startTime, endTime, var, regions, level)
        if timeType == "year":
            grid_data = self.get_year_mean_data(dataInputPath, timeType, startTime, endTime, var, regions, level)
        return grid_data

    # 获取格点常年值数据  日尺度
    def get_day_ltm_data(self, dataInputPath, timeType, startTime, endTime, var, regions, level, climateYear):
        # 获取起止年、月、日
        startYear, startMon, startDay = int(startTime[0:4]), int(startTime[4:6]), int(startTime[6:8])
        endYear, endMon, endDay = int(endTime[0:4]), int(endTime[4:6]), int(endTime[6:8])
        file_md = DateUtils.get_time_list([20000101, 20001231], timeType)
        file_md_int = np.asarray(file_md,dtype=np.int)
        file_md_int  = file_md_int - 2000*10000
        res_get_data_list = []
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当年的起止候
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpStartDay = np.where(year == startYear and tmpStartMon == startMon, startDay, 1)
            tmpStartTime = str(year)+"{0:02d}".format(tmpStartMon)+"{0:02d}".format(tmpStartDay)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            tmpEndtDay = np.where(year == endYear and tmpEndMon == endMon, endDay, calendar.monthrange(year, tmpEndMon)[1])
            tmpEndTime = str(year) + "{0:02d}".format(tmpEndMon) + "{0:02d}".format(tmpEndtDay)
            now_time = DateUtils.get_time_list([tmpStartTime,tmpEndTime], timeType)
            dataInputFile = dataInputPath + timeType + "_" + climateYear + ".nc"
            if os.path.exists(dataInputFile):
                with xr.open_dataset(dataInputFile,decode_times=False,cache=False) as ds:
                    var_data = ds[var]
                    # 重置时间维属性
                    file_time = year * 10000 + file_md_int
                    file_time =  [str(i) for i in file_time]
                    var_data['time'] = file_time
                    # 截取时间维
                    data = var_data.sel(time=now_time)
                    # 根据经纬度范围及高度层截取数据
                    data = self.partitioned_data(data, regions, level)
                    res_get_data_list.append(data)
            else:
                error_str = "file [%s] does not exist!" % dataInputFile
                raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        if len(res_get_data_list) != 0:
            result_data = xr.concat(res_get_data_list, dim="time")
            # 补全数据
            result_data = self.makeup_data_by_time(result_data, startTime, endTime, timeType)
        else:
            result_data = None
        return result_data
    # 获取格点常年值数据  候尺度
    def get_five_ltm_data(self, dataInputPath, timeType, startTime, endTime, var, regions, level, climateYear):
        # 获取起止年、月、候
        startYear, startMon, startFive = int(startTime[0:4]), int(startTime[4:6]), int(startTime[6:8])
        endYear, endMon, endFive = int(endTime[0:4]), int(endTime[4:6]), int(endTime[6:8])
        res_get_data_list = []
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当年的起止候
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpStartFive = np.where(year == startYear and tmpStartMon == startMon, startFive, 1)
            startFiveIndex = (tmpStartMon - 1) * 6 + tmpStartFive
            tmpEndMon = np.where(year == endYear, endMon, 12)
            tmpEndFive = np.where(year == endYear and tmpEndMon == endMon, endFive, 6)
            endFiveIndex = (tmpEndMon - 1) * 6 + tmpEndFive
            dataInputFile = dataInputPath + timeType + "_" + climateYear + ".nc"
            if os.path.exists(dataInputFile):
                with xr.open_dataset(dataInputFile,decode_times=False,cache=False) as ds:
                    var_data = ds[var]
                    # 重置时间维属性
                    st = year * 10000 + 1 * 100 + 1
                    et = year * 10000 + 12 * 100 + 6
                    file_time = DateUtils.get_time_list([st, et], timeType)
                    # logging.info(file_time)
                    var_data['time'] = file_time
                    # 截取时间维
                    data = var_data.isel(time=range(startFiveIndex - 1, endFiveIndex))
                    # 根据经纬度范围及高度层截取数据
                    data = self.partitioned_data(data, regions, level)
                    res_get_data_list.append(data)
            else:
                error_str = "file [%s] does not exist!" % dataInputFile
                raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        if len(res_get_data_list) != 0:
            result_data = xr.concat(res_get_data_list, dim="time")
            # 补全数据
            result_data = self.makeup_data_by_time(result_data, startTime, endTime, timeType)
        else:
            result_data = None
        return result_data

    # 获取格点常年值数据  国际候尺度
    def get_fiveYear_ltm_data(self, dataInputPath, timeType, startTime, endTime, var, regions, level, climateYear):
        dataInputFile = dataInputPath + timeType + "_" + climateYear + ".nc"
        if not os.path.exists(dataInputFile):
            dataInputFile = dataInputFile.replace(timeType, "five")
        # 获取起止年、月、候
        startYear, startFive = int(startTime[0:4]), int(startTime[4:6])
        endYear, endFive = int(endTime[0:4]), int(endTime[4:6])
        res_get_data_list = []
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当年的起止候
            tmpStartFive = np.where(year == startYear, startFive, 1)
            tmpEndFive = np.where(year == endYear, endFive, 73)
            if os.path.exists(dataInputFile):
                with xr.open_dataset(dataInputFile,decode_times=False,cache=False) as ds:
                    var_data = ds[var]
                    # 重置时间维属性
                    st = year * 100 + 1
                    et = year * 100 + 73
                    # file_time = np.arange(st, et + 1)
                    # file_time = file_time.tolist()
                    file_time = DateUtils.get_time_list([st, et], timeType)
                    # logging.info(file_time)
                    var_data['time'] = file_time
                    # 截取时间维
                    data = var_data.isel(time=range(tmpStartFive - 1, tmpEndFive))
                    # 根据经纬度范围及高度层截取数据
                    data = self.partitioned_data(data, regions, level)
                    res_get_data_list.append(data)
            else:
                error_str = "file [%s] does not exist!" % dataInputFile
                raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        if len(res_get_data_list) != 0:
            result_data = xr.concat(res_get_data_list, dim="time")
            # 补全数据
            result_data = self.makeup_data_by_time(result_data, startTime, endTime, timeType)
        else:
            result_data = None
        return result_data
    # 获取格点实况数据  旬尺度
    def get_ten_ltm_data(self, dataInputPath, timeType, startTime, endTime, var, regions, level, climateYear):
        # 获取起止年、月、旬
        startYear, startMon, startTen = int(startTime[0:4]), int(startTime[4:6]), int(startTime[6:8])
        endYear, endMon, endTen = int(endTime[0:4]), int(endTime[4:6]), int(endTime[6:8])
        res_get_data_list = []
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当年的起止旬
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpStartTen = np.where(year == startYear and tmpStartMon == startMon, startTen, 1)
            startTenIndex = (tmpStartMon - 1) * 3 + tmpStartTen
            tmpEndMon = np.where(year == endYear, endMon, 12)
            tmpEndTen = np.where(year == endYear and tmpEndMon == endMon, endTen, 3)
            endTenIndex = (tmpEndMon - 1) * 3 + tmpEndTen
            dataInputFile = dataInputPath + timeType + "_" + climateYear + ".nc"
            if os.path.exists(dataInputFile):
                with xr.open_dataset(dataInputFile,decode_times=False,cache=False) as ds:
                    var_data = ds[var]
                    # 重置时间维属性
                    st = year * 10000 + 1 * 100 + 1
                    et = year * 10000 + 12 * 100 + 3
                    file_time = DateUtils.get_time_list([st, et], timeType)
                    # logging.info(file_time)
                    var_data['time'] = file_time
                    # 截取时间维
                    data = var_data.isel(time=range(startTenIndex - 1, endTenIndex))
                    # 根据经纬度范围及高度层截取数据
                    data = self.partitioned_data(data, regions, level)
                    res_get_data_list.append(data)
            else:
                error_str = "file [%s] does not exist!" % dataInputFile
                raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        if len(res_get_data_list) != 0:
            result_data = xr.concat(res_get_data_list, dim="time")
            # 补全数据
            result_data = self.makeup_data_by_time(result_data, startTime, endTime, timeType)
        else:
            result_data = None
        return result_data
    # 获取格点常年值数据  月尺度
    def get_mon_ltm_data(self, dataInputPath, timeType, startTime, endTime, var, regions, level, climateYear):
        # 获取起止年、月
        startYear, startMon = int(startTime[0:4]), int(startTime[4:6])
        endYear, endMon = int(endTime[0:4]), int(endTime[4:6])
        res_get_data_list = []
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            dataInputFile = dataInputPath + timeType + "_" + climateYear + ".nc"
            if os.path.exists(dataInputFile):
                with xr.open_dataset(dataInputFile, decode_times=False, cache=False) as ds:
                    var_data = ds[var]
                    # 重置时间维属性
                    st = year * 100 + 1
                    et = year * 100 + 12
                    file_time = DateUtils.get_time_list([st, et], timeType)
                    # logging.info(file_time)
                    var_data['time'] = file_time
                    # 截取时间维
                    data = var_data.isel(time=range(tmpStartMon - 1, tmpEndMon))
                    # 根据经纬度范围及高度层截取数据
                    data = self.partitioned_data(data, regions, level)
                    res_get_data_list.append(data)
            else:
                error_str = "file [%s] does not exist!" % dataInputFile
                raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        if len(res_get_data_list) != 0:
            result_data = xr.concat(res_get_data_list, dim="time")
            # 补全数据
            result_data = self.makeup_data_by_time(result_data, startTime, endTime, timeType)
        else:
            result_data = None
        return result_data
    # 获取格点常年值数据  季尺度
    def get_season_ltm_data(self, dataInputPath, timeType, startTime, endTime, var, regions, level, climateYear):
        # 获取起止年、月
        startYear, startSeason = int(startTime[0:4]), int(startTime[4:6])
        endYear, endSeason = int(endTime[0:4]), int(endTime[4:6])
        res_get_data_list = []
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当年的起止季
            tmpStartSeason = np.where(year == startYear, startSeason, 4)
            if tmpStartSeason == 4:
                tmpStartSeason = 0
            tmpEndSeason = np.where(year == endYear, endSeason, 3)
            if tmpEndSeason == 4:
                tmpEndSeason = 0
            # logging.info(tmpStartSeason,tmpEndSeason)
            dataInputFile = dataInputPath + timeType + "_" + climateYear + ".nc"
            if os.path.exists(dataInputFile):
                with xr.open_dataset(dataInputFile,decode_times=False,cache=False) as ds:
                    var_data = ds[var]
                    # 重置时间维属性
                    st = year * 100 + 4
                    et = year * 100 + 3
                    file_time_t = DateUtils.get_time_list([st, et], timeType)
                    b = sorted(enumerate(file_time_t), key=lambda x: x[1])
                    file_time = [x[1] for x in b]
                    var_data['time'] = file_time
                    # 截取时间维
                    data = var_data.isel(time=range(tmpStartSeason - 1, tmpEndSeason))
                    # logging.info(data)
                    # 根据经纬度范围及高度层截取数据
                    data = self.partitioned_data(data, regions, level)
                    res_get_data_list.append(data)
            else:
                error_str = "file [%s] does not exist!" % dataInputFile
                raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        if len(res_get_data_list) != 0:
            result_data = xr.concat(res_get_data_list, dim="time")
            # 补全数据
            result_data = self.makeup_data_by_time(result_data, startTime, endTime, timeType)
        else:
            result_data = None
        return result_data
    # 获取格点常年值数据  年尺度
    def get_year_ltm_data(self, dataInputPath, timeType, startTime, endTime, var, regions, level,climateYear):
        # 获取起止年
        startYear = int(startTime[0:4])
        endYear = int(endTime[0:4])
        res_get_data_list = []
        for year in range(startYear, endYear + 1):  # 循环年份
            dataInputFile = dataInputPath + timeType + "_" + climateYear + ".nc"
            if os.path.exists(dataInputFile):
                with xr.open_dataset(dataInputFile,decode_times=False,cache=False) as ds:
                    data = ds[var]
                    # 重置时间维属性
                    data['time'] = [str(year)]
                    # 根据经纬度范围及高度层截取数据
                    data = self.partitioned_data(data, regions, level)
                    res_get_data_list.append(data)
            else:
                error_str = "file [%s] does not exist!" % dataInputFile
                raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        if len(res_get_data_list) != 0:
            result_data = xr.concat(res_get_data_list, dim="time")
            # 补全数据
            result_data = self.makeup_data_by_time(result_data, startTime, endTime, timeType)
        else:
            result_data = None
        return result_data

    def get_grid_ltm_data(self,dataInputPath, timeType, startTime, endTime, var, regions, level,climateYear):
        # 判断文件是否存在
        if timeType == "day":
           grid_data = self.get_day_ltm_data(dataInputPath, timeType, startTime, endTime, var, regions, level,climateYear)
        if timeType == "five":
           grid_data = self.get_five_ltm_data(dataInputPath, timeType, startTime, endTime, var, regions, level,climateYear)
        if timeType == "fiveYear":
           grid_data = self.get_fiveYear_ltm_data(dataInputPath, timeType, startTime, endTime, var, regions, level,climateYear)
        if timeType == "ten":
           grid_data = self.get_ten_ltm_data(dataInputPath, timeType, startTime, endTime, var, regions, level,climateYear)
        if timeType == "mon":
           grid_data = self.get_mon_ltm_data(dataInputPath, timeType, startTime, endTime, var, regions, level,climateYear)
        if timeType == "season":
            grid_data = self.get_season_ltm_data(dataInputPath, timeType, startTime, endTime, var, regions, level,climateYear)
        if timeType == "year":
            grid_data = self.get_year_ltm_data(dataInputPath, timeType, startTime, endTime, var, regions, level,climateYear)
        return grid_data

    def is_leap_year(year):
        """
        能被4整除且不能被100整除；能被400整除
        """
        if year % 400 == 0:
            return True
        if year % 4 == 0 and year % 100 != 0:
            return True
        return False

# dataInputPath = "/nfsshare1/cdbdata/data/CPC/tmax/day/"
# # dataInputPath = "/nfsshare1/cdbdata/data/NCEPRA/pressure/uwnd/ltm/"
# climateYear = "1981-2010"
# timeType = "day"
# startTime = "20190201"
# endTime  = "20190301"
# var = "tmax"
# # var = "uwnd"
# regions = "0,180,0,90"
# level = ""
# gdUtils = GridDataUtils()
# # xx = gdUtils.get_grid_ltm_data(dataInputPath, timeType, startTime, endTime, var, regions, level, climateYear)
# xx = gdUtils.get_grid_mean_data(dataInputPath, timeType, startTime, endTime, var, regions, level)
#
# # logging.info(xx)
# if xx is None:
#     logging.info("aaaaaaaaaaaaaaaaa")
# else:
#     logging.info("bbbbbbbbbbbbbbbbbbbb")
#     logging.info(xx.time.values)