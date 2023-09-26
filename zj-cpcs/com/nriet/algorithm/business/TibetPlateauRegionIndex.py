#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2021-10-13
# @Author : JiangP
#西藏高原指数

from com.nriet.algorithm.business.BusComponent import BusComponent
import xarray as xr
import numpy as np
import math


class TibetPlateauRegionIndex(BusComponent):
    def __init__(self, sub_local_params, algorithm_iuput_data):
        self.flow_data = algorithm_iuput_data
        if isinstance(self.flow_data[0]["outputData"], list):
            self.inputData = self.flow_data[0]["outputData"][0]
        else:
            self.inputData = self.flow_data[0]["outputData"]

    # def __init__(self,data):
    #     self.inputData = data
    def _BallArea(self,data):
        """
        球面面积计算，网格近似梯形计算，单位为：万平方千米
        方法来源：王东仟
        hx(i,j)=6371.0*6371.0*(grid*pi/180.0)/100000*(sin((lat+0.5*grid)*pi/180.0)-sin((lat-0.5*grid)*pi/180.0))
        :param data:原始数据（必须带经纬度）
        :return: 数据格点对应的面积
        """
        R = 6378.
        lats = data.lat.values
        lons = data.lon.values
        gridDistance = abs(np.gradient(lats))[0]
        areas = np.full((len(lats), len(lons)), np.nan)
        for l,lat in enumerate(lats):
            areas[l,...] = R*R*(gridDistance*math.pi/180.)/100000*\
                   (math.sin((lat+0.5*gridDistance)*math.pi/180.)-math.sin((lat-0.5*gridDistance)*math.pi/180.))

        areas = xr.DataArray(areas, dims=["lat","lon"], coords=[data.lat,data.lon])
        return areas

    def execute(self):
        flow_data = {}
        tpr = (self.inputData*self._BallArea(self.inputData)).sum(axis=(1,2))
        #临时针对数据缺测时，求和为0做处理
        tpr = xr.where(tpr==0,np.nan,tpr)
        flow_data["outputData"] = tpr/10.
        self.output_data = flow_data


# if __name__ == "__main__":
#     from com.nriet.utils.GridDataUtils import GridDataUtils
#     monitorPath = "/nfsshare/cdbdata/data/NCEPRA/pressure/hgt/day/"
#     tmp = GridDataUtils()
#     data = tmp.get_day_mean_data(monitorPath, "day", "20200101", "20200131",
#                                  "hgt", "80,100,25,35", "500")
#     data = data.mean(dim='level')-5000
#
# # forePath = "/nfsshare/cdbdata/data/NCEP/cfs_day/h500/day/"
# #
#     a = TibetPlateauRegionIndex(data)
#     a.execute()
