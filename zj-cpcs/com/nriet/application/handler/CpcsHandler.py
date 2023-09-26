# coding=utf-8

from com.nriet.application.handler.Basehandler import BaseHandler
from com.nriet.core.MainEntrance import MainEntrance
from com.nriet.utils.result.ResponseResultUtils import response_result_convert
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
import os
convert_switch = look_for_single_global_config('RESULT_FORMAT_TIANQIN_SWITCH')
from  tornado import gen
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
import logging, threading
class CpcsHandler(BaseHandler):
    executor = ThreadPoolExecutor(4)
    """
    CPCS服务处理类，暂不支持|方式命令
    """
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
        threading.current_thread().request_id = self.serial_no #不可删除，用于日志收集与处理

        request_dict = eval(self.get_argument('CPCS'))

        # 实例化MainEntrance,执行任务
        logging.info("开始调用CPCS通用入口接口..")
        main_entrance = MainEntrance(request_json=request_dict)
        result_dict = main_entrance.execute()
        self.needRouting = main_entrance.needRouting
        # 返回格式转换
        logging.info("结束调用CPCS通用入口接口..")
        result_dict = response_result_convert(result_dict, convert_switch)

        # # 如果考虑输出文件流
        # if eval(self.get_query_argument('needFileOutput')) == '1':
        #     # 从 result_dict中摘取下载队列
        #
        #
        #     data = xr.open_dataset(
        #         "/nfsshare/cdbdata/product/MOP/GLATMOS/TROLR/OLR/NOAA/TR/DAY/0000/2021/02/01/MOP_CHCC_GLATMOS_TROLR_OLR_NOAA_TR_DAY_0000_PB_20210201-20210201_SK.nc")
        #     data_bytes = data.to_netcdf(format="NETCDF3_CLASSIC")
        #     self.set_header('Content-Type', 'application/octet-stream')
        #     self.set_header('Content-Disposition',
        #                     'attachment; filename=' + 'MOP_CHCC_GLATMOS_TROLR_OLR_NOAA_TR_DAY_0000_PB_20210201-20210201_SK.nc')
        #     self.set_header('task_result', json_encode(result_dict))
        #     self.write(data_bytes)
        # else:
        #     self.write(result_dict)
        logging.info('check productName : %s' % os.environ.get('productName', None))
        self.productName = os.environ.get('productName', None)
        # raise gen.Return(result_dict)
        return result_dict

