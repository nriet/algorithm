# coding=utf-8
# @Time : 2021/05/24
# @Author : huxin

from tornado.web import RequestHandler
import time,uuid,os,socket
import datetime
from com.nriet.thridParty.CPCSRestartKafkaProducer import CipasKafkaProducer
import logging,requests,json
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
from com.nriet.utils.result.ResponseResultUtils import judge_response_result
from com.nriet.utils.RedisUtils import get_redis_client,transaction_set_order
import threading
class BaseHandler(RequestHandler):
    """
    基本操作类，之后的类可以直接继承
    """

    def prepare(self) -> None:
        """
        无论什么请求类型，每次请求前都会触发此方法
        Returns:

        """
        self.serial_no = str(uuid.uuid4())
        thread_local = threading.current_thread()
        thread_local.request_id = self.serial_no

        self.occur_time = int(datetime.datetime.now().timestamp())*1000
        self.process_start_time = int(datetime.datetime.now().timestamp())*1000

        self.start_time = time.time()

        self.result = None
        self.needRouting = self.get_argument('needRouting',default=None)
        logging.info("CPCS触发请求。请求id: %s ,请求参数：%s" % (self.serial_no,self.get_argument('CPCS')))

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

    def on_finish(self) -> None:
        """
        每次请求之后的处理逻辑，如日志打印、释放资源等。注意这里没法使用request.write()方法。会报：RuntimeError: Cannot write() after finish()
        Returns:
        """
        # 发送交互DI
        try:
            del os.environ['productName']
        except:
            pass

        if look_for_single_global_config('SEND_DI_OR_EI_SWITCH')=='1' and (self.get_argument('userName',"") !=""):
            param= {
                "type":"BABJ.CIPAS.DATA.INTERACTIVE",
                "name":"CIPAS交互业务监视信息",
                "occur_time":str(self.occur_time),
                "fields":{
                    "SYSTEM": "CIPAS_NN",
                    "PRODUCT_NAME": self.productName,
                    "SYS_USER_NAME": self.get_argument('userName',""),
                    "MENU_NAME": self.get_argument('menuName',""),
                    "REQUEST_ID": self.serial_no,
                    "PROCESS_START_TIME": str(self.process_start_time),
                    "PROCESS_END_TIME": str(int(datetime.datetime.now().timestamp())*1000),
                    "PROCESS_STATE": "1",
                    "BUSINESS_STATE": "1",
                    "ERROR_INFO": ""
                }
            }
            if not judge_response_result(self.result):
                param['fields']['ERROR_INFO'] = str(self.result)
                param['fields']['BUSINESS_STATE'] = "0"
            params_list=[]
            params_list.append(param)
            logging.info("交互DI发送中，入参: %s" % json.dumps(params_list))
            req = requests.post(look_for_single_global_config('TJ_URL'), data=json.dumps(params_list), headers={'Content-Type': 'application/json'})
            logging.info("交互DI发送完毕，返回结果: %s" % req.json())  # 返回字节形式



        # 发送MQ消息去重启
        if self.needRouting=='1' and (look_for_single_global_config('CPCS_SERVICE_RESTART_SWITCH')=='1'):
            logging.info("特殊请求，需要重启该pod的CPCS服务。")

            # # 容器内部IP
            # CURRENT_IP = socket.gethostbyname(socket.gethostname())
            #
            # # 先做事务性Redis插入,插入接口重启的value
            # logging.info("需要事务性修改redis的key,如果修改失败表示当前有心跳重启。")
            # redis_client = get_redis_client(look_for_single_global_config('REDIS_IP'),
            #                                 look_for_single_global_config('REDIS_PORT'))
            # tran_result = transaction_set_order(redis_client, CURRENT_IP+'_CPCS_RESTRAT', 'INTERFACE_RESTART')
            # if tran_result:
            #     logging.info("发送重启消息至kafka")
            #     producer = CipasKafkaProducer("10.40.24.33", 9092, "CPCS_RESTART_SERVICE")
            #     producer.sendjsondata(CURRENT_IP)
            # else:
            #     logging.warning("事务修改redis的key失败,当前重启指令正在队列。")

            file_name = look_for_single_global_config('IS_HEALTHY_TXT')
            logging.info("修改健康信息is_healthy=%s至%s" % ('no', file_name))
            if os.path.exists(file_name):
                with open(file_name, mode='w', encoding='utf-8') as file:
                    file.write('is_healthy=no')
            logging.info("修改健康信息is_healthy成功，等待重启管理者处理")
        thread_local = threading.current_thread()
        del thread_local.request_id

    def _request_summary(self):
        """
        定义每次请求返回时的message格式
        Returns:
        """
        return "%s  [request_ip:%s] [serial_no:%s] [result: %s]" % (self.request.method,
                                      self.request.remote_ip,
                                      self.serial_no,self.result)

