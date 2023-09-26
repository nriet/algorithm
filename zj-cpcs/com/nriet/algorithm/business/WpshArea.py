#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020-10-13
# @Author : JiangP
#西太副高——面积指数

from com.nriet.algorithm.business.BusComponent import BusComponent
import xarray as xr
import numpy as np
import math


class WpshArea(BusComponent):
    def __init__(self, sub_local_params, algorithm_iuput_data):
        self.flow_data = algorithm_iuput_data
        if isinstance(self.flow_data[0]["outputData"], list):
            self.inputData = self.flow_data[0]["outputData"][0]
        else:
            self.inputData = self.flow_data[0]["outputData"]
        self.R = sub_local_params["R"]
        self.gridDistance = float(sub_local_params["gridDistance"])
        self.output_data = None

    # def __init__(self,  iuput_data):
    #     # self.flow_data = algorithm_iuput_data[0]
    #     self.inputData = iuput_data
    #     self.R = 6371.
    #     self.gridDistance = 2.5
    #     self.output_data = None
    """
    此处筛选500hPa位势高度数据，小于5880的全部设置为缺测
    """
    def  GridScreen(self,data):
        return xr.where(data>=5880,1,np.nan)

    """
    球面面积计算，网格近似梯形计算，单位为：万平方千米
    方法来源：刘芸芸
    """
    # def BallArea(self,data,R,gridDistance):
    #     lat = data.lat.values
    #     ln = R*np.cos((lat+gridDistance)/180.)*gridDistance/180.
    #     ls = R*np.cos(lat/180.)*gridDistance/180.
    #     le = R*gridDistance / 180.
    #     area = (ln+ls)*le/20000.
    #     areas = []
    #     for i in range(len(lat)):
    #         areas.append(np.nansum(data[i,:].values*area[i]))
    #     return sum(areas)

    """
        球面面积计算，网格近似梯形计算，单位为：万平方千米
        方法来源：王东仟
        hx(i,j)=6371.0*6371.0*(grid*pi/180.0)/100000*
     &(sin((lat+0.5*grid)*pi/180.0)-sin((lat-0.5*grid)*pi/180.0)) 
        """

    def BallArea(self,data,R,gridDistance):
        lats = data.lat.values
        area = []
        areas = []
        for lat in lats:
            lat_area = R*R*(gridDistance*math.pi/180.)/100000*\
                   (math.sin((lat+0.5*gridDistance)*math.pi/180.)-math.sin((lat-0.5*gridDistance)*math.pi/180.))
            area.append(lat_area)
        for i in range(len(lats)):
            areas.append(np.nansum(data[i,:].values*area[i]))
        return sum(areas)

    def execute(self):
        flow_data = {}
        shape = self.inputData.shape
        ScreenHgt = self.GridScreen(self.inputData)
        wpsh = xr.Dataset()
        wpsh.coords['time'] = xr.DataArray(self.inputData['time'], dims=('time',))
        #监测数据，时间*纬度*经度
        if len(shape) == 3:
            wpsh_area = [self.BallArea(ScreenHgt[i,:,:],self.R,self.gridDistance) for i in range(shape[0])]
            wpsh = xr.DataArray(wpsh_area,dims='time')
        # 预测数据，时间*样本*纬度*经度
        if len(shape) == 4:
            wpsh.coords['ens'] = xr.DataArray(self.inputData['ens'], dims=('ens',))
            wpsh_area = np.full(shape[:2],np.nan)
            for e in range(shape[0]):
                wpsh_area[e,:] = [self.BallArea(ScreenHgt[e, i,...], self.R, self.gridDistance) for i in range(shape[1])]
            wpsh = xr.DataArray(wpsh_area,dims=['ens',"time"])
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
#
# a = WpshArea(data)
# a.execute()
