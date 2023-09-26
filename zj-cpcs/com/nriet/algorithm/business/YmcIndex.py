#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2021-07-22
# @Author : JiangP
# @File : ZyfIndex.py
"""
1、朱艳峰指数
2、一把梭了
"""

import  numpy as np
from com.nriet.algorithm.business.BusComponent import BusComponent
from com.nriet.utils.GridDataUtils import GridDataUtils
import xarray as xr
import math
class YmcIndex(BusComponent):

    # def __init__(self):
    #     self.timeTypes = "day"
    #     self.dataInputPaths = "/nfsshare/cdbdata/data/NCEPRA/pressure/hgt/"+self.timeTypes+"/"
    #     self.regions = "80,100,15,20"
    #     self.elements = "hgt"
    #     self.level = "500,500"
    #     self.stamp = 5800
    #     self.timeRanges = [20190101,20190121]

    def __init__(self,sub_local_params, algorithm_input_data):
        self.timeTypes = sub_local_params.get("timeType")
        self.dataInputPaths = sub_local_params.get("dataInputPaths")+self.timeTypes+"/"
        self.timeTypes = sub_local_params.get("timeType")
        self.regions = sub_local_params.get("regions")
        self.elements = sub_local_params.get("elements")
        self.level = sub_local_params.get("levels")
        self.timeRanges = sub_local_params.get("timeRanges")
    #     self.climateYear = "1981-2010"
    #     # self.climateYear = sub_local_params.get("ltm")
    #     self.zycstd = [6.7e-5, 3.014939]
    def _get_nc_data(self):
        tmp = GridDataUtils()
        data = tmp.get_grid_mean_data(self.dataInputPaths, self.timeTypes, str(self.timeRanges[0]),
                                      str(self.timeRanges[1]), self.elements, self.regions, self.level)
        return data

    def _BallArea(self,data):
        R = 6378   #这个半径用的是以前的，算下来的结果与原结果一致。实际R应当取6371，结果差别也不大
        gridDistance = abs(np.gradient(data.lon)[0])
        lats = data.lat.values
        area = []
        for lat in lats:
            lat_area = R*R*(gridDistance*math.pi/180.)*\
                   (math.sin((lat+0.5*gridDistance)*math.pi/180.)-math.sin((lat-0.5*gridDistance)*math.pi/180.))
            area.append(lat_area)
        area = xr.DataArray(area,dims=["lat"],coords=[data.lat])
        return data*area

    def execute(self):
        flow_data = {}
        hgt = self._get_nc_data().mean(axis=1)-5800
        areaS = self._BallArea(hgt).sum(axis=(1,2))/1000000
        flow_data["outputData"] = areaS
        self.output_data = flow_data


# if __name__ == "__main__":
#     a = YmcIndex()
#     data = a._get_nc_data()
#
#     a.execute()

