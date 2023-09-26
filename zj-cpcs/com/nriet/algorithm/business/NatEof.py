#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020-03-31
# @Author : chenbaiqing
# @File : NatEof.py
import logging
import numpy as np
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import PARAMETER_VALUE_MISSING_CODE
from com.nriet.algorithm.business.BusComponent import BusComponent


# NAT-EOF模态投影算法
class NatEof(BusComponent):
    def __init__(self, sub_local_params, algorithm_iuput_data):
        self.flow_data = algorithm_iuput_data
        # 去趋势后的NAT范围的海温距平数据 [time:int,lat:float,lon:float],float
        self.inputData = self.flow_data[0]["outputData"]
        # 模态空间分布数据 [lat:float,lon:float],float
        self.inputData2 = self.flow_data[1]["outputData"]
        self.bussSource = sub_local_params.get("bussSource")
        # NAT-EOF模态投影算法指数的值 [time:int],float
        self.output_data = None

    def execute(self):
        flow_data = {}
        # 缺测判断
        is_all_missing_value = True
        if not np.isnan(np.nanmean(self.inputData.values)):
            is_all_missing_value = False

        if is_all_missing_value:
            raise AlgorithmException(response_code=PARAMETER_VALUE_MISSING_CODE, response_msg='All Missing Values')
        isnan_tmp = self.inputData.mean(dim='lat').mean(dim='lon')
        # NAT的区域范围（0~60°N，280~360°E）
        # 1、对输入数据2在时间维进行维度扩展 *，得到[time:int, lat:float, lon:float]；
        # *维度扩展：将二维数据[lat:float, lon:float]
        # 扩展成三维[time:int, lat:float, lon:float]，扩展后不同时间维的数据相同
        input_data2_3D = self.inputData2.expand_dims(time=self.inputData['time'], axis=0)
        # 2、把去趋势后的NAT范围的海温距平乘以第一步结果，得到[time:int, lat:float, lon:float]；
        data3D = self.inputData * input_data2_3D.values
        # 3、对第2步结果进行经纬度区域内所有格点求和，得到[time:int]；
        data1D = data3D.sum(dim='lat').sum(dim='lon')
        # avg = np.nanmean(data1D)
        # std = np.std(data1D)
        # 4、对第3步结果进行标准化 *，得到NAT - EOF模态投影算法指数
        # *标准化方法 =（第3步结果 - 平均值） / 标准差
        # 平均值：12.7
        # 标准差：279.8
        if self.bussSource is None or self.bussSource == "":
            # avg = 12.7
            # std = 279.8
            avg = 19.570807
            std = 70.16012
        elif self.bussSource == "SSTV5_PDO":
            avg = -31.3957
            std = 136.878
        elif self.bussSource == "HADISST_PDO":
            avg = -97.2212
            std = 432.345
        elif self.bussSource == "GSSODS_PDO":
            avg = 36.1433
            std = 146.635
        elif self.bussSource == "CODAS_PDO":
            avg = -0.0067028
            std = 7153.79
        elif self.bussSource == "SST_NAT":
            avg = 29.0918
            std = 4069.96
        elif self.bussSource == "OISST_NAT":
            avg = 1.48362
            std = 228.169
        elif self.bussSource == "CMASST_NAT":
            avg = 0.0
            std = 61.7331
        elif self.bussSource == "CODAS_NAT":
            avg = -0.032117
            std = 4781.64
        elif self.bussSource == "SSTV5_NAT":
            avg = -23.20195
            std = 82.62172

        data1D = (data1D - avg) / std
        data1D[np.isnan(isnan_tmp)] = np.nan

        # 组装返回的DataArray
        flow_data["outputData"] = data1D
        flow_data["inputData"] = self.inputData
        flow_data["inputData2"] = self.inputData2
        self.output_data = flow_data


# if __name__ == "__main__":
#     # ===test===
#     temp = 10 * np.random.rand(3, 2, 2)
#     xy = np.random.rand(2, 2)
#     lat = [20.0, 30.0]
#     lon = [111.0, 122.0]
#     time = [0, 1, 2]
#
#     input_data = xa.DataArray(temp, coords=[time, lat, lon], dims=['time', 'lat', 'lon'])
#     input_data_2 = xa.DataArray(xy, coords=[lat, lon], dims=['lat', 'lon'])
#
#     flow_data1 = {}
#     flow_data1["outputData"] = input_data
#     flow_data2 = {}
#     flow_data2["outputData"] = input_data_2
#
#     fuc = NatEof(0, [flow_data1, flow_data2])
#     logging.info(fuc.output_data)
#     fuc.execute()
#     logging.info(fuc.output_data["outputData"])
