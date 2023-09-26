#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/02/21
# @Author : Eldan
# @File : StationInfoData.py

import logging
import pandas as pd
import numpy as np
import xarray as xr
from com.nriet.algorithm.business.BusComponent import BusComponent
from com.nriet.utils.databaseConnection.GbaseHandler import GbaseHandler
from com.nriet.utils.config.ConfigUtils import look_for_gbase_connection_config

class StationInfoDataForGbase(BusComponent):
    def __init__(self, sub_local_params, algorithm_input_data):
        """
                :param sub_local_params:流程参数，算法运算返回结果
                :param algorithm_input_data:流程数据
                """
        # 初始化数据库连接
        self.gbase_handler = GbaseHandler(look_for_gbase_connection_config())
        # 地区编码
        self.areaCode = sub_local_params.get("areaCode")
        # 站点类型 国家站：1   代表站：2    区域站：3
        self.stationType = sub_local_params.get("stationType")
        self.output_data = None

    def execute(self):
        sql_tmplate = "select t.station_id,t.lat,t.lon from othe_zj_aws_station_tab t where t.station_type='%s' and t.area_code like '%s%%' "
        sql_sta = sql_tmplate%(self.stationType, self.areaCode)
        logging.info("查询站点信息的SQL==>" + sql_sta)
        sql_sta_result = self.gbase_handler.executeSql(sql_sta)
        # print(sql_sk_result)
        # 解析查询的结果数据封装成二维数组
        data_info_list = pd.DataFrame(list(sql_sta_result))
        stationInfo = np.array(data_info_list)
        station_list = stationInfo[:, 0]
        latlon_list =  stationInfo[:, 1:]
        # station_list  = [int(sl) for sl in station_list1]
        locs = ['lat', 'lon']
        stationInfoData = xr.DataArray(np.asarray(latlon_list,dtype=np.float32), coords=[station_list, locs], dims=['station', 'space'])
        out_data = {}
        out_data["outputData"] = stationInfoData
        self.output_data = out_data
