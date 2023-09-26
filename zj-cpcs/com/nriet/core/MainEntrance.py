#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2019/10/21
# @Author : xulh
# @File : olr_main.py

import sys
import os
import ast
import numpy as np
import itertools
import uuid
import logging
logger = logging.getLogger(__name__)
logger.root.setLevel(level=logging.INFO)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


logging.info("Project root path is : %s" % os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from com.nriet.utils.exception.SysException import SysException
from com.nriet.core.handler.WorkFlowHandler import WorkFlowHandler
from com.nriet.utils.result.ResponseResultUtils import build_response_dict,judge_response_result,response_result_convert
from com.nriet.utils.exception.workFlow.SubWorkFlowException import SubWorkFlowException
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
from com.nriet.config import ResponseCodeAndMsgEum
import json
import copy,time,os
import traceback
class MainEntrance:

    def __init__(self,request_json= None):
        '''
        :param request_json: 前台页面参数,包含了通配符
        '''
        # 1.具体参数解析和转换
        self.request_json = request_json
        self.work_flow_handler = None
        self.needRouting='0'

    def execute(self):
        # convert_switch = look_for_single_global_config('RESULT_FORMAT_TIANQIN_SWITCH')
        try:
            # 1. 创建workFlow对象并调度执行。
            self.work_flow_handler = WorkFlowHandler(self.request_json)
            result_dict = self.work_flow_handler.execute()
            # 2.返回值兼容处理
            self.needRouting =  self.work_flow_handler.needRouting
            del self.work_flow_handler
            return result_dict
        except SubWorkFlowException as sfe:
            return sfe.__str__()
        except SysException as se:
            traceback.print_exc()
            return build_response_dict(response_code=se.response_code,response_msg=se.response_msg,from_tianqin=convert_switch)
        except Exception as e:  # 其他未捕获的异常，视为系统异常，错误码9999
            traceback.print_exc()

            return SysException(message=e.__str__(),from_tianqin=convert_switch).__str__()


# |的处理，对于多个字段分别存在|的情况，采用笛卡尔积的方式分割
def split_params(page_params):
    param_list = []
    param_dict = {}
    result_list = []
    # 将参数中存在|的参数放入param_dict
    for param_key in page_params.keys():
        param_value = page_params[param_key]
        if param_value.__contains__("|"):
            param_dict[param_key] = param_value.split("|")

    # 循环param_dict，将带有|的参数以key:value的形式拼接放入param_list
    for param_dict_key, param_dict_value in param_dict.items():
        pd_list = []
        for pd in param_dict_value:
            pd_list.append(param_dict_key + ":" + pd)
        param_list.append(pd_list)
    dcr_list = []
    # 笛卡尔积
    for item in itertools.product(*param_list):
        dcr_list.append(item)
    for dcr in dcr_list:
        dcr_param = {}
        for d in dcr:
            k, v = d.split(":")
            dcr_param[k] = v
        page_params_copy = copy.deepcopy(page_params)
        page_params_copy.update(dcr_param)
        result_list.append(page_params_copy)

    return result_list


if __name__ == "__main__":
    main_start_time = time.time()
    module = sys.modules[__name__]
    request_json = None
    serial_no = str(uuid.uuid4())
    page_params = ast.literal_eval(sys.argv[1])
   # page_params = {"timeType":"day","timeRanges":"[20230805,20230810]","ltm":"1991-2020","bussId":"BUSS_QHJC_OCEAN_NINO34_001"}
   #  page_params = {"timeType":"mon","timeRanges":"[202305,202305]","ltm":"1991-2020","areaCode":"33","bussId":"BUSS_BASICEM_CSOD_AVGT_JP_ZJ_SMALL"}
    convert_switch = look_for_single_global_config('RESULT_FORMAT_TIANQIN_SWITCH')
    if len(sys.argv) > 1:
        try:
            # 1. 获取页面传参
            print("MainEntrance serial_no is : %s ,input_params is : %s" % (serial_no, sys.argv[1]))
            # 2. 页面参数包含|的处理
            print("MainEntrance processing split-params method")
            param_list = split_params(page_params)
            result_dict = build_response_dict(from_tianqin=convert_switch)

            print("MainEntrance processing execute method")
            if param_list:
                for pl in param_list:
                    me = MainEntrance()
                    me.request_json = pl
                    result_dict = me.execute()
                    del me
                    if not judge_response_result(result_dict):
                        break
                result_dict = response_result_convert(result_dict,convert_switch)
            main_stop_time = time.time()
            cost = main_stop_time - main_start_time
            print("             %s cost %s second" % (os.path.basename(__file__), cost))
            return_str = json.dumps(result_dict, ensure_ascii=False)
            if convert_switch=='1':
                print("".join(['""', "''", return_str, "''", '""']))
            else:
                print(return_str)
        except ValueError:
            return_str = json.dumps(
                    build_response_dict(response_code=ResponseCodeAndMsgEum.INPUT_PAGE_PARAM_FORMAT_ERROR_CODE,
                                        response_msg=ResponseCodeAndMsgEum.INPUT_PAGE_PARAM_FORMAT_ERROR_MSG,
                                        serial_no=serial_no, from_tianqin=convert_switch), ensure_ascii=False)
            if convert_switch=='1':
                print("".join(['""', "''", return_str, "''", '""']))
            else:
                print(return_str)

    else:
        return_str = json.dumps(build_response_dict(response_code=ResponseCodeAndMsgEum.INPUT_PAGE_PARAM_FORMAT_ERROR_CODE, response_msg=ResponseCodeAndMsgEum.INPUT_PAGE_PARAM_FORMAT_ERROR_MSG,
                                             serial_no=serial_no,from_tianqin=page_params.get('from_tianqin',1)),ensure_ascii=False)
        if convert_switch == '1':
            print("".join(['""', "''", return_str, "''", '""']))
        else:
            print(return_str)
