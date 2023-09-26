# coding=utf-8

from com.nriet.application.handler.Basehandler import BaseHandler
from com.nriet.algorithm.common.drawComponent.drawController.DrawRegionsController import DrawRegionsController
from com.nriet.utils.result.ResponseResultUtils import response_result_convert
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config import ResponseCodeAndMsgEum
from com.nriet.utils.result.ResponseResultUtils import build_response_dict,judge_response_result
import logging, traceback,threading
from  tornado import gen
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
convert_switch = look_for_single_global_config('RESULT_FORMAT_TIANQIN_SWITCH')


class DrawRegionsHandler(BaseHandler):
    """
    绘图服务处理类，暂不支持|方式命令
    """
    executor = ThreadPoolExecutor(4)
    @gen.coroutine
    def get(self):
        """
        get请求 ,支持返回文件流
        :return:
        """
        result_dict = yield self.doing()
        self.result = result_dict
        thread_local = threading.current_thread()
        thread_local.request_id = self.serial_no
        self.write(result_dict)
        self.set_header('cpcs_request_id', self.serial_no)
        self.finish()


    @run_on_executor
    def doing(self,*args,**kwargs):
        threading.current_thread().request_id = self.serial_no  #不可删除，用于日志收集与处理

        # 获取CPCS参数
        request_dict = eval(self.get_argument('CPCS'))
        self.productName = request_dict['output_img_name'] + '.' + request_dict['output_img_type']

        # 实例化DrawFrontController,执行任务
        try:
            logging.info("开始调用通用绘图服务接口..")
            draw_front_controller = DrawRegionsController(sub_local_params=request_dict)
            result_dict = draw_front_controller.execute()

            if judge_response_result(result_dict):
                result_dict['output_img_name'] = ".".join(
                    [request_dict["output_img_name"], request_dict["output_img_type"]])
                result_dict['output_img_path'] = request_dict["output_img_path"]

        except AlgorithmException as ae:
            logging.error(traceback.format_exc())  # 这里貌似没多大必要，先放着看看效果吧
            result_dict = build_response_dict(response_code=ae.response_code, response_msg=ae.response_msg,
                                              serial_no=self.serial_no,
                                              from_tianqin=convert_switch)

        except ValueError:
            logging.error(traceback.format_exc())
            result_dict = build_response_dict(response_code=ResponseCodeAndMsgEum.INPUT_PAGE_PARAM_FORMAT_ERROR_CODE,
                                              response_msg=ResponseCodeAndMsgEum.INPUT_PAGE_PARAM_FORMAT_ERROR_MSG,
                                              serial_no=self.serial_no,
                                              from_tianqin=convert_switch)
        except Exception:
            logging.error(traceback.format_exc())
            result_dict = build_response_dict(response_code=ResponseCodeAndMsgEum.SERVER_HANDLING_ERROR_CODE,
                                              response_msg=ResponseCodeAndMsgEum.SERVER_HANDLING_ERROR_MSG,
                                              serial_no=self.serial_no,
                                              from_tianqin=convert_switch)

        # 返回格式转换
        logging.info("结束调用通用绘图服务接口。")
        result_dict = response_result_convert(result_dict, convert_switch)
        # raise gen.Return(result_dict)
        return result_dict
        # self.result = result_dict
        # self.write(result_dict)
        #
        # self.finish()
