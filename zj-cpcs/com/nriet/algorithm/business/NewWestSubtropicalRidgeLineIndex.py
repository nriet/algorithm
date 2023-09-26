#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time: 2020/3/25 下午7:18
# @Author: Shiys
# @File: NewWestSubtropicalRidgeLineIndex.py
# @update: 增加预报多样本处理 20201102
import xarray as xr
import numpy as np
import logging
from com.nriet.algorithm.business.BusComponent import BusComponent

class NewWestSubtropicalRidgeLineIndex(BusComponent):

    def __init__(self, sub_local_params, algorithm_iuput_data):
        self.flow_data = algorithm_iuput_data

        if isinstance(self.flow_data[0]["outputData"], list):
            self.inputData = self.flow_data[0]["outputData"][0]
        else:
            self.inputData = self.flow_data[0]["outputData"]

        if isinstance(self.flow_data[1]["outputData"], list):
            self.inputData2 = self.flow_data[1]["outputData"][0]
        else:
            self.inputData2 = self.flow_data[1]["outputData"]

        self.output_data = None

    def execute(self):
        # 计算脊线指数
        if len(self.inputData.shape)== 3:
            ridgeLineIndex = self.cal_ridge_line_index(self.inputData,self.inputData2)
        else:
            tmp = np.full(self.inputData.shape[:2],np.nan)
            for e,ens in enumerate(self.inputData.ens):
                tmp[e,:] = self.cal_ridge_line_index(self.inputData[e,...],self.inputData2[e,...])
            ridgeLineIndex = xr.DataArray(tmp,coords=[self.inputData.ens,self.inputData.time],dims=["ens","time"]).T
        output_data = {
            "outputData": ridgeLineIndex
        }
        self.output_data = output_data

    # @timer_with_param("cal_ridge_line_index")
    def cal_ridge_line_index(self, hgtData, uwndData):
        """
        脊线位置计算方法：逐根经线计算5880的脊线位置，如果找不到就用5840的脊线位置，最后求个平均
        :param hgtData:位势高度，数据要比实际计算的范围大一格子圈
        :param uwndData:纬向风，数据要比实际计算的范围大一格子圈
        :return:脊线位置
        """
        # 获取经度、纬度以及时间数组
        lon_list = hgtData.lon.values
        nx = len(lon_list)
        lat_list = hgtData.lat.values
        ny = len(lat_list)
        time_list = hgtData.time.values
        # logging.info(lat)
        # 判断纬度为降序时，需要转换为升序，同时处理输入数据
        if lat_list[0] > lat_list[-1]:
            lat_list = lat_list[::-1]
            hgtData = hgtData.sel(lat=lat_list)
            uwndData = uwndData.sel(lat=lat_list)
        # logging.info(lat_list)
        # logging.info(lon_list)
        # logging.info(time_list)
        # 计算脊线指数
        gx = []

        for time_index, time in enumerate(time_list):  # 循环时间维
            indtemp = np.full(nx, np.nan)
            hgt_tmp = hgtData.sel(time=time).values
            uwnd_tmp = uwndData.sel(time=time).values
            mark_5880 = np.full([ny, nx], 0)
            # logging.info(hgt_tmp)
            # 圈5880副高的范围
            for i in range(1, nx - 1):  # 循环经度维
                for j in range(1, ny - 1):  # 循环纬度维
                    if hgt_tmp[j, i] >= 5880.0:
                        hh = hgt_tmp[j - 1:j + 2, i - 1:i + 2]
                        if len(np.where(hh >= 5880.0)[0]) >= 3:
                            mark_5880[j, i] = 1
            mark_5840 = np.full([ny, nx], 0)
            # 圈5840副高的范围
            for i in range(1, nx - 1):  # 循环经度维
                for j in range(1, ny - 1):  # 循环纬度维
                    if hgt_tmp[j, i] >= 5840.0:
                        hh = hgt_tmp[j - 1:j + 2, i - 1:i + 2]
                        if len(np.where(hh >= 5840.0)[0]) >= 3:
                            mark_5840[j, i] = 1
            # logging.info(len(np.where(mark == 1)[0]))
            # logs = 0
            for i in range(1, nx - 1):  # 循环经度维
                jp = 0
                for j in range(1, ny - 1):  # 循环纬度维
                    if mark_5880[j, i] == 1:
                        # logging.info("5880点的坐标", lon_list[i], lat_list[j], i, j)
                        if uwnd_tmp[j, i] <= 0 and uwnd_tmp[j + 1, i] > 0 and uwnd_tmp[j, i] <= uwnd_tmp[j + 1, i]:
                            jp = j
                if jp != 0:
                    # logs = logs + 1
                    indtemp[i] = lat_list[jp] + (lat_list[jp + 1] - lat_list[jp]) * abs( uwnd_tmp[jp, i]) / (abs(uwnd_tmp[jp, i]) + abs(uwnd_tmp[jp + 1, i]))
                else:
                    # del j
                    for j in range(1, ny - 1):  # 循环纬度维
                        if mark_5840[j, i] == 1:
                            if uwnd_tmp[j, i] < 0 and uwnd_tmp[j, i] <= uwnd_tmp[j + 1, i]:
                                jp = j
                    if jp != 0:
                        # logs = logs + 1
                        indtemp[i] = lat_list[jp] + (lat_list[jp + 1] - lat_list[jp]) * abs(uwnd_tmp[jp, i]) / (
                                    abs(uwnd_tmp[jp, i]) + abs(uwnd_tmp[jp + 1, i]))
            # print()
            # 计算纬度的平均值
            gx.append(np.nanmean(indtemp))
            # print(xr.DataArray(indtemp,dims=["lon"],coords=[hgt_tmp.lon]),"\n",np.nanmean(indtemp))
        gx_data = xr.DataArray(gx, dims=["time"], coords=[time_list])
        # print(gx_data)
        # logging.info(gx_data)
        return gx_data

# if __name__ == "__main__":
#     from com.nriet.utils.GridDataUtils import GridDataUtils
#     hgtPath = "/nfsshare/cdbdata/data/NCEPRA/pressure/hgt/day/"
#     uwndPath = "/nfsshare/cdbdata/data/NCEPRA/pressure/uwnd/day/"
#     tmp = GridDataUtils()
#     regions = "107.5,132.5,7.5,52.5"
#     timeRanges = ["20210701","20210806"]
#     hgt = tmp.get_day_mean_data(hgtPath, "day", timeRanges[0], timeRanges[1], "hgt", regions, "500").mean(axis=1)
#     uwnd = tmp.get_day_mean_data(uwndPath, "day", timeRanges[0], timeRanges[1], "uwnd", regions, "500").mean(axis=1)
#     a = NewWestSubtropicalRidgeLineIndex(hgt,uwnd)
#     a.cal_ridge_line_index(hgt,uwnd)
