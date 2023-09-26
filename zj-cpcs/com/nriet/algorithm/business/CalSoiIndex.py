#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2021/02/22
# @Author : jiangP
# @File : CalSoiIndex.py
import xarray as xr
from com.nriet.algorithm.business.BusComponent import BusComponent
from com.nriet.utils.StationDataUtils import StationDataUtils
import numpy as np
import struct
import pandas as pd

class CalSoiIndex(BusComponent):
    def __init__(self,sub_local_params,algorithm_input_data):
        self.flow_data = algorithm_input_data
        if isinstance(self.flow_data[0]["outputData"], list):
            self.inputData = self.flow_data[0]["outputData"][0]
        else:
            self.inputData = self.flow_data[0]["outputData"]
        self.timeRanges = sub_local_params.get("timeRanges")
        self.timeType = sub_local_params.get("timeType")
        # self.dataInputPaths = sub_local_params.get("dataInputPaths")
        self.stdInputPaths = sub_local_params.get("stdInputPaths")
        self.output_data = None

    def Soi(self):
        indexslp = self.inputData[:, 0] - self.inputData[:, 1]

        # --------------------------------------------------------------------
        # year_list = range(1991, 2021)
        # res_data = []
        # for year in year_list:
        #     ds = xr.open_dataset("/nfsshare/cdbdata/data/STATION/darwin/day/"+str(year)+".nc")
        #     tmpdata = ds['slp']
        #     res_data.append(tmpdata)
        # station_mean_data = xr.concat(res_data, dim='time')
        # indexslp = station_mean_data[:, 0] - station_mean_data[:, 1]
        # resultavg = []
        # resultstd = []
        # for i in range(366):
        #     resultData = indexslp[i::366]
        #     avg = np.nanmean(resultData.values)
        #     std = np.nanstd(resultData.values)
        #     resultavg.append(avg)
        #     resultstd.append(std)
        # #
        # np.savetxt("/nfsshare/soi_day.txt",[resultavg,resultstd],fmt="%.5f")
        # --------------------------------------------------------------------

        timeList = self.inputData.time.values
        stdData = pd.read_csv(self.stdInputPaths, header=None, sep="\t")
        if self.timeType == "mon":
            index = [list(stdData.loc[:, 0]).index(int(i) % 100) for i in timeList]
        if self.timeType == "day":
            index = [list(stdData.loc[:, 0]).index(int(i) % 10000) for i in timeList]
        if self.timeType == "five":
            index = [list(stdData.loc[:, 0]).index(int(i) % 10000) for i in timeList]
        soi = (indexslp - (stdData.loc[:, 1])[index]) / (stdData.loc[:, 2])[index]
        return soi

    def execute(self):
        outputData = {}
        outputData["outputData"] = self.Soi()
        self.output_data = outputData

# if __name__ == "__main__":
#     S = StationDataUtils()
#     stationDataPath =  "/nfsshare/cdbdata/data/STATION/darwin/day/#YYYY#.nc"
#     timeType = "day"
#     stdInputPaths = "/nfsshare/cdbdata/data/STATION/darwin/ltm/"+timeType+"_avg_std.txt"
#     timeRanges = [20201202,20210121]
#     elements = "slp"
    # for year in range(timeRanges[0]//10000,timeRanges[1]//10000+1):
    #     startMon = np.where(year==timeRanges[0]//10000,timeRanges[0]%100%100,1)
    #     endMon = np.where(year==timeRanges[1]//10000,timeRanges[0]%100%100,12)
    #     for mon in range(startMon,endMon+1):
    #         dataFile =
