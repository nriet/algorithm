# -*- coding:utf-8 -*-
# @Time : 2020/12/08
# @Author : huxin
# @File : DIDto.py

from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
from com.nriet.core.dto.Time import Time
import datetime
import time

class DIDto():
    def __init__(self,type:str=None,name:str="CIPAS",message:str=None,occur_time:str=None,fields:dict=None):
        """
        构造DI/EI对象
        :param type:发送DI或者EI的天镜Type,用来标识发的是产品还是数据DI或者EI
        :param name: 此条DI/EI的名称，默认CIPAS
        :param message:透传的额外信息
        :param occur_time:业务时次的时间戳表达形式 13位！
        :param fields: 具体di/ei信息
        """
        self.type = type
        self.name = name
        if message is None:
            message=""
        self.message = message
        self.occur_time = occur_time

        if fields is None :
            fields ={}
        self.fields=fields
        self.url = look_for_single_global_config("TJ_URL")

    def send_di(self):
        pass

    def send_ei(self):
        pass

    def build_data_date_and_occur_time(self, data_date, time_type):
        data_time = Time(value=data_date, time_type=time_type)
        if time_type == "DAY":
            pass  # 没有必要特别处理
        elif time_type == "FIVE":
            data_date = data_time.get_time()
        elif time_type == "TEN":
            data_date = data_time.get_time()
        elif time_type == "WEEK":  # todo
            pass
        elif time_type == "MON":
            data_date = data_time.get_time() + "01"
        elif time_type == "SEASON":
            data_date = data_time.get_time() + "01"
        elif time_type == "YEAR":
            data_date = data_time.get_time() + "0101"
        #   统一转换为YYYY-MM-DD
        data_date = Time(value=data_date, time_type='DAY').obj.format("YYYY-MM-DD")
        if time_type in ['SEASON', 'YEAR']:
            occur_time = str(int(
                datetime.datetime.now().timestamp()) * 1000) # 季和年的业务时次通常超过3个月，天镜的es索引只保持3个月的。故这里的occur_time和实际触发时间有关。
        else:
            aaa = datetime.datetime.strptime(data_date, '%Y-%m-%d')+datetime.timedelta(minutes=10)
            occur_time = int(aaa.timestamp())*1000
        return data_date, occur_time

    def convert_tj_date_to_cipas(self, data_date, time_type):
        first_date = str(data_date)[:4] # yyyy-mm-dd
        second_date= str(data_date)[5:7]
        third_date = str(data_date)[8:]

        if time_type in ["DAY","FIVE","TEN"]:
            data_date = first_date+second_date+third_date
        elif time_type == "WEEK":  # todo
            pass
        elif time_type == "MON":
            data_date = first_date+second_date
        elif time_type == "SEASON":
            data_date = first_date+second_date
        elif time_type == "YEAR":
            data_date = first_date
        return data_date