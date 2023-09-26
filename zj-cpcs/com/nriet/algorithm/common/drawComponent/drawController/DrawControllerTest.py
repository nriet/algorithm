# -*- coding: utf-8 -*-
import json
import os
import time
import numpy as np
import logging
from com.nriet.utils import StringUtils, proxyUtils
from com.nriet.algorithm.Component import Component
from com.nriet.utils.matchUtils import match_interval

from com.nriet.algorithm.common.drawComponent.util.AxisTimeUtils import *
class DrawController(Component):

    def __init__(self, sub_local_params, algorithm_input_data):
        super().__init__(sub_local_params)
        self.input_data = []
        for input_data in algorithm_input_data:
            if isinstance(input_data, list):
                self.input_data.append([np.ma.array(data["outputData"].values, mask=np.isnan(data["outputData"].values)) for data in input_data])
            else:
                self.input_data.append(np.ma.array(input_data["outputData"].values, mask=np.isnan(input_data["outputData"].values)))
        if isinstance(algorithm_input_data[0],list):
            dims = algorithm_input_data[0][0]["outputData"].dims
            self.lon = np.ma.array(algorithm_input_data[0][0]["ncData"][dims[1]].values)
            self.lat = np.ma.array(algorithm_input_data[0][0]["ncData"][dims[0]].values)
        else:
            dims = algorithm_input_data[0]["outputData"].dims
            self.lon = np.ma.array(algorithm_input_data[0]["ncData"][dims[1]].values)
            self.lat = np.ma.array(algorithm_input_data[0]["ncData"][dims[0]].values)
        self.request_dict = sub_local_params["data_output_params"][0]
        self.algorithm_input_data = algorithm_input_data

    def execute(self):
        '''
        绘图组件入口的执行方法
        :param input_data:  待绘图数据，是一个一维数组
        :param lon: 经度数据，是一个一维数组
        :param lat: 纬度数据，是一个一维数组
        :param request_json: 业务相关参数json
        :return:
        '''
        start_time = time.time()

        input_data = self.input_data
        lon = self.lon
        lat = self.lat
        request_dict = self.request_dict
        algorithm_input_data =self.algorithm_input_data

        # 参数校验
        valid_message = validation_params(input_data, request_dict)

        if valid_message['isSuccess']:
            # 解析并整合参数
            parse_and_integrate_params(input_data, request_dict,algorithm_input_data,lon,lat)

            # 根据region_type创建实例
            region_type = request_dict["region_type"]
            class_name = ''.join([StringUtils.capitalize_str(region_type), 'Service'])
            common_business_service = proxyUtils.create_class_instance(
                '.'.join(['com.nriet.algorithm.common.drawComponent.drawService', class_name]),
                class_name,
                input_data=input_data, lon=lon, lat=lat,
                request_dict=request_dict)
            # 绘图工作
            valid_message = common_business_service.draw()

        stop_time = time.time()
        cost = stop_time - start_time
        logging.info("%s cost %s second" % (os.path.basename(__file__), cost))

        return valid_message


def validation_params(input_data, request_json):
    valid_message = {"isSuccess": True}
    if not input_data:
        logging.info("入参错误，缺少input_data!")  # 此处以后引入日志
        valid_message["isSuccess"] = False
        valid_message["error_message"] = "入参错误，缺少input_data!"
        return valid_message
    if not request_json:
        logging.info("入参错误，缺少request_json!")
        valid_message["isSuccess"] = False
        valid_message["error_message"] = "入参错误，缺少request_json!"
        return valid_message

    return valid_message


def input_data_str(input_data):
    parsed_data = np.load(input_data)
    return parsed_data


def input_data_object(input_data):
    return input_data


def replace_char(string, char, index):
    string = list(string)
    string[index] = char
    return ''.join(string)


def parse_and_integrate_params(input_data, request_dict,algorithm_input_data,lon,lat):
    '''
    解析数据，规整为统一的格式
    :param input_data: 入参数据，一维数组
    :param request_dict: 绘图参数字典
    :param algorithm_input_data: 每份数据的dataset格式，包含了时间，经纬度等要素
    :return:
    '''

    # 0.坐标轴的处理和计算
    request_dict = convert_values_and_labels(request_dict, algorithm_input_data,lon,lat)

    return input_data, request_dict

