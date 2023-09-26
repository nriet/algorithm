#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/02/17
# @Author : Eldan
# @File : StationData.py


import os,json
import numpy as np
import pandas as pd
import xarray as xr
import logging
from com.nriet.algorithm.business.BusComponent import BusComponent
from com.nriet.utils import DateUtils
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import PARAMETER_VALUE_ERROR_CODE, DB_DATA_NOT_FOUND_ERROR_CODE
from com.nriet.utils.databaseConnection.GbaseHandler import GbaseHandler
from com.nriet.utils.config.ConfigUtils import look_for_gbase_connection_config



class StationDataForGbase(BusComponent):
    def __init__(self, sub_local_params, algorithm_input_data):
        """
                :param sub_local_params:流程参数，算法运算返回结果
                :param algorithm_input_data:流程数据
                """
        # 初始化数据库连接
        self.gbase_handler = GbaseHandler(look_for_gbase_connection_config())
        # 加载Gbase要素配置map
        basedir = os.path.abspath(os.path.dirname(__file__))
        basedir = basedir[0:basedir.rfind("/com/")]
        configPath = basedir + "/com/nriet/config/gbaseElementConfig.json"
        logging.info(configPath)
        with open(configPath, "r") as f:
            datastr = f.read()
        self.gbase_element_config = json.loads(datastr)
        # 时间尺度
        self.timeType = sub_local_params.get("timeType")
        # 起止时间点
        self.timeRanges = sub_local_params.get("timeRanges")
        # 要素编码
        self.elements = sub_local_params.get("elements")
        # 数据来源
        self.dataSource = sub_local_params.get("dataSource")
        # 单位转换
        self.unitConvert = sub_local_params.get("unitConvert")
        # 地区编码
        self.areaCode = sub_local_params.get("areaCode")
        # 站点类型 国家站：1   代表站：2    区域站：3
        self.stationType = sub_local_params.get("stationType")
        # 计算类型
        self.eleType = sub_local_params.get("eleType")
        # 要素时间维的降维方法（求平均：AVG  求和：SUM）
        self.statisticType = sub_local_params.get("statisticType")
        # 常年值
        self.ltm = sub_local_params.get("ltm", "1991-2020")
        # 站点信息
        self.stationInfoData = algorithm_input_data[0]["outputData"]

        # 算法输出
        self.output_data = None

    def execute(self):
        output_data = {}
        data_list = []
        # 获取实况数据
        if self.eleType.find("SK") != -1:
            # 获取数据
            res_data_mean = self.query_mean_data(self.timeType, str(self.timeRanges[0]), str(self.timeRanges[1]),
                                                 self.dataSource, self.elements, self.areaCode, self.stationType,
                                                 self.statisticType)
            # 封装返回的结果数据
            data_list.append(res_data_mean)

        # 获取常年值数据
        if self.eleType.find("LTM") != -1:
            # 获取数据
            res_data_ltm = self.query_ltm_data(self.timeType, str(self.timeRanges[0]), str(self.timeRanges[1]),
                                                self.dataSource, self.elements, self.areaCode, self.stationType,
                                                self.statisticType, self.ltm)
            # 封装返回的结果数据
            data_list.append(res_data_ltm)
        output_data["outputData"] = data_list
        self.output_data = output_data

    # 查询站点实况数据
    def query_mean_data(self, timeType, startTime, endTime, dataSource, elements, areaCode, stationType, statisticType):
        key = dataSource.upper() + "_" + elements.upper() + "_" + timeType.upper()
        logging.info(key)
        sta_list = self.stationInfoData.station.values.tolist()
        time_list = DateUtils.get_time_list([startTime, endTime], timeType)
        # 查询的要素的表字段
        tableField = self.gbase_element_config.get(key).get("tableField")
        # 各尺度的时间分组处理
        if timeType == "day":
            wantTimeStr = "SUBSTRING(t2.D_DATETIME, 1, 10) want_time"
        if timeType == "five":
            wantTimeStr = "CASE WHEN t2.V04003 BETWEEN 1 AND 5 THEN CONCAT( SUBSTRING(t2.D_DATETIME,1,7),'-01') WHEN t2.V04003 BETWEEN 6 AND 10 THEN CONCAT( SUBSTRING(t2.D_DATETIME,1,7),'-02') WHEN t2.V04003 BETWEEN 11 AND 15 THEN CONCAT( SUBSTRING(t2.D_DATETIME,1,7),'-03') WHEN t2.V04003 BETWEEN 16 AND 20 THEN CONCAT( SUBSTRING(t2.D_DATETIME,1,7),'-04') WHEN t2.V04003 BETWEEN 21 AND 25 THEN CONCAT( SUBSTRING(t2.D_DATETIME,1,7),'-05') WHEN t2.V04003 > 25 THEN CONCAT( SUBSTRING(t2.D_DATETIME,1,7),'-06') END want_time"
        if timeType == "ten":
            wantTimeStr = "CASE WHEN t2.V04003 BETWEEN 1 AND 10 THEN CONCAT( SUBSTRING(t2.D_DATETIME,1,7),'-01') WHEN t2.V04003 BETWEEN 11 AND 20 THEN CONCAT( SUBSTRING(t2.D_DATETIME,1,7),'-02') WHEN t2.V04003 > 20 THEN CONCAT( SUBSTRING(t2.D_DATETIME,1,7),'-03') END want_time"
        if timeType == "mon":
            wantTimeStr = "SUBSTRING(t2.D_DATETIME, 1, 7) want_time"
        if timeType == "season":
            wantTimeStr = "CASE WHEN t2.V04002 BETWEEN 3 AND 5 THEN CONCAT(t2.V04001, '-01') WHEN t2.V04002 BETWEEN 6 AND 8 THEN CONCAT(t2.V04001, '-02') WHEN t2.V04002 BETWEEN 9 AND 11 THEN CONCAT(t2.V04001, '-03') WHEN t2.V04002 BETWEEN 1 AND 2 THEN CONCAT(t2.V04001, '-04') WHEN t2.V04002 = 12 THEN CONCAT(t2.V04001 + 1, '-04') END want_time"
        if timeType == "year":
            wantTimeStr = "t2.V04001 want_time"
        # 查询的表名
        tableName = self.gbase_element_config.get(key).get("tableName")
        # 区域站点设置
        staConditionStr = "AND t1.station_type = '%s' AND t1.area_code like '%s%%'" % (stationType, areaCode)
        # 将其它尺度类型的日期转换成日
        # 日、候、旬 转换成日
        if timeType in ["day", "five", "ten"]:
            if timeType != "day":
                tempStartTime = DateUtils.dateToStr(
                    DateUtils.strToDate(DateUtils.otherTime2Day(startTime, timeType)[0], "%Y%m%d"), "%Y-%m-%d")
                tempEndTime = DateUtils.dateToStr(
                    DateUtils.strToDate(DateUtils.otherTime2Day(endTime, timeType)[-1], "%Y%m%d"), "%Y-%m-%d")
            else:
                tempStartTime = DateUtils.dateToStr(DateUtils.strToDate(startTime, "%Y%m%d"), "%Y-%m-%d")
                tempEndTime = DateUtils.dateToStr(DateUtils.strToDate(endTime, "%Y%m%d"), "%Y-%m-%d")
        #  月、季、年 转换成月
        if timeType in ["mon", "season", "year"]:
            if timeType != "mon":
                tempStartTime = DateUtils.dateToStr(
                    DateUtils.strToDate(DateUtils.otherTime2Month(startTime, timeType)[0], "%Y%m"), "%Y-%m")
                tempEndTime = DateUtils.dateToStr(
                    DateUtils.strToDate(DateUtils.otherTime2Month(endTime, timeType)[-1], "%Y%m"), "%Y-%m")
            else:
                tempStartTime = DateUtils.dateToStr(DateUtils.strToDate(startTime, "%Y%m"), "%Y-%m")
                tempEndTime = DateUtils.dateToStr(DateUtils.strToDate(endTime, "%Y%m"), "%Y-%m")
            tempStartTime = tempStartTime + "-01"
            tempEndTime = tempEndTime + "-01"
        # 按区域查询实况数据的sql模板
        sql_tmplate = "SELECT a.stationId, a.want_time D_DATETIME, %s(a.val) val FROM ( SELECT t2.V01301 stationId, t2.D_DATETIME, %s val, %s FROM %s t2, othe_zj_aws_station_tab t1 WHERE t1.station_id = t2.V01301 %s AND t2.D_DATETIME BETWEEN '%s' AND '%s' ) a WHERE a.val != 32766 GROUP BY a.want_time, a.stationId"
       # 针对降水 特殊处理
        if tableField == "V13305":
            tableField_s = "(case when t2.V13305=32700 then 0.1 else t2.V13305 end)"
        else:
            tableField_s = "t2." + tableField
        # 替换sql模板里的占位符(统计方法,表字段,各尺度的时间分组，表名，区域站点)，生成完整的SQL语句
        sql_str = sql_tmplate % (statisticType, tableField_s, wantTimeStr, tableName, staConditionStr, tempStartTime, tempEndTime)
        logging.info("从Gbase库查询实况的数据SQL==> " + sql_str)
        # 执行sql查询数据
        s1 = DateUtils.getTimeStamp()
        sql_result = self.gbase_handler.executeSql(sql_str)
        if len(sql_result) == 0:
            error_str = "当前SQL==>[%s]未查询到数据！" % sql_str
            raise AlgorithmException(response_code=DB_DATA_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        s2 = DateUtils.getTimeStamp()
        logging.info("          %s 耗时: %s ms" % ("从Gbase库查询实况的数据", str(s2 - s1)))

        # 解析查询的结果数据封装成二维数组
        sql_data = pd.DataFrame(list(sql_result))
        sqlData = np.array(sql_data)
        locs = ['station', 'time', 'val']
        sql_time_list = sqlData[:, 1]
        sqlData = xr.DataArray(sqlData, coords=[sql_time_list, locs], dims=['sql_time', 'space'])
        res_data1 = []
        nan_data = xr.DataArray(np.full((1, len(sta_list)), np.nan, dtype=np.float32), coords=[["999"], sta_list],
                                dims=['time', 'station'])
        res_data1.append(nan_data)
        for ii, tt in enumerate(time_list):
            tmpTime = DateUtils.time_format_en(tt, timeType, "-")
            if tmpTime in sql_time_list:
                # print(tmpTime)
                data_t = sqlData.sel(sql_time=tmpTime)
                if len(data_t.shape) == 1:
                    sta_t = list(data_t.sel(space='station').values)
                    val_t = list(map(float, [data_t.sel(space='val').values.tolist()]))
                    tmpdata = xr.DataArray(val_t, coords=[sta_t], dims=['station'])
                    # 将数组扩维
                    newdata = tmpdata.expand_dims("time")
                else:
                    sta_t = list(data_t.sel(space='station').values)
                    val_t = list(map(float, data_t.sel(space='val').values))
                    tmpdata = xr.DataArray(val_t, coords=[sta_t], dims=['station'])
                    # 将数组扩维
                    newdata = tmpdata.expand_dims("time")
            else:
                newdata = nan_data.copy()
            # 设置时间维度信息
            newdata["time"] = [tt]
            res_data1.append(newdata)
        # 将时间维合并
        res_data = xr.concat(res_data1, dim="time")
        res_data = res_data.sel(time=time_list)
        # logging.info(res_data.shape)
        # logging.info(res_data)
        s3 = DateUtils.getTimeStamp()
        logging.info("          %s 耗时: %s ms" % ("解析SQL查询的Gbase实况结果数据", str(s3 - s2)))
        return res_data

    # 查询站点常年值数据
    def query_ltm_data(self, timeType, startTime, endTime, dataSource, elements, areaCode, stationType, statisticType, ltm):
        key = dataSource.upper() + "_" + elements.upper() + "_" + timeType.upper()
        logging.info(key)
        sta_list = self.stationInfoData.station.values.tolist()
        time_list = DateUtils.get_time_list([startTime, endTime], timeType)
        # 查询的要素的表字段
        tableField = self.gbase_element_config.get(key).get("tableField")
        # 查询的表名
        tableName = self.gbase_element_config.get(key).get("ltmTableName")
        tableName = tableName % (ltm.split("-")[0], ltm.split("-")[1])
        # 区域站点设置
        staConditionStr = "AND t3.station_type = '%s' AND t3.area_code like '%s%%'" % (stationType, areaCode)
        # 按区域查询实况数据的sql模板
        sql_tmplate = "SELECT t1.V01301 stationId, t1.D_TIME D_DATETIME, t1.D_VALUE val FROM %s t1, othe_zj_aws_station_tab t3 WHERE t1.V01301 = t3.station_id AND t1.D_VALUE < 99999 %s AND t1.D_ELEMENT = '%s'"
        # 替换sql模板里的占位符(统计方法,表字段,各尺度的时间分组，表名，区域站点)，生成完整的SQL语句
        sql_str = sql_tmplate % (tableName, staConditionStr, tableField)
        logging.info("从Gbase库查询常年值的数据SQL==> " + sql_str)
        # 执行sql查询数据
        s1 = DateUtils.getTimeStamp()
        sql_result = self.gbase_handler.executeSql(sql_str)
        if len(sql_result) == 0:
            error_str = "当前SQL==>[%s]未查询到数据！" % sql_str
            raise AlgorithmException(response_code=DB_DATA_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        s2 = DateUtils.getTimeStamp()
        logging.info("          %s 耗时: %s ms" % ("从Gbase库查询常年值的数据", str(s2 - s1)))

        # 解析查询的结果数据封装成二维数组
        sql_data = pd.DataFrame(list(sql_result))
        sqlData = np.array(sql_data)
        locs = ['station', 'time', 'val']
        sql_time_list = sqlData[:, 1]
        sqlData = xr.DataArray(sqlData, coords=[sql_time_list, locs], dims=['sql_time', 'space'])
        res_data1 = []
        nan_data = xr.DataArray(np.full((1, len(sta_list)), np.nan, dtype=np.float32), coords=[["999"], sta_list],
                                dims=['time', 'station'])
        res_data1.append(nan_data)
        for ii, tt in enumerate(time_list):
            tmpTime = tt[4:]
            if tmpTime in sql_time_list:
                # print(tmpTime)
                data_t = sqlData.sel(sql_time=tmpTime)
                if len(data_t.shape) == 1:
                    sta_t = list(data_t.sel(space='station').values)
                    val_t = list(map(float, [data_t.sel(space='val').values.tolist()]))
                    tmpdata = xr.DataArray(val_t, coords=[sta_t], dims=['station'])
                    # 将数组扩维
                    newdata = tmpdata.expand_dims("time")
                else:
                    sta_t = list(data_t.sel(space='station').values)
                    val_t = list(map(float, data_t.sel(space='val').values))
                    tmpdata = xr.DataArray(val_t, coords=[sta_t], dims=['station'])
                    # 将数组扩维
                    newdata = tmpdata.expand_dims("time")
            else:
                newdata = nan_data.copy()
            # 设置时间维度信息
            newdata["time"] = [tt]
            res_data1.append(newdata)
        # 将时间维合并
        res_data = xr.concat(res_data1, dim="time")
        res_data = res_data.sel(time=time_list)
        # logging.info(res_data.shape)
        # logging.info(res_data)
        s3 = DateUtils.getTimeStamp()
        logging.info("          %s 耗时: %s ms" % ("解析SQL查询的Gbase常年值结果数据", str(s3 - s2)))
        return  res_data

