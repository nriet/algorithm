#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/02/09
# @Author : xulh
# @File : MysqlDBDataOutput.py
import uuid
import numpy as np
import xarray as xr
from com.nriet.algorithm.common.outputData.OutputDataComponent import OutputDataComponent
from com.nriet.config.MySQLConfig import config
from com.nriet.utils.MathUtils import formatting_data
from com.nriet.utils.databaseConnection.MySQLHandler import MysqldbHelper
from com.nriet.utils import DateUtils
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import PARAMETER_VALUE_MISSING_CODE
import logging
import importlib,sys

importlib.reload(sys)
#sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
class MysqlDBDataOutput(OutputDataComponent):

    def __init__(self, sub_local_params, algorithm_input_data):
        """
        :param sub_local_params:流程参数，算法运算返回结果
        :param algorithm_input_data:流程数据
        """
        # self.flow_data = algorithm_input_data[0]
        if len(algorithm_input_data) > 1:
            self.convert_data(algorithm_input_data)
        else:
            self.flow_data = algorithm_input_data[0]["outputData"]
        self.productId = sub_local_params.get("productId")
        self.productName = sub_local_params.get("productName")
        self.productPath = sub_local_params.get("productPath")
        self.time_ranges = sub_local_params.get("timeRanges")
        self.timeType = sub_local_params.get("timeType")
        self.forecastTime = sub_local_params.get("reportingTime")
        self.forecastPeriod = sub_local_params.get("forecastPeriod")
        self.indexTitle = sub_local_params.get("indexTitle")

        self.format = sub_local_params.get("format")
        self.saveType = sub_local_params.get("saveType")
        self.output_data = None

    def execute(self):

        if self.productPath:
            productType, orgName, busType, busId, element, dataSource, areaCode, timeType, level = self.productPath.split(
                "_")
        else:
            if self.productId:
                productType, orgName, busType, busId, element, dataSource, areaCode, timeType, level = self.productId.split(
                    "_")[0:9]
            else:
                raise AlgorithmException(response_code=PARAMETER_VALUE_MISSING_CODE,response_msg='Lack of productId!')
        # 初始化打开数据库连接
        mydb = MysqldbHelper(config)
        try:
            propertyId = str(uuid.uuid1())

            product_params = {
                "productId": str(self.productId),
                "productName": str(self.productName),
                "orgName": str(orgName)
            }
            cond_dict = {
                "productId": str(self.productId)
            }
            result = mydb.select("T_AUTO_PRODUCT", cond_dict=cond_dict)
            if len(result) <= 0:
                insert_result = mydb.insert("T_AUTO_PRODUCT", product_params)
            else:
                insert_result = True

            if self.indexTitle:
                title_param = {
                    "productId": str(self.productId),
                    "titles": str(self.indexTitle)
                }
                mydb.delete("T_PRODUCT_TITLE", cond_dict={"productId": str(self.productId)})
                insert_result = mydb.insert("T_PRODUCT_TITLE", title_param)

            if insert_result:
                # 判断T_PRODUCT_PROPERTY表是否存在相同类型的业务数据，若存在则先删除再插入
                if self.time_ranges and not self.forecastPeriod:
                    startTime = str(self.time_ranges[0])
                    endTime = str(self.time_ranges[1])
                    if self.timeType == "year" and len(startTime)>4:
                        startTime = startTime[0:4]
                        endTime = endTime[0:4]
                elif self.forecastPeriod and not self.time_ranges:
                    startTime, endTime = [str(fp) for fp in self.forecastPeriod]
                    if self.timeType == "year" and len(startTime)>4:
                        startTime = startTime[0:4]
                        endTime = endTime[0:4]
                elif self.time_ranges and self.forecastPeriod:
                    startTime = str(self.time_ranges[0])
                    endTime = [str(fp) for fp in self.forecastPeriod][1]

                property_cond_dict = {
                    "productId": str(self.productId),
                    "productType": str(productType),
                    "busType": str(busType),
                    "busId": str(busId),
                    "element": str(element),
                    "dataSource": str(dataSource),
                    "areaCode": str(areaCode),
                    "timeType": str(timeType),
                    "level": str(level),
                    # "startTime": startTime,
                    # "endTime": endTime,
                    "forecastTime": str(self.forecastTime)
                }

                # 数据更新
                if self.forecastTime:
                    # 预测数据
                    property_dict = {
                        "productId": str(self.productId),
                        "forecastTime": str(self.forecastTime)
                    }
                    property_result = mydb.select("T_PRODUCT_PROPERTY", cond_dict=property_dict)
                    if len(property_result) > 0:
                        propertyId = property_result[0].get("propertyId")
                        mydb.delete("T_PRODUCT_DATA", cond_dict={"propertyId": propertyId})
                    else:
                        property_params = {
                            "propertyId": propertyId,
                        }
                        property_params.update(property_cond_dict)
                        mydb.insert("T_PRODUCT_PROPERTY", property_params)
                elif self.time_ranges:
                    if isinstance(self.flow_data, list):
                        input_data = self.flow_data[0]
                    else:
                        input_data = self.flow_data
                    if "time" in input_data.dims:
                        time_list_tmp = input_data.time.values
                        startTime = time_list_tmp[0]
                        endTime = time_list_tmp[-1]
                    elif "year" in input_data.dims:
                        time_list_tmp = input_data.year.values
                        startTime = time_list_tmp[0]
                        endTime = time_list_tmp[-1]
                    # 监测数据
                    sqlStr = 'SELECT a.time, a.value, b.productId,a.propertyId \
                                               FROM T_PRODUCT_DATA AS a \
                                               INNER JOIN T_PRODUCT_PROPERTY AS b \
                                               ON a.propertyId = b.propertyId \
                                               WHERE b.productId = "' + str(self.productId) + '" \
                                               AND a.time BETWEEN ' + startTime + ' AND ' + endTime
                    # 执行sql查询，返回结果数据
                    property_result = mydb.executeSql(sqlStr)
                    # logging.info("monitor data size: " + str(len(property_result)))
                    if len(property_result) > 0:
                        propertyId = property_result[0].get("propertyId")
                        del_sql = 'DELETE FROM T_PRODUCT_DATA  \
                                  WHERE propertyId = "' + str(propertyId) + '" AND time BETWEEN ' \
                                  + startTime + ' AND ' + endTime
                        mydb.executeCommit(del_sql) #我服了，写操作不提交？？？？？？
                    else:
                        property_result = mydb.select("T_PRODUCT_PROPERTY", cond_dict=property_cond_dict)
                        # logging.info("T_PRODUCT_PROPERTY data size: " + str(len(property_result)))
                        if len(property_result) > 0:
                            propertyId = property_result[0].get("propertyId")
                        else:
                            property_params = {
                                "propertyId": propertyId,
                            }
                            property_params.update(property_cond_dict)
                            mydb.insert("T_PRODUCT_PROPERTY", property_params)
                # property_result = mydb.select("T_PRODUCT_PROPERTY", cond_dict=property_cond_dict)
                # if len(property_result) > 0:
                #     propertyId = property_result[0].get("propertyId")
                #     mydb.delete("T_PRODUCT_DATA", cond_dict={"propertyId": propertyId})
                # else:
                #     property_params = {
                #         "propertyId": propertyId,
                #     }
                #     property_params.update(property_cond_dict)
                #     mydb.insert("T_PRODUCT_PROPERTY", property_params)
                if isinstance(self.flow_data, list):
                    input_data = self.flow_data[0].values
                    input_data_all = self.flow_data[0]
                else:
                    input_data = self.flow_data.values
                    input_data_all = self.flow_data

                if not self.format is None and  not self.saveType is None:
                    input_data = formatting_data(self.format, self.saveType, input_data)

                if "time" in input_data_all.dims:
                    time_list = input_data_all.time.values
                elif "year" in input_data_all.dims:
                    time_list = input_data_all.year.values
                else:
                    time_ranges = [startTime,endTime]
                    time_list = DateUtils.get_time_list(time_ranges, self.timeType)
                insert_attrs = ["dataId", "propertyId", "time", "value"]
                data_list = []
                for i, time in enumerate(time_list):
                    dataId = str(uuid.uuid1())
                    if isinstance(input_data[i], np.ndarray) and len(input_data[i]) > 1:
                        value = ",".join([str(indet_data_value) for indet_data_value in input_data[i]])
                    else:
                        value = str(input_data[i])
                    value_list = [dataId, propertyId, time, value]
                    data_list.append(value_list)
                mydb.insertMany("T_PRODUCT_DATA", insert_attrs, data_list)
            else:
                logging.info("productId do not exist!")
        finally: #任何情况都得释放掉连接
            mydb.con.close()

    # 多数据源合并
    def convert_data(self, algorithm_input_data):
        flow_data = []

        for aid_index, aid in enumerate(algorithm_input_data):
            if isinstance(aid["outputData"], list):
                for a in aid["outputData"]:
                    flow_data.append(a.values)
                    time_data = a.time
            else:
                if len(aid["outputData"].shape) == 2:
                    for xi in range(aid["outputData"].shape[1]):
                        flow_data.append(aid["outputData"][:, xi])
                else:
                    flow_data.append(aid["outputData"].values)
                time_data = aid["outputData"].time
        flow_data = np.asarray(flow_data)
        data_list = []
        for time_index, time in enumerate(time_data):
            data_list.append(flow_data[:, time_index])
        flow_data = xr.DataArray(data_list, dims=["time", "value"])
        flow_data["time"] = time_data
        self.flow_data = flow_data
