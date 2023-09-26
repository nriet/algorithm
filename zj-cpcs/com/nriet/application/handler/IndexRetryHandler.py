# coding=utf-8

from com.nriet.application.handler.Basehandler import BaseHandler
from com.nriet.core.MainEntrance import MainEntrance
from com.nriet.utils.result.ResponseResultUtils import response_result_convert
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
from com.nriet.utils.DateUtils import get_time_list
from com.nriet.core.dto.Time import Time
from com.nriet.core.dto.di.DIDto import DIDto
from com.nriet.utils.rabbitMQ.RabbitMQ import RabbitMQ
import logging, json, threading
import time, uuid

convert_switch = look_for_single_global_config('RESULT_FORMAT_TIANQIN_SWITCH')
from tornado import gen
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor


class IndexRetryHandler(BaseHandler):
    """
    CPCS服务处理类，暂不支持|方式命令
    """
    executor = ThreadPoolExecutor(4)

    def prepare(self) -> None:
        """
        无论什么请求类型，每次请求前都会触发此方法
        Returns:

        """
        self.start_time = time.time()
        self.serial_no = str(uuid.uuid4())
        thread_local = threading.current_thread()
        thread_local.request_id = self.serial_no
        self.productName = None
        self.result = None
        CPCS = {key: self.get_argument(key) for key in self.request.arguments.keys()}
        self.needRouting = self.get_argument('needRouting', default=None)
        logging.info("CPCS触发指数补录。请求id: %s ,请求参数：%s" % (self.serial_no, CPCS))

    @gen.coroutine
    def post(self):
        """
        post请求 ,支持返回文件流
        :return:
        """

        result_dict = yield self.doing()
        self.result = result_dict

        self.write(result_dict)
        self.set_header('cpcs_request_id', self.serial_no)
        self.flush()

    @run_on_executor
    def doing(self, *args, **kwargs):
        threading.current_thread().request_id = self.serial_no  # 不可删除，用于日志收集与处理

        # 1.获取所有参数，包含了definedField、prodDuty、dataDate、dateDate
        CPCS = {key: self.get_argument(key) for key in self.request.arguments.keys()}
        logging.info(CPCS)
        request_dict = eval(str(CPCS))
        request_dict['definedField'] = eval(request_dict['definedField'])
        request_dict['prodDuty'] = request_dict['prodDuty'].lower()
        request_dict['dataDate'] = ''.join(CPCS['dataDate'].split('-'))

        # 2.要把dataDate搞成 definedField字段中对应的值，非yyyy-mm-dd格式
        if request_dict['definedField']['timeType'].__contains__('#{prodDuty}'):
            request_dict['definedField']['timeType'] = request_dict['prodDuty']
        if request_dict['definedField']['timeType'] in ['day', 'five', 'ten']:
            pass
        elif request_dict['definedField']['timeType'] in ['pen', 'fiveYear']:
            five73_start_md = "0101,0106,0111,0116,0121,0126,0131,0205,0210,0215,0220,0225,0302,0307,0312,0317,0322,0327,0401,0406,0411,0416,0421,0426,0501,0506,0511,0516,0521,0526,0531,0605,0610,0615,0620,0625,0630,0705,0710,0715,0720,0725,0730,0804,0809,0814,0819,0824,0829,0903,0908,0913,0918,0923,0928,1003,1008,1013,1018,1023,1028,1102,1107,1112,1117,1122,1127,1202,1207,1212,1217,1222,1227"
            five73_start_list = five73_start_md.split(",")
            year = request_dict['dataDate'][:4]
            month_day = request_dict['dataDate'][4:]
            five73_index = five73_start_list.index(month_day) + 1
            five73_index = '0' + str(five73_index) if five73_index < 9 else str(five73_index)
            request_dict['dataDate'] = year + five73_index

        elif request_dict['definedField']['timeType'] in ['mon', 'month', 'sea', 'season']:
            request_dict['dataDate'] = request_dict['dataDate'][:6]
        elif request_dict['definedField']['timeType'] in ['year', 'yer']:
            request_dict['dataDate'] = request_dict['dataDate'][:4]

        # 3.如果有DBTimeType,那么dateDate需要根据timeType类型特殊处理。
        if request_dict['definedField'].get('DBtimeType'):
            if request_dict['definedField'].get('reportingTime'):
                # 直接为传进来的dateDate，不做任何特殊处理
                request_dict['dataDate'] = ''.join(CPCS['dataDate'].split('-'))
            else:
                db_start_day = Time(request_dict['dataDate'],
                                    request_dict['definedField'].get('DBtimeType').upper()).get_start()
                request_dict['dataDate'] = Time(db_start_day, 'DAY').convert(
                    request_dict['definedField'].get('timeType').upper()).get_time()

        for key, value in request_dict.items():
            if key == 'definedField':
                continue
            request_dict['definedField'][key] = value

        # 2.实例化MainEntrance,执行任务
        logging.info("开始调用CPCS指数补录接口..")
        main_entrance = MainEntrance(request_json=request_dict['definedField'])
        result_dict = main_entrance.execute()

        # 3.调用补算接口
        diDto = DIDto()
        timeType = request_dict['definedField']['timeType'].upper()
        if request_dict['definedField'].get('timeRanges'):  # 监测类型的指数
            timeRanges = request_dict['definedField']['timeRanges']

            time_list = get_time_list(timeRanges, timeType)
        elif (request_dict['definedField'].get('reportingTime')):  # 预测类型的指数
            time_list = [str(request_dict['definedField']['reportingTime'])]

        prodDuty = request_dict['definedField']['prodDuty'].upper()
        dataType = request_dict['definedField']['dataType']
        mq = RabbitMQ('10.20.70.62', '5672', 'sea', 'sea', '/')  # 传入初始化参数
        mq.connect()  # 调用connect方法，连接broker
        for time_index, time in enumerate(time_list):
            data_time = Time(value=time, time_type=timeType)
            # 先转成prodDuty对应的时间
            data_time = data_time.convert(prodDuty)
            data_time_recount = data_time.get_time()

            # 再转成di对应的标准格式 yyyy-mm-dd
            data_date, occur_time = diDto.build_data_date_and_occur_time(data_time_recount, prodDuty)
            data = {'makeupType': 'product', 'dataType': dataType, 'makeupDate': data_date}
            logging.info("发送消息来处理天镜补算业务")
            message_str = json.dumps(data)
            mq.put(message_str, "TJ_CIPAS_RECOUNT", "TJ_CIPAS_RECOUNT", "TJ_CIPAS_RECOUNT")

        # 4.返回格式转换
        logging.info("结束调用CPCS指数补录接口..  处理结果为: %s" % result_dict.__str__())
        result_dict = response_result_convert(result_dict, convert_switch)
        return result_dict
