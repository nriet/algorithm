# -*- coding:utf-8 -*-
# @Time : 2020/09/01s
# @Author : huxin
# @File : GridDataInterfaceData.py
# 格点数据读取接口算法


import requests, time, os
import urllib.parse
from com.nriet.algorithm.common.inputData.InputDataComponent import InputDataComponent
from com.nriet.utils.dataInterface.GridDataSet import GridDataSet
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
from com.nriet.utils.databaseConnection.MySQLHandler import MysqldbHelper
from com.nriet.config.MySQLConfig import config
from com.nriet.config.ResponseCodeAndMsgEum import DB_DATA_NOT_FOUND_ERROR_CODE
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
import logging
import traceback
import numpy as np




class GridDataInterfaceData(InputDataComponent):

    def __init__(self, sub_local_params, algorithm_input_data):
        """
        :param sub_local_params:流程参数，算法运算返回结果
        :param algorithm_input_data:流程数据
        """
        # 1.数据接口地址
        self.baseUrl =look_for_single_global_config("SPACE_URL")
        self.args = sub_local_params.copy()
        self.timeType = sub_local_params.get("timeType")

        # 2.1接口参数没有四级编码dataCode时，需从库中查询四级编码
        if "dataCode" not in self.args.keys():
           ele_config = self.get_element_config(self.args.get("dataSource"), self.args.get("elements"), self.args.get("timeType"))
           self.args["dataCode"] = ele_config["spaceDataCode"]  # 资料代码
           self.args["element"] = ele_config["spaceVar"]   # 要素名称
        # 2.2 剔除 dataSource、 elements、 timeType
        if "dataSource" in self.args.keys():
            self.args.pop("dataSource")
        if "elements" in self.args.keys():
            self.args.pop("elements")
        if "timeType" in self.args.keys():
            self.args.pop("timeType")

        # 3.特殊字段【calOperation】常年值替换处理
        if "calOperation" in self.args.keys():
            calOperationStr = self.args["calOperation"]
            calOperationStr = calOperationStr.replace("1981-2010","1981").replace("1991-2020","1991")
            self.args["calOperation"] = calOperationStr

        # 4.特殊字段【area】str处理
        if "area" in self.args.keys() and (isinstance(self.args.get("area"), tuple)):
            self.args["area"] = ','.join([str(item) for item in self.args["area"]])

        # 5.季尺度 前冬04处理成00
        if "timeType" in sub_local_params.keys() and sub_local_params.get("timeType") == "season":
            timeRange = self.args["timeRange"]
            tmpStartTime = str(timeRange[0])
            if tmpStartTime.endswith("04"):
                tmpStartTime = tmpStartTime[0:4] + "00"
            tmpEndTime =  str(timeRange[1])
            if tmpEndTime.endswith("04"):
                tmpEndTime = tmpEndTime[0:4] + "00"
            self.args["timeRange"] = [int(tmpStartTime), int(tmpEndTime)]  # 时间范围

    def execute(self):
        outputData = {}
        data_list = []

        # 1.调用格点接口获取数据，并转换为Xarray库的DataArray对象
        xarray_data = self.query_data_by_interface()
        # 季尺度时间转换 00 ——> 04
        if self.timeType and self.timeType == "season":
            if "time" in xarray_data.dims:
                xarray_data.time.values = [ str(tt+4)if str(tt).endswith("00") else str(tt) for tt in list(xarray_data.time.values)]
        # 2.数据结果保存至临时队列
        data_list.append(xarray_data)
        outputData["outputData"] = xarray_data
        self.output_data = outputData

    def query_data_by_interface(self):
        """
        调用格点接口获取数据，并转换为Xarray库的DataArray对象
        :return: Xarray库的DataArray对象
        """

        logging.info("              " + self.args.__str__())
        main_start_time = time.time()

        # 1.调用格点接口获取数据
        # data = requests.get(self.baseUrl, params=self.args)
        url = self.baseUrl + urllib.parse.urlencode(self.args)
        logging.info("             " + url)
        print("             " + url)
        data = requests.request('get', url)

        # 2.将字节流转换为Xarray库的DataArray对象
        nc_bytes = data.content
        try:
            nc_dataset = GridDataSet(nc_bytes)
        except ValueError as e:
            logging.warning("              " + self.args.__str__())
            logging.warning("             " + url)
            logging.warning(nc_bytes)
            raise e

        xarray_data = nc_dataset.get_xarray_data()
        # 要素的变量名
        var = self.args.get('element')
        if "analysisType" in self.args.keys() and self.args.get("analysisType") == "correlation":
            var = "ppmcc"

        out_data = xarray_data[var]

        main_stop_time = time.time()
        cost = main_stop_time - main_start_time
        logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))

        # 3.返回数据
        return out_data


    def get_element_config(self, dataSoruce, element, time_type):
        # 拼接获取空间库配置信息数据的SQL
        table_name = look_for_single_global_config("SPACE_DB")
        sql_str = "SELECT * FROM `%s` WHERE dataSourceName = '%s' AND elementName='%s' AND timeType = '%s'" % (table_name,
            dataSoruce.upper(), element.upper(), time_type.upper())
        logging.info(sql_str)
        # 查询数据配置
        mydb = MysqldbHelper(config)
        sql_result = mydb.executeSql(sql_str)
        if not sql_result:
            raise AlgorithmException(response_code=DB_DATA_NOT_FOUND_ERROR_CODE,
                                     response_msg='Cannot find space config,dataSourceName is %s ,elementName is %s ,timeType is %s'
                                                  % (dataSoruce, element, time_type.upper()))
        logging.info("The spaceAvailable Value is %s" % sql_result[0].get('spaceAvailable'))
        return sql_result[0]