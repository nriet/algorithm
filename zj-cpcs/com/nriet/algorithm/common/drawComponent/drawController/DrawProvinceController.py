# -*- coding:utf-8 -*-
# @Time : 2021/09/18
# @Author : hyh
# @File : DrawProvinceController.py

import importlib, sys

importlib.reload(sys)
from mpl_toolkits.basemap import Basemap
# matplotlib升级为3.3.4
# 因为函数名变更，需要修改basemap下__init__.py文件和proj.py文件的import部分
import os, sys, uuid, ast, itertools
import traceback
import datetime

sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))))
import copy
from com.nriet.utils.StationDataUtils import StationDataUtils as sdu
import math
from scipy.interpolate import Rbf, griddata
from PIL import ImageFont
import time, io
import matplotlib
import pandas as pd
import PIL.Image as Image
import matplotlib.patches as mpatches
from com.nriet.config import ResponseCodeAndMsgEum
from metpy.interpolate import remove_nan_observations, interpolate_to_grid
from matplotlib import font_manager
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.algorithm.common.inputData.GbaseData import GbaseData
from com.nriet.algorithm.business.StationDataForGbase import StationDataForGbase

# from com.nriet.utils.obs.HuaweiObsUtils import img_save_to_obs
matplotlib.use('Agg')
# from com.nriet.utils.obs.HuaweiObsUtils import download_file
from com.nriet.utils.result.ResponseResultUtils import build_response_dict, judge_response_result, \
    response_result_convert
from com.nriet.config.ResponseCodeAndMsgEum import SERVER_HANDLING_ERROR_CODE, CIPAS_SUCCESS_CODE, \
    PARAMETER_VALUE_MISSING_CODE
import matplotlib.ticker as ticker
from com.nriet.algorithm.common.drawComponent.util import Maskout
from com.nriet.algorithm.common.drawComponent.drawController.DrawController import DrawController
from matplotlib.patches import Polygon
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from com.nriet.utils import matchUtils, fileUtils
from com.nriet.algorithm import Component
from com.nriet.config import PathConfig
from com.nriet.utils.result.ResponseResultUtils import build_response_dict
from matplotlib.ticker import AutoMinorLocator, MultipleLocator
import numpy as np
import json, logging

logging.info("Project root path is : %s" % os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))))
import matplotlib.colors as mcolors
import xarray as xr
from com.nriet.utils.colorTool import getColorValueDef, getColorMap


