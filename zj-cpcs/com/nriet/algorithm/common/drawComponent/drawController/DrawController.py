# -*- coding: utf-8 -*-

import importlib, sys

importlib.reload(sys)
import traceback,logging
import json
import os
import time
import numpy as np
import copy
import math
from com.nriet.utils import StringUtils, proxyUtils
from com.nriet.algorithm.Component import Component
from com.nriet.utils.matchUtils import match_interval
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import SERVER_HANDLING_ERROR_CODE, CIPAS_SUCCESS_CODE
from com.nriet.algorithm.common.drawComponent.util.AxisTimeUtils import *
from com.nriet.utils.result.ResponseResultUtils import build_response_dict
from com.nriet.utils.decorator.DIDecorator import DI_decorater
from com.nriet.utils.StringUtils import judge_str_is_number


class DrawController(Component):

    def __init__(self, sub_local_params, algorithm_input_data):
        super().__init__(sub_local_params)
        self.input_data = []
        # 达标站空间分布图显示达标的站点数
        if sub_local_params.get("drawMarkNumsType"):
            dbzNum = algorithm_input_data[0]["outputData"].attrs['dbzNum']
            sub_local_params.get("data_output_params")[0].get("layers")[0]["note"]="达标站数："+dbzNum
        draw_regions = sub_local_params.get("data_output_params")[0].get("layers")[0].get("draw_regions")
        # 20220920 江鹏临时处理，如果娶不到layers下面的经纬度范围，取上一级的
        if not draw_regions:
            draw_regions = sub_local_params.get("data_output_params")[0].get("draw_regions")

        if draw_regions:  # 解析绘图经纬度，给全球散点的绘图经纬度准备
            sLon, eLon, sLat, eLat = draw_regions.split(',')
            sLon = int(sLon) if judge_str_is_number(sLon) else 0
            eLon = int(eLon) if judge_str_is_number(eLon) else 360
            sLat = int(sLat) if judge_str_is_number(sLat) else -90
            eLat = int(eLat) if judge_str_is_number(eLat) else 90
            lonRanges = range(sLon, eLon + 1)
            latRanges = range(sLat, eLat + 1)
        else:
            lonRanges = range(0, 361)
            latRanges = range(-90, 91)
        self.request_dict = sub_local_params["data_output_params"][0]
        # 输入数据处理标识 主要针对处理一个算法返回多个数据存储时，多嵌套了一层list的问题
        input_data_proc_flag = sub_local_params.get("input_data_proc_flag",False)
        if input_data_proc_flag:
            algorithm_input_data = algorithm_input_data[0]
        # 1.确定输入数据self.input_data，可能会转置啥的
        for index, input_data in enumerate(algorithm_input_data):
            c_input_data = copy.deepcopy(input_data)
            algorithm_input_data[index] = c_input_data

            if isinstance(c_input_data, list):
                self.input_data.append([])
                for ind, data in enumerate(c_input_data):
                    if self.request_dict.get('x_dim'):
                        data["outputData"] = data["outputData"].transpose(transpose_coords=True)
                    self.input_data[index].append(
                        np.ma.array(data["outputData"].values, mask=np.isnan(data["outputData"].values)))
            else:
                if self.request_dict.get('x_dim'):
                    c_input_data["outputData"] = c_input_data["outputData"].transpose(transpose_coords=True)
                self.input_data.append(
                    np.ma.array(c_input_data["outputData"].values, mask=np.isnan(c_input_data["outputData"].values)))

        # 如果纵坐标为高度，则数据level维的值做特殊处理
        if self.request_dict.get('y_types'):
            if self.request_dict.get('y_types') == "height":
                for idx, tmpdata in enumerate(algorithm_input_data):
                    if isinstance(tmpdata, list):
                        for i, listdata in enumerate(tmpdata):
                            tmpdata = listdata['outputData']
                            tmpdata['level'] = [round(math.log10(i), 2) * 1000 for i in tmpdata['level'].values]
                            algorithm_input_data[idx][i]['outputData'] = tmpdata
                    else:
                        tmpdata = tmpdata['outputData']
                        tmpdata['level'] = [round(math.log10(i), 2) * 1000 for i in tmpdata['level'].values]
                        algorithm_input_data[idx]['outputData'] = tmpdata

        # 2.1 收集所绘图层数据之维度信息
        dims_set = set()
        self.lat = None
        self.lon = None
        self.station_lat = None
        self.station_lon = None

        # 2.1.1 定义语法糖
        def collect_dim(algorithm_input_data, dims_set):
            if not isinstance(algorithm_input_data, list):
                dims_set.update(algorithm_input_data["outputData"].dims)
            else:
                for dim_data in algorithm_input_data:
                    collect_dim(dim_data, dims_set)

        # 2.1.2 收集所有的维度如lon,lat,time,station,level等，去重处理
        collect_dim(algorithm_input_data, dims_set)
        dims_set_all = dims_set

        # 2.2 写值到self里边
        for dim_idx, dim_data in enumerate(algorithm_input_data):
            if not dims_set:
                break

            if isinstance(dim_data, list):
                dim_data_given = dim_data[0]['outputData']
            else:
                dim_data_given = dim_data['outputData']
            dims = dim_data_given.dims
            if dim_idx == 0:
                self.dims = dims

            if 'station' in dims:  # 一般是站点绘图,站点数据的“经纬”度从属性里边获取
                if isinstance(dim_data_given.attrs['lons'], str):  # 站点经纬度要另外赋值到station_lon,station_lat
                    self.station_lon = np.array(
                        eval(copy.deepcopy(dim_data_given.attrs['lons'])))
                    if not any(item in dims_set_all for item in ['lon', 'time']):
                        self.lon = lonRanges
                        self.lon_indexes = np.ma.array(list(range(len(lonRanges))))
                    self.station_lat = np.array(
                        eval(copy.deepcopy(dim_data_given.attrs['lats'])))
                    if not any(item in dims_set_all for item in ['lat', 'time']):
                        self.lat = latRanges
                        self.lat_indexes = np.ma.array(list(range(len(latRanges))))
                else:
                    self.station_lon = dim_data_given.attrs['lons']
                    if not any(item in dims_set_all for item in ['lon', 'time']):
                        self.lon_indexes = np.ma.array(list(range(len(lonRanges))))
                        self.lon = lonRanges
                    self.station_lat = dim_data_given.attrs['lats']
                    if not any(item in dims_set_all for item in ['lat', 'time']):
                        self.lat_indexes = np.ma.array(list(range(len(latRanges))))
                        self.lat = latRanges

            else:  # level/lon/lat/都是一样的，只是time维度的要转换为索引数组！
                if dims[1] != 'time':
                    self.lon_indexes = self.lon = np.ma.array(dim_data_given[dims[1]].values, dtype=np.float32)
                else:
                    self.lon = np.ma.array(dim_data_given[dims[1]].values, dtype=np.int)
                    self.lon_indexes = np.ma.array(list(range(len(self.lon))))
                if dims[0] != 'time':
                    self.lat_indexes = self.lat = np.ma.array(dim_data_given[dims[0]].values, dtype=np.float32)
                else:
                    self.lat = np.ma.array(dim_data_given[dims[0]].values, dtype=np.int)
                    self.lat_indexes = np.ma.array(list(range(len(self.lat))))

            dims_set = dims_set - set(dims)  # 更新已有的

        # if isinstance(algorithm_input_data[0], list):
        #     dims_data = algorithm_input_data[0][0]["outputData"]
        #     dims = dims_data.dims
        #
        #     if len(dims) == 1 and dims[0] == 'station':  # 如果是站点数据
        #         if isinstance(dims_data.attrs['lons'], str):
        #             self.lon = np.array(eval(copy.deepcopy(dims_data.attrs['lons'])))
        #             self.lon_indexes = self.lon
        #             self.lat = np.array(eval(copy.deepcopy(dims_data.attrs['lats'])))
        #             self.lat_indexes = self.lat
        #         else:
        #             self.lon = dims_data.attrs['lons']
        #             self.lon_indexes = self.lon
        #             self.lat = dims_data.attrs['lats']
        #             self.lat_indexes = self.lat
        #     else:  # 如果是二维数据
        #         if (dims[1] != 'time'):
        #             self.lon = np.ma.array(dims_data[dims[1]].values, dtype=np.float32)
        #             self.lon_indexes = self.lon
        #         else:
        #             self.lon = np.ma.array(dims_data[dims[1]].values, dtype=np.int)
        #             self.lon_indexes = list(range(len(self.lon)))
        #
        #         if dims[0] != 'time':
        #             self.lat = np.ma.array(dims_data[dims[0]].values, dtype=np.float32)
        #             self.lat_indexes = self.lat
        #         else:
        #             self.lat = np.ma.array(dims_data[dims[0]].values, dtype=np.int)
        #             self.lat_indexes = list(range(len(self.lat)))
        #
        # else:
        #     dims_data = algorithm_input_data[0]["outputData"]
        #     dims = dims_data.dims
        #
        #     if len(dims) == 1 and dims[0] == 'station':  # 如果是一维数据，且是站点数据
        #         if isinstance(dims_data.attrs['lons'], str):
        #             self.station_lon = np.array(eval(copy.deepcopy(dims_data.attrs['lons'])))
        #             self.station_lon_indexes = self.station_lon
        #             self.station_lat = np.array(eval(copy.deepcopy(dims_data.attrs['lats'])))
        #             self.station_lat_indexes = self.station_lat
        #         else:
        #             self.station_lon = dims_data.attrs['lons']
        #             self.station_lon_indexes = self.station_lon
        #             self.station_lat = dims_data.attrs['lats']
        #             self.station_lat_indexes = self.station_lat
        #     else:  # 如果是二维数据
        #         if dims[1] != 'time':
        #             self.lon = np.ma.array(dims_data[dims[1]].values, dtype=np.float32)
        #             self.lon_indexes = self.lon
        #         else:
        #             self.lon = np.ma.array(dims_data[dims[1]].values, dtype=np.int)
        #             self.lon_indexes = np.ma.array(list(range(len(self.lon))))
        #         if dims[0] != 'time':
        #             self.lat = np.ma.array(dims_data[dims[0]].values, dtype=np.float32)
        #             self.lat_indexes = self.lat
        #         else:
        #             self.lat = np.ma.array(dims_data[dims[0]].values, dtype=np.int)
        #             self.lat_indexes = np.ma.array(list(range(len(self.lat)))
        self.algorithm_input_data = algorithm_input_data

    @DI_decorater(type="ImgProduct")
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
        try:
            input_data = self.input_data
            lon = self.lon
            lat = self.lat
            request_dict = self.request_dict
            algorithm_input_data = self.algorithm_input_data
            lon_indexes = self.lon_indexes
            lat_indexes = self.lat_indexes

            # 参数校验
            draw_result = validation_params(input_data, request_dict)

            if draw_result['response_code'] == CIPAS_SUCCESS_CODE:
                # 解析并整合参数
                parse_and_integrate_params(input_data, request_dict, algorithm_input_data, lon, lat)

                # 根据region_type创建实例
                region_type = request_dict["region_type"]
                class_name = ''.join([StringUtils.capitalize_str(region_type), 'Service'])
                common_business_service = proxyUtils.create_class_instance(
                    '.'.join(['com.nriet.algorithm.common.drawComponent.drawService', class_name]),
                    class_name,
                    input_data=input_data, lon=lon, lat=lat,
                    request_dict=request_dict, lon_indexes=lon_indexes, lat_indexes=lat_indexes, dims=self.dims, station_lat=self.station_lat, station_lon=self.station_lon)
                # 绘图工作
                draw_result = common_business_service.draw()
                stop_time = time.time()
                cost = stop_time - start_time
                logging.info("         %s cost %s second" % (os.path.basename(__file__), cost))

                return draw_result
        except Exception as e:
            logging.error(traceback.format_exc())
            raise AlgorithmException(response_code=SERVER_HANDLING_ERROR_CODE, response_msg=e.__str__())


