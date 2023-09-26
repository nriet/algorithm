#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/07/09
# @Author : Shiys
# @File : DataMeanRegular.py

import json
import logging
import os

from com.nriet.algorithm.business.BusComponent import BusComponent
from com.nriet.config.ResponseCodeAndMsgEum import PARAMETER_VALUE_ERROR_CODE
from com.nriet.utils.DataMeanRegularUtils import DataMeanRegularUtils
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException


class DataMeanRegular(BusComponent):
    def __init__(self, sub_local_params, algorithm_iuput_data):
        self.dmrUtils = DataMeanRegularUtils()

        basedir = os.path.abspath(os.path.dirname(__file__))
        basedir = basedir[0:basedir.rfind("/com/")]
        configPath = basedir + "/com/nriet/config/dataRegularConfig.json"
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

        key = self.dataSources + "." + self.elements + "." + self.timeType
        # 需要高度层属性区分KEY
        if self.levelType:
            key = self.dataSources + "." + self.levelType + "." + self.elements + "." + self.timeType
        elementDataConfig = self.data_config.get(key.upper())
        if elementDataConfig is None:
            error_str = " According to the key[%s], no relevant data was found to regularize the configuration!" % key.upper()
            raise AlgorithmException(response_code=PARAMETER_VALUE_ERROR_CODE, response_msg=error_str)
        # regular_day_raw_data_single
        if elementDataConfig.get("method") == "regular_day_raw_data_single":
            result_dict = self.dmrUtils.regular_day_raw_data_single(elementDataConfig, startTime, endTime)
        # regular_day_raw_data_single_tmp
        if elementDataConfig.get("method") == "regular_day_raw_data_single_tmp":
            result_dict = self.dmrUtils.regular_day_raw_data_single_tmp(elementDataConfig, startTime, endTime)
        # regular_day_raw_data_single_tmin_0cm
        if elementDataConfig.get("method") == "regular_day_raw_data_single_tmin_0cm":
            result_dict = self.dmrUtils.regular_day_raw_data_single_tmin_0cm(elementDataConfig, startTime, endTime)
        # regular_day_raw_data_multiple
        if elementDataConfig.get("method") == "regular_day_raw_data_multiple":
            result_dict = self.dmrUtils.regular_day_raw_data_multiple(elementDataConfig, startTime, endTime)
        # regular_day_raw_data_multiple_hms
        if elementDataConfig.get('method') == "regular_day_raw_data_multiple_hms":
            result_dict = self.dmrUtils.regular_day_raw_data_multiple_hms(elementDataConfig, startTime, endTime)
        # regular_day_raw_data_multiple_hpa
        if elementDataConfig.get('method') == "regular_day_raw_data_multiple_hpa":
            result_dict = self.dmrUtils.regular_day_raw_data_multiple_hpa(elementDataConfig, startTime, endTime)
        # regular_day_raw_data_from_mon  #根据按月存放的日数据规整日数据
        if elementDataConfig.get("method") == "regular_day_raw_data_from_mon":
            result_dict = self.dmrUtils.regular_day_raw_data_from_mon(elementDataConfig, startTime, endTime)
        # regular_five_data
        if elementDataConfig.get("method") == "regular_five_data":
            result_dict = self.dmrUtils.regular_five_data(elementDataConfig, startTime, endTime)
        # regular_ten_data
        if elementDataConfig.get("method") == "regular_ten_data":
            result_dict = self.dmrUtils.regular_ten_data(elementDataConfig, startTime, endTime)
        # regular_mon_raw_data_multiple
        if elementDataConfig.get("method") == "regular_mon_raw_data_multiple":
            result_dict = self.dmrUtils.regular_mon_raw_data_multiple(elementDataConfig, startTime, endTime)
        # regular_mon_data
        if elementDataConfig.get("method") == "regular_mon_data":
            result_dict = self.dmrUtils.regular_mon_data(elementDataConfig, startTime, endTime)
        # regular_season_data
        if elementDataConfig.get("method") == "regular_season_data":
            result_dict = self.dmrUtils.regular_season_data(elementDataConfig, startTime, endTime)
        # regular_year_data
        if elementDataConfig.get("method") == "regular_year_data":
            result_dict = self.dmrUtils.regular_year_data(elementDataConfig, startTime, endTime)
        # regular_day_raw_data_single_u10v10
        if elementDataConfig.get("method") == "regular_day_raw_data_single_u10v10":
            result_dict = self.dmrUtils.regular_day_raw_data_single_u10v10(elementDataConfig, startTime, endTime)
        # regular_day_raw_data_single_sic
        if elementDataConfig.get("method") == "regular_day_raw_data_single_sic":
            result_dict = self.dmrUtils.regular_day_raw_data_single_sic(elementDataConfig, startTime, endTime)
        # regular_month_raw_data_single
        if elementDataConfig.get("method") == "regular_month_raw_data_single":
            result_dict = self.dmrUtils.regular_month_raw_data_single(elementDataConfig, startTime, endTime)
        # regular_station_five_data
        if elementDataConfig.get("method") == "regular_station_five_data":
            result_dict = self.dmrUtils.regular_station_five_data(elementDataConfig, startTime, endTime)
        # regular_station_ten_data
        if elementDataConfig.get("method") == "regular_station_ten_data":
            result_dict = self.dmrUtils.regular_station_ten_data(elementDataConfig, startTime, endTime)
        # regular_station_mon_data
        if elementDataConfig.get("method") == "regular_station_mon_data":
            result_dict = self.dmrUtils.regular_station_mon_data(elementDataConfig, startTime, endTime)
        # regular_station_season_data
        if elementDataConfig.get("method") == "regular_station_season_data":
            result_dict = self.dmrUtils.regular_station_season_data(elementDataConfig, startTime, endTime)
        # regular_station_year_data
        if elementDataConfig.get("method") == "regular_station_year_data":
            result_dict = self.dmrUtils.regular_station_year_data(elementDataConfig, startTime, endTime)
        # regular_fy_day_data
        if elementDataConfig.get("method") == "regular_day_raw_data_fy_tbb":
            result_dict = self.dmrUtils.regular_day_raw_data_fy_tbb(elementDataConfig, startTime, endTime)
        if elementDataConfig.get("method") == "regular_day_raw_data_fy_qpe":
            result_dict = self.dmrUtils.regular_day_raw_data_fy_qpe(elementDataConfig, startTime, endTime)
        if elementDataConfig.get("method") == "regular_day_raw_data_fy_amv":
            result_dict = self.dmrUtils.regular_day_raw_data_fy_amv(elementDataConfig, startTime, endTime)
        if elementDataConfig.get("method") == "regular_hour_data":
            result_dict = self.dmrUtils.regular_hour_data(elementDataConfig, startTime, endTime)
        if elementDataConfig.get("method") == "regular_hour_data_history":
            result_dict = self.dmrUtils.regular_hour_data_history(elementDataConfig, startTime, endTime)
        if elementDataConfig.get("method") == "regular_hour2day_data":
            result_dict = self.dmrUtils.regular_hour2day_data(elementDataConfig, startTime, endTime)
        if elementDataConfig.get("method") == "regular_hour_data_rh":
            result_dict = self.dmrUtils.regular_hour_data_rh(elementDataConfig, startTime, endTime)
        if elementDataConfig.get("method") == "regular_hour_data_bj":
            result_dict = self.dmrUtils.regular_hour_data_bj(elementDataConfig, startTime, endTime)
        if elementDataConfig.get("method") == "regular_reduce_dim":
            result_dict = self.dmrUtils.regular_reduce_dim(elementDataConfig, startTime, endTime)
        # cpsv3月尺度规整
        if elementDataConfig.get("method") == "regular_bcccpsv3_mon_data":
            result_dict = self.dmrUtils.regular_bcccpsv3_mon_data(elementDataConfig, startTime, endTime)
        # cpsv3日尺度规整
        if elementDataConfig.get("method") == "regular_bcccpsv3_day_data":
            result_dict = self.dmrUtils.regular_bcccpsv3_day_data(elementDataConfig, startTime, endTime)
        # modes单模式规整
        if elementDataConfig.get("method") == "regular_modes_data":
            result_dict = self.dmrUtils.regular_modes_data(elementDataConfig, startTime, endTime)
        # modes单模式气候态规整（一次性规整）
        if elementDataConfig.get("method") == "regular_modes_ltm_data":
            result_dict = self.dmrUtils.regular_modes_ltm_data(elementDataConfig, startTime, endTime)
        # modes多模式集合平均规整
        if elementDataConfig.get("method") == "regular_modes_mme_data":
            result_dict = self.dmrUtils.regular_modes_mme_data(elementDataConfig, startTime, endTime)
        # modes多模式集合平均气候态规整（一次性规整）
        if elementDataConfig.get("method") == "regular_modes_mme_ltm_data":
            result_dict = self.dmrUtils.regular_modes_mme_ltm_data(elementDataConfig, startTime, endTime)

        # logging.info(result_dict)
        return result_dict

#
#         pass
# sub_local_params1 ={}
# sub_local_params1["timeType"] = "mon"
# sub_local_params1["timeRanges"] = [202007,202007]
# sub_local_params1["elements"] = "uwnd"
# sub_local_params1["dataSources"] = "CRA"
# algorithm_iuput_data1 = []
# dmr = DataMeanRegular(sub_local_params1,"")
# dmr.execute()
