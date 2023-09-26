# coding=utf-8
# @Time : 2021/12/10
# @Author : huxin

from tornado.web import RequestHandler
import time,uuid,os,socket
import logging
from  tornado import gen
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
from com.nriet.utils.result.ResponseResultUtils import build_response_dict

class TimeOutTestHandler(RequestHandler):
    """
    基本操作类，之后的类可以直接继承
    """
    executor = ThreadPoolExecutor(4)
    def prepare(self) -> None:
        """
        无论什么请求类型，每次请求前都会触发此方法
        Returns:

        """

        self.serial_no = str(uuid.uuid4())
        self.result = None

        # logging.info("CPCS触发健康监测请求。请求id: %s ,请求参数：%s" % (self.serial_no,self.get_argument('CPCS')))

    @gen.coroutine
    def get(self):
        # logging.info("CPCS结束健康监测请求")
        # self.write("Server status's normal.")
        self.set_header('cpcs_request_id', self.serial_no)

        result_dict = yield self.doing()
        self.result = result_dict
        self.write(result_dict)
        self.finish()

    @run_on_executor
    def doing(self,*args,**kwargs):
        logging.info('服务正在处理 %s' % self.serial_no)
        time.sleep(10)
        logging.info('服务处理完毕 %s' % self.serial_no)
        return build_response_dict()


    def set_default_headers(self):
        """
        设置默认的响应头
        :return:
        """
        # 解决JS跨域请求问题
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST, GET')
        self.set_header('Access-Control-Max-Age', 1000)
        self.set_header('Access-Control-Allow-Headers', '*')
        # 设计返回类型，默认返回json类型，如果后边需要返回文件流，请修改Content-type
        self.set_header('Content-type', 'application/json; charset=UTF-8')

        # 设置服务器标识，安全考虑
        self.set_header('Server', 'WebServer')
        # 删除此请求头，不然相同命令会经常返回304
        # del self.request.headers['If-None-Match']


    def _request_summary(self):
        """
        定义每次请求返回时的message格式
        Returns:
        """
        return "%s  [request_ip:%s] [serial_no:%s] [result: %s]" % (self.request.method,
                                      self.request.remote_ip,
                                      self.serial_no,self.result)

