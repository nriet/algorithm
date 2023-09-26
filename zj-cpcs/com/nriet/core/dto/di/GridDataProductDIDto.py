# -*- coding:utf-8 -*-
# @Time : 2020/12/08
# @Author : huxin
# @File : GridDataProductDIDto.py

from com.nriet.core.dto.di.DIDto import DIDto
import json, requests, logging
from com.nriet.config.dataConfig.DataCodeConfig import data_code_config
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import PARAMETER_VALUE_MISSING_CODE, PARAMETER_VALUE_MISSING_MSG

GRID_DATA_PRODUCT_DI_TYPE = 'RT.DPC.STATION.DI'
GRID_DATA_PRODUCT_EI_TYPE = ''

"""
此脚本专用于发送格点数据入空间库的DI接口
"""


class GridDataProductDIDto(DIDto):

    def __init__(self, type: str = None, name: str = "CIPAS", message: str = None, occur_time: str = None,
                 fields: dict = None, args=None):
        super().__init__(type=type, name=name, message=message, occur_time=occur_time, fields=fields)
        self.args = args[0]

    def send_di(self):
        args = self.args.__dict__

        self.type = GRID_DATA_PRODUCT_DI_TYPE
        self.data_code = args.get('data_code')

        # 加载该四级编码对应数据的相关其他信息，进行正确性校验
        data_config_dict = data_code_config.get(self.data_code)
        if (not data_config_dict) or (not {"name","data_type"}.issubset(data_config_dict)):
            raise AlgorithmException(response_code=PARAMETER_VALUE_MISSING_CODE,
                                     response_msg=PARAMETER_VALUE_MISSING_MSG)

        self.name = data_config_dict.get('name')
        fields = self.fields

        # 获取业务时次
        if args.get('reportingTime'):
            data_date = str(args.get('reportingTime'))
        elif args.get('timeRanges'):
            data_date = str(args.get('timeRanges')[1])
        # 获取时间尺度（转换为大写）
        time_type = args.get('timeType').upper()

        # data_date转化为di所需要的的业务时次
        data_date, occur_time = self.build_data_date_and_occur_time(data_date, time_type)

        actual_num = str(args.get('actual_num', "0"))
        norm_num = str(args.get('norm_num', "1"))

        param = {"type": self.type,
                 "name": self.name,
                 "message": self.message,
                 "occur_time": occur_time,
                 "fields": fields
                 }

        fields['SYSTEM'] = 'CIPAS_NN'  # CIPAS_NN:南京十四所
        fields['DATA_TYPE'] = data_config_dict.get('data_type')  # 解码入库的四级编码
        fields['DATA_TYPE_1'] = data_config_dict.get('data_type_1', "")  # 源文件的四级编码,不一定

        fields['DATA_DATE'] = data_date  # 业务时次
        fields['PROD_DUTY'] = time_type

        fields['RECEIVE'] = 'NCC'  # DPL表示调用者为产品加工流水线
        fields['SEND'] = 'STDB'  # 目标数据存储的标识名称。统计评估为STDB，其他加工可能有非结构
        fields["DATA_FLOW"] = "BDMAIN"  # BDMAIN:大数据平台主流程；
        fields["PROCESS_LINK"] = "3"  # 业务系统关键业务环节 1-数据获取，2-内部处理环节，多个时21、22…， 3-入库

        fields["PROCESS_START_TIME"] = ""  # 业务环节开始处理时间,毫秒级时间戳，可选
        fields["PROCESS_END_TIME"] = ""  # 业务环节结束处理时间，毫秒级时间戳，如果是入库环节，入库时间test_
        fields["FILE_NAME_O"] = self.name  # 源文件名

        fields["RECORD_ACTUALNUM"] = actual_num  # 实际生成的文件数,这里统一为1
        fields["RECORD_NORMALNUM"] = norm_num  # 应该生成的文件数,这里根据实际业务决定
        fields["PROCESS_STATE"] = "1"  # 系统处理状态 1-正常，0-错误
        fields["BUSINESS_STATE"] = "1" if actual_num == norm_num else "4" # 一般情况下，业务状态分为1-正常，0-错误；当需要考虑质控时，可能业务状态为1-正常，0-错误，3-可疑，4-缺测，待确认

        factor_info_dict = args.get("factor_info")
        FACTOR_LIST =[]

        # 组装要素入库详情信息
        for key,value in factor_info_dict.items():
            FACTOR_LIST.append({'ELEMENT_NAME':key,'ELEMENT_NORMALNUM':value[0],'ELEMENT_ACTUALNUM':value[1]})
        fields['ELEMENT_INFO'] = FACTOR_LIST


        param = [param]

        print("             Grid data di request params: %s" % json.dumps(param))
        req = requests.post(self.url, data=json.dumps(param), headers={'Content-Type': 'application/json'})
        print("             Grid data di response: %s" % req.json())  # 返回字节形式
    def send_ei(self):
        pass
