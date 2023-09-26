#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2019/10/21
# @Author : xulh
# @File : DimReduct.py

import logging
import xarray as xr
import numpy as np

from com.nriet.algorithm.business.BusComponent import BusComponent
from com.nriet.utils import DateUtils

class DimReduct(BusComponent):

    def __init__(self, sub_local_params, algorithm_input_data):
        """
        降维算法
        :param sub_local_params:流程参数，算法运算返回结果
        :param algorithm_input_data:流程数据
        """

        # 子流程算法执行产生的数据
        self.flow_data = algorithm_input_data[0]
        if isinstance(self.flow_data["outputData"], list):
            self.ncData = self.flow_data["outputData"][0].copy()
        else:
            self.ncData = self.flow_data["outputData"].copy()

        # 算法降维方式
        self.statTypes = sub_local_params["statTypes"]
        # 数据需要降维的维度
        self.statDims = sub_local_params["statDims"]
        # 数据要素
        self.elements = sub_local_params["elements"]
        self.statRanges = sub_local_params.get("statRanges")
        # self.dims = proData["ncData"]["dims"]
        self.timeType = sub_local_params.get("timeType")
        self.forecastPeriod = sub_local_params.get("forecastPeriod")
        self.output_data = None

    def execute(self):
        flow_data = {}
        # 根据statTypes计算数据
        # logging.info(self.ncData)
        outputData = self.ncData
        if str(outputData.dtype).find("<U") != -1:
            outputData.values = outputData.values.astype(float)
        for i, dim in enumerate(self.statDims):
            stat = self.statTypes[i]
            if self.statRanges[i] != ":":
                dim_data = self.ncData[dim]
                start_value, end_value = self.statRanges[i]
                sel_data = dim_data[(dim_data >= start_value) & (dim_data <= end_value)]
                outputData = outputData.sel({dim: sel_data})
            # 胡玉恒 20210408修改——增加跳过缺测值属性
            if stat == "avg":
                outputData = outputData.mean(dim=dim, skipna=True, keep_attrs=True)
            elif stat == "min":
                outputData = outputData.min(dim=dim, skipna=True, keep_attrs=True)
            elif stat == "max":
                outputData = outputData.max(dim=dim, skipna=True, keep_attrs=True)
            elif stat == "sum":
                # 降维求和修改 胡玉恒 20210413
                tmpdata = outputData.mean(dim=dim, skipna=True, keep_attrs=True)
                tmpdata = tmpdata.where(np.isnan(tmpdata), 1)
                outputData = outputData.sum(dim=dim, skipna=True, keep_attrs=True)
                outputData = outputData * tmpdata
                outputData.attrs = self.ncData.attrs

        # 截取预测部分的数据
        if self.forecastPeriod:
            sub_time_list = DateUtils.get_time_list(self.forecastPeriod, self.timeType)
            outputData = outputData.sel(time=sub_time_list)
        flow_data["outputData"] = outputData
        # flow_data["ncData"] = self.ncData
        self.output_data = flow_data
