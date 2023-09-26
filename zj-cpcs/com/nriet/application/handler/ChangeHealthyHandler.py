# coding=utf-8
# @Time : 2021/12/10
# @Author : huxin

from tornado.web import RequestHandler
import time,uuid,os,socket
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
import logging
class ChangeHealthyHandler(RequestHandler):
    """
    基本操作类，之后的类可以直接继承
    """

    def prepare(self) -> None:
        """
        无论什么请求类型，每次请求前都会触发此方法
        Returns:

        """

        self.serial_no = str(uuid.uuid4())
        self.result = None

        # logging.info("CPCS触发健康监测请求。请求id: %s ,请求参数：%s" % (self.serial_no,self.get_argument('CPCS')))

    def get(self):
        # logging.info("CPCS结束健康监测请求")
        # self.write("Server status's normal.")
        self.set_header('cpcs_request_id', self.serial_no)
        value = self.get_argument('CPCS')
        # 从当前环境变量里边查询当前服务是否正常

        file_name = look_for_single_global_config('IS_HEALTHY_TXT')
        logging.info("修改健康信息is_healthy=%s至%s" % (value,file_name))
        if os.path.exists(file_name):
            with open(file_name, mode='w', encoding='utf-8') as file:
                file.write('is_healthy=%s' % value)
        logging.info("修改健康信息is_healthy成功")
        self.finish()

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

