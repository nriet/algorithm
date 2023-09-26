#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2021-07-21
# @Author : JiangP
# @File : StandardizationAnomalyModalPrjection.py
"""
1、北大西洋涛动
2、标准化距平模态投影
"""
from math import e as exp
import  numpy as np
from com.nriet.utils.GridDataUtils import GridDataUtils
from com.nriet.algorithm.business.BusComponent import BusComponent
import xarray as xr
import math
class StandardizationAnomalyModalPrjection(BusComponent):
    def __init__(self,sub_local_params, algorithm_input_data):
        self.flow_data = algorithm_input_data
        if isinstance(self.flow_data[0]["outputData"], list):
            self.hgt = self.flow_data[0]["outputData"][0]
        else:
            self.hgt = self.flow_data[0]["outputData"]

        if isinstance(self.flow_data[1]["outputData"], list):
            self.hgtltm = self.flow_data[1]["outputData"][0]
        else:
            self.hgtltm = self.flow_data[1]["outputData"]

        if isinstance(self.flow_data[2]["outputData"], list):
            self.std = self.flow_data[2]["outputData"][0]
        else:
            self.std = self.flow_data[2]["outputData"]
        self.type = sub_local_params.get("type") #用于识别是截取哪个模态
        self.patPath = sub_local_params.get("patPath") #模态文件
        self.patvar = sub_local_params.get("patvar") #模态存储的要素名称

    # def __init__(self):
    #     self.type = "NAO"
        # self.
    #     pass

    """
    获取模态数据，前10个模态对应的就是北大西洋涛动以及遥相关指数的几个
    """
    def __getpatdata(self,type="NAO"):
        elementTypes = ["NAO", "PNA", "EA", "WP", "NP", "EAWR", "TNH", "POL", "SCA", "PT" ]
        # patPath = "/nfsshare/cdbdata/data/NCEPRA/pressure/cli_pattern/cli_ao_pattern.nc"
        # patvar = "ao_pat"
        ds_pat = xr.open_dataset(self.patPath)
        pat = ds_pat[self.patvar]
        return pat[elementTypes.index(type)+2::10,...]

    def execute(self):
        hgt = self.hgt
        hgtltm = self.hgtltm
        std = self.std
        flow_data = {}
        pat = self.__getpatdata(self.type)
        hgtstd = ((hgt - hgtltm)/std)
        ai_mean = np.full(hgtstd.shape[0],np.nan)
        for i , t in enumerate(hgtstd.time.values):
            mon = int(t)%100-1
            pattemp = pat[mon,...]
            patvars = math.sqrt((pattemp**2).mean())
            samp = (hgtstd[i,...]*pattemp/patvars).mean()
            ai_mean[i] = samp
        ai_mean = xr.DataArray(ai_mean, dims=["time"], coords=[hgtstd.time])
        flow_data["outputData"] = ai_mean
        self.output_data = flow_data

# if __name__ == "__main__":
#     from com.nriet.utils.GridDataUtils import GridDataUtils
#     monitorPath = "/nfsshare/cdbdata/data/NCEPRA/pressure/hgt/mon/"
#     monitorLtmPath = "/nfsshare/cdbdata/data/NCEPRA/pressure/hgt/ltm/"
#     stdPath = "/nfsshare/cdbdata//index/NCEPRA/pressure/hgt/ltm/std_"
#     tmp = GridDataUtils()
#     stdvar = "hgt_std"
#     climateYear = "1981-2010"
#     hgt = tmp.get_grid_mean_data(monitorPath, "mon", "201801", "201912",
#                                  "hgt", "0,360,20,90", "500")
#     hgtLtm = tmp.get_grid_ltm_data(monitorLtmPath, "mon", "201801", "201912",
#                                  "hgt", "0,360,20,90", "500",climateYear)
#     std  = tmp.get_grid_ltm_data(stdPath, "mon", "201801", "201912",
#                                  stdvar, "0,360,20,90", "500",climateYear)
#     dmp = StandardizationAnomalyModalPrjection()
#     nao  = dmp.execute(hgt,hgtLtm,std)
#     print(nao)
    #
    # stdvar = "hgt_std"
    #
    #
    # ds_std = xr.open_dataset(stdPath)
    #
    # std = ds_pat[stdvar]
    # print(std)

