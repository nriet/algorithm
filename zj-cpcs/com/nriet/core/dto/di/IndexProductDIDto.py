# -*- coding:utf-8 -*-
# @Time : 2020/12/08
# @Author : huxin
# @File : ImgProductDIDto.py

from com.nriet.core.dto.di.DIDto import DIDto
import json, requests, logging
from com.nriet.utils import DateUtils
import time,copy
IMG_PRODUCT_DI_TYPE = 'BABJ.CIPAS.DATA.DATAFLOW'
IMG_PRODUCT_EI_TYPE = ''
SYSTEM_NAME = 'CIPAS'


class IndexProductDIDto(DIDto):

    def __init__(self, type: str = IMG_PRODUCT_DI_TYPE, name: str = SYSTEM_NAME, message: str = "",
                 occur_time: str = None, product_normal_num: int = 1, product_actual_num: int = 1,
                 process_state: int = 1,bussiness_state: int = 1, fields: dict = None, args=None):
        super().__init__(type=type, name=name, message=message, occur_time=occur_time, fields=fields)
        self.args = args[0].__dict__
        self.product_normal_num = product_normal_num
        self.product_actual_num = product_actual_num
        self.process_state = process_state
        self.bussiness_state = bussiness_state

    def send_di(self):
        # 1.如果沒有JSON配置中沒有四級編碼或者沒有時間尺度，则默认不发送DI！
        if not self.args.get('data_type'):
            logging.info("             None of data type type found for sending product di!")
            return
        if not self.args.get('timeType'):
            logging.info("             None of time type found for sending product di!")
            return
        if self.args.get('productType')=='INDEX_PTEP':
            logging.warning("INDEX_PTEP SHOULD NOT BE MONITORED!")
            return

        # 2. DI的类型这里和发送图片产品类型一致
        args = self.args
        fields = self.fields

        # 3.获取时间尺度（转换为大写），优先用DBtimeType
        time_type = args.get('DBtimeType',None)
        if time_type is None :
            time_type = args.get('timeType')
        time_type = time_type.upper()
        
        
        time_ranges_fix = args.get('time_ranges',None)
        if not time_ranges_fix:
            time_ranges_fix = args.get('timeRanges', None)

        # 4. 获取业务时次，不管是监测指数还是预测指数，只要管起报就行
        if time_ranges_fix:
            # 4.1 计算需要发送多少条DI，因为有可能补录多条指数
            date_date_list = DateUtils.get_time_list(time_ranges_fix, time_type.lower())

            # 4.2 循环组装DI信息，因为可能一次批发多条DI
            params_list=[]
            for d_index,data_date in enumerate(date_date_list):
                # data_date转化为di所需要的的业务时次
                d_list = self.build_data_date_and_occur_time(date_date_list[d_index], time_type)

                # 每条DI的基本格式
                param = {"type": self.type,
                         "name": self.name,
                         "message": self.message,
                         "occur_time": d_list[1],
                         "fields": {}
                         }

                param['fields']['SYSTEM'] = self.name
                param['fields']['DATA_TYPE'] = args.get('data_type')  # 指数的四级编码
                param['fields']['PROD_DUTY'] = time_type  # 时间尺度
                param['fields']['DATA_DATE'] =  d_list[0]# 业务时次
                param['fields']['RECEIVE'] = 'DPL'  # DPL表示调用者为产品加工流水线
                param['fields']['SEND'] = 'STDB'  # 目标数据存储的标识名称。统计评估为STDB，其他加工可能有非结构
                param['fields']["DATA_FLOW"] = "BDMAIN"  # BDMAIN:大数据平台主流程；

                param['fields']["PROCESS_LINK"] = "3"  # 业务系统关键业务环节 1-数据获取，2-内部处理环节，多个时21、22…， 3-入库
                param['fields']["PROCESS_START_TIME"] = ""  # 业务环节开始处理时间,毫秒级时间戳，可选
                param['fields']["PROCESS_END_TIME"] = ""  # 业务环节结束处理时间，毫秒级时间戳，如果是入库环节，入库时间test_
                param['fields']["PRODUCT_ACTUALNUM"] = str(args.get('product_actual_num',self.product_actual_num))  # 实际生成的数据库条数
                param['fields']["PRODUCT_NORMALNUM"] = str(args.get('product_normal_num',self.product_normal_num))  # 应该生成的数据库条数
                param['fields']["PROCESS_STATE"] =str(self.process_state)  # 系统处理状态 1-正常，0-错误
                param['fields']["ERROR_INFO"] = self.message  # 算法异常/入库异常/……可选
                param['fields']["BUSINESS_STATE"] =str(self.process_state)  # 一般情况下，业务状态分为1-正常，0-错误；当需要考虑质控时，可能业务状态为1-正常，0-错误，3-可疑，4-缺测，待确认
                params_list.append(param)


            logging.info("             Index product di request params: %s" % json.dumps(params_list))
            req = requests.post(self.url, data=json.dumps(params_list), headers={'Content-Type': 'application/json'})
            logging.info("             Index product di response: %s" % req.json())  # 返回字节形式

    def send_ei(self):
        # 1.如果沒有JSON配置中沒有四級編碼或者沒有時間尺度，则默认不发送DI！
        if not self.args.get('data_type'):
            logging.warning("             None of data type type found for sending product di!")
            return
        if not self.args.get('timeType'):
            logging.warning("             None of time type found for sending product di!")
            return

        # 2. DI的类型这里和发送图片产品类型一致
        args = self.args
        fields = self.fields

        # 3.获取时间尺度（转换为大写）
        time_type = args.get('timeType').upper()

        # 4. 获取业务时次，不管是监测指数还是预测指数，只要管起报就行
        if args.get('timeRanges'):
            # 4.1 计算需要发送多少条DI，因为有可能补录多条指数


            # 4.2 循环组装DI信息，因为可能一次批发多条DI
            params_list = []
            for data_date in args.get('ret_list'): # 只会从差值日期列表中，挑选并发送DI
                # data_date转化为di所需要的的业务时次
                d_list = self.build_data_date_and_occur_time(data_date, time_type)

                # 每条DI的基本格式
                param = {"type": self.type,
                         "name": self.name,
                         "message": self.message,
                         "occur_time": d_list[1],
                         "fields": fields
                         }

                fields['SYSTEM'] = self.name
                fields['DATA_TYPE'] = args.get('data_type')  # 指数的四级编码
                fields['PROD_DUTY'] = time_type  # 时间尺度
                fields['DATA_DATE'] = d_list[0]  # 业务时次

                fields['RECEIVE'] = 'DPL'  # DPL表示调用者为产品加工流水线
                fields['SEND'] = 'STDB'  # 目标数据存储的标识名称。统计评估为STDB，其他加工可能有非结构
                fields["DATA_FLOW"] = "BDMAIN"  # BDMAIN:大数据平台主流程；

                fields["PROCESS_LINK"] = "3"  # 业务系统关键业务环节 1-数据获取，2-内部处理环节，多个时21、22…， 3-入库
                fields["PROCESS_START_TIME"] = ""  # 业务环节开始处理时间,毫秒级时间戳，可选
                fields["PROCESS_END_TIME"] = ""  # 业务环节结束处理时间，毫秒级时间戳，如果是入库环节，入库时间test_
                fields["PRODUCT_ACTUALNUM"] = str(args.get('product_actual_num',self.product_actual_num))  # 实际生成的数据库条数
                fields["PORDUCT_NORMALNUM"] = "0"  # 应该生成的数据库条数这里直接为0
                fields["PROCESS_STATE"] = str(self.process_state)  # 系统处理状态 1-正常，0-错误
                fields["ERROR_INFO"] = self.message  # 算法异常/入库异常/……可选
                fields["BUSINESS_STATE"] = str(args.get('bussiness_state',self.bussiness_state)) # 一般情况下，业务状态分为1-正常，0-错误；当需要考虑质控时，可能业务状态为1-正常，0-错误，3-可疑，4-缺测，待确认
                params_list.append(param)
            print("             Index product ei request params: %s" % json.dumps(params_list))
            req = requests.post(self.url, data=json.dumps(params_list), headers={'Content-Type': 'application/json'})
            print("             Index product ei response: %s" % req.json())  # 返回字节形式