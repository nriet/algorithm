#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time: 2020/3/25 下午7:18
# @Author: Shiys
# @File: PolarVortexAreaIndex.py
import xarray as xr
import numpy as np
import math

from com.nriet.algorithm.business.BusComponent import BusComponent

class PolarVortexAreaIndex(BusComponent):

    def __init__(self, sub_local_params, algorithm_iuput_data):
        self.flow_data = algorithm_iuput_data

        if isinstance(self.flow_data[0]["outputData"], list):
            self.inputData = self.flow_data[0]["outputData"][0]
        else:
            self.inputData = self.flow_data[0]["outputData"]
        self.R = float(sub_local_params["R"])
        self.gridDistance = float(sub_local_params["gridDistance"])
        self.output_data = None

    def execute(self):
        shape = self.inputData.shape
        pvl = [0, 5480, 5520, 5520, 5520, 5600, 5680, 5720, 5720, 5680, 5640, 5560, 5520]
        # 监测数据，时间*纬度*经度
        pv_list =[]
        if len(shape) == 3:
            time_list = self.inputData.time.values
            for i,tt in enumerate(time_list):
                mon = int(tt[4:6])
                tmp_data = self.inputData.sel(time=tt)
                tmp_value = pvl[mon]
                if np.isnan(tmp_data).all():
                    pv_list.append(np.nan)
                else:
                    pv_list.append(self.cal_pv_area(tmp_data, tmp_value, 1, 4))
        pv_area = xr.DataArray(pv_list,coords=[self.inputData.time],dims=['time'])
        output_data = {
            "outputData": pv_area
        }
        self.output_data = output_data

    def cal_pv_area(self,data, value, n1, n2):
        """
            球面面积计算，网格近似梯形计算，单位为：万平方千米
            方法来源：王东仟
            hx(i,j)=6371.0*6371.0*(grid*pi/180.0)/100000*
         &(sin((lat+0.5*grid)*pi/180.0)-sin((lat-0.5*grid)*pi/180.0))
            """
        lats = data.lat.values
        area = []
        for lat in lats:
            lat_area = self.R * self.R * (self.gridDistance * math.pi / 180.) * (
                        math.sin((lat + 0.5 * self.gridDistance) * math.pi / 180.) - math.sin(
                    (lat - 0.5 * self.gridDistance) * math.pi / 180.))
            area.append(lat_area)
        # 筛选大于极涡南界特征等高线点，并设置该点的面积
        shape = data.shape
        jw_area_data = np.full(shape, np.nan)
        ny,nx = shape[0],shape[1]
        for i in range(1,ny):
            for j in range(0,nx):
                s_j = j - n1
                if s_j < 0:
                    s_j = 0
                e_j = j + n1
                if e_j > nx - 1:
                    e_j = nx - 1
                s_i = i - n1
                e_i = i + n1
                if e_i > ny - 1:
                    e_i = ny - 1
                tdata = data[s_i:e_i + 1, s_j:e_j + 1]
                if len(np.where(tdata <= value)[0]) >= n2:
                    jw_area_data[i, j] = area[i]
        # 计算满足条件的各点的面积之和
        pv = np.nansum(jw_area_data)/1000000
        return pv


if __name__ == '__main__':
    dataInputPath = "/nfsshare/cdbdata/data/NCEPRA/pressure/hgt/mon/2020.nc"
    ds = xr.open_dataset(dataInputPath)
    par_data = ds["hgt"]
    nc_data = par_data
    level = "500,500"
    regions = "70,140,10,60"
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
    gg = PolarVortexAreaIndex({"R":"6371","gridDistance":"2.5"},[{"outputData":nc_data}])
    gg.execute()