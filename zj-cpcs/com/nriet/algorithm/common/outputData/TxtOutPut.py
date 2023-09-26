#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/01/09
# @Author : xulh
# @File : TxtOutPut.py

import os
import numpy as np
from com.nriet.algorithm.common.outputData.OutputDataComponent import OutputDataComponent
from com.nriet.utils import fileUtils, DateUtils
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import PARAMETER_VALUE_MISSING_CODE
import logging


class TxtOutPut(OutputDataComponent):

    def __init__(self, sub_local_params, algorithm_input_data):

        """
        :param sub_local_params:流程参数，算法运算返回结果
        :param algorithm_input_data:流程数据
        """
        self.filePath = sub_local_params["outPutPath"]
        self.fileName = sub_local_params["outPutName"]
        self.sub_flow_data = algorithm_input_data[0]
        self.data = algorithm_input_data[0]["outputData"]
        self.timeRanges = sub_local_params.get("timeRanges")
        self.times = sub_local_params.get("timeType")
        self.title = sub_local_params["txtFields"]
        self.output_data = None
        # self.request_json = proData.getParam("work_flow_params")[data_index]["data_output_params"][0][0]

    def execute(self):
        if np.isnan(np.mean(self.data.values)):
            raise AlgorithmException(response_code=PARAMETER_VALUE_MISSING_CODE, response_msg='All Missing Values')
        if self.title[0] == "time":
            time_list = DateUtils.get_time_list(self.timeRanges, self.times)
        else:
            time_list = np.asarray(self.data[self.title[0]].values, dtype=np.int)

        file_name = self.filePath + self.fileName
        content = ""
        np.set_logging.infooptions(suppress=True)
        if not os.path.exists(file_name):
            content = str(self.title[0]) + " " + str(self.title[1]) + "\r\n"
            for i, con in enumerate(np.around(self.data.values, decimals=2)):
                content = content + str(time_list[i]) + " " + '{:.2f}'.format(con) + "\r\n"
            # 上传文件到obs
            fileUtils.creat_txt_file_to_obs(self.filePath, self.fileName, content)

            fileUtils.creatTxtFile(self.filePath, self.fileName, content)
        else:
            for i, con in enumerate(np.around(self.data.values, decimals=2)):
                content = content + str(time_list[i]) + " " + str(con) + "\r\n"
            fileUtils.relpace_content(self.filePath + self.fileName, time_list[0], time_list[-1], content)