def validation_params(input_data, request_json):
    draw_result = build_response_dict()
    if not input_data:
        logging.info("request params error,lack of input_data!")  # 此处以后引入日志
        draw_result["response_code"] = "9851"
        draw_result["response_msg"] = " DrawController request params error,lack of 'input_data' !"
        return draw_result
    if not request_json:
        logging.info("DrawController request params error,lack of 'input_data' !")
        draw_result["response_code"] = "9851"
        draw_result["response_msg"] = "request params error,lack of 'request_json' !"
        return draw_result

    return draw_result


def input_data_str(input_data):
    parsed_data = np.load(input_data)
    return parsed_data


def input_data_object(input_data):
    return input_data


def replace_char(string, char, index):
    string = list(string)
    string[index] = char
    return ''.join(string)


def parse_and_integrate_params(input_data, request_dict, algorithm_input_data, lon, lat):
    '''
    解析数据，规整为统一的格式
    :param input_data: 入参数据，一维数组
    :param request_dict: 绘图参数字典
    :param algorithm_input_data: 每份数据的dataset格式，包含了时间，经纬度等要素
    :return:
    '''

    # 0.坐标轴的处理和计算
    convert_values_and_labels(request_dict, algorithm_input_data, lon, lat)


def convert_values_and_labels(request_dict, algorithm_input_data, x_axis_data, y_axis_data):
    '''
    计算并转换坐标轴相关配置
    :param request_dict: 绘图参数字典
    :param algorithm_input_data: 每份数据的dataset格式，包含了时间，经纬度等要素
    :return 返回更新后的参数字典
    注意：
    1.模板类型中目前只有全球和剖面模板支持坐标轴
    2.用户给定了x轴或y轴的坐标轴信息,则以用户的为准
    '''
    # 0. 中国，半球模板,卫星模板不处理
    if request_dict.get('region_type') in ['wholeChina', 'hemisphere', 'satellite', 'ChinaTest']:
        return

    # 0.1 timeType兼容处理
    if request_dict.get('time_type'):
        request_dict['time_type'] = str.upper(request_dict.get('time_type'))

    # 1.数据相关变量准备
    x_max_value, x_min_value, x_type, y_max_value, y_min_value, y_type = build_axises_params(algorithm_input_data,
                                                                                             request_dict, x_axis_data,
                                                                                             y_axis_data)

    # 2.x轴的处理
    if request_dict.get('x_values') and request_dict.get('x_labels'):  # 人工配置的参数
        pass
    else:
        request_dict = convert_x_axis_labels_and_values(request_dict, x_max_value, x_min_value, x_type, x_axis_data)

    # 3.y轴的处理 (如果纵坐标为高度，则做特殊处理)
    if request_dict.get('y_values') and request_dict.get('y_labels'):  # 人工配置的参数
        if request_dict.get('y_types'):
            if request_dict.get('y_types') == "height":
                y_values = request_dict.get('y_values')
                y_values = [round(math.log10(i), 2) * 1000 for i in y_values]
                request_dict['y_values'] = y_values
        else:
            pass
    else:
        request_dict = convert_y_axis_labels_and_values(request_dict, y_max_value, y_min_value, y_type, y_axis_data)

    return request_dict


