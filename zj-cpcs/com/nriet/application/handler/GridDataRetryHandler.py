# coding=utf-8

from com.nriet.application.handler.Basehandler import BaseHandler
from com.nriet.core.dto.di.DIDto import DIDto
from com.nriet.utils.result.ResponseResultUtils import response_result_convert, build_response_dict
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
from com.nriet.utils.rabbitMQ.RabbitMQ import RabbitMQ
import logging
import time,uuid

import json
convert_switch = look_for_single_global_config('RESULT_FORMAT_TIANQIN_SWITCH')


class GridDataRetryHandler(BaseHandler):
    """
    CPCS服务处理类，暂不支持|方式命令
    """

    def prepare(self) -> None:
        """
        无论什么请求类型，每次请求前都会触发此方法
        Returns:

        """
        self.start_time = time.time()
        self.serial_no = str(uuid.uuid4())
        self.productName=None
        self.result = None
        CPCS = {key: self.get_argument(key) for key in self.request.arguments.keys()}
        self.needRouting = self.get_argument('needRouting', default=None)
        logging.info("CPCS触发格点补录。请求id: %s ,请求参数：%s" % (self.serial_no, CPCS))

    def post(self):
        """
        post请求 ,支持返回文件流
        :return:
        """

        logging.info("开始调用CPCS格点数据补录接口..")


        # 1.获取所有参数
        CPCS = {key: self.get_argument(key) for key in self.request.arguments.keys()}
        logging.info(CPCS)
        request_dict = eval(str(CPCS))

        # 1.1天镜格式下的日期，必须转化成真实的日期格式才行
        diDto = DIDto()
        timeType = CPCS.get('timeType').upper()
        timeRanges_tj = eval(request_dict['timeRanges'])
        request_dict['timeRanges'] = [int(diDto.convert_tj_date_to_cipas(time_tj, timeType)) for time_tj in
                                      timeRanges_tj]

        request_dict['isReput'] = 1
        if request_dict.get('elementInfo'):
            request_dict['elementInfo'] = eval(request_dict['elementInfo'])
        if request_dict.get('elementList'):
            request_dict['elementList'] = eval(request_dict['elementList'])

        # 2.发送消息至MQ
        mq = RabbitMQ('10.20.70.62', '5672', 'sea', 'sea', '/')  # 传入初始化参数
        mq.connect()  # 调用connect方法，连接broker

        message_str = json.dumps(request_dict)
        mq.put(message_str, "GRID_DATA_REPUT", "GRID_DATA_REPUT", "GRID_DATA_REPUT")


        # 3.构造响应并返回
        logging.info("结束调用CPCS格点数据补录接口..")
        result_dict = build_response_dict()
        result_dict = response_result_convert(result_dict, convert_switch)
        self.result = result_dict
        self.write(result_dict)
        self.finish()





if __name__ == '__main__':
    # 发送消息测试
    mq = RabbitMQ('10.20.70.62', '5672', 'sea', 'sea', '/')  # 传入初始化参数
    mq.connect()  # 调用connect方法，连接broker
    request_dict = {
        " isReput": 1,
        " dataCode": "K.0502.0001.S001",
        "timeType":"DAY",
        "elementList": ["tmp", "prate"],
        "timeRanges": [20210925, 20210926],
        "elementInfo": [{"ELEMENT_NAME": "tmp", "ELEMENT_NORMALNUM": "5124", "ELEMENT_ACTUALNUM": "500"},
                        {"ELEMENT_NAME": "tmax", "ELEMENT_NORMALNUM": "5124", "ELEMENT_ACTUALNUM": "5124"},
                        {"ELEMENT_NAME": "prate", "ELEMENT_NORMALNUM": "5124", "ELEMENT_ACTUALNUM": "4000"}
                        ]
    }
    # request_dict = {'makeupType': 'source', 'dataType': 'K.0502.0001.S001', 'makeupDate':'2021-07-13'}
    message_str = json.dumps(request_dict)
    # 调用put方法，向目标queue中发送数据， 第一个参数是data, 第二个参数是queue_name, 第三个参数是route_name
    # mq.put(message_str, "TJ_CIPAS_RECOUNT", "TJ_CIPAS_RECOUNT", "TJ_CIPAS_RECOUNT")
    mq.put(message_str, "GRID_DATA_REPUT", "GRID_DATA_REPUT", "GRID_DATA_REPUT")
