#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time: 2021/08/11
# @Author: hyh
# @File: NorthBoundaryIndex.py
import xarray as xr
import numpy as np

from com.nriet.algorithm.business.BusComponent import BusComponent
from com.nriet.utils.decorator.TimerDecorator import timer_with_param
from datetime import datetime
class NorthBoundaryIndex(BusComponent):

    def __init__(self, sub_local_params, algorithm_iuput_data):
        self.flow_data = algorithm_iuput_data

        if isinstance(self.flow_data[0]["outputData"], list):
            self.inputData = self.flow_data[0]["outputData"][0]
        else:
            self.inputData = self.flow_data[0]["outputData"]

        self.output_data = None

    def execute(self):
        # 计算脊线指数
        resultData = self.cal_north_index(self.inputData)
        output_data = {
            "outputData": resultData
        }
        self.output_data = output_data

    # @timer_with_param("cal_north_index")
    # 计算副高北界指数
    def cal_north_index(self, hgtData):
        # 获取经度、纬度以及时间数组
        lon_list = hgtData.lon.values
        lat_list = hgtData.lat.values
        time_list = hgtData.time.values
        # 判断纬度为降序时，需要转换为升序，同时处理输入数据
        if lat_list[0] > lat_list[-1]:
            lat_list = lat_list[::-1]
            hgtData = hgtData.sel(lat=lat_list)
        if len(hgtData.shape) == 3:
            _, ny, nx = hgtData.shape
            index = np.full(time_list.shape, np.nan)
            for time_index, time in enumerate(time_list):  # 循环时间维
                hgt_tmp = hgtData[time_index].values - 5880

                index_lon = np.full([nx], np.nan)
                for i in range(nx):  # 循环经度维
                    for j in range(ny):  # 循环纬度维
                        if hgt_tmp[j, i] >= 0.0:
                            k = j

                    if "k" in locals():
                        if k == ny-1:
                            index_lon[i] = lat_list[-1]
                        else:
                            index_lon[i] = (abs(hgt_tmp[k, i])*lat_list[k+1]+abs(hgt_tmp[k+1, i])*lat_list[k])/(abs(hgt_tmp[k, i])+abs(hgt_tmp[k+1, i]))

                # index_lon = [[(abs(hgt_tmp[j, i])*lat_list[j+1]+abs(hgt_tmp[j+1, i])*lat_list[j])/(abs(hgt_tmp[j, i])+abs(hgt_tmp[j+1, i])) if hgt_tmp[j, i]*hgt_tmp[j+1,i] <= 0.0 else np.nan for j in range(ny-1)] for i in range(nx)]

                index[time_index] = np.nanmean(index_lon)

            index = xr.DataArray(index, dims=["time"], coords=[time_list])
        if len(hgtData.shape) == 4:
            _,_, ny, nx = hgtData.shape
            ens_list = hgtData.ens.values
            index = np.full([ens_list.shape[0],time_list.shape[0]], np.nan)
            for ens_index, end in enumerate(ens_list):
                for time_index, time in enumerate(time_list):  # 循环时间维
                    hgt_tmp = hgtData.sel(time=time).values - 5880

                    index_lon = np.full([nx], np.nan)
                    for i in range(nx):  # 循环经度维
                        for j in range(ny):  # 循环纬度维
                            if hgt_tmp[ens_index, j, i] >= 0.0:
                                k = j

                        if "k" in locals():
                            if k == ny - 1:
                                index_lon[i] = lat_list[-1]
                            else:
                                index_lon[i] = (abs(hgt_tmp[ens_index, k, i]) * lat_list[k + 1] + abs(hgt_tmp[ens_index, k + 1, i]) * lat_list[
                                    k]) / (abs(hgt_tmp[ens_index, k, i]) + abs(hgt_tmp[ens_index, k + 1, i]))

                    # index_lon = [[(abs(hgt_tmp[j, i])*lat_list[j+1]+abs(hgt_tmp[j+1, i])*lat_list[j])/(abs(hgt_tmp[j, i])+abs(hgt_tmp[j+1, i])) if hgt_tmp[j, i]*hgt_tmp[j+1,i] <= 0.0 else np.nan for j in range(ny-1)] for i in range(nx)]

                    index[ens_index, time_index] = np.nanmean(index_lon)

            index = xr.DataArray(index, dims=["ens","time"], coords=[ens_list, time_list])
            index = index.T
        # print(gx_data)
        return index

if __name__ == "__main__":
    # ===test===
    ds_hgt = xr.open_dataset('/nfsshare/cdbdata/data/NCEPRA/pressure/hgt/day/2020_07.nc')
    hgt_data = ds_hgt['hgt']
    lon = ds_hgt['lon']
    lon = lon[(lon >=110) & (lon <= 245)]
    lat = ds_hgt['lat']
    lat = lat[(lat >= 10) & (lat <= 60)]
    hgt_data = hgt_data.sel(lat=lat, lon=lon,level=500)
    hgt_data = {"outputData": hgt_data}

    algorithm_input_data = []
    algorithm_input_data.append(hgt_data)
    sub_local_params = {}

    fuc = NorthBoundaryIndex(sub_local_params,algorithm_input_data)
    # print(fuc.output_data)
    print(datetime.now())
    fuc.execute()
    print(datetime.now())
    print(fuc.output_data["outputData"])