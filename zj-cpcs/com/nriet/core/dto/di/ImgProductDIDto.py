# -*- coding:utf-8 -*-
# @Time : 2020/12/08
# @Author : huxin
# @File : ImgProductDIDto.py

from com.nriet.core.dto.di.DIDto import DIDto
import json,requests
IMG_PRODUCT_DI_TYPE = 'BABJ.CIPAS.DATA.DATAFLOW'
IMG_PRODUCT_EI_TYPE = ''

class ImgProductDIDto(DIDto):

    def __init__(self,type:str=None,name:str="CIPAS",message:str=None,occur_time:str=None,fields:dict=None,args=None):
        super().__init__(type=type, name=name, message=message, occur_time=occur_time,fields=fields)
        self.args = args[0].request_dict

    def send_di(self):
        if not self.args.get('data_type') or not self.args.get('time_type') :
            print("             None of data type or time type found for sending product di!")
            return

        self.type = IMG_PRODUCT_DI_TYPE
        args = self.args
        fields = self.fields
        output_img_name = args.get('output_img_name')
        output_img_type = args.get('output_img_type')

        #获取业务时次
        if args.get('reportingTime'):
            data_date=str(args.get('reportingTime'))
        elif args.get('timeRanges'):
            data_date=str(args.get('timeRanges')[1])
        #获取时间尺度（转换为大写）
        time_type = args.get('time_type').upper()

        # data_date转化为di所需要的的业务时次
        data_date, occur_time = self.build_data_date_and_occur_time(data_date, time_type)
        param = {"type": self.type,
                 "name": self.name,
                 "message": self.message,
                 "occur_time": occur_time,
                 "fields": fields
                 }

        fields['SYSTEM'] = 'CIPAS'



        fields['DATA_TYPE'] = args.get('data_type') # 图片产品的四级编码
        fields['PROD_DUTY'] = time_type  # 时间尺度
        fields['DATA_DATE'] = data_date #业务时次

        fields['RECEIVE'] = 'DPL'  # DPL表示调用者为产品加工流水线
        fields['SEND'] = 'STDB'  # 目标数据存储的标识名称。统计评估为STDB，其他加工可能有非结构
        fields["DATA_FLOW"] = "BDMAIN"  # BDMAIN:大数据平台主流程；

        fields["PROCESS_LINK"] = "3"  # 业务系统关键业务环节 1-数据获取，2-内部处理环节，多个时21、22…， 3-入库
        fields["PROCESS_START_TIME"] = ""  # 业务环节开始处理时间,毫秒级时间戳，可选
        fields["PROCESS_END_TIME"] = ""  # 业务环节结束处理时间，毫秒级时间戳，如果是入库环节，入库时间test_
        fields["PRODUCT_ACTUALNUM"] = "1"  # 实际生成的文件数,这里统一为1
        fields["PORDUCT_NORMALNUM"] = "1"  # 应该生成的文件数,这里统一为1
        fields["PROCESS_STATE"] = "1"  # 系统处理状态 1-正常，0-错误
        fields["ERROR_INFO"] = ""  # 算法异常/入库异常/……可选
        fields["BUSINESS_STATE"] = "1"  # 一般情况下，业务状态分为1-正常，0-错误；当需要考虑质控时，可能业务状态为1-正常，0-错误，3-可疑，4-缺测，待确认
        fields["PICTURE_NAME"] = '.'.join([output_img_name,output_img_type])
        param = [param]
        print("             Img product di request params: %s" % json.dumps(param))
        print()
        req = requests.post(self.url, data=json.dumps(param), headers={'Content-Type': 'application/json'})
        print("             Img product 'di response: %s" % req.json())  # 返回字节形式



    def send_ei(self):
        pass
