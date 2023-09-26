#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2019/10/30
# @Author : xulh
# @File : WorkFlowDto.py

import ast, re
import os

# 工具类
from com.nriet.config.AreaCodeConfig import area_code_dict
from com.nriet.config.DataSourceConfig import data_source_dict
from com.nriet.config.PathConfig import WORK_FLOW_STORE, BUS_PARAMS_STORE,INTERACT_SAVE_PATH
from com.nriet.utils import DateUtils
from com.nriet.utils.DateUtils import strToDate, dateToStr
from com.nriet.utils.TimeRangeUtils import formatter_time_range
from com.nriet.utils.colorTool import getColorValueDef, getColorMap
from com.nriet.utils.fileUtils import readJson
from com.nriet.utils.StrSequenceConvertUtils import str_to_sequence
from com.nriet.utils.exception.workFlow.WorkFlowException import WorkFlowException
from com.nriet.config.ResponseCodeAndMsgEum import JSON_FORMAT_ERROR_CODE,FILE_NOT_FOUND_ERROR_CODE

from com.nriet.core.dto.Time import Time
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
import importlib,sys,io
importlib.reload(sys)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import traceback,logging
class WorkFlowDto:
    local_params = {}

    def __init__(self, local_params):
        logging.info("     WorkFlowDto  processing init method ")

        # 0.解决服务接口运行代码时的缓存问题，用的字段
        self.needRouting='0'

        # 1. 页面参数的预处理流程
        logging.info("     WorkFlowDto  processing  pre_local_params_convert method ")
        self.pre_local_params_convert(local_params)

        # 2. 解析转换json
        logging.info("     WorkFlowDto  processing  resolveParam method ")
        self.resolveParam()

        # 3.各算法输出结果存放队列
        self.tmp_data_queue = []



    def pre_local_params_convert(self, local_params):
        '''
        页面参数的预处理环节，因为页面传递过来的参数不一定是具体的值，有可能包含通配符
        :param local_params: 页面参数
        '''
        # 1.替换通配符
        logging.info("         pre_local_params_convert processing replace_local_params_symbols method ")
        self.replace_local_params_symbols(local_params)

        # 2. timeRanges字段的特殊处理
        logging.info("         pre_local_params_convert processing special_fields_handle method ")
        self.special_fields_handle(local_params, ['timeRanges', 'forecastPeriod','yearList','yearTimeRange'])
        #logging.info(local_params)

        # 3.页面参数重新赋值
        self.local_params = local_params

    def replace_local_params_symbols(self, local_params):
        for key, value in local_params.items():
            if isinstance(value, str):
                regex_key_list = re.findall("#{(.*?)}", value)
                if regex_key_list:  # 如果有通配符的
                    for regex_key in regex_key_list:
                        value =value.replace('#{' + regex_key + '}', local_params[regex_key])
                        local_params[key] =value

            elif isinstance(value, list):
                for index, val in enumerate(value):
                    if isinstance(val, str):
                        regex_key_list = re.findall("#{(.*?)}", val)
                        if regex_key_list:  # 如果有通配符的
                            for regex_key in regex_key_list:
                                val = val.replace('#{' + regex_key + '}', local_params[regex_key])
                            local_params[key][index] = val
            else:  # 页面参数目前只有字符串和list类型,其他类型暂不做处理
                continue

    def special_fields_handle(self, local_params, special_fields):

        for field in special_fields:
            if not local_params.get(field):
                continue
            #字符串数组/字典转成 真正的数组/字典！
            if not field in ['levels']:
                local_params[field] = str_to_sequence(local_params[field])

            if not field in ['timeRanges', 'forecastPeriod']:
                continue

            for index, time_range in enumerate(local_params[field]):

                if not isinstance(time_range, int) :
                    time = None
                    for handle_index, handle_type in enumerate(time_range.split(";")):
                        # 首个字符串必然做Time实例化
                        if handle_index == 0:
                            time_type = local_params['timeType']
                            if local_params.get('timeConvertType'):
                                time_type = local_params.get('timeConvertType')
                            # 未来几周的 1,2,3,4 不做时间推送  跳过
                            if len(handle_type)<4:
                                continue
                            time = Time(handle_type, time_type.upper())
                            # 如果当前的handle_index有且只有一个，那么直接更新
                            local_params[field][index] = int(time.value)
                            continue

                        method_name = handle_type.split(".")[0]
                        method_params = handle_type.split('.')[1:]
                        # 如果不是最后一个
                        if handle_index != len(time_range.split(";")) - 1:
                            if method_params:
                                time = getattr(time, method_name)(*method_params)
                            else:
                                time = getattr(time, method_name)()
                        else:  # 最后一个必然是以get_time,get_end,get_start方法结尾                          
                            local_params[field][index] = int(getattr(time, method_name)())

    def getParam(self, param):
        if self.hasKey(param):
            return self.local_params[param]
        else:
            return ""

    def setParam(self, paramName, value):

        self.local_params[paramName] = value

    def hasKey(self, param):
        for key in self.local_params.keys():
            if key == param:
                return True
        return False

    def resolveParam(self):

        # 1.解析转换参数，封装到LocalParamter对象去，包含了绘图参数和其他流程参数
        logging.info("         resolveParam processing convert_and_parse_params method")
        self.convert_and_parse_params()

        # 2.整合待处理数据的具体路径，文件名称
        logging.info("         resolveParam processing query_data_input_path method")
        self.query_data_input_path()

        # 3.加载具体的流程链
        self.setParam("work_flow_path",
                      os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + WORK_FLOW_STORE + self.local_params[
                          "work_flow_id"] + ".json")
        # logging.info("         Local params is: %s" % json.dumps(self.local_params,ensure_ascii=False))

    def convert_and_parse_params(self):
        '''
        解析、拼接并转换业务和流程参数，实现通配符替换，最终封装到localParamsDto
        :return:
        '''
        # 1.根据buss_id寻找对应的业务参数配置，并加载
        paramFile = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + BUS_PARAMS_STORE + self.local_params[
            "bussId"] + ".json"
        try:
            bussiness_params = readJson(paramFile)
        except json.decoder.JSONDecodeError:
            raise WorkFlowException(response_code=JSON_FORMAT_ERROR_CODE,response_msg="%s format error !!" % paramFile)
        except :
            logging.error(traceback.format_exc())
            raise WorkFlowException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg="%s not found !!" % paramFile)

        # 2.把每项业务参数，传递到localParams里
        for item in bussiness_params.items():
            self.setParam(item[0], item[1])

        # 3.获取所有子流程的参数
        work_flow_params = self.getParam("work_flow_params")
        is_interact = self.getParam('isInteract')
        saveToNfsshare=self.getParam('saveToNfsshare')
        saveToObs=self.getParam('saveToObs')

        # 4.所有子流程参数，通配符替换
        '''
        20200410 胡昕改造，增加对json工具生成的json额外处理.
        对于method_params和subflow_inputdaa_indexes的多余”“处理
        '''
        for i, wfp in enumerate(work_flow_params):
            # 4.1 method_params的处理
            method_params = wfp.get("method_params")
            for method_param in method_params:
                # method_params 代码健壮性处理
                for alg_key, alg_value in method_param.items():
                    if alg_key in ['levels','regions','saveType',"whetherMakeup","ltm"]:
                        continue

                    method_param[alg_key] = str_to_sequence(alg_value)

                # subflow_inputdata_indexes 代码健壮性处理
                subflow_inputdata_indexes = wfp.get("subflow_inputdata_indexes")
                for alg_index, alg_data_indexes in enumerate(subflow_inputdata_indexes):
                    subflow_inputdata_indexes[alg_index] = str_to_sequence(alg_data_indexes)


        for i, wfp in enumerate(work_flow_params):
            # 4.1 method_params的处理

            method_params = wfp.get("method_params")
            # logging.info(method_params)
            for method_param in method_params:
                # # 空间库调用日志打印 特殊处理
                # if "spaceSwich" in  method_param.keys():
                #     spaceSwich = method_param.get("spaceSwich")
                #     # 110-120°E平均降水演变监测模块
                #     if spaceSwich == "MYRAINCFSV2":
                #         spaceurl = "http://10.40.16.42/data/postgre/getGridData?dataCode=F.0061.0002.R001&area=110%2C120%2C10%2C60&element=pre&validTimeRange=%5B20220924%2C+20221106%5D&timeRange=%5B2022092320%2C+2022092320%5D&ensNo=%5B-1%2C+-1%5D&calOperation=%2A%3A21600&dimOperation=time%3Aavg%2CensNo%3Aavg%2Clon%3Aavg"
                #     # 110-120°E平均气温演变监测模块
                #     if spaceSwich == "MYTEMPCFSV2":
                #         spaceurl = "http://10.40.16.42/data/postgre/getGridData?dataCode=F.0061.0002.R001&area=110%2C120%2C10%2C60&element=tmp&validTimeRange=%5B20220924%2C+20221106%5D&timeRange=%5B2022092320%2C+2022092320%5D&ensNo=%5B-1%2C+-1%5D&calOperation=-%3A273.15&dimOperation=time%3Aavg%2CensNo%3Aavg%2Clon%3Aavg"
                #     # PDO海温模态指数监测模块
                #     if spaceSwich == "PDOSST":
                #         spaceurl = "http://10.40.16.42/data/postgre/getGridData?timeRange=%5B202207%2C+202207%5D&area=110%2C260%2C20%2C70&calOperation=Anomaly%3A1991&dimOperation=time%3Aavg&dataCode=C.0013.0008.R004&element=sst"
                #     # IOBW指数监测模块
                #     if spaceSwich == "IOBWOISST":
                #         spaceurl = "http://10.40.16.42/data/postgre/getGridData?timeRange=%5B202208%2C+202208%5D&area=10%2C140%2C-40%2C40&calOperation=Anomaly%3A1991&dimOperation=time%3Aavg&dataCode=C.0013.0006.S002&element=oisst"
                #     # 北大西洋NAT指数-固定区域监测模块
                #     if spaceSwich == "NATGDQY":
                #         spaceurl = "http://10.40.16.42/data/postgre/getGridData?timeRange=%5B202208%2C+202208%5D&area=280%2C360%2C0%2C60&calOperation=Anomaly%3A1991&dimOperation=time%3Aavg&dataCode=C.0013.0006.S002&element=oisst"
                #     # 115-145°E平均500Pa副高脊线位置演变监测模块
                #     if spaceSwich == "FGJXYB":
                #         spaceurl = "http://10.40.16.42/data/postgre/getGridData?dataCode=F.0070.0001.S001&area=90%2C180%2C0%2C60&element=hgt&timeRange=%5B20220823%2C+20220922%5D&level=%5B500.0%2C+500.0%5D&dimOperation=level%3Aavg%2Ctime%3Aavg"
                #     # 北极涛动指数监测模块
                #     if spaceSwich == "BJTD":
                #         spaceurl = "http://10.40.16.42/data/postgre/getGridData?dataCode=F.0070.0001.S001&element=air&timeRange=%5B20220823%2C+20220922%5D&level=%5B10.0%2C+1000.0%5D&calOperation=-%3A273.15&dimOperation=level%3Aavg%2Ctime%3Aavg"
                #     logging.info("             " + spaceurl)

                data_output_params = method_param.get("data_output_params")
                if not data_output_params:
                    if "outPutName" in method_param:
                        method_param["saveToNfsshare"]=saveToNfsshare in ['1',1,True]
                        method_param["saveToObs"] = saveToObs in ['1', 1, True]
                    for key, value in method_param.items():
                        # 替换数据输出路径及文件名中的timeType
                        if isinstance(value, str) and key in ["outPutPath", "outPutName", "productPath", "productId"]:
                            value = value.replace("#{timeType}", self.getParam("timeType").upper())
                            if value.__contains__("#{levels}"):
                                level = self.format_levels(key)
                                value = value.replace("#{levels}", level)
                        if isinstance(value, str):
                            value = self.format_tpf(value)
                        # timeRanges 处理
                        if isinstance(value, str) and value.__contains__("@"):
                            value = self.format_time_ranges(value)
                        # areaCode 处理
                        if isinstance(value, str) and value.__contains__("%"):
                            value = self.area_code_format(value)

                        # outPutPath 交互处理
                        if key =='outPutPath' and (is_interact == "1"):
                            value = INTERACT_SAVE_PATH+datetime.strftime(datetime.today(),"%Y%m%d")+"/"
                        method_param[key] = value
                else:

                    level = self.format_levels("")
                    if method_param.get("iniPath"):
                        ini_path = method_param.get("iniPath").replace("#{levels}", level)
                    for output_param in data_output_params:
                        #5.0 json工具兼容处理

                        for alg_key, alg_value in output_param.items():
                            output_param[alg_key] = str_to_sequence(alg_value)

                        for layer_index, layer_dict in enumerate(output_param.get('layers')):
                            for layer_key, layer_value in layer_dict.items():
                                if layer_key in ['draw_regions']:
                                    continue
                                layer_dict[layer_key] = str_to_sequence(layer_value)


                        for item in output_param.items():
                            key, value = item[0:2]
                            if isinstance(value, str) and value.__contains__("#{timeType}"):
                                value = value.replace("#{timeType}", self.getParam("timeType").upper())
                            if isinstance(value, str) and value.__contains__("#{levels}"):
                                level = self.format_levels(key)
                                value = value.replace("#{levels}", level)
                            if isinstance(value, str):
                                value = self.format_tpf(value)
                            if isinstance(value, str) and value.__contains__("@"):
                                value = self.format_time_ranges(value)
                            if isinstance(value, str) and value.__contains__("%"):
                                # value 不以%结尾
                                if not value.endswith("%"):
                                    value = self.area_code_format(value)

                            if key == 'output_img_path' and (is_interact == "1"):
                                value = INTERACT_SAVE_PATH+datetime.strftime(datetime.today(),"%Y%m%d")+"/"

                            if key in ['output_img_name','output_img_type','output_img_path']:
                                self.local_params[key] = value

                            if key == "sub_titles":
                                sub_titles = []
                                for sub_title in output_param.get(key):
                                    # EC逐周日期标题显示调整
                                    if sub_title.find("forecastPeriodExt") != -1:
                                        startWeekday = DateUtils.day2Week(self.getParam("reportingTime"),self.getParam("forecastPeriod")[0])[0]
                                        endWeekday = DateUtils.day2Week(self.getParam("reportingTime"),self.getParam("forecastPeriod")[1])[1]
                                        self.local_params["forecastPeriodExt"]=[startWeekday,endWeekday]
                                    # 通配符处理
                                    sub_title = self.format_tpf(sub_title)
                                    # timeRanges处理
                                    if isinstance(sub_title, str) and sub_title.__contains__("@"):
                                        sub_title = self.format_time_ranges(sub_title)
                                    # 合成分析特殊处理
                                    if self.hasKey("yearList") and self.hasKey("yearTimeRange"):
                                        year_time_start, year_time_end = self.getParam("yearTimeRange")
                                        year_time_start = "0"+str(year_time_start) if int(year_time_start)<10 else str(year_time_start)
                                        year_time_end = "0"+str(year_time_end) if int(year_time_end)<10 else str(year_time_end)
                                        if year_time_start == year_time_end:
                                            sub_title = ",".join([str(year) for year in self.getParam(
                                                "yearList")]) + "年 " + year_time_start + "月"
                                        elif year_time_start == "01" and year_time_end == "12":
                                            sub_title = ",".join(
                                                [str(year) for year in self.getParam("yearList")]) + "年"
                                        else:
                                            sub_title = ",".join([str(year) for year in self.getParam(
                                                "yearList")]) + "年 " + year_time_start + "-" + year_time_end + "月"
                                    sub_titles.append(sub_title)
                                value = sub_titles

                            if key == "layers":
                                for layer in output_param.get(key):

                                    if layer.get("data_source"):
                                        # 英文版特殊处理，胡玉恒添加 2020.10.12
                                        if "DataSource" in layer["data_source"]:
                                            layer["data_source"] = layer["data_source"].replace("#{dataSource}",self.getParam("dataSource"))
                                        else:
                                            layer["data_source"] = "数据：" + layer["data_source"].replace("#{dataSource}",self.getParam("dataSource"))
                                    if method_param.get("iniPath") and not layer.get("noUseIniPath"):
                                        layer["intervals"] = getColorValueDef(ini_path).tolist()
                                        # layer["colors"] = getColorMap(ini_path).tolist() if not layer.get("colors") else layer.get("colors")
                                        layer["colors"] = getColorMap(ini_path).tolist()

                                    if layer.get('note'):
                                        layer['note'] = layer.get('note').replace("#{ltm}", self.getParam('ltm'))

                                    if layer.get("rectangle_list") and layer.get("rectangle_list").__contains__("%"):
                                        layer['rectangle_list']= self.area_code_format(layer.get("rectangle_list"))
                                    if layer.get("draw_regions") and layer.get("draw_regions").__contains__("%"):
                                        layer['draw_regions']= self.area_code_format(layer.get("draw_regions"))
                                    # 序列图图例标签替换常年值
                                    if layer.get('labelName'):
                                        tmpvalue =  layer['labelName']
                                        tmpvalue = tmpvalue.replace("#{ltm}",self.getParam('ltm'))
                                        if isinstance(tmpvalue, str) and tmpvalue.__contains__("%"):
                                            tmpvalue = self.data_source_format(tmpvalue)
                                        layer['labelName'] =tmpvalue
                                layers_str = json.dumps(output_param.get(key))

                                for cache_field in ['map_masking_areas','map_masking_areas','RasterFill','contourLine','hemisphere','vector','cnLine']:
                                    if cache_field in layers_str:
                                        logging.info("              Find cache risk! Add needRouting=1 into WorkFlowDto")
                                        self.needRouting = '1'
                            # 省界线 ，需要重启服务
                            if key in ["isProvince"]:
                                logging.info("              Find cache risk! Add needRouting=1 into WorkFlowDto")
                                self.needRouting = '1'

                            if key =="line_values":
                                for line_index,line_value in enumerate(value):
                                    if isinstance(line_value, str) and line_value.__contains__("@"):
                                        value[line_index]=self.format_time_ranges(line_value)

                            #分割线替换占位字符
                            if key =="split_lines":
                                for split_line_index,split_line_value in enumerate(value):
                                    if isinstance(split_line_value, str):
                                        value[split_line_index]=self.format_tpf(split_line_value)
                            output_param[key] = value


                        if saveToNfsshare:
                            output_param['saveToNfsshare']=saveToNfsshare in ['1', 1, True]
                        if saveToObs:
                            output_param['saveToObs']=saveToObs in ['1', 1, True]

    def query_data_input_path(self):
        for sub_work_flow in self.getParam("work_flow_params"):
            method_params = sub_work_flow.get("method_params")
            for method_param in method_params:
                element = method_param.get("elements")
                if method_param.keys().__contains__("dataInputPaths"):
                    # 1.更新源数据存放路径

                    self.data_path_update(element, method_param)
                    dataInputName = []
                    # 2.获取数据文件列表
                    if method_param.get("timeRanges") and method_param.get("timeType") and (
                            not method_param.get("dataInputPaths").__contains__("ltm")):

                        timeTypes = method_param.get("timeType")
                        timeRanges = method_param.get("timeRanges")
                        if timeTypes == "day":
                            # 开始时间
                            start_time = strToDate(str(timeRanges[0]), "%Y%m%d")
                            # 结束时间
                            end_time = strToDate(str(timeRanges[1]), "%Y%m%d")
                            yer = end_time.year - start_time.year
                            mon = end_time.month - start_time.month
                            mon = yer * 12 + mon
                            for i in range(mon + 1):
                                dataInputName.append(dateToStr(start_time, "%Y_%m"))
                                if start_time.month == 12:
                                    start_time = start_time.replace(year=start_time.year + 1, month=1)
                                else:
                                    start_time = start_time+ relativedelta(months=1)
                        else:
                            start_time = str(timeRanges[0])[0:4]
                            end_time = str(timeRanges[1])[0:4]
                            if start_time == end_time:
                                dataInputName.append(start_time)
                            else:
                                t = int(end_time) - int(start_time)
                                for i in range(t + 1):
                                    dataInputName.append(int(start_time) + i)
                    else:
                        timeRanges = method_param.get("timeRanges")
                        if timeRanges:
                            start_time = str(timeRanges[0])[0:4]
                            end_time = str(timeRanges[1])[0:4]
                            if start_time == end_time:
                                dataInputName.append("")
                            else:
                                t = int(end_time) - int(start_time)
                                for i in range(t + 1):
                                    dataInputName.append("")
                    method_param["dataInputName"] = dataInputName
                method_param["elements"] = element

    def data_path_update(self, element, sub_work_flow):

        timeType = sub_work_flow.get("timeType")
        if timeType:
            sub_work_flow["dataInputPaths"] = \
                sub_work_flow["dataInputPaths"].replace("#{timeType}", timeType)
            if element == "oisst" and (timeType in ["day", "five"]):
                element = "sst"

            if sub_work_flow.get("ltmDataInputPaths"):
                sub_work_flow["jpDataInputPaths"] = sub_work_flow.get("ltmDataInputPaths")
                sub_work_flow["jpDataInputName"] = timeType + "_1981-2010.nc"

    def format_levels(self, key):
        levels = self.getParam("levels")

        if levels:
            level_start, level_end = levels.split(",")
            if key == "main_title":
                return level_start

            return level_start.zfill(4)
        return levels

    def format_time_ranges(self, value):
        value_list = value.split("@")
        for value_index, vl in enumerate(value_list):
            if value_index % 2 != 0 and value_index != len(value_list):
                time = vl.split("_")[-1]
                # timeRanges = self.getParam("timeRanges")
                timeRanges = self.getParam(time)
                time_type = self.getParam("timeType")
                if not isinstance(timeRanges, list):
                    timeRanges = [timeRanges, timeRanges]
                value_list[value_index] = formatter_time_range(timeRanges, time_type + "_" + vl)
        value = "".join(value_list)
        return value

    # 通配符处理
    def format_tpf(self, value):
        regex_key_list = re.findall("#{(.+?)}", value)
        if regex_key_list:  # 如果有通配符的
            for regex_key in regex_key_list:
                if isinstance(self.getParam(regex_key), str):
                    value = value.replace('#{' + regex_key + '}', self.getParam(regex_key))
                else:
                    value = self.getParam(regex_key)
        return value

    def area_code_format(self,value):
        value_list = value.split("%")
        value_position = value.index("%")
        for value_index, vl in enumerate(value_list):
            if value_index % 2 != 0 and value_index != len(value_list):
                key,key_attr = vl.split("_")
                area_code = self.getParam(key)
                area = area_code_dict.get(area_code)
                if area:
                    if value_position == 0 and value.endswith("%") and len(value_list)==3:
                        value = area.get(key_attr)
                    else:
                        value = value.replace("%" + vl + "%", str(area.get(key_attr)))
        return value

    def data_source_format(self,value):
        value_list = value.split("%")
        value_position = value.index("%")
        for value_index, vl in enumerate(value_list):
            if value_index % 2 != 0 and value_index != len(value_list):
                key,key_attr = vl.split("|")
                data_source_code = self.getParam(key)
                data_source = data_source_dict.get(data_source_code)
                if data_source:
                    if value_position == 0 and value.endswith("%") and len(value_list)==3:
                        value = data_source.get(key_attr)
                    else:
                        value = value.replace("%" + vl + "%", str(data_source.get(key_attr)))
        return value