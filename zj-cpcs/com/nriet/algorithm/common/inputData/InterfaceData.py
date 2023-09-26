#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2019/11/12
# @Author : xulh
# @File : InterfaceData.py

import requests
import logging
from com.nriet.algorithm.common.inputData.InputDataComponent import InputDataComponent
from com.nriet.utils import fileUtils
from com.nriet.utils.GridDataSet import GridDataSet


class InterfaceDataAlgorithm(InputDataComponent):
    baseUrl = "http://10.40.16.38:8080/data"

    def __init__(self, proData, data_index):
        """
        :param proData:全局业务对象，包含流程参数，算法运算返回结果
        :param data_index:流程数据索引
        """
        self.sub_flow_param = proData.getParam("work_flow_params")[data_index]
        # 数据接口地址
        self.baseUrl = self.sub_flow_param["baseUrl"]
        # 数据类型
        self.dataCode = self.sub_flow_param["dataCode"]
        # 数据要素
        self.fcstEles = self.sub_flow_param["fcstEles"]
        self.element = self.sub_flow_param["elements"]
        # 时间范围
        self.times = proData.getparam("times")
        param_list = {}
        if (self.sub_flow_param["area"] != ""):
            # 数据区域
            param_list["area"] = self.sub_flow_param["area"]
        if (self.sub_flow_param["dataFormat"] != ""):
            # 数据格式
            param_list["dataFormat"] = self.sub_flow_param["dataFormat"]
        if (self.sub_flow_param["limitCnt"] != ""):
            # 数据限制条数
            param_list["limitCnt"] = self.sub_flow_param["limitCnt"]
        self.args = param_list

        self.nc_dateset = self.query_data_by_interface()  # todo 接口数据单独处理
        self.proData = proData
        logging.info(param_list)

    def execute(self):
        # self.proData["ncData"] = nc_dataset.get_ncData()
        nc_dataset = self.nc_dateset
        outputData = {}
        outputData[self.element] = nc_dataset.get_data()
        outputData["lat"] = nc_dataset.get_lat()
        outputData["lon"] = nc_dataset.get_lon()
        outputData["time"] = nc_dataset.get_time()
        self.proData.setParam("ncData", outputData)
        self.proData.setParam("jpData", {})
        return self.proData

    def query_data_by_interface(self):
        fcstEles = ','.join(self.fcstEles)
        times = ','.join(self.times)
        param = {"dataCode": self.dataCode, "fcstEles": fcstEles, "times": times}
        param.update(self.args)
        logging.info(param)
        startTime = fileUtils.getTimeStamp()
        data = requests.get(self.baseUrl + "/getGridData", params=param)
        nc_bytes = data.content
        logging.info("nc_bytes", nc_bytes)
        nc_dataset = GridDataSet(nc_bytes)
        endTime = fileUtils.getTimeStamp()
        logging.info("read NcData time:", endTime - startTime)
        return nc_dataset
