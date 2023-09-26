#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020-10-13
# @Author : JiangP
#西太副高——强度指数

from com.nriet.algorithm.business.BusComponent import BusComponent
import xarray as xr
import numpy as np
import math
import logging

class WpshIntensity(BusComponent):
    def __init__(self, sub_local_params, algorithm_iuput_data):
        self.flow_data = algorithm_iuput_data
        if isinstance(self.flow_data[0]["outputData"], list):
            self.inputData = self.flow_data[0]["outputData"][0]
        else:
            self.inputData = self.flow_data[0]["outputData"]
        # self.R = 6300
        self.gridDistance = float(sub_local_params["gridDistance"])
        self.R  = float(sub_local_params["R"])
        self.output_data = None

    # def __init__(self,  iuput_data):
    #     # self.flow_data = algorithm_iuput_data[0]
    #     self.inputData = iuput_data
    #     self.R = 6371.
    #     self.gridDistance = 2.5
    #     self.output_data = None
    """
    此处筛选500hPa位势高度数据大于5880，满足的设置为1，其余设置为缺测
    """
    def  GridScreen(self,data):
        return xr.where(data>=5880,1,np.nan)

    """
    强度计算：
    1.球面面积计算，网格近似梯形计算，单位为：万平方千米
    2.强度计算
    """
    def Wpsh_Intensity(self,data,R,gridDistance):
        lats = data.lat.values
        area = []
        for lat in lats:
            lat_area = R * R * (gridDistance * math.pi / 180.) / 100000 * \
                       (math.sin((lat + 0.5 * gridDistance) * math.pi / 180.) - math.sin(
                           (lat - 0.5 * gridDistance) * math.pi / 180.))
            area.append(lat_area)
        hgt = xr.where(data>=5880,data,np.nan)
        ScreenGrid = self.GridScreen(data)
        Intensity = []
        for i in range(len(lats)):
            Intensity.append(np.nansum(ScreenGrid[i,:].values*area[i]*(hgt[i,:].values-5870)/10))
        return sum(Intensity)

    def execute(self):
        flow_data = {}
        # logging.info(self.inputData)
        shape = self.inputData.shape
        ScreenHgt = self.GridScreen(self.inputData)
        wpsh = xr.Dataset()
        wpsh.coords['time'] = xr.DataArray(self.inputData['time'], dims=('time',))
        #监测数据，时间*纬度*经度
        if len(shape) == 3:
            wpsh_Intensity = [self.Wpsh_Intensity(self.inputData[i,:,:],self.R,self.gridDistance) for i in range(shape[0])]
            wpsh = xr.DataArray(wpsh_Intensity,dims='time')
            wpsh.coords['time'] = xr.DataArray(self.inputData['time'], dims=('time',))
        # 预测数据，时间*样本*纬度*经度
        if len(shape) == 4:
            wpsh_Intensity = np.full(shape[:2],np.nan)
            for e in range(shape[0]):
                wpsh_Intensity[e,:] = [self.Wpsh_Intensity(self.inputData[e,i,...],
                                                           self.R, self.gridDistance) for i in range(shape[1])]
            wpsh = xr.DataArray(wpsh_Intensity,dims=['ens','time'])
            wpsh.coords['time'] = xr.DataArray(self.inputData['time'], dims=('time',))
            wpsh.coords['ens'] = xr.DataArray(self.inputData['ens'], dims=('ens',))
            wpsh = wpsh.T
        flow_data["outputData"] = wpsh
        self.output_data = flow_data
# from com.nriet.utils.GridDataUtils import GridDataUtils
# monitorPath = "/nfsshare/cdbdata/data/NCEPRA/pressure/hgt/day/"
# tmp = GridDataUtils()
# data = tmp.get_day_mean_data(monitorPath, "day", "20190803", "20190812",
#                              "hgt", "110,180,10,60", "500")
# data = data.mean(dim='level')
# forePath = "/nfsshare/cdbdata/data/NCEP/cfs_day/h500/day/"

# a = WpshIntensity(data)
# a.execute()