def build_axises_params(algorithm_input_data, request_dict, x_axis_data=None, y_axis_data=None):
    '''
    坐标轴处理前的参数准备操作
    :param request_dict: 绘图参数字典
    :param algorithm_input_data: 每份数据的dataset格式，包含了时间，经纬度等要素
    '''

    if isinstance(algorithm_input_data[0], list):  # [contour_data,[u,v]]
        axis_data = algorithm_input_data[0][0]['outputData']
    else:
        axis_data = algorithm_input_data[0]['outputData']
    if 'station' in axis_data.dims:
        y_type, x_type = ['lat', 'lon']
    else:
        y_type, x_type = axis_data.dims  # x,y轴的维度类型

    x_draw_data = [float(data) if x_type != 'time' else int(data) for data in list(x_axis_data)]
    y_draw_data = [float(data) if y_type != 'time' else int(data) for data in list(y_axis_data)]
    draw_regions = request_dict.get('layers')[0].get('draw_regions', None)
    if draw_regions:
        # x_min_value, x_max_value, y_min_value, y_max_value = [float(value) for value in draw_regions.split(",")]
        x_min_value, x_max_value, y_min_value, y_max_value = draw_regions.split(",")

        x_min_value = float(x_min_value) if x_min_value.isdigit() else np.min(x_draw_data)
        x_max_value = float(x_max_value) if x_max_value.isdigit() else np.max(x_draw_data)
        y_min_value = float(y_min_value) if y_min_value.isdigit() else np.min(y_draw_data)
        y_max_value = float(y_max_value) if y_max_value.isdigit() else np.max(y_draw_data)

        if x_type == 'time':
            x_min_value = int(x_min_value)
            x_max_value = int(x_max_value)
        if y_type == 'time':
            y_min_value = int(y_min_value)
            y_max_value = int(y_max_value)

    else:
        # 当为时间轴且尺度为季节尺度时，最大和最小分别取数组的最后一个和第一个值
        x_max_value = x_draw_data[-1] if x_type == 'time' and request_dict.get("time_type") == 'SEASON' else np.max(
            x_draw_data)
        x_min_value = x_draw_data[0] if x_type == 'time' and request_dict.get("time_type") == 'SEASON' else np.min(
            x_draw_data)
        y_max_value = y_draw_data[-1] if y_type == 'time' and request_dict.get("time_type") == 'SEASON' else np.max(
            y_draw_data)
        y_min_value = y_draw_data[0] if y_type == 'time' and request_dict.get("time_type") == 'SEASON' else np.min(
            y_draw_data)

    return x_max_value, x_min_value, x_type, y_max_value, y_min_value, y_type


