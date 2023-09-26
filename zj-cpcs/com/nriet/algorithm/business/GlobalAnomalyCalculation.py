#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020-02-24
# @Author : chenmeng
# @File : GlobalAnomalyCalculation.py
from com.nriet.algorithm.business.BusComponent import BusComponent
import xarray as xr
import numpy as np
import logging

# 全球距平均值去趋势计算
class GlobalAnomalyCalculation(BusComponent):
    def __init__(self, sub_local_params, algorithm_iuput_data):
        self.flow_data = algorithm_iuput_data
        self.inputData = self.flow_data[0]["outputData"]
        self.inputData2 = self.flow_data[1]["outputData"]
        self.output_data = None

    def execute(self):
        flow_data = {}
        region_data = self.inputData
        # 维的名称
        dimName = region_data.dims
        # 维的大小
        shape = region_data.shape
        global_data = self.inputData2
        # 对全球数据除第一维以外的维求平均
        time_data = global_data.mean(dim=dimName[1:])
        # 设置需要扩展维的名称、大小和位置
        dim = {}
        axis = []
        for dn in dimName:
            if dn != dimName[0]:
                dim[dn] = shape[dimName.index(dn)]
                axis.append(dimName.index(dn))
        # 对平均后的全球数据进行扩维
        expand_data = time_data.expand_dims(dim, axis)
        # 去趋势计算
        region_data.values = region_data.values - expand_data.values
        flow_data["outputData"] = region_data
        self.output_data = flow_data

if __name__ == '__main__':
    algorithm_input_data = []
    input_data = np.arange(27).reshape(3,3,3)
    logging.info("input_data:",input_data)
    input_data2 = np.arange(-27,0).reshape(3, 3, 3)
    logging.info("input_data2:", input_data2)
    dims = ["time","lat","lon"]
    input_data = xr.DataArray(input_data,dims=dims)
    input_data2 = xr.DataArray(input_data2,dims=dims)

    out_put_data = {"outputData":input_data}
    out_put_data2 = {"outputData": input_data2}
    algorithm_input_data.append(out_put_data)
    algorithm_input_data.append(out_put_data2)

    sub_local_params = {}
    gc = GlobalAnomalyCalculation(sub_local_params,algorithm_input_data)
    gc.execute()
    logging.info(gc.output_data)

