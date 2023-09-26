#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/07/09
# @Author : Shiys
# @File : DataMeanRegularUtils.py

import calendar
import datetime
import logging
import os
import re

import numpy as np
import pandas as pd
import scipy.interpolate
import xarray as xr
import math
from metpy.interpolate import remove_nan_observations
from scipy.interpolate import Rbf
# from xgrads import CtlDescriptor, open_CtlDataset

from com.nriet.config.ResponseCodeAndMsgEum import FILE_NOT_FOUND_ERROR_CODE, DATA_OUT_OF_SCALE_CODE, DATA_ALL_MISS_CODE
from com.nriet.utils import DateUtils
from com.nriet.utils.MathUtils import formatting_data
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.utils.fileUtils import convert_data, data_convert
from com.nriet.utils.result.ResponseResultUtils import build_response_dict


class DataMeanRegularUtils:

    # 生成netCDF文件
    def writ_nc(self, res_data, resVar, out_file_path, latlonType=None):
        # 判断输出目录是否存在，不存在就创建
        str_dir = os.path.dirname(out_file_path)
        # logging.info(out_file_path)
        if not os.path.exists(str_dir):
            os.makedirs(str_dir)
        # 判断输出文件是否存在，存在则删除
        if os.path.exists(out_file_path):
            os.remove(out_file_path)
        # 生成netCDF文件
        data_set = xr.Dataset({resVar: res_data})
        # 设置netcdf的数据属性
        encoding = {resVar: {'dtype': 'float32', '_FillValue': 999999.0},
                    "time": {'dtype': 'float64'}
                    }
        if latlonType:
            # logging.info(latlonType)
            encoding["lat"] = {'dtype': latlonType}
            encoding["lon"] = {'dtype': latlonType}
        logging.info("%s is ok" % out_file_path)
        data_set.to_netcdf(out_file_path, encoding=encoding)

    # 获取输入的月日是一年中的第几天
    def get_day_of_year(self, year, month, day):
        return int(datetime.datetime(year, month, day).strftime("%j"))

    # 根据时间维补全数据
    def makeup_data_by_time(self, acquired_data, want_time_list, res_data=None):
        # 已获取数据的时间维和想要的时间数组长度相等
        if len(acquired_data.time.values) == len(want_time_list):
            tmp_result_data = acquired_data
            # 按时间进行排序，重新整合数据
            b = sorted(enumerate(tmp_result_data.time.values), key=lambda x: x[1])
            time_index = [x[0] for x in b]
            tmp_result_data = tmp_result_data.isel(time=time_index)
        # 已获取数据的时间维大小 < 想要的时间数组长度
        if 0 < len(acquired_data.time.values) < len(want_time_list):
            result_data_want = acquired_data
            time_acquired_list = list(result_data_want.time.values)
            if res_data is not None:
                time_mon_list = list(res_data.time.values)
                time_diff_list = list(set(time_mon_list).difference(set(time_acquired_list)))
                result_data_m = res_data.sel(time=time_diff_list)
            else:
                time_diff_list = list(set(want_time_list).difference(set(time_acquired_list)))
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
            # logging.info(tmp_result_data)
            # 将合并后的数据按时间进行排序，重新整合数据
            b = sorted(enumerate(tmp_result_data.time.values), key=lambda x: x[1])
            time_index = [x[0] for x in b]
            tmp_result_data = tmp_result_data.isel(time=time_index)
        return tmp_result_data

    #
    def check_miss_data(self, grid_data):
        # 设置 缺测值为0,非缺测为1
        grid_data = xr.where(np.isnan(grid_data), 0, 1)
        # 统计求和的维
        dims = list(grid_data.dims)
        dims.remove("time")
        flag = len(np.where(grid_data.sum(dim=dims).values == 0)[0]) > 0
        return flag

    # 根据原始数据规整日数据(源数据是年文件)
    def regular_day_raw_data_single(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_day_raw_data_single")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
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
                # 获取数据输出的路径
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym)
                logging.info(dataOutputPath)
                # 若输出文件存在，则获取数据
                if os.path.exists(dataOutputPath):
                    ds_r = xr.open_dataset(dataOutputPath)
                    result_data = ds_r[dataConfig.get("var")]
                # 获取源数据的输入位置
                dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year))
                logging.info(dataInputPath)
                if os.path.exists(dataInputPath):
                    # 加载数据
                    ds = xr.open_dataset(dataInputPath)
                    # 重置变量名和维的名称
                    if dataConfig.get("original"):
                        if dataConfig.get("original").get("var"):
                            ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                    data_all = ds[dataConfig.get("var")]
                    # 单位转换
                    if dataConfig.get("unitConvert"):
                        data_all.attrs['units'] = dataConfig.get("unitConvert").get("unitName")
                        convert_type, convert_value = dataConfig.get("unitConvert").get("unitProc").split("_")
                        data_allx = convert_data(data_all, convert_type, convert_value)
                        data_allx.attrs = data_all.attrs
                        data_all = data_allx
                        logging.info(data_all.max().values)
                        if "valid_range" in data_all.attrs.keys():
                            data_all.attrs.pop('valid_range')
                        if "actual_range" in data_all.attrs.keys():
                            data_all.attrs.pop('actual_range')
                    # 处理插值
                    if dataConfig.get("interp"):
                        lats = dataConfig.get("interp").get("lats")
                        lons = dataConfig.get("interp").get("lons")
                        glon = np.linspace(lons[0], lons[1], lons[2], dtype=np.float32)
                        glat = np.linspace(lats[0], lats[1], lats[2], dtype=np.float32)
                        data_all = data_all.interp(lat=glat, lon=glon)

                    if startDayIndex > len(data_all.time.values):
                        currStartTime = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(tmpStartDay)
                        file_time_list = DateUtils.get_time_list([str(year) + "0101", str(year) + "1231"], "day")
                        fileEndTime = file_time_list[len(data_all.time.values) - 1]
                        error_str = "数据规整的开始时间[%s]大于源文件[%s]的结束时间[%s]" % (
                            DateUtils.time_format_ch(currStartTime, "day"), dataInputPath,
                            DateUtils.time_format_ch(fileEndTime, "day"))
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)
                            continue
                    if endDayIndex > len(data_all.time.values):
                        tmpEndDay = tmpEndDay - (endDayIndex - len(data_all.time.values))
                        endDayIndex = len(data_all.time.values)
                    # 筛选数据
                    data = data_all.isel(time=range(startDayIndex - 1, endDayIndex))
                    # logging.info(data)
                    # 重置时间维的数值
                    data.time.values = list(range(tmpStartDay, tmpEndDay + 1))
                    # 补全数据
                    if "result_data" in locals():
                        result_data = self.makeup_data_by_time(data, list(range(1, monDays + 1)), result_data)
                    else:
                        result_data = self.makeup_data_by_time(data, list(range(1, monDays + 1)))
                    # 判断结果数据是否存在，若存在就存储文件
                    if "result_data" in locals():
                        self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                        del result_data
                        file_num = file_num + 1
                else:
                    error_str = "源文件【%s】不存在!" % (dataInputPath)
                    if startTime == endTime:  # 同一时间点直接抛异常
                        raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                    else:
                        logging.error(error_str)
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 根据规整后的最高最低气温规整平均气温 日
    def regular_day_raw_data_single_tmp(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_day_raw_data_single_tmp")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
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
                # 获取数据输出的路径
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym)
                # 若输出文件存在，则获取数据
                if os.path.exists(dataOutputPath):
                    ds_r = xr.open_dataset(dataOutputPath)
                    result_data = ds_r[dataConfig.get("var")]
                # 获取源数据的输入位置
                dataInputPath_tmax = dataConfig.get("dataInputPath").replace("#YYYY_MM#", ym).replace("#V#", "tmax")
                dataInputPath_tmin = dataConfig.get("dataInputPath").replace("#YYYY_MM#", ym).replace("#V#", "tmin")
                if os.path.exists(dataInputPath_tmax) and os.path.exists(dataInputPath_tmin):
                    # 加载数据
                    ds_tmax = xr.open_dataset(dataInputPath_tmax)
                    data_tmax = ds_tmax["tmax"]
                    # 筛选数据
                    data_tmax = data_tmax.isel(time=range(tmpStartDay - 1, tmpEndDay))
                    # 加载数据
                    ds_tmin = xr.open_dataset(dataInputPath_tmin)
                    data_tmin = ds_tmin["tmin"]
                    # 筛选数据
                    data_tmin = data_tmin.isel(time=range(tmpStartDay - 1, tmpEndDay))
                    if startTime == endTime:  # 同一时间点直接抛异常
                        if np.isnan(data_tmax).all():
                            error_str = "源文件[%s]中%s的数据都是缺测值" % (
                                dataInputPath_tmax, DateUtils.time_format_ch(startTime, "day"))
                            raise AlgorithmException(response_code=DATA_ALL_MISS_CODE, response_msg=error_str)
                        if np.isnan(data_tmin).all():
                            error_str = "源文件[%s]中%s的数据都是缺测值" % (
                                dataInputPath_tmin, DateUtils.time_format_ch(startTime, "day"))
                            raise AlgorithmException(response_code=DATA_ALL_MISS_CODE, response_msg=error_str)
                    data = (data_tmax + data_tmin) / 2.0
                    # 重置时间维的数值
                    data.time.values = list(range(tmpStartDay, tmpEndDay + 1))
                    # 补全数据
                    if "result_data" in locals():
                        result_data = self.makeup_data_by_time(data, list(range(1, monDays + 1)), result_data)
                    else:
                        result_data = self.makeup_data_by_time(data, list(range(1, monDays + 1)))
                    # 判断结果数据是否存在，若存在就存储文件
                    if "result_data" in locals():
                        self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                        del result_data
                        file_num = file_num + 1
                else:
                    error_str = "源文件【%s】不存在!" % (dataInputPath_tmax + "," + dataInputPath_tmin)
                    if startTime == endTime:  # 同一时间点直接抛异常
                        raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                    else:
                        logging.error(error_str)
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 根据规整后的最低气温规整地面气温 日
    def regular_day_raw_data_single_tmin_0cm(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_day_raw_data_single_tmin_0cm")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                result_data_get = []
                # 计算当月的天数
                monDays = calendar.monthrange(year, mon)[1]
                # 计算当月的起止日
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)

                for day in range(tmpStartDay, tmpEndDay + 1):  # 循环日
                    # 获取源数据的输入位置
                    ymd = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(day)
                    dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYYMMDD#", ymd)
                    dataInputPath = dataConfig.get("dataInputPath").replace(
                        "#YYYYMMDD#", ymd).replace("#YYYY#", ymd[:4]).replace("#MM#", ymd[4:6])
                    if os.path.exists(dataInputPath):
                        # 加载数据
                        ds = xr.open_dataset(dataInputPath)
                        if dataConfig.get("original").get("var") not in ds.keys():
                            continue
                        if dataConfig.get("original").get("var"):
                            ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                        if dataConfig.get("original").get("lat"):
                            ds = ds.rename({dataConfig.get("original").get("lat"): "lat"})
                        if dataConfig.get("original").get("lon"):
                            ds = ds.rename({dataConfig.get("original").get("lon"): "lon"})
                        data_all = ds[dataConfig.get("var")]

                        # 站点信息
                        station_info = '/nfsshare/cdbdata/data/STATION/shuangdong/station_2305.txt'
                        data = pd.read_table(station_info, header=None, encoding='utf-8', sep="\t")
                        stationInfo = np.array(data)
                        locs = ['station', 'lon', 'lat']
                        stations = stationInfo[:, 0]
                        stationInfoData = xr.DataArray(stationInfo, coords=[stations, locs], dims=['station', 'space'])

                        # 插值
                        zlat = stationInfoData.sel(space='lat')
                        zlon = stationInfoData.sel(space='lon')
                        g2s_data = data_all.interp(lat=zlat, lon=zlon)
                        g2s_data = g2s_data - 273.15
                        g2s_data.attrs['units'] = 'degT'

                        # 温差
                        temp_diff_nc = '/nfsshare/cdbdata/data/STATION/shuangdong/all_station.nc'
                        temp_diff_data = xr.open_dataset(temp_diff_nc)
                        temp_diff_data = temp_diff_data['tmin_0cm'].sel({'time': int(ymd[4:6])})

                        # 插值+温差
                        result_data = g2s_data + temp_diff_data

                        if "result_data" in locals():
                            self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                            del result_data
                            file_num = file_num + 1
                    else:
                        error_str = "源文件【%s】不存在!" % (dataInputPath)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)

        result_dict["file_num"] = str(file_num)
        return result_dict

    # 根据原始数据规整日数据(源数据是日文件、nc文件、文件名需要统配)
    def regular_day_raw_data_single_sic(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_day_raw_data_single_sic")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                result_data_get = []
                # 计算当月的天数
                monDays = calendar.monthrange(year, mon)[1]
                # 计算当月的起止日
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                # 获取数据输出的路径
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym)
                logging.info(dataOutputPath)
                # 若输出文件存在，则获取数据
                if os.path.exists(dataOutputPath):
                    ds_r = xr.open_dataset(dataOutputPath)
                    result_data = ds_r[dataConfig.get("var")]
                for day in range(tmpStartDay, tmpEndDay + 1):  # 循环日
                    ymd = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(day)
                    dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace("#YYYYMMDD#",
                                                                                                         ymd).replace(
                        "#YYYYMM#", ymd[:6])
                    # 文件名中包含时分秒，用#.*#
                    file_list = os.listdir(os.path.dirname(dataInputPath))
                    re_filename = os.path.basename(dataInputPath).replace('#.*#', '.*')
                    getfilename = [i for i in file_list if re.findall(re_filename, i)]
                    if len(getfilename) != 0:
                        dataInputPath = os.path.dirname(dataInputPath) + '/' + getfilename[0]

                    if os.path.exists(dataInputPath):
                        logging.info(dataInputPath)
                        ds = xr.open_dataset(dataInputPath)
                        # logging.info(ds)
                        # 重置变量名和维的名称
                        # logging.info(dataConfig.get("original").get("var")+"%%%%%"+dataInputPath)
                        if dataConfig.get("original").get("var") not in ds.keys():
                            continue
                        if dataConfig.get("original").get("var"):
                            ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                        if dataConfig.get("original").get("level"):
                            ds = ds.rename({dataConfig.get("original").get("level"): "level"})
                            if dataConfig.get("var") not in ["u100m", "v100m"]:
                                ds['level'] = ds['level'] * 0.01
                                ds['level'].attrs['units'] = "hPa"
                        if dataConfig.get("original").get("lat"):
                            ds = ds.rename({dataConfig.get("original").get("lat"): "lat"})
                        if dataConfig.get("original").get("lon"):
                            ds = ds.rename({dataConfig.get("original").get("lon"): "lon"})
                        data = ds[dataConfig.get("var")][0]
                        if dataConfig.get("original").get("levels"):
                            logging.info("只需要保留指定的高度层...")
                            data = data.sel(level=dataConfig.get("original").get("levels"))
                        # 单位转换
                        logging.info("原始数据的大小范围在%s~%s..." % (data.min().values, data.max().values))
                        if dataConfig.get("unitConvert"):
                            data.attrs['units'] = dataConfig.get("unitConvert").get("unitName")
                            convert_type, convert_value = dataConfig.get("unitConvert").get("unitProc").split("_")
                            logging.info("%s开始单位转换...转换公式为%s" % (
                                dataConfig.get("var"), [convert_type, convert_value]))
                            data_allx = convert_data(data, convert_type, convert_value)
                            data_allx.attrs = data.attrs
                            data = data_allx
                            logging.info("转换后的数据大小范围在%s~%s..." % (data.min().values, data.max().values))
                            logging.info(data.max().values)
                            if "valid_range" in data.attrs.keys():
                                data.attrs.pop('valid_range')
                            if "actual_range" in data.attrs.keys():
                                data.attrs.pop('actual_range')
                        # if dataConfig.get("var") in ["u100m","v100m"]:
                        # data = data.sel(lv_HTGL1=100)
                        # logging.info(data)
                        data.expand_dims(dim="time", axis=0)
                        data["time"] = day
                        result_data_get.append(data)
                    else:
                        error_str = "源文件【%s】不存在!" % (dataInputPath)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)

                if len(result_data_get) != 0:
                    data_a = xr.concat(result_data_get, dim="time")
                    # 补全数据
                    if "result_data" in locals():
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)), result_data)
                    else:
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)))
                # 判断结果数据是否存在，若存在就存储文件
                if "result_data" in locals():
                    self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                    del result_data
                    file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 根据原始数据规整日数据(源数据是日文件)
    def regular_day_raw_data_multiple(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_day_raw_data_multiple")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            # logging.info(tmpStartMon,tmpEndMon)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                result_data_get = []
                monDays = calendar.monthrange(year, mon)[1]
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym)
                logging.info(dataOutputPath)
                # 若输出文件存在，则获取数据
                if os.path.exists(dataOutputPath):
                    ds_r = xr.open_dataset(dataOutputPath)
                    # logging.info(ds_r)
                    result_data = ds_r[dataConfig.get("var")]
                # 计算当月的起止日
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                for day in range(tmpStartDay, tmpEndDay + 1):  # 循环日
                    ymd = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(day)
                    dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace("#YYYYMMDD#",
                                                                                                         ymd)
                    if os.path.exists(dataInputPath):
                        logging.info(dataInputPath)
                        ds = xr.open_dataset(dataInputPath, engine='pynio')
                        # logging.info(ds)
                        # 重置变量名和维的名称
                        # logging.info(dataConfig.get("original").get("var")+"%%%%%"+dataInputPath)
                        if dataConfig.get("original").get("var") not in ds.keys():
                            continue
                        if dataConfig.get("original").get("var"):
                            ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                        if dataConfig.get("original").get("level"):
                            ds = ds.rename({dataConfig.get("original").get("level"): "level"})
                            if dataConfig.get("var") not in ["u100m", "v100m"]:
                                ds['level'] = ds['level'] * 0.01
                                ds['level'].attrs['units'] = "hPa"
                        if dataConfig.get("original").get("lat"):
                            ds = ds.rename({dataConfig.get("original").get("lat"): "lat"})
                        if dataConfig.get("original").get("lon"):
                            ds = ds.rename({dataConfig.get("original").get("lon"): "lon"})
                        data = ds[dataConfig.get("var")]
                        if dataConfig.get("original").get("levels"):
                            logging.info("只需要保留指定的高度层...")
                            data = data.sel(level=dataConfig.get("original").get("levels"))
                        # 单位转换
                        logging.info("原始数据的大小范围在%s~%s..." % (data.min().values, data.max().values))
                        if dataConfig.get("unitConvert"):
                            data.attrs['units'] = dataConfig.get("unitConvert").get("unitName")
                            convert_type, convert_value = dataConfig.get("unitConvert").get("unitProc").split("_")
                            logging.info("%s开始单位转换...转换公式为%s" % (
                                dataConfig.get("var"), [convert_type, convert_value]))
                            data_allx = convert_data(data, convert_type, convert_value)
                            data_allx.attrs = data.attrs
                            data = data_allx
                            logging.info("转换后的数据大小范围在%s~%s..." % (data.min().values, data.max().values))
                            logging.info(data.max().values)
                            if "valid_range" in data.attrs.keys():
                                data.attrs.pop('valid_range')
                            if "actual_range" in data.attrs.keys():
                                data.attrs.pop('actual_range')
                        # if dataConfig.get("var") in ["u100m","v100m"]:
                        # data = data.sel(lv_HTGL1=100)
                        # logging.info(data)
                        data.expand_dims(dim="time", axis=0)
                        data["time"] = day
                        result_data_get.append(data)
                    else:
                        error_str = "源文件【%s】不存在!" % (dataInputPath)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)

                if len(result_data_get) != 0:
                    data_a = xr.concat(result_data_get, dim="time")
                    # 补全数据
                    if "result_data" in locals():
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)), result_data)
                    else:
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)))
                # 判断结果数据是否存在，若存在就存储文件
                if "result_data" in locals():
                    self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                    del result_data
                    file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 根据原始数据规整日数据(源数据是日文件)(增加了#.*#匹配)
    def regular_day_raw_data_multiple_hms(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_day_raw_data_multiple_hms")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            # logging.info(tmpStartMon,tmpEndMon)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                result_data_get = []
                monDays = calendar.monthrange(year, mon)[1]
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym)
                logging.info(dataOutputPath)
                # 若输出文件存在，则获取数据
                if os.path.exists(dataOutputPath):
                    ds_r = xr.open_dataset(dataOutputPath)
                    # logging.info(ds_r)
                    result_data = ds_r[dataConfig.get("var")]
                # 计算当月的起止日
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                for day in range(tmpStartDay, tmpEndDay + 1):  # 循环日
                    ymd = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(day)
                    dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace("#YYYYMMDD#",
                                                                                                         ymd).replace(
                        "#YYYYMM#", ymd[:6])
                    # 文件名中包含时分秒，用#.*#
                    file_list = os.listdir(os.path.dirname(dataInputPath))
                    re_filename = os.path.basename(dataInputPath).replace('#.*#', '.*')
                    getfilename = [i for i in file_list if re.findall(re_filename, i)]
                    if len(getfilename) != 0:
                        dataInputPath = os.path.dirname(dataInputPath) + '/' + getfilename[0]

                    if os.path.exists(dataInputPath):
                        logging.info(dataInputPath)
                        ds = xr.open_dataset(dataInputPath, engine='pynio')
                        # logging.info(ds)
                        # 重置变量名和维的名称
                        # logging.info(dataConfig.get("original").get("var")+"%%%%%"+dataInputPath)
                        if dataConfig.get("original").get("var") not in ds.keys():
                            continue
                        if dataConfig.get("original").get("var"):
                            ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                        if dataConfig.get("original").get("level"):
                            ds = ds.rename({dataConfig.get("original").get("level"): "level"})
                            if dataConfig.get("var") not in ["u100m", "v100m"]:
                                ds['level'] = ds['level'] * 0.01
                                ds['level'].attrs['units'] = "hPa"
                        if dataConfig.get("original").get("lat"):
                            ds = ds.rename({dataConfig.get("original").get("lat"): "lat"})
                        if dataConfig.get("original").get("lon"):
                            ds = ds.rename({dataConfig.get("original").get("lon"): "lon"})
                        data = ds[dataConfig.get("var")]
                        if dataConfig.get("original").get("levels"):
                            logging.info("只需要保留指定的高度层...")
                            data = data.sel(level=dataConfig.get("original").get("levels"))
                        # 单位转换
                        logging.info("原始数据的大小范围在%s~%s..." % (data.min().values, data.max().values))
                        if dataConfig.get("unitConvert"):
                            data.attrs['units'] = dataConfig.get("unitConvert").get("unitName")
                            convert_type, convert_value = dataConfig.get("unitConvert").get("unitProc").split("_")
                            logging.info("%s开始单位转换...转换公式为%s" % (
                                dataConfig.get("var"), [convert_type, convert_value]))
                            data_allx = convert_data(data, convert_type, convert_value)
                            data_allx.attrs = data.attrs
                            data = data_allx
                            logging.info("转换后的数据大小范围在%s~%s..." % (data.min().values, data.max().values))
                            logging.info(data.max().values)
                            if "valid_range" in data.attrs.keys():
                                data.attrs.pop('valid_range')
                            if "actual_range" in data.attrs.keys():
                                data.attrs.pop('actual_range')
                        # if dataConfig.get("var") in ["u100m","v100m"]:
                        # data = data.sel(lv_HTGL1=100)
                        # logging.info(data)
                        data.expand_dims(dim="time", axis=0)
                        data["time"] = day
                        result_data_get.append(data)
                    else:
                        error_str = "源文件【%s】不存在!" % (dataInputPath)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)

                if len(result_data_get) != 0:
                    data_a = xr.concat(result_data_get, dim="time")
                    # 补全数据
                    if "result_data" in locals():
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)), result_data)
                    else:
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)))
                # 判断结果数据是否存在，若存在就存储文件
                if "result_data" in locals():
                    self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                    del result_data
                    file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 根据原始数据规整日数据(源数据是日文件)(ERA5源文件中level是hPa)
    def regular_day_raw_data_multiple_hpa(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_day_raw_data_multiple_hpa")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            # logging.info(tmpStartMon,tmpEndMon)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                result_data_get = []
                monDays = calendar.monthrange(year, mon)[1]
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym)
                logging.info(dataOutputPath)
                # 若输出文件存在，则获取数据
                if os.path.exists(dataOutputPath):
                    ds_r = xr.open_dataset(dataOutputPath)
                    # logging.info(ds_r)
                    result_data = ds_r[dataConfig.get("var")]
                # 计算当月的起止日
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                for day in range(tmpStartDay, tmpEndDay + 1):  # 循环日
                    ymd = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(day)
                    dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace("#YYYYMMDD#",
                                                                                                         ymd)
                    if os.path.exists(dataInputPath):
                        logging.info(dataInputPath)
                        ds = xr.open_dataset(dataInputPath, engine='pynio')
                        # logging.info(ds)
                        # 重置变量名和维的名称
                        # logging.info(dataConfig.get("original").get("var")+"%%%%%"+dataInputPath)
                        if dataConfig.get("original").get("var") not in ds.keys():
                            continue
                        if dataConfig.get("original").get("var"):
                            ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                        if dataConfig.get("original").get("level"):
                            ds = ds.rename({dataConfig.get("original").get("level"): "level"})
                            # 单位是Pa 转为hPa
                            if ds['level'].attrs['units'] == "Pa":
                                ds['level'] = ds['level'] * 0.01
                                ds['level'].attrs['units'] = "hPa"
                        if dataConfig.get("original").get("lat"):
                            ds = ds.rename({dataConfig.get("original").get("lat"): "lat"})
                        if dataConfig.get("original").get("lon"):
                            ds = ds.rename({dataConfig.get("original").get("lon"): "lon"})
                        data = ds[dataConfig.get("var")]
                        if dataConfig.get("original").get("levels"):
                            logging.info("只需要保留指定的高度层...")
                            data = data.sel(level=dataConfig.get("original").get("levels"))
                        # 单位转换
                        logging.info("原始数据的大小范围在%s~%s..." % (data.min().values, data.max().values))
                        if dataConfig.get("unitConvert"):
                            data.attrs['units'] = dataConfig.get("unitConvert").get("unitName")
                            convert_type, convert_value = dataConfig.get("unitConvert").get("unitProc").split("_")
                            logging.info("%s开始单位转换...转换公式为%s" % (
                                dataConfig.get("var"), [convert_type, convert_value]))
                            data_allx = convert_data(data, convert_type, convert_value)
                            data_allx.attrs = data.attrs
                            data = data_allx
                            logging.info("转换后的数据大小范围在%s~%s..." % (data.min().values, data.max().values))
                            logging.info(data.max().values)
                            if "valid_range" in data.attrs.keys():
                                data.attrs.pop('valid_range')
                            if "actual_range" in data.attrs.keys():
                                data.attrs.pop('actual_range')
                        # if dataConfig.get("var") in ["u100m","v100m"]:
                        # data = data.sel(lv_HTGL1=100)
                        # logging.info(data)
                        data.expand_dims(dim="time", axis=0)
                        data["time"] = day
                        result_data_get.append(data)
                    else:
                        error_str = "源文件【%s】不存在!" % (dataInputPath)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)

                if len(result_data_get) != 0:
                    data_a = xr.concat(result_data_get, dim="time")
                    # 补全数据
                    if "result_data" in locals():
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)), result_data)
                    else:
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)))
                # 判断结果数据是否存在，若存在就存储文件
                if "result_data" in locals():
                    self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                    del result_data
                    file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 根据原始数据规整日数据(源数据是按月存放的日文件)
    def regular_day_raw_data_from_mon(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_day_raw_data_from_mon")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            # logging.info(tmpStartMon,tmpEndMon)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                result_data_get = []
                monDays = calendar.monthrange(year, mon)[1]
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym)
                logging.info(dataOutputPath)
                # 若输出文件存在，则获取数据
                if os.path.exists(dataOutputPath):
                    ds_r = xr.open_dataset(dataOutputPath)
                    # logging.info(ds_r)
                    result_data = ds_r[dataConfig.get("var")]
                # 计算当月的起止日
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                # 计算当月的起止日在本月中的位置
                startDayIndex = tmpStartDay - 1
                endDayIndex = tmpEndDay - 1
                # 获取源数据的输入位置
                # logging.info(str(year * 100 + mon))
                dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace("#YYYYMM#",
                                                                                                     str(year * 100 + mon))
                if os.path.exists(dataInputPath):
                    # 加载数据
                    ds = xr.open_dataset(dataInputPath)
                    # logging.info(ds.coords)
                    # 重置变量名和维的名称
                    if dataConfig.get("original"):
                        if dataConfig.get("original").get("var"):
                            ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                        # 个别数据，有垃圾维，得删
                        if dataConfig.get("original").get("remove_dim"):
                            ds._coord_names.remove(dataConfig.get("original").get("remove_dim"))
                    data_all = ds[dataConfig.get("var")]
                    # 单位转换
                    if dataConfig.get("unitConvert"):
                        data_all.attrs['units'] = dataConfig.get("unitConvert").get("unitName")
                        convert_type, convert_value = dataConfig.get("unitConvert").get("unitProc").split("_")
                        data_allx = convert_data(data_all, convert_type, convert_value)
                        data_allx.attrs = data_all.attrs
                        data_all = data_allx
                        logging.info(data_all.max().values)
                        if "valid_range" in data_all.attrs.keys():
                            data_all.attrs.pop('valid_range')
                        if "actual_range" in data_all.attrs.keys():
                            data_all.attrs.pop('actual_range')
                    if data_all.lon.min() < 0:
                        lonx = data_all.lon
                        lonx = xr.where(lonx < 0, lonx + 360, lonx)
                        data_all["lon"].values = lonx.values
                        data_all = data_all.sortby(data_all["lon"])
                    # 处理插值
                    if dataConfig.get("interp"):
                        lats = dataConfig.get("interp").get("lats")
                        lons = dataConfig.get("interp").get("lons")
                        glon = np.linspace(lons[0], lons[1], lons[2], dtype=np.float32)
                        glat = np.linspace(lats[0], lats[1], lats[2], dtype=np.float32)
                        data_all = data_all.interp(lat=glat, lon=glon)

                    if startDayIndex > len(data_all.time.values):
                        currStartTime = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(tmpStartDay)
                        file_time_list = DateUtils.get_time_list([str(year) + "0101", str(year) + "1231"], "day")
                        fileEndTime = file_time_list[len(data_all.time.values) - 1]
                        error_str = "数据规整的开始时间[%s]大于源文件[%s]的结束时间[%s]" % (
                            DateUtils.time_format_ch(currStartTime, "day"), dataInputPath,
                            DateUtils.time_format_ch(fileEndTime, "day"))
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)
                            continue
                    if endDayIndex > len(data_all.time.values):
                        tmpEndDay = tmpEndDay - (endDayIndex - len(data_all.time.values))
                        endDayIndex = len(data_all.time.values)
                    # 筛选数据
                    data = data_all.isel(time=range(startDayIndex - 1, endDayIndex))
                    # logging.info(data)
                    # 重置时间维的数值
                    data.time.values = list(range(tmpStartDay, tmpEndDay + 1))
                    # ERA5数据存在一个没用的realization属性，干掉他
                    if "realization" in data._coords:
                        del data._coords["realization"]
                    # logging.info(data.shape)
                    # 补全数据
                    if "result_data" in locals():
                        result_data = self.makeup_data_by_time(data, list(range(1, monDays + 1)), result_data)
                    else:
                        result_data = self.makeup_data_by_time(data, list(range(1, monDays + 1)))
                    # 判断结果数据是否存在，若存在就存储文件
                    if "result_data" in locals():
                        self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                        del result_data
                        file_num = file_num + 1
                else:
                    error_str = "源文件【%s】不存在!" % (dataInputPath)
                    if startTime == endTime:  # 同一时间点直接抛异常
                        raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                    else:
                        logging.error(error_str)
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 根据规整后的日数据规整候数据
    def regular_five_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_five_data")
        # 计算开始年 开始月 开始日
        startYear, startMon, startFive = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endFive = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            result_data_get = []
            dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", str(year))
            logging.info(dataOutputPath)
            # 若输出文件存在，则获取数据
            if os.path.exists(dataOutputPath):
                ds_r = xr.open_dataset(dataOutputPath)
                result_data = ds_r[dataConfig.get("var")]
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            # logging.info(tmpStartMon,tmpEndMon)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                # 计算当月的起止候
                tmpStartFive = np.where(year == startYear and mon == startMon, startFive, 1)
                tmpEndFive = np.where(year == endYear and mon == endMon, endFive, 6)
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY_MM#", ym)
                if os.path.exists(dataInputPath):
                    ds = xr.open_dataset(dataInputPath)
                    data_m = ds[dataConfig.get("var")]
                    for five in range(tmpStartFive, tmpEndFive + 1):  # 循环候
                        # 计算当前候在一年中的位置
                        indx = (mon - 1) * 6 + five
                        # 计算当前候对应的起止日期
                        tmpStartDay = (five - 1) * 5 + 1
                        tmpEndDay = np.where(five == 6, calendar.monthrange(year, mon)[1], five * 5)
                        # 判断规整当前候所需的日数据是否都部署缺测
                        if self.check_miss_data(data_m.sel(time=range(tmpStartDay, tmpEndDay + 1))):
                            currTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + "{0:02d}".format(five) + "候"
                            regularStartTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + "{0:02d}".format(
                                tmpStartDay) + "日"
                            regularEndTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + "{0:02d}".format(
                                tmpEndDay) + "日"
                            error_str = "源文件[%s]中规整候[%s]数据对应的时间范围[%s~%s]有缺测，无法规整该候数据。" % (
                                dataInputPath, currTime, regularStartTime, regularEndTime)
                            if startTime == endTime:  # 同一时间点直接抛异常
                                raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE, response_msg=error_str)
                            else:
                                logging.error(error_str)
                                continue
                        data_w = data_m[0]
                        if dataConfig.get("var") in ["rain", "precip", "ssrd"]:
                            data_w.values = data_m.sel(time=range(tmpStartDay, tmpEndDay + 1)).sum(dim="time").values
                            tmp_data = data_m.sel(time=range(tmpStartDay, tmpEndDay + 1)).mean(dim="time").values
                            data_w.values = np.where(np.isnan(tmp_data), tmp_data, data_w.values)
                            logging.info("%s侯要素求和了..." % (dataConfig.get("var")))
                        else:
                            data_w.values = data_m.sel(time=range(tmpStartDay, tmpEndDay + 1)).mean(dim="time").values
                        data_w.expand_dims(dim="time", axis=0)
                        data_w["time"] = indx
                        result_data_get.append(data_w)
                else:
                    error_str = "源文件【%s】不存在!" % (dataInputPath)
                    if startTime == endTime:  # 同一时间点直接抛异常
                        raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                    else:
                        logging.error(error_str)
            if len(result_data_get) != 0:
                data_a = xr.concat(result_data_get, dim="time")
                # 补全数据
                if "result_data" in locals():
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 73)), result_data)
                else:
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 73)))
            # 判断结果数据是否存在，若存在就存储文件
            if "result_data" in locals():
                self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                del result_data
                file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 根据规整后的日数据规整旬数据
    def regular_ten_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_ten_data")
        # 计算开始年 开始月 开始日
        startYear, startMon, startTen = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endTen = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            result_data_get = []
            dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", str(year))
            # logging.info(dataOutputPath)
            # 若输出文件存在，则获取数据
            if os.path.exists(dataOutputPath):
                ds_r = xr.open_dataset(dataOutputPath)
                result_data = ds_r[dataConfig.get("var")]
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            # logging.info(tmpStartMon,tmpEndMon)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                # 计算当月的起止旬
                tmpStartTen = np.where(year == startYear and mon == startMon, startTen, 1)
                tmpEndTen = np.where(year == endYear and mon == endMon, endTen, 3)
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY_MM#", ym)
                if os.path.exists(dataInputPath):
                    ds = xr.open_dataset(dataInputPath)
                    data_m = ds[dataConfig.get("var")]
                    for ten in range(tmpStartTen, tmpEndTen + 1):  # 循环旬
                        # 计算当前旬在一年中的位置
                        indx = (mon - 1) * 3 + ten
                        # 计算当前旬对应的起止日期
                        tmpStartDay = (ten - 1) * 10 + 1
                        tmpEndDay = np.where(ten == 3, calendar.monthrange(year, mon)[1], ten * 10)
                        # 判断规整当前旬所需的日数据是否都部署缺测
                        if self.check_miss_data(data_m.sel(time=range(tmpStartDay, tmpEndDay + 1))):
                            tenStr = np.where(ten == 1, "上旬", np.where(ten == 2, "中旬", "下旬"))
                            currTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + str(tenStr)
                            regularStartTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + "{0:02d}".format(
                                tmpStartDay) + "日"
                            regularEndTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + "{0:02d}".format(
                                tmpEndDay) + "日"
                            error_str = "源文件[%s]中规整旬[%s]数据对应的时间范围[%s~%s]有缺测，无法规整该旬数据。" % (
                                dataInputPath, currTime, regularStartTime, regularEndTime)
                            if startTime == endTime:  # 同一时间点直接抛异常
                                raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE, response_msg=error_str)
                            else:
                                logging.error(error_str)
                                continue
                        data_w = data_m[0]
                        if dataConfig.get("var") in ["rain", "precip", "ssrd"]:
                            data_w.values = data_m.sel(time=range(tmpStartDay, tmpEndDay + 1)).sum(dim="time")
                            tmp_data = data_m.sel(time=range(tmpStartDay, tmpEndDay + 1)).mean(dim="time")
                            data_w.values = data_m.sum(dim="time").values
                            data_w.values = np.where(np.isnan(tmp_data), tmp_data.values, data_w.values)
                            logging.info("%s旬要素求和了..." % (dataConfig.get("var")))
                        else:
                            data_w.values = data_m.sel(time=range(tmpStartDay, tmpEndDay + 1)).mean(dim="time").values
                        data_w.expand_dims(dim="time", axis=0)
                        data_w["time"] = indx
                        result_data_get.append(data_w)
                else:
                    error_str = "源文件【%s】不存在!" % (dataInputPath)
                    if startTime == endTime:  # 同一时间点直接抛异常
                        raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                    else:
                        logging.error(error_str)
            if len(result_data_get) != 0:
                data_a = xr.concat(result_data_get, dim="time")
                # 补全数据
                if "result_data" in locals():
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 37)), result_data)
                else:
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 37)))
            # 判断结果数据是否存在，若存在就存储文件
            if "result_data" in locals():
                self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                del result_data
                file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 原始月（按月存存储） -> 月
    def regular_mon_raw_data_multiple(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_mon_raw_data_multiple")
        # 计算开始年 开始月
        startYear, startMon = int(str(startTime)[0:4]), int(str(startTime)[4:6])
        # 计算结束年 结束月
        endYear, endMon = int(str(endTime)[0:4]), int(str(endTime)[4:6])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            result_data_get = []
            dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", str(year))
            # logging.info(dataOutputPath)
            # 若输出文件存在，则获取数据
            if os.path.exists(dataOutputPath):
                ds_r = xr.open_dataset(dataOutputPath)
                result_data = ds_r[dataConfig.get("var")]
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):
                ym = str(year) + "{0:02d}".format(mon)
                # logging.info(ym)
                dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace("#YYYYMM#", ym)
                logging.info(dataInputPath)

                if os.path.exists(dataInputPath):
                    ds = xr.open_dataset(dataInputPath, engine='pynio')
                    # 重置变量名和维的名称
                    if dataConfig.get("original").get("var"):
                        ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                    if dataConfig.get("original").get("level"):
                        ds = ds.rename({dataConfig.get("original").get("level"): "level"})
                        if dataConfig.get("var") not in ["u100m", "v100m"]:
                            ds['level'] = ds['level'] * 0.01
                            ds['level'].attrs['units'] = "hPa"
                        # logging.info(ds['level'])
                        # exit()
                    if dataConfig.get("original").get("lat"):
                        ds = ds.rename({dataConfig.get("original").get("lat"): "lat"})
                    if dataConfig.get("original").get("lon"):
                        ds = ds.rename({dataConfig.get("original").get("lon"): "lon"})
                    data = ds[dataConfig.get("var")]
                    if dataConfig.get("original").get("levels"):
                        logging.info("只需要保留指定的高度层...")
                        data = data.sel(level=dataConfig.get("original").get("levels"))
                    logging.info("原始数据的大小范围在%s~%s..." % (data.min().values, data.max().values))
                    if dataConfig.get("unitConvert"):
                        data.attrs['units'] = dataConfig.get("unitConvert").get("unitName")
                        unitConverts = dataConfig.get("unitConvert").get("unitProc").split("-")
                        convert_type, convert_value = unitConverts[0].split("_")
                        logging.info("%s开始单位转换...转换公式为%s" % (dataConfig.get("var"), unitConverts))
                        data_allx = convert_data(data, convert_type, convert_value)
                        if len(unitConverts) == 2:
                            if unitConverts[1] == "mon":
                                mon_days = calendar.monthrange(year, mon)[1]
                                data_allx *= mon_days
                        data_allx.attrs = data.attrs
                        data = data_allx
                        logging.info("转换后的数据大小范围在%s~%s..." % (data.min().values, data.max().values))
                        if "valid_range" in data.attrs.keys():
                            data.attrs.pop('valid_range')
                        if "actual_range" in data.attrs.keys():
                            data.attrs.pop('actual_range')
                    if "time" not in data.dims:  # 读出来的数据里如果没有time就加一个time维度
                        data.expand_dims(dim="time", axis=0)
                        data["time"] = mon
                    else:
                        data["time"] = [mon]
                    result_data_get.append(data)
                else:
                    error_str = "源文件【%s】不存在!" % (dataInputPath)
                    if startTime == endTime:  # 同一时间点直接抛异常
                        raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                    else:
                        logging.error(error_str)
            if len(result_data_get) != 0:
                data_a = xr.concat(result_data_get, dim="time")
                # 补全数据
                if "result_data" in locals():
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 13)), result_data)
                else:
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 13)))
            # 判断结果数据是否存在，若存在就存储文件
            if "result_data" in locals():
                self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                del result_data
                file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 根据规整后的日数据规整月数据
    def regular_mon_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_mon_data")
        # 计算开始年 开始月
        startYear, startMon = int(str(startTime)[0:4]), int(str(startTime)[4:6])
        # 计算结束年 结束月
        endYear, endMon = int(str(endTime)[0:4]), int(str(endTime)[4:6])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            result_data_get = []
            dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", str(year))
            # logging.info(dataOutputPath)
            # 若输出文件存在，则获取数据
            if os.path.exists(dataOutputPath):
                ds_r = xr.open_dataset(dataOutputPath)
                result_data = ds_r[dataConfig.get("var")]
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            # logging.info(tmpStartMon,tmpEndMon)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY_MM#", ym)
                # logging.info(dataInputPath)
                if os.path.exists(dataInputPath):
                    ds = xr.open_dataset(dataInputPath)
                    data_m = ds[dataConfig.get("var")]
                    # 判断规整当前月所需的日数据是否都部署缺测
                    tmpStartDay = 1
                    tmpEndDay = calendar.monthrange(year, mon)[1]
                    if self.check_miss_data(data_m.sel(time=range(tmpStartDay, tmpEndDay + 1))):
                        currTime = str(year) + "年" + "{0:02d}".format(mon) + "月"
                        regularStartTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + "{0:02d}".format(
                            tmpStartDay) + "日"
                        regularEndTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + "{0:02d}".format(
                            tmpEndDay) + "日"
                        error_str = "源文件[%s]中规整月[%s]数据对应的时间范围[%s~%s]有缺测，无法规整该月数据。" % (
                            dataInputPath, currTime, regularStartTime, regularEndTime)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)
                            continue
                    data_w = data_m[0]
                    if dataConfig.get("var") in ["rain", "precip", "ssrd"]:
                        tmp_data = data_m.mean(dim="time")
                        data_w.values = data_m.sum(dim="time").values
                        data_w.values = np.where(np.isnan(tmp_data), tmp_data.values, data_w.values)
                        logging.info("%s日转月要素求和了..." % (dataConfig.get("var")))
                    else:
                        data_w.values = data_m.mean(dim="time").values
                    data_w.expand_dims(dim="time", axis=0)
                    data_w["time"] = mon
                    result_data_get.append(data_w)
                else:
                    error_str = "源文件【%s】不存在!" % (dataInputPath)
                    if startTime == endTime:  # 同一时间点直接抛异常
                        raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                    else:
                        logging.error(error_str)
            if len(result_data_get) != 0:
                data_a = xr.concat(result_data_get, dim="time")
                # 补全数据
                if "result_data" in locals():
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 13)), result_data)
                else:
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 13)))
            # 判断结果数据是否存在，若存在就存储文件
            if "result_data" in locals():
                self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                del result_data
                file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 根据规整后的月数据规整季数据
    def regular_season_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_season_data")
        # 计算开始年 开始季
        startYear, startSeason = int(str(startTime)[0:4]), int(str(startTime)[4:6])
        # 计算结束年 结束季
        endYear, endSeason = int(str(endTime)[0:4]), int(str(endTime)[4:6])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            result_data_get = []
            dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", str(year))
            # logging.info(dataOutputPath)
            # 若输出文件存在，则获取数据
            if os.path.exists(dataOutputPath):
                ds_r = xr.open_dataset(dataOutputPath)
                result_data = ds_r[dataConfig.get("var")]
            # 计算当前年的起止月份
            tmpStartSeason = np.where(year == startYear, startSeason, 1)
            tmpEndSeason = np.where(year == endYear, endSeason, 4)
            # logging.info(tmpStartMon,tmpEndMon)
            for season in range(tmpStartSeason, tmpEndSeason + 1):  # 循环季
                # 当前季不是冬季处理
                if season != 4:
                    mons = range(season * 3, (season + 1) * 3)
                    dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year))
                    # logging.info(dataInputPath)
                    if os.path.exists(dataInputPath):
                        ds = xr.open_dataset(dataInputPath)
                        data_m = ds[dataConfig.get("var")]
                        if self.check_miss_data(data_m.sel(time=mons)):
                            seaStr = np.where(season == 1, "春季", np.where(season == 2, "夏季", "秋季"))
                            currTime = str(year) + "年" + str(seaStr)
                            regularStartTime = str(year) + "年" + "{0:02d}".format(list(mons)[0]) + "月"
                            regularEndTime = str(year) + "年" + "{0:02d}".format(list(mons)[-2]) + "月"
                            error_str = "源文件[%s]中规整季[%s]数据对应的时间范围[%s~%s]有缺测，无法规整该季数据。" % (
                                dataInputPath, currTime, regularStartTime, regularEndTime)
                            if startTime == endTime:  # 同一时间点直接抛异常
                                raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE, response_msg=error_str)
                            else:
                                logging.error(error_str)
                                continue
                        data_w = data_m[0]
                        if dataConfig.get("var") in ["rain", "precip", "ssrd"]:
                            tmp_data = data_m.sel(time=mons).mean(dim="time")
                            data_w.values = data_m.sel(time=mons).sum(dim="time").values
                            data_w.values = np.where(np.isnan(tmp_data), tmp_data.values, data_w.values)
                            logging.info("%s季要素求和了..." % (dataConfig.get("var")))
                        else:
                            data_w.values = data_m.sel(time=mons).mean(dim="time").values
                        data_w.expand_dims(dim="time", axis=0)
                        data_w["time"] = season
                        result_data_get.append(data_w)
                    else:
                        error_str = "源文件【%s】不存在!" % (dataInputPath)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)
                else:
                    # 当前季是冬季处理
                    dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year))
                    dataInputPath_prex = dataConfig.get("dataInputPath").replace("#YYYY#", str(year - 1))
                    # logging.info(dataInputPath)
                    if os.path.exists(dataInputPath) and os.path.exists(dataInputPath_prex):
                        ds_now = xr.open_dataset(dataInputPath)
                        data_now = ds_now[dataConfig.get("var")]
                        data_now = data_now.sel(time=[1, 2])
                        ds_prex = xr.open_dataset(dataInputPath_prex)
                        data_prex = ds_prex[dataConfig.get("var")]
                        try:
                            data_prex = data_prex.sel(time=[12])
                        except KeyError:
                            # 个别月数据的时间属性有问题，这边直接取时间里的12月的下标
                            data_prex = data_prex[11:12, ...]
                        data_m = xr.concat([data_now, data_prex], dim='time')
                        if self.check_miss_data(data_m):
                            currTime = str(year) + "年冬季"
                            regularStartTime = str(year - 1) + "年12月"
                            regularEndTime = str(year) + "年02月"
                            error_str = "源文件[%s,%s]中规整季[%s]数据对应的时间范围[%s~%s]有缺测，无法规整该季数据。" % (
                                dataInputPath_prex, dataInputPath, currTime, regularStartTime, regularEndTime)
                            if startTime == endTime:  # 同一时间点直接抛异常
                                raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE, response_msg=error_str)
                            else:
                                logging.error(error_str)
                                continue
                        data_w = data_m[0]
                        if dataConfig.get("var") in ["rain", "precip", "ssrd"]:
                            tmp_data = data_m.mean(dim="time").values
                            data_w.values = data_m.sum(dim="time").values
                            data_w.values = np.where(np.isnan(tmp_data), tmp_data, data_w.values)
                        else:
                            # 对时间求平均
                            data_w.values = data_m.mean(dim="time").values
                        data_w.expand_dims(dim="time", axis=0)
                        data_w["time"] = season
                        result_data_get.append(data_w)
                    else:
                        error_str = "源文件【%s，%s】不存在!" % (dataInputPath_prex, dataInputPath)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)

            if len(result_data_get) != 0:
                data_a = xr.concat(result_data_get, dim="time")
                # 补全数据
                if "result_data" in locals():
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 5)), result_data)
                else:
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 5)))
            # 判断结果数据是否存在，若存在就存储文件
            if "result_data" in locals():
                self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                del result_data
                file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 根据规整后的月数据规整年数据
    def regular_year_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_year_data")
        # 计算开始年
        startYear = int(str(startTime)[0:4])
        # 计算结束年
        endYear = int(str(endTime)[0:4])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            result_data_get = []
            dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", str(year))
            # logging.info(dataOutputPath)
            # 若输出文件存在，则获取数据
            if os.path.exists(dataOutputPath):
                ds_r = xr.open_dataset(dataOutputPath)
                result_data = ds_r[dataConfig.get("var")]
            dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year))
            # logging.info(dataInputPath)
            if os.path.exists(dataInputPath):
                ds = xr.open_dataset(dataInputPath)
                data_m = ds[dataConfig.get("var")]
                if self.check_miss_data(data_m):
                    currTime = str(year) + "年"
                    regularStartTime = str(year) + "年01月"
                    regularEndTime = str(year) + "年12月"
                    error_str = "源文件[%s]中规整年[%s]数据对应的时间范围[%s~%s]有缺测，无法规整该年数据。" % (
                        dataInputPath, currTime, regularStartTime, regularEndTime)
                    if startTime == endTime:  # 同一时间点直接抛异常
                        raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE, response_msg=error_str)
                    else:
                        logging.error(error_str)
                        continue
                data_w = data_m[0]
                if dataConfig.get("var") in ["rain", "precip", "ssrd"]:
                    tmp_data = data_m.mean(dim="time")
                    data_w.values = data_m.sum(dim="time").values
                    data_w.values = np.where(np.isnan(tmp_data), tmp_data.values, data_w.values)
                    logging.info("%s年要素求和了..." % (dataConfig.get("var")))
                else:
                    data_w.values = data_m.mean(dim="time").values
                data_w.expand_dims(dim="time", axis=0)
                data_w["time"] = 1
                result_data_get.append(data_w)
            else:
                error_str = "源文件【%s】不存在!" % (dataInputPath)
                if startTime == endTime:  # 同一时间点直接抛异常
                    raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                else:
                    logging.error(error_str)
            if len(result_data_get) != 0:
                data_a = xr.concat(result_data_get, dim="time")
                # 补全数据
                if "result_data" in locals():
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 2)), result_data)
                else:
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 2)))
            # 判断结果数据是否存在，若存在就存储文件
            if "result_data" in locals():
                self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                del result_data
                file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 根据规整后的10m经纬向风规整10m风速 日
    def regular_day_raw_data_single_u10v10(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_day_raw_data_single_u10v10")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        vars = dataConfig.get("vars")
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
                # 获取数据输出的路径
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym)
                # 若输出文件存在，则获取数据
                if os.path.exists(dataOutputPath):
                    ds_r = xr.open_dataset(dataOutputPath)
                    result_data = ds_r[dataConfig.get("var")]
                # 获取源数据的输入位置
                dataInputPath_u10 = dataConfig.get("dataInputPath").replace("#YYYY_MM#", ym).replace("#V#", vars[0])
                dataInputPath_v10 = dataConfig.get("dataInputPath").replace("#YYYY_MM#", ym).replace("#V#", vars[1])
                if os.path.exists(dataInputPath_u10) and os.path.exists(dataInputPath_v10):
                    # 加载数据
                    ds_u10 = xr.open_dataset(dataInputPath_u10)
                    data_u10 = ds_u10[vars[0]]
                    # 筛选数据
                    data_u10 = data_u10.isel(time=range(tmpStartDay - 1, tmpEndDay))
                    if self.check_miss_data(data_u10):
                        regularStartTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + "{0:02d}".format(
                            tmpStartDay) + "日"
                        regularEndTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + "{0:02d}".format(
                            tmpEndDay) + "日"
                        error_str = "源文件[%s]中[%s~%s]的数据有缺测，无法规整风速数据。" % (
                            dataInputPath_u10, regularStartTime, regularEndTime)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)
                            continue
                    # 加载数据
                    ds_v10 = xr.open_dataset(dataInputPath_v10)
                    data_v10 = ds_v10[vars[1]]
                    # 筛选数据
                    data_v10 = data_v10.isel(time=range(tmpStartDay - 1, tmpEndDay))
                    if self.check_miss_data(data_v10):
                        regularStartTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + "{0:02d}".format(
                            tmpStartDay) + "日"
                        regularEndTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + "{0:02d}".format(
                            tmpEndDay) + "日"
                        error_str = "源文件[%s]中[%s~%s]的数据有缺测，无法规整风速数据。" % (
                            dataInputPath_v10, regularStartTime, regularEndTime)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)
                            continue
                    # cal wind speed
                    u10_pow_data = xr.ufuncs.square(data_u10)
                    v10_pow_data = xr.ufuncs.square(data_v10)
                    data = xr.ufuncs.sqrt(u10_pow_data + v10_pow_data)
                    # 重置时间维的数值
                    data.time.values = list(range(tmpStartDay, tmpEndDay + 1))
                    # 补全数据
                    if "result_data" in locals():
                        result_data = self.makeup_data_by_time(data, list(range(1, monDays + 1)), result_data)
                    else:
                        result_data = self.makeup_data_by_time(data, list(range(1, monDays + 1)))
                    # 判断结果数据是否存在，若存在就存储文件
                    if "result_data" in locals():
                        self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                        del result_data
                        file_num = file_num + 1
                else:
                    if not os.path.exists(dataInputPath_u10):
                        error_str = "源文件【%s】不存在!" % (dataInputPath_u10)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)
                    if not os.path.exists(dataInputPath_v10):
                        error_str = "源文件【%s】不存在!" % (dataInputPath_v10)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 根据原始数据规整月数据(源数据是一个文件)
    def regular_month_raw_data_single(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_month_raw_data_single")
        # 获取源数据的输入位置
        dataInputPath = dataConfig.get("dataInputPath")
        if "#YYYY#" in dataInputPath:
            # 计算开始年 开始月
            startYear, startMon = int(str(startTime)[0:4]), int(str(startTime)[4:6])
            # 计算结束年 结束月
            endYear, endMon = int(str(endTime)[0:4]), int(str(endTime)[4:6])
            # 获取源数据的输入位置
            dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(startYear))
        if os.path.exists(dataInputPath):
            # 加载数据
            ds = xr.open_dataset(dataInputPath)
            # 计算源文件的起止时间
            time_list = ds['time'].values
            file_start_time, file_end_time = str(time_list[0])[0:7].replace("-", ""), str(time_list[-1])[0:7].replace(
                "-", "")
            file_time_list = DateUtils.get_time_list([file_start_time, file_end_time], "mon")
            # 重置变量名和维的名称
            if dataConfig.get("original"):
                if dataConfig.get("original").get("var"):
                    ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
            # 根据要素获取数据
            data_all = ds[dataConfig.get("var")]
        else:
            # error_str = " original file [%s] is not found" % (dataInputPath)
            error_str = "源文件【%s】不存在!" % (dataInputPath)
            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)

        # 计算开始年 开始月
        startYear, startMon = int(str(startTime)[0:4]), int(str(startTime)[4:6])
        # 计算结束年 结束月
        endYear, endMon = int(str(endTime)[0:4]), int(str(endTime)[4:6])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            want_start_time, want_end_time = str(year) + "{0:02d}".format(tmpStartMon), str(year) + "{0:02d}".format(
                tmpEndMon)
            # 获取数据输出的路径
            dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", str(year))
            # 若输出文件存在，则获取数据
            if os.path.exists(dataOutputPath):
                ds_r = xr.open_dataset(dataOutputPath)
                result_data = ds_r[dataConfig.get("var")]

            # 计算当前年的起止月在源文件中的下标
            if want_start_time not in file_time_list:
                error_str = "数据规整的开始时间[%s]大于源文件[%s]的结束时间[%s]" % (
                    DateUtils.time_format_ch(want_start_time, "mon"), dataInputPath,
                    DateUtils.time_format_ch(file_end_time, "mon"))
                if startTime == endTime:  # 同一时间点直接抛异常
                    raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE, response_msg=error_str)
                else:
                    logging.error(error_str)
                    continue
            startIndex = file_time_list.index(want_start_time)
            if want_end_time in file_time_list:
                endIndex = file_time_list.index(want_end_time)
            else:
                endIndex = len(file_time_list) - 1
                tmpEndMon = int(str(file_end_time)[4:6])

            # 筛选数据
            data = data_all.isel(time=range(startIndex, endIndex + 1))
            # 重置时间维的数值
            data.time.values = list(range(tmpStartMon, tmpEndMon + 1))
            # 单位转换
            if dataConfig.get("unitConvert"):
                data.attrs['units'] = dataConfig.get("unitConvert").get("unitName")
                convert_type, convert_value = dataConfig.get("unitConvert").get("unitProc").split("_")
                specialConvert = dataConfig.get("unitConvert").get("specialConvert")
                if specialConvert:
                    data_list = []
                    for tt in list(data.time.values):
                        tmp_data = data.isel(time=tt - 1)
                        c_val = 0
                        if tt in [1, 3, 5, 7, 8, 10, 12]:
                            c_val = 31
                        if tt in [4, 6, 9, 11]:
                            c_val = 30
                        if tt == 2:
                            if year % 100 == 0 and year % 400 == 0:
                                c_val = 29
                            elif year % 100 != 0 and year % 4 == 0:
                                c_val = 29
                            else:
                                c_val = 28
                        tmp_data = convert_data(tmp_data, convert_type, c_val)
                        tmp_data = tmp_data.expand_dims("time")
                        tmp_data['time'] = [tt]
                        data_list.append(tmp_data)
                        # data.isel(time=tt-1).values = tmp_data
                    # data1 = xr.concat(data_list,dim="time")
                    data = xr.concat(data_list, dim="time")
                else:
                    datax = convert_data(data, convert_type, convert_value)
                    datax.attrs = data.attrs
                    data = datax
                # 剔除异常属性
                if "valid_range" in data.attrs.keys():
                    data.attrs.pop('valid_range')
                if "actual_range" in data.attrs.keys():
                    data.attrs.pop('actual_range')

            # 处理插值
            if dataConfig.get("interp"):
                lats = dataConfig.get("interp").get("lats")
                lons = dataConfig.get("interp").get("lons")
                glon = np.linspace(lons[0], lons[1], lons[2], dtype=np.float32)
                glat = np.linspace(lats[0], lats[1], lats[2], dtype=np.float32)
                data = data.interp(lat=glat, lon=glon)
            # 判断纬度维，如果是升序的话，转置成降序
            tmplat = list(data.lat.values)
            if tmplat[0] < tmplat[1]:
                data = data.sortby(data.lat, ascending=False)
            # 补全数据
            if "result_data" in locals():
                result_data = self.makeup_data_by_time(data, list(range(1, 13)), result_data)
            else:
                result_data = self.makeup_data_by_time(data, list(range(1, 13)))
            # 判断结果数据是否存在，若存在就存储文件
            if "result_data" in locals():
                self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                del result_data
                file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 根据规整后的日数据规整候数据（站点）
    def regular_station_five_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_station_five_data")
        # 计算开始年 开始月 开始候
        startYear, startMon, startFive = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(
            str(startTime)[6:8])
        # 计算结束年 结束月 结束候
        endYear, endMon, endFive = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            result_data_get = []
            dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", str(year))
            logging.info(dataOutputPath)
            # 若输出文件存在，则获取数据
            if os.path.exists(dataOutputPath):
                ds_r = xr.open_dataset(dataOutputPath)
                result_data = ds_r[dataConfig.get("var")]
            dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year))
            if os.path.exists(dataInputPath):
                ds = xr.open_dataset(dataInputPath)
                # 计算当前年的起止月份
                tmpStartMon = np.where(year == startYear, startMon, 1)
                tmpEndMon = np.where(year == endYear, endMon, 12)
                # logging.info(tmpStartMon,tmpEndMon)
                for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                    # 计算当月的起止候
                    tmpStartFive = np.where(year == startYear and mon == startMon, startFive, 1)
                    tmpEndFive = np.where(year == endYear and mon == endMon, endFive, 6)
                    data_m = ds[dataConfig.get("var")]
                    for five in range(tmpStartFive, tmpEndFive + 1):  # 循环候
                        # 计算当前候在一年中的位置
                        indx = (mon - 1) * 6 + five
                        # 计算当前候对应的起止日期及下标
                        tmpStartDay = (five - 1) * 5 + 1
                        tmpStartTime = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(tmpStartDay)
                        tmpStartIndex = DateUtils.get_time_index([tmpStartTime], "day")[0]
                        tmpEndDay = np.where(five == 6, calendar.monthrange(year, mon)[1], five * 5)
                        tmeEndTime = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(tmpEndDay)
                        tmpEndIndex = DateUtils.get_time_index([tmeEndTime], "day")[0]
                        # 判断规整当前候所需的日数据是否都部署缺测
                        if self.check_miss_data(data_m.isel(time=range(tmpStartIndex, tmpEndIndex + 1))):
                            currTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + "{0:02d}".format(five) + "候"
                            regularStartTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + "{0:02d}".format(
                                tmpStartDay) + "日"
                            regularEndTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + "{0:02d}".format(
                                tmpEndDay) + "日"
                            error_str = "源文件[%s]中规整候[%s]数据对应的时间范围[%s~%s]有缺测，无法规整该候数据。" % (
                                dataInputPath, currTime, regularStartTime, regularEndTime)
                            if startTime == endTime:  # 同一时间点直接抛异常
                                raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE,
                                                         response_msg=error_str)
                            else:
                                logging.error(error_str)
                                continue
                        data_w = data_m[0]
                        if "staticType" in dataConfig.keys() and dataConfig.get("staticType") == "sum":
                            data_w.values = data_m.isel(time=range(tmpStartIndex, tmpEndIndex + 1)).sum(
                                dim="time").values
                            tmp_data = data_m.isel(time=range(tmpStartIndex, tmpEndIndex + 1)).mean(dim="time").values
                            data_w.values = np.where(np.isnan(tmp_data), tmp_data, data_w.values)
                            logging.info("%s侯要素求和了..." % (dataConfig.get("var")))
                        else:
                            data_w.values = data_m.isel(time=range(tmpStartIndex, tmpEndIndex + 1)).mean(
                                dim="time").values
                        data_w.expand_dims(dim="time", axis=0)
                        data_w["time"] = indx
                        result_data_get.append(data_w)
            else:
                error_str = "源文件【%s】不存在!" % (dataInputPath)
                if startTime == endTime:  # 同一时间点直接抛异常
                    raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                else:
                    logging.error(error_str)
            if len(result_data_get) != 0:
                data_a = xr.concat(result_data_get, dim="time")
                # 补全数据
                if "result_data" in locals():
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 73)), result_data)
                else:
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 73)))
            # 判断结果数据是否存在，若存在就存储文件
            if "result_data" in locals():
                self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                del result_data
                file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 根据规整后的日数据规整旬数据（站点）
    def regular_station_ten_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_station_ten_data")
        # 计算开始年 开始月 开始旬
        startYear, startMon, startTen = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(
            str(startTime)[6:8])
        # 计算结束年 结束月 结束旬
        endYear, endMon, endTen = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            result_data_get = []
            dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", str(year))
            logging.info(dataOutputPath)
            # 若输出文件存在，则获取数据
            if os.path.exists(dataOutputPath):
                ds_r = xr.open_dataset(dataOutputPath)
                result_data = ds_r[dataConfig.get("var")]
            dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year))
            if os.path.exists(dataInputPath):
                ds = xr.open_dataset(dataInputPath)
                # 计算当前年的起止月份
                tmpStartMon = np.where(year == startYear, startMon, 1)
                tmpEndMon = np.where(year == endYear, endMon, 12)
                # logging.info(tmpStartMon,tmpEndMon)
                for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                    # 计算当月的起止旬
                    tmpStartTen = np.where(year == startYear and mon == startMon, startTen, 1)
                    tmpEndTen = np.where(year == endYear and mon == endMon, endTen, 3)
                    data_m = ds[dataConfig.get("var")]
                    for ten in range(tmpStartTen, tmpEndTen + 1):  # 循环旬
                        # 计算当前旬在一年中的位置
                        indx = (mon - 1) * 3 + ten
                        # 计算当前旬对应的起止日期及下标
                        tmpStartDay = (ten - 1) * 10 + 1
                        tmpStartTime = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(tmpStartDay)
                        tmpStartIndex = DateUtils.get_time_index([tmpStartTime], "day")[0]
                        tmpEndDay = np.where(ten == 3, calendar.monthrange(year, mon)[1], ten * 10)
                        tmeEndTime = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(tmpEndDay)
                        tmpEndIndex = DateUtils.get_time_index([tmeEndTime], "day")[0]
                        # 判断规整当前候所需的日数据是否都部署缺测
                        if self.check_miss_data(data_m.isel(time=range(tmpStartIndex, tmpEndIndex + 1))):
                            tenStr = ""
                            if ten == 1:
                                tenStr = "上旬"
                            if ten == 2:
                                tenStr = "中旬"
                            if ten == 3:
                                tenStr = "下旬"
                            currTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + tenStr
                            regularStartTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + "{0:02d}".format(
                                tmpStartDay) + "日"
                            regularEndTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + "{0:02d}".format(
                                tmpEndDay) + "日"
                            error_str = "源文件[%s]中规整旬[%s]数据对应的时间范围[%s~%s]有缺测，无法规整该候数据。" % (
                                dataInputPath, currTime, regularStartTime, regularEndTime)
                            if startTime == endTime:  # 同一时间点直接抛异常
                                raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE,
                                                         response_msg=error_str)
                            else:
                                logging.error(error_str)
                                continue
                        data_w = data_m[0]
                        if "staticType" in dataConfig.keys() and dataConfig.get("staticType") == "sum":
                            data_w.values = data_m.isel(time=range(tmpStartIndex, tmpEndIndex + 1)).sum(
                                dim="time").values
                            tmp_data = data_m.isel(time=range(tmpStartIndex, tmpEndIndex + 1)).mean(dim="time").values
                            data_w.values = np.where(np.isnan(tmp_data), tmp_data, data_w.values)
                            logging.info("%s旬要素求和了..." % (dataConfig.get("var")))
                        else:
                            data_w.values = data_m.isel(time=range(tmpStartIndex, tmpEndIndex + 1)).mean(
                                dim="time").values
                        data_w.expand_dims(dim="time", axis=0)
                        data_w["time"] = indx
                        result_data_get.append(data_w)
            else:
                error_str = "源文件【%s】不存在!" % (dataInputPath)
                if startTime == endTime:  # 同一时间点直接抛异常
                    raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                else:
                    logging.error(error_str)
            if len(result_data_get) != 0:
                data_a = xr.concat(result_data_get, dim="time")
                # 补全数据
                if "result_data" in locals():
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 37)), result_data)
                else:
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 37)))
            # 判断结果数据是否存在，若存在就存储文件
            if "result_data" in locals():
                self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                del result_data
                file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 根据规整后的日数据规整月数据（站点）
    def regular_station_mon_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_station_mon_data")
        # 计算开始年 开始月
        startYear, startMon = int(str(startTime)[0:4]), int(str(startTime)[4:6])
        # 计算结束年 结束月
        endYear, endMon = int(str(endTime)[0:4]), int(str(endTime)[4:6])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            result_data_get = []
            dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", str(year))
            logging.info(dataOutputPath)
            # 若输出文件存在，则获取数据
            if os.path.exists(dataOutputPath):
                ds_r = xr.open_dataset(dataOutputPath)
                result_data = ds_r[dataConfig.get("var")]
            dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year))
            if os.path.exists(dataInputPath):
                ds = xr.open_dataset(dataInputPath)
                # 计算当前年的起止月份
                tmpStartMon = np.where(year == startYear, startMon, 1)
                tmpEndMon = np.where(year == endYear, endMon, 12)
                # logging.info(tmpStartMon,tmpEndMon)
                for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                    # 计算当前月在一年中的位置
                    indx = mon - 1
                    # 计算当前月对应的起止日期及下标
                    tmpStartDay = 1
                    tmpStartTime = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(tmpStartDay)
                    tmpStartIndex = DateUtils.get_time_index([tmpStartTime], "day")[0]
                    tmpEndDay = calendar.monthrange(year, mon)[1]
                    tmeEndTime = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(tmpEndDay)
                    tmpEndIndex = DateUtils.get_time_index([tmeEndTime], "day")[0]
                    data_m = ds[dataConfig.get("var")]
                    # 判断规整当前候所需的日数据是否都部署缺测
                    if self.check_miss_data(data_m.isel(time=range(tmpStartIndex, tmpEndIndex + 1))):
                        currTime = str(year) + "年" + "{0:02d}".format(mon) + "月"
                        regularStartTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + "{0:02d}".format(
                            tmpStartDay) + "日"
                        regularEndTime = str(year) + "年" + "{0:02d}".format(mon) + "月" + "{0:02d}".format(
                            tmpEndDay) + "日"
                        error_str = "源文件[%s]中规整月[%s]数据对应的时间范围[%s~%s]有缺测，无法规整该候数据。" % (
                            dataInputPath, currTime, regularStartTime, regularEndTime)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE,
                                                     response_msg=error_str)
                        else:
                            logging.error(error_str)
                            continue
                    data_w = data_m[0]
                    if "staticType" in dataConfig.keys() and dataConfig.get("staticType") == "sum":
                        data_w.values = data_m.isel(time=range(tmpStartIndex, tmpEndIndex + 1)).sum(
                            dim="time").values
                        tmp_data = data_m.isel(time=range(tmpStartIndex, tmpEndIndex + 1)).mean(dim="time").values
                        data_w.values = np.where(np.isnan(tmp_data), tmp_data, data_w.values)
                        logging.info("%s月要素求和了..." % (dataConfig.get("var")))
                    else:
                        data_w.values = data_m.isel(time=range(tmpStartIndex, tmpEndIndex + 1)).mean(dim="time").values
                    data_w.expand_dims(dim="time", axis=0)
                    data_w["time"] = mon
                    result_data_get.append(data_w)
            else:
                error_str = "源文件【%s】不存在!" % (dataInputPath)
                if startTime == endTime:  # 同一时间点直接抛异常
                    raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                else:
                    logging.error(error_str)
            if len(result_data_get) != 0:
                data_a = xr.concat(result_data_get, dim="time")
                # 补全数据
                if "result_data" in locals():
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 13)), result_data)
                else:
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 13)))
            # 判断结果数据是否存在，若存在就存储文件
            if "result_data" in locals():
                self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                del result_data
                file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 根据规整后的月数据规整季数据(站点)
    def regular_station_season_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_season_data")
        # 计算开始年 开始季
        startYear, startSeason = int(str(startTime)[0:4]), int(str(startTime)[4:6])
        # 计算结束年 结束季
        endYear, endSeason = int(str(endTime)[0:4]), int(str(endTime)[4:6])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            result_data_get = []
            dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", str(year))
            # logging.info(dataOutputPath)
            # 若输出文件存在，则获取数据
            if os.path.exists(dataOutputPath):
                ds_r = xr.open_dataset(dataOutputPath)
                result_data = ds_r[dataConfig.get("var")]
            # 计算当前年的起止月份
            tmpStartSeason = np.where(year == startYear, startSeason, 1)
            tmpEndSeason = np.where(year == endYear, endSeason, 4)
            # logging.info(tmpStartMon,tmpEndMon)
            for season in range(tmpStartSeason, tmpEndSeason + 1):  # 循环季
                # 当前季不是冬季处理
                if season != 4:
                    mons = range(season * 3, (season + 1) * 3)
                    dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year))
                    # logging.info(dataInputPath)
                    if os.path.exists(dataInputPath):
                        ds = xr.open_dataset(dataInputPath)
                        data_m = ds[dataConfig.get("var")]
                        if self.check_miss_data(data_m.sel(time=mons)):
                            seaStr = np.where(season == 1, "春季", np.where(season == 2, "夏季", "秋季"))
                            currTime = str(year) + "年" + str(seaStr)
                            regularStartTime = str(year) + "年" + "{0:02d}".format(list(mons)[0]) + "月"
                            regularEndTime = str(year) + "年" + "{0:02d}".format(list(mons)[-2]) + "月"
                            error_str = "源文件[%s]中规整季[%s]数据对应的时间范围[%s~%s]有缺测，无法规整该季数据。" % (
                                dataInputPath, currTime, regularStartTime, regularEndTime)
                            if startTime == endTime:  # 同一时间点直接抛异常
                                raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE, response_msg=error_str)
                            else:
                                logging.error(error_str)
                                continue
                        data_w = data_m[0]
                        if "staticType" in dataConfig.keys() and dataConfig.get("staticType") == "sum":
                            tmp_data = data_m.sel(time=mons).mean(dim="time")
                            data_w.values = data_m.sel(time=mons).sum(dim="time").values
                            data_w.values = np.where(np.isnan(tmp_data), tmp_data.values, data_w.values)
                            logging.info("%s季要素求和了..." % (dataConfig.get("var")))
                        else:
                            data_w.values = data_m.sel(time=mons).mean(dim="time").values
                        data_w.expand_dims(dim="time", axis=0)
                        data_w["time"] = season
                        result_data_get.append(data_w)
                    else:
                        error_str = "源文件【%s】不存在!" % (dataInputPath)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)
                else:
                    # 当前季是冬季处理
                    dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year))
                    dataInputPath_prex = dataConfig.get("dataInputPath").replace("#YYYY#", str(year - 1))
                    # logging.info(dataInputPath)
                    if os.path.exists(dataInputPath) and os.path.exists(dataInputPath_prex):
                        ds_now = xr.open_dataset(dataInputPath)
                        data_now = ds_now[dataConfig.get("var")]
                        data_now = data_now.sel(time=[1, 2])
                        ds_prex = xr.open_dataset(dataInputPath_prex)
                        data_prex = ds_prex[dataConfig.get("var")]
                        try:
                            data_prex = data_prex.sel(time=[12])
                        except KeyError:
                            # 个别月数据的时间属性有问题，这边直接取时间里的12月的下标
                            data_prex = data_prex[11:12, ...]
                        data_m = xr.concat([data_now, data_prex], dim='time')
                        # print(data_m)
                        if self.check_miss_data(data_m):
                            currTime = str(year) + "年冬季"
                            regularStartTime = str(year - 1) + "年12月"
                            regularEndTime = str(year) + "年02月"
                            error_str = "源文件[%s,%s]中规整季[%s]数据对应的时间范围[%s~%s]有缺测，无法规整该季数据。" % (
                                dataInputPath_prex, dataInputPath, currTime, regularStartTime, regularEndTime)
                            if startTime == endTime:  # 同一时间点直接抛异常
                                raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE, response_msg=error_str)
                            else:
                                logging.error(error_str)
                                continue
                        data_w = data_m[0]
                        if "staticType" in dataConfig.keys() and dataConfig.get("staticType") == "sum":
                            tmp_data = data_m.mean(dim="time").values
                            data_w.values = data_m.sum(dim="time").values
                            data_w.values = np.where(np.isnan(tmp_data), tmp_data, data_w.values)
                            logging.info("%s季要素求和了..." % (dataConfig.get("var")))
                        else:
                            # 对时间求平均
                            data_w.values = data_m.mean(dim="time").values
                        data_w.expand_dims(dim="time", axis=0)
                        data_w["time"] = season
                        result_data_get.append(data_w)
                    else:
                        error_str = "源文件【%s，%s】不存在!" % (dataInputPath_prex, dataInputPath)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)

            if len(result_data_get) != 0:
                data_a = xr.concat(result_data_get, dim="time")
                # 补全数据
                if "result_data" in locals():
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 5)), result_data)
                else:
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 5)))
            # 判断结果数据是否存在，若存在就存储文件
            if "result_data" in locals():
                self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                del result_data
                file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 根据规整后的月数据规整年数据（站点）
    def regular_station_year_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_station_year_data")
        # 计算开始年
        startYear = int(str(startTime)[0:4])
        # 计算结束年
        endYear = int(str(endTime)[0:4])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            result_data_get = []
            dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", str(year))
            # logging.info(dataOutputPath)
            # 若输出文件存在，则获取数据
            if os.path.exists(dataOutputPath):
                ds_r = xr.open_dataset(dataOutputPath)
                result_data = ds_r[dataConfig.get("var")]
            dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year))
            # logging.info(dataInputPath)
            if os.path.exists(dataInputPath):
                ds = xr.open_dataset(dataInputPath)
                data_m = ds[dataConfig.get("var")]
                if self.check_miss_data(data_m):
                    currTime = str(year) + "年"
                    regularStartTime = str(year) + "年01月"
                    regularEndTime = str(year) + "年12月"
                    error_str = "源文件[%s]中规整年[%s]数据对应的时间范围[%s~%s]有缺测，无法规整该年数据。" % (
                        dataInputPath, currTime, regularStartTime, regularEndTime)
                    if startTime == endTime:  # 同一时间点直接抛异常
                        raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE, response_msg=error_str)
                    else:
                        logging.error(error_str)
                        continue
                data_w = data_m[0]
                if "staticType" in dataConfig.keys() and dataConfig.get("staticType") == "sum":
                    tmp_data = data_m.mean(dim="time")
                    data_w.values = data_m.sum(dim="time").values
                    data_w.values = np.where(np.isnan(tmp_data), tmp_data.values, data_w.values)
                    logging.info("%s年要素求和了..." % (dataConfig.get("var")))
                else:
                    data_w.values = data_m.mean(dim="time").values
                data_w.expand_dims(dim="time", axis=0)
                data_w["time"] = 1
                result_data_get.append(data_w)
            else:
                error_str = "源文件【%s】不存在!" % (dataInputPath)
                if startTime == endTime:  # 同一时间点直接抛异常
                    raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                else:
                    logging.error(error_str)
            if len(result_data_get) != 0:
                data_a = xr.concat(result_data_get, dim="time")
                # 补全数据
                if "result_data" in locals():
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 2)), result_data)
                else:
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 2)))
            # 判断结果数据是否存在，若存在就存储文件
            if "result_data" in locals():
                self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                del result_data
                file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    def regular_day_raw_data_fy_tbb(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_station_year_data")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                result_data_get = []
                # 计算当月的天数
                monDays = calendar.monthrange(year, mon)[1]
                # 计算当月的起止日
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                # 获取数据输出的路径
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym)
                logging.info(dataOutputPath)
                # 若输出文件存在，则获取数据
                if os.path.exists(dataOutputPath):
                    ds_r = xr.open_dataset(dataOutputPath)
                    result_data = ds_r[dataConfig.get("var")]
                for day in range(tmpStartDay, tmpEndDay + 1):  # 循环日
                    ymd = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(day)
                    dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace("#YYYYMMDD#",
                                                                                                         ymd)
                    ctlfile = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace("#YYYYMMDD#",
                                                                                                   ymd).replace('.dat',
                                                                                                                '.ctl')
                    fileContent = []
                    with open(ctlfile, 'r', encoding='utf-8') as f:
                        for line in f.readlines():
                            fileContent.append(line.lstrip())
                    fileContent[0] = 'dset ' + dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace(
                        "#YYYYMMDD#", '%y4%m2%d2') + '\n'
                    ctl_descriptor = CtlDescriptor(content=''.join(fileContent))
                    ctl_descriptor.dsetPath = [dataInputPath]

                    if os.path.exists(dataInputPath):
                        logging.info(dataInputPath)
                        ds = open_CtlDataset(ctl_descriptor)
                        # logging.info(ds)
                        # 重置变量名和维的名称
                        # logging.info(dataConfig.get("original").get("var")+"%%%%%"+dataInputPath)
                        if dataConfig.get("original").get("var") not in ds.keys():
                            continue
                        if dataConfig.get("original").get("var"):
                            ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                        if dataConfig.get("original").get("level"):
                            ds = ds.rename({dataConfig.get("original").get("level"): "level"})
                        if dataConfig.get("original").get("lat"):
                            ds = ds.rename({dataConfig.get("original").get("lat"): "lat"})
                        if dataConfig.get("original").get("lon"):
                            ds = ds.rename({dataConfig.get("original").get("lon"): "lon"})
                        data = ds[dataConfig.get("var")].sel(level=1.0)
                        if dataConfig.get("original").get("levels"):
                            logging.info("只需要保留指定的高度层...")
                            data = data.sel(level=dataConfig.get("original").get("levels"))
                        # 单位转换
                        logging.info("原始数据的大小范围在%s~%s..." % (data.min().values, data.max().values))
                        if dataConfig.get("unitConvert"):
                            data.attrs['units'] = dataConfig.get("unitConvert").get("unitName")
                            convert_type, convert_value = dataConfig.get("unitConvert").get("unitProc").split("_")
                            logging.info("%s开始单位转换...转换公式为%s" % (
                                dataConfig.get("var"), [convert_type, convert_value]))
                            data_allx = convert_data(data, convert_type, convert_value)
                            data_allx.attrs = data.attrs
                            data = data_allx
                            logging.info("转换后的数据大小范围在%s~%s..." % (data.min().values, data.max().values))
                            logging.info(data.max().values)
                            if "valid_range" in data.attrs.keys():
                                data.attrs.pop('valid_range')
                            if "actual_range" in data.attrs.keys():
                                data.attrs.pop('actual_range')
                        # if dataConfig.get("var") in ["u100m","v100m"]:
                        # data = data.sel(lv_HTGL1=100)
                        # logging.info(data)
                        # data = data.drop_dims("level")
                        data = data.drop("level")

                        data = xr.where(data == 65535.0, np.nan, data)
                        # data.expand_dims(dim="time", axis=0)
                        data["time"] = [day]
                        result_data_get.append(data)
                    else:
                        error_str = "源文件【%s】不存在!" % (dataInputPath)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)

                if len(result_data_get) != 0:
                    data_a = xr.concat(result_data_get, dim="time")
                    # 补全数据
                    if "result_data" in locals():
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)), result_data)
                    else:
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)))
                # 判断结果数据是否存在，若存在就存储文件
                if "result_data" in locals():
                    self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                    del result_data
                    file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    def regular_day_raw_data_fy_qpe(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_station_year_data")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                result_data_get = []
                # 计算当月的天数
                monDays = calendar.monthrange(year, mon)[1]
                # 计算当月的起止日
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                # 获取数据输出的路径
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym)
                logging.info(dataOutputPath)
                # 若输出文件存在，则获取数据
                if os.path.exists(dataOutputPath):
                    ds_r = xr.open_dataset(dataOutputPath)
                    result_data = ds_r[dataConfig.get("var")]
                for day in range(tmpStartDay, tmpEndDay + 1):  # 循环日
                    ymd = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(day)
                    dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace("#YYYYMMDD#",
                                                                                                         ymd)
                    ctlfile = '/nfsshare1/cdbdata/ftpdata/FY4A-QPE-DAILY/FY4A-QPE-DAILY/2021/DAILY/20210101RAIN.ctl'
                    fileContent = []
                    with open(ctlfile, 'r', encoding='utf-8') as f:
                        for line in f.readlines():
                            fileContent.append(line.lstrip())
                    fileContent[0] = 'dset ' + dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace(
                        "#YYYYMMDD#", '%y4%m2%d2') + '\n'
                    ctl_descriptor = CtlDescriptor(content=''.join(fileContent))
                    ctl_descriptor.dsetPath = [dataInputPath]

                    if os.path.exists(dataInputPath):
                        logging.info(dataInputPath)
                        ds = open_CtlDataset(ctl_descriptor)
                        # logging.info(ds)
                        # 重置变量名和维的名称
                        # logging.info(dataConfig.get("original").get("var")+"%%%%%"+dataInputPath)
                        if dataConfig.get("original").get("var") not in ds.keys():
                            continue
                        if dataConfig.get("original").get("var"):
                            ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                        if dataConfig.get("original").get("level"):
                            ds = ds.rename({dataConfig.get("original").get("level"): "level"})
                        if dataConfig.get("original").get("lat"):
                            ds = ds.rename({dataConfig.get("original").get("lat"): "lat"})
                        if dataConfig.get("original").get("lon"):
                            ds = ds.rename({dataConfig.get("original").get("lon"): "lon"})
                        lon = ds["lon"]
                        lat = ds["lat"]
                        lat = lat[(lat >= -50) & (lat <= 50)]
                        data = ds[dataConfig.get("var")].sel(level=1.0, lat=lat, lon=lon)
                        if dataConfig.get("original").get("levels"):
                            logging.info("只需要保留指定的高度层...")
                            data = data.sel(level=dataConfig.get("original").get("levels"))
                        # 单位转换
                        logging.info("原始数据的大小范围在%s~%s..." % (data.min().values, data.max().values))
                        if dataConfig.get("unitConvert"):
                            data.attrs['units'] = dataConfig.get("unitConvert").get("unitName")
                            convert_type, convert_value = dataConfig.get("unitConvert").get("unitProc").split("_")
                            logging.info("%s开始单位转换...转换公式为%s" % (
                                dataConfig.get("var"), [convert_type, convert_value]))
                            data_allx = convert_data(data, convert_type, convert_value)
                            data_allx.attrs = data.attrs
                            data = data_allx
                            logging.info("转换后的数据大小范围在%s~%s..." % (data.min().values, data.max().values))
                            logging.info(data.max().values)
                            if "valid_range" in data.attrs.keys():
                                data.attrs.pop('valid_range')
                            if "actual_range" in data.attrs.keys():
                                data.attrs.pop('actual_range')
                        # if dataConfig.get("var") in ["u100m","v100m"]:
                        # data = data.sel(lv_HTGL1=100)
                        # logging.info(data)
                        data = data.drop("level")

                        data = xr.where(data == 65535.0, np.nan, data)
                        # data.expand_dims(dim="time", axis=0)
                        data["time"] = [day]
                        result_data_get.append(data)
                    else:
                        error_str = "源文件【%s】不存在!" % (dataInputPath)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)

                if len(result_data_get) != 0:
                    data_a = xr.concat(result_data_get, dim="time")
                    # 补全数据
                    if "result_data" in locals():
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)), result_data)
                    else:
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)))
                # 判断结果数据是否存在，若存在就存储文件
                if "result_data" in locals():
                    self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                    del result_data
                    file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    def regular_day_raw_data_fy_amv(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_station_year_data")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                result_data_get = []
                # 计算当月的天数
                monDays = calendar.monthrange(year, mon)[1]
                # 计算当月的起止日
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                # 获取数据输出的路径
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym)
                logging.info(dataOutputPath)
                # 若输出文件存在，则获取数据
                if os.path.exists(dataOutputPath):
                    ds_r = xr.open_dataset(dataOutputPath)
                    result_data = ds_r[dataConfig.get("original").get("levels")[0][0]]
                for day in range(tmpStartDay, tmpEndDay + 1):  # 循环日
                    ymd = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(day)
                    dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace("#YYYYMMDD#",
                                                                                                         ymd)
                    ctlfile = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace("#YYYYMMDD#",
                                                                                                   ymd).replace('.dat',
                                                                                                                '.ctl')
                    fileContent = []
                    with open(ctlfile, 'r', encoding='utf-8') as f:
                        for line in f.readlines():
                            fileContent.append(line.lstrip())
                    fileContent[0] = 'dset ' + dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace(
                        "#YYYYMMDD#", '%y4%m2%d2') + '\n'
                    ctl_descriptor = CtlDescriptor(content=''.join(fileContent))
                    ctl_descriptor.dsetPath = [dataInputPath]

                    if os.path.exists(dataInputPath):
                        logging.info(dataInputPath)
                        ds = open_CtlDataset(ctl_descriptor)
                        # logging.info(ds)
                        # 重置变量名和维的名称
                        # logging.info(dataConfig.get("original").get("var")+"%%%%%"+dataInputPath)
                        # if dataConfig.get("original").get("var") not in ds.keys():
                        #     continue
                        # if dataConfig.get("original").get("var"):
                        #     ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                        if dataConfig.get("original").get("level"):
                            ds = ds.rename({dataConfig.get("original").get("level"): "level"})
                        if dataConfig.get("original").get("lat"):
                            ds = ds.rename({dataConfig.get("original").get("lat"): "lat"})
                        if dataConfig.get("original").get("lon"):
                            ds = ds.rename({dataConfig.get("original").get("lon"): "lon"})
                        # data = ds[dataConfig.get("var")][0]
                        # if dataConfig.get("original").get("levels"):
                        #     logging.info("只需要保留指定的高度层...")
                        #     data = data.sel(level=dataConfig.get("original").get("levels"))
                        # 单位转换
                        # logging.info("原始数据的大小范围在%s~%s..." % (data.min().values, data.max().values))
                        # if dataConfig.get("unitConvert"):
                        #     data.attrs['units'] = dataConfig.get("unitConvert").get("unitName")
                        #     convert_type, convert_value = dataConfig.get("unitConvert").get("unitProc").split("_")
                        #     logging.info("%s开始单位转换...转换公式为%s" % (
                        #         dataConfig.get("var"), [convert_type, convert_value]))
                        #     data_allx = convert_data(data, convert_type, convert_value)
                        #     data_allx.attrs = data.attrs
                        #     data = data_allx
                        #     logging.info("转换后的数据大小范围在%s~%s..." % (data.min().values, data.max().values))
                        #     logging.info(data.max().values)
                        #     if "valid_range" in data.attrs.keys():
                        #         data.attrs.pop('valid_range')
                        #     if "actual_range" in data.attrs.keys():
                        #         data.attrs.pop('actual_range')
                        # if dataConfig.get("var") in ["u100m","v100m"]:
                        # data = data.sel(lv_HTGL1=100)
                        # logging.info(data)
                        data_level = []
                        for i, ele in enumerate(dataConfig.get("original").get("levels")):
                            data = ds[ele][0]
                            data = xr.where(data == -999.0, np.nan, data)
                            data.expand_dims(dim="time", axis=0)
                            data["time"] = day
                            data["level"].values = [float(i + 1)]
                            data_level.append(data)
                        data = xr.concat(data_level, dim="level")
                        result_data_get.append(data)

                    else:
                        error_str = "源文件【%s】不存在!" % (dataInputPath)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)

                if len(result_data_get) != 0:
                    data_a = xr.concat(result_data_get, dim="time")
                    # 补全数据
                    if "result_data" in locals():
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)), result_data)
                    else:
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)))
                    # 判断结果数据是否存在，若存在就存储文件
                if "result_data" in locals():
                    self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                    del result_data
                    file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    def tbbtoNc(self, file_in, var, startLon, endLon, startLat, endLat):
        data_tbb = xr.open_dataset(file_in)
        data = data_tbb[var]
        data = np.where(data >= 65534, np.nan, data)

        # 4km分辨率
        raw_file = "/nfsshare/cdbdata/data/FY/FullMask_Grid_4000.raw"
        raw_data = open(raw_file, 'rb').read()
        np_raw_data = np.frombuffer(raw_data, dtype=np.double)
        reshaped_raw_data = np_raw_data.reshape((2748, 2748, 2))
        start_x_index = int(data_tbb["geospatial_lat_lon_extent"].attrs["begin_line_number"])
        end_x_index = int(data_tbb["geospatial_lat_lon_extent"].attrs["end_line_number"])
        start_y_index = int(data_tbb["geospatial_lat_lon_extent"].attrs["begin_pixel_number"])
        end_y_index = int(data_tbb["geospatial_lat_lon_extent"].attrs["end_pixel_number"])

        lat = reshaped_raw_data[start_x_index:end_x_index + 1, start_y_index:end_y_index + 1, 0]  # 175:1267
        lon = reshaped_raw_data[start_x_index:end_x_index + 1, start_y_index:end_y_index + 1, 1]
        lat = np.where(lat > 999, np.nan, lat)
        lon = np.where(lon > 999, np.nan, lon)
        lon = np.where(lon < 0, 360 + lon, lon)

        tmp = np.where(np.isnan(lon), np.nan, 1)
        data = data * tmp

        glon = np.linspace(startLon, endLon, (endLon - startLon) * 20 + 1).astype(np.float32)
        glat = np.linspace(startLat, endLat, (endLat - startLat) * 20 + 1).astype(np.float32)
        olon, olat = np.meshgrid(glon, glat)

        zlon1, zlat1, tmpdata = remove_nan_observations(lon.ravel(), lat.ravel(), data.ravel())
        data = scipy.interpolate.griddata((zlon1, zlat1), tmpdata, (olon, olat), method='nearest')
        data = np.where(data == 999999.0, np.nan, data)
        # result_data = xr.DataArray(data, coords=[glat, glon], dims=["lat", "lon"])
        # return result_data
        return data

    def regular_day_raw_data_fy4al2_tbb(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_day_raw_data_fy4al2_tbb")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                result_data_get = []
                # 计算当月的天数
                monDays = calendar.monthrange(year, mon)[1]
                # 计算当月的起止日
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                # 获取数据输出的路径
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym)
                logging.info(dataOutputPath)
                # 若输出文件存在，则获取数据
                if os.path.exists(dataOutputPath):
                    ds_r = xr.open_dataset(dataOutputPath)
                    result_data = ds_r[dataConfig.get("var")]
                for day in range(tmpStartDay, tmpEndDay + 1):  # 循环日
                    ymd = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(day)
                    dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace("#YYYYMMDD#",
                                                                                                         ymd)

                    # 文件名中包含时分秒，用#.*#
                    if not os.path.exists(os.path.dirname(dataInputPath)):
                        continue
                    file_list = os.listdir(os.path.dirname(dataInputPath))
                    re_filename = os.path.basename(dataInputPath).replace('#.*#', '.*')
                    getfilename = [i for i in file_list if re.findall(re_filename, i)]
                    dataInputPath_list = [os.path.dirname(dataInputPath) + '/' + i for i in getfilename]

                    startLon = dataConfig.get("original").get("startLon")
                    endLon = dataConfig.get("original").get("endLon")
                    startLat = dataConfig.get("original").get("startLat")
                    endLat = dataConfig.get("original").get("endLat")

                    glon = np.linspace(startLon, endLon, (endLon - startLon) * 20 + 1).astype(np.float32)
                    glat = np.linspace(startLat, endLat, (endLat - startLat) * 20 + 1).astype(np.float32)
                    if len(dataInputPath_list) != 0:
                        logging.info(dataInputPath_list)
                        ds_list = []
                        for tempfile in dataInputPath_list:
                            try:
                                tempdata = self.tbbtoNc(tempfile, dataConfig.get("original").get("var"), startLon, endLon, startLat, endLat)
                                ds_list.append(tempdata)
                            except Exception:
                                continue

                        data = np.nanmean(np.array(ds_list), axis=0)
                        data = xr.DataArray(data, coords=[glat, glon], dims=["lat", "lon"])
                        data.expand_dims(dim="time", axis=0)
                        data["time"] = day
                        result_data_get.append(data)
                    else:
                        error_str = "源文件【%s】不存在!" % (dataInputPath)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)

                if len(result_data_get) != 0:
                    data_a = xr.concat(result_data_get, dim="time")
                    # 补全数据
                    if "result_data" in locals():
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)), result_data)
                    else:
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)))
                # 判断结果数据是否存在，若存在就存储文件
                if "result_data" in locals():
                    self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                    del result_data
                    file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    def regular_day_raw_data_fy4al2_qpe(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_day_raw_data_fy4al2_qpe")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                result_data_get = []
                # 计算当月的天数
                monDays = calendar.monthrange(year, mon)[1]
                # 计算当月的起止日
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                # 获取数据输出的路径
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym)
                logging.info(dataOutputPath)
                # 若输出文件存在，则获取数据
                if os.path.exists(dataOutputPath):
                    ds_r = xr.open_dataset(dataOutputPath)
                    result_data = ds_r[dataConfig.get("var")]
                for day in range(tmpStartDay, tmpEndDay + 1):  # 循环日
                    ymd = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(day)
                    dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace("#YYYYMMDD#",
                                                                                                         ymd)

                    # 文件名中包含时分秒，用#.*#
                    if not os.path.exists(os.path.dirname(dataInputPath)):
                        continue
                    file_list = os.listdir(os.path.dirname(dataInputPath))
                    re_filename = os.path.basename(dataInputPath).replace('#.*#', '.*')
                    getfilename = [i for i in file_list if re.findall(re_filename, i)]
                    getfilenames = []
                    for qpefile in getfilename:
                        hour = qpefile[52:54]
                        hour59 = qpefile[67:71]
                        if hour + '59' == hour59:
                            getfilenames.append(qpefile)
                    dataInputPath_list = [os.path.dirname(dataInputPath) + '/' + i for i in getfilenames]

                    startLon = dataConfig.get("original").get("startLon")
                    endLon = dataConfig.get("original").get("endLon")
                    startLat = dataConfig.get("original").get("startLat")
                    endLat = dataConfig.get("original").get("endLat")

                    glon = np.linspace(startLon, endLon, (endLon - startLon) * 20 + 1).astype(np.float32)
                    glat = np.linspace(startLat, endLat, (endLat - startLat) * 20 + 1).astype(np.float32)
                    if len(dataInputPath_list) != 0:
                        logging.info(dataInputPath_list)
                        ds_list = []
                        for tempfile in dataInputPath_list:
                            try:
                                tempdata = self.tbbtoNc(tempfile, dataConfig.get("original").get("var"), startLon, endLon, startLat, endLat)
                                ds_list.append(tempdata)
                            except Exception:
                                continue

                        data = np.nansum(np.array(ds_list), axis=0)
                        data = xr.DataArray(data, coords=[glat, glon], dims=["lat", "lon"])
                        data.expand_dims(dim="time", axis=0)
                        data["time"] = day
                        result_data_get.append(data)
                    else:
                        error_str = "源文件【%s】不存在!" % (dataInputPath)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)

                if len(result_data_get) != 0:
                    data_a = xr.concat(result_data_get, dim="time")
                    # 补全数据
                    if "result_data" in locals():
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)), result_data)
                    else:
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)))
                # 判断结果数据是否存在，若存在就存储文件
                if "result_data" in locals():
                    self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                    del result_data
                    file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    def amvtoNc(self, ds_lat, ds_lon, ds_pres, ds_wd, ds_ws, var):
        data_lat = np.linspace(-50, 50, 101)
        data_lon = np.linspace(45, 145, 101)

        data_l = np.full((101, 101), np.nan)
        data_m = np.full((101, 101), np.nan)
        data_h = np.full((101, 101), np.nan)
        lat_line = ds_lat.ravel()
        lon_line = ds_lon.ravel()
        pres_line = ds_pres.ravel()
        wd_line = ds_wd.ravel()
        ws_line = ds_ws.ravel()
        for lon, lat, lev, d, s in zip(lon_line, lat_line, pres_line, wd_line, ws_line):
            m = int(lon - 45)
            n = int(lat + 50)
            if m >= 1 and m <= 101 and n >= 1 and n <= 101:
                if lev >= 100 and lev <= 399:
                    if var == "u":
                        data_h[m - 1][n - 1] = (-1) * s * math.sin(d * math.pi / 180)
                    elif var == "v":
                        data_h[m - 1][n - 1] = (-1) * s * math.cos(d * math.pi / 180)
                elif lev >= 400 and lev <= 699:
                    if var == "u":
                        data_m[m - 1][n - 1] = (-1) * s * math.sin(d * math.pi / 180)
                    elif var == "v":
                        data_m[m - 1][n - 1] = (-1) * s * math.cos(d * math.pi / 180)
                elif lev >= 700 and lev <= 950:
                    if var == "u":
                        data_l[m - 1][n - 1] = (-1) * s * math.sin(d * math.pi / 180)
                    elif var == "v":
                        data_l[m - 1][n - 1] = (-1) * s * math.cos(d * math.pi / 180)

        # result_data = xr.DataArray(data, coords=[data_lon, data_lat], dims=["lon", "lat"])

        return data_l, data_m, data_h

    def getU(self, pre, wd, ws, min, max):
        data_u = np.where(pre >= min, pre, np.nan)
        data_u = np.where(data_u <= max, data_u, np.nan)
        data_u = np.where(np.isnan(data_u), np.nan, 0.0)
        data_u = data_u + (-1) * ws * np.sin(wd * np.pi / 180)
        return data_u

    def getV(self, pre, wd, ws, min, max):
        data_v = np.where(pre >= min, pre, np.nan)
        data_v = np.where(data_v <= max, data_v, np.nan)
        data_v = np.where(np.isnan(data_v), np.nan, 0.0)
        data_v = data_v + (-1) * ws * np.cos(wd * np.pi / 180)
        return data_v

    def regular_day_raw_data_fy4al2_amv(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_day_raw_data_fy4al2_amv")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                result_data_get = []
                # 计算当月的天数
                monDays = calendar.monthrange(year, mon)[1]
                # 计算当月的起止日
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                # 获取数据输出的路径
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym)
                logging.info(dataOutputPath)
                # 若输出文件存在，则获取数据
                if os.path.exists(dataOutputPath):
                    ds_r = xr.open_dataset(dataOutputPath)
                    result_data = ds_r[dataConfig.get("var")]
                for day in range(tmpStartDay, tmpEndDay + 1):  # 循环日
                    ymd = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(day)
                    dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace("#YYYYMMDD#",
                                                                                                         ymd)

                    # 文件名中包含时分秒，用#.*#
                    dataInputPath_C009 = dataInputPath.replace("#ELE#", "C009")
                    if not os.path.exists(os.path.dirname(dataInputPath_C009)):
                        continue
                    file_list = os.listdir(os.path.dirname(dataInputPath_C009))
                    re_filename = os.path.basename(dataInputPath_C009).replace('#.*#', '.*')
                    getfilename = [i for i in file_list if re.findall(re_filename, i)]
                    dataInputPathC009_list = [os.path.dirname(dataInputPath_C009) + '/' + i for i in getfilename]

                    if len(dataInputPathC009_list) != 0:
                        logging.info(dataInputPathC009_list)
                        ds_l_list, ds_m_list, ds_h_list = [], [], []
                        ds_olat, ds_olon = None, None
                        data_olat = np.linspace(-50, 50, 101).astype(np.float32)
                        data_olon = np.linspace(45, 145, 101).astype(np.float32)
                        for temp in dataInputPathC009_list:
                            ds_l, ds_m, ds_h = None, None, None
                            data_l, data_m, data_h = None, None, None
                            data_lat, data_lon = None, None
                            for c_file in ["C009", "C010", "C012"]:
                                temp_file = temp.replace("C009", c_file)
                                if os.path.exists(temp_file):
                                    ds = xr.open_dataset(temp_file)
                                    ds_pre = ds["pressure"]
                                    ds_pre = np.where(ds_pre == -999, np.nan, ds_pre)
                                    ds_wd = ds["wind_direction"]
                                    ds_wd = np.where(ds_wd == -999, np.nan, ds_wd)
                                    ds_ws = ds["wind_speed"]
                                    ds_ws = np.where(ds_ws == -999, np.nan, ds_ws)
                                    ds_lat = ds["lat"].values
                                    ds_lon = ds["lon"].values

                                    data_l, data_m, data_h = self.amvtoNc(ds_lat, ds_lon, ds_pre, ds_wd, ds_ws, dataConfig.get("var"))

                                    if type(ds_l) == type(None):
                                        ds_l, ds_m, ds_h = data_l, data_m, data_h
                                        data_lat, data_lon = ds_lat, ds_lon
                                    ds_l = np.where(np.isnan(ds_l), data_l, ds_l)
                                    ds_m = np.where(np.isnan(ds_m), data_m, ds_m)
                                    ds_h = np.where(np.isnan(ds_h), data_h, ds_h)
                                    data_lat = np.where(np.isnan(data_lat), ds_lat, data_lat)
                                    data_lon = np.where(np.isnan(data_lon), ds_lon, data_lon)
                            if type(ds_olat) == type(None):
                                ds_olat = data_lat
                                ds_olon = data_lon
                            else:
                                ds_olat = np.where(np.isnan(ds_olat), data_lat, ds_olat)
                                ds_olon = np.where(np.isnan(ds_olon), data_lon, ds_olon)
                            ds_l_list.append(ds_l)
                            ds_m_list.append(ds_m)
                            ds_h_list.append(ds_h)

                        ds_l_mean = np.nanmean(np.array(ds_l_list), axis=0)  # 8,229,229
                        ds_m_mean = np.nanmean(np.array(ds_m_list), axis=0)
                        ds_h_mean = np.nanmean(np.array(ds_h_list), axis=0)

                        data_l = xr.DataArray(ds_l_mean.T, coords=[data_olat, data_olon], dims=["lat", "lon"])
                        data_m = xr.DataArray(ds_m_mean.T, coords=[data_olat, data_olon], dims=["lat", "lon"])
                        data_h = xr.DataArray(ds_h_mean.T, coords=[data_olat, data_olon], dims=["lat", "lon"])

                        data_l.expand_dims(dim="time", axis=0)
                        data_l["time"] = day
                        data_l["level"] = float(1)
                        data_m.expand_dims(dim="time", axis=0)
                        data_m["time"] = day
                        data_m["level"] = float(2)
                        data_h.expand_dims(dim="time", axis=0)
                        data_h["time"] = day
                        data_h["level"] = float(3)
                        data_level = [data_l, data_m, data_h]
                        data = xr.concat(data_level, dim="level")
                        result_data_get.append(data)
                    else:
                        error_str = "源文件【%s】不存在!" % (dataInputPath)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)

                if len(result_data_get) != 0:
                    data_a = xr.concat(result_data_get, dim="time")
                    # 补全数据
                    if "result_data" in locals():
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)), result_data)
                    else:
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)))
                # 判断结果数据是否存在，若存在就存储文件
                if "result_data" in locals():
                    self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                    del result_data
                    file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 规整冷暖昼夜现象数据 日
    def regular_lnzy_weater_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_lnzy_weater_data")
        # 获取现象阈值数据的输入位置
        weatherDataInputPath = dataConfig.get("weatherDataInputPath")
        ds_w = xr.open_dataset(weatherDataInputPath)
        weather_data = ds_w[dataConfig.get("weaterVar")]
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
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
                # 获取数据输出的路径
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym)
                # 若输出文件存在，则获取数据
                if os.path.exists(dataOutputPath):
                    ds_r = xr.open_dataset(dataOutputPath)
                    result_data = ds_r[dataConfig.get("resVar")]
                # 获取源数据的输入位置
                dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY_MM#", ym)
                if os.path.exists(dataInputPath):
                    # 加载数据
                    ds = xr.open_dataset(dataInputPath)
                    data_m = ds[dataConfig.get("var")]
                    # 筛选数据
                    data_m = data_m.sel(time=range(tmpStartDay, tmpEndDay + 1))
                    # 重置时间维的数值
                    # data_m.time.values = list(range(tmpStartDay, tmpEndDay + 1))
                    if startTime == endTime:  # 同一时间点直接抛异常
                        if np.isnan(data_m).all():
                            error_str = "源文件[%s]中%s的数据都是缺测值" % (
                                dataInputPath, DateUtils.time_format_ch(startTime, "day"))
                            raise AlgorithmException(response_code=DATA_ALL_MISS_CODE, response_msg=error_str)
                    # 获取现象阈值
                    startDayIndex = \
                        DateUtils.get_time_index([str(year) + "{0:02d}".format(mon) + "{0:02d}".format(tmpStartDay)],
                                                 "day")[0]
                    endDayIndex = \
                        DateUtils.get_time_index([str(year) + "{0:02d}".format(mon) + "{0:02d}".format(tmpEndDay)], "day")[
                            0]
                    data_wea = weather_data.isel(time=range(startDayIndex, endDayIndex + 1))
                    data_wea.time.values = data_m.time.values
                    # data = xr.where(data_m>=data_wea, 1, 0)
                    if dataConfig.get("logicType") == "ge":
                        data = xr.where(data_m.values >= data_wea.values, 1, 0)
                    if dataConfig.get("logicType") == "le":
                        data = xr.where(data_m.values <= data_wea.values, 1, 0)
                    data = xr.DataArray(data, dims=data_m.dims, coords=data_m.coords)
                    # 重置时间维的数值
                    data.time.values = list(range(tmpStartDay, tmpEndDay + 1))
                    # 补全数据
                    if "result_data" in locals():
                        result_data = self.makeup_data_by_time(data, list(range(1, monDays + 1)), result_data)
                    else:
                        result_data = self.makeup_data_by_time(data, list(range(1, monDays + 1)))
                    # 判断结果数据是否存在，若存在就存储文件
                    if "result_data" in locals():
                        self.writ_nc(result_data, dataConfig.get("resVar"), dataOutputPath)
                        del result_data
                        file_num = file_num + 1
                else:
                    error_str = "源文件【%s】不存在!" % (dataInputPath)
                    if startTime == endTime:  # 同一时间点直接抛异常
                        raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                    else:
                        logging.error(error_str)
        result_dict["file_num"] = str(file_num)
        return result_dict

        # 规整连续5日累计降水数据 日

    def regular_tp5d_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_tp5d_data")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                # 获取数据输出的路径
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym)
                # 若输出文件存在，则获取数据
                if os.path.exists(dataOutputPath):
                    ds_r = xr.open_dataset(dataOutputPath)
                    result_data = ds_r[dataConfig.get("resVar")]

                # 计算当月的天数
                monDays = calendar.monthrange(year, mon)[1]
                # 计算当月的起止日
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                mon_data_list = []
                for day in range(tmpStartDay, tmpEndDay + 1):  # 循环日
                    tmp_end_time = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(day)
                    tmp_start_time = DateUtils.getForwradTime(tmp_end_time, "day", -4)
                    tmp_start_day = int(tmp_start_time[6:])
                    if tmp_start_day > day:
                        # 获取源数据的输入位置
                        dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY_MM#", ym)
                        ym_prex = tmp_start_time[0:4] + "_" + tmp_start_time[4:6]
                        dataInputPath_prex = dataConfig.get("dataInputPath").replace("#YYYY_MM#", ym_prex)
                        if os.path.exists(dataInputPath) and os.path.exists(dataInputPath_prex):
                            ds_prex = xr.open_dataset(dataInputPath_prex)
                            data_m1 = ds_prex[dataConfig.get("var")]
                            tmpMonDays = calendar.monthrange(int(tmp_start_time[0:4]), int(tmp_start_time[4:6]))[1]
                            # 筛选数据
                            data_m1 = data_m1.isel(time=range(tmp_start_day - 1, tmpMonDays))
                            ds = xr.open_dataset(dataInputPath)
                            data_m2 = ds[dataConfig.get("var")]
                            # 筛选数据
                            data_m2 = data_m2.isel(time=range(0, day))
                            data_m = xr.concat([data_m1, data_m2], dim="time")
                            data_d = data_m.sum(dim="time")
                            data_d = data_d.expand_dims(dim="time")
                            data_d["time"] = [day]
                            mon_data_list.append(data_d)
                        else:
                            file_path = ""
                            if not os.path.exists(dataInputPath):
                                file_path = file_path + "," + dataInputPath
                            if not os.path.exists(dataInputPath_prex):
                                file_path = file_path + "," + dataInputPath_prex
                            error_str = "源文件【%s】不存在!" % (file_path[1:])
                            if startTime == endTime:  # 同一时间点直接抛异常
                                raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE,
                                                         response_msg=error_str)
                            else:
                                logging.error(error_str)
                    else:
                        # 获取源数据的输入位置
                        dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY_MM#", ym)
                        if os.path.exists(dataInputPath):
                            # 加载数据
                            ds = xr.open_dataset(dataInputPath)
                            data_m = ds[dataConfig.get("var")]
                            # 筛选数据
                            data_m = data_m.isel(time=range(tmp_start_day - 1, day))
                            if startTime == endTime:  # 同一时间点直接抛异常
                                if np.isnan(data_m).all():
                                    error_str = "源文件[%s]中%s的数据都是缺测值" % (
                                        dataInputPath, DateUtils.time_format_ch(startTime, "day"))
                                    raise AlgorithmException(response_code=DATA_ALL_MISS_CODE,
                                                             response_msg=error_str)
                            data_d = data_m.sum(dim="time")
                            data_d = data_d.expand_dims(dim="time")
                            data_d["time"] = [day]
                            mon_data_list.append(data_d)
                        else:
                            error_str = "源文件【%s】不存在!" % (dataInputPath)
                            if startTime == endTime:  # 同一时间点直接抛异常
                                raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE,
                                                         response_msg=error_str)
                            else:
                                logging.error(error_str)

                if len(mon_data_list) != 0:
                    data = xr.concat(mon_data_list, dim="time")
                    # 补全数据
                    if "result_data" in locals():
                        result_data = self.makeup_data_by_time(data, list(range(1, monDays + 1)), result_data)
                    else:
                        result_data = self.makeup_data_by_time(data, list(range(1, monDays + 1)))
                # 判断结果数据是否存在，若存在就存储文件
                if "result_data" in locals():
                    self.writ_nc(result_data, dataConfig.get("resVar"), dataOutputPath)
                    del result_data
                    file_num = file_num + 1

        result_dict["file_num"] = str(file_num)
        return result_dict

        # 规整CMA-GLST(v1.0)数据 月

    def regular_cmaglst_mon_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_cmaglst_mon_data")
        # 计算开始年 开始月
        startYear, startMon = int(str(startTime)[0:4]), int(str(startTime)[4:6])
        # 计算结束年 结束月
        endYear, endMon = int(str(endTime)[0:4]), int(str(endTime)[4:6])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 获取数据输出的路径
            dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", str(year))
            # 若输出文件存在，则获取数据
            if os.path.exists(dataOutputPath):
                ds_r = xr.open_dataset(dataOutputPath)
                result_data = ds_r[dataConfig.get("var")]
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            mon_data_list = []
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                ym = str(year) + "{0:02d}".format(mon)
                # 获取源数据的输入位置
                dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace("#YYYYMM#", ym)
                if os.path.exists(dataInputPath):
                    ds = xr.open_dataset(dataInputPath)
                    # 重置变量名和维的名称
                    if dataConfig.get("original"):
                        if dataConfig.get("original").get("var"):
                            ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                    tmpdata = ds[dataConfig.get("var")]
                    lats = ds["lat"].values
                    lons = ds["lon"].values
                    print(lats)
                    print(lons)
                    tmpdata["latitude"].values = lats
                    tmpdata["longitude"].values = lons
                    print(tmpdata.isel(longitude=351, latitude=20))
                    # exit()
                    tmpdata = xr.DataArray(tmpdata.values, coords=[lats, lons], dims=["lat", "lon"])
                    print(tmpdata.isel(lon=351, lat=20))
                    print(tmpdata.sel(lon=171.5, lat=69.5))
                    # exit()
                    lonx = tmpdata.lon
                    lonx = xr.where(lonx < 0, lonx + 360, lonx)
                    tmpdata["lon"].values = lonx.values
                    tmpdata = tmpdata.sortby(tmpdata["lon"])
                    tmpdata = tmpdata.expand_dims(dim="time")
                    tmpdata["time"] = [mon]
                    print(tmpdata.sel(lon=171.5, lat=69.5))
                    exit()
                    mon_data_list.append(tmpdata)
                else:
                    error_str = "源文件【%s】不存在!" % (dataInputPath)
                    if startTime == endTime:  # 同一时间点直接抛异常
                        raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE,
                                                 response_msg=error_str)
                    else:
                        logging.error(error_str)

            if len(mon_data_list) != 0:
                data = xr.concat(mon_data_list, dim="time")
                # 补全数据
                if "result_data" in locals():
                    result_data = self.makeup_data_by_time(data, list(range(1, 13)), result_data)
                else:
                    result_data = self.makeup_data_by_time(data, list(range(1, 13)))
            # 判断结果数据是否存在，若存在就存储文件
            if "result_data" in locals():
                self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                del result_data
                file_num = file_num + 1

        result_dict["file_num"] = str(file_num)
        return result_dict

    def regular_day_sta_data_multiple(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_day_sta_data_multiple")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            result_data_get = []
            dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", str(year))
            logging.info(dataOutputPath)
            # 若输出文件存在，则获取数据
            if os.path.exists(dataOutputPath):
                ds_r = xr.open_dataset(dataOutputPath)
                # logging.info(ds_r)
                result_data = ds_r[dataConfig.get("var")]
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
                    ym = str(year) + "{0:02d}".format(mon)
                    dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)) \
                        .replace("#YYYYMM#", ym).replace("#YYYYMMDD#", ymd)
                    if os.path.exists(dataInputPath):
                        logging.info(dataInputPath)
                        ds = xr.open_dataset(dataInputPath, engine='pynio')
                        # logging.info(ds)
                        data = ds[dataConfig.get("var")]
                        # 单位转换
                        logging.info("原始数据的大小范围在%s~%s..." % (data.min().values, data.max().values))
                        if dataConfig.get("unitConvert"):
                            data.attrs['units'] = dataConfig.get("unitConvert").get("unitName")
                            convert_type, convert_value = dataConfig.get("unitConvert").get("unitProc").split("_")
                            logging.info("%s开始单位转换...转换公式为%s" % (
                                dataConfig.get("var"), [convert_type, convert_value]))
                            data_allx = convert_data(data, convert_type, convert_value)
                            data_allx.attrs = data.attrs
                            data = data_allx
                            logging.info("转换后的数据大小范围在%s~%s..." % (data.min().values, data.max().values))
                            logging.info(data.max().values)
                            if "valid_range" in data.attrs.keys():
                                data.attrs.pop('valid_range')
                            if "actual_range" in data.attrs.keys():
                                data.attrs.pop('actual_range')
                        data.expand_dims(dim="time", axis=0)
                        data["time"] = DateUtils.get_time_index([ymd], "day")[0] + 1
                        result_data_get.append(data)
                    else:
                        error_str = "源文件【%s】不存在!" % (dataInputPath)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)

            if len(result_data_get) != 0:
                data_a = xr.concat(result_data_get, dim="time")
                # 补全数据
                if "result_data" in locals():
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 367)), result_data)
                else:
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 367)))
            # 判断结果数据是否存在，若存在就存储文件
            if "result_data" in locals():
                self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                del result_data
                file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 站点数据转换成格点数据
    def regular_station2grid_day_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_station2grid_day_data")
        # 获取全国站点基础信息
        dataInputStation = dataConfig.get("dataInputStation")
        data = pd.read_table(dataInputStation, header=None, encoding='utf-8', sep="\t")
        stationInfo = np.array(data)
        locs = ['station', 'lon', 'lat', 'level']
        stations = stationInfo[:, 0]
        stationInfoData = xr.DataArray(stationInfo, coords=[stations, locs], dims=['station', 'space'])
        zlat, zlon = stationInfoData.sel(space="lat"), stationInfoData.sel(space="lon")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                result_data_get = []
                # 获取数据输出的路径
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym)
                logging.info(dataOutputPath)
                # 若输出文件存在，则获取数据
                if os.path.exists(dataOutputPath):
                    ds_r = xr.open_dataset(dataOutputPath)
                    result_data = ds_r[dataConfig.get("resVar")]
                # 计算当月的天数
                monDays = calendar.monthrange(year, mon)[1]
                # 计算当月的起止日
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                # 计算当月的起止日在一年中的位置
                startDayIndex = DateUtils.get_time_index([str(year) + "{0:02d}".format(mon) + "{0:02d}".format(tmpStartDay)], "day")[0]
                endDayIndex = DateUtils.get_time_index([str(year) + "{0:02d}".format(mon) + "{0:02d}".format(tmpEndDay)], "day")[0]
                dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year))
                if os.path.exists(dataInputPath):
                    ds = xr.open_dataset(dataInputPath)
                    # 计算当前年的起止月份
                    data_m = ds[dataConfig.get("var")]
                    data_w = data_m.isel(time=range(startDayIndex, endDayIndex + 1))
                    data_w.time.values = np.asarray(range(tmpStartDay, tmpEndDay + 1), dtype=np.int32)
                    tmp_sta_data = data_w.sel(station=stationInfoData.station.values)
                    # 单位转换
                    if dataConfig.get("unitConvert"):
                        tmp_sta_data.attrs['units'] = dataConfig.get("unitConvert").get("unitName")
                        convert_type, convert_value = dataConfig.get("unitConvert").get("unitProc").split("_")
                        tmp_sta_datax = convert_data(tmp_sta_data, convert_type, convert_value)
                        tmp_sta_datax.attrs = tmp_sta_data.attrs
                        tmp_sta_data = tmp_sta_datax
                        logging.info(tmp_sta_data.max().values)
                        if "valid_range" in tmp_sta_data.attrs.keys():
                            tmp_sta_data.attrs.pop('valid_range')
                        if "actual_range" in tmp_sta_data.attrs.keys():
                            tmp_sta_data.attrs.pop('actual_range')
                    lats = dataConfig.get("interp").get("lats")
                    lons = dataConfig.get("interp").get("lons")
                    interp_grid_data = self.interp_ref(tmp_sta_data, lats, lons, zlat, zlon)
                    # 负值处理成0
                    if dataConfig.get("negativeType", "0") == "1":
                        interp_grid_data = xr.where(interp_grid_data < 0, 0, interp_grid_data)
                    result_data_get.append(interp_grid_data)
                else:
                    error_str = "源文件【%s】不存在!" % (dataInputPath)
                    if startTime == endTime:  # 同一时间点直接抛异常
                        raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                    else:
                        logging.error(error_str)
                if len(result_data_get) != 0:
                    data_a = xr.concat(result_data_get, dim="time")
                    # 补全数据
                    if "result_data" in locals():
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)), result_data)
                    else:
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)))
                # 判断结果数据是否存在，若存在就存储文件
                if "result_data" in locals():
                    self.writ_nc(result_data, dataConfig.get("resVar"), dataOutputPath)
                    del result_data
                    file_num = file_num + 1
        result_dict["file_num"] = str(file_num)

        return result_dict

    # 站点数据转换成格点数据
    def regular_station2grid_mon_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_station2grid_mon_data")
        # 获取全国站点基础信息
        dataInputStation = dataConfig.get("dataInputStation")
        data = pd.read_table(dataInputStation, header=None, encoding='utf-8', sep="\t")
        stationInfo = np.array(data)
        locs = ['station', 'lon', 'lat', 'level']
        stations = stationInfo[:, 0]
        stationInfoData = xr.DataArray(stationInfo, coords=[stations, locs], dims=['station', 'space'])
        zlat, zlon = stationInfoData.sel(space="lat"), stationInfoData.sel(space="lon")
        # 计算开始年 开始月
        startYear, startMon = int(str(startTime)[0:4]), int(str(startTime)[4:6])
        # 计算结束年 结束月
        endYear, endMon = int(str(endTime)[0:4]), int(str(endTime)[4:6])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            result_data_get = []
            dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", str(year))
            logging.info(dataOutputPath)
            # 若输出文件存在，则获取数据
            if os.path.exists(dataOutputPath):
                ds_r = xr.open_dataset(dataOutputPath)
                result_data = ds_r[dataConfig.get("resVar")]
            dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year))
            if os.path.exists(dataInputPath):
                ds = xr.open_dataset(dataInputPath)
                # 计算当前年的起止月份
                tmpStartMon = np.where(year == startYear, startMon, 1)
                tmpEndMon = np.where(year == endYear, endMon, 12)
                tmpStartIndex = tmpStartMon - 1
                tmpEndIndex = tmpEndMon - 1
                # logging.info(tmpStartMon,tmpEndMon)
                data_m = ds[dataConfig.get("var")]
                data_w = data_m.isel(time=range(tmpStartIndex, tmpEndIndex + 1))
                tmp_sta_data = data_w.sel(station=stationInfoData.station.values)
                # 单位转换
                if dataConfig.get("unitConvert"):
                    tmp_sta_data.attrs['units'] = dataConfig.get("unitConvert").get("unitName")
                    convert_type, convert_value = dataConfig.get("unitConvert").get("unitProc").split("_")
                    tmp_sta_datax = convert_data(tmp_sta_data, convert_type, convert_value)
                    tmp_sta_datax.attrs = tmp_sta_data.attrs
                    tmp_sta_data = tmp_sta_datax
                    logging.info(tmp_sta_data.max().values)
                    if "valid_range" in tmp_sta_data.attrs.keys():
                        tmp_sta_data.attrs.pop('valid_range')
                    if "actual_range" in tmp_sta_data.attrs.keys():
                        tmp_sta_data.attrs.pop('actual_range')
                lats = dataConfig.get("interp").get("lats")
                lons = dataConfig.get("interp").get("lons")
                interp_grid_data = self.interp_ref(tmp_sta_data, lats, lons, zlat, zlon)
                # 负值处理成0
                if dataConfig.get("negativeType", "0") == "1":
                    interp_grid_data = xr.where(interp_grid_data < 0, 0, interp_grid_data)
                result_data_get.append(interp_grid_data)

            else:
                error_str = "源文件【%s】不存在!" % (dataInputPath)
                if startTime == endTime:  # 同一时间点直接抛异常
                    raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                else:
                    logging.error(error_str)
            if len(result_data_get) != 0:
                data_a = xr.concat(result_data_get, dim="time")
                # 补全数据
                if "result_data" in locals():
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 13)), result_data)
                else:
                    result_data = self.makeup_data_by_time(data_a, list(range(1, 13)))
            # 判断结果数据是否存在，若存在就存储文件
            if "result_data" in locals():
                self.writ_nc(result_data, dataConfig.get("resVar"), dataOutputPath)
                del result_data
                file_num = file_num + 1
        result_dict["file_num"] = str(file_num)

        return result_dict

    # @nb.jit(forceobj=True)
    def interp_ref(self, inputData, lats, lons, zlat, zlon):
        glon = np.linspace(lons[0], lons[1], lons[2])
        glat = np.linspace(lats[0], lats[1], lats[2])
        olon, olat = np.meshgrid(glon, glat)
        times = inputData["time"].values
        expand_dim_name = "time"
        interp_data = []
        for ii, tt in enumerate(times):
            tmpdata = inputData.isel(time=ii)
            if len(tmpdata) == 0 or np.isnan(tmpdata.values).all():
                interpData = np.full([lats[2], lons[2]], np.nan)
            else:
                zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, tmpdata)
                rf = Rbf(zlon1, zlat1, tmpdata.values, kind="thin_plate", smooth=0.2)
                interpData = rf(olon, olat)
                interpData = interpData.reshape((lats[2], lons[2]))
            interpData = xr.DataArray(interpData, coords=[glat, glon], dims=['lat', 'lon'])
            interpData = interpData.expand_dims(expand_dim_name)
            interpData[expand_dim_name] = [tt]
            interp_data.append(interpData)
        interp_grid_data = xr.concat(interp_data, dim=expand_dim_name)
        return interp_grid_data

    def regular_lwjs_day_txt_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_lwjs_day_txt_data")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            result_data_get_dict = {}
            result_data_dict = {}
            head_str = None
            dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", str(year))
            logging.info(dataOutputPath)
            # 若输出文件存在，则获取数据
            if os.path.exists(dataOutputPath):
                with open(dataOutputPath, "r") as f:
                    result_data_list = f.readlines()
                if head_str is None:
                    head_str = result_data_list[0].strip()
                for rd in result_data_list[1:]:
                    result_data_dict[rd[0:8]] = rd.strip()

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
                    ym = str(year) + "{0:02d}".format(mon)
                    dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace("#YYYYMM#", ym).replace("#YYYYMMDD#", ymd)
                    if os.path.exists(dataInputPath):
                        logging.info(dataInputPath)
                        ds = xr.open_dataset(dataInputPath, engine='pynio')
                        # logging.info(ds)
                        data = ds[dataConfig.get("var")]
                        if head_str is None:
                            sta_list = list(map(int, data.station.values))
                            stax = list(map(str, sta_list))
                            stax.insert(0, "time")
                            head_str = "\t".join(stax)
                        tmp_list = list(map(str, formatting_data(2, "round", data.values)))
                        tmp_list.insert(0, str(ymd))
                        tmp_str = "\t".join(tmp_list).replace("nan", "999999")
                        result_data_dict[str(ymd)] = tmp_str
                    else:
                        error_str = "源文件【%s】不存在!" % (dataInputPath)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)

            if result_data_dict:
                # 判断输出目录是否存在，不存在就创建
                str_dir = os.path.dirname(dataOutputPath)
                # logging.info(out_file_path)
                if not os.path.exists(str_dir):
                    os.makedirs(str_dir)
                start_time = str(np.min(np.array(list(result_data_dict.keys()), dtype=np.int32)))
                end_time = str(np.max(np.array(list(result_data_dict.keys()), dtype=np.int32)))
                # print(start_time,end_time)
                res_time_list = DateUtils.get_time_list([start_time, end_time], "day")
                res_data_list = []
                res_data_list.append(head_str)
                for rt in res_time_list:
                    if rt in result_data_dict.keys():
                        res_data_list.append(result_data_dict.get(rt))
                    else:
                        nan_list = ["999999"] * (len(head_str.split()) - 1)
                        nan_list.insert(0, str(rt))
                        res_data_list.append("\t".join(nan_list))

                with open(dataOutputPath, "w") as fo:
                    fo.write("\r\n".join(res_data_list))
                file_num = file_num + 1

        result_dict["file_num"] = str(file_num)
        return result_dict

    # 规整小时，源数据时小时文件，规整为24个小时一个文件，文件名时间为世界时，切换到北京时
    def regular_hour_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_hour_data")
        logging.info("dataConfig:-->" + str(dataConfig))
        # 计算开始年，开始月，开始日，开始时
        startYear, startMon, startDay, startHour = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(
            str(startTime)[6:8]), int(str(startTime)[8:10])
        # 计算结束年，结束月，结束日，结束时
        endYear, endMon, endDay, endHour = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8]), int(
            str(endTime)[8:10])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                # 计算当前月的起止日
                monDays = calendar.monthrange(year, mon)[1]
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                for day in range(tmpStartDay, tmpEndDay + 1):  # 循环日
                    ymd = str(year) + "_{0:02d}".format(mon) + "_{0:02d}".format(day)
                    result_data_get = []
                    dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", ymd[0:4]).replace("#YYYY_MM_DD#", ymd)
                    logging.info(dataOutputPath)
                    # 若输出文件存在，则获取数据
                    if os.path.exists(dataOutputPath):
                        ds_r = xr.open_dataset(dataOutputPath)
                        result_data = ds_r[dataConfig.get("var")]
                    # 计算当前日的起止时
                    tmpStartHour = np.where(year == startYear and mon == startMon and day == startDay, startHour, 1)
                    tmpEndHour = np.where(year == endYear and mon == endMon and day == endDay, endHour, 24)
                    t_day = datetime.datetime.strptime(ymd, "%Y_%m_%d")
                    for hour in range(tmpStartHour, tmpEndHour + 1):  # 循环小时 [1,24] -> [1-0]
                        # 北京时转世界时
                        # ymdh = str(year) + "_{0:02d}".format(mon) + "_{0:02d}".format(day) + "_{0:02d}".format(hour)
                        # t_bj = datetime.datetime.strptime(ymdh, "%Y_%m_%d_%H")
                        # t_utc = t_bj - datetime.timedelta(hours=8)
                        t_bj = t_day + datetime.timedelta(hours=hour)
                        t_utc = t_bj - datetime.timedelta(hours=8)
                        ymdh_utc = datetime.datetime.strftime(t_utc, "%Y%m%d%H")

                        logging.info("{} 获取北京时{}-{}-{} {} 世界时{}-{}-{} {}".format(hour, t_bj.year, t_bj.month, t_bj.day,
                                                                                         t_bj.hour, t_utc.year, t_utc.month,
                                                                                         t_utc.day, t_utc.hour))
                        dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", ymdh_utc[0:4]).replace("#YYYYMMDD#",
                                                                                                                 ymdh_utc[0:8]).replace(
                            "#YYYYMMDDHH#", ymdh_utc)
                        file_list = os.listdir(os.path.dirname(dataInputPath))
                        re_filename = os.path.basename(dataInputPath).replace('#.*#', '.*')
                        getfilename = [i for i in file_list if re.findall(re_filename, i)]
                        if len(getfilename) != 0:
                            dataInputPath = os.path.dirname(dataInputPath) + '/' + getfilename[0]
                        if os.path.exists(dataInputPath):
                            logging.info("获取到nc文件：{}".format(dataInputPath))
                            ds = xr.open_dataset(dataInputPath, engine='pynio')
                            # 重置变量名和维的名称
                            if dataConfig.get("original").get("var") not in ds.keys():
                                continue
                            if dataConfig.get("original").get("var"):
                                ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                            if dataConfig.get("original").get("lat"):
                                ds = ds.rename({dataConfig.get("original").get("lat"): "lat"})
                            if dataConfig.get("original").get("lon"):
                                ds = ds.rename({dataConfig.get("original").get("lon"): "lon"})
                            data = ds[dataConfig.get("var")]

                            # 剪裁数据
                            startlon = dataConfig.get("original").get("startLon")
                            endlon = dataConfig.get("original").get("endLon")
                            startlat = dataConfig.get("original").get("startLat")
                            endlat = dataConfig.get("original").get("endLat")
                            data = data.loc[startlat:endlat, startlon:endlon]

                            data.expand_dims(dim="time", axis=0)
                            data["time"] = hour
                            result_data_get.append(data)
                        else:
                            logging.info("源文件不存在")
                            error_str = "源文件【%s】不存在!" % (dataInputPath)
                            if startTime == endTime:  # 同一时间点直接抛异常
                                raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE,
                                                         response_msg=error_str)
                            else:
                                logging.info(error_str)

                    if len(result_data_get) != 0:
                        data_a = xr.concat(result_data_get, dim="time")
                        # 补全数据
                        if "result_data" in locals():
                            result_data = self.makeup_data_by_time(data_a, list(range(1, 25)), result_data)
                        else:
                            result_data = self.makeup_data_by_time(data_a, list(range(1, 25)))
                    # 判断结果数据是否存在，若存在就存储文件
                    if "result_data" in locals():
                        self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                        del result_data
                        file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 规整小时，源数据时小时文件，规整为24个小时一个文件，文件名时间为世界时，切换到北京时
    def regular_hour_data_history(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_hour_data_history")
        logging.info("dataConfig:-->" + str(dataConfig))
        # 计算开始年，开始月，开始日，开始时
        startYear, startMon, startDay, startHour = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(
            str(startTime)[6:8]), int(str(startTime)[8:10])
        # 计算结束年，结束月，结束日，结束时
        endYear, endMon, endDay, endHour = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(
            str(endTime)[6:8]), int(str(endTime)[8:10])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                # 计算当前月的起止日
                monDays = calendar.monthrange(year, mon)[1]
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                for day in range(tmpStartDay, tmpEndDay + 1):  # 循环日
                    ymd = str(year) + "_{0:02d}".format(mon) + "_{0:02d}".format(day)
                    result_data_get = []
                    dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", ymd[0:4]).replace("#YYYY_MM_DD#", ymd)
                    logging.info(dataOutputPath)
                    # 若输出文件存在，则获取数据
                    if os.path.exists(dataOutputPath):
                        ds_r = xr.open_dataset(dataOutputPath)
                        result_data = ds_r[dataConfig.get("var")]
                    # 计算当前日的起止时
                    tmpStartHour = np.where(year == startYear and mon == startMon and day == startDay, startHour, 1)
                    tmpEndHour = np.where(year == endYear and mon == endMon and day == endDay, endHour, 24)
                    t_day = datetime.datetime.strptime(ymd, "%Y_%m_%d")
                    for hour in range(tmpStartHour, tmpEndHour + 1):  # 循环小时 [1,24] -> [1-0]
                        # 北京时转世界时
                        # ymdh = str(year) + "_{0:02d}".format(mon) + "_{0:02d}".format(day) + "_{0:02d}".format(hour)
                        # t_bj = datetime.datetime.strptime(ymdh, "%Y_%m_%d_%H")
                        # t_utc = t_bj - datetime.timedelta(hours=8)
                        t_bj = t_day + datetime.timedelta(hours=hour)
                        t_utc = t_bj - datetime.timedelta(hours=8)
                        ymdh_utc = datetime.datetime.strftime(t_utc, "%Y%m%d%H")

                        logging.info(
                            "{} 获取北京时{}-{}-{} {} 世界时{}-{}-{} {}".format(hour, t_bj.year, t_bj.month,
                                                                                t_bj.day,
                                                                                t_bj.hour, t_utc.year, t_utc.month,
                                                                                t_utc.day, t_utc.hour))
                        if hour < 8 or hour > 20:
                            utcadd1 = t_utc + datetime.timedelta(days=1)
                            dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", utcadd1.strftime("%Y")).replace(
                                "#YYYYMMDD#", utcadd1.strftime("%Y%m%d")).replace("#YYYYMMDDHH#", ymdh_utc)
                        else:
                            dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", ymdh_utc[0:4]).replace(
                                "#YYYYMMDD#", ymdh_utc[0:8]).replace("#YYYYMMDDHH#", ymdh_utc)
                        if os.path.exists(dataInputPath):
                            logging.info("获取到nc文件：{}".format(dataInputPath))
                            ds = xr.open_dataset(dataInputPath, engine='netcdf4')
                            # 重置变量名和维的名称
                            if dataConfig.get("original").get("var") not in ds.keys():
                                continue
                            if dataConfig.get("original").get("var"):
                                ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                            if dataConfig.get("original").get("lat"):
                                ds = ds.rename({dataConfig.get("original").get("lat"): "lat"})
                            if dataConfig.get("original").get("lon"):
                                ds = ds.rename({dataConfig.get("original").get("lon"): "lon"})
                            data = ds[dataConfig.get("var")]
                            # data = data[416:512:,896:1024:]
                            data.expand_dims(dim="time", axis=0)
                            data["time"] = hour
                            result_data_get.append(data)
                        else:
                            logging.info("源文件不存在")
                            error_str = "源文件【%s】不存在!" % (dataInputPath)
                            if startTime == endTime:  # 同一时间点直接抛异常
                                raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE,
                                                         response_msg=error_str)
                            else:
                                logging.info(error_str)

                    if len(result_data_get) != 0:
                        data_a = xr.concat(result_data_get, dim="time")
                        # 补全数据
                        if "result_data" in locals():
                            result_data = self.makeup_data_by_time(data_a, list(range(1, 25)), result_data)
                        else:
                            result_data = self.makeup_data_by_time(data_a, list(range(1, 25)))
                    # 判断结果数据是否存在，若存在就存储文件
                    if "result_data" in locals():
                        self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                        del result_data
                        file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    # 规整小时，源数据时小时文件，规整为24个小时一个文件，文件名时间为北京时
    def regular_hour_data_bj(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_hour_data_bj")
        logging.info("dataConfig:-->" + str(dataConfig))
        # 计算开始年，开始月，开始日，开始时
        startYear, startMon, startDay, startHour = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(
            str(startTime)[6:8]), int(str(startTime)[8:10])
        # 计算结束年，结束月，结束日，结束时
        endYear, endMon, endDay, endHour = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8]), int(
            str(endTime)[8:10])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                # 计算当前月的起止日
                monDays = calendar.monthrange(year, mon)[1]
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                for day in range(tmpStartDay, tmpEndDay + 1):  # 循环日
                    ymd = str(year) + "_{0:02d}".format(mon) + "_{0:02d}".format(day)
                    result_data_get = []
                    dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", str(year)).replace("#YYYY_MM_DD#", ymd)
                    logging.info(dataOutputPath)
                    # 若输出文件存在，则获取数据
                    if os.path.exists(dataOutputPath):
                        ds_r = xr.open_dataset(dataOutputPath)
                        result_data = ds_r[dataConfig.get("var")]
                    # 计算当前日的起止时
                    tmpStartHour = np.where(year == startYear and mon == startMon and day == startDay, startHour, 1)
                    tmpEndHour = np.where(year == endYear and mon == endMon and day == endDay, endHour, 24)
                    t_day = datetime.datetime.strptime(ymd, "%Y_%m_%d")
                    for hour in range(tmpStartHour, tmpEndHour + 1):  # 循环小时 [1,24] -> [1-0]
                        # 北京时转世界时
                        # ymdh = str(year) + "_{0:02d}".format(mon) + "_{0:02d}".format(day) + "_{0:02d}".format(hour)
                        # t_bj = datetime.datetime.strptime(ymdh, "%Y_%m_%d_%H")
                        # t_utc = t_bj - datetime.timedelta(hours=8)
                        t_bj = t_day + datetime.timedelta(hours=hour)
                        ymdh = datetime.datetime.strftime(t_bj, "%Y%m%d%H")

                        dataInputPath = dataConfig.get("dataInputPath").replace("#YYYYMMDDHH#", ymdh)
                        file_list = os.listdir(os.path.dirname(dataInputPath))
                        re_filename = os.path.basename(dataInputPath).replace('#.*#', '.*')
                        getfilename = [i for i in file_list if re.findall(re_filename, i)]
                        if len(getfilename) != 0:
                            dataInputPath = os.path.dirname(dataInputPath) + '/' + getfilename[0]
                        if os.path.exists(dataInputPath):
                            logging.info("获取到nc文件：{}".format(dataInputPath))
                            ds = xr.open_dataset(dataInputPath, engine='pynio')
                            # 重置变量名和维的名称
                            if dataConfig.get("original").get("var") not in ds.keys():
                                continue
                            if dataConfig.get("original").get("var"):
                                ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                            if dataConfig.get("original").get("lat"):
                                ds = ds.rename({dataConfig.get("original").get("lat"): "lat"})
                            if dataConfig.get("original").get("lon"):
                                ds = ds.rename({dataConfig.get("original").get("lon"): "lon"})
                            data = ds[dataConfig.get("var")]
                            data.expand_dims(dim="time", axis=0)
                            data["time"] = hour
                            result_data_get.append(data)
                        else:
                            logging.info("源文件不存在")
                            error_str = "源文件【%s】不存在!" % (dataInputPath)
                            if startTime == endTime:  # 同一时间点直接抛异常
                                raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE,
                                                         response_msg=error_str)
                            else:
                                logging.info(error_str)

                    if len(result_data_get) != 0:
                        data_a = xr.concat(result_data_get, dim="time")
                        # 补全数据
                        if "result_data" in locals():
                            result_data = self.makeup_data_by_time(data_a, list(range(1, 25)), result_data)
                        else:
                            result_data = self.makeup_data_by_time(data_a, list(range(1, 25)))
                    # 判断结果数据是否存在，若存在就存储文件
                    if "result_data" in locals():
                        self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                        del result_data
                        file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    def regular_hour2day_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_hour2day_data")
        logging.info("dataConfig:-->" + str(dataConfig))
        # 计算开始年，开始月，开始日，开始时
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年，结束月，结束日，结束时
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                result_data_get = []
                monDays = calendar.monthrange(year, mon)[1]
                ym = str(year) + '_' + "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", str(year)).replace("#YYYY_MM#", ym)
                logging.info(dataOutputPath)
                # 若输出文件存在，则获取数据
                if os.path.exists(dataOutputPath):
                    ds_r = xr.open_dataset(dataOutputPath)
                    result_data = ds_r[dataConfig.get("var")]
                # 计算当前月的起止日
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)

                for day in range(tmpStartDay, tmpEndDay + 1):  # 循环日
                    # t_day = datetime.datetime.strptime(ym, "%Y%d") + datetime.timedelta(hours=day)
                    ymd = str(year) + '_' + "{0:02d}".format(mon) + "_{0:02d}".format(day)
                    dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", ymd[0:4]).replace("#YYYY_MM_DD#", ymd)
                    yesterday = datetime.datetime.strptime(ymd, "%Y_%m_%d") - datetime.timedelta(days=1)
                    yesterday = datetime.datetime.strftime(yesterday, "%Y_%m_%d")
                    dataInputPath1 = dataConfig.get("dataInputPath").replace("#YYYY#", yesterday[0:4]).replace("#YYYY_MM_DD#", yesterday)
                    if os.path.exists(dataInputPath) and os.path.exists(dataInputPath1):
                        logging.info("获取到nc文件：{},{}".format(dataInputPath, dataInputPath1))
                        # 读取dataInputPath中1-19,dataInputPath1中20-24,然后判断缺测阈值，平均
                        ds = xr.open_dataset(dataInputPath, engine='netcdf4')
                        data = ds.sel(time=list(range(1, 20)))
                        ds1 = xr.open_dataset(dataInputPath1, engine='netcdf4')
                        data1 = ds1.sel(time=list(range(20, 25)))
                        ds = xr.combine_nested([data, data1], concat_dim=["time"])

                        # 判断阈值 ,缺测时次大于等于5，视为缺测
                        not_nan_time = ds.count(dim="time")[dataConfig.get("original").get("var")][0][0]
                        if (24 - not_nan_time) >= 5:
                            error_str = "源文件【%s,%s】数据缺测" % (dataInputPath, dataInputPath1)
                            logging.info("数据时次缺测数达到阈值，视为缺测。" + error_str)
                            continue
                        if dataConfig.get("original").get("var"):
                            ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                        if dataConfig.get("original").get("lat"):
                            ds = ds.rename({dataConfig.get("original").get("lat"): "lat"})
                        if dataConfig.get("original").get("lon"):
                            ds = ds.rename({dataConfig.get("original").get("lon"): "lon"})
                        data = ds[dataConfig.get("var")]
                        # 数据转换
                        if dataConfig.get("dataConvert"):
                            convert_type = dataConfig.get("dataConvert").get("dataProc")
                            data = data_convert(data, convert_type)
                        else:
                            data = data_convert(data, "avg")
                        # data.expand_dims(time="time", axis=0)
                        data["time"] = day
                        result_data_get.append(data)
                    else:
                        logging.info("源文件不存在")
                        error_str = "源文件【%s】不存在!" % (dataInputPath)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE,
                                                     response_msg=error_str)
                        else:
                            logging.info(error_str)

                if len(result_data_get) != 0:
                    data_a = xr.concat(result_data_get, dim="time")
                    # 补全数据
                    if "result_data" in locals():
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)), result_data)
                    else:
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)))
                # 判断结果数据是否存在，若存在就存储文件
                if "result_data" in locals():
                    self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                    del result_data
                    file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    def CalculateRH(self, T, P, Q):
        E = 6.112 * np.exp(17.67 * (T - 273.16) / (T - 29.76))
        e = P * Q / (0.622 + 0.378 * Q)
        RH = e / E
        return RH

    def regular_hour_data_rh(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_hour_data_rh")
        logging.info("dataConfig:-->" + str(dataConfig))
        # 计算开始年，开始月，开始日，开始时
        startYear, startMon, startDay, startHour = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(
            str(startTime)[6:8]), int(str(startTime)[8:10])
        # 计算结束年，结束月，结束日，结束时
        endYear, endMon, endDay, endHour = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8]), int(
            str(endTime)[8:10])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                # 计算当前月的起止日
                monDays = calendar.monthrange(year, mon)[1]
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                for day in range(tmpStartDay, tmpEndDay + 1):  # 循环日
                    ymd = str(year) + "_{0:02d}".format(mon) + "_{0:02d}".format(day)
                    result_data_get = []
                    dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY#", str(year)).replace("#YYYY_MM_DD#", ymd)
                    logging.info(dataOutputPath)
                    # 若输出文件存在，则获取数据
                    if os.path.exists(dataOutputPath):
                        ds_r = xr.open_dataset(dataOutputPath)
                        result_data = ds_r[dataConfig.get("var")]
                    # 计算当前日的起止时
                    tmpStartHour = np.where(year == startYear and mon == startMon and day == startDay, startHour, 1)
                    tmpEndHour = np.where(year == endYear and mon == endMon and day == endDay, endHour, 24)
                    t_day = datetime.datetime.strptime(ymd, "%Y_%m_%d")
                    for hour in range(tmpStartHour, tmpEndHour + 1):  # 循环小时 [1,24] -> [1-0]
                        # 北京时转世界时
                        # ymdh = str(year) + "_{0:02d}".format(mon) + "_{0:02d}".format(day) + "_{0:02d}".format(hour)
                        # t_bj = datetime.datetime.strptime(ymdh, "%Y_%m_%d_%H")
                        # t_utc = t_bj - datetime.timedelta(hours=8)
                        t_bj = t_day + datetime.timedelta(hours=hour)
                        t_utc = t_bj - datetime.timedelta(hours=8)
                        ymdh_utc = datetime.datetime.strftime(t_utc, "%Y%m%d%H")

                        logging.info("{} 获取北京时{}-{}-{} {} 世界时{}-{}-{} {}".format(hour, t_bj.year, t_bj.month, t_bj.day,
                                                                                         t_bj.hour, t_utc.year, t_utc.month,
                                                                                         t_utc.day, t_utc.hour))
                        # 多个要素
                        dataInputPath_dict = {}
                        eles = dataConfig.get("ELE")
                        for ele, original in eles.items():
                            dataInputPath = dataConfig.get("dataInputPath").replace("#YYYYMMDDHH#", ymdh_utc).replace(
                                "#ELE#", ele)
                            file_list = os.listdir(os.path.dirname(dataInputPath))
                            re_filename = os.path.basename(dataInputPath).replace('#.*#', '.*')
                            getfilename = [i for i in file_list if re.findall(re_filename, i)]
                            if len(getfilename) != 0:
                                dataInputPath = os.path.dirname(dataInputPath) + '/' + getfilename[0]
                            # 多个输入文件
                            if os.path.exists(dataInputPath):
                                logging.info("获取到nc文件：{}".format(dataInputPath))
                                ds = xr.open_dataset(dataInputPath, engine='pynio')
                                # 重置变量名和维的名称
                                if original.get("var") not in ds.keys():
                                    continue
                                if original.get("var"):
                                    ds = ds.rename({original.get("var"): ele})
                                if original.get("lat"):
                                    ds = ds.rename({original.get("lat"): "lat"})
                                if original.get("lon"):
                                    ds = ds.rename({original.get("lon"): "lon"})
                                data = ds[ele]
                                dataInputPath_dict[ele] = data
                            else:
                                logging.info("源文件不存在")
                                error_str = "源文件【%s】不存在!" % (dataInputPath)
                                if startTime == endTime:  # 同一时间点直接抛异常
                                    raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE,
                                                             response_msg=error_str)
                                else:
                                    logging.info(error_str)
                        if len(dataInputPath_dict) == 3:
                            T = dataInputPath_dict.get("TMP")
                            P = dataInputPath_dict.get("PRS")
                            Q = dataInputPath_dict.get("SHU")
                            data = self.CalculateRH(T, P, Q)
                            data.expand_dims(dim="time", axis=0)
                            data["time"] = hour
                            result_data_get.append(data)
                        else:
                            logging.info("要素不全，无法计算相对湿度")

                    if len(result_data_get) != 0:
                        data_a = xr.concat(result_data_get, dim="time")
                        # 补全数据
                        if "result_data" in locals():
                            result_data = self.makeup_data_by_time(data_a, list(range(1, 25)), result_data)
                        else:
                            result_data = self.makeup_data_by_time(data_a, list(range(1, 25)))
                    # 判断结果数据是否存在，若存在就存储文件
                    if "result_data" in locals():
                        self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                        del result_data
                        file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    def regular_reduce_dim(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_reduce_dim")
        # 计算开始年 开始月 开始日
        startYear, startMon, startDay = int(str(startTime)[0:4]), int(str(startTime)[4:6]), int(str(startTime)[6:8])
        # 计算结束年 结束月 结束日
        endYear, endMon, endDay = int(str(endTime)[0:4]), int(str(endTime)[4:6]), int(str(endTime)[6:8])
        file_num = 0
        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            # logging.info(tmpStartMon,tmpEndMon)
            for mon in range(tmpStartMon, tmpEndMon + 1):  # 循环月份
                result_data_get = []
                monDays = calendar.monthrange(year, mon)[1]
                ym = str(year) + "_" + "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym)
                logging.info(dataOutputPath)
                # 若输出文件存在，则获取数据
                if os.path.exists(dataOutputPath):
                    ds_r = xr.open_dataset(dataOutputPath)
                    # logging.info(ds_r)
                    result_data = ds_r[dataConfig.get("var")]
                # 计算当月的起止日
                tmpStartDay = np.where(year == startYear and mon == startMon, startDay, 1)
                tmpEndDay = np.where(year == endYear and mon == endMon, endDay, monDays)
                for day in range(tmpStartDay, tmpEndDay + 1):  # 循环日
                    ymd = str(year) + "{0:02d}".format(mon) + "{0:02d}".format(day)
                    nex_mon = (datetime.datetime.strptime(ymd, "%Y%m%d").replace(day=28) + datetime.timedelta(days=4)).strftime("%Y%m")
                    dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace("#YYYYMMDD#", ymd).replace("#NEXT_MON#", nex_mon)

                    if os.path.exists(dataInputPath):
                        logging.info(dataInputPath)
                        ds = xr.open_dataset(dataInputPath, engine='netcdf4')
                        # logging.info(ds)
                        # 重置变量名和维的名称
                        # logging.info(dataConfig.get("original").get("var")+"%%%%%"+dataInputPath)
                        if dataConfig.get("original").get("var") not in ds.keys():
                            continue
                        if dataConfig.get("original").get("var"):
                            ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                        if dataConfig.get("original").get("level"):
                            ds = ds.rename({dataConfig.get("original").get("level"): "level"})
                        if dataConfig.get("original").get("lat"):
                            ds = ds.rename({dataConfig.get("original").get("lat"): "lat"})
                        if dataConfig.get("original").get("lon"):
                            ds = ds.rename({dataConfig.get("original").get("lon"): "lon"})
                        data = ds[dataConfig.get("var")]
                        if dataConfig.get("original").get("levels"):
                            logging.info("只需要保留指定的高度层...")
                            data = data.sel(level=dataConfig.get("original").get("levels"))
                        # 单位转换
                        logging.info("原始数据的大小范围在%s~%s..." % (data.min().values, data.max().values))
                        if dataConfig.get("unitConvert"):
                            data.attrs['units'] = dataConfig.get("unitConvert").get("unitName")
                            convert_type, convert_value = dataConfig.get("unitConvert").get("unitProc").split("_")
                            logging.info("%s开始单位转换...转换公式为%s" % (
                                dataConfig.get("var"), [convert_type, convert_value]))
                            data_allx = convert_data(data, convert_type, convert_value)
                            data_allx.attrs = data.attrs
                            data = data_allx
                            logging.info("转换后的数据大小范围在%s~%s..." % (data.min().values, data.max().values))
                            logging.info(data.max().values)
                            if "valid_range" in data.attrs.keys():
                                data.attrs.pop('valid_range')
                            if "actual_range" in data.attrs.keys():
                                data.attrs.pop('actual_range')
                        # if dataConfig.get("var") in ["u100m","v100m"]:
                        # data = data.sel(lv_HTGL1=100)
                        # logging.info(data)
                        # ds = {key.lower():value for key, value in ds.items()}
                        data = data.reduce(np.mean, dim=dataConfig.get("dim"))
                        data.expand_dims(dim="time", axis=0)
                        data["time"] = day
                        result_data_get.append(data)
                    else:
                        error_str = "源文件【%s】不存在!" % (dataInputPath)
                        if startTime == endTime:  # 同一时间点直接抛异常
                            raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                        else:
                            logging.error(error_str)

                if len(result_data_get) != 0:
                    data_a = xr.concat(result_data_get, dim="time")
                    # 补全数据
                    if "result_data" in locals():
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)), result_data)
                    else:
                        result_data = self.makeup_data_by_time(data_a, list(range(1, monDays + 1)))
                # 判断结果数据是否存在，若存在就存储文件
                if "result_data" in locals():
                    self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                    del result_data
                    file_num = file_num + 1
        result_dict["file_num"] = str(file_num)
        return result_dict

    def regular_bcccpsv3_mon_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_bcccpsv3_mon_data")
        # 获取起报时间数据
        reporting_time_list = DateUtils.get_time_list([startTime, endTime], "mon")
        file_num = 0
        for reportingTime in reporting_time_list:
            y_m = reportingTime[0:4]+"_"+reportingTime[4:]
            dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", y_m)
            dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", reportingTime[0:4]).replace("#YYYYMM#", reportingTime)
            if os.path.exists(dataInputPath):
                ds = xr.open_dataset(dataInputPath)
                # 重置变量名和维的名称
                if dataConfig.get("original"):
                    if dataConfig.get("original").get("var"):
                        org_var_list = dataConfig.get("original").get("var").split(",")
                        for org_var in org_var_list:
                            if org_var in ds.data_vars:
                                ds = ds.rename({org_var: dataConfig.get("var")})
                    if dataConfig.get("original").get("lat") and dataConfig.get("original").get("lat") in ds.dims:
                        ds = ds.rename({dataConfig.get("original").get("lat"): "lat"})
                    if dataConfig.get("original").get("lon") and dataConfig.get("original").get("lon") in ds.dims:
                        ds = ds.rename({dataConfig.get("original").get("lon"): "lon"})
                result_data = ds[dataConfig.get("var")]
                if dataConfig.get("level"):
                    result_data = result_data.sel(level=float(dataConfig.get("level")))
                logging.info("原始数据的大小范围在%s~%s..." % (result_data.min().values, result_data.max().values))
                if dataConfig.get("unitConvert"):
                    result_data.attrs['unit'] = dataConfig.get("unitConvert").get("unitName")
                    unitConverts = dataConfig.get("unitConvert").get("unitProc").split("-")
                    convert_type, convert_value = unitConverts[0].split("_")
                    logging.info("%s开始单位转换...转换公式为%s" % (dataConfig.get("var"), unitConverts))
                    data_allx = convert_data(result_data, convert_type, convert_value)
                    if len(unitConverts) == 2:
                        if unitConverts[1] == "mon":
                            fore_time_list = data_allx.time.values
                            for k,foreTime in enumerate(fore_time_list):
                                logging.info(foreTime)
                                year,mon = int(str(foreTime)[0:4]),int(str(foreTime)[5:7])
                                mon_days = calendar.monthrange(year, mon)[1]
                                logging.info(mon_days)
                                data_allx[k] = data_allx[k]*mon_days
                    data_allx.attrs = result_data.attrs
                    result_data = data_allx
                    logging.info("转换后的数据大小范围在%s~%s..." % (result_data.min().values, result_data.max().values))
                # print(result_data)
                self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath,"float32")
                file_num = file_num +1
            else:
                error_str = "源文件【%s】不存在!" % (dataInputPath)
                if startTime == endTime:  # 同一时间点直接抛异常
                    raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                else:
                    logging.error(error_str)
        result_dict["file_num"] = str(file_num)
        return result_dict

    def regular_bcccpsv3_day_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_bcccpsv3_day_data")
        # 获取起报时间数据
        reporting_time_list = DateUtils.get_time_list([startTime, endTime], "day")
        file_num = 0
        member_list = ["01", "02", "03", "04"]
        fn_list = ["", "p01", "p02", "p03"]
        for reportingTime in reporting_time_list:
            y_m = reportingTime[0:4] + "_" + reportingTime[4:]
            dataOutputPath_ymd = dataConfig.get("dataOutputPath").replace("#YYYY#", reportingTime[0:4]).replace("#MM#",reportingTime[4:6]).replace("#YYYYMMDD#", reportingTime)
            dataInputPath_ymd = dataConfig.get("dataInputPath").replace("#YYYY#", reportingTime[0:4]).replace("#YYYYMMDD#", reportingTime)
            m_data_list = []
            for n, member in enumerate(member_list):
                dataOutputPath_member = dataOutputPath_ymd.replace("#MN#", member)
                dataInputPath_member = dataInputPath_ymd.replace("#MN#", fn_list[n])
                if os.path.exists(dataInputPath_member):
                    ds = xr.open_dataset(dataInputPath_member)
                    # 重置变量名和维的名称
                    if dataConfig.get("original"):
                        if dataConfig.get("original").get("var"):
                            org_var_list = dataConfig.get("original").get("var").split(",")
                            for org_var in org_var_list:
                                if org_var in ds.data_vars:
                                    ds = ds.rename({org_var: dataConfig.get("var")})
                        if dataConfig.get("original").get("lat") and dataConfig.get("original").get("lat") in ds.dims:
                            ds = ds.rename({dataConfig.get("original").get("lat"): "lat"})
                        if dataConfig.get("original").get("lon") and dataConfig.get("original").get("lon") in ds.dims:
                            ds = ds.rename({dataConfig.get("original").get("lon"): "lon"})
                    result_data = ds[dataConfig.get("var")]
                    if dataConfig.get("level"):
                        result_data = result_data.sel(level=float(dataConfig.get("level")))
                    logging.info("原始数据的大小范围在%s~%s..." % (result_data.min().values, result_data.max().values))
                    if dataConfig.get("unitConvert"):
                        result_data.attrs['unit'] = dataConfig.get("unitConvert").get("unitName")
                        unitConverts = dataConfig.get("unitConvert").get("unitProc").split("-")
                        convert_type, convert_value = unitConverts[0].split("_")
                        logging.info("%s开始单位转换...转换公式为%s" % (dataConfig.get("var"), unitConverts))
                        data_allx = convert_data(result_data, convert_type, convert_value)
                        if len(unitConverts) == 2:
                            if unitConverts[1] == "mon":
                                fore_time_list = data_allx.time.values
                                for k, foreTime in enumerate(fore_time_list):
                                    logging.info(foreTime)
                                    year, mon = int(str(foreTime)[0:4]), int(str(foreTime)[5:7])
                                    mon_days = calendar.monthrange(year, mon)[1]
                                    logging.info(mon_days)
                                    data_allx[k] = data_allx[k] * mon_days
                        data_allx.attrs = result_data.attrs
                        result_data = data_allx
                        logging.info("转换后的数据大小范围在%s~%s..." % (result_data.min().values, result_data.max().values))
                    # print(result_data)
                    self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath_member, "float32")
                    file_num = file_num + 1
                    result_data_m = result_data.expand_dims("m")
                    result_data_m["m"] = [member]
                    m_data_list.append(result_data_m)
                else:
                    error_str = "源文件【%s】不存在!" % (dataInputPath_member)
                    if startTime == endTime:  # 同一时间点直接抛异常
                        raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                    else:
                        logging.error(error_str)
            if len(m_data_list) == 4:
                m_data = xr.concat(m_data_list, dim="m")
                m_data = m_data.mean(dim=["m"])
                dataOutputPath_mn = dataOutputPath_ymd.replace("#MN#", "mn")
                self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath_mn, "float32")
        result_dict["file_num"] = str(file_num)
        return result_dict

    def regular_modes_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_modes_data")
        # 计算开始年 开始月
        startYear, startMon = int(str(startTime)[0:4]), int(str(startTime)[4:6])
        # 计算结束年 结束月
        endYear, endMon = int(str(endTime)[0:4]), int(str(endTime)[4:6])
        file_num = 0

        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):
                result_data_get = []
                ym = str(year) + "{0:02d}".format(mon)
                # logging.info(ym)
                dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace("#YYYYMM#", ym)
                ym_out = str(year) + "_" +  "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym_out)
                # logging.info(dataOutputPath)
                # 若输出文件存在，则删除数据
                if os.path.exists(dataOutputPath):
                    os.remove(dataOutputPath)
                logging.info(dataInputPath)
                if os.path.exists(dataInputPath):
                    ds = xr.open_dataset(dataInputPath)
                    if dataConfig.get("original"):
                        if dataConfig.get("original").get("var"):
                            ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                    data = ds[dataConfig.get("var")]
                    # # 剪裁为浙江范围数据
                    # lon = ds['lon']
                    # lat = ds['lat']
                    # lat_range = lat[(lat >= 27) & (lat <= 32)]
                    # lon_range = lon[(lon >= 115) & (lon <= 123)]
                    # data = data.sel(lon=lon_range, lat=lat_range)
                    # 单位转换
                    logging.info("原始数据的大小范围在%s~%s..." % (data.min().values, data.max().values))
                    if dataConfig.get("unitConvert"):
                        data.attrs['units'] = dataConfig.get("unitConvert").get("unitName")
                        unitConverts = dataConfig.get("unitConvert").get("unitProc").split("-")
                        convert_type, convert_value = unitConverts[0].split("_")
                        logging.info("%s开始单位转换...转换公式为%s" % (dataConfig.get("var"), unitConverts))
                        data_allx = convert_data(data, convert_type, convert_value)
                        if len(unitConverts) == 2:
                            if unitConverts[1] == "mon":
                                mon_days = calendar.monthrange(year, mon)[1]
                                data_allx *= mon_days
                        data_allx.attrs = data.attrs
                        data = data_allx
                        logging.info("转换后的数据大小范围在%s~%s..." % (data.min().values, data.max().values))
                        if "valid_range" in data.attrs.keys():
                            data.attrs.pop('valid_range')
                        if "actual_range" in data.attrs.keys():
                            data.attrs.pop('actual_range')
                    result_data_get.append(data)
                    # 判断结果数据是否存在，若存在就存储文件
                    if "result_data_get" in locals():
                        self.writ_nc(data, dataConfig.get("var"), dataOutputPath)
                        del result_data_get
                        file_num = file_num + 1
                else:
                    error_str = "源文件【%s】不存在!" % (dataInputPath)
                    if startTime == endTime:  # 同一时间点直接抛异常
                        raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                    else:
                        logging.error(error_str)

        result_dict["file_num"] = str(file_num)
        return result_dict
    def regular_modes_ltm_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_modes_ltm_data")
        # 计算开始年 开始月
        startYear, startMon = int(str(startTime)[0:4]), int(str(startTime)[4:6])
        # 计算结束年 结束月
        endYear, endMon = int(str(endTime)[0:4]), int(str(endTime)[4:6])
        file_num = 0

        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):
                result_data_get = []
                mm = "{0:02d}".format(mon)
                # logging.info(ym)
                dataInputPath = dataConfig.get("dataInputPath").replace("#MM#", mm)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#MM#", mm)
                # logging.info(dataOutputPath)
                # 若输出文件存在，则删除数据
                if os.path.exists(dataOutputPath):
                    os.remove(dataOutputPath)
                logging.info(dataInputPath)
                if os.path.exists(dataInputPath):
                    ds = xr.open_dataset(dataInputPath)
                    if dataConfig.get("original"):
                        if dataConfig.get("original").get("var"):
                            ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                    data = ds[dataConfig.get("var")]
                    # 单位转换
                    logging.info("原始数据的大小范围在%s~%s..." % (data.min().values, data.max().values))
                    if dataConfig.get("unitConvert"):
                        data.attrs['units'] = dataConfig.get("unitConvert").get("unitName")
                        unitConverts = dataConfig.get("unitConvert").get("unitProc").split("-")
                        convert_type, convert_value = unitConverts[0].split("_")
                        logging.info("%s开始单位转换...转换公式为%s" % (dataConfig.get("var"), unitConverts))
                        data_allx = convert_data(data, convert_type, convert_value)
                        if len(unitConverts) == 2:
                            if unitConverts[1] == "mon":
                                mon_days = calendar.monthrange(year, mon)[1]
                                data_allx *= mon_days
                        data_allx.attrs = data.attrs
                        data = data_allx
                        logging.info("转换后的数据大小范围在%s~%s..." % (data.min().values, data.max().values))
                        if "valid_range" in data.attrs.keys():
                            data.attrs.pop('valid_range')
                        if "actual_range" in data.attrs.keys():
                            data.attrs.pop('actual_range')
                    result_data_get.append(data)
                    # 判断结果数据是否存在，若存在就存储文件
                    if "result_data_get" in locals():
                        self.writ_nc(data, dataConfig.get("var"), dataOutputPath)
                        del result_data_get
                        file_num = file_num + 1
                else:
                    error_str = "源文件【%s】不存在!" % (dataInputPath)
                    if startTime == endTime:  # 同一时间点直接抛异常
                        raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                    else:
                        logging.error(error_str)
        result_dict["file_num"] = str(file_num)
        return result_dict

    def regular_modes_mme_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_modes_mme_data")
        # 计算开始年 开始月
        startYear, startMon = int(str(startTime)[0:4]), int(str(startTime)[4:6])
        # 计算结束年 结束月
        endYear, endMon = int(str(endTime)[0:4]), int(str(endTime)[4:6])
        file_num = 0

        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):
                result_data_get = []
                ym = str(year) + "{0:02d}".format(mon)
                # logging.info(ym)
                dataInputPath = dataConfig.get("dataInputPath").replace("#YYYY#", str(year)).replace("#YYYYMM#", ym)
                ym_out = str(year) + "_" +  "{0:02d}".format(mon)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#YYYY_MM#", ym_out)
                # logging.info(dataOutputPath)
                # 若输出文件存在，则删除数据
                if os.path.exists(dataOutputPath):
                    os.remove(dataOutputPath)
                logging.info(dataInputPath)
                if os.path.exists(dataInputPath):
                    # 遍历文件路径，选取ukmo_glosea5、jma_cps3、ncep_cfs、ncc_csm11数据，有几个算几个
                    modes_filenames = os.listdir(dataInputPath)
                    for mode_filename in modes_filenames:
                        if mode_filename.endswith('.nc') and ("ukmo_glosea5" in mode_filename or "jma_cps3" in mode_filename or "ncep_cfs2" in mode_filename or "ncc_csm11" in mode_filename):
                            logging.info("sMODES集合平均单模式文件有：%s" % mode_filename)
                            ds = xr.open_dataset(dataInputPath + mode_filename)
                            if dataConfig.get("original"):
                                if dataConfig.get("original").get("var"):
                                    ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                            # 截取modes多个模式同时能预报的时间
                            if "ukmo_glosea5" in mode_filename or "jma_cps3" in mode_filename:
                                data = (ds[dataConfig.get("var")])[0:5]
                            else:
                                data = (ds[dataConfig.get("var")])[1:6]
                            # 单位转换
                            logging.info("原始数据的大小范围在%s~%s..." % (data.min().values, data.max().values))
                            if dataConfig.get("unitConvert"):
                                data.attrs['units'] = dataConfig.get("unitConvert").get("unitName")
                                unitConverts = dataConfig.get("unitConvert").get("unitProc").split("-")
                                convert_type, convert_value = unitConverts[0].split("_")
                                logging.info("%s开始单位转换...转换公式为%s" % (dataConfig.get("var"), unitConverts))
                                data_allx = convert_data(data, convert_type, convert_value)
                                if len(unitConverts) == 2:
                                    if unitConverts[1] == "mon":
                                        mon_days = calendar.monthrange(year, mon)[1]
                                        data_allx *= mon_days
                                data_allx.attrs = data.attrs
                                data = data_allx
                                logging.info("转换后的数据大小范围在%s~%s..." % (data.min().values, data.max().values))
                                if "valid_range" in data.attrs.keys():
                                    data.attrs.pop('valid_range')
                                if "actual_range" in data.attrs.keys():
                                    data.attrs.pop('actual_range')
                            result_data_get.append(data)
                    # 求模式平均
                    if len(result_data_get) != 0:
                        # （time,lat,lon)
                        modes_data_shape = result_data_get[0].shape
                        #  modes_mme不同维度信息
                        modes_mme_time = result_data_get[0]['time']
                        modes_mme_lat = result_data_get[0]['lat']
                        modes_mme_lon = result_data_get[0]['lon']
                        result_data_tmp = np.full((len(result_data_get), modes_data_shape[0], modes_data_shape[1], modes_data_shape[2]), np.nan)
                        for result_data_get_index, result_data_get_tmp in enumerate(result_data_get):
                            result_data_tmp[result_data_get_index] = result_data_get_tmp.values
                        result_data = np.nanmean(result_data_tmp,0)
                        result_data = xr.DataArray(result_data, coords=[modes_mme_time, modes_mme_lat, modes_mme_lon], dims=["time", "lat", "lon"])
                        result_data.attrs = result_data_get[0].attrs
                    # 判断结果数据是否存在，若存在就存储文件
                    if "result_data_get" in locals():
                        self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                        del result_data_get
                        file_num = file_num + 1
                else:
                    error_str = "源文件【%s】不存在!" % (dataInputPath)
                    if startTime == endTime:  # 同一时间点直接抛异常
                        raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                    else:
                        logging.error(error_str)

        result_dict["file_num"] = str(file_num)
        return result_dict

    def regular_modes_mme_ltm_data(self, dataConfig, startTime, endTime):
        result_dict = build_response_dict()
        logging.info("regular_modes_mme_ltm_data")
        # 计算开始年 开始月
        startYear, startMon = int(str(startTime)[0:4]), int(str(startTime)[4:6])
        # 计算结束年 结束月
        endYear, endMon = int(str(endTime)[0:4]), int(str(endTime)[4:6])
        file_num = 0

        for year in range(startYear, endYear + 1):  # 循环年份
            # 计算当前年的起止月份
            tmpStartMon = np.where(year == startYear, startMon, 1)
            tmpEndMon = np.where(year == endYear, endMon, 12)
            for mon in range(tmpStartMon, tmpEndMon + 1):
                result_data_get = []
                mm = "{0:02d}".format(mon)
                # logging.info(ym)
                dataInputPath = dataConfig.get("dataInputPath").replace("#MM#", mm)
                dataOutputPath = dataConfig.get("dataOutputPath").replace("#MM#", mm)
                # logging.info(dataOutputPath)
                # 若输出文件存在，则删除数据
                if os.path.exists(dataOutputPath):
                    os.remove(dataOutputPath)
                logging.info(dataInputPath)
                if os.path.exists(dataInputPath):
                    # 遍历文件路径，选取ukmo_glosea5、jma_cps3、ncep_cfs、ncc_csm11数据，有几个算几个
                    modes_filenames = os.listdir(dataInputPath)
                    for mode_filename in modes_filenames:
                        if mode_filename.endswith('.nc') and ("ukmo_glosea5" in mode_filename or "jma_cps3" in mode_filename or "ncep_cfs2" in mode_filename or "ncc_csm11" in mode_filename):
                            logging.info("sMODES集合平均单模式文件有：%s" % mode_filename)
                            ds = xr.open_dataset(dataInputPath + mode_filename)
                            if dataConfig.get("original"):
                                if dataConfig.get("original").get("var"):
                                    ds = ds.rename({dataConfig.get("original").get("var"): dataConfig.get("var")})
                            # 截取modes多个模式同时能预报的时间
                            if "ukmo_glosea5" in mode_filename or "jma_cps3" in mode_filename:
                                data = (ds[dataConfig.get("var")])[0:5]
                            else:
                                data = (ds[dataConfig.get("var")])[1:6]
                            # 单位转换
                            logging.info("原始数据的大小范围在%s~%s..." % (data.min().values, data.max().values))
                            if dataConfig.get("unitConvert"):
                                data.attrs['units'] = dataConfig.get("unitConvert").get("unitName")
                                unitConverts = dataConfig.get("unitConvert").get("unitProc").split("-")
                                convert_type, convert_value = unitConverts[0].split("_")
                                logging.info("%s开始单位转换...转换公式为%s" % (dataConfig.get("var"), unitConverts))
                                data_allx = convert_data(data, convert_type, convert_value)
                                if len(unitConverts) == 2:
                                    if unitConverts[1] == "mon":
                                        mon_days = calendar.monthrange(year, mon)[1]
                                        data_allx *= mon_days
                                data_allx.attrs = data.attrs
                                data = data_allx
                                logging.info("转换后的数据大小范围在%s~%s..." % (data.min().values, data.max().values))
                                if "valid_range" in data.attrs.keys():
                                    data.attrs.pop('valid_range')
                                if "actual_range" in data.attrs.keys():
                                    data.attrs.pop('actual_range')
                            result_data_get.append(data)
                    # 求模式平均
                    if len(result_data_get) != 0:
                        # （time,lat,lon)
                        modes_data_shape = result_data_get[0].shape
                        #  modes_mme不同维度信息
                        modes_mme_time = result_data_get[0]['time']
                        modes_mme_lat = result_data_get[0]['lat']
                        modes_mme_lon = result_data_get[0]['lon']
                        result_data_tmp = np.full((len(result_data_get), modes_data_shape[0], modes_data_shape[1], modes_data_shape[2]), np.nan)
                        for result_data_get_index, result_data_get_tmp in enumerate(result_data_get):
                            result_data_tmp[result_data_get_index] = result_data_get_tmp.values
                        result_data = np.nanmean(result_data_tmp,0)
                        result_data = xr.DataArray(result_data, coords=[modes_mme_time, modes_mme_lat, modes_mme_lon], dims=["time", "lat", "lon"])
                        result_data.attrs = result_data_get[0].attrs
                    # 判断结果数据是否存在，若存在就存储文件
                    if "result_data_get" in locals():
                        self.writ_nc(result_data, dataConfig.get("var"), dataOutputPath)
                        del result_data_get
                        file_num = file_num + 1
                else:
                    error_str = "源文件【%s】不存在!" % (dataInputPath)
                    if startTime == endTime:  # 同一时间点直接抛异常
                        raise AlgorithmException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg=error_str)
                    else:
                        logging.error(error_str)

        result_dict["file_num"] = str(file_num)
        return result_dict