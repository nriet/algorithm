#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2019/10/25
# @Author : xulh
# @File : DIDecorator.py

import logging
import requests
import json


def sendDI(dataDate, dataType, proDuty, processLink, startTime, endTime, dataState, busiNessState, productNum, num,
           failFileList,
           taskErrorDetail):
    di = {}
    # decorator = {}
    # 业务系统
    # decorator["SYSTEM"] = "CIPAS"
    di["DATA_TYPE"] = dataType
    di["DATA_TYPE_1"] = ""
    di["TT"] = ""
    di["DATA_UPDATE_FLAG"] = ""
    di["IIiii"] = ""
    di["STATION_LEVEL"] = ""
    di["LONGITUDE"] = ""
    di["LATITUDE"] = ""
    di["HEIGHT"] = ""
    di["FILE_NAME"] = ""
    di["COUNTRY_NAME"] = ""
    di["DIST_NAME"] = ""
    di["ELE_NAME"] = ""
    di["RECEIVE"] = ""
    di["SEND"] = ""
    di["TRAN_TIME"] = ""
    di["DATA_TIME"] = dataDate
    di["PROD_DUTY"] = proDuty
    di["DATA_FLOW"] = ""
    di["PROD_SYS"] = "CIPAS"
    di["PROCESS_LINK"] = processLink
    di["PROCESS_START_TIME"] = startTime
    di["PROCESS_END_TIME"] = endTime
    di["FILE_NAME_O"] = ""
    di["FILE_NAME_N"] = ""
    di["FILE_SIZE"] = ""
    di["PROCESS_STATE"] = dataState
    di["BUSINESS_STATE"] = busiNessState
    di["RECORD_TIME"] = ""
    di["PRODUCT_NUM"] = productNum
    di["PRODUCT_PLAN_NUM"] = num
    di["FAIL_FILE_LIST"] = failFileList
    di["TASK_ERROR_DETAIL"] = taskErrorDetail
    di["DATA_RECORD_ID"] = ""

    # 资料业务日期
    # decorator["DATA_DATE"] = dataDate
    # 产品ID
    # decorator["DATA_TYPE"] = dataType
    # 产品时间类型
    # decorator["TIME_TYPE"] = timeType
    # 处理环节
    # decorator["PROCESS_LINK"] = processLink
    # 数据处理开始时间
    # decorator["START_TIME"] = startTime
    # 数据处理结束时间
    # decorator["END_TIME"] = endTime
    # 数据处理状态
    # decorator["DATA_STATE"] = dataState
    # 产品生成数
    # decorator["PRODUCT_NUM"] = productNum
    # 产品应生成数
    # decorator["NUM"] = num
    # 未生成文件列表
    # decorator["FAIL_FILE_LIST"] = failFileList
    # 任务异常状态说明
    # decorator["TASK_ERROR_DETAIL"] = taskErrorDetail
    # logging.info("CIPAS2.0 DI参数：", decorator)
    # url = "http://smart-view.nmic.cma/store/openapi/v2/logs/push_batch?apikey=e10adc3949ba59abbe56e057f2gg88dd"
    url = "http://127.0.0.1:29999/transfer"
    param = {"type": "RT.DPL.decorator", "name": "CIPAS2.0", "message": "123", "fields": di}
    logging.info(json.dumps(param))
    req = requests.post(url, data=json.dumps(param), headers={'Content-Type': 'application/json'})
    logging.info(req.json())  # 返回字节形式
    return req.json()

# url = "http://smart-view.nmic.cma/store/openapi/v2/logs/push_batch?apikey=e10adc3949ba59abbe56e057f2gg88dd"
# dataDate = tool.dateToStr(datetime.datetime.now(), "%Y-%m-%d")
# startTime = tool.dateToStr(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S")
# endTime = tool.dateToStr(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S")
# decorator = sendDI(dataDate, "PRO_20191026", "day", "CIPAS_PRODUCT", startTime, endTime, "1", "1", "1", "1", "1")
# param = {"type": "1", "name": "CIPAS2.0", "message": "123", "fields": decorator}
# logging.info(json.dumps(param))
# req = requests.post(url, data=json.dumps(param), headers={'Content-Type': 'application/json'})
# logging.info(req.json())  # 返回字节形式