def convert_values_and_labels(request_dict,algorithm_input_data,x_axis_data,y_axis_data):
    '''
    计算并转换坐标轴相关配置
    :param request_dict: 绘图参数字典
    :param algorithm_input_data: 每份数据的dataset格式，包含了时间，经纬度等要素
    :return 返回更新后的参数字典
    注意：
    1.模板类型中目前只有全球和剖面模板支持坐标轴
    2.用户给定了x轴或y轴的坐标轴信息,则以用户的为准
    '''
    # 0. 中国，半球模板不处理
    if request_dict.get('region_type') in ['wholeChina','hemisphere']:
        return


    # 1.数据相关变量准备
    x_max_value, x_min_value, x_type, y_max_value, y_min_value, y_type = build_axises_params(algorithm_input_data,request_dict,x_axis_data,y_axis_data)

    # 2.x轴的处理
    if request_dict.get('x_values') and request_dict.get('x_labels'):  # 人工配置的参数
        pass
    else:
        request_dict = convert_x_axis_labels_and_values(request_dict, x_max_value, x_min_value,x_type)


    # 3.y轴的处理
    if  request_dict.get('y_values') and request_dict.get('y_labels'): #人工配置的参数
        pass
    else:
        request_dict = convert_y_axis_labels_and_values(request_dict, y_max_value, y_min_value,y_type)

    return request_dict

def build_axises_params(algorithm_input_data, request_dict,x_axis_data=None,y_axis_data=None):
    '''
    坐标轴处理前的参数准备操作
    :param request_dict: 绘图参数字典
    :param algorithm_input_data: 每份数据的dataset格式，包含了时间，经纬度等要素
    '''

    if isinstance(algorithm_input_data[0], list):  # [contour_data,[u,v]]
        axis_data = algorithm_input_data[0][0]['outputData']
    else:
        axis_data = algorithm_input_data[0]['outputData']
    y_type, x_type = axis_data.dims  # x,y轴的维度类型

    x_draw_data = [float(data) if x_type != 'time' else int(data) for data in list(x_axis_data)]
    y_draw_data = [float(data) if y_type != 'time' else int(data) for data in list(y_axis_data)]
    draw_regions = request_dict.get('layers')[0].get('draw_regions', None)
    if draw_regions:
        x_min_value, x_max_value, y_min_value, y_max_value = draw_regions
    else:
        x_max_value = np.max(x_draw_data)
        x_min_value = np.min(x_draw_data)
        y_max_value = np.max(y_draw_data)
        y_min_value = np.min(y_draw_data)

    return x_max_value, x_min_value, x_type, y_max_value, y_min_value, y_type


def convert_x_axis_labels_and_values(request_dict, x_max_value, x_min_value, x_type):
    """
    x轴坐标轴的相关计算
    :param request_dict: 绘图参数字典
    :param x_max_value: x轴数据的输入最大值
    :param x_min_value: x轴数据的输入最小值
    :param x_type: 绘图数据x轴的数据类型，lon ,lat, time(结合time_type判断又有六种具体类型：year:年，mon:月,day:日,five:中国候,fiveyear:国际候，季：season)
    :return 返回更新后的参数字典，可能包含x_labels,x_values,x_sub_values
    """

    # 定义返回值
    x_values =None
    x_labels =None
    x_sub_values=None


    # 2.1 x_values处理
    if x_type in ['lon', 'lat']:
        x_draw_intervals = x_max_value - x_min_value
        x_axis_space = match_interval(x_draw_intervals, [0, 8, 16, 41, 90, 181, 361], [1, 2, 5, 10, 30, 60], None)
        x_sub_axis_space = match_interval(x_draw_intervals, [0, 8, 16, 41, 90, 181, 361], [None, 1, 1, 2, 10, 10],
                                          None)
        x_minor_on = False
        if x_draw_intervals > 8:
            if x_min_value / x_axis_space != x_min_value // x_axis_space:
                start_value = int(np.ceil(x_min_value / x_axis_space)) * x_axis_space
            else:
                start_value = x_min_value

            x_values = list(np.arange(start_value, x_max_value + 1, x_axis_space))
            x_minor_on = True
            x_sub_start_value = x_values[0] - np.floor(
                (x_values[0] - x_min_value) / x_sub_axis_space) * x_sub_axis_space
            x_sub_values = list(np.arange(x_sub_start_value, x_max_value + 1, x_sub_axis_space))

        else:
            x_values = list(range(x_min_value, x_max_value + 1, x_axis_space))
            x_sub_values = x_values

        if x_type == 'lon':
            for index, x_value in enumerate(x_values):
                if x_value < 180:
                    x_labels.append(str(x_value) + 'E')
                elif x_value in [180.0, 360.0]:
                    x_labels.append(str(360 - x_value))
                elif x_value > 180 and x_value < 360:
                    x_labels.append(str(360 - x_value) + 'W')
        else:
            for index, x_value in enumerate(x_values):
                if x_value < 0:
                    x_labels.append(str(np.abs(x_value)) + 'S')
                elif x_value == 0:
                    x_labels.append(str(x_value))
                elif x_value > 0:
                    x_labels.append(str(np.abs(x_value)) + 'N')

    elif (x_type == 'time'):
        time_type = request_dict.get('time_type')
        x_labels, x_sub_values, x_values = get_axis_by_time_type(time_type, x_labels, x_max_value, x_min_value,
                                                                 x_sub_values, x_values)
    request_dict['x_values'] = x_values
    request_dict['x_labels'] = x_labels
    request_dict['x_sub_values'] = x_sub_values
    return request_dict