class DrawProvinceController():
    def __init__(self, sub_local_params):
        self.request_dict = sub_local_params
        self.areaName = sub_local_params.get("areaName")
        self.mainTitle = sub_local_params.get("mainTitle")
        self.subTitles = sub_local_params.get("subTitles")
        self.outputFile = sub_local_params.get("outputFile")
        self.sublevs = sub_local_params.get("intervals")
        self.colors = sub_local_params.get("colors")
        self.unit = sub_local_params.get("unit")
        inputData = sub_local_params.get("inputData")
        # 1、调用obs接口下载文件，数据以bytes类型返回，结果在content属性下
        # backet_name = "cipas"
        # result_dict = download_file(backet_name, input_data_name)
        # if not judge_response_result:
        #     raise AlgorithmException(response_code=judge_response_result['response_code'],
        #                              response_msg=judge_response_result["response_msg"])

        # input_data_set = xr.open_dataset(result_dict['content'])

        self.data = inputData

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
        outputFile = self.outputFile
        request_dict = self.request_dict
        data = self.data

        sublevs = self.sublevs
        colors = self.colors

        legend_labels = [str(int(i)) if i % 1 == 0 else str(i) for i in sublevs]
        labels = ['＜' + legend_labels[0]]
        for i in range(1, len(legend_labels)):
            labels.extend([legend_labels[i - 1] + '～' + legend_labels[i]])
        labels.extend(['＞' + legend_labels[-1]])

        # # 参数校验
        # draw_result = validation_params(data, request_dict)

        try:
            fontFile = PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC"
            configPath = PathConfig.CPCS_ROOT_PATH + 'com/nriet/config/regionConfigFy.json'
            font1 = FontProperties(fname=fontFile)

            fontFile_main = PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/simhei.ttf"
            font_main = FontProperties(fname=fontFile_main)

            fontFile_sub = PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/simhei.ttf"
            font_sub = FontProperties(fname=fontFile_sub)

            # 读取配置文件
            with open(configPath, "r", encoding='UTF-8') as f:
                datastr = f.read()
            data_config = json.loads(datastr)
            # 获取传参区域的参数
            areaConfig = data_config.get(areaName)
            # 获取传参区域的shp标识
            label = areaConfig.get('label')
            # 获取传参区域的中文名称
            chineseName = areaConfig.get('name')
            # 获取传参区域的绘图区域范围
            areaRegions = areaConfig.get('regions')
            startLon, endLon, startLat, endLat = [float(i) for i in areaRegions.split(',')]
            # 获取传参区域掩膜shp文件的位置
            shpFile = areaConfig.get('shpFile')
            # 获取图例位置
            barloc = areaConfig.get('loc')
            # 获取主标题的偏移度
            y_pad_main = areaConfig.get('y_pad_main')
            # 获取副标题的偏移度
            y_pad_sub = areaConfig.get('y_pad_sub')
            # 设置fig像素
            width = 2000
            if (endLon - startLon) > (endLat - startLat):
                height = 2000
            else:
                height = 3000
            fig = plt.figure(figsize=(width / 100, height / 100))
            # 设置图片个数及位置
            ax = fig.add_subplot(111)
            rate = (endLat - startLat) / (endLon - startLon) * width / height
            ax.set_position([0.08, 1 - (0.85 * rate + 0.05), 0.85, 0.85 * rate])
            # 截取指定范围数据
            lon = data["lon"]
            lat = data["lat"]
            lon = lon[(lon >= startLon - 2.5) & (lon <= endLon + 2.5)]
            lat = lat[(lat >= startLat - 2.5) & (lat <= endLat + 2.5)]
            data = data.sel(lon=lon, lat=lat)
            # 创建地图 标识为m
            m = Basemap(llcrnrlon=startLon, urcrnrlon=endLon, llcrnrlat=startLat, urcrnrlat=endLat, projection='cyl')
            # m = Basemap(llcrnrlon=startLon, urcrnrlon=endLon, llcrnrlat=startLat, urcrnrlat=endLat, lon_0=(startLon+endLon)/2, lat_0=(startLat+endLat)/2, projection='lcc')
            # 创建地图网格
            xx, yy = np.meshgrid(data['lon'], data['lat'])
            # 读取色例文件并自定义cmap
            # f = open(iniPath, "r")
            # lines = f.read().splitlines()
            levs = [-9999.0]
            endlevs = [9999.0]
            # sublevs = [float(i) for i in list(lines[4].split(','))];print(sublevs)
            levs.extend(sublevs)
            levs.extend(endlevs)
            # ccolorStr = lines[11:];print(ccolorStr)
            ccolors = [RGB_to_Hex(i) for i in colors]
            my_cmap = mcolors.ListedColormap(ccolors)
            norm = mcolors.BoundaryNorm(levs, my_cmap.N)
            # 绘图并掩膜
            cs = m.contourf(xx, yy, data, levels=levs, cmap=my_cmap, norm=norm)
            clip = Maskout.shp2clip(cs, ax, m, shpFile, chineseName, label)
            # 裁剪图片经纬度范围
            lon1, lon2 = ax.set_xlim(startLon, endLon)
            lat1, lat2 = ax.set_ylim(startLat, endLat)
            # 自适应经纬度的主副刻度间隔
            lat_axis_major_space = matchUtils.match_interval(endLat - startLat, [0, 3, 8, 16, 41, 90, 181, 361],
                                                             [0.5, 1, 2, 5, 10, 30, 60],
                                                             None)
            lat_axis_minor_space = matchUtils.match_interval(endLat - startLat, [0, 3, 8, 16, 41, 90, 181, 361],
                                                             [0.1, 0.2, 0.5, 1, 2, 5, 10],
                                                             None)
            lon_axis_major_space = matchUtils.match_interval(endLon - startLon, [0, 3, 8, 16, 41, 90, 181, 361],
                                                             [0.5, 1, 2, 5, 10, 30, 60],
                                                             None)
            lon_axis_minor_space = matchUtils.match_interval(endLon - startLon, [0, 3, 8, 16, 41, 90, 181, 361],
                                                             [0.1, 0.2, 0.5, 1, 2, 5, 10],
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
            ax.yaxis.set_major_formatter('{x:.0f}°N')
            ax.xaxis.set_major_formatter('{x:.0f}°E')
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
                        x_sub = tmpshp.get('x_sub')
                        y_sub = tmpshp.get('y_sub')
                        addName(m, font1, fontsize, x_sub, y_sub, city)
            # 边框加粗
            lines = plt.gca()
            lines.spines['top'].set_linewidth(4)
            lines.spines['bottom'].set_linewidth(4)
            lines.spines['left'].set_linewidth(4)
            lines.spines['right'].set_linewidth(4)
            # 绘制色例
            # coef = (endLon - startLon) / (endLat - startLat)
            # num = str(8 * coef) + "%"
            # bar = m.colorbar(cs, location='bottom', pad=num)
            # bar.set_ticks(levs)
            # for label in [bar.ax.xaxis.get_ticklabels()[0], bar.ax.xaxis.get_ticklabels()[-1]]:
            #     label.set_visible(False)
            # bar.ax.tick_params(labelsize=30, tick1On=False)
            patch = getColorLabel(colors[::-1], labels[::-1])
            plt.rcParams['font.sans-serif'] = ['SimHei']  # 显示中文标签
            plt.rcParams['font.serif'] = ['Arial']
            plt.rcParams['axes.unicode_minus'] = False
            font = {'size': "18",
                    'fname': PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC"}
            lagend_font = font_manager.FontProperties("font", **font)
            legend_title = "  单位：" + self.unit
            leg = plt.legend(handles=patch, loc=barloc, title=legend_title, title_fontsize=20, labelcolor='black',
                             edgecolor='black', framealpha=1, prop=lagend_font, labelspacing=0.2)
            # 图例边框粗细
            leg.get_frame().set_linewidth(2.0)
            # 标题
            title = mainTitle
            subTitle = ""
            # for i in range(len(subTitles)):
            #     subTitle = subTitle + subTitles[i] + "\n"
            for i in range(len(subTitles)):
                subTitle = subTitle + subTitles[i]

            # plt.title(title, fontproperties=font_main, fontsize=40, y=1 - 100 / (height * 0.85 * rate), color="blue")
            # plt.suptitle(subTitle, fontproperties=font_sub, fontsize=30, y=0.95 - 120 / height, x=0.505, color="blue")
            # 字体
            # font_main = ImageFont.truetype(font=fontFile, size=40)  # 主标题20px
            # font_sub = ImageFont.truetype(font=fontFile, size=30)  # 副标题15px
            # plt.text(116, 44, title, fontsize = 40, fontproperties=font1)

            # 6.保存
            # 是否上传nfsshare
            save_to_nfsshare_switch = look_for_single_global_config("SAVE_TO_NFSSHARE_SWITCH")
            save_to_obs_switch = look_for_single_global_config("SAVE_TO_OBS_SWITCH")

            save_to_nfsshare_switch = 1
            if int(save_to_nfsshare_switch) or self.request_dict.get("saveToNfsshare"):
                plt.savefig(outputFile)
                im = Image.open(outputFile, "r")
                # 叠加logo
                # ncc_img = Image.open(PathConfig.CPCS_ROOT_PATH+ 'com/nriet/algorithm/common/drawComponent/logoFiles/logo.png')
                # x, y = ncc_img.size
                # p1 = Image.new('RGBA', ncc_img.size, (255, 255, 255))
                # p1.paste(ncc_img, (0, 0, x, y), ncc_img)
                # im.paste(p1, (int(width*0.08) + 30, int(height*0.05) + 30))
                if areaName == "YAJIANG":
                    yajiang_img = Image.open(
                        PathConfig.CPCS_ROOT_PATH + 'com/nriet/algorithm/common/drawComponent/imgFiles/yajiang.png')
                    im.paste(yajiang_img, (0, 0, yajiang_img.size[0], yajiang_img.size[1]), yajiang_img)
                real_pic_size = (0, 0, width, height * (0.05 + 0.85 * rate) + 150)
                im = im.crop(real_pic_size)
                im.save(outputFile)

            # # 是否上传至obs
            # if int(save_to_obs_switch) or self.request_dict.get("saveToObs"):
            #     buf = io.BytesIO()
            #     plt.savefig(buf, fmt=output_img_type, dpi=100)
            #     buf.seek(0)
            #     pil_img = copy.deepcopy(Image.open(buf))
            #     buf.close()
            #     storage_result = img_save_to_obs(pil_img, output_img_name, output_img_type)

            # 删除临时文件
            # os.remove(output_img_path + output_img_name + '.' + output_img_type)
            # logging.info("             delete temp file %s" % output_img_path + output_img_name + '.' + output_img_type)

        except Exception as e:
            logging.error(traceback.format_exc())
            raise AlgorithmException(response_code=SERVER_HANDLING_ERROR_CODE, response_msg=e.__str__())

        stop_time = time.clock()
        cost = stop_time - start_time
        logging.info("         %s cost %s second" % (os.path.basename(__file__), cost))

        return


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


def addName(m, font, fontsize, x_sub=None, y_sub=None, city=None):
    '''
    叠加点位和中文标注
    :param m: 地图
    :return: None
    '''
    for shapedict, state in zip(m.point_info, m.point):
        short_name = shapedict['name1']
        x, y = np.array(state)
        # 内部实心圆
        # plt.scatter(x, y, marker='o', s=30, color='black')
        # # 外部空心圆
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


def add_logos(im, params_dict):
    for logo_name, logo_instance in params_dict.items():
        ncc_img = Image.open(logo_instance['file_path'])
        x, y = ncc_img.size
        p1 = Image.new('RGBA', ncc_img.size, (255, 255, 255))
        p1.paste(ncc_img, (0, 0, x, y), ncc_img)
        im.paste(p1, logo_instance['logo_location'])


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
        logging.info("request params error,lack of input_data!")  # 此处以后引入日志
        draw_result["response_code"] = "9851"
        draw_result["response_msg"] = " DrawController request params error,lack of 'input_data' !"
        return draw_result
    if not request_dict:
        logging.info("DrawController request params error,lack of 'input_data' !")
        draw_result["response_code"] = "9851"
        draw_result["response_msg"] = "request params error,lack of 'request_dict' !"
        return draw_result

    return draw_result


def interp_idw(areaName, inputData, station_lon, station_lat, startLon, endLon, startLat, endLat):
    zlat = station_lat
    zlon = station_lon
    if areaName in ["BABJ"]:
        lon_grid = ((int(endLon + 1) - int(startLon - 1))) + 1
        lat_grid = ((int(endLat + 1) - int(startLat - 1))) + 1
        glon = np.linspace(int(startLon), int(endLon), lon_grid)
        glat = np.linspace(int(startLat), int(endLat), lat_grid)
    else:
        lon_grid = ((int(endLon + 1) - int(startLon - 1))) * 20 + 1
        lat_grid = ((int(endLat + 1) - int(startLat - 1))) * 20 + 1
        glon = np.linspace(int(startLon - 1), int(endLon + 1), lon_grid)
        glat = np.linspace(int(startLat - 1), int(endLat + 1), lat_grid)
    olon, olat = np.meshgrid(glon, glat)
    olon, olat = olon.flatten(), olat.flatten()
    zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, inputData)
    grid1 = simple_idw(zlon1, zlat1, tmpdata, olon, olat)
    grid1 = grid1.reshape(lat_grid, lon_grid)
    interp_grid_data = xr.DataArray(grid1, coords=[glat, glon], dims=['lat', 'lon'])

    # output_data = {}
    # encoding = {}
    # output_data["grid"] = interp_grid_data
    # encoding["grid"] = {'dtype': 'float32', '_FillValue': 999999.0}
    # data_set = xr.Dataset(output_data)
    # data_set.to_netcdf("/nfsshare/cdbdata/product/cipas3/hzzz/111.nc", encoding=encoding)

    return interp_grid_data


def interp_ref(areaName, inputData, station_lon, station_lat, startLon, endLon, startLat, endLat):
    zlat = station_lat
    zlon = station_lon
    if areaName in ["BABJ"]:
        lon_grid = ((int(endLon) - int(startLon))) + 1
        lat_grid = ((int(endLat) - int(startLat))) + 1
        glon = np.linspace(int(startLon), int(endLon), lon_grid)
        glat = np.linspace(int(startLat), int(endLat), lat_grid)
    else:
        lon_grid = ((int(endLon + 1) - int(startLon - 1))) * 20 + 1
        lat_grid = ((int(endLat + 1) - int(startLat - 1))) * 20 + 1
        glon = np.linspace(int(startLon - 1), int(endLon + 1), lon_grid)
        glat = np.linspace(int(startLat - 1), int(endLat + 1), lat_grid)

    olon, olat = np.meshgrid(glon, glat)
    zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, inputData)

    rf = Rbf(zlon1, zlat1, tmpdata, kind="thin_plate", smooth=0.01)
    grid1 = rf(olon, olat)
    grid1 = grid1.reshape(lat_grid, lon_grid)
    interp_grid_data = xr.DataArray(grid1, coords=[glat, glon], dims=['lat', 'lon'])

    return interp_grid_data


