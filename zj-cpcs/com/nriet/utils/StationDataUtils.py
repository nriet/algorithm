#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/03/09
# @Author : shiys
# @File : StationDataUtils.py


import os
import xarray as xr
import numpy as np
from com.nriet.utils import DateUtils


class StationDataUtils:
    """ 获取站点数据工具类
    根据传入的站点文件的路径、时间尺度、时间访问、要素、站号等实时获取出相关的站点数据
    """

    # 根据时间维补全数据
    def makeup_data_by_time(acquired_data, startTime, endTime, timeType):
        request_time_list = DateUtils.get_time_list([startTime, endTime], timeType)
        acquired_time_list = acquired_data.time.values
        time_diff_list = list(set(request_time_list).difference(set(acquired_time_list)))
        if len(time_diff_list) != 0:
            # print("xxxxxxxxxxxxxxx")
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
                for ii, s_time in enumerate(sort_time_tmp):
                    if s_time[4:6] == '04':
                        sort_time.append(s_time[0:4] + "00")
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
        return tmp_result_data

    def get_station_mean_data(dataInPutPath, timeType, startTime, endTime, var, station_range, level):
        """获取站点实况数据
        根据输入的条件筛选指定的站点数据
        Args:
            :param dataInPutPath: 站点实况数据文件的存储位置
            :param timeType: 时间尺度
            :param startTime: 开始时间
            :param endTime: 结束时间
            :param var: 要素
            :param station_range: 站号
            :param level: 高度层
        Returns:
            返回一个xarray的DataArray类型的数组
        """
        res_data = []
        startYear = int(startTime[0:4])
        endYear = int(endTime[0:4])
        for year in range(startYear, endYear + 1):
            dataFile_y = dataInPutPath.replace("#YYYY#", str(year))
            if os.path.exists(dataFile_y):
                # 处理一年的开始时间
                tmpStartTime = DateUtils.get_begin_date(str(year), startTime, timeType)
                # 处理一年的结束时间
                tmpEndTime = DateUtils.get_end_date(str(year), endTime, timeType)
                want_times_list = DateUtils.get_time_list([tmpStartTime, tmpEndTime], timeType)
                index_list = DateUtils.get_time_index(want_times_list, timeType)
                # 加载数据
                ds = xr.open_dataset(dataFile_y)
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
                # 筛选时间
                tmpdata = tmpdata.isel(time=index_list)
                # 若站点数据的层次不为空，则需要筛选指定层次
                if (level != ""):
                    pass
                tmpdata["time"] = want_times_list
                if var == "rain":
                    tmpdata = xr.where(tmpdata > 32000., 0.1, tmpdata)
                    # tmpdata.values[tmpdata.values > 32000.] = 0.1
                res_data.append(tmpdata)
        if len(res_data) != 0:
            station_mean_data = xr.concat(res_data, dim="time")
            # 补全数据
            station_mean_data = StationDataUtils.makeup_data_by_time(station_mean_data, startTime, endTime, timeType)
        else:
            station_mean_data = None
        # station_mean_data = xr.concat(res_data, dim='time')
        return station_mean_data

    def get_station_ltm_data(dataInPutPath, timeType, startTime, endTime, var, station_range, level):
        """获取站点常年值数据
        根据输入的条件筛选指定的站点常年值数据
        Args:
            :param dataInPutPath: 站点常年值数据文件的存储位置
            :param timeType: 时间尺度
            :param startTime: 开始时间
            :param endTime: 结束时间
            :param var: 要素
            :param station_range: 站号
            :param level: 高度层
        Returns:
            返回一个xarray的DataArray类型的数组
        """
        res_data = []
        startYear = int(startTime[0:4])
        endYear = int(endTime[0:4])
        for year in range(startYear, endYear + 1):
            # 处理一年的开始时间
            tmpStartTime = DateUtils.get_begin_date(str(year), startTime, timeType)
            # 处理一年的结束时间
            tmpEndTime = DateUtils.get_end_date(str(year), endTime, timeType)
            want_times_list = DateUtils.get_time_list([tmpStartTime, tmpEndTime], timeType)
            index_list = DateUtils.get_time_index(want_times_list, timeType)
            # 加载数据
            ds = xr.open_dataset(dataInPutPath)
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
            # 筛选时间
            tmpdata = tmpdata.isel(time=index_list)
            # 若站点数据的层次不为空，则需要筛选指定层次
            if (level != ""):
                pass
            tmpdata["time"] = want_times_list
            if var == "rain":
                tmpdata = xr.where(tmpdata > 32000., 0.1, tmpdata)
                # tmpdata.values[tmpdata.values > 32000.] = 0.1
            res_data.append(tmpdata)
        station_ltm_data = xr.concat(res_data, dim='time')
        return station_ltm_data