#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/02/21
# @Author : Eldan
# @File : NcToStation.py
import pandas as pd

from com.nriet.algorithm.business.BusComponent import BusComponent


class NcToStation(BusComponent):
    def __init__(self, sub_local_params, algorithm_input_data):
        """
                :param sub_local_params:流程参数，算法运算返回结果
                :param algorithm_input_data:流程数据
                """
        # 站点数据
        if isinstance(algorithm_input_data[0]["outputData"], list):
            self.inputData = algorithm_input_data[0]["outputData"][0]
        else:
            self.inputData = algorithm_input_data[0]["outputData"]
        # 站点信息
        self.inputData2 = algorithm_input_data[1]["outputData"]
        self.output_data = None

    def execute(self):
        out_data = {}
        zlat = self.inputData2.sel(space="lat")
        zlon = self.inputData2.sel(space="lon")
        g2s_data = self.inputData.interp(lat=zlat, lon=zlon)
        out_data["outputData"] = g2s_data
        self.output_data = out_data