def interp_cressman(areaName, inputData, station_lon, station_lat, startLon, endLon, startLat, endLat):
    zlat = station_lat
    zlon = station_lon
    lon_grid = ((int(endLon) - int(startLon))) + 1
    lat_grid = ((int(endLat) - int(startLat))) + 1
    glon = np.linspace(int(startLon), int(endLon), lon_grid)
    glat = np.linspace(int(startLat), int(endLat), lat_grid)
    olon, olat = np.meshgrid(glon, glat)
    boundary_coords = {"west": startLon, "south": startLat, "east": endLon, "north": endLat}
    # ols = np.asarray([olon.flatten(), olat.flatten()]).swapaxes(1, 0)
    zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, inputData)
    gx, gy, grid1 = interpolate_to_grid(zlon1, zlat1, tmpdata, interp_type='cressman', minimum_neighbors=2, hres=0.5,
                                        search_radius=3.5, boundary_coords=boundary_coords)
    glat = gy[:, 0]
    glon = gx[0]
    # grid1 = inverse_distance_to_grid(zlon1, zlat1, tmpdata, olon, olat, 2.5)
    # logging.info(grid1.shape)
    interp_grid_data = xr.DataArray(grid1, coords=[glat, glon], dims=['lat', 'lon'])
    return interp_grid_data


def txtOutPut(var, filePath, fileName, index, station, lon, lat, jp, sk, ltm):
    time = datetime.datetime.now().strftime('%Y-%m-%d')
    if var == "RAIN":
        content = "CIPAS 1 2 13 14\r\n# HEADINFO\r\n# DESCRIPTION 站点图_降水量预报值_1000_" + time + "-00-00-00\r\n# SCD_CATEGORY -999\r\n# DATA_STORAGE_FORMAT CIPAS\r\n# TIME PDAY 10 -999 -999\r\n# LEVEL 1 1000\r\n# MISSING_VALUE 999999\r\n# ATTRIBUTES " + str(
            len(
                station)) + " 7 站点编号 站点经度 站点纬度 站点海拔 距平百分率 降水量预报值 气候场\r\n# FORMATDEFINE f10.2 f10.2 f10.2 f10.2 f10.2 f10.2 f10.2\r\n# PROJECTION LONGLAT\r\n# SPATALL_BOX 73.0 54.0 135.0 4.0\r\n# DRAWSET 00\r\n# DATASET\r\n# DATA 1\r\n"
    if var == "FROST":
        content = "CIPAS 1 2 13 14\r\n# HEADINFO\r\n# DESCRIPTION 站点图_初霜冻日期预报值_1000_" + time + "-00-00-00\r\n# SCD_CATEGORY -999\r\n# DATA_STORAGE_FORMAT CIPAS\r\n# TIME PDAY 10 -999 -999\r\n# LEVEL 1 1000\r\n# MISSING_VALUE 999999\r\n# ATTRIBUTES " + str(
            len(
                station)) + " 7 站点编号 站点经度 站点纬度 站点海拔 距平 初霜冻日序预报值 气候场\r\n# FORMATDEFINE f10.2 f10.2 f10.2 f10.2 f10.2 f10.2 f10.2\r\n# PROJECTION LONGLAT\r\n# SPATALL_BOX 73.0 54.0 135.0 4.0\r\n# DRAWSET 00\r\n# DATASET\r\n# DATA 1\r\n"
    if var == "TEMP":
        content = "CIPAS 1 2 13 14\r\n# HEADINFO\r\n# DESCRIPTION 站点图_气温预报值_1000_" + time + "-00-00-00\r\n# SCD_CATEGORY -999\r\n# DATA_STORAGE_FORMAT CIPAS\r\n# TIME PDAY 10 -999 -999\r\n# LEVEL 1 1000\r\n# MISSING_VALUE 999999\r\n# ATTRIBUTES " + str(
            len(
                station)) + " 7 站点编号 站点经度 站点纬度 站点海拔 距平 气温预报值 气候场\r\n# FORMATDEFINE f10.2 f10.2 f10.2 f10.2 f10.2 f10.2 f10.2\r\n# PROJECTION LONGLAT\r\n# SPATALL_BOX 73.0 54.0 135.0 4.0\r\n# DRAWSET 00\r\n# DATASET\r\n# DATA 1\r\n"
    for i in range(len(station)):
        if i in index:
            if str(ltm[index.index(i)]) == "nan":
                ltm[index.index(i)] = "999999.00"
                content = content + str(int(station[i])) + " " + '{:.2f}'.format(lon[i]) + " " + '{:.2f}'.format(
                    lat[i]) + " 999999.00 " + '{:.2f}'.format(jp[i]) + " " + "999999.00 999999.00" + "\r\n"
            else:
                content = content + str(int(station[i])) + " " + '{:.2f}'.format(lon[i]) + " " + '{:.2f}'.format(
                    lat[i]) + " 999999.00 " + '{:.2f}'.format(jp[i]) + " " + '{:.2f}'.format(
                    sk[index.index(i)]) + " " + '{:.2f}'.format(
                    ltm[index.index(i)]) + "\r\n"
        else:
            content = content + str(int(station[i])) + " " + '{:.2f}'.format(lon[i]) + " " + '{:.2f}'.format(
                lat[i]) + " 999999.00 " + '{:.2f}'.format(jp[i]) + " 999999.00 999999.00" + "\r\n"

    if not os.path.isdir(filePath):
        os.makedirs(filePath)
    with open(filePath + fileName + ".cps", "w", encoding="utf-8") as f:
        f.write(content)
    return


