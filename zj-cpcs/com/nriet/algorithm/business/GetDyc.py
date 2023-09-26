#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/10/22
# @Author : jiangP
# @File : AoIndex.py;东亚大槽
import xarray as xr
from com.nriet.algorithm.business.BusComponent import BusComponent
# import cartopy.crs as ccrs
# import cartopy.feature as cfeature
import numpy as np
import os
import struct
import pandas as pd
class GetDyc(BusComponent):

    def __init__(self,sub_local_params,algorithm_input_data):
        self.flow_data = algorithm_input_data
        if isinstance(self.flow_data[0]["outputData"], list):
            self.inputData = self.flow_data[0]["outputData"][0]
        else:
            self.inputData = self.flow_data[0]["outputData"]
        self.type = sub_local_params['type']
        self.output_data = None

    # def __init__(self, hgtData):
    #     # self.flow_data = algorithm_input_data[0]
    #     self.inputData = hgtData
    #     self.output_data = None

    def dyc(self,hgt1):
        #数据全缺测，则返回nan
        if hgt1.isnull().all():
            return np.nan
        lons = hgt1.lon.values.tolist()
        try:
            si = lons.index(110)
            ei = lons.index(170)
        except ValueError:
            ysi = str(self._getLeastLon(lons,[110]))
            yei = str(self._getLeastLon(lons,[170]))
            si = int(ysi[1:-1])
            ei = int(yei[1:-1])
        hgt = hgt1[:, si:ei + 1]
        lon = hgt.lon
        lat = hgt.lat
        size1 = hgt1.shape
        size = hgt.shape
        htemp = np.zeros(size)
        htro = np.zeros(size[0])
        lave = np.zeros(size[1])
        ltemp = np.zeros(size)
        mark1 = np.zeros(size1)
        mark = np.zeros(size)
        lontro = np.zeros(size[0])
        nums = 0
        # for j in range(1,size[1]-1):
        # size: lat(ny) * lon(nx)
        for j in range(1,size[1]-1):
            for i in range(size1[0]):
                if hgt1[i,j]<hgt1[i,j-1] and hgt1[i,j]<hgt1[i,j+1]:
                    nums+=1
                    mark1[i,j] = 1
        logs = 0
        mark = mark1[:,si:ei+1]
        if nums>=5:
            k = -1
            while nums>=5:
                k += 1
                if k==10:
                    break
                # 45度
                markrun = np.zeros(size)
                for j in range(size[1]):
                    if mark[2,j] == 1:
                        ltemp[2, k] = lon[j]
                        lave[k] += lon[j]
                        htemp[2,k] = hgt[i,j]
                        markrun[i,j] = 1
                        break
                if ltemp[2,k]!= 0:
                    # 50、55度
                    for j in range(size[1]):
                        for jrun in range(4, 6):
                            for i in range(size[0]):
                                if abs(lat[i]-(30+5*jrun))<0.1:
                                    #这边疑似应该为ltemp[2,k],下面几个疑似都应该为ltemp[2,k]，与45°纬线比较
                                    if mark[i,j]==1 and abs(lon[j]-ltemp[3,k])<=(5*jrun-10):
                                        ltemp[jrun - 1, k] = lon[j]
                                        lave[k] += lon[j]
                                        htemp[jrun - 1, k] = hgt[i,j]
                                        markrun[i,j] = 1
                                        break
                    # 35、40度
                    for j in range(size[1]):
                        for jrun in range(1,3):
                            for i in range(size[0]):
                                if abs(lat[i] - (30 + 5 * jrun)) < 0.1:
                                    if mark[i,j] == 1 and abs(lon[j]-ltemp[3,k])<=(20-5*jrun):
                                        ltemp[jrun - 1, k] = lon[j]
                                        lave[k] += lon[j]
                                        htemp[jrun - 1, k] = hgt[i, j]
                                        markrun[i, j] = 1
                                        break
                    numrun = 0
                    for j in range(size[1]):
                        for i in range(size[0]):
                            if markrun[i, j]==1:
                                numrun += 1
                    if numrun == 5:
                        lave[k] =lave[k]/ numrun
                        for j in range(size[1]):
                            for i in range(size[0]):
                                if markrun[i, j] == 1:
                                    nums += -1
                                    mark[i,j] = 0
                    else:
                        lave[k] = 0
                        for j in range(size[1]):
                            for i in range(size[0]):
                                if abs(lat[i]-45)<0.1 and abs(lon[j]-ltemp[3,k])<0.1:
                                    nums += -1
                                    mark[i, j] = 0
                                    break
                                    break
                else:
                    break
            kp = -1
            for k in range(10):
                if lave[k]!=0:
                    kp = k
                    break
            if kp != -1:
                for k in range(10):
                    if abs(lave[k]-130)<abs(lave[kp]-130):
                        kp = k
                lontro = ltemp[:,kp]
                htro = htemp[:,kp]
                logs = 1
        if logs == 0:
            #45°
            hgt_45 = hgt[2]
            jp = hgt_45.values.tolist().index(hgt_45.values.min())
            lontro[2] = lon[jp]
            htro[2] = hgt_45.min()
            # 50°
            hgt_50 = hgt[3]
            lon50 = lon[(lon>=lontro[2]-10) & (lon<=lontro[2]+15)]
            jp = hgt_50.values.tolist().index(hgt_50.sel(lon = lon50 ).min())
            lontro[3] = lon[jp]
            htro[3] = hgt_50.min()
            # 40°
            hgt_40 = hgt[1]
            lon40 = lon[(lon>=lontro[2]-10) & (lon<=lontro[2]+15)]
            jp = hgt_40.values.tolist().index(hgt_40.sel(lon=lon40).min())
            lontro[1] = lon[jp]
            htro[1] = hgt_40.min()
            # 55°
            hgt_55 = hgt[4]
            lon55 = lon[(lon >= lontro[3] - 10) & (lon <= lontro[3] + 15)]
            jp = hgt_55.values.tolist().index(hgt_55.sel(lon=lon55).min())
            lontro[4] = lon[jp]
            htro[4] = hgt_55.min()
             # 35°
            hgt_35 = hgt[0]
            lon35 = lon[(lon >= lontro[1] - 10) & (lon <= lontro[1] + 15)]
            jp = hgt_35.values.tolist().index(hgt_35.sel(lon=lon35).min())
            lontro[0] = lon[jp]
            htro[0] = hgt_35.min()

        dycindex = lontro.mean()
        dycqd = htro.sum() + htro.min()-htro.max()
        if self.type=="qd":
            return dycqd
        else:
            return dycindex

    def _getLeastLon(self, lons, values):
        s = []
        for v in values:
            tmp = [abs(lon - v) for lon in lons]
            s.append(tmp.index(min(tmp)))
        return s

    def execute(self):
        out_data = {}
        timeList = self.inputData.time
        lats = self.inputData.lat.values
        lons = self.inputData.lon.values
        try:
            hgtData = self.inputData.sel(lat = range(35,60,5),lon = self.inputData.lon[(self.inputData.lon>=107.5) & (self.inputData.lon<=172.5)])
        except KeyError:
            latindex = self._getLeastLon(lats, range(35,60,5))
            if len(self.inputData.shape) == 3:
                hgtData = self.inputData[:,latindex,:].sel(lon = self.inputData.lon[(self.inputData.lon>=107.5) & (self.inputData.lon<=172.5)])
            else:
                hgtData = self.inputData[:,:,latindex,:].sel(lon = lons[(lons >= 107.5) & (lons <= 172.5)])
        if len(self.inputData.shape)==3:
            dydc = np.full((len(timeList)),np.nan)
            for t,time in enumerate(timeList):
                mon = int(time.values)//100%100
                #东亚槽定义：6~8月不计算
                # if mon>=6 and mon<=8:
                #     continue
                hgt = hgtData[t]
                dydc[t] = self.dyc(hgt)
            result = xr.DataArray(dydc,coords=[timeList],dims=["time"])
        else:
            dydc = np.full(self.inputData.shape[:2] ,np.nan)
            for t,time in enumerate(timeList):
                mon = int(time.values)//100%100
                #东亚槽定义：6~8月不计算
                # if mon>=6 and mon<=8:
                #     continue
                for e,ens in enumerate(self.inputData.ens):
                    hgt = hgtData.sel(ens = ens,time = time)
                    dydc[e,t] = self.dyc(hgt)
            result = xr.DataArray(dydc,coords=[self.inputData.ens,timeList],dims=["ens","time"])
            result = result.T
        out_data["outputData"] = result
        self.output_data = out_data

# from com.nriet.utils.GridDataUtils import GridDataUtils
# hgtPath = "/nfsshare/cdbdata/data/NCEPRA/pressure/hgt/day/"
# hgtPath = "/nfsshare/cdbdata/data/NCEPRA/pressure/hgt/mon/"


# from com.nriet.utils.NcepCfsDataUtils import NcepCfsDataUtils
# forePath = "/nfsshare/cdbdata/data/NCEP/cfs_day/h500/day/#YYYY#/#MM#/#YYYYMMDD#_#HH#_#NM#.nc"
# hfore = NcepCfsDataUtils()
# h = GridDataUtils()
# hgtfore = hfore.get_cfs_mean_data(forePath,"20200801","20200802","20200831","h500",35,85,0,360,False)
# a = BlockingHig(hgtfore)
# a.execute()
# exit()
# # hgt = h.get_day_mean_data(hgtPath,"day","20190801","20190831","hgt","0,360,35,85","500").mean(dim='level')
# hgt = h.get_mon_mean_data(hgtPath,"mon","201510","201604","hgt","90,360,0,90","500").mean(dim='level')
# a = GetDyc(hgt)
# a.execute()
