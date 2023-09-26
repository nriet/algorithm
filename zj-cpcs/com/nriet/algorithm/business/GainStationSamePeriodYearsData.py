#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2023/06/14
# @Author : Shiys
# @File : GainStationSamePeriodYearsData.py

import numpy as np
import os, sys, json, ast
import xarray as xr
import pandas as pd
import logging, traceback
logger = logging.getLogger(__name__)
logger.root.setLevel(level=logging.INFO)
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
logging.info(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from com.nriet.algorithm.common.inputData.InputDataComponent import InputDataComponent
from com.nriet.utils import DateUtils
from com.nriet.config import PathConfig
from com.nriet.utils.result.ResponseResultUtils import build_response_dict
from com.nriet.config.ResponseCodeAndMsgEum import PARAMETER_VALUE_MISSING_CODE, \
    PARAMETER_VALUE_MISSING_MSG, CUSTOM_ERROR_CODE, CUSTOM_ERROR_MSG
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.utils.fileUtils import creatTxtFile
from com.nriet.utils.databaseConnection.GbaseHandler import GbaseHandler
from com.nriet.utils.config.ConfigUtils import look_for_gbase_connection_config


class GainStationSamePeriodYearsData(InputDataComponent):

    def __init__(self):
        # 初始化数据库连接
        self.gbase_handler = GbaseHandler(look_for_gbase_connection_config())

    def init_param(self, params):
        """
        初始化参数
        Args:
            params:

        Returns:

        """
        # 时间尺度
        self.timeType = params.get("timeType")
        # 预报开始时间
        self.startTime = params.get("startTime")
        # 预报结束时间
        self.endTime = params.get("endTime")
        # 要素
        self.element = params.get("element")
        # 要素
        self.eleType = params.get("eleType")
        # 要素
        self.ltm = params.get("ltm", "1991-2020")
        # 区域编码
        self.areaCode = params.get("areaCode")
        # 时序的开始年份
        self.startYear = params.get("startYear")
        # 时序图数据输出位置
        self.dataOutputPath = params.get("dataOutputPath")

    # 获取nc数据
    def execute(self, params):
        # 1.初始化参数
        self.init_param(params)
        result_dict = build_response_dict()
        endYear = self.endTime[0:4]
        #  获取历年同期的监测站点实况数据
        sql_sk = self.get_sameyears_sql(self.timeType,self.startTime,self.endTime,self.startYear,endYear,self.element,self.areaCode)
        print("历年同期的监测站点实况数据==>"+sql_sk)
        sql_sk_result = self.gbase_handler.executeSql(sql_sk)
        sk_data = {}
        for slr in sql_sk_result:
            sk_data[slr["YEAR"]] = float(slr["val"])

        #  获取历年同期的监测站点常年值数据
        sql_ltm = self.get_ltm_sql(self.timeType, self.startTime, self.endTime, self.ltm, self.element, self.areaCode)
        print("历年同期的监测站点常年值数据==>" + sql_ltm)
        sql_ltm_result = self.gbase_handler.executeSql(sql_ltm)
        ltm_data = float(sql_ltm_result[0]["val"])

        res_moni_data=[]
        res_time_list = DateUtils.get_time_list([self.startYear, endYear], "year")
        for tt in res_time_list:
            if tt in sk_data.keys():
                if self.eleType == "JP":
                    res_moni_data.append("{:.2f}".format(sk_data[tt]-ltm_data))
                else:
                    res_moni_data.append(sk_data[tt])
            else:
                res_moni_data.append("")

        res_data_dict={}
        res_data_dict["moni"] = res_moni_data
        res_data_dict["xAxisData"] = [DateUtils.time_format_en(tt,"year","-") for tt in res_time_list]
        res_data_dict["xAxisDataCh"] = [DateUtils.time_format_ch(tt,"year") for tt in res_time_list]
        if self.startTime == self.endTime:
            res_data_dict["subTitle"] = self.startYear+"年-"+endYear+"年 "+DateUtils.time_format_ch(self.endTime,self.timeType)[6:]
        else:
            res_data_dict["subTitle"] = self.startYear+"年-"+endYear+"年 "+DateUtils.time_format_ch(self.startTime,self.timeType)[6:]+"-"+DateUtils.time_format_ch(self.endTime,self.timeType)[6:]
        creatTxtFile(os.path.dirname(self.dataOutputPath) + "/", os.path.basename(self.dataOutputPath), json.dumps(res_data_dict, ensure_ascii=False))
        result_dict["data"] = res_data_dict
        return result_dict

    def get_sameyears_sql(self, time_type, startTime, endTime, startYear, endYear, element, area_code):
        # 根据时间尺度，设置需要查询的表名称
        if time_type == "day":
            tableName = "SURF_WEA_ZJ_MUL_DAY_TAB"
        if time_type == "mon":
            tableName = "SURF_WEA_ZJ_MUL_MON_TAB"
        # 根据要素，设置需要查询的表字段以及对时间的统计方式
        if element == "AVGT":
            tableField = "V12001_701"
            staticStr = "AVG"
        # 根据时间及尺度，设置历年同期的时间查询条件及年份分组
        case_list = []
        time_cond_list = []
        year_list = DateUtils.get_time_list([startYear,endYear],"year")
        startMd = startTime[4:]
        endMd = endTime[4:]
        case_list.append("CASE")
        for year in year_list[::-1]:
            tmp_start_time, tmp_end_time = self.getProdTimes(year,startMd,endMd)

            if time_type == "day":
                tmp_start_time = DateUtils.time_format_en(tmp_start_time,time_type,"-")
                tmp_end_time = DateUtils.time_format_en(tmp_end_time,time_type,"-")

            if time_type == "mon":
                tmp_start_time = DateUtils.time_format_en(tmp_start_time,time_type,"-")+"-01"
                tmp_end_time = DateUtils.time_format_en(tmp_end_time,time_type,"-")+"-01"

            case_list.append("WHEN t1.D_DATETIME BETWEEN '"+tmp_start_time+"' AND '"+tmp_end_time+"' THEN '"+year+"'")
            time_cond_list.append(" ( t1.D_DATETIME BETWEEN '"+tmp_start_time+"' AND '"+tmp_end_time+"' ) ")
        case_list.append("END")

        caseStr = " ".join(case_list)
        timeCondStr = "OR".join(time_cond_list)

        # caseStr = "CASE WHEN t1.D_DATETIME BETWEEN '2022-12-01' AND '2023-01-01' THEN '2023' WHEN t1.D_DATETIME BETWEEN '2021-12-01' AND '2022-01-01' THEN '2022' WHEN t1.D_DATETIME BETWEEN '2020-12-01' AND '2021-01-01' THEN '2021' WHEN t1.D_DATETIME BETWEEN '2019-12-01' AND '2020-01-01' THEN '2020' END"
        # timeCondStr = "( t1.D_DATETIME BETWEEN '2022-12-01' AND '2023-01-01' ) OR ( t1.D_DATETIME BETWEEN '2021-12-01' AND '2022-01-01' ) OR ( t1.D_DATETIME BETWEEN '2020-12-01' AND '2021-01-01' ) OR ( t1.D_DATETIME BETWEEN '2019-12-01' AND '2020-01-01' )"


        sql_tmplate ="SELECT A.YEAR, ROUND(AVG(A.val), 2) val FROM( SELECT t1.V01301, %s YEAR, %s(t1.%s) val FROM %s t1, othe_zj_aws_station_tab t2 WHERE t1.V01301 = t2.station_id AND t1.%s < 99999 AND t2.station_type = '2' AND t2.area_code LIKE '%s%%' AND ( %s ) GROUP BY YEAR, t1.V01301 ) A GROUP BY A.YEAR"
        sql_str = sql_tmplate%(caseStr,staticStr,tableField,tableName,tableField,area_code,timeCondStr)
        return sql_str

    def get_ltm_sql(self, time_type, startTime, endTime, ltm, element, area_code):
        # 根据时间尺度，设置需要查询的表名称
        if time_type == "day":
            tableName = "SURF_CLI_ZJ_MDAY_%s_%s_TAB" % (ltm.split("-")[0], ltm.split("-")[1])
        if time_type == "mon":
            tableName = "SURF_CLI_ZJ_MMON_%s_%s_TAB" % (ltm.split("-")[0], ltm.split("-")[1])
        # 根据要素，设置需要查询的表字段以及对时间的统计方式
        if element == "AVGT":
            tableField = "V12001_701"
            staticStr = "AVG"
        # 根据时间及尺度，设置历年同期的时间查询条件
        startMd = startTime[4:]
        endMd = endTime[4:]
        if startMd > endMd:
            timeCondStr = "( t1.D_TIME BETWEEN '"+startMd+"' and '1231' ) or ( t1.D_TIME BETWEEN '0101' and '"+endMd+"' )"
        else:
            timeCondStr = "t1.D_TIME BETWEEN '"+startMd+"' and '"+endMd+"'"

        sql_tmplate ="SELECT ROUND(AVG(A.val), 2) val FROM ( SELECT t1.V01301 stationId, %s(t1.D_VALUE) val FROM %s t1, othe_zj_aws_station_tab t2 WHERE t1.V01301 = t2.station_id AND t1.D_ELEMENT = '%s' AND t2.station_type = '2' AND t2.area_code LIKE '%s%%' AND ( %s ) GROUP BY t1.V01301 ) A"
        sql_str = sql_tmplate%(staticStr, tableName, tableField, area_code,timeCondStr)
        return sql_str

    def getProdTimes(self,tmpYear, start_md, end_md):
        tmp_smd = float(str(start_md).replace("-", ""))
        tmp_emd = float(str(end_md).replace("-", ""))
        # 判断是否跨年
        if tmp_emd >= tmp_smd:
            tmpSatrtTime = str(tmpYear) + str(start_md).replace("-", "")
        else:
            tmpSatrtTime = str(int(tmpYear) - 1) + str(start_md).replace("-", "")
        tmpEndTime = str(tmpYear) + str(end_md).replace("-", "")
        return tmpSatrtTime, tmpEndTime


if __name__ == "__main__":
    try:
        t1 = DateUtils.getTimeStamp()
        # 获取页面传参
        page_params = ast.literal_eval(sys.argv[1])
        # page_params = {"timeType": "day",
        #                "startYear": "2013",
        #                "startTime": "20230501",
        #                "endTime": "20230520",
        #                "dataSource": "CSOD",
        #                # "dataSource": "MODES_MME,MODES_CFS2,MODES_EC5,MODES_NCC,MODES_UKMO5,MODES_JMA3,CMMEV2_MME,MODES_WMME,SEDES,ZJPPC",
        #                "dataOutputPath": "/nfsshare/cdbdata/data/dry_data/test_more.json",
        #                "areaCode": "3305",
        #                "eleType": "SK",
        #                "element": "AVGT"}
        gs2gd = GainStationSamePeriodYearsData()
        result_dict = gs2gd.execute(page_params)
        t2 = DateUtils.getTimeStamp()
        logging.info("获取模式表格数据总耗时: %s ms" % (str(t2 - t1)))
    except AlgorithmException as ae:
        logging.error(traceback.format_exc())
        result_dict = ae.__str__()
    except IndentationError as ie:
        logging.error(traceback.format_exc())
        result_dict = build_response_dict(response_code=PARAMETER_VALUE_MISSING_CODE,
                                          response_msg=PARAMETER_VALUE_MISSING_MSG % "methodName")
    except Exception as e:
        logging.error(traceback.format_exc())
        result_dict = build_response_dict(response_code=CUSTOM_ERROR_CODE, response_msg=CUSTOM_ERROR_MSG)
    # 输出结果信息
    print(json.dumps(result_dict, ensure_ascii=False))
    # logging.info(json.dumps(result_dict, ensure_ascii=False))
