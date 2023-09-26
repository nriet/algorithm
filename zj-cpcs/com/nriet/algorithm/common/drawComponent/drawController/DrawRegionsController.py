# -*- coding:utf-8 -*-


import importlib, sys

importlib.reload(sys)
from mpl_toolkits.basemap import Basemap
# matplotlib升级为3.3.4
# 因为函数名变更，需要修改basemap下__init__.py文件和proj.py文件的import部分
import os, uuid, ast, itertools
import importlib
import pandas as pd

importlib.reload(sys)
import traceback

sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))))
import copy
import math
from PIL import ImageFont
import time, io
import matplotlib
import PIL.Image as Image
import matplotlib.patches as mpatches
from com.nriet.config import ResponseCodeAndMsgEum
from matplotlib import font_manager
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.utils.obs.ObsUtils import ObsUtils

matplotlib.use('Agg')

from com.nriet.utils.result.ResponseResultUtils import build_response_dict, judge_response_result, \
    response_result_convert
from com.nriet.config.ResponseCodeAndMsgEum import SERVER_HANDLING_ERROR_CODE, CIPAS_SUCCESS_CODE, \
    PARAMETER_VALUE_MISSING_CODE
import matplotlib.ticker as ticker
from com.nriet.algorithm.common.drawComponent.util import Maskout
from matplotlib.patches import Polygon
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from com.nriet.utils import matchUtils
from com.nriet.algorithm import Component
from com.nriet.config import PathConfig
from com.nriet.utils.result.ResponseResultUtils import build_response_dict
from com.nriet.utils.matchUtils import match_interval_decimal
from matplotlib.ticker import AutoMinorLocator, MultipleLocator
import numpy as np
import json, logging

logging.info("Project root path is : %s" % os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))))
import matplotlib.colors as mcolors
import xarray as xr
from scipy.ndimage import gaussian_filter