def convert_y_axis_labels_and_values(request_dict, y_max_value, y_min_value, y_type):
    """
    y轴坐标轴的相关计算
    :param request_dict: 绘图参数字典
    :param y_max_value: x轴数据的输入最大值
    :param y_min_value: x轴数据的输入最小值
    :param y_type: 绘图数据x轴的数据类型，lat, time(结合time_type判断又有六种具体类型：year:年，mon:月,day:日,five:中国候,fiveyear:国际候，季：season)
    :return 返回更新后的参数字典，可能包含y_labels,y_values,y_sub_values
    """
    # 1.定义返回变量
    y_values = None
    y_labels = None
    y_sub_values = None

    # 2.1 y_values处理
    if y_type == 'lat':
        y_draw_intervals = y_max_value - y_min_value
        y_axis_space = match_interval(y_draw_intervals, [0, 8, 16, 41, 90, 181, 361], [1, 2, 5, 10, 30, 60], None)
        y_sub_axis_space = match_interval(y_draw_intervals, [0, 8, 16, 41, 90, 181, 361], [None, 1, 1, 2, 10, 10],
                                          None)
        y_minor_on = False
        if y_draw_intervals > 8:
            if y_min_value / y_axis_space != y_min_value // y_axis_space:
                start_value = int(np.ceil(y_min_value / y_axis_space)) * y_axis_space
            else:
                start_value = y_min_value

            y_values = list(np.arange(start_value, y_max_value + 1, y_axis_space))
            y_minor_on = True
            y_sub_start_value = y_values[0] - np.floor(
                (y_values[0] - y_min_value) / y_sub_axis_space) * y_sub_axis_space
            y_sub_values = list(np.arange(y_sub_start_value, y_max_value + 1, y_sub_axis_space))

        else:
            y_values = list(range(y_min_value, y_max_value + 1, y_axis_space))
            y_sub_values = y_values

        for index, y_value in enumerate(y_values):
            if y_value < 0:
                y_labels.append(str(np.abs(y_value)) + 'S')
            elif y_value == 0:
                y_labels.append(str(y_value))
            elif y_value > 0:
                y_labels.append(str(np.abs(y_value)) + 'N')
    elif y_type == 'time':
        time_type = request_dict.get('time_type')
        y_labels, y_sub_values, y_values = get_axis_by_time_type(time_type, y_labels, y_max_value, y_min_value,
                                                                 y_sub_values, y_values)
    request_dict['y_values'] = y_values
    request_dict['y_labels'] = y_labels
    request_dict['y_sub_values'] = y_sub_values
    return y_labels, y_sub_values, y_values

