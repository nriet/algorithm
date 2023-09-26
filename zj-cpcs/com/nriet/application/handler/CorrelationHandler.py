# -*- coding:utf-8 -*-

from com.nriet.application.handler.Basehandler import BaseHandler
from com.nriet.utils.result.ResponseResultUtils import response_result_convert
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
from com.nriet.utils.proxyUtils import create_class_instance
import logging, traceback,threading
from com.nriet.utils.result.ResponseResultUtils import build_response_dict
from com.nriet.config.ResponseCodeAndMsgEum import PARAMETER_VALUE_MISSING_CODE,PARAMETER_VALUE_MISSING_MSG,CUSTOM_ERROR_CODE,CUSTOM_ERROR_MSG
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
convert_switch = look_for_single_global_config('RESULT_FORMAT_TIANQIN_SWITCH')
from  tornado import gen
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
class CorrelationHandler(BaseHandler):
    executor = ThreadPoolExecutor(4)
    @gen.coroutine
    def get(self):
        """
        GET请求
        :return:
        """
        result_dict = yield self.doing()
        self.result = result_dict
        thread_local = threading.current_thread()
        thread_local.request_id = self.serial_no
        self.write(result_dict)
        self.set_header('cpcs_request_id', self.serial_no)
        self.flush()

    @run_on_executor
    def doing(self,*args,**kwargs):
        threading.current_thread().request_id = self.serial_no #不可删除，用于日志收集与处理

        logging.info("开始调用合成分析接口..")
        request_dict = eval(self.get_argument('CPCS'))
        try:
            # method_name = ast.literal_eval(self.get_argument('methodName'))
            method_name = eval(self.get_argument('methodName'))
            logging.info("方法名称：%s" % method_name)
            method_object = create_class_instance(
                '.'.join(['com.nriet.algorithm.business', method_name]),
                method_name)
            result_dict = method_object.execute(request_dict)
            result_dict = response_result_convert(result_dict, convert_switch)
        except AlgorithmException as ae:
            logging.error(traceback.format_exc())
            result_dict = ae.__str__()


        except IndentationError as ie:
            logging.error(traceback.format_exc())
            result_dict = build_response_dict(response_code=PARAMETER_VALUE_MISSING_CODE,response_msg=PARAMETER_VALUE_MISSING_MSG % "methodName")
        except Exception as e:
            logging.error(traceback.format_exc())
            result_dict = build_response_dict(response_code=CUSTOM_ERROR_CODE,response_msg=CUSTOM_ERROR_MSG)
        logging.info("结束调用合成分析接口..")
        # raise gen.Return(result_dict)
        return result_dict