class DrawRegionsController():
    def __init__(self, sub_local_params: dict):
        self.request_dict = sub_local_params
        self.areaName = sub_local_params.get("areaName")
        self.mainTitle = sub_local_params.get("main_title")
        self.subTitles = sub_local_params.get("sub_titles")
        self.output_img_path = sub_local_params.get("output_img_path")
        self.output_img_name = sub_local_params.get("output_img_name")
        self.output_img_type = sub_local_params.get("output_img_type")
        # self.sublevs = sub_local_params.get("intervals")
        # self.colors = sub_local_params.get("colors")
        self.unit = sub_local_params.get("unit")
        self.data_source = sub_local_params.get("data_source")
        self.note = sub_local_params.get("note")
        self.islogo = sub_local_params.get("islogo")
        # self.marker_size = sub_local_params.get("marker_size")
        self.layers = sub_local_params.get("layers")
        self.shpInfo = sub_local_params.get("shpInfo")
        input_data_variables = sub_local_params.get("input_data_variables")
        input_data_name = sub_local_params.get("input_data_name")
        input_data_path = sub_local_params.get("input_data_path")
        # 1、调用obs接口下载文件，数据以bytes类型返回，结果在content属性下
        backet_name = look_for_single_global_config(key="OBS_BUCKET_NAME")
        result_dict = ObsUtils().download_file(backet_name, input_data_name)
        if not judge_response_result:
            raise AlgorithmException(response_code=judge_response_result['response_code'],
                                     response_msg=judge_response_result["response_msg"])
        input_data_set = xr.open_dataset(result_dict['content'])

        # input_data_set = xr.open_dataset(input_data_path + input_data_name)
        # self.data = input_data_set[individual_var]

        algorithm_input_data = []

        for var_index, var in enumerate(input_data_variables):
            if isinstance(var, list):
                tmp_dict_list = []
                for individual_var in var:
                    tmp_dict = {}
                    tmp_dict['outputData'] = input_data_set[individual_var]
                    tmp_dict_list.append(tmp_dict)
                algorithm_input_data.append(tmp_dict_list)
            else:
                tmp_dict = {}
                tmp_dict['outputData'] = input_data_set[var]
                algorithm_input_data.append(tmp_dict)

        # 1.3 确定绘图数据self.input_data
        self.input_data = []
        for index, input_data in enumerate(algorithm_input_data):
            if isinstance(input_data, list):
                self.input_data.append([])
                for ind, data in enumerate(input_data):
                    self.input_data[index].append(data["outputData"])
            else:
                self.input_data.append((input_data["outputData"]))

    def execute(self):
        '''
        绘图组件入口的执行方法
        :param input_data:  待绘图数据，是一个一维数组
        :param lon: 经度数据，是一个一维数组
        :param lat: 纬度数据，是一个一维数组
        :param request_json: 业务相关参数json
        :return:
        '''
        start_time = time.clock()
        areaName = self.areaName
        mainTitle = self.mainTitle
        subTitles = self.subTitles
        output_img_path = self.output_img_path
        output_img_name = self.output_img_name
        output_img_type = self.output_img_type
        request_dict = self.request_dict
        data = self.input_data
        islogo = self.islogo
        layers = self.layers

        try:
            draw_result = validation_params(data, request_dict)
            fontFile = PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC"
            configPath = PathConfig.CPCS_ROOT_PATH + 'com/nriet/config/regionConfig.json'
            font1 = FontProperties(fname=fontFile)

            # 读取配置文件
            with open(configPath, "r", encoding='UTF-8') as f:
                datastr = f.read()
            data_config = json.loads(datastr)
            # 获取传参区域的参数
            if "," in areaName:
                areaConfig = data_config.get(areaName.split(",")[0])
                # 获取传参区域的中文名称
                chineseName = areaName.split(",")
                # 获取传参区域的绘图区域范围
                areaRegions = get_regions(data_config, areaName)
                startLon, endLon, startLat, endLat = [float(i) for i in areaRegions.split(',')]
                r = (endLat - startLat) / (endLon - startLon)
                y1, y2, y3, y4, logo_size = get_params(r)
            else:
                areaConfig = data_config.get(areaName)
                # 获取传参区域的中文名称
                chineseName = areaConfig.get('name')
                # 获取传参区域的绘图区域范围
                areaRegions = areaConfig.get('regions')
                startLon, endLon, startLat, endLat = [float(i) for i in areaRegions.split(',')]
                r = (endLat - startLat) / (endLon - startLon)
                y1 = areaConfig.get('y1')
                y2 = areaConfig.get('y2')
                y3 = areaConfig.get('y3')
                y4 = areaConfig.get('y4')
                logo_size = areaConfig.get('logo_size')
            # 获取传参区域的shp标识
            label = areaConfig.get('label')
            # 获取传参区域掩膜shp文件的位置
            shpFile = areaConfig.get('shpFile')
            # 获取图例位置
            barloc = areaConfig.get('loc')
            uptitle = areaConfig.get('uptitle')
            # 获取主标题的偏移度
            y_pad_main = areaConfig.get('y_pad_main')
            # 获取副标题的偏移度
            y_pad_sub = areaConfig.get('y_pad_sub')
            # 设置fig像素
            width = 2000
            if (endLon - startLon) > (endLat - startLat):
                height = 2000
            else:
                if r < 1.5:
                    height = 3000
                else:
                    height = 2000 * r
            fig = plt.figure(figsize=(width / 100, height / 100))
            # 设置图片个数及位置
            ax = fig.add_subplot(111)
            rate = (endLat - startLat) / (endLon - startLon) * width / height
            if uptitle:
                ax.set_position([0.08, 1 - (0.85 * rate + 0.1), 0.85, 0.85 * rate])
            else:
                ax.set_position([0.08, 1 - (0.85 * rate + 0.05), 0.85, 0.85 * rate])

            # 创建地图 标识为m
            m = Basemap(llcrnrlon=startLon, urcrnrlon=endLon, llcrnrlat=startLat, urcrnrlat=endLat, projection='cyl')
            # m = Basemap(llcrnrlon=77, urcrnrlon=140, llcrnrlat=14, urcrnrlat=51, lon_0=110, lat_1=33, lat_2 = 45, projection='lcc')

            c_bar = ""
            for i, layer in enumerate(layers):
                layer_type = layer['layer_type']  # 当前图层的类型
                layer_data = data[i]  # 当前图层的绘图数据
                if layer_type == "contourMap":  # 色斑图层
                    # 获取值色对
                    sublevs = layer.get('intervals')
                    colors = layer.get('colors')
                    legend_labels = layer.get('legend_labels')
                    ch_legend_labels = layer.get('ch_legend_labels')
                    # labels未设置时， 默认使用 intervals
                    labels = layer.get('labels', sublevs.copy())
                    # 设置缺测图例 灰色
                    isNaN = layer.get('isNaN', "False")
                    if isNaN == "True":
                        colors.insert(0, [0.67, 0.67, 0.67])
                        sublevs.insert(0, -999.0)
                        if labels:
                            labels.insert(0, 'NaN')
                        if legend_labels:
                            legend_labels.insert(0, 'NaN')
                        if ch_legend_labels:
                            ch_legend_labels.insert(0, '缺测')
                    # 设置levs
                    levs_map = [-9999.0]
                    endlevs = [9999.0]
                    levs_map.extend(sublevs)
                    levs_map.extend(endlevs)
                    # 标准化颜色
                    ccolors = [RGB_to_Hex(i) for i in colors]
                    my_cmap = mcolors.ListedColormap(ccolors)
                    norm = mcolors.BoundaryNorm(levs_map, my_cmap.N)
                    # 根据绘图经纬度截取数据
                    lon = layer_data["lon"]
                    lat = layer_data["lat"]
                    lon = lon[(lon >= startLon - 2.5) & (lon <= endLon + 2.5)]
                    lat = lat[(lat >= startLat - 2.5) & (lat <= endLat + 2.5)]
                    layer_data = layer_data.sel(lon=lon, lat=lat)
                    # 创建地图网格
                    xx, yy = np.meshgrid(layer_data['lon'], layer_data['lat'])
                    # 绘制色斑
                    cf = m.contourf(xx, yy, layer_data, levels=levs_map, cmap=my_cmap, norm=norm)
                    # 色斑掩膜处理
                    clip = Maskout.shp2clip(cf, ax, m, shpFile, chineseName, label)
                    c_bar = cf

                if layer_type == "rasterFill":  # 栅格图层
                    # 获取值色对
                    sublevs = layer.get('intervals')
                    colors = layer.get('colors')
                    legend_labels = layer.get('legend_labels')
                    ch_legend_labels = layer.get('ch_legend_labels')
                    # labels未设置时， 默认使用 intervals
                    labels = layer.get('labels', sublevs.copy())
                    # 设置缺测图例 灰色
                    isNaN = layer.get('isNaN', "False")
                    if isNaN == "True":
                        colors.insert(0, [0.67, 0.67, 0.67])
                        sublevs.insert(0, -999.0)
                        if labels:
                            labels.insert(0, 'NaN')
                        if legend_labels:
                            legend_labels.insert(0, 'NaN')
                        if ch_legend_labels:
                            ch_legend_labels.insert(0, '缺测')
                    # 设置levs
                    levs_map = [-9999.0]
                    endlevs = [9999.0]
                    levs_map.extend(sublevs)
                    levs_map.extend(endlevs)
                    # 标准化颜色
                    ccolors = [RGB_to_Hex(i) for i in colors]
                    my_cmap = mcolors.ListedColormap(ccolors)
                    norm = mcolors.BoundaryNorm(levs_map, my_cmap.N)
                    # 根据绘图经纬度截取数据
                    lon = layer_data["lon"]
                    lat = layer_data["lat"]
                    lon = lon[(lon >= startLon - 2.5) & (lon <= endLon + 2.5)]
                    lat = lat[(lat >= startLat - 2.5) & (lat <= endLat + 2.5)]
                    layer_data = layer_data.sel(lon=lon, lat=lat)
                    # 创建地图网格
                    xx, yy = np.meshgrid(layer_data['lon'], layer_data['lat'])
                    # 绘制色斑
                    cf = m.pcolormesh(xx, yy, layer_data, cmap=my_cmap, norm=norm)
                    # 色斑掩膜处理
                    clip = Maskout.shp2clip(cf, ax, m, shpFile, chineseName, label, vcplot=True)
                    if c_bar:
                        continue
                    else:
                        c_bar = cf

                if layer_type == "contourLine":  # 等值线图层
                    # 获取间隔值
                    levs = layer.get('intervals')
                    contour_line_labels = []
                    for inv in layer.get('intervals'):
                        if str(inv).endswith(".0"):
                            contour_line_labels.append(str(int(inv)))
                        else:
                            contour_line_labels.append(str(inv))
                    # 获取
                    if layer.get('contour_line_labels'):
                        contour_line_labels = layer.get('contour_line_labels')

                    # 匹配format
                    fmt = {}
                    for item, lev in enumerate(levs):
                        fmt[lev] = contour_line_labels[item]

                    # contour_line_space = layer.get('contour_line_space')
                    contour_line_color = layer.get('contour_line_color', 'black')
                    if "," in contour_line_color:
                        contour_line_color = RGB_to_Hex_str(contour_line_color)
                    # contour_line_colors = layer.get('contour_line_colors')
                    line_thickness = float(layer.get('line_thickness', 1.5))
                    # line_thicknesses = layer.get('line_thicknesses')
                    contour_line_types = layer.get('contour_line_types', 'solid')
                    cnLineMax = float(layer.get('cnLineMax')) if layer.get('cnLineMax') else None
                    cnLineMin = float(layer.get('cnLineMin')) if layer.get('cnLineMin') else None

                    lon = layer_data["lon"]
                    lat = layer_data["lat"]
                    lon = lon[(lon >= startLon - 2.5) & (lon <= endLon + 2.5)]
                    lat = lat[(lat >= startLat - 2.5) & (lat <= endLat + 2.5)]
                    layer_data = layer_data.sel(lon=lon, lat=lat)
                    # 创建地图网格
                    xx, yy = np.meshgrid(layer_data['lon'], layer_data['lat'])
                    cs = m.contour(xx, yy, layer_data, levels=levs, colors=contour_line_color, vmin=cnLineMin,
                                   vmax=cnLineMax, linewidths=line_thickness, linestyles=contour_line_types)
                    cn_label = ax.clabel(cs, inline=True, fontsize=20, fmt=fmt)
                    clip = Maskout.shp2clip(cs, ax, m, shpFile, chineseName, label, clabel=cn_label)

                if layer_type == "vector":  # 风场图层
                    vector_scale = float(layer.get('vector_scale')) if layer.get('vector_scale') else None
                    vector_unit = layer.get('vector_unit', "m/s")
                    # vector_unit = layer.get('vector_unit')
                    lon = layer_data[0]["lon"]
                    lat = layer_data[0]["lat"]
                    lon = lon[(lon >= startLon - 2.5) & (lon <= endLon + 2.5)]
                    lat = lat[(lat >= startLat - 2.5) & (lat <= endLat + 2.5)]
                    layer_data[0] = layer_data[0].sel(lon=lon, lat=lat)
                    layer_data[1] = layer_data[1].sel(lon=lon, lat=lat)
                    # 创建地图网格
                    xx, yy = np.meshgrid(layer_data[0]['lon'], layer_data[0]['lat'])
                    cq = m.quiver(xx, yy, layer_data[0], layer_data[1], scale=vector_scale, scale_units='inches',
                                  color='black', width=0.002, latlon=True)
                    font_vc = FontProperties(fname=fontFile, size=20)
                    if vector_scale:
                        plt.quiverkey(cq, 0.95, 0.95, vector_scale, str(vector_scale) + vector_unit, labelpos='S',
                                      fontproperties=font_vc)
                    clip = Maskout.shp2clip(cq, ax, m, shpFile, chineseName, label, vcplot=True)

                if layer_type == "streamLine":  # 流线图层
                    lon = layer_data[0]["lon"]
                    lat = layer_data[0]["lat"]
                    lon = lon[(lon >= startLon - 2.5) & (lon <= endLon + 2.5)]
                    lat = lat[(lat >= startLat - 2.5) & (lat <= endLat + 2.5)]
                    layer_data[0] = layer_data[0].sel(lon=lon, lat=lat)
                    layer_data[1] = layer_data[1].sel(lon=lon, lat=lat)
                    # 创建地图网格
                    xx, yy = np.meshgrid(layer_data[0]['lon'], layer_data[0]['lat'])
                    cq = m.streamplot(xx, yy, layer_data[0], layer_data[1], density=3, linewidth=1.0, color='black',
                                      minlength=0.1, maxlength=4.0, arrowsize=2, arrowstyle='simple', latlon=True)

                if layer_type == "polyMarker":  # 散点图层
                    if layer.get('colors'):
                        # 获取值色对
                        sublevs = layer.get('intervals')
                        colors = layer.get('colors')
                        legend_labels = layer.get('legend_labels')
                        ch_legend_labels = layer.get('ch_legend_labels')
                        # labels未设置时， 默认使用 intervals
                        labels = layer.get('labels', sublevs.copy())
                        # 设置缺测图例 灰色
                        isNaN = layer.get('isNaN', "False")
                        if isNaN == "True":
                            colors.insert(0, [0.67, 0.67, 0.67])
                            sublevs.insert(0, -999.0)
                            if labels:
                                labels.insert(0, 'NaN')
                            if legend_labels:
                                legend_labels.insert(0, 'NaN')
                            if ch_legend_labels:
                                ch_legend_labels.insert(0, '缺测')
                        # 设置levs
                        levs_map = [-9999.0]
                        endlevs = [9999.0]
                        levs_map.extend(sublevs)
                        levs_map.extend(endlevs)
                        # 标准化颜色
                        ccolors = [RGB_to_Hex(i) for i in colors]
                        my_cmap = mcolors.ListedColormap(ccolors)
                        norm = mcolors.BoundaryNorm(levs_map, my_cmap.N)
                    if layer.get('marker_size'):
                        marker_size = layer.get('marker_size')
                    else:
                        marker_size = areaConfig.get('marker_size', 350)

                    marker_type = layer.get('marker_type', "o")

                    marker_color = layer.get('marker_color', 'black')

                    lons = list(layer_data.attrs["lons"])
                    lats = list(layer_data.attrs["lats"])
                    # 获取基本属性
                    data_dict = {
                        "data": layer_data,
                        "lons": lons,
                        "lats": lats
                    }
                    layer_data = pd.DataFrame(data_dict)
                    '''
                    缺测值打点
                    '''
                    nan_row_indexes = list(np.where(pd.isna(layer_data))[0])
                    nan_data = np.ma.array(layer_data.iloc[nan_row_indexes, 0])
                    nan_lons = np.ma.array(layer_data.iloc[nan_row_indexes, 1])
                    nan_lats = np.ma.array(layer_data.iloc[nan_row_indexes, 2])
                    cm = m.scatter(nan_lons, nan_lats, marker=marker_type, s=int(marker_size), c="#ABABAB")
                    '''
                    剔除缺测值过后,打点绘图
                    '''
                    input_data = layer_data.dropna(axis=0, how='any')
                    data = np.ma.array(input_data.iloc[:, 0])
                    lons = np.ma.array(input_data.iloc[:, 1])
                    lats = np.ma.array(input_data.iloc[:, 2])
                    if layer.get('colors'):
                        cm = m.scatter(lons, lats, marker=marker_type, s=int(marker_size), c=data, cmap=my_cmap,
                                       norm=norm)
                    else:
                        if layer.get('marker_color') is None and "my_cmap" in locals().keys() and "norm" in locals().keys():
                            cm = m.scatter(lons, lats, marker=marker_type, s=int(marker_size), c=data, cmap=my_cmap,
                                           norm=norm)
                        else:
                            cm = m.scatter(lons, lats, marker=marker_type, s=int(marker_size), c=marker_color)
                        cm = m.scatter(lons, lats, marker=marker_type, s=int(marker_size), c=marker_color)

                    clip = Maskout.shp2clip(cm, ax, m, shpFile, chineseName, label, vcplot=True)
                    if c_bar:
                        continue
                    else:
                        c_bar = cm

            # 裁剪图片经纬度范围
            lon1, lon2 = ax.set_xlim(startLon, endLon)
            lat1, lat2 = ax.set_ylim(startLat, endLat)
            # 自适应经纬度的主副刻度间隔
            lat_axis_major_space = matchUtils.match_interval(endLat - startLat, [0, 1, 3, 8, 16, 41, 90, 181, 361],
                                                             [0.1, 0.5, 1, 2, 5, 10, 30, 60],
                                                             None)
            lat_axis_minor_space = matchUtils.match_interval(endLat - startLat, [0, 1, 3, 8, 16, 41, 90, 181, 361],
                                                             [0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10],
                                                             None)
            lon_axis_major_space = matchUtils.match_interval(endLon - startLon, [0, 1, 3, 8, 16, 41, 90, 181, 361],
                                                             [0.1, 0.5, 1, 2, 5, 10, 30, 60],
                                                             None)
            lon_axis_minor_space = matchUtils.match_interval(endLon - startLon, [0, 1, 3, 8, 16, 41, 90, 181, 361],
                                                             [0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10],
                                                             None)
            # 画纬度
            # parallels = np.arange(startLat, endLat, lat_axis_major_space)  # 主刻度上标注纬度label
            # m.drawparallels(parallels, labels=[1, 0, 0, 0], color='white', dashes=[1, 3], fontproperties=font1, fontsize=30,
            #                 linewidth=0)
            # 画经度
            # meridians = np.arange(startLon, endLon, lon_axis_major_space)  # 主刻度上标注经度label
            # m.drawmeridians(meridians, labels=[0, 0, 0, 1], color='white', dashes=[1, 3], fontproperties=font1, fontsize=30,
            #                 linewidth=0)
            # 设置经纬度刻度
            # ax.xaxis.tick_bottom()
            # lat_tick = np.arange(startLat, endLat, lat_axis_minor_space)  # 纬度刻度
            # lon_tick = np.arange(startLon, endLon, lon_axis_minor_space)  # 经度刻度
            # ax.set_yticks(lat_tick)
            # ax.set_xticks(lon_tick)
            # ax.tick_params(labelcolor='none')
            ax.xaxis.set_major_locator(MultipleLocator(lon_axis_major_space))
            ax.xaxis.set_minor_locator(AutoMinorLocator(lon_axis_major_space / lon_axis_minor_space))
            ax.yaxis.set_major_locator(MultipleLocator(lat_axis_major_space))
            ax.yaxis.set_minor_locator(AutoMinorLocator(lat_axis_major_space / lat_axis_minor_space))
            if areaConfig.get('regions_type'):
                ax.yaxis.set_major_formatter('{x:.1f}°N')
                ax.xaxis.set_major_formatter('{x:.1f}°E')
            else:
                if areaConfig.get('regions_range'):
                    ax.yaxis.set_major_formatter(
                        lambda x, pos: str(round(-x, 1)) + 'S' if x < 0 else 'EQ' if x == 0 else str(round(x, 1)) + 'N')
                    ax.xaxis.set_major_formatter(
                        lambda x, pos: str(round(-x, 1)) + 'W' if x < 0 and x > -180 else str(abs(round(x, 1))) if x in [0, 180, -180] else str(round(x, 1)) + 'E')
                else:
                    ax.yaxis.set_major_formatter(
                        lambda x, pos: str(int(-x)) + 'S' if x < 0 else 'EQ' if x == 0 else str(int(x)) + 'N')
                    ax.xaxis.set_major_formatter(
                        lambda x, pos: str(int(-x)) + 'W' if x < 0 and x > -180 else str(abs(int(x))) if x in [0, 180, -180] else str(int(x)) + 'E')
            for xlabel in ax.get_xticklabels():
                xlabel.set_fontproperties(font1)
            for ylabel in ax.get_yticklabels():
                ylabel.set_fontproperties(font1)
            ax.tick_params(which='major', labelsize=30, length=15, width=3.0)
            ax.tick_params(which='minor', labelsize=30, length=10, width=2.0)
            # 读取并叠加shp文件
            if areaConfig.get('shp'):
                shps_set = areaConfig.get('shp')
                for key in shps_set:
                    tmpshp = shps_set.get(key)
                    # shpColor为16进制标识或系统自带颜色
                    result = m.readshapefile(tmpshp.get('shpFile'), key, color=tmpshp.get('shpColor'),
                                    linewidth=float(tmpshp.get('shpThick')), default_encoding='gbk')
                    if tmpshp.get('shpType'):
                        col = result[-1]
                        col.set_linestyle(tmpshp.get('shpType'))
                    if key == "lake":  # 湖泊填充颜色
                        for shp in m.lake:
                            poly = Polygon(shp, facecolor=tmpshp.get('shpColor'))
                            ax.add_patch(poly)
                    if key == "point":  # 点位位置
                        fontsize = tmpshp.get('labelSize')
                        city = tmpshp.get('cityName')
                        point = tmpshp.get('point','True')
                        x_sub = tmpshp.get('x_sub')
                        y_sub = tmpshp.get('y_sub')
                        addName(m, font1, fontsize, x_sub, y_sub, city, point)
            # 灵活绘制地理信息
            if "," in areaName:
                areaNames_tmp = areaName.split(",")
                areasNum = len(areaNames_tmp)
                for areaName_tmp in areaNames_tmp:
                    areaConfig_tmp = data_config.get(areaName_tmp)
                    if areaConfig_tmp.get('shpInfo') and self.shpInfo:
                        shpInfo = self.shpInfo
                        draw_shpInfo(areaConfig_tmp, shpInfo, m, ax, font1, areasNum)
            else:
                areasNum = 1
                if areaConfig.get('shpInfo') and self.shpInfo:
                    shpInfo = self.shpInfo
                    draw_shpInfo(areaConfig, shpInfo, m, ax, font1, areasNum)

            # 边框加粗
            lines = plt.gca()
            lines.spines['top'].set_linewidth(4)
            lines.spines['bottom'].set_linewidth(4)
            lines.spines['left'].set_linewidth(4)
            lines.spines['right'].set_linewidth(4)
            # 绘制色例
            if c_bar:
                if legend_labels:
                    patch = getColorLabel(colors[::-1], legend_labels[::-1])
                    plt.rcParams['font.sans-serif'] = ['SimHei']  # 显示中文标签
                    plt.rcParams['font.serif'] = ['Arial']
                    plt.rcParams['axes.unicode_minus'] = False
                    font = {'size': "20",
                            'fname': PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC"}
                    lagend_font = font_manager.FontProperties("font", **font)
                    if self.unit:
                        legend_title = "   图例\n单位（" + self.unit + "）"
                    else:
                        legend_title = "   图例"
                    leg = plt.legend(handles=patch, loc=barloc, title=legend_title, title_fontsize=25,
                                     labelcolor='black',
                                     edgecolor='black', framealpha=1, prop=lagend_font, labelspacing=0.2)
                    leg.get_frame().set_linewidth(2.0)
                else:
                    if ch_legend_labels:
                        plt.rcParams['font.sans-serif'] = ['SimHei']  # 显示中文标签
                        plt.rcParams['font.serif'] = ['Arial']
                        coef = (endLon - startLon) / (endLat - startLat)
                        num = str(8 * coef) + "%"
                        sizeNum = str(coef * 3) + "%"
                        bar = m.colorbar(c_bar, location='bottom', size=sizeNum, pad=num)
                        bar.set_ticks(levs_map)
                        if ch_legend_labels:
                            for ii,ch_label in enumerate(ch_legend_labels):
                                levs_map[ii] = "             "+ch_label
                            levs_map[-1] = " "
                        bar.set_ticklabels([str(item) for item in levs_map])
                        for label in [bar.ax.xaxis.get_ticklabels()[0], bar.ax.xaxis.get_ticklabels()[-1]]:
                            label.set_visible(False)
                        bar.ax.tick_params(labelsize=25, labelbottom="labelleft", tick1On=False)
                        bar.ax.set_xlabel(self.unit, labelpad=0.4, loc="right", fontproperties=font1, fontsize=25)
                    else:
                        coef = (endLon - startLon) / (endLat - startLat)
                        num = str(8 * coef) + "%"
                        sizeNum = str(coef * 3) + "%"
                        bar = m.colorbar(c_bar, location='bottom', size=sizeNum, pad=num)
                        bar.set_ticks(levs_map)
                        if labels:
                            levs_map[1:-1] = labels
                        tick_labels = [str(int(i)) if not isinstance(i,str) and i % 1 == 0 else str(i) for i in levs_map]
                        bar.set_ticklabels(tick_labels)
                        for label in [bar.ax.xaxis.get_ticklabels()[0], bar.ax.xaxis.get_ticklabels()[-1]]:
                            label.set_visible(False)
                        bar.ax.tick_params(labelsize=25, tick1On=False)
                        bar.ax.set_xlabel(self.unit, labelpad=0.4, loc="right", fontproperties=font1, fontsize=25)
            # 标题
            title = mainTitle
            subTitle = ""
            if subTitles:
                for i in range(len(subTitles)):
                    subTitle = subTitle + subTitles[i] + "\n"

            if uptitle:
                if len(subTitles) == 1:
                    if y1:
                        plt.title(title, fontproperties=font1, fontsize=35, y=float(y1))
                    else:
                        plt.title(title, fontproperties=font1, fontsize=35, y=1.08)
                    if y2:
                        plt.suptitle(subTitle, fontproperties=font1, fontsize=25, y=float(y2), x=0.505)
                    else:
                        plt.suptitle(subTitle, fontproperties=font1, fontsize=25, y=0.92, x=0.505)
                else:
                    if y3:
                        plt.title(title, fontproperties=font1, fontsize=35, y=float(y3))
                    else:
                        plt.title(title, fontproperties=font1, fontsize=35, y=1.12)
                    if y4:
                        plt.suptitle(subTitle, fontproperties=font1, fontsize=25, y=float(y4), x=0.505)
                    else:
                        plt.suptitle(subTitle, fontproperties=font1, fontsize=25, y=0.94, x=0.505)
            else:
                plt.title(title, fontproperties=font1, fontsize=35, y=1 - 100 / (height * 0.85 * rate))
                plt.suptitle(subTitle, fontproperties=font1, fontsize=25, y=0.95 - 120 / height, x=0.505)
            # 数据源等信息

            if self.data_source:
                font_data_source = ImageFont.truetype(font=fontFile, size=18)
                x_data_source, y_data_source = font_data_source.getsize(self.data_source)
                if uptitle:
                    plt.text(endLon - x_data_source * 1.65 * (endLon - startLon) / (width * 0.85),
                             endLat + (y_data_source + 20) * (endLat - startLat) / (height * 0.85 * rate),
                             self.data_source,
                             fontproperties=font1, fontsize=18)
                else:
                    plt.text(endLon - x_data_source * 1.65 * (endLon - startLon) / (width * 0.85),
                             endLat - (y_data_source + 20) * (endLat - startLat) / (height * 0.85 * rate),
                             self.data_source,
                             fontproperties=font1, fontsize=18)

            if self.note:
                font_note = ImageFont.truetype(font=fontFile, size=18)
                x_note, y_note = font_note.getsize(self.note)
                if uptitle:
                    plt.text(endLon - x_note * 1.6 * (endLon - startLon) / (width * 0.85),
                             endLat + (y_note * 2 + 40) * (endLat - startLat) / (height * 0.85 * rate), self.note,
                             fontproperties=font1, fontsize=18)
                else:
                    plt.text(endLon - x_note * 1.6 * (endLon - startLon) / (width * 0.85),
                             endLat - (y_note * 2 + 40) * (endLat - startLat) / (height * 0.85 * rate), self.note,
                             fontproperties=font1, fontsize=18)

            # 字体
            # font_main = ImageFont.truetype(font=fontFile, size=40)  # 主标题20px
            # font_sub = ImageFont.truetype(font=fontFile, size=30)  # 副标题15px
            # plt.text(116, 44, title, fontsize = 40, fontproperties=font1)

            # 6.保存
            # 是否上传nfsshare
            save_to_nfsshare_switch = look_for_single_global_config("SAVE_TO_NFSSHARE_SWITCH")
            save_to_obs_switch = look_for_single_global_config("SAVE_TO_OBS_SWITCH")

            if int(save_to_nfsshare_switch) or self.request_dict.get("saveToNfsshare"):
                plt.savefig(output_img_path + output_img_name + "." + output_img_type)
                plt.close()
                im = Image.open(output_img_path + output_img_name + '.' + output_img_type, "r")
                # 叠加logo
                if islogo and islogo == "False":
                    pass
                else:
                    ncc_img = Image.open(
                        PathConfig.CPCS_ROOT_PATH + 'com/nriet/algorithm/common/drawComponent/logoFiles/logo.png')
                    x1, y1 = ncc_img.size
                    if logo_size:
                        ncc_img = ncc_img.resize((int(x1 * float(logo_size)),
                                                  int(y1 * float(logo_size))),
                                                 Image.ANTIALIAS)
                    else:
                        ncc_img = ncc_img.resize((int(x1 * ((height * (0.05 + 0.85 * rate) + 150) / width)),
                                                  int(y1 * ((height * (0.05 + 0.85 * rate) + 150) / width))),
                                                 Image.ANTIALIAS)
                    x, y = ncc_img.size
                    p1 = Image.new('RGBA', ncc_img.size, (255, 255, 255))
                    p1.paste(ncc_img, (0, 0, x, y), ncc_img)
                    if "," in areaName:
                        logo_pad, logo_pad_y = get_logo_pad(r)
                    else:
                        if areaConfig.get('logo_pad_y'):
                            logo_pad_y = areaConfig.get('logo_pad_y')
                        else:
                            logo_pad_y = "80"
                        if areaConfig.get('logo_pad'):
                            logo_pad = areaConfig.get('logo_pad')
                        else:
                            logo_pad = "130"
                    if uptitle:
                        im.paste(p1, (int(width * 0.08) + int(logo_pad), int(logo_pad_y)))
                    else:
                        im.paste(p1, (int(width * 0.08) + int(logo_pad), int(height * 0.05) + 30))
                if uptitle:
                    real_pic_size = (0, 0, width, height * (0.1 + 0.85 * rate) + 150)
                else:
                    real_pic_size = (0, 0, width, height * (0.05 + 0.85 * rate) + 150)
                im = im.crop(real_pic_size)
                im.save(output_img_path + output_img_name + '.' + output_img_type)
                im.close()

                if self.request_dict.get("output_img_type_eps"):
                    if int(self.request_dict.get("output_img_type_eps")) == 1:
                        fig = Image.open(output_img_path + output_img_name + '.' + output_img_type)
                        if fig.mode in ('RGBA', 'LA'):
                            fig = fig.convert('RGB')
                        fig.save(output_img_path + output_img_name + '.eps')
                        fig.close()

                stop_time = time.clock()
                cost = stop_time - start_time
                print("         %s cost %s second" % (os.path.basename(__file__), cost))
                # return draw_result

            # # 是否上传至obs
            if int(save_to_obs_switch) or self.request_dict.get("saveToObs"):
                plt.savefig(output_img_path + output_img_name + "." + output_img_type)
                im = Image.open(output_img_path + output_img_name + '.' + output_img_type, "r")
                # 叠加logo
                # 叠加logo
                if islogo and islogo == "False":
                    pass
                else:
                    ncc_img = Image.open(
                        PathConfig.CPCS_ROOT_PATH + 'com/nriet/algorithm/common/drawComponent/logoFiles/logo.png')
                    x1, y1 = ncc_img.size
                    if logo_size:
                        ncc_img = ncc_img.resize((int(x1 * float(logo_size)),
                                                  int(y1 * float(logo_size))),
                                                 Image.ANTIALIAS)
                    else:
                        ncc_img = ncc_img.resize((int(x1 * ((height * (0.05 + 0.85 * rate) + 150) / width)),
                                                  int(y1 * ((height * (0.05 + 0.85 * rate) + 150) / width))),
                                                 Image.ANTIALIAS)
                    x, y = ncc_img.size
                    p1 = Image.new('RGBA', ncc_img.size, (255, 255, 255))
                    p1.paste(ncc_img, (0, 0, x, y), ncc_img)
                    if "," in areaName:
                        logo_pad, logo_pad_y = get_logo_pad(r)
                    else:
                        if areaConfig.get('logo_pad_y'):
                            logo_pad_y = areaConfig.get('logo_pad_y')
                        else:
                            logo_pad_y = "80"
                        if areaConfig.get('logo_pad'):
                            logo_pad = areaConfig.get('logo_pad')
                        else:
                            logo_pad = "130"
                    if uptitle:
                        im.paste(p1, (int(width * 0.08) + int(logo_pad), int(logo_pad_y)))
                    else:
                        im.paste(p1, (int(width * 0.08) + int(logo_pad), int(height * 0.05) + 30))
                if uptitle:
                    real_pic_size = (0, 0, width, height * (0.1 + 0.85 * rate) + 150)
                else:
                    real_pic_size = (0, 0, width, height * (0.05 + 0.85 * rate) + 150)
                im = im.crop(real_pic_size)

                # buf = io.BytesIO()
                # plt.savefig(buf, fmt=output_img_type, dpi=100)
                # buf.seek(0)
                # pil_img = copy.deepcopy(Image.open(buf))
                # buf.close()
                if self.request_dict.get("output_img_type_eps") and int(self.request_dict.get("output_img_type_eps")) == 1:
                    if im.mode in ('RGBA', 'LA'):
                        im = im.convert('RGB')
                    storage_result = ObsUtils().img_save_to_obs(im, output_img_name, "eps")
                else:
                    storage_result = ObsUtils().img_save_to_obs(im, output_img_name, output_img_type)

            # 删除临时文件
            # os.remove(output_img_path + output_img_name + '.' + output_img_type)
            # logging.info("             delete temp file %s" % output_img_path + output_img_name + '.' + output_img_type)

            return draw_result

        except Exception as e:
            traceback.format_exc()
            raise AlgorithmException(response_code=SERVER_HANDLING_ERROR_CODE, response_msg=e.__str__())


def RGB_to_Hex(rgb):
    """
    RGB转换为16进制，自定义cmap需要
    :param rgb: rgb三色，“,”分隔，字符串
    :return: 16进制颜色标识，字符串
    """
    # RGB = rgb.split(',')  # 将RGB格式划分开来
    color = '#'
    for i in rgb:
        num = int(i * 255 + 0.5)
        # 将R、G、B分别转化为16进制拼接转换并大写  hex() 函数用于将10进制整数转换成16进制，以字符串形式表示
        color += str(hex(num))[-2:].replace('x', '0').upper()
    return color


def RGB_to_Hex_str(rgb):
    """
    RGB转换为16进制，自定义cmap需要
    :param rgb: rgb三色，“,”分隔，字符串
    :return: 16进制颜色标识，字符串
    """
    RGB = rgb.split(',')  # 将RGB格式划分开来
    color = '#'
    for i in RGB:
        num = int(int(i) + 0.5)
        # 将R、G、B分别转化为16进制拼接转换并大写  hex() 函数用于将10进制整数转换成16进制，以字符串形式表示
        color += str(hex(num))[-2:].replace('x', '0').upper()
    return color


def getColorLabel(colors, labels):
    '''
    patch颜色与标签
    :param colors: 颜色列表
    :param labels: 标签列表
    :return: patch后的结果
    '''
    patch = []
    for i, color in enumerate(colors):
        tmp_patch = mpatches.Patch(color=color, label=labels[i])
        patch.append(tmp_patch)
    return patch

def add_city_name(m, key, font, fontsize, outerCircleSize, innerCircleSize, vval, x_sub=None, y_sub=None, city=None, point=None):
    '''
    叠加市名和省会名中文标注
    :param m: 地图
    :param outerCircleSize, innerCircleSize: 标注点内外圆大小,
    :param vval：省会名圆圈位置
    :return: None
    '''

    # 读取shp文件信息，如shp_tmp1:m.shi_label_info，shp_tmp2:m.shi_label, shp_tmp3:NAME，参考addName函数
    shp_tmp1 = "m." + key + "_info"
    shp_tmp2 = "m." + key
    # 市名默认黑色，省会名默认红色
    if key == "shi_label":
        shp_tmp3 = "NAME"
    elif key == "province_label":
        shp_tmp3 = "FCNAME"
    for shapedict, state in zip(eval(shp_tmp1), eval(shp_tmp2)):
        short_name = shapedict[shp_tmp3]
        x, y = np.array(state)
        if point:
            # 内部空心圆
            plt.scatter(x, y - float(vval), marker='o', s=int(innerCircleSize), color='None', edgecolor='black')
            # 外部空心圆
            plt.scatter(x, y - float(vval), marker='o', s=int(outerCircleSize), color='None', edgecolors='black')
        # 在上方标注中文
        if city:
            if short_name in city:
                index = city.index(short_name)
                x_pad = x_sub[index]
                y_pad = y_sub[index]
                plt.text(x + float(x_pad), y + float(y_pad), short_name, fontproperties=font, fontsize=fontsize,
                         ha="center")
            else:
                plt.text(x, y, short_name, fontproperties=font, fontsize=fontsize, ha="center")
        else:
            plt.text(x, y, short_name, fontproperties=font, fontsize=fontsize, ha="center", color='black')

def addName(m, font, fontsize, x_sub=None, y_sub=None, city=None, point=None):
    '''
    叠加点位和中文标注
    :param m: 地图
    :return: None
    '''
    for shapedict, state in zip(m.point_info, m.point):
        short_name = shapedict['NAME']
        x, y = np.array(state)
        vval = 0.0
        if point == "True":
            vval = 0.07
            # 内部实心圆
            plt.scatter(x, y, marker='o', s=30, color='black')
            # 外部空心圆
            plt.scatter(x, y, marker='o', s=150, color='None', edgecolors='black')
        # 在上方标注中文
        if city:
            if short_name in city:
                index = city.index(short_name)
                x_pad = x_sub[index]
                y_pad = y_sub[index]
                plt.text(x + float(x_pad), y + float(y_pad), short_name, fontproperties=font, fontsize=fontsize,
                         ha="center")
            else:
                plt.text(x, y + vval, short_name, fontproperties=font, fontsize=fontsize, ha="center")
        else:
            plt.text(x, y + vval, short_name, fontproperties=font, fontsize=fontsize, ha="center")


def add_logos(im, params_dict):
    for logo_name, logo_instance in params_dict.items():
        ncc_img = Image.open(logo_instance['file_path'])
        x, y = ncc_img.size
        p1 = Image.new('RGBA', ncc_img.size, (255, 255, 255))
        p1.paste(ncc_img, (0, 0, x, y), ncc_img)
        im.paste(p1, logo_instance['logo_location'])

def get_regions(data_config, areaName):
    areaArr = areaName.split(",")[1:]
    startLon = 180.0
    endLon = 0.0
    startLat = 70.0
    endLat = 0.0
    for area in areaArr:
        startLon = min(float(data_config.get(area).get('regions').split(",")[0]), startLon)
        endLon = max(float(data_config.get(area).get('regions').split(",")[1]), endLon)
        startLat = min(float(data_config.get(area).get('regions').split(",")[2]), startLat)
        endLat = max(float(data_config.get(area).get('regions').split(",")[3]), endLat)
    regions = ",".join([str(startLon), str(endLon), str(startLat), str(endLat)])
    return regions

def get_params(r):
    if r >= 1.08:
        y1, y2, y3, y4, logo_size = 1.05, 0.925, 1.06, 0.935, 0.8
    elif r >= 1.0:
        y1, y2, y3, y4, logo_size = 1.05, 0.92, 1.06, 0.93, 0.8
    elif r >= 0.92:
        y1, y2, y3, y4, logo_size = 1.05, 0.925, 1.07, 0.94, 0.8
    elif r >= 0.80:
        y1, y2, y3, y4, logo_size = 1.05, 0.925, 1.08, 0.945, 0.8
    elif r >= 0.70:
        y1, y2, y3, y4, logo_size = 1.06, 0.925, 1.10, 0.945, 0.8
    elif r >= 0.57:
        y1, y2, y3, y4, logo_size = 1.07, 0.925, 1.11, 0.945, 0.8
    elif r >= 0.50:
        y1, y2, y3, y4, logo_size = 1.09, 0.925, 1.13, 0.945, 0.7
    elif r >= 0.42:
        y1, y2, y3, y4, logo_size = 1.09, 0.925, 1.15, 0.945, 0.6
    elif r >= 0.38:
        y1, y2, y3, y4, logo_size = 1.11, 0.925, 1.17, 0.945, 0.6
    elif r >= 0.34:
        y1, y2, y3, y4, logo_size = 1.13, 0.925, 1.22, 0.945, 0.6
    elif r >= 0.29:
        y1, y2, y3, y4, logo_size = 1.14, 0.925, 1.24, 0.945, 0.5
    else:
        y1, y2, y3, y4, logo_size = 1.15, 0.925, 1.27, 0.945, 0.5
    return y1, y2, y3, y4, logo_size

def get_logo_pad(r):
    if r >= 1.0:
        logo_pad, logo_pad_y = 40,170
    elif r >= 0.53:
        logo_pad, logo_pad_y = 40,70
    elif r >= 0.50:
        logo_pad, logo_pad_y = 100,70
    else:
        logo_pad, logo_pad_y = 100,100
    return logo_pad, logo_pad_y


# |的处理，对于多个字段分别存在|的情况，采用笛卡尔积的方式分割
def split_params(page_params):
    param_list = []
    param_dict = {}
    result_list = []
    # 将参数中存在|的参数放入param_dict
    for param_key in page_params.keys():
        param_value = page_params[param_key]
        if param_value.__contains__("|"):
            param_dict[param_key] = param_value.split("|")

    # 循环param_dict，将带有|的参数以key:value的形式拼接放入param_list
    for param_dict_key, param_dict_value in param_dict.items():
        pd_list = []
        for pd in param_dict_value:
            pd_list.append(param_dict_key + ":" + pd)
        param_list.append(pd_list)
    dcr_list = []
    # 笛卡尔积
    for item in itertools.product(*param_list):
        dcr_list.append(item)
    for dcr in dcr_list:
        dcr_param = {}
        for d in dcr:
            k, v = d.split(":")
            dcr_param[k] = v
        page_params_copy = copy.deepcopy(page_params)
        page_params_copy.update(dcr_param)
        result_list.append(page_params_copy)

    return result_list


def validation_params(input_data, request_dict):
    draw_result = build_response_dict()
    if not input_data:
        print("request params error,lack of input_data!")  # 此处以后引入日志
        draw_result["response_code"] = "9851"
        draw_result["response_msg"] = " DrawController request params error,lack of 'input_data' !"
        return draw_result
    if not request_dict:
        print("DrawController request params error,lack of 'input_data' !")
        draw_result["response_code"] = "9851"
        draw_result["response_msg"] = "request params error,lack of 'request_dict' !"
        return draw_result

    return draw_result


def draw_shpInfo(areaConfig, shpInfo, m, ax, font, areasNum):
    '''
        绘制地理信息
        :param areaConfig: 配置信息
        :param shpInfo: 需要绘制的地理信息
        :param m: 地图
        :param ax: 画布
        :param font: 字体
        :param areasNum: 需要绘制的区域数,区域数为1,市名、省会名字体大小、圆圈大小和位置按照配置文件绘制,区域数大于1,市名、省会名字体大小、圆圈大小和位置写死
        :return: None
    '''
    shps_set = areaConfig.get('shpInfo')
    for key in shps_set:
        if shpInfo and key in shpInfo:
            tmpshp = shps_set.get(key)
            # shpColor为16进制标识或系统自带颜色
            if key == "water" or key == "lake":
                shpColor = (14.0 / 255, 190.0 / 255, 254.0 / 255)
            else:
                shpColor = tmpshp.get('shpColor')
            result = m.readshapefile(tmpshp.get('shpFile'), key, color=shpColor, linewidth=float(tmpshp.get('shpThick')), default_encoding='gbk')
            if tmpshp.get('shpType'):
                col = result[-1]
                col.set_linestyle(tmpshp.get('shpType'))
            if key == "lake":  # 湖泊填充颜色
                for shp in m.lake:
                    poly = Polygon(shp, facecolor=shpColor)
                    ax.add_patch(poly)
            if key == "shi_label" or key == "province_label":
                city = tmpshp.get('cityName')
                if key == "shi_label":
                    point = False
                elif key == "province_label":
                    point = True
                x_sub = tmpshp.get('x_sub')
                y_sub = tmpshp.get('y_sub')
                # 市名、省会名标签
                if areasNum == 1:
                    fontsize = tmpshp.get('labelSize')
                    outerCircleSize = tmpshp.get('outerCircleSize', 120)
                    innerCircleSize = tmpshp.get('innerCircleSize', 15)
                    vval = tmpshp.get('vval', 0.07)
                else:
                    fontsize = 10
                    outerCircleSize = 60
                    innerCircleSize = 5
                    vval = 0.12
                add_city_name(m, key, font, fontsize, outerCircleSize, innerCircleSize, vval, x_sub, y_sub, city, point)
                # 由于大区、区域市名shp文件未包含省会名，shpInfo仅选择市名时，需补充省会名
                if "shp_area" in tmpshp.get("shpFile") and "province_label" not in shpInfo and "province_label" in shps_set:
                    key = "province_label"
                    tmpshp = shps_set.get(key)
                    shpColor = tmpshp.get('shpColor')
                    result = m.readshapefile(tmpshp.get('shpFile'), key, color=shpColor, linewidth=float(tmpshp.get('shpThick')), default_encoding='gbk')
                    city = tmpshp.get('cityName')
                    point = False
                    x_sub = tmpshp.get('x_sub')
                    y_sub = tmpshp.get('y_sub')
                    add_city_name(m, key, font, fontsize, outerCircleSize, innerCircleSize, vval, x_sub, y_sub, city, point)

if __name__ == '__main__':
    main_start_time = time.clock()
    module = sys.modules[__name__]
    request_dict = None
    serial_no = str(uuid.uuid4())
    page_params = ast.literal_eval(sys.argv[1])
    # page_params = {"areaName":"YN","data_output_types":"png","data_source":"数据：国家站","input_data_name":"云南平均气温距平合成图_04月_2018-2019,2021-2022年_1991-2020_03be93a4-1389-4caf-9bb7-fe9ccab65c73.nc","input_data_path":"/nfsshare/cdbdata/temp_cipas3/","input_data_variables":["data_hcfx","data_hcfx_tjy"],"layers":[{"colors":[[0.02,0.0,0.98],[0.0,0.6,0.99],[0.0,1.0,1.0],[0.76,0.99,1.0],[1.0,1.0,0.51],[1.0,0.71,0.45],[0.98,0.53,0.51],[0.98,0.01,0.0],[0.58,0.09,0.04]],"intervals":[-4.0,-2.0,-1.0,0.0,1.0,2.0,4.0,6.0],"layer_type":"contourMap"},{"layer_type":"polyMarker","marker_type":"+","marker_color":"black"}],"main_title":"云南平均气温距平合成图","note":"气候值：1991-2020年","output_img_max_width":"930","output_img_name":"云南平均气温距平合成图_04月_2018-2019,2021-2022年_1991-2020_03be93a4-1389-4caf-9bb7-fe9ccab65c73","output_img_path":"/nfsshare/cdbdata/temp_cipas3/","output_img_type":"png","saveToObs":"1","shpInfo":["liuyu_boundary","fenqu_boundary","province_boundary","water","lake"],"sub_titles":["04月  2018-2019,2021-2022年"],"unit":"单位：℃"}
    # page_params = {"areaName":"HLJ","data_output_types":"png","data_source":"数据：国家站","input_data_name":"黑龙江降水距平百分率分布图_10月_2022年_1991-2020_fadf3b49-68ff-4bae-81f1-c29f4d1c5771.nc","input_data_path":"/nfsshare/cdbdata/temp_cipas3/","input_data_variables":["data_hcfx"],"layers":[{"colors":[[1.0,0.0,0.01],[1.0,0.39,0.39],[0.99,0.58,0.38],[1.0,1.0,0.58],[0.78,1.0,0.78],[0.19,0.79,0.19],[0.0,0.99,1.0],[0.0,0.59,1.0],[0.0,0.0,0.99]],"intervals":[-80.0,-50.0,-20.0,0.0,20.0,50.0,100.0,200.0],"layer_type":"contourMap"}],"main_title":"黑龙江降水距平百分率分布图","note":"气候值：1991-2020年","output_img_max_width":"930","output_img_name":"黑龙江降水距平百分率分布图_10月_2022年_1991-2020_fadf3b49-68ff-4bae-81f1-c29f4d1c5771","output_img_path":"/nfsshare/cdbdata/temp_cipas3/","output_img_type":"png","saveToObs":"1","sub_titles":["10月  2022年"],"unit":"单位：％"}
    # page_params = {"output_img_type_eps":"1","areaName":"NORTHAREA","data_output_types":"png","data_source":"数据：国家站","input_data_name":"北方地区初霜冻日期监测距平(1991-2020)CSOD_2022年08月01日_11月08日.nc","input_data_path":"/nfsshare/cdbdata/temp/","input_data_variables":["csd","csd_zd"],"layers":[{"colors":[[0.07,0.19,0.55],[0.08,0.38,0.83],[0.2,0.49,0.88],[0.35,0.66,0.96],[0.56,0.83,0.98],[0.9,1.0,1.0],[1.0,1.0,0.75],[0.9,0.86,0.2],[1.0,0.84,0.43],[1.0,0.71,0.2],[0.94,0.51,0.16],[0.93,0.32,0.38],[0.98,0.24,0.24],[0.94,0.0,0.51],[0.62,0.06,0.12],[0.8,0.07,0.15]],"intervals":[-35,-30,-25,-20,-15,-10,-5,0,5,10,15,20,25,30,35],"isNaN":"True","layer_type":"contourMap"},{"layer_type":"polyMarker"}],"main_title":"北方地区初霜冻日期监测距平","note":"气候值：1991-2020年","output_img_max_width":"930","output_img_name":"北方地区初霜冻日期监测距平(1991-2020)CSOD_2022年08月01日_11月08日22222","output_img_path":"/nfsshare/cdbdata/temp/","output_img_type":"png","saveToObs":"1","sub_titles":["2022年08月01日-2022年11月08日2222"],"unit":"单位：天"}
    # page_params = {"areaName":"NORTHAREA","data_output_types":"png","data_source":"数据：国家站","input_data_name":"北方地区初霜冻日期监测距平(1991-2020)CSOD_2022年08月01日_11月08日_dt.nc","input_data_path":"/nfsshare/cdbdata/temp/","input_data_variables":["csd_zd"],"layers":[{"colors":[[0.07,0.19,0.55],[0.08,0.38,0.83],[0.2,0.49,0.88],[0.35,0.66,0.96],[0.56,0.83,0.98],[0.9,1.0,1.0],[1.0,1.0,0.75],[0.9,0.86,0.2],[1.0,0.84,0.43],[1.0,0.71,0.2],[0.94,0.51,0.16],[0.93,0.32,0.38],[0.98,0.24,0.24],[0.94,0.0,0.51],[0.62,0.06,0.12],[0.8,0.07,0.15]],"intervals":[-35,-30,-25,-20,-15,-10,-5,0,5,10,15,20,25,30,35],"isNaN":"True","layer_type":"polyMarker"}],"main_title":"北方地区初霜冻日期监测距平","note":"气候值：1991-2020年","output_img_max_width":"930","output_img_name":"北方地区初霜冻日期监测距平(1991-2020)CSOD_2022年08月01日_11月08日","output_img_path":"/nfsshare/cdbdata/temp/","output_img_type":"png","saveToObs":"1","sub_titles":["2022年08月01日-2022年11月08日"],"unit":"单位：天"}
    # page_params = {"areaName":"NORTHAREA","data_output_types":"png","data_source":"数据：国家站","input_data_name":"北方地区初霜冻日期监测距平(1991-2020)CSOD_2022年08月01日_11月08日.nc","input_data_path":"/nfsshare/cdbdata/temp/","input_data_variables":["csd_zd"],"layers":[{"colors":[[0.07,0.19,0.55],[0.08,0.38,0.83],[0.2,0.49,0.88],[0.35,0.66,0.96],[0.56,0.83,0.98],[0.9,1.0,1.0],[1.0,1.0,0.75],[0.9,0.86,0.2],[1.0,0.84,0.43],[1.0,0.71,0.2],[0.94,0.51,0.16],[0.93,0.32,0.38],[0.98,0.24,0.24],[0.94,0.0,0.51],[0.62,0.06,0.12],[0.8,0.07,0.15]],"intervals":[-35,-30,-25,-20,-15,-10,-5,0,5,10,15,20,25,30,35],"isNaN":"True","layer_type":"polyMarker"}],"main_title":"北方地区初霜冻日期监测距平","note":"气候值：1991-2020年","output_img_max_width":"930","output_img_name":"北方地区初霜冻日期监测距平(1991-2020)CSOD_2022年08月01日_11月08日","output_img_path":"/nfsshare/cdbdata/temp/","output_img_type":"png","saveToObs":"1","sub_titles":["2022年08月01日-2022年11月08日xx"],"unit":"单位：天"}
    # page_params = {"areaName":"NORTHAREA","data_output_types":"png","data_source":"数据：国家站","input_data_name":"北方地区初霜冻日期监测距平(1991-2020)CSOD_2022年08月01日_11月08日.nc","input_data_path":"/nfsshare/cdbdata/temp/","input_data_variables":["csd","csd_zd"],"layers":[{"colors":[[0.07,0.19,0.55],[0.08,0.38,0.83],[0.2,0.49,0.88],[0.35,0.66,0.96],[0.56,0.83,0.98],[0.9,1.0,1.0],[1.0,1.0,0.75],[0.9,0.86,0.2],[1.0,0.84,0.43],[1.0,0.71,0.2],[0.94,0.51,0.16],[0.93,0.32,0.38],[0.98,0.24,0.24],[0.94,0.0,0.51],[0.62,0.06,0.12],[0.8,0.07,0.15]],"intervals":[-35,-30,-25,-20,-15,-10,-5,0,5,10,15,20,25,30,35],"isNaN":"True","layer_type":"contourMap"},{"colors":[[0.07,0.19,0.55],[0.08,0.38,0.83],[0.2,0.49,0.88],[0.35,0.66,0.96],[0.56,0.83,0.98],[0.9,1.0,1.0],[1.0,1.0,0.75],[0.9,0.86,0.2],[1.0,0.84,0.43],[1.0,0.71,0.2],[0.94,0.51,0.16],[0.93,0.32,0.38],[0.98,0.24,0.24],[0.94,0.0,0.51],[0.62,0.06,0.12],[0.8,0.07,0.15]],"intervals":[-35,-30,-25,-20,-15,-10,-5,0,5,10,15,20,25,30,35],"layer_type":"polyMarker"}],"main_title":"北方地区初霜冻日期监测距平","note":"气候值：1991-2020年","output_img_max_width":"930","output_img_name":"北方地区初霜冻日期监测距平(1991-2020)CSOD_2022年08月01日_11月08日","output_img_path":"/nfsshare/cdbdata/temp/","output_img_type":"png","saveToObs":"1","sub_titles":["2022年08月01日-2022年11月08日"],"unit":"单位：天"}
    # page_params = {"areaName":"NORTHAREA","data_output_types":"png","data_source":"数据：国家站","input_data_name":"北方地区初霜冻日期监测距平(1991-2020)CSOD_2022年08月01日_11月10日.nc","input_data_path":"/nfsshare/cdbdata/temp/","input_data_variables":["csd","csd_zd"],"layers":[{"colors":[[0.07,0.19,0.55],[0.08,0.38,0.83],[0.2,0.49,0.88],[0.35,0.66,0.96],[0.56,0.83,0.98],[0.9,1.0,1.0],[1.0,1.0,0.75],[0.9,0.86,0.2],[1.0,0.84,0.43],[1.0,0.71,0.2],[0.94,0.51,0.16],[0.93,0.32,0.38],[0.98,0.24,0.24],[0.94,0.0,0.51],[0.62,0.06,0.12],[0.8,0.07,0.15]],"intervals":[-35,-30,-25,-20,-15,-10,-5,0,5,10,15,20,25,30,35],"layer_type":"contourMap"},{"colors":[[0.07,0.19,0.55],[0.08,0.38,0.83],[0.2,0.49,0.88],[0.35,0.66,0.96],[0.56,0.83,0.98],[0.9,1.0,1.0],[1.0,1.0,0.75],[0.9,0.86,0.2],[1.0,0.84,0.43],[1.0,0.71,0.2],[0.94,0.51,0.16],[0.93,0.32,0.38],[0.98,0.24,0.24],[0.94,0.0,0.51],[0.62,0.06,0.12],[0.8,0.07,0.15]],"intervals":[-35,-30,-25,-20,-15,-10,-5,0,5,10,15,20,25,30,35],"layer_type":"polyMarker"}],"main_title":"北方地区初霜冻日期监测距平","note":"气候值：1991-2020年","output_img_max_width":"930","output_img_name":"北方地区初霜冻日期监测距平(1991-2020)CSOD_2022年08月01日_11月10日xx","output_img_path":"/nfsshare/cdbdata/temp/","output_img_type":"png","saveToObs":"1","sub_titles":["2022年08月01日-2022年11月10日"],"unit":""}
    # page_params = {"areaName":"NORTHAREA","data_output_types":"png","data_source":"数据：国家站","input_data_name":"北方地区初霜冻日期监测距平(1991-2020)CSOD_2022年08月01日_11月09日.nc","input_data_path":"/nfsshare/cdbdata/temp/","input_data_variables":["csd_zd"],"layers":[{"colors":[[0.07,0.19,0.55],[0.08,0.38,0.83],[0.2,0.49,0.88],[0.35,0.66,0.96],[0.56,0.83,0.98],[0.9,1.0,1.0],[1.0,1.0,0.75],[0.9,0.86,0.2],[1.0,0.84,0.43],[1.0,0.71,0.2],[0.94,0.51,0.16],[0.93,0.32,0.38],[0.98,0.24,0.24],[0.94,0.0,0.51],[0.62,0.06,0.12],[0.8,0.07,0.15]],"intervals":[-35,-30,-25,-20,-15,-10,-5,0,5,10,15,20,25,30,35],"layer_type":"polyMarker"}],"main_title":"北方地区初霜冻日期监测距平","note":"气候值：1991-2020年","output_img_max_width":"930","output_img_name":"北方地区初霜冻日期监测距平(1991-2020)CSOD_2022年08月01日_11月09日","output_img_path":"/nfsshare/cdbdata/temp/","output_img_type":"png","saveToObs":"1","sub_titles":["2022年08月01日-2022年11月09日"],"unit":"单位："}
    # page_params = {"areaName":"NORTHAREA","data_output_types":"png","data_source":"数据：国家站","input_data_name":"北方地区初霜冻日期监测距平(1991-2020)CSOD_2022年08月01日_11月10日.nc","input_data_path":"/nfsshare/cdbdata/temp/","input_data_variables":["csd","csd_zd"],"layers":[{"colors":[[0.07,0.19,0.55],[0.08,0.38,0.83],[0.2,0.49,0.88],[0.35,0.66,0.96],[0.56,0.83,0.98],[0.9,1.0,1.0],[1.0,1.0,0.75],[0.9,0.86,0.2],[1.0,0.84,0.43],[1.0,0.71,0.2],[0.94,0.51,0.16],[0.93,0.32,0.38],[0.98,0.24,0.24],[0.94,0.0,0.51],[0.62,0.06,0.12],[0.8,0.07,0.15]],"intervals":[-35,-30,-25,-20,-15,-10,-5,0,5,10,15,20,25,30,35],"layer_type":"contourMap"},{"layer_type":"polyMarker"}],"main_title":"北方地区初霜冻日期监测距平","note":"气候值：1991-2020年","output_img_max_width":"930","output_img_name":"北方地区初霜冻日期监测距平(1991-2020)CSOD_2022年08月01日_11月10日","output_img_path":"/nfsshare/cdbdata/temp/","output_img_type":"png","saveToObs":"1","sub_titles":["2022年08月01日-2022年11月10日"],"unit":"单位："}
    # page_params = {"areaName":"B_CHANGJIANG","data_output_types":"png","data_source":"数据：CFSV2_CSOD","input_data_name":"f7e4af82-f74a-4eab-9c99-f4630b0da727.nc","input_data_path":"/nfsshare/cdbdata/temp/","input_data_variables":["PPS"],"layers":[{"colors":[[0.2,0.0,1.0],[0.2,0.4,1.0],[0.2,0.6,1.0],[0.71,0.98,0.67],[0.47,0.96,0.45],[0.22,0.82,0.24],[1.0,0.8,0.0],[1.0,0.6,0.0],[1.0,0.4,0.0],[1.0,0.0,0.0]],"intervals":[10.0,20.0,30.0,40.0,50.0,60.0,70.0,80.0,90.0],"isNaN":"True","layer_type":"polyMarker"}],"main_title":"长江流域强降水过程（10mm）预测检验（PPS）","output_img_max_width":"930","output_img_name":"f7e4af82-f74a-4eab-9c99-f4630b0da727","output_img_path":"/nfsshare/cdbdata/temp/","output_img_type":"png","saveToObs":"1","sub_titles":["起报:2022年09月19日 预报: 未来11-30天"],"unit":"单位：%"}
    # page_params = {"areaName":"NORTHAREA","data_output_types":"png","data_source":"数据：国家站","input_data_name":"北方地区轻霜冻日等级CSOD_2021年.nc","input_data_path":"/nfsshare/cdbdata/temp/","input_data_variables":["csd_level"],"layers":[{"colors":[[0.0,0.07,0.99],[0.36,0.65,0.95],[0.99,1.0,0.75],[0.99,0.8,0.36],[0.93,0.51,0.16]],"intervals":[1,2,3,4],"ch_legend_labels":["异常偏早","偏早","正常","偏晚","异常偏晚"],"layer_type":"contourMap"}],"main_title":"北方地区轻霜冻日等级","output_img_max_width":"930","output_img_name":"北方地区轻霜冻日等级CSOD_2021年CH","output_img_path":"/nfsshare/cdbdata/tempch/","output_img_type":"png","saveToNfsshare":"1","sub_titles":["2021年"],"unit":"单位："}
    # page_params = {"areaName":"NORTHAREA","data_output_types":"png","data_source":"数据：国家站","input_data_name":"北方地区轻霜冻日等级CSOD_2021年.nc","input_data_path":"/nfsshare/cdbdata/temp/","input_data_variables":["csd_level"],"layers":[{"colors":[[0.0,0.07,0.99],[0.36,0.65,0.95],[0.99,1.0,0.75],[0.99,0.8,0.36],[0.93,0.51,0.16]],"intervals":[1,2,3,4],"legend_labels":["异常偏早","偏早","正常","偏晚","异常偏晚"],"layer_type":"contourMap"}],"main_title":"北方地区轻霜冻日等级","output_img_max_width":"930","output_img_name":"北方地区轻霜冻日等级CSOD_2021年CH","output_img_path":"/nfsshare/cdbdata/tempch/","output_img_type":"png","saveToNfsshare":"1","sub_titles":["2021年"],"unit":"单位："}
    # page_params = {"areaName":"NORTHAREA","data_output_types":"png","data_source":"数据：国家站","input_data_name":"北方地区轻霜冻日等级CSOD_2021年.nc","input_data_path":"/nfsshare/cdbdata/temp/","input_data_variables":["csd_level"],"layers":[{"colors":[[0.0,0.07,0.99],[0.36,0.65,0.95],[0.99,1.0,0.75],[0.99,0.8,0.36],[0.93,0.51,0.16]],"intervals":[1,2,3,4],"labels":["Extra Early","Early","Normal","Late"],"layer_type":"contourMap"}],"main_title":"北方地区轻霜冻日等级","output_img_max_width":"930","output_img_name":"北方地区轻霜冻日等级CSOD_2021年xx","output_img_path":"/nfsshare/cdbdata/tempch/","output_img_type":"png","saveToNfsshare":"1","sub_titles":["2021年"],"unit":"单位："}
    # page_params = {"areaName":"AREA,B_CHANGJIANG,B_ZHUJIANG","data_output_types":"png","data_source":"数据：国家站","input_data_name":"黑龙江省平均气温距平空间分布(1991-2020)CSOD_2022年10月05日_11月03日.nc","input_data_path":"/nfsshare/cdbdata/temp/","input_data_variables":["temp_sb","temp_sb"],"layers":[{"colors":[[0.02,0.0,0.98],[0.0,0.6,0.99],[0.0,1.0,1.0],[0.76,0.99,1.0],[1.0,1.0,0.51],[1.0,0.71,0.45],[0.98,0.53,0.51],[0.98,0.01,0.0],[0.58,0.09,0.04]],"intervals":[-4,-2,-1,0,1,2,4,6],"layer_type":"contourMap"}],"main_title":"黑龙江省平均气温距平空间分布","note":"气候值：1991-2020年","output_img_max_width":"930","output_img_name":"黑龙江省平均气温距平空间分布(1991-2020)CSOD_2022年10月05日_11月03日","output_img_path":"/nfsshare/cdbdata/temp/","output_img_type":"png","saveToObs":"1","sub_titles":["2022年10月05日-2022年11月03日"],"unit":"单位：°C"}
    # page_params = {"areaName":"PROV,HLJ,JL,LN","data_output_types":"png","data_source":"数据：国家站","input_data_name":"黑龙江省平均气温距平空间分布(1991-2020)CSOD_2022年10月05日_11月03日.nc","input_data_path":"/nfsshare/cdbdata/temp/","input_data_variables":["temp_sb","temp_sb"],"layers":[{"colors":[[0.02,0.0,0.98],[0.0,0.6,0.99],[0.0,1.0,1.0],[0.76,0.99,1.0],[1.0,1.0,0.51],[1.0,0.71,0.45],[0.98,0.53,0.51],[0.98,0.01,0.0],[0.58,0.09,0.04]],"intervals":[-4,-2,-1,0,1,2,4,6],"layer_type":"contourMap"}],"main_title":"黑龙江省平均气温距平空间分布","note":"气候值：1991-2020年","output_img_max_width":"930","output_img_name":"黑龙江省平均气温距平空间分布(1991-2020)CSOD_2022年10月05日_11月03日","output_img_path":"/nfsshare/cdbdata/temp/","output_img_type":"png","saveToObs":"1","sub_titles":["2022年10月05日-2022年11月03日"],"unit":"单位：°C"}
    # page_params = {"areaName":"ASIA","data_output_types":"png","data_source":"数据：GSOD","input_data_name":"巴基斯坦平均气温距平空间分布(1991-2020)GSOD_2022年09月20日_10月19日.nc","input_data_path":"/nfsshare/cdbdata/temp/","input_data_variables":["temp_sb","temp_sb"],"layers":[{"colors":[[0.02,0.0,0.98],[0.0,0.6,0.99],[0.0,1.0,1.0],[0.76,0.99,1.0],[1.0,1.0,0.51],[1.0,0.71,0.45],[0.98,0.53,0.51],[0.98,0.01,0.0],[0.58,0.09,0.04]],"intervals":[-4,-2,-1,0,1,2,4,6],"layer_type":"contourMap"}],"main_title":"巴基斯坦平均气温距平空间分布","note":"气候值：1991-2020年","output_img_max_width":"930","output_img_name":"巴基斯坦平均气温距平空间分布(1991-2020)GSOD_2022年09月20日_10月19日","output_img_path":"/nfsshare/cdbdata/temp/","output_img_type":"png","saveToObs":"1","sub_titles":["2022年09月20日-2022年10月19日"],"unit":"单位：°C"}
    # page_params = {"areaName":"PAK","data_output_types":"png","data_source":"数据：CRA40","input_data_name":"巴基斯坦降水量空间分布CRA40_2022年09月20日_10月19日.nc","input_data_path":"/nfsshare/cdbdata/temp/","input_data_variables":["precip","precip"],"layers":[{"colors":[[1.0,1.0,1.0],[0.55,0.78,0.55],[0.19,1.0,0.2],[0.0,1.0,1.0],[0.0,0.58,1.0],[0.0,0.0,1.0],[1.0,0.0,1.0],[0.49,0.0,0.25]],"intervals":[1,10,50,100,200,300,500],"layer_type":"contourMap"}],"main_title":"巴基斯坦降水量空间分布","output_img_max_width":"930","output_img_name":"巴基斯坦降水量空间分布CRA40_2022年09月20日_10月19日","output_img_path":"/nfsshare/cdbdata/temp/","output_img_type":"png","saveToObs":"1","sub_titles":["2022年09月20日-2022年10月19日"],"unit":"单位：mm"}
    # page_params = {"areaName": "NX",
    #                "intervals": [-32, -28, -24, -20, -16, -12, -8, -4, 0, 4, 8, 12, 16, 20, 24, 28, 32],
    #                # "intervals": [20,22,24,26,28,30,32,34,36,38,40],
    #                "colors": [[0.0, 0.0, 0.2], [0.0, 0.0, 0.59], [0.0, 0.0, 1.0], [0.0, 0.29, 1.0], [0.0, 0.59, 1.0],
    #                           [0.0, 0.78, 1.0], [0.2, 1.0, 1.0], [0.61, 1.0, 1.0], [0.78, 1.0, 1.0], [1.0, 1.0, 0.59],
    #                           [1.0, 1.0, 0.2], [1.0, 0.78, 0.0], [1.0, 0.59, 0.39], [1.0, 0.59, 0.2], [1.0, 0.39, 0.0],
    #                           [0.9, 0.0, 0.0], [0.59, 0.0, 0.0], [0.39, 0.0, 0.0]],
    #                # "colors":[[0.933333333,0.4,0.094117647],[0.933333333,0.345098039,0.121568627],[0.905882353,0.294117647,0.101960784],[0.878431373,0.247058824,0.08627451],[0.850980392,0.2,0.070588235],[0.815686275,0.141176471,0.054901961],[0.760784314,0,0.011764706],[0.709803922,0.003921569,0.035294118],[0.662745098,0.007843137,0.062745098],[0.541176471,0.019607843,0.098039216],[0.435294118,0,0.082352941],[0.31372549,0,0.058823529]],
    #                "mainTitle": "宁夏省平均气温分布", "subTitles": ["2020年03月10日-2020年04月08日"],
    #                "output_img_path": "/usr/local/src/hyh/",
    #                "output_img_name": "NX", "output_img_type": "png", "unit": "单位：℃",
    #                "input_data_path": "/nfsshare/cdbdata/temp/localSwap/tomcat/webapps/cipas/",
    #                "input_data_variables": ["temp_sb"],"data_source": "数据：CSOD","note": "气候值：1981-2010年",
    #                "input_data_name": "CSOD_20211010-20211108.nc"}

    if len(sys.argv) > 1:
        try:
            # 1. 获取页面传参
            print("DrawRegionsController serial_no is : %s ,input_params is : %s" % (serial_no, sys.argv[1]))
            # 2. 页面参数包含|的处理
            print("DrawRegionsController processing split-params method")
            param_list = split_params(page_params)
            sub_local_params = build_response_dict(from_tianqin=page_params.get('from_tianqin', 0))

            print("DrawRegionsController processing execute method")
            if param_list:
                for pl in param_list:
                    me = DrawRegionsController(sub_local_params=pl)
                    result_dict = me.execute()
                    del me
                    if not judge_response_result(result_dict):
                        break
                    else:  # 成功时带回图片名称
                        result_dict['output_img_name'] = '.'.join(
                            [pl.get("output_img_name"), pl.get("output_img_type")])
                result_dict = response_result_convert(result_dict)
            main_stop_time = time.clock()
            cost = main_stop_time - main_start_time
            print("             %s cost %s second" % (os.path.basename(__file__), cost))
            print(json.dumps(result_dict, ensure_ascii=False))
        except AlgorithmException as ae:
            traceback.format_exc()
            print(json.dumps(
                build_response_dict(response_code=ae.response_code, response_msg=ae.response_msg, serial_no=serial_no,
                                    from_tianqin=page_params.get('from_tianqin', 1)), ensure_ascii=False))

        except ValueError:
            traceback.format_exc()
            print(
                json.dumps(build_response_dict(response_code=ResponseCodeAndMsgEum.INPUT_PAGE_PARAM_FORMAT_ERROR_CODE,
                                               response_msg=ResponseCodeAndMsgEum.INPUT_PAGE_PARAM_FORMAT_ERROR_MSG,
                                               serial_no=serial_no, from_tianqin=page_params.get('from_tianqin', 1)),
                           ensure_ascii=False))
        except Exception:
            traceback.format_exc()
            print(json.dumps(
                build_response_dict(response_code=ResponseCodeAndMsgEum.SERVER_HANDLING_ERROR_CODE,
                                    response_msg=ResponseCodeAndMsgEum.SERVER_HANDLING_ERROR_MSG, serial_no=serial_no,
                                    from_tianqin=page_params.get('from_tianqin', 1)), ensure_ascii=False))
    else:
        print(
            json.dumps(build_response_dict(response_code=ResponseCodeAndMsgEum.INPUT_PAGE_PARAM_FORMAT_ERROR_CODE,
                                           response_msg=ResponseCodeAndMsgEum.INPUT_PAGE_PARAM_FORMAT_ERROR_MSG,
                                           serial_no=serial_no, from_tianqin=page_params.get('from_tianqin', 1)),
                       ensure_ascii=False))
