#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020-10-13
# @Author : JiangP
#西太副高——西伸脊点

from com.nriet.algorithm.business.BusComponent import BusComponent
import xarray as xr
import numpy as np
import logging
from com.nriet.utils.config.ConfigUtils import look_for_gbase_connection_config
from com.nriet.utils.databaseConnection.GbaseHandler import GbaseHandler

class WestRidgePoint(BusComponent):
    def __init__(self, sub_local_params, algorithm_iuput_data):
        self.flow_data = algorithm_iuput_data
        if isinstance(self.flow_data[0]["outputData"], list):
            self.inputData = self.flow_data[0]["outputData"][0]
        else:
            self.inputData = self.flow_data[0]["outputData"]
        self.gridDistance = float(sub_local_params["gridDistance"])
        self.dataSource = sub_local_params.get("dataSource")
        self.output_data = None

    # def __init__(self,  iuput_data):
    #     # self.flow_data = algorithm_iuput_data[0]
    #     self.inputData = iuput_data
    #     self.gridDistance = 2.5
    #     self.output_data = None

    def queryStationInfoData(self,startYear,nowYear,mon):
        # 初始化数据库连接
        mydb = GbaseHandler(look_for_gbase_connection_config())
        sql_str = "select max(t.D_VALUE) D_VALUE from ncc_cipas.cipas_product_index_mop_mon t " \
        "where D_PRODUCT_ID = 'BUSS_MF_EWI_WPSHRIDGEPOINTM_001' " \
        "and v04002 = '%s' " \
        "and D_DATASOURCE = '%s' " \
        "and v04001 between '%s' " \
        "and '%s' " \
        "and t.D_VALUE != 'nan' "
        # 查询数据
        sql_result = mydb.executeSql(sql_str%(mon,self.dataSource,startYear,nowYear))
        return sql_result[0]["D_VALUE"]


    def execute(self):
        flow_data = {}
        shape = self.inputData.shape
        wpsh = xr.Dataset()
        #监测数据，时间*纬度*经度
        timeList = self.inputData.time.values
        lon_list = self.inputData.lon.values
        nx = len(lon_list)
        lat_list = self.inputData.lat.values
        ny = len(lat_list)
        if lat_list[0] > lat_list[-1]:
            lat_list = lat_list[::-1]
            self.inputData = self.inputData.sel(lat=lat_list)
        if len(shape) == 3:
            gd = np.full(len(timeList),np.nan)
            for time_index, time in enumerate(timeList):
                hgtData = self.inputData.sel(time=time).values
                for k in range(1, nx - 1):  # 循环经度维
                    i = nx - k
                    for j in range(ny - 1):  # 循环纬度维
                        if hgtData[j,i] >= 5880.0 and hgtData[j, i-1] < 5880.0:
                            gd[time_index] = i - (hgtData[j,i]-5880.)/(hgtData[j,i]-hgtData[j,i-1])
                            gd[time_index] = gd[time_index] * self.gridDistance + 90
                            # logging.info(gd[time_index] )
                #统计是否达到90 ºE边界
                hgtData[:, 2][hgtData[:,2]>5880.] = 99999.
                ks = list(hgtData[:,2]).count(99999)
                if ks>= 1:
                    if any(hgtData[:,1]>=5880.):
                        gd[time_index] = 90.
            wpsh = xr.DataArray(gd, dims='time')
            wpsh.coords['time'] = xr.DataArray(self.inputData['time'], dims=('time',))
            print(wpsh.values)
            #针对月尺度
            if len(str(self.inputData.time[0].values)) == 6:
                startYear = "1901"
                #针对NCEP跟CRA需要单独配置
                if self.dataSource:
                    for t,time in enumerate(wpsh.time.values):
                        #如果是因为算出来是缺测 ， 而不是吊原始数据缺测
                        if np.isnan(wpsh[t]) and (not np.isnan(self.inputData.sel(time=time)).all()):
                            #查询该月的历史极大值
                            mon = time[4:]
                            nowYear = str(int(time[0:4])-1)#结束年要往前推一推
                            wpsh[t] = self.queryStationInfoData(startYear,nowYear,mon)
            print(wpsh.values)
        # 预测数据，时间*样本*纬度*经度
        if len(shape) == 4:
            ens = self.inputData.ens
            gd = np.full((len(timeList),len(ens)),np.nan)
            for ens_index,indx in enumerate(ens):
                for time_index, time in enumerate(timeList):
                    hgtData = self.inputData.sel(ens = indx,time=time).values
                    for i in range(1, nx - 1):  # 循环经度维
                        k = nx - i
                        for j in range(1, ny - 1):  # 循环纬度维
                            if hgtData[j, k] >= 5880.0 and hgtData[j, k - 1] < 5880.0:
                                gd[time_index,ens_index] = k - (hgtData[j, k] - 5880.) / (hgtData[j, k] - hgtData[j, k - 1])
                                gd[time_index,ens_index] = gd[time_index,ens_index] * self.gridDistance + 90
                    # 统计是否达到90 ºE边界
                    hgtData[:, 2][hgtData[:, 2] > 5880.] = 99999.
                    ks = list(hgtData[:, 2]).count(99999)
                    if ks >= 1:
                        if any(hgtData[:, 1] >= 5880.):
                            gd[time_index,ens_index] = 90.
            wpsh = xr.DataArray(gd, dims=['time','ens'])
            wpsh.coords['ens'] = xr.DataArray(self.inputData['ens'], dims=('ens',))
            wpsh.coords['time'] = xr.DataArray(self.inputData['time'], dims=('time',))
        flow_data["outputData"] = wpsh
        self.output_data = flow_data
# from com.nriet.utils.GridDataUtils import GridDataUtils
# monitorPath = "/nfsshare/cdbdata/data/NCEPRA/pressure/hgt/day/"
# tmp = GridDataUtils()
# data = tmp.get_day_mean_data(monitorPath, "day", "20190803", "20190812",
#                              "hgt", "90,180,10,45", "300,500")
# data = xr.DataArray(data.copy(),coords = [data['time'],data['level'],data['lat'],data['lon']],dims = ['time','ens','lat','lon'])
# data = data.mean(dim='level')
# forePath = "/nfsshare/cdbdata/data/NCEP/cfs_day/h500/day/"

# a = WestRidgePoint(data)
# a.execute()
