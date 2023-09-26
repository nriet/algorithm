# -*- coding:utf-8 -*-
# @Time : 2020/12/07
# @Author : huxin
# @File : DIDecorator.py

import requests
import json
import logging
from com.nriet.utils.result.ResponseResultUtils import judge_response_result
from com.nriet.utils.proxyUtils import create_class_instance
from com.nriet.core.dto.Time import Time
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
#DI修饰器
def DI_decorater(type):
    def decorater(func):
        def call_fun(*args, **kwargs):
            try:
                class_name = str(type)+"DIDto"
                di_dto = create_class_instance('.'.join(['com.nriet.core.dto.di', class_name]), class_name,args=args)
                logging.info(*args)  # 这个是方法执行时的具体对象,对象的属性就有
                func_result = func(*args, **kwargs)

                # DI、EI受开关控制
                if int(look_for_single_global_config("SEND_DI_OR_EI_SWITCH")):
                    if judge_response_result(func_result):
                        di_dto.send_di()
                    else:
                        di_dto.send_ei()

            except Exception as e: # 如果算法执行过程中出现异常,先发送EI 再向上继续抛出此异常
                # DI、EI受开关控制
                if int(look_for_single_global_config("SEND_DI_OR_EI_SWITCH")):
                    di_dto.send_ei()
                raise e
            return func_result
        return call_fun
    return decorater



def send_product_DI():
    di = {}
    data_date = "20210116"
    data_date_time = Time(data_date,'DAY')
    param = {"type": "BABJ.CIPAS.DATA.DATAFLOW",
             "name": "CIPAS",
             "message": "123",
             "occur_time":str((data_date_time.obj.shift(minutes=1).timestamp)*1000),
             "fields": di
             }


    di['SYSTEM']= 'CIPAS'
    di['DATA_TYPE']="C.0017.0007.S002"
    di['PROD_DUTY']= "3" #1：分钟；2：小时；3：日；4：中国候；5：世界候；6：旬；7：月；8：季；9：年
    di['DATA_DATE']= data_date_time.obj.format("YYYY-MM-DD") #

    # 疑惑字段
    di['RECEIVE'] = 'DPL'  # DPL表示调用者为产品加工流水线
    di['SEND']='STDB' #目标数据存储的标识名称。统计评估为STDB，其他加工可能有非结构
    di["DATA_FLOW"] = "BDMAIN" #BDMAIN:大数据平台主流程；

    di["PROCESS_LINK"] = "3" #业务系统关键业务环节 1-数据获取，2-内部处理环节，多个时21、22…， 3-入库
    di["PROCESS_START_TIME"] = "" #业务环节开始处理时间,毫秒级时间戳，可选
    di["PROCESS_END_TIME"] = "" #业务环节结束处理时间，毫秒级时间戳，如果是入库环节，入库时间test_
    di["PRODUCT_ACTUALNUM"] = "1" #实际生成的文件数,这里统一为1
    di["PORDUCT_NORMALNUM"] = "1" #应该生成的文件数,这里根据实际业务决定
    di["PROCESS_STATE"] = "1" #系统处理状态 1-正常，0-错误
    di["ERROR_INFO"] = "" #算法异常/入库异常/……可选
    di["BUSINESS_STATE"] = "1" #一般情况下，业务状态分为1-正常，0-错误；当需要考虑质控时，可能业务状态为1-正常，0-错误，3-可疑，4-缺测，待确认
    di["PICTURE_NAME"] = "TEST_MOP_CHCC_EPEWF_AIRDIST_PM10_CHAQMONI_CH_DAY_0000_PB_20201204-20201204_SK.png"
    param  = [param]
    url='http://smart-view.nmic.cma/store/openapi/v2/logs/push_batch?apikey=e10adc3949ba59abbe56e057f2gg88dd'
    url='http://10.20.64.78/store/openapi/v2/logs/push_batch?apikey=e10adc3949ba59abbe56e057f2gg88dd'
    logging.info("url: %s" % url)
    logging.info()
    logging.info("di request params: %s" % json.dumps(param))
    logging.info()
    req = requests.post(url, data=json.dumps(param), headers={'Content-Type': 'application/json'})
    logging.info("di response: %s" % req.json())  # 返回字节形式

def send_data_DI():
    di = {}
    data_date = "20201215"
    data_date_time = Time(data_date,'DAY')
    param = {"type": "RT.DPC.STATION.DI",
             "name": "美国气象环境预报中心预报模式CFS",
             "message": "123",
             "occur_time":str((data_date_time.obj.shift(minutes=1).timestamp)*1000),
             "fields": di
             }

    di['SYSTEM'] = 'CIPAS_NN'  # 南京十四所
    di['DATA_TYPE']="K.0786.0001.R001" # 解码入库的四级编码R001
    di['DATA_TYPE_1']="" # 源文件的四级编码,不一定
    di['DATA_DATE']= data_date_time.obj.format("YYYY-MM-DD") #
    di['PROD_DUTY'] = 'DAY'


    # 疑惑字段
    di['RECEIVE'] = 'NCC'  # 资料来源
    di['SEND']='STDB' # 目标数据存储的标识名称。统计评估为STDB，其他加工可能有非结构
    di["DATA_FLOW"] ="BDMAIN" #BDMAIN:大数据平台主流程；
    di["PROCESS_LINK"] = "3"  # 业务系统关键业务环节 1-数据获取，2-内部处理环节，多个时21、22…， 3-入库

    di["PROCESS_START_TIME"] = "" #业务环节开始处理时间,毫秒级时间戳，可选
    di["PROCESS_END_TIME"] = "" #业务环节结束处理时间，毫秒级时间戳，如果是入库环节，入库时间test_
    di["FILE_NAME_O"] = "美国气象环境预报中心预报模式GFS" #源文件名

    di["RECORD_ACTUALNUM"] = "1" #实际生成的文件数,这里统一为1
    di["RECORD_NORMALNUM"] = "1" #应该生成的文件数,这里根据实际业务决定
    di["PROCESS_STATE"] = "1" #系统处理状态 1-正常，0-错误
    di["BUSINESS_STATE"] = "1" #一般情况下，业务状态分为1-正常，0-错误；当需要考虑质控时，可能业务状态为1-正常，0-错误，3-可疑，4-缺测，待确认

    param  = [param]
    url='http://smart-view.nmic.cma/store/openapi/v2/logs/push_batch?apikey=e10adc3949ba59abbe56e057f2gg88dd'
    url='http://10.20.64.78/store/openapi/v2/logs/push_batch?apikey=e10adc3949ba59abbe56e057f2gg88dd'
    logging.info("url: %s" % url)
    logging.info()
    logging.info("di request params: %s" % json.dumps(param))
    logging.info()
    req = requests.post(url, data=json.dumps(param), headers={'Content-Type': 'application/json'})
    logging.info("di response: %s" % req.json())  # 返回字节形式



# send_product_DI()
# send_data_DI()