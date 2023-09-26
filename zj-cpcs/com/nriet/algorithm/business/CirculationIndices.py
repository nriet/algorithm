#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time: 2020/3/25 下午7:18
# @Author: Shiys
# @File: CirculationIndices.py
import xarray as xr
import numpy as np
import math

from com.nriet.algorithm.business.BusComponent import BusComponent

class CirculationIndices(BusComponent):

    def __init__(self, sub_local_params, algorithm_iuput_data):
        self.flow_data = algorithm_iuput_data

        if isinstance(self.flow_data[0]["outputData"], list):
            self.inputData = self.flow_data[0]["outputData"][0]
        else:
            self.inputData = self.flow_data[0]["outputData"]
        self.elementType = sub_local_params.get("elementType")
        self.output_data = None

    def execute(self):
        hgtData = self.inputData

        if self.elementType == "IZ":  # 计算纬向环流
            tmphgt = hgtData[:,:,::6]
            diff = tmphgt.sel(lat=45) - tmphgt.sel(lat=60)
            nlon = diff.shape[1]
            fz = diff.sum(dim="lon")
            fm = 20. * nlon
            zs = fz / fm

        else:   # 计算经向环流
            tmphgt = hgtData[:, ::4, ::6]
            shape = tmphgt.shape
            tmp = np.full(shape[0:2], np.nan)
            nlat = shape[1]
            nlon = shape[2]
            lats = tmphgt.lat.values
            for i in range(nlat):
                for j in range(nlon-1):
                    tmp[:,i] = (tmphgt.isel(lat=i,lon=j) - tmphgt.isel(lat=i,lon=j+1))/math.cos(lats[i])
            fz = abs(np.nansum(tmp, axis=1))
            fm = 3. * 15. * nlon
            zs = fz / fm
            zs = xr.DataArray(zs,coords=[hgtData.time],dims=['time'])
        # 处理区域范围的数据全缺测时，计算出的指数为0的异常处理
        # 设置 缺测值为0,非缺测为1
        hgtData = xr.where(np.isnan(hgtData), 0, 1)
        # 统计求和的维
        dims = list(hgtData.dims)
        dims.remove("time")
        miss_index = list(np.where(hgtData.sum(dim=dims).values == 0)[0])
        if len(miss_index)>0:
            zs[miss_index] = np.nan
        # print(zs)
        output_data = {
            "outputData": zs
        }
        self.output_data = output_data


if __name__ == '__main__':
    dataInputPath = "/nfsshare/cdbdata/data/NCEPRA/pressure/hgt/mon/2020.nc"
    ds = xr.open_dataset(dataInputPath)
    par_data = ds["hgt"]
    nc_data = par_data
    level = "500,500"
    regions = "0,150,45,65"
    if level is not None and level != "":
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

    nc_data = nc_data.mean(dim="level")
    gg = CirculationIndices({"elementType":"IM"},[{"outputData":nc_data}])
    gg.execute()