def get_axis_by_time_type(time_type, x_labels, x_max_value, x_min_value, x_sub_values, x_values):
    if time_type == 'year':  # 输入格式 YYYY
        year_list = list(range(x_min_value, x_max_value + 1))
        times = len(year_list)  # 时间类型的维度的个数
        x_axis_space = match_interval(times, [0, 8, 16, 40, 80, 9999999], [1, 2, 5, 10, (times % 80 + 1) * 10],
                                      None)
        x_sub_axis_space = match_interval(times, [0, 8, 16, 40, 80, 9999999],
                                          [None, 1, 1, 2, (times % 80 + 1) * 2], None)

        if times < 8:
            x_values = list(range(x_min_value, x_max_value + 1, x_axis_space))
            x_minor_on = False  # 此时不需要显示副刻度
            x_sub_values = None  # 此时无副刻度
        elif times >= 8 and times < 16:
            x_values = list(range(x_min_value, x_max_value + 1, x_axis_space))
            x_minor_on = True
            x_sub_values = list(range(x_min_value, x_max_value + 1))
        elif times >= 16 and times < 40:
            x_values = [year for year in year_list if year % x_axis_space == 0]  # 去能被间隔整除的年
            x_minor_on = True
            x_sub_values = list(range(x_min_value, x_max_value + 1))
        elif times >= 40:
            x_values = [year for year in year_list if year % x_axis_space == 0]  # 去能被间隔整除的年
            x_minor_on = True
            x_sub_start_value = x_values[0] - np.floor(
                (x_values[0] - x_min_value) / x_sub_axis_space) * x_sub_axis_space
            x_sub_values = list(np.arange(x_sub_start_value, x_max_value + 1, x_sub_axis_space))

        x_labels = [str(x_value) for x_value in x_values]

    elif time_type == 'mon':  # 输入格式 YYYYMM
        # x_sub_axis_space = match_interval(times, [0,8,16,25,48,96,9999999],[None, 1, 1, 1, 3, 3], None)
        # 获取这段时间内的所有月份列表
        month_list = get_each_month(str(x_min_value), str(x_max_value))
        times = len(month_list)
        if (times < 8):
            x_values = month_list

            individual_years_indexes = get_individual_years_indexes(x_values)
            x_labels = [get_month_abbr(str(x_value)[-2:]) for x_value in x_values]  # 先变成MM
            for individual_years_index in individual_years_indexes:
                x_labels[individual_years_index] = get_month_abbr(
                    str(x_values[individual_years_index])[-2:]) + str(x_values[individual_years_index])[
                                                                  :4]  # 年首标MMYYYY

            x_minor_on = False  # 此时不需要显示副刻度
            x_sub_values = None  # 此时无副刻度

        elif times >= 8 and times < 16:
            x_values = [month for month in month_list if month % 2 != 0]  # 要奇数月！

            individual_years_indexes = get_individual_years_indexes(x_values)
            x_labels = [get_month_abbr(str(x_value)[-2:]) for x_value in x_values]  # 先变成MM
            for individual_years_index in individual_years_indexes:
                x_labels[individual_years_index] = get_month_abbr(
                    str(x_values[individual_years_index])[-2:]) + str(x_values[individual_years_index])[
                                                                  :4]  # 年首标MMYYYY

            x_minor_on = True  # 需要显示副刻度
            x_sub_values = month_list  # 次数副刻度间隔为1，此时主副刻度可重合！


        elif times >= 16 and times < 25:
            x_values = [month for month in month_list if
                        str(month)[-2:] in ['01', '04', '07', '10']]  # 找到 month_list 中的1,4,7,10月

            individual_years_indexes = get_individual_years_indexes(x_values)
            x_labels = [get_month_abbr(str(x_value)[-2:]) for x_value in x_values]  # 先变成MM
            for individual_years_index in individual_years_indexes:
                x_labels[individual_years_index] = get_month_abbr(
                    str(x_values[individual_years_index])[-2:]) + str(x_values[individual_years_index])[
                                                                  :4]  # 年首标MMYYYY

            x_minor_on = True  # 需要显示副刻度
            x_sub_values = month_list  # 次数副刻度间隔为1，此时主副刻度可重合！

        elif times >= 25 and times < 48:
            x_values = [month for month in month_list if
                        str(month)[-2:] in ['01', '07']]  # 找到 month_list 中的1,7月

            individual_years_indexes = get_individual_years_indexes(x_values)
            x_labels = [get_month_abbr(str(x_value)[-2:]) for x_value in x_values]  # 先变成MM
            for individual_years_index in individual_years_indexes:
                x_labels[individual_years_index] = get_month_abbr(
                    str(x_values[individual_years_index])[-2:]) + str(x_values[individual_years_index])[
                                                                  :4]  # 年首标MMYYYY

            x_minor_on = True  # 需要显示副刻度
            x_sub_values = month_list  # 次数副刻度间隔为1，此时主副刻度可重合！

        elif times >= 48:
            x_values = [month for month in month_list if str(month)[-2:] == '01']  # 找到 month_list中的1月

            x_labels = [str(x_value)[:4] for x_value in x_values]  # 全部标年YYYY

            x_minor_on = True  # 需要显示副刻度
            x_sub_values = [month for month in month_list if
                            str(month)[-2:] in ['04', '07', '10']]  # 次数副刻度间隔为1，此时主副刻度可重合！

    elif time_type == 'day':
        # x_axis_space = match_interval(times, [0,8,16,40,90,125,240,367,99999999], [1,2,5,10,15,30,30,30], None)
        # x_sub_axis_space = match_interval(times, [0,8,16,40,90,125,240,367,99999999], [None, 1, 1, 5, 5, 15,15,15], None)
        day_list = get_each_day(str(x_min_value), str(x_max_value))
        times = len(day_list)
        if times < 8:
            x_values = day_list

            individual_years_indexes = get_individual_years_indexes(x_values)
            x_labels = [get_day_month(day) for day in day_list]  # MMDD
            for individual_years_index in individual_years_indexes:
                x_labels[individual_years_index] = get_day_month_year(
                    x_values[individual_years_index])  # 每首次出现的年日期，都必须得标年

            x_minor_on = False  # 此时不需要显示副刻度
            x_sub_values = None  # 此时无副刻度

        elif times >= 8 and times < 16:
            # x_values = list(range(day_list[0], day_list[-1] + 1, 2))  # 从第一天开始，隔两天
            x_values = [day for day in day_list if day_list.index(day) % 2 == 0]  # 从第一天开始，隔两天

            individual_years_indexes = get_individual_years_indexes(x_values)
            x_labels = [get_day_month(day) for day in x_values]  # MMDD
            for individual_years_index in individual_years_indexes:
                x_labels[individual_years_index] = get_day_month_year(
                    x_values[individual_years_index])  # 每首次出现的年日期，都必须得标年

            x_minor_on = True  # 需要显示副刻度
            x_sub_values = day_list  # 次数副刻度间隔为1，此时主副刻度可重合！

        elif times >= 16 and times < 40:
            x_values = [day for day in day_list if str(day)[-2:] in ['01', '06', '11', '16', '21',
                                                                     '26']]  # 日期在 '01','06','11','16','21','26'

            individual_years_indexes = get_individual_years_indexes(x_values)
            x_labels = [get_day_month(day) for day in x_values]  # MMDD
            for individual_years_index in individual_years_indexes:
                x_labels[individual_years_index] = get_day_month_year(
                    x_values[individual_years_index])  # 每首次出现的年日期，都必须得标年

            x_minor_on = True  # 需要显示副刻度
            x_sub_values = day_list  # 次数副刻度间隔为1，此时主副刻度可重合！


        elif times >= 40 and times < 90:
            x_values = [day for day in day_list if str(day)[-2:] in ['01', '11', '21']]  # 日期在 '01','11','21'

            individual_years_indexes = get_individual_years_indexes(x_values)
            x_labels = [get_day_month(day) for day in x_values]  # MMDD
            for individual_years_index in individual_years_indexes:
                x_labels[individual_years_index] = get_day_month_year(
                    x_values[individual_years_index])  # 每首次出现的年日期，都必须得标年

            x_minor_on = True  # 需要显示副刻度
            x_sub_values = [day for day in day_list if
                            str(day)[-2:] in ['06', '16', '26']]  # 日期在 '06','16','26'

        elif times >= 90 and times < 125:
            x_values = [day for day in day_list if str(day)[-2:] in ['01', '16']]  # 日期在 '01','16'

            individual_years_indexes = get_individual_years_indexes(x_values)
            x_labels = [get_day_month(day) for day in x_values]  # MMDD
            for individual_years_index in individual_years_indexes:
                x_labels[individual_years_index] = get_day_month_year(
                    x_values[individual_years_index])  # 每首次出现的年日期，都必须得标年

            x_minor_on = True  # 需要显示副刻度
            x_sub_values = [day for day in day_list if
                            str(day)[-2:] in ['06', '11', '16', '21', '26']]  # 日期在 '06', '11','16', '21','26'

        elif times >= 125 and times < 240:
            x_values = [day for day in day_list if str(day)[-2:] == '01']  # 找到 month_list中的01日

            individual_years_indexes = get_individual_years_indexes(x_values)
            x_labels = [get_month_abbr(str(day)[4:6]) for day in x_values]  # 此时标记为 MM
            for individual_years_index in individual_years_indexes:
                x_labels[individual_years_index] = get_month_year(
                    x_values[individual_years_index])  # 每首次出现的年日期，标记为MMYYYY

            x_minor_on = True  # 需要显示副刻度
            x_sub_values = [day for day in day_list if str(day)[-2:] == '16']  # 日期在 '16'

        else:
            # 获取日期间的月份
            x_values = [day for day in day_list if str(day)[-2:] == '01']
            x_labels = [get_month_abbr(str(day)[4:6]) for day in x_values]
            individual_years_indexes = get_individual_years_indexes(x_values)
            for individual_years_index in individual_years_indexes:
                x_labels[individual_years_index] = get_month_year(
                    x_values[individual_years_index])  # 每首次出现的年日期，标记为MMYYYY
    elif time_type == 'five':  # 中国候 YYYYMMHH
        five_list = get_five_list(str(x_min_value), str(x_max_value))  # 注意这个地方返回的 str格式！！！！！！
        times = len(five_list)
        if times < 48:
            x_values = [int(five) for five in five_list if five[-2:] in ['01', '03', '05']]  # 主刻度只显示每月的010305候
            x_labels = [str(x_value) for x_value in x_values]

            # 先把每月的01候位置搞到，需要变成YYYYMM
            first_month_values = [x_value for x_value in x_values if str(x_value).endswith('01')]
            first_year_month_indexes = []
            # 找到首年首月的值
            individual_years_indexes = get_individual_years_indexes(first_month_values)
            for individual_years_index in individual_years_indexes:
                first_year_month_indexes.append(x_values.index(first_month_values[individual_years_index]))
            # 找到所有0305候的值
            third_or_five_values = [x_value for x_value in x_values if str(x_value)[-2:] in ['03', '05']]

            for first_month_value in first_month_values:
                index = x_labels.index(str(first_month_value))
                if index != -1:
                    x_labels[index] = get_month_abbr(x_labels[index][4:6])
            for first_year_month_index in first_year_month_indexes:
                x_labels[first_year_month_index] = str(x_values[first_year_month_index])[:4] + get_month_abbr(
                    str(x_values[first_year_month_index])[4:6])
            for third_or_five_value in third_or_five_values:
                index = x_values.index(third_or_five_value)
                if index != -1:
                    last_two_number = str(third_or_five_value)[-2:]
                    if last_two_number.startswith('0'):
                        last_two_number = last_two_number[-1]
                    x_labels[index] = last_two_number

            x_minor_on = True
            x_sub_values = [int(five) for five in five_list if five[-2:] in ['02', '04', '06']]  # 副刻度为02/04/06


        elif times >= 48:
            x_values = [int(five) for five in five_list if five[-2:] == '01']  # 主刻度只显示每月的01候
            month_list = [str(x_value)[:6] for x_value in x_values]
            individual_years_indexes = get_individual_years_indexes(month_list)
            x_labels = [get_month_abbr(month[-2:]) for month in month_list]  # 先变成MM
            for individual_years_index in individual_years_indexes:
                x_labels[individual_years_index] = get_month_abbr(
                    str(month_list[individual_years_index])[-2:]) + str(month_list[individual_years_index])[
                                                                    :4]  # 年首标MMYYYY

    elif time_type == 'fiveYear':
        pass
    elif time_type == 'season':
        pass
    return x_labels, x_sub_values, x_values




