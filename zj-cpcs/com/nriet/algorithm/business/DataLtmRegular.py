#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/07/09
# @Author : Shiys
# @File : DataLtmRegular.py

import json
import os,logging
from com.nriet.algorithm.business.BusComponent import BusComponent
from com.nriet.utils.DataLtmRegularUtils import DataLtmRegularUtils
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import FILE_NOT_FOUND_ERROR_CODE,PARAMETER_VALUE_ERROR_CODE


class DataLtmRegular(BusComponent):
    def __init__(self, sub_local_params, algorithm_iuput_data):
        self.DLRU = DataLtmRegularUtils()
  
        basedir = os.path.abspath(os.path.dirname(__file__))
        basedir = basedir[0:basedir.rfind("/com/")]
        configPath = basedir+"/com/nriet/config/dataLtmRegularConfig.json"
        logging.info(configPath)

        with open(configPath, "r") as f:
            datastr = f.read()
            # logging.info(datastr)
        self.data_config = json.loads(datastr)
        self.timeType = sub_local_params.get("timeType")
        self.timeRanges = sub_local_params.get("timeRanges")
        self.elements = sub_local_params.get("elements")
        self.dataSources = sub_local_params.get("dataSources")
        self.levelType = sub_local_params.get("levelType")
        self.output_data = None

    def execute(self):
        # 获取规整数据的起止时间
        startTime, endTime = [time for time in self.timeRanges]
        timeType =  self.timeType
        keys = [self.dataSources, self.elements, self.timeType]
        # 需要高度层属性区分KEY
        if self.levelType:
            keys.insert(1, self.levelType)
        key = ".".join(keys).upper()
        elementDataConfig = self.data_config.get(key)
        if elementDataConfig is None:
            error_str = " According to the key[%s], no relevant data was found to regularize the configuration!" % key
            raise AlgorithmException(response_code=PARAMETER_VALUE_ERROR_CODE, response_msg=error_str)
        # regular_day_ltm_data
        if  elementDataConfig.get("method") == "regular_day_ltm_data":
            self.DLRU.regular_day_ltm_data(elementDataConfig, timeType, startTime, endTime)
        # regular_other_ltm_data
        if elementDataConfig.get("method") == "regular_other_ltm_data":
            self.DLRU.regular_other_ltm_data(elementDataConfig, timeType, startTime, endTime)
        # regular_day_ltm_data_hd
        if elementDataConfig.get("method") == "regular_day_ltm_data_hd":
            self.DLRU.regular_day_ltm_data_hd(elementDataConfig, timeType, startTime, endTime)
        # regular_other_ltm_data_hd
        if  elementDataConfig.get("method") == "regular_other_ltm_data_hd":
            self.DLRU.regular_other_ltm_data_hd(elementDataConfig, timeType, startTime, endTime)
        # regular_bcccsm13m_ltm_data
        if elementDataConfig.get("method") == "regular_bcccsm13m_ltm_data":
            self.DLRU.regular_bcccsm13m_ltm_data(elementDataConfig, timeType, startTime, endTime)