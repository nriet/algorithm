#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2019/10/21
# @Author : xulh
# @File : fileUtils.py

import xarray as xr
import numpy as np
from com.nriet.utils import DateUtils


def data_convert(inputData, timeType, convertTimeType, startTime, endTime,statType):
    # 日尺度转换到中国候
    if timeType == "day" and convertTimeType == "five":
        convert_data = day2Five(inputData, timeType, convertTimeType, startTime, endTime,statType)
    # 月尺度转换到季
    if timeType == "mon" and convertTimeType == "season":
        convert_data = month2Season(inputData, timeType, convertTimeType, startTime, endTime,statType)

    return convert_data


def day2Five(inputData, timeType, convertTimeType, startTime, endTime,statType):
    want_five_list = DateUtils.get_time_list([startTime, endTime], convertTimeType)
    data_five_list = []
    for i, ff in enumerate(want_five_list):
        cday_list = DateUtils.otherTime2Day(ff, convertTimeType)
        tmp_start_day, tmp_end_day = cday_list[0], cday_list[1]
        tmp_day_list = DateUtils.get_time_list([tmp_start_day, tmp_end_day], timeType)
        data_5d = inputData.sel(time=tmp_day_list)
        if statType == "avg":
            single_data = data_5d.mean(dim="time", skipna=True, keep_attrs=True)
        if statType == "sum":
            # 降维求和修改 胡玉恒 20210413
            tmpdata = data_5d.mean(dim="time", skipna=True, keep_attrs=True)
            tmpdata = tmpdata.where(np.isnan(tmpdata), 1)
            single_data = data_5d.sum(dim="time", skipna=True, keep_attrs=True)
            single_data = single_data * tmpdata
        single_data = single_data.expand_dims('time')
        single_data['time'] = [ff]
        data_five_list.append(single_data)
    convert_five_data = xr.concat(data_five_list, dim="time")
    return convert_five_data


def month2Season(inputData, timeType, convertTimeType, startTime, endTime,statType):
    want_season_list = DateUtils.get_time_list([startTime, endTime], convertTimeType)
    data_season_list = []
    for i, ff in enumerate(want_season_list):
        cmon_list = DateUtils.otherTime2Month(ff, convertTimeType)
        tmp_start_mon, tmp_end_mon = cmon_list[0], cmon_list[1]
        tmp_mon_list = DateUtils.get_time_list([tmp_start_mon, tmp_end_mon], timeType)
        data_m = inputData.sel(time=tmp_mon_list)
        if statType == "avg":
            single_data = data_m.mean(dim="time", skipna=True, keep_attrs=True)
        if statType == "sum":
            # 降维求和修改 胡玉恒 20210413
            tmpdata = data_m.mean(dim="time", skipna=True, keep_attrs=True)
            tmpdata = tmpdata.where(np.isnan(tmpdata), 1)
            single_data = data_m.sum(dim="time", skipna=True, keep_attrs=True)
            single_data = single_data * tmpdata
        single_data = single_data.expand_dims('time')
        single_data['time'] = [ff]
        data_season_list.append(single_data)
    convert_season_data = xr.concat(data_season_list, dim="time")
    return convert_season_data
