#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2021-08-11
# @Author : hyh
# @File : PolorRegionOscillation.py
import numpy as np
from com.nriet.algorithm.business.BusComponent import BusComponent
import xarray as xr
import math
# import metpy.calc as mc
# from metpy.units import units
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import PARAMETER_VALUE_ERROR_CODE,PARAMETER_VALUE_ERROR_MSG

# 极地涛动计算
class PolarRegionOscillation(BusComponent):

    def __init__(self, sub_local_params, algorithm_input_data):
        self.sub_local_params = sub_local_params
        self.inputData = algorithm_input_data[0]["outputData"] # 1000hPa位势高度距平数据（time,lat,lon）
        self.patternPath = sub_local_params["patternPath"]
        # self.areaCode = sub_local_params["areaCode"]
        self.output_data = None

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
            areas[l,...] = R*R*(gridDistance*math.pi/180.)*\
                   (math.sin((lat+0.5*gridDistance)*math.pi/180.)-math.sin((lat-0.5*gridDistance)*math.pi/180.))
        areas = xr.DataArray(areas, dims=["lat","lon"], coords=[data.lat,data.lon])
        return areas


    def execute(self):
        flow_data = {}
        ds_pattern = xr.open_dataset(self.patternPath)
        # pattern_data = ds_pattern['eof']
        pattern_data = ds_pattern['ao_pat']
        if self.areaCode == "AO":
            # 读取模态数据
            pattern_data = pattern_data[0,:,:]
        elif self.areaCode == "AAO":
            pattern_data = pattern_data[1,:,:]
        else:
            raise AlgorithmException(response_code=PARAMETER_VALUE_ERROR_CODE, response_msg=PARAMETER_VALUE_ERROR_MSG)
        pattern_data_3d = pattern_data.expand_dims(time=self.inputData['time'], axis=0)
        area_data = self._BallArea(self.inputData)
        aarea = area_data.sum()
        area_data_3d = area_data.expand_dims(time=self.inputData['time'], axis=0)
        hgt_area_w = self.inputData * area_data_3d
        pat2 = pattern_data*pattern_data
        patvar = math.sqrt(pat2.mean(dim='lat').mean(dim='lon'))
        aoindex = ((hgt_area_w*pattern_data_3d.values).sum(dim='lat').sum(dim='lon')/aarea)/patvar
        flow_data["outputData"] = aoindex
        self.output_data = flow_data

# if __name__ == "__main__":
#     # ===test===
#     sub_local_params1 = {
# 					"bussId":"11",
# 					"elements":"hgt",
# 					"timeType":"day",
# 					"timeRanges":[20210101,20210131],
# 					"levels":"700,700",
# 					"regions":"0,360,-90,-20",
# 					"dataInputPaths":"/nfsshare/cdbdata/data/NCEPRA/pressure/hgt/day/",
# 					"ltmDataInputPaths":"/nfsshare/cdbdata/data/NCEPRA/pressure/hgt/ltm/",
# 					"ltm":"1981-2010",
# 					"unitConvert":""
# 				}
#     algorithm_input_data1 = []
#     fuc1 = NcData(sub_local_params1,algorithm_input_data1)
#     fuc1.execute()
#
#     jpData = fuc1.output_data['outputData'][0] - fuc1.output_data['outputData'][1]
#     jpData = jpData[:,0,:,:]
#     jpData = {"outputData": jpData}
#
#
#
#     algorithm_input_data = []
#     algorithm_input_data.append(jpData)
#     sub_local_params = {"patternPath":"/mnt/wmfs/data/NCEPRA/pressure/cli_pattern/cli_ao_pattern.nc","areaCode":"AAO"}
#
#     fuc = PolorRegionOscillation(sub_local_params,algorithm_input_data)
#     # print(fuc.output_data)
#     fuc.execute()
#     print(fuc.output_data["outputData"])