def convert_x_axis_labels_and_values(request_dict, x_max_value, x_min_value, x_type, x_axis_data):
    """
    x轴坐标轴的相关计算
    :param request_dict: 绘图参数字典
    :param x_max_value: x轴数据的输入最大值
    :param x_min_value: x轴数据的输入最小值
    :param x_type: 绘图数据x轴的数据类型，lon ,lat, time(结合time_type判断又有六种具体类型：year:年，mon:月,day:日,five:中国候,fiveyear:国际候，季：season)
    :return 返回更新后的参数字典，可能包含x_labels,x_values,x_sub_values
    """

    # 定义返回值
    x_values = []
    x_labels = []
    x_sub_values = []

    # 2.1 x_values处理
    if x_type in ['lon', 'lat']:
        x_draw_intervals = x_max_value - x_min_value

        if request_dict.get("x_axis_space") and request_dict.get("x_sub_axis_space"):
            x_axis_space = request_dict.get("x_axis_space")
            x_sub_axis_space = request_dict.get("x_sub_axis_space")
        else:
            x_axis_space = match_interval(x_draw_intervals, [0, 8, 16, 41, 90, 181, 361], [1, 2, 5, 10, 30, 60], None)
            x_sub_axis_space = match_interval(x_draw_intervals, [0, 8, 16, 41, 90, 181, 361], [None, 1, 1, 2, 10, 10],
                                              None)
        if x_draw_intervals > 8:
            if x_min_value / x_axis_space != x_min_value // x_axis_space:
                start_value = int(np.ceil(x_min_value / x_axis_space)) * x_axis_space
            else:
                start_value = x_min_value

            x_values = list(np.arange(start_value, x_max_value + 0.001, x_axis_space))
            x_sub_start_value = x_values[0] - np.floor(
                (x_values[0] - x_min_value) / x_sub_axis_space) * x_sub_axis_space
            x_sub_values = list(np.arange(x_sub_start_value, x_max_value + 1, x_sub_axis_space))

        else:
            x_values = list(np.arange(x_min_value, x_max_value + 0.001, x_axis_space))
            x_sub_values = x_values

        if x_type == 'lon':
            for index, x_value in enumerate(x_values):
                x_value = int(x_value)
                if x_value < -180:
                    x_labels.append(str(x_value + 360) + 'E')
                elif x_value == -180:
                    x_labels.append(str(x_value))
                elif x_value < 0:
                    x_labels.append(str(x_value * -1) + 'W')
                elif x_value == 0:
                    x_labels.append(str(x_value))
                elif x_value < 180:
                    x_labels.append(str(x_value) + 'E')
                elif x_value in [180.0, 360.0]:
                    x_labels.append(str(360 - x_value))
                elif x_value > 180 and x_value < 360:
                    x_labels.append(str(360 - x_value) + 'W')
        else:
            for index, x_value in enumerate(x_values):
                x_value = int(x_value)
                if x_value < 0:
                    x_labels.append(str(np.abs(x_value)) + 'S')
                elif x_value == 0:
                    x_labels.append(str(x_value))
                elif x_value > 0:
                    x_labels.append(str(np.abs(x_value)) + 'N')

        # x_values = [list(x_axis_data).index(x_value) for x_value in x_values]
        # x_sub_values = [list(x_axis_data).index(x_sub_value) for x_sub_value in x_sub_values]


    elif (x_type == 'time'):
        time_type = request_dict.get('time_type')
        x_labels, x_sub_values, x_values = get_axis_by_time_type(time_type, x_labels, x_max_value, x_min_value,
                                                                 x_sub_values, x_values)
        x_values = [list(x_axis_data).index(x_value) for x_value in x_values]
        if x_sub_values:
            x_sub_values = [list(x_axis_data).index(x_sub_value) for x_sub_value in x_sub_values]

    request_dict['x_values'] = x_values
    request_dict['x_labels'] = x_labels
    request_dict['x_sub_values'] = x_sub_values
    return request_dict