def simple_idw(x, y, z, xi, yi):
    dist = distance_matrix(x, y, xi, yi)
    weights = 1.0 / dist ** 10
    weights /= weights.sum(axis=0)
    zi = np.dot(weights.T, z)
    return zi


def distance_matrix(x0, y0, x1, y1):
    obs = np.vstack((x0, y0)).T
    interp = np.vstack((x1, y1)).T
    d0 = np.subtract.outer(obs[:, 0], interp[:, 0])
    d1 = np.subtract.outer(obs[:, 1], interp[:, 1])
    return np.hypot(d0, d1)


if __name__ == '__main__':
    main_start_time = time.clock()
    module = sys.modules[__name__]
    request_dict = None
    serial_no = str(uuid.uuid4())
    ext_params = ast.literal_eval(sys.argv[1])
    # ext_params = {"outputFile":"/nfsshare/cdbdata/data/zj_data/monitor/hzzz/降水量预报图_4a31e6b5-ce00-4f6b-8096-213b2e97a6ed_image.png","province":"ZJ","subTitles":"2023年7月","ltm":"1991-2020","mainTitle":"降水量预报图","drawType":"SK","timeType":"mon","dataFile":"/nfsshare/cdbdata/data/zj_data/monitor/hzzz/4a31e6b5-ce00-4f6b-8096-213b2e97a6ed.txt","startTime":"202307","endTime":"202307","element":"RAIN"}
    # ext_params = {"dataFile": "/nfsshare/cdbdata/product/cipas3/hzzz/b919d55b-c8e9-421f-9db3-009fa8dbae90.txt", "element": "TEMP", "province": "BABJ","mainTitle":"123456","subTitles":["000"],"outputFile":"/nfsshare/cdbdata/product/cipas3/hzzz/a28326d8-1778-4a64-8837-e29139adb1c4.png","drawType":"SK","timeType":"mon","ltm":"1991-2020","startTime":"202111","endTime":"202111"}

    colors = ext_params.get("colors", None)
    intervals = ext_params.get("intervals", None)
    time_type = ext_params.get("timeType", "NONE")
    ltm = ext_params.get("ltm", "NONE")
    outputFile = ext_params.get("outputFile")
    outputFileArr = outputFile.split("/")
    output_img_name = outputFileArr[-1].split(".")[0]
    output_img_path = '/'.join(outputFileArr[:-1])
    # 气温参数
    if ext_params.get("element") == "TEMP":
        # if ext_params.get("drawType") == "SK":
        #     ltm_path = "/nfsshare/cdbdata/data/STATION/avgt/ltm/CH/" + time_type + "_"+ ltm +".nc"
        #     ds = xr.open_dataset(ltm_path)
        #     station_all = ds["station"].values
        var = "avgt"
        unit_sk = "℃"
        unit_jp = "℃"
        iniPath_jp = "/nfsshare/cdbdata/algorithm/conductor/WMFS/huishang/avgt_jp.ini"
        iniPath_sk = "/nfsshare/cdbdata/algorithm/conductor/WMFS/huishang/talk_avgt_sk_ch.ini"
        legend_labels_jp = ['<-2', '-2~F34~*~F~-1', '-1~F34~*~F~-0.5', '-0.5~F34~*~F~0.5', '0.5~F34~*~F~1',
                            '1~F34~*~F~2', '>2']
        legend_labels_sk = ['<-32', '-32~F34~*~F~-28', '-28~F34~*~F~-24', '-24~F34~*~F~-20', '-20~F34~*~F~-16',
                            '-16~F34~*~F~-12', '-12~F34~*~F~-8', '-8~F34~*~F~-4', '-4~F34~*~F~0', '0~F34~*~F~4',
                            '4~F34~*~F~8', '8~F34~*~F~12', '12~F34~*~F~16', '16~F34~*~F~20', '20~F34~*~F~24',
                            '24~F34~*~F~28', '28~F34~*~F~32', '>32']
        intervals_sk = [-32, -28, -24, -20, -16, -12, -8, -4, 0, 4, 8, 12, 16, 20, 24, 28, 32]
        colors_sk = [[0, 0, 0.196078431372549
                      ], [0, 0, 0.588235294117647
                          ], [0, 0, 1
                              ], [0, 0.294117647058824, 1
                                  ], [0, 0.588235294117647, 1
                                      ], [0, 0.784313725490196, 1
                                          ], [0.196078431372549, 1, 1
                                              ], [0.607843137254902, 1, 1
                                                  ], [0.784313725490196, 1, 1
                                                      ], [1, 1, 0.588235294117647
                                                          ], [1, 1, 0.196078431372549
                                                              ], [1, 0.784313725490196, 0
                                                                  ], [1, 0.588235294117647, 0.392156862745098
                                                                      ], [1, 0.588235294117647, 0.196078431372549
                                                                          ], [1, 0.392156862745098, 0
                                                                              ], [0.901960784313726, 0, 0
                                                                                  ], [0.588235294117647, 0, 0
                                                                                      ], [0.392156862745098, 0, 0
                                                                                          ]]
        intervals_jp = [-1.99, -0.99, -0.49, 0.49, 0.99, 1.99]
        intervals_jp_prov = [-2.0, -1.0, -0.5, 0.5, 1.0, 2.0]
        colors_jp = [[0.0196078431372549, 0, 0.980392156862745
                      ], [0, 0.603921568627451, 0.988235294117647
                          ], [0.443137254901961, 0.988235294117647, 1
                              ], [1, 1, 0.858823529411765
                                  ], [0.976470588235294, 0.525490196078431, 0.505882352941176
                                      ], [1, 0.235294117647059, 0.227450980392157
                                          ], [0.792156862745098, 0.129411764705882, 0.211764705882353
                                              ]]
    # 降水参数
    if ext_params.get("element") == "RAIN":
        # if ext_params.get("drawType") == "SK":
        #     ltm_path = "/nfsshare/cdbdata/data/STATION/rain/20-20/ltm/CH/" + time_type + "_" + ltm + ".nc"
        #     ds = xr.open_dataset(ltm_path)
        #     station_all = ds["station"].values
        var = "rain"
        unit_sk = "mm"
        unit_jp = "%"
        iniPath_jp = "/nfsshare/cdbdata/algorithm/conductor/WMFS/huishang/rain_jp.ini"
        iniPath_sk = "/nfsshare/cdbdata/algorithm/conductor/WMFS/huishang/talk_rain_sk_ch.ini"
        legend_labels_jp = ['-80%~F34~*~F~-50%', '-50%~F34~*~F~-20%', '-20%~F34~*~F~-10%', '-10%~F34~*~F~10%',
                            '10%~F34~*~F~20%', '20%~F34~*~F~50%', '50%~F34~*~F~80%']
        legend_labels_sk = ['<1', '1~F34~*~F~10', '10~F34~*~F~25', '25~F34~*~F~50', '50~F34~*~F~100', '100~F34~*~F~200',
                            '200~F34~*~F~300', '300~F34~*~F~400', '400~F34~*~F~600', '600~F34~*~F~800', '>800']
        intervals_sk = [1, 10.0, 25.0, 50, 100, 200, 300, 400, 600, 800]
        colors_sk = [[0.992156862745098, 1, 0.674509803921569
                      ], [0.984313725490196, 0.984313725490196, 0.0509803921568627
                          ], [0.309803921568627, 0.972549019607843, 0
                              ], [0.168627450980392, 0.705882352941177, 0
                                  ],
                     [0.133333333333333, 0.470588235294118, 0
                      ], [0.482352941176471, 0.63921568627451, 0.870588235294118
                          ], [0.27843137254902, 0.258823529411765, 1
                              ], [0.0666666666666667, 0.0588235294117647, 0.623529411764706
                                  ],
                     [0.996078431372549, 0.0117647058823529, 0.831372549019608
                      ], [1, 0, 0
                          ], [0.556862745098039, 0, 0
                              ]]
        intervals_jp = [-49.9, -19.9, -9.9, 9.9, 19.9, 49.9]
        intervals_jp_prov = [-50.0, -20.0, -10.0, 10.0, 20.0, 50.0]
        colors_jp = [[0.988235294117647, 0.00784313725490196, 0], [1, 0.509803921568627, 0.00392156862745098
                                                                   ], [1, 0.709803921568627, 0.454901960784314
                                                                       ], [0.996078431372549, 1, 0.87843137254902
                                                                           ], [0.443137254901961, 0.988235294117647, 1
                                                                               ],
                     [0, 0.603921568627451, 0.988235294117647
                      ],
                     [0.0196078431372549, 0, 0.980392156862745]]
    # 初霜冻参数
    if ext_params.get("element") == "FROST":
        if ext_params.get("drawType") == "SK":
            ltm_path = "/nfsshare/cdbdata/data/STATION/csd/ltm/CH/" + time_type + "_" + ltm + ".nc"
            ds = xr.open_dataset(ltm_path)
            station_all = ds["station"].values
        var = "csd"
        unit_sk = "月-日"
        unit_jp = "日"
        iniPath_jp = ""
        iniPath_sk = "/nfsshare/cdbdata/ini/color_csd_fy.ini"
        legend_labels_jp = []
        legend_labels_sk = ['<9.1', '9.1~F34~*~F~9.10', '9.11~F34~*~F~9.20', '9.21~F34~*~F~9.30',
                            '10.01~F34~*~F~10.10',
                            '10.11~F34~*~F~10.20', '10.21~F34~*~F~10.31', '11.01~F34~*~F~11.10',
                            '11.11~F34~*~F~11.20',
                            '11.21~F34~*~F~11.30', '12.01~F34~*~F~12.10', '12.11~F34~*~F~12.20',
                            '12.21~F34~*~F~12.31',
                            '01.01~F34~*~F~01.10', '01.11~F34~*~F~01.20', '>01.20']

    page_params = {}
    page_params["areaName"] = ext_params.get("province")
    page_params["mainTitle"] = ext_params.get("mainTitle")
    page_params["subTitles"] = ext_params.get("subTitles")
    page_params["dataFile"] = ext_params.get("dataFile")
    page_params["outputFile"] = ext_params.get("outputFile")

    # 获取插值范围
    areaName = ext_params.get("province")
    # 全国范围
    if areaName in ["BABJ"]:
        startLon, endLon, startLat, endLat = [60, 150, 0, 60]
        method_params = {
            "cycle": "",
            "data_output_types": "png",
            "iniPath": "/nfsshare/cdbdata/algorithm/conductor/WMFS/huishang/",
            "data_output_params": [
                {
                    "region_type": "wholeChinaPro",
                    "output_img_type": "png",
                    "output_img_max_width": "930",
                    "layers": [
                        {
                            "draw_regions": ":,:,:,:",
                            "data_source": "",
                            "layer_type": "contourMap"
                        }
                    ],
                    "x_values": "",
                    "y_values": ""
                }
            ]
        }
        # txt数据的插值处理得到距平格点数据
        if ext_params.get("drawType") == "JP":
            data_src = pd.read_table(ext_params.get("dataFile"), header=None, encoding='utf-8', sep=" ")
            dataAll = np.array(data_src)
            data = dataAll[:, 3]
            station_lon = dataAll[:, 1]
            station_lat = dataAll[:, 2]

            grid_data = interp_idw(areaName, data, station_lon, station_lat, startLon, endLon, startLat, endLat)
            tmp1 = {}
            tmp1["outputData"] = grid_data
            tmp2 = [tmp1]

            method_params["iniPath"] = iniPath_jp
            # intervals = getColorValueDef(iniPath_jp).tolist()
            method_params["data_output_params"][0]["layers"][0]["intervals"] = getColorValueDef(iniPath_jp).tolist()
            method_params["data_output_params"][0]["layers"][0]["colors"] = getColorMap(iniPath_jp).tolist()
            method_params["data_output_params"][0]["layers"][0]["legend_labels"] = legend_labels_jp
            if intervals:
                method_params["data_output_params"][0]["layers"][0]["intervals"] = intervals
                legend_labels = [str(int(i)) if i % 1 == 0 else str(i) for i in intervals]
                labels = ['<' + legend_labels[0]]
                for i in range(1, len(legend_labels)):
                    labels.extend([legend_labels[i - 1] + '~F34~*~F~' + legend_labels[i]])
                labels.extend(['>' + legend_labels[-1]])
                method_params["data_output_params"][0]["layers"][0]["legend_labels"] = labels
            if colors:
                method_params["data_output_params"][0]["layers"][0]["colors"] = colors
            method_params["data_output_params"][0]["main_title"] = ext_params.get("mainTitle")
            method_params["data_output_params"][0]["sub_titles"] = ext_params.get("subTitles")

            method_params["data_output_params"][0]["main_title_font"] = "times.ttf"
            method_params["data_output_params"][0]["sub_titles_font"] = "simhei.ttf"
            method_params["data_output_params"][0]["title_color"] = "blue"
            method_params["data_output_params"][0]["main_title_size"] = "65"
            method_params["data_output_params"][0]["sub_titles_size"] = "80"
            method_params["data_output_params"][0]["title_leftshift"] = "100"
            method_params["data_output_params"][0]["title_topshift"] = "80"

            method_params["data_output_params"][0]["output_img_path"] = output_img_path + "/"
            method_params["data_output_params"][0]["output_img_name"] = output_img_name
            method_params["data_output_params"][0]["layers"][0]["unit"] = "单位：" + unit_jp

            me = DrawController(sub_local_params=method_params, algorithm_input_data=tmp2)
            result_dict = me.execute()

        # 反演得到预报实况数据
        if ext_params.get("drawType") == "SK":
            data_src = pd.read_table(ext_params.get("dataFile"), header=None, encoding='utf-8', sep=" ")
            dataAll = np.array(data_src)
            data_file = dataAll[:, 3]
            station_lon_file = dataAll[:, 1]
            station_lat_file = dataAll[:, 2]
            station_id = dataAll[:, 0]
            data = data_file
            station_lon = station_lon_file
            station_lat = station_lat_file

            if time_type.upper() == "SEASON":
                tmpSatrtTime = ext_params.get("startTime")
                tmpEndTime = ext_params.get("endTime")
                sea = ["04", "01", "02", "03"]
                sindex = sea.index(tmpSatrtTime[4:])
                eindex = sea.index(tmpEndTime[4:])
                smon = ["12", "03", "06", "09"]
                emon = ["02", "05", "08", "11"]
                tmpSatrtTime = str(int(tmpSatrtTime[:4]) - 1) + smon[sindex] if sindex == 0 else tmpSatrtTime[:4] + \
                                                                                                 smon[sindex]
                tmpEndTime = str(int(tmpEndTime[:4])) + emon[eindex] if eindex == 0 else tmpEndTime[:4] + \
                                                                                         emon[eindex]
                time_type = "mon"
            else:
                tmpSatrtTime = ext_params.get("startTime")
                tmpEndTime = ext_params.get("endTime")

            # 加载数据
            # station_inter = [val for val in station_id if val in station_all]
            # index = [station_id.tolist().index(sta) for sta in station_id.tolist() if sta in station_inter]
            # data = data_file[index]
            # station_lon = station_lon_file[index]
            # station_lat = station_lat_file[index]
            # ltm_data = sdu.get_station_ltm_data(ltm_path, time_type, tmpSatrtTime, tmpEndTime, var, station_inter, "")
            if ext_params.get("element") == "TEMP":
                ltm_data_a = GbaseData({
                    'dataSource': 'CSOD'
                    , 'elements': 'TEMP'
                    , 'statisticType': 'AVG'
                    , 'eleType': 'LTM'
                    , 'ltm': ltm
                    , 'stationStr': ",".join([str(int(item)) for item in station_id])
                    , 'timeType': time_type
                    , 'timeRanges': [int(tmpSatrtTime), int(tmpEndTime)]
                }, None)
                ltm_data_a.execute()
                ltm_data = ltm_data_a.output_data[0]['outputData']
                ltm_data = ltm_data.mean(dim="time", skipna=True, keep_attrs=True)
                skData = data + ltm_data.values
                result = txtOutPut("TEMP", output_img_path + "/", output_img_name, list(range(len(station_id))),
                                   station_id, station_lon_file,
                                   station_lat_file,
                                   data_file, skData, ltm_data.values)
                grid_data = interp_idw(areaName, skData, station_lon, station_lat, startLon, endLon, startLat, endLat)
            if ext_params.get("element") == "RAIN":
                ltm_data_a = GbaseData({
                    'dataSource': 'CSOD'
                    , 'elements': 'RAIN'
                    , 'statisticType': 'SUM'
                    , 'ltm': ltm
                    , 'eleType': 'LTM'
                    , 'stationStr': ",".join([str(int(item)) for item in station_id])
                    , 'timeType': time_type
                    , 'timeRanges': [int(tmpSatrtTime), int(tmpEndTime)]
                }, None)
                ltm_data_a.execute()
                ltm_data = ltm_data_a.output_data[0]['outputData']
                tmpdata = ltm_data.mean(dim="time", skipna=True, keep_attrs=True)
                ltm_data = ltm_data.sum(dim="time", skipna=True, keep_attrs=True)
                tmpdata = tmpdata.where(np.isnan(tmpdata), 1)
                ltm_data = ltm_data * tmpdata

                skData = (data * ltm_data.values) / 100 + ltm_data.values
                result = txtOutPut("RAIN", output_img_path + "/", output_img_name, list(range(len(station_id))),
                                   station_id, station_lon_file,
                                   station_lat_file,
                                   data_file, skData, ltm_data.values)
                grid_data = interp_idw(areaName, skData, station_lon, station_lat, startLon, endLon, startLat, endLat)

            if ext_params.get("element") == "FROST":
                # 加载数据
                station_inter = [val for val in station_id if val in station_all]
                index = [station_id.tolist().index(sta) for sta in station_id.tolist() if sta in station_inter]
                data = data_file[index]
                station_lon = station_lon_file[index]
                station_lat = station_lat_file[index]
                ltm_data = sdu.get_station_ltm_data(ltm_path, time_type, tmpSatrtTime, tmpEndTime, var, station_inter,
                                                    "")
                ltm_data = ltm_data.mean(dim="time", skipna=True, keep_attrs=True)
                skData = data + ltm_data.values
                result = txtOutPut("FROST", output_img_path + "/", output_img_name, index, station_id, station_lon_file,
                                   station_lat_file,
                                   data_file, skData, ltm_data.values)

                grid_data = interp_cressman(areaName, skData, station_lon, station_lat, startLon, endLon, startLat,
                                            endLat)
            tmp1 = {}
            tmp1["outputData"] = grid_data
            tmp2 = [tmp1]

            method_params["iniPath"] = iniPath_sk
            # intervals = getColorValueDef(iniPath_sk).tolist()
            method_params["data_output_params"][0]["layers"][0]["intervals"] = getColorValueDef(iniPath_sk).tolist()
            method_params["data_output_params"][0]["layers"][0]["colors"] = getColorMap(iniPath_sk).tolist()
            method_params["data_output_params"][0]["layers"][0]["legend_labels"] = legend_labels_sk
            if intervals:
                method_params["data_output_params"][0]["layers"][0]["intervals"] = intervals
                legend_labels = [str(int(i)) if i % 1 == 0 else str(i) for i in intervals]
                labels = ['<' + legend_labels[0]]
                for i in range(1, len(legend_labels)):
                    labels.extend([legend_labels[i - 1] + '~F34~*~F~' + legend_labels[i]])
                labels.extend(['>' + legend_labels[-1]])
                method_params["data_output_params"][0]["layers"][0]["legend_labels"] = labels
            if colors:
                method_params["data_output_params"][0]["layers"][0]["colors"] = colors
            method_params["data_output_params"][0]["main_title"] = ext_params.get("mainTitle")
            method_params["data_output_params"][0]["sub_titles"] = ext_params.get("subTitles")

            method_params["data_output_params"][0]["main_title_font"] = "times.ttf"
            method_params["data_output_params"][0]["sub_titles_font"] = "simhei.ttf"
            method_params["data_output_params"][0]["title_color"] = "blue"
            method_params["data_output_params"][0]["main_title_size"] = "65"
            method_params["data_output_params"][0]["sub_titles_size"] = "80"
            method_params["data_output_params"][0]["title_leftshift"] = "100"
            method_params["data_output_params"][0]["title_topshift"] = "80"

            method_params["data_output_params"][0]["output_img_path"] = output_img_path + "/"
            method_params["data_output_params"][0]["output_img_name"] = output_img_name
            method_params["data_output_params"][0]["layers"][0]["unit"] = "单位：" + unit_sk

            me = DrawController(sub_local_params=method_params, algorithm_input_data=tmp2)
            result_dict = me.execute()
            if result_dict:
                result_dict["value"] = [grid_data.min().values.tolist(), grid_data.max().values.tolist()]
            else:
                result_dict = {"response_code":"0000"}
                result_dict["value"] = [grid_data.min().values.tolist(), grid_data.max().values.tolist()]
            print(json.dumps(result_dict, ensure_ascii=False))
            logging.info(json.dumps(result_dict, ensure_ascii=False))
    elif areaName in ["NORTH"]:
        startLon, endLon, startLat, endLat = [30, 150, 0, 60]
        method_params = {
            "cycle": "",
            "data_output_types": "png",
            "iniPath": "/nfsshare/cdbdata/algorithm/conductor/WMFS/huishang/",
            "data_output_params": [
                {
                    "region_type": "NorthPro",
                    "output_img_type": "png",
                    "output_img_max_width": "930",
                    "layers": [
                        {
                            "draw_regions": ":,:,:,:",
                            "layer_type": "contourMap"
                        }
                    ],
                    "x_values": "",
                    "y_values": ""
                }
            ]
        }
        # 反演得到预报实况数据
        if ext_params.get("drawType") == "SK":
            data_src = pd.read_table(ext_params.get("dataFile"), header=None, encoding='utf-8', sep="\\s+")
            dataAll = np.array(data_src)
            data_file = dataAll[:, 3]
            station_lon_file = dataAll[:, 1]
            station_lat_file = dataAll[:, 2]
            station_id = dataAll[:, 0]

            tmpSatrtTime = ext_params.get("startTime")
            tmpEndTime = ext_params.get("endTime")

            # 加载数据
            station_inter = [val for val in station_id if val in station_all]
            index = [station_id.tolist().index(sta) for sta in station_id.tolist() if sta in station_inter]
            data = data_file[index]
            station_lon = station_lon_file[index]
            station_lat = station_lat_file[index]
            ltm_data = sdu.get_station_ltm_data(ltm_path, time_type, tmpSatrtTime, tmpEndTime, var, station_inter,
                                                "")
            if ext_params.get("element") == "TEMP":
                ltm_data = ltm_data.mean(dim="time", skipna=True, keep_attrs=True)
                skData = data + ltm_data.values * 0.1
                result = txtOutPut("TEMP", output_img_path + "/", output_img_name, index, station_id,
                                   station_lon_file,
                                   station_lat_file,
                                   data_file, skData, ltm_data.values * 0.1)
                grid_data = interp_idw(areaName, skData, station_lon, station_lat, startLon, endLon, startLat,
                                       endLat)
            if ext_params.get("element") == "RAIN":
                tmpdata = ltm_data.mean(dim="time", skipna=True, keep_attrs=True)
                ltm_data = ltm_data.sum(dim="time", skipna=True, keep_attrs=True)
                tmpdata = tmpdata.where(np.isnan(tmpdata), 1)
                ltm_data = ltm_data * tmpdata

                skData = (data * ltm_data.values) / 100 + ltm_data.values
                result = txtOutPut("RAIN", output_img_path + "/", output_img_name, index, station_id,
                                   station_lon_file,
                                   station_lat_file,
                                   data_file, skData, ltm_data.values)
                grid_data = interp_idw(areaName, skData, station_lon, station_lat, startLon, endLon, startLat,
                                       endLat)
            if ext_params.get("element") == "FROST":
                ltm_data = ltm_data.mean(dim="time", skipna=True, keep_attrs=True)
                skData = data + ltm_data.values
                result = txtOutPut("FROST", output_img_path + "/", output_img_name, index, station_id,
                                   station_lon_file,
                                   station_lat_file,
                                   data_file, skData, ltm_data.values)

                grid_data = interp_cressman(areaName, skData, station_lon, station_lat, startLon, endLon, startLat,
                                            endLat)
            tmp1 = {}
            tmp1["outputData"] = grid_data
            tmp2 = [tmp1]

            method_params["iniPath"] = iniPath_sk
            # intervals = getColorValueDef(iniPath_sk).tolist()
            method_params["data_output_params"][0]["layers"][0]["intervals"] = getColorValueDef(iniPath_sk).tolist()
            method_params["data_output_params"][0]["layers"][0]["colors"] = getColorMap(iniPath_sk).tolist()
            method_params["data_output_params"][0]["layers"][0]["legend_labels"] = legend_labels_sk
            if intervals:
                method_params["data_output_params"][0]["layers"][0]["intervals"] = intervals
                legend_labels = [str(int(i)) if i % 1 == 0 else str(i) for i in intervals]
                labels = ['<' + legend_labels[0]]
                for i in range(1, len(legend_labels)):
                    labels.extend([legend_labels[i - 1] + '~F34~*~F~' + legend_labels[i]])
                labels.extend(['>' + legend_labels[-1]])
                method_params["data_output_params"][0]["layers"][0]["legend_labels"] = labels
            if colors:
                method_params["data_output_params"][0]["layers"][0]["colors"] = colors
            method_params["data_output_params"][0]["main_title"] = ext_params.get("mainTitle")
            method_params["data_output_params"][0]["sub_titles"] = ext_params.get("subTitles")

            method_params["data_output_params"][0]["main_title_font"] = "times.ttf"
            method_params["data_output_params"][0]["sub_titles_font"] = "simhei.ttf"
            method_params["data_output_params"][0]["title_color"] = "blue"
            method_params["data_output_params"][0]["main_title_size"] = "65"
            method_params["data_output_params"][0]["sub_titles_size"] = "80"
            method_params["data_output_params"][0]["title_leftshift"] = "100"
            method_params["data_output_params"][0]["title_topshift"] = "80"

            method_params["data_output_params"][0]["output_img_path"] = output_img_path + "/"
            method_params["data_output_params"][0]["output_img_name"] = output_img_name
            method_params["data_output_params"][0]["layers"][0]["unit"] = "单位：" + unit_sk

            me = DrawController(sub_local_params=method_params, algorithm_input_data=tmp2)
            result_dict = me.execute()
            if result_dict:
                result_dict["value"] = [grid_data.min().values.tolist(), grid_data.max().values.tolist()]
            else:
                result_dict = {"response_code":"0000"}
                result_dict["value"] = [grid_data.min().values.tolist(), grid_data.max().values.tolist()]
            print(json.dumps(result_dict, ensure_ascii=False))
            logging.info(json.dumps(result_dict, ensure_ascii=False))
    else:  # 省级范围
        configPath = PathConfig.CPCS_ROOT_PATH + 'com/nriet/config/regionConfigFy.json'
        # 读取配置文件
        with open(configPath, "r", encoding='UTF-8') as f:
            datastr = f.read()
        data_config = json.loads(datastr)
        # 获取传参区域的参数
        areaConfig = data_config.get(areaName)
        areaRegions = areaConfig.get('regions')
        startLon, endLon, startLat, endLat = [float(i) for i in areaRegions.split(',')]

        # txt数据的插值处理得到距平格点数据
        if ext_params.get("drawType") == "JP":
            data_src = pd.read_table(ext_params.get("dataFile"), header=None, encoding='utf-8', sep=" ")
            dataAll = np.array(data_src)
            data = dataAll[:, 3]
            station_lon = dataAll[:, 1]
            station_lat = dataAll[:, 2]

            grid_data = interp_ref(areaName, data, station_lon, station_lat, startLon, endLon, startLat, endLat)

            page_params["inputData"] = grid_data
            page_params["intervals"] = intervals_jp_prov
            page_params["colors"] = colors_jp
            if intervals:
                page_params["intervals"] = intervals
            if colors:
                page_params["colors"] = colors
            page_params["unit"] = unit_jp

            me = DrawProvinceController(sub_local_params=page_params)
            result_dict = me.execute()

        # 反演得到预报实况数据
        if ext_params.get("drawType") == "SK":
            data_src = pd.read_table(ext_params.get("dataFile"), header=None, encoding='utf-8', sep=" ")
            dataAll = np.array(data_src)
            data_file = dataAll[:, 3]
            station_lon_file = dataAll[:, 1]
            station_lat_file = dataAll[:, 2]
            station_id = dataAll[:, 0]
            data = data_file
            station_lon = station_lon_file
            station_lat = station_lat_file
            # 封装站点信息数组
            locs = ['lat', 'lon']
            latlon_list = []
            for i in range(len(station_lat)):
                latlon_list.append([station_lat[i],station_lon[i]])
            station_list = [str(int(staid)) for staid in station_id]
            stationInfoData = xr.DataArray(np.asarray(latlon_list, dtype=np.float32), coords=[station_list, locs],
                                           dims=['station', 'space'])

            if time_type.upper() == "SEASON":
                tmpSatrtTime = ext_params.get("startTime")
                tmpEndTime = ext_params.get("endTime")
                sea = ["04", "01", "02", "03"]
                sindex = sea.index(tmpSatrtTime[4:])
                eindex = sea.index(tmpEndTime[4:])
                smon = ["12", "03", "06", "09"]
                emon = ["02", "05", "08", "11"]
                tmpSatrtTime = str(int(tmpSatrtTime[:4]) - 1) + smon[sindex] if sindex == 0 else tmpSatrtTime[:4] + \
                                                                                                 smon[sindex]
                tmpEndTime = str(int(tmpEndTime[:4])) + emon[eindex] if eindex == 0 else tmpEndTime[:4] + \
                                                                                         emon[eindex]
                time_type = "mon"
            else:
                tmpSatrtTime = ext_params.get("startTime")
                tmpEndTime = ext_params.get("endTime")

            # 加载数据
            # station_inter = [val for val in station_id if val in station_all]
            # index = [station_id.tolist().index(sta) for sta in station_id.tolist() if sta in station_inter]
            # data = data_file[index]
            # station_lon = station_lon_file[index]
            # station_lat = station_lat_file[index]
            # ltm_data = sdu.get_station_ltm_data(ltm_path, time_type, tmpSatrtTime, tmpEndTime, var, station_inter, "")
            if ext_params.get("element") == "TEMP":
                # 组装查询站点数据的参数
                moni_params = {}
                moni_params["timeType"] = time_type
                moni_params["timeRanges"] = [int(tmpSatrtTime), int(tmpEndTime)]
                moni_params["elements"] = 'TEMP'
                moni_params["dataSource"] = "CSOD"
                moni_params["areaCode"] = "33"
                moni_params["stationType"] = "1"
                moni_params["eleType"] = "LTM"
                moni_params["statisticType"] = "AVG"
                moni_params["ltm"] = ltm
                alg_input_data = [{"outputData": stationInfoData}]
                sdfg = StationDataForGbase(moni_params, alg_input_data)
                sdfg.execute()
                ltm_data = sdfg.output_data["outputData"][0]
                ltm_data = ltm_data.mean(dim="time", skipna=True, keep_attrs=True)
                skData = data + ltm_data.values
                result = txtOutPut("TEMP", output_img_path + "/", output_img_name, list(range(len(station_id))),
                                   station_id, station_lon_file, station_lat_file,
                                   data_file, skData, ltm_data.values)
            if ext_params.get("element") == "RAIN":
                # 组装查询站点数据的参数
                moni_params = {}
                moni_params["timeType"] = time_type
                moni_params["timeRanges"] = [int(tmpSatrtTime), int(tmpEndTime)]
                moni_params["elements"] = 'RAIN'
                moni_params["dataSource"] = "CSOD"
                moni_params["areaCode"] = "33"
                moni_params["stationType"] = "1"
                moni_params["eleType"] = "LTM"
                moni_params["statisticType"] = "SUM"
                moni_params["ltm"] = ltm
                alg_input_data = [{"outputData": stationInfoData}]
                sdfg = StationDataForGbase(moni_params, alg_input_data)
                sdfg.execute()
                ltm_data = sdfg.output_data["outputData"][0]
                tmpdata = ltm_data.mean(dim="time", skipna=True, keep_attrs=True)
                ltm_data = ltm_data.sum(dim="time", skipna=True, keep_attrs=True)
                tmpdata = tmpdata.where(np.isnan(tmpdata), 1)
                ltm_data = ltm_data * tmpdata

                skData = (data * ltm_data.values) / 100 + ltm_data.values
                result = txtOutPut("RAIN", output_img_path + "/", output_img_name, list(range(len(station_id))),
                                   station_id, station_lon_file, station_lat_file,
                                   data_file, skData, ltm_data.values)

            grid_data = interp_ref(areaName, skData, station_lon, station_lat, startLon, endLon, startLat, endLat)

            page_params["inputData"] = grid_data
            page_params["intervals"] = intervals_sk
            page_params["colors"] = colors_sk
            if intervals:
                page_params["intervals"] = intervals
            if colors:
                page_params["colors"] = colors
            page_params["unit"] = unit_sk

            me = DrawProvinceController(sub_local_params=page_params)
            result_dict = me.execute()
            if result_dict:
                result_dict["value"] = [grid_data.min().values.tolist(), grid_data.max().values.tolist()]
            else:
                result_dict = {"response_code":"0000"}
                result_dict["value"] = [grid_data.min().values.tolist(), grid_data.max().values.tolist()]
            print(json.dumps(result_dict, ensure_ascii=False))
            # logging.info(json.dumps(result_dict, ensure_ascii=False))
