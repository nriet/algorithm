#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/02/28
# @Author : xulh
# @File : WorkFlowHandler.py
import ast
import logging
from com.nriet.algorithm.Component import Component
from com.nriet.core.dto.WorkFlowDto import WorkFlowDto
from com.nriet.core.handler.SubWorkFlowHandler import SubWorkFlowHandler
from pathlib import Path
from com.nriet.utils.exception.workFlow.SubWorkFlowException import SubWorkFlowException
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import CIPAS_SUCCESS_CODE,INPUT_PAGE_PARAM_MISSING_CODE,INPUT_PAGE_PARAM_MISSING_MSG
from com.nriet.utils.result.ResponseResultUtils import build_response_dict,judge_response_result
from com.nriet.utils.obs.ObsUtils import ObsUtils
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
from com.nriet.utils.exception.workFlow.WorkFlowException import WorkFlowException

from com.nriet.utils.fileUtils import readJson
import importlib,sys,time,os
importlib.reload(sys)
class WorkFlowHandler(Component):

    def __init__(self, request_json):
        self.request_json = request_json
        self.local_params = None
        self.work_flow_dto = None
        self.sub_flow_handlers = []
        self.needRouting='0'

    # 参数校验
    def verify(self):
        local_params = self.request_json
        result_dict = {}
        response_code=CIPAS_SUCCESS_CODE
        response_msg=None

        param_name_list = ["bussId"]
        if not local_params:
            for param_name in param_name_list:
                if not local_params.keys().__contains__(param_name):
                    response_code = INPUT_PAGE_PARAM_MISSING_CODE
                    response_msg = INPUT_PAGE_PARAM_MISSING_MSG % param_name
                    break
        result_dict = build_response_dict(result_dict,response_code=response_code,response_msg=response_msg)
        result_dict["local_params"] = local_params
        return result_dict

    # 创建workFlowDto
    def build_inner_dto(self):
        self.work_flow_dto = WorkFlowDto(self.local_params)

    def execute(self):
        work_flow_start_time = time.time()

        result_dict = self.verify()
        if judge_response_result(result_dict):
            logging.info(" WorkFlowHandler verify request params success!")

            # 循环创建SubWorkFlowHandler对象
            try:
                self.local_params = result_dict.pop("local_params")
                self.build_inner_dto()

                # 是否重载，如果不重载就查OBS，OBS有结果则直接返回
                SAVE_TO_OBS_SWITCH = int(look_for_single_global_config("SAVE_TO_OBS_SWITCH"))
                RELOAD_SWITCH = int(look_for_single_global_config("RELOAD_SWITCH"))
                logging.info(" SAVE_TO_OBS_SWITCH is %s" % str(SAVE_TO_OBS_SWITCH))
                logging.info(" RELOAD_SWITCH is %s" % str(RELOAD_SWITCH))
                logging.info(" Reload params is %s" % self.local_params.get('reload',0))

                if int(self.local_params.get('reload',0))==1 or RELOAD_SWITCH==1:
                    output_img_name = self.local_params['output_img_name']
                    output_img_type = self.local_params['output_img_type']

                    if SAVE_TO_OBS_SWITCH:
                        output_img_name_concat = '.'.join([output_img_name,output_img_type])
                        output_file_name_concat = '.'.join([output_img_name,"nc"])
                        bucket_name = look_for_single_global_config("OBS_BUCKET_NAME")
                        check_resp = ObsUtils().check_object_exist(bucket_name=bucket_name,
                                                                   object_name=output_img_name_concat)
                        if check_resp:
                            # 20211102,加入图片名称到临时变量，方便上下联动
                            os.environ['productName'] = output_img_name_concat
                            logging.info(" Product %s found in OBS, just return the result" % output_img_name_concat)
                            result_dict['output_img_name'] = output_img_name_concat
                            result_dict['output_file_name'] = output_file_name_concat
                            return result_dict

                    else:
                        output_img_path = self.local_params['output_img_path']
                        output_img_name_concat = ''.join([output_img_path,output_img_name,".",output_img_type])
                        output_file_name_concat = ''.join([output_img_path,output_img_name,".nc"])
                        img_file = Path(output_img_name_concat)
                        if img_file.exists():
                            # 20211102,加入图片名称到临时变量，方便上下联动
                            os.environ['productName'] = output_img_name_concat
                            logging.info(" Product %s found in nfsshare, just return the result" % output_img_name_concat)
                            result_dict['output_path'] = output_img_path
                            result_dict['output_img_name'] = output_img_name_concat
                            result_dict['output_file_name'] = output_file_name_concat
                            return result_dict

                logging.info(" WorkFlowHandler loading sub_flow_indexes!")
                sub_flow_indexes = readJson(self.work_flow_dto.getParam("work_flow_path"))["sub_flow_indexes"]
                for sub_flow_order, sub_flow_index in enumerate(sub_flow_indexes):
                    sub_flow_handler = SubWorkFlowHandler(sub_flow_index, self.work_flow_dto, sub_flow_order)
                    sub_result_dict = sub_flow_handler.execute()
                    if not sub_result_dict or (sub_result_dict.get("response_code") != CIPAS_SUCCESS_CODE):
                        logging.info(" WorkFlowHandler processing SubWorkFlowHandler failed,The number of SubWorkFlowHandler is %s" % str(sub_flow_order))
                        result_dict = sub_result_dict
                        break
                    else:
                        result_dict.update(sub_result_dict)
                self.needRouting=self.work_flow_dto.needRouting
                del self.work_flow_dto
                work_flow_stop_time = time.time()
                cost = work_flow_stop_time - work_flow_start_time
                logging.info(" %s cost %s second" % (os.path.basename(__file__), cost))

                return result_dict
            except SubWorkFlowException as sfe:
                return sfe.__str__()
            except AlgorithmException as ae:
                return ae.__str__()
            except WorkFlowException as we:
                return we.__str__()
            # except Exception:
            #     return build_response_dict(response_code="9999",response_msg=        "System error occurred!")

        else: # 校验失败，主流程结束,返回校验结果给上级
            logging.info(" WorkFlowHandler verify request params failed!")
            result_dict.pop('local_params')
            return result_dict