def convert_y_axis_labels_and_values(request_dict, y_max_value, y_min_value, y_type, y_axis_data):
    """
    y轴坐标轴的相关计算
    :param request_dict: 绘图参数字典
    :param y_max_value: x轴数据的输入最大值
    :param y_min_value: x轴数据的输入最小值
    :param y_type: 绘图数据x轴的数据类型，lat, time(结合time_type判断又有六种具体类型：year:年，mon:月,day:日,five:中国候,fiveyear:国际候，季：season)
    :return 返回更新后的参数字典，可能包含y_labels,y_values,y_sub_values
    """
    # 1.定义返回变量
    y_values = []
    y_labels = []
    y_sub_values = []

    # 2.1 y_values处理
    if y_type == 'lat':
        y_draw_intervals = y_max_value - y_min_value

        if request_dict.get("y_axis_space") and request_dict.get("y_sub_axis_space"):
            y_axis_space = request_dict.get("y_axis_space")
            y_sub_axis_space = request_dict.get("y_sub_axis_space")
        else:
            y_axis_space = match_interval(y_draw_intervals, [0, 8, 16, 41, 90, 181, 361], [1, 2, 5, 10, 30, 60], None)
            y_sub_axis_space = match_interval(y_draw_intervals, [0, 8, 16, 41, 90, 181, 361], [None, 1, 1, 2, 10, 10],
                                              None)
        y_minor_on = False
        if y_draw_intervals > 8:
            if y_min_value / y_axis_space != y_min_value // y_axis_space:
                start_value = int(np.ceil(y_min_value / y_axis_space)) * y_axis_space
            else:
                start_value = y_min_value

            y_values = list(np.arange(start_value, y_max_value + 0.001, y_axis_space))
            y_sub_start_value = y_values[0] - np.floor(
                (y_values[0] - y_min_value) / y_sub_axis_space) * y_sub_axis_space
            y_sub_values = list(np.arange(y_sub_start_value, y_max_value + 0.001, y_sub_axis_space))

        else:
            y_values = list(np.arange(y_min_value, y_max_value + 0.001, y_axis_space))
            y_sub_values = y_values

        for index, y_value in enumerate(y_values):
            y_value = int(y_value)
            if y_value < 0:
                y_labels.append(str(np.abs(y_value)) + 'S')
            elif y_value == 0:
                y_labels.append('EQ')
            elif y_value > 0:
                y_labels.append(str(np.abs(y_value)) + 'N')

        # y_values = [list(y_axis_data).index(y_value) for y_value in y_values]
        # y_sub_values = [list(y_axis_data).index(y_sub_value) for y_sub_value in y_sub_values]

    elif y_type == 'time':
        time_type = request_dict.get('time_type')
        y_labels, y_sub_values, y_values = get_axis_by_time_type(time_type, y_labels, y_max_value, y_min_value,
                                                                 y_sub_values, y_values)
        # 转换为下标
        y_values = [list(y_axis_data).index(y_value) for y_value in y_values]
        if y_sub_values:
            y_sub_values = [list(y_axis_data).index(y_sub_value) for y_sub_value in y_sub_values]

    request_dict['y_values'] = y_values
    request_dict['y_labels'] = y_labels
    request_dict['y_sub_values'] = y_sub_values
    return y_labels, y_sub_values, y_values


