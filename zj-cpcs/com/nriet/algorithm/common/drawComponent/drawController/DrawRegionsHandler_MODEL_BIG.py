# -*- coding:utf-8 -*-
import importlib, sys
import logging
importlib.reload(sys)
from mpl_toolkits.basemap import Basemap
# matplotlib升级为3.3.4
# 因为函数名变更，需要修改basemap下__init__.py文件和proj.py文件的import部分
import shapefile
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from shapely.geometry import Point as ShapelyPoint
import matplotlib.patches as mpatches
from shapely.geometry import Polygon as ShapelyPolygon
from collections import Iterable
import os, ast
import pandas as pd
import traceback
from PIL import ImageFont
import time
import matplotlib
import PIL.Image as Image
from scipy.ndimage import gaussian_filter

matplotlib.use('Agg')
import matplotlib.ticker as ticker
from matplotlib.patches import Polygon
from matplotlib import font_manager
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import AutoMinorLocator, MultipleLocator
import numpy as np
import json
import matplotlib.colors as mcolors
import xarray as xr
from intervals import IntInterval, FloatInterval
from com.nriet.config import PathConfig
from com.nriet.config import DataSourceConfig
from com.nriet.config import TitleConfig

class DrawRegionsHandler_MODEL_BIG():
    def __init__(self, params: dict, algorithm_input_data):
        # dataSourceConfigPath = PathConfig.CPCS_ROOT_PATH + 'com/nriet/config/dataSourceNoteConfig.json'
        # with open(dataSourceConfigPath, "r", encoding='UTF-8') as f:
        #     datasourcestr = f.read()
        # self.datasource_config = json.loads(datasourcestr)
        self.iniPath = params.get("iniPath")
        self.datasource_config = DataSourceConfig.data_source_dict
        self.title_config = TitleConfig.title_dict
        self.request_dict = params["data_output_params"][0]
        params = params["data_output_params"][0]
        # 区域Code
        self.areaCode = str(params.get("areaCode"))
        # 主标题
        self.mainTitle = params.get("main_title")
        # 副标题，字符串列表（最多两行）
        self.subTitles = params.get("sub_titles")
        # 输出图片路径
        self.output_img_path = params.get("output_img_path")
        # 输出图片名称（默认png）
        self.output_img_name = params.get("output_img_name")
        # 输出图片类型
        self.output_img_type = params.get("output_img_type")
        # 单位标注
        self.unit = params.get("unit")
        # 数据源标注
        self.data_source = params.get("data_source")
        # 其他信息标注
        self.note = params.get("note")
        # 图层，字典列表
        self.layers = params.get("layers")
        # logo标注
        self.logo = params.get("logo")
        # 数据源源
        self.dataSource = params.get("dataSource")
        # 起报时间尺度
        self.reportTimeType = params.get("reportTimeType")
        # 时间尺度
        self.timeType = params.get("timeType")
        # 起报时间
        self.forecastTime = params.get("forecastTime")
        # 预报开始时间
        self.startTime = params.get("startTime")
        # 预报结束时间
        self.endTime = params.get("endTime")
        # 统计方式
        self.eleType = params.get("eleType")
        # 变量
        self.element = params.get("element")
        # 地理信息
        self.shpInfo = params.get("shpInfo")
        # 输入数据的变量名，字符串列表
        input_data_variable = params.get("element")
        # 色例是否显示>和<部分
        self.extendColor = params.get("extendColor", "True")
        # 色例是否显示
        self.barShow = params.get("barShow", "True")

        # input_data_variables = []
        # input_data_variables.append(input_data_variable)
        # algorithm_input_data = []
        # # 数据解析
        # for var_index, var in enumerate(input_data_variables):
        #     if isinstance(var, list):
        #         tmp_dict_list = []
        #         for individual_var in var:
        #             tmp_dict = {}
        #             tmp_dict['outputData'] = input_data_set[individual_var]
        #             tmp_dict_list.append(tmp_dict)
        #         algorithm_input_data.append(tmp_dict_list)
        #     else:
        #         tmp_dict = {}
        #         tmp_dict['outputData'] = input_data_set
        #         algorithm_input_data.append(tmp_dict)
        # # 绘图数据确定
        # self.input_data = []
        # for index, input_data in enumerate(algorithm_input_data):
        #     if isinstance(input_data, list):
        #         self.input_data.append([])
        #         for ind, data in enumerate(input_data):
        #             self.input_data[index].append(data["outputData"])
        #     else:
        #         self.input_data.append((input_data["outputData"]))
        algorithm_input_data = algorithm_input_data
        self.input_data = []
        for index, input_data in enumerate(algorithm_input_data):
            if isinstance(input_data, list):
                self.input_data.append([])
                for ind, data in enumerate(input_data):
                    self.input_data[index].append(data["outputData"])
            else:
                self.input_data.append((input_data["outputData"]))

    def execute(self):
        # 进入默认路径
        areaCode = self.areaCode
        mainTitle = self.mainTitle
        subTitles = self.subTitles
        output_img_path = self.output_img_path
        output_img_name = self.output_img_name
        output_img_type = self.output_img_type
        data = self.input_data
        layers = self.layers

        try:
            # 设置中文字体
            fontFile = PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/simhei.ttf"
            font1 = FontProperties(fname=fontFile)
            # 区域基本信息配置文件
            configPath = PathConfig.CPCS_ROOT_PATH + "com/regionConfig_ZJ.json"
            # 读取配置文件
            with open(configPath, "r", encoding='UTF-8') as f:
                datastr = f.read()
            data_config = json.loads(datastr)
            # 获取传参区域的参数
            areaConfig = data_config.get(areaCode)
            # 区域类型
            regionType = areaConfig.get('regionType')
            # 获取传参区域的shp标识
            label = areaConfig.get('label')
            # 获取传参区域的中文名称
            chineseName = areaConfig.get('name')
            # 获取图例位置
            barloc = areaConfig.get('barloc')
            # 获取传参区域的绘图区域范围
            areaRegions = areaConfig.get('regions')
            startLon, endLon, startLat, endLat = [float(i) for i in areaRegions.split(',')]
            # logo位置
            # logo_x = float(areaConfig.get('logo_x'))
            # logo_y = float(areaConfig.get('logo_y'))
            # 设置colorbar位置，left,bottom,width,height,数值为figure的百分比
            barLeft, barBottom, barWidth, barHeight = [float(i) for i in barloc.split(',')]
            barlabel = areaConfig.get("barlabel")
            bar_x, bar_y = [float(i) for i in barlabel.split(',')]
            datasource_loc = areaConfig.get("datasource")
            datasource_x, datasource_y = [float(i) for i in datasource_loc.split(',')]
            note_loc = areaConfig.get("note")
            note_x, note_y = [float(i) for i in note_loc.split(',')]

            # 获取传参区域掩膜shp文件的位置
            shpFile = areaConfig.get('shpFile')
            # 主副标题偏移量
            y1 = areaConfig.get('y1')
            y2 = areaConfig.get('y2')
            y3 = areaConfig.get('y3')
            y4 = areaConfig.get('y4')
            # 设置fig像素（支持常规的绘图范围，太过狭长的绘图范围需要自行调整）
            width = 2000
            if (endLon - startLon) > (endLat - startLat):
                height = 2000
            else:
                height = 3000
            fig = plt.figure(figsize=(width / 100, height / 100))
            # 设置图片位置（仅支持单张图形绘制）
            ax = fig.add_subplot(111)
            rate = (endLat - startLat) / (endLon - startLon) * width / height
            ax.set_position([0.08, 1 - (0.85 * rate + 0.1), 0.85, 0.85 * rate])

            # 创建地图，标识为m。仅支持等经纬绘图。
            m = Basemap(llcrnrlon=startLon, urcrnrlon=endLon, llcrnrlat=startLat, urcrnrlat=endLat, projection='cyl')

            # 根据layer图层匹配数据并叠加图层
            c_bar = ""
            for i, layer in enumerate(layers):
                layer_type = layer['layer_type']  # 当前图层的类型
                # 当前图层的绘图数据
                layer_data = data[i]

                if layer_type == "contourMap":  # 色斑图层
                    # 获取值色对
                    sublevs = layer.get('intervals')
                    colors = layer.get('colors')

                    labels = layer.get('labels')

                    legend_labels = [str(int(i)) if i % 1 == 0 else str(i) for i in sublevs]
                    labels = ['＜' + legend_labels[0]]
                    for i in range(1, len(legend_labels)):
                        labels.extend([legend_labels[i - 1] + '～' + legend_labels[i]])
                    labels.extend(['＞' + legend_labels[-1]])

                    # 设置levs
                    if self.eleType == "TCC" or self.extendColor == False:
                        levs_map = []
                        levs_map.extend(sublevs)
                    else:
                        levs_map = [-9999.0]
                        levs_map.extend(sublevs)
                        endlevs = [9999.0]
                        levs_map.extend(endlevs)
                    # 标准化颜色，页面直接传rgb，iniPath传浮点数
                    if self.iniPath:
                        ccolors = [Float_to_Hex(i) for i in colors]
                    else:
                        ccolors = [RGB_to_Hex(i) for i in colors]
                    my_cmap = mcolors.ListedColormap(ccolors)
                    norm = mcolors.BoundaryNorm(levs_map, my_cmap.N)
                    # 根据绘图经纬度截取数据
                    lon = layer_data["lon"]
                    lat = layer_data["lat"]
                    # 适当扩大绘图数据的范围
                    lon = lon[(lon >= startLon - 2.5) & (lon <= endLon + 2.5)]
                    lat = lat[(lat >= startLat - 2.5) & (lat <= endLat + 2.5)]
                    # 数据插值
                    # glon = np.linspace(lon[0], lon[-1], len(lon) * 20)
                    # glat = np.linspace(lat[0], lat[-1], len(lat) * 20)
                    # layer_data = layer_data.interp(lat=glat, lon=glon)
                    # 剪裁数据
                    layer_data = layer_data.sel(lon=lon, lat=lat)
                    # 创建地图网格
                    xx, yy = np.meshgrid(layer_data['lon'], layer_data['lat'])
                    # 绘图数据平滑，不改变数据形状
                    layer_data_smooth = gaussian_filter(layer_data, sigma=1)
                    # 绘图
                    cf = m.contourf(xx, yy, layer_data_smooth, levs_map, cmap=my_cmap, norm=norm)
                    # 色斑掩膜处理
                    clip = shp2clip(cf, ax, m, shpFile, chineseName, label)

                    # cf = m.pcolormesh(xx, yy, layer_data, shading='gouraud', cmap=my_cmap, norm=norm)
                    # 色斑掩膜处理
                    # clip = shp2clip(cf, ax, m, shpFile, chineseName, label, vcplot=True)

                    # 后续绘制色例用
                    c_bar = cf
                    if self.barShow:
                        c_bar_style = 1
                    else:
                        c_bar_style = 3

                if layer_type == "polyMarker":  # 散点图层
                    # 散点颜色解析
                    if layer.get('colors'):
                        # 获取值色对
                        sublevs = layer.get('intervals')
                        colors = layer.get('colors')
                        labels = layer.get('labels')
                        # 设置levs
                        # levs_map = [-9999.0]
                        # endlevs = [9999.0]
                        # levs_map.extend(sublevs)
                        # levs_map.extend(endlevs)
                        levs_map = []
                        levs_map.extend(sublevs)
                        # 标准化颜色
                        ccolors = [RGB_to_Hex(i) for i in colors]
                        my_cmap = mcolors.ListedColormap(ccolors)
                        norm = mcolors.BoundaryNorm(levs_map, my_cmap.N)
                    # 散点大小
                    if layer.get('marker_size'):
                        marker_size = layer.get('marker_size')
                    else:
                        if regionType == "3":
                            marker_size = areaConfig.get('marker_size', 500)
                        else:
                            marker_size = areaConfig.get('marker_size', 350)

                    # 散点类型，默认点图，可改成"+"等标识
                    marker_type = layer.get('marker_type', "o")

                    # 散点颜色，默认黑色
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
                    # cm = m.scatter(nan_lons, nan_lats, marker=marker_type, s=int(marker_size), c="#ABABAB")
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
                        cm = m.scatter(lons, lats, marker=marker_type, s=int(marker_size), c=marker_color)
                    clip = shp2clip(cm, ax, m, shpFile, chineseName, label, vcplot=True)
                    # 后续绘制色例用
                    if c_bar:
                        continue
                    else:
                        c_bar = cm
                        # colorbar类型，散点图类型为2
                        c_bar_style = 2

            # 裁剪图片经纬度范围
            lon1, lon2 = ax.set_xlim(startLon, endLon)
            lat1, lat2 = ax.set_ylim(startLat, endLat)
            # 自适应经纬度的主副刻度间隔，可自己更改
            lat_axis_major_space = match_interval(endLat - startLat, [0, 0.5, 1, 3, 8, 16, 41, 90, 181, 361],
                                                  [0.05, 0.1, 0.5, 1, 2, 5, 10, 30, 60],
                                                  None)
            lat_axis_minor_space = match_interval(endLat - startLat, [0, 0.5, 1, 3, 8, 16, 41, 90, 181, 361],
                                                  [0.01, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10],
                                                  None)
            lon_axis_major_space = match_interval(endLon - startLon, [0, 0.5, 1, 3, 8, 16, 41, 90, 181, 361],
                                                  [0.05, 0.1, 0.5, 1, 2, 5, 10, 30, 60],
                                                  None)
            lon_axis_minor_space = match_interval(endLon - startLon, [0, 0.5, 1, 3, 8, 16, 41, 90, 181, 361],
                                                  [0.01, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10],
                                                  None)

            # 设置主副刻度
            ax.xaxis.set_major_locator(MultipleLocator(lon_axis_major_space))
            ax.xaxis.set_minor_locator(AutoMinorLocator(lon_axis_major_space / lon_axis_minor_space))
            ax.yaxis.set_major_locator(MultipleLocator(lat_axis_major_space))
            ax.yaxis.set_minor_locator(AutoMinorLocator(lat_axis_major_space / lat_axis_minor_space))
            # 设置经纬度format
            if regionType == "1":
                ax.yaxis.set_major_formatter('{x:.1f}°N')
                ax.xaxis.set_major_formatter('{x:.1f}°E')
            if regionType == "2":
                ax.yaxis.set_major_formatter(
                                lambda x, pos: str(round(-x, 1)) + '°S' if x < 0 else 'EQ' if x == 0 else str(
                                    round(x, 1)) + '°N')
                ax.xaxis.set_major_formatter(
                                lambda x, pos: str(round(-x, 1)) + '°W' if x < 0 and x > -180 else str(
                                    abs(round(x, 1))) if x in [0, 180, -180] else str(round(x, 1)) + '°E')
            if regionType == "3":
                ax.yaxis.set_major_formatter(
                                lambda x, pos: str(round(-x, 2)) + '°S' if x < 0 else 'EQ' if x == 0 else str(
                                    round(x, 2)) + '°N')
                ax.xaxis.set_major_formatter(
                                lambda x, pos: str(round(-x, 1)) + '°W' if x < 0 and x > -180 else str(
                                    abs(round(x, 2))) if x in [0, 180, -180] else str(round(x, 2)) + '°E')

            # 设置经纬度label的字体
            for xlabel in ax.get_xticklabels():
                xlabel.set_fontname('Times New Roman')
            for ylabel in ax.get_yticklabels():
                ylabel.set_fontname('Times New Roman')
            # 设置横纵坐标刻度的长度和粗细
            ax.tick_params(which='major', labelsize=30, length=15, width=3.0)
            ax.tick_params(which='minor', labelsize=30, length=10, width=2.0)
            # 读取并叠加shp文件，在地图上叠加一些地理特征线，如区域边界、河流、湖泊等
            if areaConfig.get('shp'):
                shps_set = areaConfig.get('shp')
                for key in shps_set:
                    tmpshp = shps_set.get(key)
                    encoding = tmpshp.get('encoding', 'gbk')
                    # shpColor为16进制标识或系统自带颜色
                    m.readshapefile(tmpshp.get('shpFile'), key, color=tmpshp.get('shpColor'),
                                                linewidth=float(tmpshp.get('shpThick')), default_encoding=encoding)
                    if key == "lake":  # 湖泊填充颜色
                        for shp in m.lake:
                            poly = Polygon(shp, facecolor=tmpshp.get('shpColor'))
                            ax.add_patch(poly)
                    if key == "point":  # 点位位置
                        fontsize = tmpshp.get('labelSize')
                        city = tmpshp.get('cityName')
                        x_sub = tmpshp.get('x_sub')
                        y_sub = tmpshp.get('y_sub')
                        addName(m, font1, fontsize, x_sub, y_sub, city)
            if areaConfig.get('shpInfo'):
                shps_set = areaConfig.get('shpInfo')
                for key in shps_set:
                    if self.shpInfo:
                        shpInfo = self.shpInfo
                        if key in shpInfo:
                            tmpshp = shps_set.get(key)
                            encoding = tmpshp.get('encoding', 'gbk')
                            # shpColor为16进制标识或系统自带颜色
                            m.readshapefile(tmpshp.get('shpFile'), key, color=tmpshp.get('shpColor'),
                                            linewidth=float(tmpshp.get('shpThick')), default_encoding=encoding)
                            if key == "lake":  # 湖泊填充颜色
                                for shp in m.lake:
                                    poly = Polygon(shp, facecolor=tmpshp.get('shpColor'))
                                    ax.add_patch(poly)
                            if key == "province_label" or key == "city_label" or key == "county_label":  # 点位位置
                                fontsize = tmpshp.get('labelSize')
                                city = tmpshp.get('cityName')
                                x_sub = tmpshp.get('x_sub')
                                y_sub = tmpshp.get('y_sub')
                                addName(m, regionType, key, font1, fontsize, x_sub, y_sub, city)

            # 绘图边框加粗
            lines = plt.gca()
            lines.spines['top'].set_linewidth(2)
            lines.spines['bottom'].set_linewidth(2)
            lines.spines['left'].set_linewidth(2)
            ax.spines['right'].set_visible(True)
            lines.spines['right'].set_linewidth(2)

            # 标题
            if not mainTitle:
                mainTitle = chineseName + self.title_config.get(self.element)["shownames"] + self.title_config.get(self.eleType)["shownames"]
                if self.eleType == "JP" or self.eleType == "SK":
                    mainTitle += "预测"
                elif self.eleType == "TCC" or self.eleType == "TRMSE" or self.eleType == "ERR" or self.eleType == "SYMBOL" or self.eleType == "RERR":
                    mainTitle += "检验"

            title = mainTitle

            subTitle = ""
            if not subTitles:
                subTitles = []
                if len(self.forecastTime) == 6:
                    forecastTime = self.forecastTime[0:4] + "年" + self.forecastTime[4:6] + "月"
                elif len(self.forecastTime) == 8:
                    forecastTime = self.forecastTime[0:4] + "年" + self.forecastTime[4:6] + "月" + self.forecastTime[6:8] + "日"

                if len(self.startTime) == 6:
                    startTime = self.startTime[0:4] + "年" + self.startTime[4:6] + "月"
                elif len(self.startTime) == 8:
                    startTime = self.startTime[0:4] + "年" + self.startTime[4:6] + "月" + self.startTime[6:8] + "日"

                if len(self.endTime) == 6:
                    endTime = self.endTime[0:4] + "年" + self.endTime[4:6] + "月"
                elif len(self.endTime) == 8:
                    endTime = self.endTime[0:4] + "年" + self.endTime[4:6] + "月" + self.endTime[6:8] + "日"

                if self.eleType == "SK" or self.eleType == "JP":
                    if startTime == endTime:
                        subTitles.append(forecastTime + "起报  " + "预报日期：" + startTime)
                    else:
                        if startTime[0:4] == endTime[0:4]:
                            subTitles.append(forecastTime + "起报  " + "预报时段：" + startTime + "-" + endTime[5::])
                        else:
                            subTitles.append(forecastTime + "起报  " + "预报时段：" + startTime + "-" + endTime)
                elif self.eleType == "SYMBOL" or self.eleType == "ERR" or self.eleType == "RERR" or self.eleType == "TCC" or self.eleType == "TRMSE":
                    if startTime == endTime:
                        subTitles.append(forecastTime + "起报  " + "检验日期：" + startTime)
                    else:
                        if startTime[0:4] == endTime[0:4]:
                            subTitles.append(forecastTime + "起报  " + "检验时段：" + startTime + "-" + endTime[5::])
                        else:
                            subTitles.append(forecastTime + "起报  " + "检验时段：" + startTime + "-" + endTime)

            if subTitles:
                for i in range(len(subTitles)):
                    subTitle = subTitle + subTitles[i] + "\n"
                if len(subTitles) == 1:  # 一行副标题位置设置
                    plt.title(mainTitle, fontproperties=font1, fontsize=40, y=float(y1))
                    plt.suptitle(subTitle, fontproperties=font1, fontsize=30, y=float(y2), x=0.505)
                else:  # 两行副标题位置设置
                    plt.title(title, fontproperties=font1, fontsize=40, y=float(y3))
                    plt.suptitle(subTitle, fontproperties=font1, fontsize=30, y=float(y4), x=0.505)

            # 绘制色例
            if c_bar:
                # 色斑图图例
                if c_bar_style == 1:
                    coef = (endLon - startLon) / (endLat - startLat)
                    # 设置colorbar位置，left,bottom,width,height,数值为figure的百分比
                    rect = [barLeft, barBottom, barWidth, barHeight]
                    cbar_ax = fig.add_axes(rect)
                    # bar = m.colorbar(c_bar, location='right', size=sizeNum, pad=-1)
                    bar = fig.colorbar(c_bar, cax = cbar_ax)
                    bar.set_ticks(levs_map)
                    if self.eleType != "TCC":
                        if self.extendColor:
                            levs_map[0] = ''
                            levs_map[-1] = ''
                    bar.set_ticklabels([str(item) for item in levs_map])
                    for label in bar.ax.xaxis.get_ticklabels():
                        label.set_fontname('Times New Roman')
                    bar.ax.tick_params(labelsize=25, tick1On=False, length=0)
                    # bar.ax.set_xlabel(self.unit, labelpad=0.4, loc="center", fontproperties=font1, fontsize=25)
                    plt.text(bar_x, bar_y, self.unit, fontproperties=font1, fontsize=25, transform=ax.transData,
                                         horizontalalignment="left")
                # 散点图图例
                elif c_bar_style == 2:
                    patch = getColorMarkerLabel(ax, ccolors[::-1], labels[::-1])
                    plt.rcParams['font.sans-serif'] = ['SimHei']  # 显示中文标签
                    plt.rcParams['font.serif'] = ['Arial']
                    plt.rcParams['axes.unicode_minus'] = False
                    font = {'size': "28", 'fname': PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC"}
                    lagend_font = font_manager.FontProperties("font", **font)
                    legend_title = ""
                    leg = plt.legend(handles=patch, loc="lower right", title=legend_title, title_fontsize=30,
                                     labelcolor='black', edgecolor='black', framealpha=1, prop=font, labelspacing=0.3)
                    # 图例边框粗细
                    leg.get_frame().set_linewidth(0)

            # 数据源信息标注
            if not self.data_source:
                self.data_source = "数据源：" + self.datasource_config.get(self.dataSource)["shownames"]
            if self.data_source:
                plt.text(datasource_x, datasource_y, self.data_source, fontproperties=font1, fontsize=25,
                                     transform=ax.transData, horizontalalignment="right")

            # 其他信息标注
            if self.note:
                plt.text(note_x, note_y, self.note, fontproperties=font1, fontsize=25,
                                     transform=ax.transData, horizontalalignment="right")

            # logo标注
            if self.logo:
                if regionType == "1":
                    plt.text(startLon + 0.1, startLat + 0.1, "浙江省气候中心", fontproperties=font1,
                                         fontsize=25, transform=ax.transData,
                                         horizontalalignment="left")
                if regionType == "2":
                    plt.text(startLon + 0.05, startLat + 0.05, "浙江省气候中心", fontproperties=font1,
                                         fontsize=25, transform=ax.transData,
                                         horizontalalignment="left")
                if regionType == "3":
                    plt.text(startLon + 0.008, startLat + 0.008, "浙江省气候中心", fontproperties=font1,
                                         fontsize=25, transform=ax.transData,
                                         horizontalalignment="left")

            # output_img_name = "PREP_ZJCC_AVGT_" + self.dataSource + "_" + self.areaCode + "_" + str(self.reportTimeType.upper()) \
            #                   + "_0000_PB_" + self.forecastTime + "_" + self.startTime + "-" + self.endTime + \
            #                     "_" + self.eleType + "_BIG"

            # 保存图片
            plt.savefig(output_img_path + output_img_name + "." + output_img_type, bbox_inches="tight", pad_inches=0.1)
            # logging.info("图片生成: " + output_img_path + output_img_name + "." + output_img_type)

            return

        except Exception as e:
            traceback.format_exc()
            raise e


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


def getColorMarkerLabel(ax, colors, labels):
    '''
    圆点
    patch颜色与标签
    :param colors: 颜色列表
    :param labels: 标签列表
    :return: patch后的结果
    '''
    patch = []
    for i, color in enumerate(colors):
        tmp_patch = ax.scatter([], [], marker="o", s=350, facecolor=color, edgecolors=color, label=labels[i])
        # mpatches.Patch(color=color, label=labels[i])
        patch.append(tmp_patch)
    return patch


def RGB_to_Hex(rgb):
    """
    RGB转换为16进制，自定义cmap需要
    :param rgb: rgb三色，列表
    :return: 16进制颜色标识，字符串
    """
    # RGB = rgb.split(',')  # 将RGB格式划分开来
    color = '#'
    for i in rgb:
        # num = int(i * 255 + 0.5)
        # 将R、G、B分别转化为16进制拼接转换并大写  hex() 函数用于将10进制整数转换成16进制，以字符串形式表示
        color += str(hex(i))[-2:].replace('x', '0').upper()
    return color


def Float_to_Hex(rgb):
    """
    浮点数转换为16进制，自定义cmap需要
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


def match_interval(query_value, range_values, match_values, default_value=0.0):
    """
    获取给定值在某个区间所对应的值
    :param query_value: 给定值
    :param range_values: 区间范围组
    :param match_values: 匹配值组
    :param default_value: 未匹配到的默认值
    :return:  返回对应值,没有匹配到则返回None
    """
    list_interval = []
    for i in range(len(range_values)):
        if i != len(range_values) - 1:
            data_range = FloatInterval.closed_open(range_values[i], range_values[i + 1])
            # data_range = IntInterval.closed_open(range_values[i], range_values[i + 1])
            list_interval.append(data_range)
    match_value = default_value
    for i in range(len(list_interval)):
        if query_value in list_interval[i]:
            match_value = match_values[i]
    return match_value


def shp2clip(originfig, ax, m, shpfile, region, label, clabel=None, vcplot=None):
    sf = shapefile.Reader(shpfile, encoding='gbk')
    vertices = []
    codes = []
    for shape_rec in sf.shapeRecords():
        ####这里需要找到和region匹配的唯一标识符，record[]中必有一项是对应的。
        # if shape_rec.record[3] == region:   #####在country1.shp上，对中国以外的其他国家或地区进行maskout
        if shape_rec.record[label] in region:  #####在bou2_4p.shp上，对中国的某几个省份或地区之外的部分进行maskout
            pts = shape_rec.shape.points
            prt = list(shape_rec.shape.parts) + [len(pts)]
            for i in range(len(prt) - 1):
                for j in range(prt[i], prt[i + 1]):
                    vertices.append(m(pts[j][0], pts[j][1]))
                codes += [Path.MOVETO]
                codes += [Path.LINETO] * (prt[i + 1] - prt[i] - 2)
                codes += [Path.CLOSEPOLY]
            clip = Path(vertices, codes)
            clip = PathPatch(clip, transform=ax.transData)

    if vcplot:
        if isinstance(originfig, Iterable):
            for ivec in originfig:
                ivec.set_clip_path(clip)
        else:
            originfig.set_clip_path(clip)
    else:
        for contour in originfig.collections:
            contour.set_clip_path(clip)

    if clabel:
        clip_map_shapely = ShapelyPolygon(vertices)
        for text_object in clabel:
            if not clip_map_shapely.contains(ShapelyPoint(text_object.get_position())):
                text_object.set_visible(False)

    return clip


def addName(m, regionType, key, font, fontsize, x_sub=None, y_sub=None, city=None):
    '''
    叠加点位和中文标注
    :param m: 地图
    :return: None
    '''
    shp_tmp1 = "m." + key + "_info"
    shp_tmp2 = "m." + key
    for shapedict, state in zip(eval(shp_tmp1), eval(shp_tmp2)):

        if regionType == "1":
            if key == "province_label":
                short_name = shapedict['province']
            if key == "city_label":
                short_name = shapedict['NAME']
            if key == "county_label":
                short_name = shapedict['name1']
        else:
            short_name = shapedict['name']

        x, y = np.array(state)
        # 内部实心圆
        # plt.scatter(x, y, marker='o', s=30, color='black')
        # 外部空心圆
        # plt.scatter(x, y, marker='o', s=150, color='None', edgecolors='black')
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
            plt.text(x, y, short_name, fontproperties=font, fontsize=fontsize, ha="center")
