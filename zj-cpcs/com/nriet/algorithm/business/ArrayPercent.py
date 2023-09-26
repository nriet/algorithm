#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020-02-21
# @Author : JiangP
# @File : ArrayPercent.py
import numpy as np
from com.nriet.algorithm.business.BusComponent import BusComponent
import xarray as xr

# 数组求距平百分率运算
class ArrayPercent(BusComponent):

    def __init__(self, sub_local_params, algorithm_input_data):
        if len(algorithm_input_data) == 2:
            self.inputData = algorithm_input_data[0]["outputData"]
            self.inputData2 = algorithm_input_data[1]["outputData"]
            self.flag = False
        else:
            self.flow_data = algorithm_input_data[0]
            self.inputData = self.flow_data["outputData"][0]
            self.inputData2 = self.flow_data["outputData"][1]

        self.sub_local_params = sub_local_params
        self.output_data = None

    def execute(self):
        flow_data = {}
        if self.inputData.shape != self.inputData2.shape:
            return None
        self.inputData2 = np.where(self.inputData2 == 0, 0.1, self.inputData2)
        flow_data["outputData"] =(self.inputData - self.inputData2)*100/self.inputData2
        # 距平百分率计算后数据的属性与源数据保持一致
        flow_data["outputData"].attrs = self.inputData.attrs
        self.output_data = flow_data

# if __name__ == '__main__':
#     algorithm_input_data = []
#     input_data = [0.1, 0.2, 0.3, 0.4, 0.5]
#     input_data2 = [0, 3.1, 0, 5.1, 6.1]
#     dims = ["time"]
#     input_data = xr.DataArray(input_data, dims=dims)
#     input_data2 = xr.DataArray(input_data2, dims=dims)
#     out_put_data = {"outputData": input_data}
#     out_put_data2 = {"outputData": input_data2}
#     algorithm_input_data.append(out_put_data)
#     algorithm_input_data.append(out_put_data2)
#     sub_local_params = {}
#     ar = ArrayPercent(sub_local_params,algorithm_input_data)
#     ar.execute()