def get_axis_by_time_type(time_type, labels, max_value, min_value, sub_values, values):
    if time_type == 'YEAR':  # 输入格式 YYYY
        year_list = list(range(min_value, max_value + 1))
        times = len(year_list)  # 时间类型的维度的个数
        x_axis_space = match_interval(times, [0, 8, 16, 40, 80, 9999999], [1, 2, 5, 10, (times % 80 + 1) * 10],
                                      None)
        x_sub_axis_space = match_interval(times, [0, 8, 16, 40, 80, 9999999],
                                          [None, 1, 1, 2, (times % 80 + 1) * 2], None)

        if times < 8:
            values = list(range(min_value, max_value + 1, x_axis_space))
            x_minor_on = False  # 此时不需要显示副刻度
            sub_values = None  # 此时无副刻度
        elif times >= 8 and times < 16:
            values = list(range(min_value, max_value + 1, x_axis_space))
            x_minor_on = True
            sub_values = list(range(min_value, max_value + 1))
        elif times >= 16 and times < 40:
            values = [year for year in year_list if year % x_axis_space == 0]  # 去能被间隔整除的年
            x_minor_on = True
            sub_values = list(range(min_value, max_value + 1))
        elif times >= 40:
            values = [year for year in year_list if year % x_axis_space == 0]  # 去能被间隔整除的年
            x_minor_on = True
            x_sub_start_value = values[0] - np.floor(
                (values[0] - min_value) / x_sub_axis_space) * x_sub_axis_space
            sub_values = list(np.arange(x_sub_start_value, max_value + 1, x_sub_axis_space))

        labels = [str(x_value) for x_value in values]

        # 重新赋值给x_values ,这里用的下标
        values = [year_list.index(x_value) for x_value in values]
        sub_values = [year_list.index(x_sub_value) for x_sub_value in sub_values]
    elif time_type == 'MON':  # 输入格式 YYYYMM
        # 获取这段时间内的所有月份列表
        month_list = get_each_month(str(min_value), str(max_value))
        times = len(month_list)
        if (times < 8):
            values = month_list

            individual_years_indexes = get_individual_years_indexes(values)
            labels = [get_month_abbr(str(x_value)[-2:]) for x_value in values]  # 先变成MM
            for individual_years_index in individual_years_indexes:
                labels[individual_years_index] = get_month_abbr(
                    str(values[individual_years_index])[-2:]) + str(values[individual_years_index])[
                                                                :4]  # 年首标MMYYYY

            x_minor_on = False  # 此时不需要显示副刻度
            sub_values = None  # 此时无副刻度

        elif times >= 8 and times < 16:
            values = [month for month in month_list if month % 2 != 0]  # 要奇数月！

            individual_years_indexes = get_individual_years_indexes(values)
            labels = [get_month_abbr(str(x_value)[-2:]) for x_value in values]  # 先变成MM
            for individual_years_index in individual_years_indexes:
                labels[individual_years_index] = get_month_abbr(
                    str(values[individual_years_index])[-2:]) + str(values[individual_years_index])[
                                                                :4]  # 年首标MMYYYY

            x_minor_on = True  # 需要显示副刻度
            sub_values = month_list  # 次数副刻度间隔为1，此时主副刻度可重合！


        elif times >= 16 and times < 25:
            values = [month for month in month_list if
                      str(month)[-2:] in ['01', '04', '07', '10']]  # 找到 month_list 中的1,4,7,10月

            individual_years_indexes = get_individual_years_indexes(values)
            labels = [get_month_abbr(str(x_value)[-2:]) for x_value in values]  # 先变成MM
            for individual_years_index in individual_years_indexes:
                labels[individual_years_index] = get_month_abbr(
                    str(values[individual_years_index])[-2:]) + str(values[individual_years_index])[
                                                                :4]  # 年首标MMYYYY

            x_minor_on = True  # 需要显示副刻度
            sub_values = month_list  # 次数副刻度间隔为1，此时主副刻度可重合！

        elif times >= 25 and times < 48:
            values = [month for month in month_list if
                      str(month)[-2:] in ['01', '07']]  # 找到 month_list 中的1,7月

            individual_years_indexes = get_individual_years_indexes(values)
            labels = [get_month_abbr(str(x_value)[-2:]) for x_value in values]  # 先变成MM
            for individual_years_index in individual_years_indexes:
                labels[individual_years_index] = get_month_abbr(
                    str(values[individual_years_index])[-2:]) + str(values[individual_years_index])[
                                                                :4]  # 年首标MMYYYY

            x_minor_on = True  # 需要显示副刻度
            sub_values = month_list  # 次数副刻度间隔为1，此时主副刻度可重合！

        elif times >= 48:
            values = [month for month in month_list if str(month)[-2:] == '01']  # 找到 month_list中的1月

            labels = [str(x_value)[:4] for x_value in values]  # 全部标年YYYY

            x_minor_on = True  # 需要显示副刻度
            sub_values = [month for month in month_list if
                          str(month)[-2:] in ['04', '07', '10']]  # 次数副刻度间隔为1，此时主副刻度可重合！

    elif time_type == 'DAY':
        # x_axis_space = match_interval(times, [0,8,16,40,90,125,240,367,99999999], [1,2,5,10,15,30,30,30], None)
        # x_sub_axis_space = match_interval(times, [0,8,16,40,90,125,240,367,99999999], [None, 1, 1, 5, 5, 15,15,15], None)
        day_list = get_each_day(str(min_value), str(max_value))
        times = len(day_list)
        if times < 8:
            values = day_list

            individual_years_indexes = get_individual_years_indexes(values)
            labels = [get_day_month(day) for day in day_list]  # MMDD
            for individual_years_index in individual_years_indexes:
                labels[individual_years_index] = get_day_month_year(
                    values[individual_years_index])  # 每首次出现的年日期，都必须得标年

            x_minor_on = False  # 此时不需要显示副刻度
            sub_values = None  # 此时无副刻度

        elif times >= 8 and times < 16:
            # x_values = list(range(day_list[0], day_list[-1] + 1, 2))  # 从第一天开始，隔两天
            values = [day for day in day_list if day_list.index(day) % 2 == 0]  # 从第一天开始，隔两天

            individual_years_indexes = get_individual_years_indexes(values)
            labels = [get_day_month(day) for day in values]  # MMDD
            for individual_years_index in individual_years_indexes:
                labels[individual_years_index] = get_day_month_year(
                    values[individual_years_index])  # 每首次出现的年日期，都必须得标年

            x_minor_on = True  # 需要显示副刻度
            sub_values = day_list  # 次数副刻度间隔为1，此时主副刻度可重合！

        elif times >= 16 and times < 40:
            values = [day for day in day_list if str(day)[-2:] in ['01', '06', '11', '16', '21',
                                                                   '26']]  # 日期在 '01','06','11','16','21','26'

            individual_years_indexes = get_individual_years_indexes(values)
            labels = [get_day_month(day) for day in values]  # MMDD
            for individual_years_index in individual_years_indexes:
                labels[individual_years_index] = get_day_month_year(
                    values[individual_years_index])  # 每首次出现的年日期，都必须得标年

            x_minor_on = True  # 需要显示副刻度
            sub_values = day_list  # 次数副刻度间隔为1，此时主副刻度可重合！


        elif times >= 40 and times < 90:
            values = [day for day in day_list if str(day)[-2:] in ['01', '11', '21']]  # 日期在 '01','11','21'

            individual_years_indexes = get_individual_years_indexes(values)
            labels = [get_day_month(day) for day in values]  # MMDD
            for individual_years_index in individual_years_indexes:
                labels[individual_years_index] = get_day_month_year(
                    values[individual_years_index])  # 每首次出现的年日期，都必须得标年

            x_minor_on = True  # 需要显示副刻度
            sub_values = [day for day in day_list if
                          str(day)[-2:] in ['06', '16', '26']]  # 日期在 '06','16','26'

        elif times >= 90 and times < 125:
            values = [day for day in day_list if str(day)[-2:] in ['01', '16']]  # 日期在 '01','16'

            individual_years_indexes = get_individual_years_indexes(values)
            labels = [get_day_month(day) for day in values]  # MMDD
            for individual_years_index in individual_years_indexes:
                labels[individual_years_index] = get_day_month_year(
                    values[individual_years_index])  # 每首次出现的年日期，都必须得标年

            x_minor_on = True  # 需要显示副刻度
            sub_values = [day for day in day_list if
                          str(day)[-2:] in ['06', '11', '16', '21', '26']]  # 日期在 '06', '11','16', '21','26'

        elif times >= 125 and times < 240:
            values = [day for day in day_list if str(day)[-2:] == '01']  # 找到 month_list中的01日

            individual_years_indexes = get_individual_years_indexes(values)
            labels = [get_month_abbr(str(day)[4:6]) for day in values]  # 此时标记为 MM
            for individual_years_index in individual_years_indexes:
                labels[individual_years_index] = get_month_year(
                    str(values[individual_years_index])[:6])  # 每首次出现的年日期，标记为MMYYYY

            x_minor_on = True  # 需要显示副刻度
            sub_values = [day for day in day_list if str(day)[-2:] == '16']  # 日期在 '16'

        else:
            # 获取日期间的月份
            values = [day for day in day_list if str(day)[-2:] == '01']
            labels = [get_month_abbr(str(day)[4:6]) for day in values]
            individual_years_indexes = get_individual_years_indexes(values)
            for individual_years_index in individual_years_indexes:
                labels[individual_years_index] = get_month_year(
                    str(values[individual_years_index])[:6])  # 每首次出现的年日期，标记为MMYYYY
            sub_values = None
    elif time_type == 'FIVE':  # 中国候 YYYYMMHH
        five_list = get_five_list(str(min_value), str(max_value))  # 注意这个地方返回的 str格式！！！！！！
        times = len(five_list)
        if times < 48:
            values = [int(five) for five in five_list if five[-2:] in ['01', '03', '05']]  # 主刻度只显示每月的010305候
            labels = [str(x_value) for x_value in values]

            # 先把每月的01候位置搞到，需要变成YYYYMM
            first_month_values = [x_value for x_value in values if str(x_value).endswith('01')]
            first_year_month_indexes = []
            # 找到首年首月的值
            individual_years_indexes = get_individual_years_indexes(first_month_values)
            for individual_years_index in individual_years_indexes:
                first_year_month_indexes.append(values.index(first_month_values[individual_years_index]))
            # 找到所有0305候的值
            third_or_five_values = [x_value for x_value in values if str(x_value)[-2:] in ['03', '05']]

            for first_month_value in first_month_values:
                index = labels.index(str(first_month_value))
                if index != -1:
                    labels[index] = get_month_abbr(labels[index][4:6])
            for first_year_month_index in first_year_month_indexes:
                labels[first_year_month_index] = str(values[first_year_month_index])[:4] + get_month_abbr(
                    str(values[first_year_month_index])[4:6])
            for third_or_five_value in third_or_five_values:
                index = values.index(third_or_five_value)
                if index != -1:
                    last_two_number = str(third_or_five_value)[-2:]
                    if last_two_number.startswith('0'):
                        last_two_number = last_two_number[-1]
                    labels[index] = last_two_number

            x_minor_on = True
            sub_values = [int(five) for five in five_list if five[-2:] in ['02', '04', '06']]  # 副刻度为02/04/06


        elif times >= 48:
            values = [int(five) for five in five_list if five[-2:] == '01']  # 主刻度只显示每月的01候
            month_list = [str(x_value)[:6] for x_value in values]
            individual_years_indexes = get_individual_years_indexes(month_list)
            labels = [get_month_abbr(month[-2:]) for month in month_list]  # 先变成MM
            for individual_years_index in individual_years_indexes:
                labels[individual_years_index] = get_month_abbr(
                    str(month_list[individual_years_index])[-2:]) + str(month_list[individual_years_index])[
                                                                    :4]  # 年首标MMYYYY

    elif time_type == 'FIVEYEAR':
        five_year_list, year_list = get_each_fiveyear(max_value, min_value)
        times = len(five_year_list)  # 时间类型的维度的个数

        if times < 8:
            values = five_year_list
            sub_values = None  # 此时无副刻度
        elif times >= 8 and times < 16:
            values = five_year_list[::2]  # 偶数位
            sub_values = None  # 此时无副刻度
        else:
            interval_fiveyear = math.floor(times / 8) + 1
            values = five_year_list[::interval_fiveyear]
            sub_values = None  # 此时无副刻度

        yaer_labels = [x_value // 100 for x_value in values]
        first_year_fiveyear_indexes = [yaer_labels.index(year) for year in year_list]
        five_year_time_start = ["0101", "0106", "0111", "0116", "0121", "0126", "0131", "0205", "0210", "0215",
                                "0220",
                                "0225", "0302", "0307", "0312", "0317", "0322", "0327", "0401", "0406", "0411",
                                "0416",
                                "0421", "0426", "0501", "0506", "0511", "0516", "0521", "0526", "0531", "0605",
                                "0610",
                                "0615", "0620", "0625", "0630", "0705", "0710", "0715", "0720", "0725", "0730",
                                "0804",
                                "0809", "0814", "0819", "0824", "0829", "0903", "0908", "0913", "0918", "0923",
                                "0928",
                                "1003", "1008", "1013", "1018", "1023", "1028", "1102", "1107", "1112", "1117",
                                "1122",
                                "1127", "1202", "1207", "1212", "1217", "1222", "1227"]
        labels = []
        for x_index, x_value in enumerate(values):
            x_fiveyear = x_value % 100
            x_label = five_year_time_start[x_fiveyear - 1]
            if x_index in first_year_fiveyear_indexes:
                x_year = x_value // 100
                x_label = str(x_year) + x_label
            labels.append(x_label)

        # labels = [str(x_value) for x_value in values]

    elif time_type == 'SEASON':
        season_list = get_seasons_list(str(min_value), str(max_value))
        times = len(season_list)
        # 时间长度小于12，全部展示
        if times <= 12:
            values = [int(x_value) for x_value in season_list]
            labels = [
                x_value[:4] + x_value[4:].replace("01", "SPR").replace("02", "SUM").replace("03", "AUT").replace("04",
                                                                                                                 "WIN") if x_value[
                                                                                                                           4:] == "04" else x_value[
                                                                                                                                            4:].replace(
                    "01", "SPR").replace("02", "SUM").replace("03", "AUT").replace("04", "WIN") for x_value in
                season_list]
        elif times <= 24: # 时间长度小于24，间隔一位展示，且展示冬季和夏季
            sub_values = [int(x_value) for x_value in season_list if x_value[-2:] in ['01', '03']]
            season_list = [item for item in season_list if item[-2:] in ['04', '02']]
            values = [int(x_value) for x_value in season_list]
            labels = [
                x_value[:4] + x_value[4:].replace("01", "SPR").replace("02", "SUM").replace("03", "AUT").replace("04",
                                                                                                                 "WIN") if x_value[
                                                                                                                           4:] == "04" else x_value[
                                                                                                                                            4:].replace(
                    "01", "SPR").replace("02", "SUM").replace("03", "AUT").replace("04", "WIN") for x_value in
                season_list]
        else: # 时间长度大于24，只展示冬季，间隔4
            sub_values = [int(x_value) for x_value in season_list if x_value[-2:] in ['01', '02', '03']]
            season_list = [item for item in season_list if item[-2:] in ['04']]
            values = [int(x_value) for x_value in season_list]
            labels = [
                x_value[:4] + x_value[4:].replace("01", "SPR").replace("02", "SUM").replace("03", "AUT").replace("04",
                                                                                                                 "WIN") if x_value[
                                                                                                                           4:] == "04" else x_value[
                                                                                                                                            4:].replace(
                    "01", "SPR").replace("02", "SUM").replace("03", "AUT").replace("04", "WIN") for x_value in
                season_list]
    return labels, sub_values, values


def get_each_fiveyear(max_value, min_value):
    min_year = min_value // 100
    min_five_year = min_value % 100
    max_year = max_value // 100
    max_five_year = max_value % 100
    if max_year - min_year == 0:
        five_year_list = list(range(min_value, max_value + 1))
    elif max_year - min_year == 1:
        min_five_year_list = list(range(min_value, min_year * 100 + 73 + 1))
        max_five_year_list = list(range(max_year * 100 + 1, max_value + 1))
        five_year_list = min_five_year_list + max_five_year_list
    elif max_year - min_year > 1:
        min_five_year_list = list(range(min_value, min_year * 100 + 73 + 1))
        max_five_year_list = list(range(max_year * 100 + 1, max_value + 1))
        year_list = list(range(min_year, max_year + 1))
        year_list.remove(min_year)
        year_list.remove(max_year)
        middle_five_year_list = []
        for middle_year in year_list:
            for i in range(1, 74):
                middle_five_year_list.append(middle_year * 100 + i)
        five_year_list = min_five_year_list + middle_five_year_list
        five_year_list = five_year_list + max_five_year_list
    five_year_list.sort()
    year_list = list(range(min_year, max_year + 1))
    return five_year_list, year_list
