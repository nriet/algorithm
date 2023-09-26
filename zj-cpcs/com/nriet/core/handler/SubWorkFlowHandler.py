#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/02/28
# @Author : xulh
# @File : SubWorkFlowHandler.py
from com.nriet.algorithm.Component import Component
from com.nriet.config.flowMap.FlowMapping import flow_map
from com.nriet.utils import proxyUtils
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.utils.exception.workFlow.SubWorkFlowException import SubWorkFlowException
from com.nriet.config.ResponseCodeAndMsgEum import SUB_WORK_FLOW_ERROR_CODE,CIPAS_SUCCESS_CODE
import traceback
import logging
import os
import importlib,sys
importlib.reload(sys)

class SubWorkFlowHandler(Component):

    def  __init__(self, sub_flow_index, work_flow_dto, sun_flow_order):
        '''
        :param sub_flow_index: 子流程所包含的算法
        :param work_flow_dto: 流程对象，包含流程参数及流程运行中生成的结果序列
        :param sun_flow_index: 子流程执行顺序
        '''
        logging.info("     SubWorkFlowHandler processing init method")

        self.work_flow_dto = work_flow_dto
        self.sub_flow_index = sub_flow_index
        self.sub_flow_order = sun_flow_order
        self.sub_local_params = work_flow_dto.getParam("work_flow_params")[sun_flow_order]
        self.algorithms = []
        self.sub_work_flow_dto = None

    def verify(self):
        result_dict = {"response_code":CIPAS_SUCCESS_CODE }
        if not self.sub_flow_index:
            result_dict["response_code"] = SUB_WORK_FLOW_ERROR_CODE
            result_dict["response_msg"] = "sub_flow_index error:%s" % self.sub_flow_order
        return result_dict

    def build_inner_dto(self):
        pass

    def execute(self):
        logging.info("         SubWorkFlowHandler processing execute method")
        # try:
        result_dict = self.verify()
        if result_dict["response_code"]==CIPAS_SUCCESS_CODE:
            try:

                for algorithm_order, algorithm_id in enumerate(self.sub_flow_index):
                    # 创建具体算法类
                    cs = proxyUtils.import_module(flow_map[str(algorithm_id)])
                    className = flow_map[str(algorithm_id)].split(".")[-1]
                    obj_class = proxyUtils.get_attr(cs, className)

                    # 准备算法参数
                    algorithm_param_list = []
                    algorithm_data_index = self.sub_local_params["subflow_inputdata_indexes"][algorithm_order]
                    algorithm_input_data = []
                    if algorithm_data_index:
                        for data_index in algorithm_data_index:
                            if isinstance(data_index, list):
                                temp = []
                                for index in data_index:
                                    temp.append(self.work_flow_dto.tmp_data_queue[index])
                                algorithm_input_data.append(temp)
                            else:
                                algorithm_input_data.append(self.work_flow_dto.tmp_data_queue[data_index])


                    algorithm_param_list.append(self.sub_local_params["method_params"][algorithm_order])
                    algorithm_param_list.append(algorithm_input_data)
                    obj = obj_class(*algorithm_param_list)
                    logging.info("         Current algorithm is : %s" % obj_class )
                    # 执行算法,根据className判断是否为绘图子流程
                    if className in ["DrawController","DrawRegionsCpcsController","DrawChartCpcsController","DrawRegionsHandler_MODEL_BIG","DrawRegionsHandler_MODEL_SMALL"]:
                        output_img_path = algorithm_param_list[0]['data_output_params'][0]['output_img_path']
                        output_img_name = algorithm_param_list[0]['data_output_params'][0]['output_img_name']
                        output_img_type = algorithm_param_list[0]['data_output_params'][0]['output_img_type']
                        result_dict['output_img_name'] = output_img_path+output_img_name+'.'+output_img_type
                        result_dict['output_path'] = output_img_path

                        # 20211102,加入图片名称到临时变量，方便上下联动
                        os.environ['productName'] = output_img_name+'.'+output_img_type

                        algorithm_result = obj.execute()
                    elif(className in ['TxtOutPut','StatisticsDataOutput']):
                        outPutName=algorithm_param_list[0]['outPutName']
                        outPutPath=algorithm_param_list[0]['outPutPath']
                        result_dict['output_file_name'] = ''.join((outPutPath,outPutName))
                        result_dict['output_path'] = outPutPath
                        algorithm_result = obj.execute()
                        self.work_flow_dto.tmp_data_queue.append(obj.output_data)
                    else:
                        algorithm_result = obj.execute()
                        self.work_flow_dto.tmp_data_queue.append(obj.output_data)
                     #   如果算法有返回result,并且为失败
                    if  algorithm_result:
                        if algorithm_result.get('response_code') !=CIPAS_SUCCESS_CODE:
                            result_dict = algorithm_result
                            break
                        else:
                            result_dict.update(algorithm_result)

            except AlgorithmException as ae:
                return ae.__str__()
            except Exception as e :
                logging.error(traceback.format_exc())
                raise SubWorkFlowException(response_msg=e.__str__())

        return result_dict


