from matplotlib import pyplot as plt
import matplotlib.dates as mdates
import datetime
from matplotlib.ticker import AutoMinorLocator, MultipleLocator
import numpy as np
import math
import os, sys
from matplotlib.font_manager import FontProperties

sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))))
from com.nriet.config.PathConfig import CPCS_ROOT_PATH
from intervals import IntInterval
import PIL.Image as Image
from com.nriet.algorithm.common.drawComponent.util.ChartAxisTimeUtils import get_day_month, get_day_month_year, \
    get_each_month, get_individual_years_indexes, get_month_abbr, get_each_day, get_five_list, get_month_year, \
    get_seasons_list, get_ten_list
from com.nriet.utils.DateUtils import get_time_list

# 设置全局默认字体，字号为20像素
plt.rcParams["font.sans-serif"] = ["Times New Roman"]
plt.rcParams["font.size"] = 20


class DrawChartController():
    def __init__(self, sub_local_params: dict, algorithm_input_data):
        self.request_dict = sub_local_params
        # 主标题
        self.mainTitle = sub_local_params.get("main_title")
        # 副标题，字符串列表（最多两行）
        self.subTitles = sub_local_params.get("sub_titles")
        # 输出图片路径
        self.output_img_path = sub_local_params.get("output_img_path")
        # 输出图片名称（默认png）
        self.output_img_name = sub_local_params.get("output_img_name")
        # 单位标注
        self.unit = sub_local_params.get("unit")
        # 图层，字典列表
        self.layers = sub_local_params.get("layers")
        # 是否叠加logo
        self.islogo = sub_local_params.get("islogo", "True")
        # 时间尺度
        self.timeType = sub_local_params.get("timeType")
        # y轴上限
        self.yMax = sub_local_params.get("yMax")
        # y轴下限
        self.yMin = sub_local_params.get("yMin")
        # 监测时间范围处理
        self.timeRanges = sub_local_params.get("timeRanges")
        # 箱线图范围处理
        self.boxPeriod = sub_local_params.get("boxPeriod")
        # 是否添加0线
        self.isZero = sub_local_params.get("isZero", "False")
        # 是否使用英文的时间轴
        self.isEnXaxis = sub_local_params.get("isEnXaxis", "False")
        self.algorithm_input_data = algorithm_input_data

    def execute(self):

        mainTitle = self.mainTitle
        subTitles = self.subTitles
        inputData = self.algorithm_input_data
        layers = self.layers
        islogo = self.islogo
        isZero = self.isZero
        isEnXaxis = self.isEnXaxis
        unit = self.unit
        output_img_path = self.output_img_path
        output_img_name = self.output_img_name
        timeType = self.timeType
        startTime = self.timeRanges[0]
        endTime = self.timeRanges[1]
        yMax = self.yMax
        yMin = self.yMin
        bar_legend = False

        # 数据缺测值，特殊值处理
        for indexitem, item in enumerate(inputData):
            if isinstance(item[0], list):
                for index, i in enumerate(item):
                    inputData[indexitem][index] = [np.nan if a in ["999999", "nan", "", 999999.] else float(a) for a in
                                                   inputData[indexitem][index]]
            else:
                inputData[indexitem] = [np.nan if a in ["999999", "nan", "", 999999., "∞", "-∞"] else float(a) for a in
                                        inputData[indexitem]]

        # 设置微软雅黑字体
        fontPath = CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC"
        font = FontProperties(fname=fontPath)
        # 设置fig像素（默认为930x520像素）
        width = 930 * 2
        height = 520 * 2
        fig = plt.figure(figsize=(width / 100, height / 100))
        # 设置图片位置（仅支持单张图形绘制）
        ax = fig.add_subplot(111)
        ax.set_position([0.1, 0.12, 0.85, 0.71])

        # 求取所有绘图序列的最大最小，为chart图上下线准备
        max_series = []
        min_series = []
        for item in inputData:
            if isinstance(item[0], list):
                for i in item:
                    item_no_nan = [a for a in i if not np.isnan(a)]
                    if len(item_no_nan) > 0:
                        max_series.append(max(item_no_nan))
                        min_series.append(min(item_no_nan))
            else:
                i_no_nan = [a for a in item if not np.isnan(a)]
                if len(i_no_nan) > 0:
                    max_series.append(max(i_no_nan))
                    min_series.append(min(i_no_nan))
        max_series = max(max_series)
        min_series = min(min_series)

        # y轴的主副刻度间隔
        lat_axis_major_space = match_interval(max_series - min_series,
                                              [0, 1, 3, 5, 10, 50, 100, 500],
                                              [0.2, 0.5, 1, 2, 5, 10, 20],
                                              None)
        lat_axis_minor_space = match_interval(max_series - min_series,
                                              [0, 1, 3, 5, 10, 50, 100, 500],
                                              [0.1, 0.1, 0.5, 1, 1, 2, 5],
                                              None)
        ax.yaxis.set_major_locator(MultipleLocator(lat_axis_major_space))
        ax.yaxis.set_minor_locator(AutoMinorLocator(lat_axis_major_space / lat_axis_minor_space))

        # 设置y轴的上下限
        max_series_y = float(max_series + lat_axis_major_space)
        min_series_y = float(min_series - lat_axis_major_space)
        if yMax:
            max_series_y = float(yMax)
        if yMin:
            min_series_y = float(yMin)
        lat1, lat2 = ax.set_ylim(min_series_y, max_series_y)

        # x轴的主副刻度间隔
        x_axis_real = get_time_list([int(startTime), int(endTime)], timeType)
        x_axis = np.arange(1, len(x_axis_real) + 1)
        x_axis_label = np.arange(len(x_axis_real) + 2)

        lon1, lon2 = ax.set_xlim(x_axis_label[0], x_axis_label[-1])

        xticks_major = []
        xticklabels_major = []
        xticks_minor = []
        xticks_major, xticklabels_major, xticks_minor = get_xticks(startTime, endTime, timeType,isEnXaxis, xticks_major,
                                                                   xticklabels_major, xticks_minor)

        if self.boxPeriod:
            startTime_box = self.boxPeriod[0]
            endTime_box = self.boxPeriod[1]
            boxPeriod_list = get_time_list([int(startTime_box), int(endTime_box)], timeType)
            box_position = [x_axis_real.index(i) + 1 for i in boxPeriod_list]

        legends = []
        legendsName = []
        if isZero == "True":
            ax.plot(x_axis_label, np.full(len(x_axis_label), 0.0), color="black",
                    linewidth=1.0,
                    linestyle="-")
        for i, layer in enumerate(layers):
            if layer.get('layer_type') == "bar":
                input_data = inputData[i]
                if layer.get('isColorDivide', 'False') == "True":
                    bar_legend = True
                    barColor = layer.get('barColor', '#FF0000,#0000FF')
                    upColor = barColor.split(",")[0]
                    downColor = barColor.split(",")[1]
                    if layer.get('isBarFill', 'True') == "True":
                        bar = ax.bar(x_axis, input_data, color=np.where(np.array(input_data) > 0, upColor, downColor))
                    else:
                        bar = ax.bar(x_axis, input_data, color='white',
                                     edgecolor=np.where(np.array(input_data) > 0, upColor, downColor))
                else:
                    if layer.get('isBarFill', 'True') == "True":
                        bar = ax.bar(x_axis, input_data, color=layer.get('barColor', 'red'))
                    else:
                        bar = ax.bar(x_axis, input_data, color='white', edgecolor=layer.get('barColor', 'red'))
                legends.append(bar)
                legendsName.append(layer.get("labelName", "指数"))
            if layer.get('layer_type') == "line":
                input_data = inputData[i]
                line, = ax.plot(x_axis, input_data, color=layer.get('lineColor', 'black'),
                                linewidth=float(layer.get('lineWidth', 1.0)),
                                linestyle=layer.get('lineStyle', '-'))
                legends.append(line)
                legendsName.append(layer.get("labelName", "指数"))
            if layer.get('layer_type') == "fill_between":
                input_data1 = inputData[i][0]
                input_data2 = inputData[i][1]
                fill_between = ax.fill_between(x_axis, input_data1, input_data2,
                                               alpha=float(layer.get("fillAlpha", "0.5")), linewidth=0,
                                               color=layer.get('fillColor', 'grey'))
                legends.append(fill_between)
                legendsName.append(layer.get("labelName", "指数"))
            if layer.get('layer_type') == "box":
                input_data = np.array(inputData[i]).T
                box = ax.boxplot(input_data, positions=box_position, widths=0.8, patch_artist=True,
                                 showmeans=False,
                                 showfliers=False, medianprops={"color": "white", "linewidth": 0.5},
                                 boxprops={"facecolor": layer.get("fillColor", "C0"),
                                           "edgecolor": layer.get("fillColor", "C0"), "linewidth": 1.0,
                                           "alpha": float(layer.get("fillAlpha", "1.0"))},
                                 whiskerprops={"color": layer.get("fillColor", "C0"), "linewidth": 1.0},
                                 capprops={"color": layer.get("fillColor", "C0"), "linewidth": 1.0})
                legends.append(box["boxes"][0])
                legendsName.append(layer.get("labelName", "指数"))

        ax.set_xticks(xticks_major)
        ax.set_xticklabels(xticklabels_major)
        ax.set_xticks(xticks_minor, minor=True)
        ax.legend(legends, legendsName, loc='upper left', prop=font, ncol=10, frameon=False)

        # 设置经纬度label的字体
        for xlabel in ax.get_xticklabels():
            xlabel.set_fontname('Times New Roman')
        for ylabel in ax.get_yticklabels():
            ylabel.set_fontname('Times New Roman')

        # 设置横纵坐标刻度的长度和粗细
        ax.tick_params(which='major', labelsize=36, length=10, width=1.0)
        ax.tick_params(which='minor', labelsize=36, length=6, width=1.0)

        lines = plt.gca()
        lines.spines['top'].set_linewidth(1)
        lines.spines['bottom'].set_linewidth(1)
        lines.spines['left'].set_linewidth(1)
        lines.spines['right'].set_linewidth(1)

        if unit:
            ax.set_ylabel(unit, fontproperties=font, fontsize=30)

        # 标题
        title = mainTitle
        subTitle = ""
        if subTitles:
            for i in range(len(subTitles)):
                subTitle = subTitle + subTitles[i] + "\n"

            if len(subTitles) == 1:  # 一行副标题位置设置
                plt.title(title, fontproperties=font, fontsize=40, y=1.08)
                plt.suptitle(subTitle, fontproperties=font, fontsize=30, y=0.88, x=0.523)
            else:  # 两行副标题位置设置
                plt.title(title, fontproperties=font, fontsize=40, y=1.15)
                plt.suptitle(subTitle, fontproperties=font, fontsize=30, y=0.93, x=0.523)
        else:
            plt.title(title, fontproperties=font, fontsize=40, y=1.04)
        plt.savefig(output_img_path + output_img_name + '.png')
        im = Image.open(output_img_path + output_img_name + '.png', "r")
        # 正红负蓝图例图片叠加
        if bar_legend:
            img_legend = Image.open(CPCS_ROOT_PATH + 'com/nriet/algorithm/common/drawComponent/imgFiles/legend.png')
            for i in range(img_legend.size[0]):
                for j in range(img_legend.size[1]):
                    data = img_legend.getpixel((i, j))
                    if data == (250, 3, 3, 255):
                        img_legend.putpixel((i, j), hex_to_rgb(upColor))
                    if data == (13, 12, 229, 255):
                        img_legend.putpixel((i, j), hex_to_rgb(downColor))
            im.paste(img_legend, (210, 205, 210 + img_legend.size[0], 205 + img_legend.size[1]), img_legend)
        # logo叠加
        if islogo == "True":
            img1 = Image.open(CPCS_ROOT_PATH + 'com/nriet/algorithm/common/drawComponent/logoFiles/NCC.png')
            img1 = img1.resize((int(img1.size[0] * 2.0),
                                int(img1.size[1] * 2.0)),
                               Image.ANTIALIAS)
            im.paste(img1, (80, 40, 80 + img1.size[0], 40 + img1.size[1]), img1)
            img2 = Image.open(CPCS_ROOT_PATH + 'com/nriet/algorithm/common/drawComponent/logoFiles/BCC.png')
            img2 = img2.resize((int(img2.size[0] * 2.0),
                                int(img2.size[1] * 2.0)),
                               Image.ANTIALIAS)
            im.paste(img2, (100 + img1.size[0], 40, 100 + img1.size[0] + img2.size[0], 40 + img2.size[1]), img2)
            im.save(output_img_path + output_img_name + '.png')


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
            data_range = IntInterval.closed_open(range_values[i], range_values[i + 1])
            list_interval.append(data_range)
    match_value = default_value
    for i in range(len(list_interval)):
        if query_value in list_interval[i]:
            match_value = match_values[i]
    return match_value


def get_xticks(startTime, endTime, timeType, isEnXaxis, xticks_major, xticklabels_major, xticks_minor):
    if timeType == "day":
        day_list = get_each_day(str(startTime), str(endTime))
        times = len(day_list)
        if times < 8:
            labels = day_list
            xticks_major = np.arange(1, len(day_list) + 1)
            individual_years_indexes = get_individual_years_indexes(labels)
            xticklabels_major = [get_day_month(day) for day in labels]  # MM/DD
            for individual_years_index in individual_years_indexes:
                xticklabels_major[individual_years_index] = get_day_month_year(
                    labels[individual_years_index])  # 每首次出现的年日期，都必须得标年
        elif times >= 8 and times < 16:
            labels = [day for day in day_list if day_list.index(day) % 2 == 0]  # 从第一天开始，隔两天
            xticks_major = [day_list.index(i) + 1 for i in labels]
            individual_years_indexes = get_individual_years_indexes(labels)
            xticklabels_major = [get_day_month(day) for day in labels]  # MM/DD
            for individual_years_index in individual_years_indexes:
                xticklabels_major[individual_years_index] = get_day_month_year(
                    labels[individual_years_index])  # 每首次出现的年日期，都必须得标年
            xticks_minor = np.arange(1, len(day_list) + 1)  # 次数副刻度间隔为1，此时主副刻度可重合！
        elif times >= 16 and times < 40:
            labels = [day for day in day_list if str(day)[-2:] in ['01', '06', '11', '16', '21',
                                                                   '26']]  # 日期在 '01','06','11','16','21','26'
            xticks_major = [day_list.index(i) + 1 for i in labels]
            individual_years_indexes = get_individual_years_indexes(labels)
            xticklabels_major = [get_day_month(day) for day in labels]  # MM/DD
            for individual_years_index in individual_years_indexes:
                xticklabels_major[individual_years_index] = get_day_month_year(
                    labels[individual_years_index])  # 每首次出现的年日期，都必须得标年
            xticks_minor = np.arange(1, len(day_list) + 1)  # 次数副刻度间隔为1，此时主副刻度可重合！
        elif times >= 40 and times < 90:
            labels = [day for day in day_list if str(day)[-2:] in ['01', '11', '21']]  # 日期在 '01','11','21'
            xticks_major = [day_list.index(i) + 1 for i in labels]
            individual_years_indexes = get_individual_years_indexes(labels)
            xticklabels_major = [get_day_month(day) for day in labels]  # MM/DD
            for individual_years_index in individual_years_indexes:
                xticklabels_major[individual_years_index] = get_day_month_year(
                    labels[individual_years_index])  # 每首次出现的年日期，都必须得标年
            sub_labels = [day for day in day_list if
                          str(day)[-2:] in ['06', '16', '26']]  # 日期在 '06','16','26'
            xticks_minor = [day_list.index(i) + 1 for i in sub_labels]
        elif times >= 90 and times < 125:
            labels = [day for day in day_list if str(day)[-2:] in ['01', '16']]  # 日期在 '01','16'
            xticks_major = [day_list.index(i) + 1 for i in labels]
            individual_years_indexes = get_individual_years_indexes(labels)
            xticklabels_major = [get_day_month(day) for day in labels]  # MM/DD
            for individual_years_index in individual_years_indexes:
                xticklabels_major[individual_years_index] = get_day_month_year(
                    labels[individual_years_index])  # 每首次出现的年日期，都必须得标年
            sub_labels = [day for day in day_list if
                          str(day)[-2:] in ['06', '11', '16', '21', '26']]  # 日期在 '06', '11','16', '21','26'
            xticks_minor = [day_list.index(i) + 1 for i in sub_labels]
        elif times >= 125 and times < 240:
            labels = [day for day in day_list if str(day)[-2:] == '01']  # 找到 month_list中的01日
            xticks_major = [day_list.index(i) + 1 for i in labels]
            individual_years_indexes = get_individual_years_indexes(labels)
            xticklabels_major = [get_day_month(day) for day in labels]  # 此时标记为 MM
            for individual_years_index in individual_years_indexes:
                xticklabels_major[individual_years_index] = get_day_month_year(
                    labels[individual_years_index])  # 每首次出现的年日期，都必须得标年
            sub_labels = [day for day in day_list if str(day)[-2:] == '16']  # 日期在 '16'
            xticks_minor = [day_list.index(i) + 1 for i in sub_labels]
        else:
            # 获取日期间的月份
            labels = [day for day in day_list if str(day)[-2:] == '01']
            xticks_major = [day_list.index(i) + 1 for i in labels]
            xticklabels_major = [get_month_abbr(str(day)[4:6])[0:2] for day in labels]
            individual_years_indexes = get_individual_years_indexes(labels)
            for individual_years_index in individual_years_indexes:
                xticklabels_major[individual_years_index] = get_month_year(
                    str(labels[individual_years_index])[:6])  # 每首次出现的年日期，标记为MMYYYY

    if timeType == "five":
        five_list = get_five_list(str(startTime), str(endTime))
        times = len(five_list)  # 时间类型的维度的个数

        #  需要显示的候
        # 1个月
        if times <= 6:
            five_exist_labels = ['01', '02', '03', '04', '05', '06']
        # 3个月
        elif times <= 18:
            five_exist_labels = ['01', '03', '05']
        # 6个月
        elif times <= 36:
            five_exist_labels = ['01', '04']
        # 6个月以上
        else:
            five_exist_labels = ['01']

        #  需要显示的月
        # 1年
        if times <= 72:
            mon_exist_labels = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
        # 1年半
        elif times <= 108:
            mon_exist_labels = ['01', '03', '05', '07', '09', '11']
        # 3年
        elif times <= 216:
            mon_exist_labels = ['01', '04', '07', '10']
        # 5年
        elif times <= 324:
            mon_exist_labels = ['01', '07']
        else:
            mon_exist_labels = ['01']

        labels = []
        for mon_exist in mon_exist_labels:
            for five_exist in five_exist_labels:
                labels.append(mon_exist + five_exist)

        if times <= 36:
            five_labels = [five for five in five_list if five[-4:] in labels]

            # 统计需要显示的首次出现的年的index
            year_list = []
            for five in five_labels:
                year_list.append(five[0:4])
            individual_years = list(set(year_list))
            individual_years_indexes = []
            for year in individual_years:
                for five in five_labels:
                    if year in five:
                        individual_years_indexes.append(five_list.index(five))
                        break

            # 统计需要显示的首次出现的月的index
            yyyymm_list = []
            for five in five_labels:
                yyyymm_list.append(five[0:6])
            individual_yyyymm = list(set(yyyymm_list))
            individual_yyyymm_indexes = []
            for yyyymm in individual_yyyymm:
                for five in five_labels:
                    if yyyymm in five:
                        individual_yyyymm_indexes.append(five_list.index(five))
                        break

            xticks_major = []
            xticklabels_major = []
            for label in five_list:
                index = five_list.index(label)
                if label in five_labels:
                    if index in individual_yyyymm_indexes:
                        if index in individual_years_indexes:
                            label = label[4:6] + '/' + label[-2:] + "\n" + label[0:4]
                        else:
                            label = label[4:6] + '/' + label[-2:]
                    else:
                        label = label[-2:]
                    xticklabels_major.append(label)
                    xticks_major.append(index + 1)

            xticks_minor = [five_list.index(i) + 1 for i in five_list]

        else:
            five_labels = [five for five in five_list if five[-4:] in labels]

            # 统计需要显示的首次出现的年的index
            year_list = []
            for five in five_labels:
                year_list.append(five[0:4])
            individual_years = list(set(year_list))
            individual_years_indexes = []
            for year in individual_years:
                for five in five_labels:
                    if year in five:
                        individual_years_indexes.append(five_list.index(five))
                        break

            xticks_major = []
            xticklabels_major = []
            for label in five_list:
                index = five_list.index(label)
                if label in five_labels:
                    #  首次出现的年要标明
                    if index in individual_years_indexes:
                        label = label[4:6] + '/' + label[-2:] + "\n" + label[0:4]
                    else:
                        label = label[4:6] + '/' + label[-2:]
                    xticklabels_major.append(label)
                    xticks_major.append(index + 1)

            xticks_minor = [five_list.index(i) + 1 for i in five_list]

    if timeType == "ten":
        ten_list = get_ten_list(str(startTime), str(endTime))
        times = len(ten_list)  # 时间类型的维度的个数

        if times <= 6:
            ten_exist_labels = ['01', '02', '03']
        else:
            ten_exist_labels = ['01']

        if times <= 18:
            mon_exist_labels = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
        elif times <= 36:
            mon_exist_labels = ['01', '03', '05', '07', '09', '11']
        elif times <= 108:
            mon_exist_labels = ['01', '04', '07', '10']
        elif times <= 180:
            mon_exist_labels = ['01', '07']
        else:
            mon_exist_labels = ['01']

        labels = []
        for mon_exist in mon_exist_labels:
            for ten_exist in ten_exist_labels:
                labels.append(mon_exist + ten_exist)

        if times <= 6:
            ten_labels = [ten for ten in ten_list if ten[-4:] in labels]

            # 统计需要显示的首次出现的年的index
            year_list = []
            for ten in ten_labels:
                year_list.append(ten[0:4])
            individual_years = list(set(year_list))
            individual_years_indexes = []
            for year in individual_years:
                for ten in ten_labels:
                    if year in ten:
                        individual_years_indexes.append(ten_list.index(ten))
                        break

            # 统计需要显示的首次出现的月的index
            yyyymm_list = []
            for ten in ten_labels:
                yyyymm_list.append(ten[0:6])
            individual_yyyymm = list(set(yyyymm_list))
            individual_yyyymm_indexes = []
            for yyyymm in individual_yyyymm:
                for ten in ten_labels:
                    if yyyymm in ten:
                        individual_yyyymm_indexes.append(ten_list.index(ten))
                        break

            xticks_major = []
            xticklabels_major = []
            for label in ten_list:
                index = ten_list.index(label)
                if label in ten_labels:
                    if index in individual_yyyymm_indexes:
                        if index in individual_years_indexes:
                            label = label[4:6] + '/' + label[-2:] + "\n" + label[0:4]
                        else:
                            label = label[4:6] + '/' + label[-2:]
                    else:
                        label = label[-2:]
                    xticklabels_major.append(label)
                    xticks_major.append(index + 1)

            xticks_minor = [ten_list.index(i) + 1 for i in ten_list]

        else:
            ten_labels = [ten for ten in ten_list if ten[-4:] in labels]

            # 统计需要显示的首次出现的年的index
            year_list = []
            for ten in ten_labels:
                year_list.append(ten[0:4])
            individual_years = list(set(year_list))
            individual_years_indexes = []
            for year in individual_years:
                for ten in ten_labels:
                    if year in ten:
                        individual_years_indexes.append(ten_list.index(ten))
                        break

            xticks_major = []
            xticklabels_major = []
            for label in ten_list:
                index = ten_list.index(label)
                if label in ten_labels:
                    #  首次出现的年要标明
                    if index in individual_years_indexes:
                        label = label[4:6] + '/' + label[-2:] + "\n" + label[0:4]
                    else:
                        label = label[4:6] + '/' + label[-2:]
                    xticklabels_major.append(label)
                    xticks_major.append(index + 1)

            xticks_minor = [ten_list.index(i) + 1 for i in ten_list]

    if timeType == "mon":
        # 获取这段时间内的所有月份列表
        month_list = get_each_month(str(startTime), str(endTime))
        times = len(month_list)
        if (times < 8):
            labels = month_list
            xticks_major = np.arange(1, len(month_list) + 1)
            individual_years_indexes = get_individual_years_indexes(labels)
            xticklabels_major = [get_month_abbr(str(x_value)[-2:])[0:2] for x_value in labels]  # 先变成MM
            for individual_years_index in individual_years_indexes:
                xticklabels_major[individual_years_index] = get_month_abbr(
                    str(labels[individual_years_index])[-2:])[0:2] + "\n" + str(labels[individual_years_index])[
                                                                            :4]  # 年首标MMYYYY

        elif times >= 8 and times < 16:
            labels = [month for month in month_list if month % 2 != 0]  # 要奇数月！
            xticks_major = [month_list.index(i) + 1 for i in labels]

            individual_years_indexes = get_individual_years_indexes(labels)
            xticklabels_major = [get_month_abbr(str(x_value)[-2:])[0:2] for x_value in labels]  # 先变成MM
            for individual_years_index in individual_years_indexes:
                xticklabels_major[individual_years_index] = get_month_abbr(
                    str(labels[individual_years_index])[-2:])[0:2] + "\n" + str(labels[individual_years_index])[
                                                                            :4]  # 年首标MMYYYY

            xticks_minor = np.arange(1, len(month_list) + 1)  # 次数副刻度间隔为1，此时主副刻度可重合！

        elif times >= 16 and times < 25:
            labels = [month for month in month_list if
                      str(month)[-2:] in ['01', '04', '07', '10']]  # 找到 month_list 中的1,4,7,10月
            xticks_major = [month_list.index(i) + 1 for i in labels]

            individual_years_indexes = get_individual_years_indexes(labels)
            xticklabels_major = [get_month_abbr(str(x_value)[-2:])[0:2] for x_value in labels]  # 先变成MM
            for individual_years_index in individual_years_indexes:
                xticklabels_major[individual_years_index] = get_month_abbr(
                    str(labels[individual_years_index])[-2:])[0:2] + "\n" + str(labels[individual_years_index])[
                                                                            :4]  # 年首标MMYYYY

            xticks_minor = np.arange(1, len(month_list) + 1)  # 次数副刻度间隔为1，此时主副刻度可重合！

        elif times >= 25 and times < 48:
            labels = [month for month in month_list if
                      str(month)[-2:] in ['01', '07']]  # 找到 month_list 中的1,7月
            xticks_major = [month_list.index(i) + 1 for i in labels]

            individual_years_indexes = get_individual_years_indexes(labels)
            xticklabels_major = [get_month_abbr(str(x_value)[-2:])[0:2] for x_value in labels]  # 先变成MM
            for individual_years_index in individual_years_indexes:
                xticklabels_major[individual_years_index] = get_month_abbr(
                    str(labels[individual_years_index])[-2:])[0:2] + "\n" + str(labels[individual_years_index])[
                                                                            :4]  # 年首标MMYYYY

            xticks_minor = np.arange(1, len(month_list) + 1)  # 次数副刻度间隔为1，此时主副刻度可重合！

        elif times >= 48:
            labels = [month for month in month_list if str(month)[-2:] == '01']  # 找到 month_list中的1月
            xticks_major = [month_list.index(i) + 1 for i in labels]

            xticklabels_major = [str(x_value)[:4] for x_value in labels]  # 全部标年YYYY

            sub_labels = [month for month in month_list if
                          str(month)[-2:] in ['04', '07', '10']]  # 次数副刻度间隔为1，此时主副刻度可重合！
            xticks_minor = [month_list.index(i) + 1 for i in sub_labels]

        if isEnXaxis=="True":
            monthName = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
            for index,item in enumerate(xticklabels_major):
                xticklabels_major[index] = monthName[int(item[:2])-1]+item[2:]

    if timeType == "season":
        season_list = get_seasons_list(str(startTime), str(endTime))
        times = len(season_list)
        if times <= 12:
            values = [int(x_value) for x_value in season_list]
            labels = [
                x_value[:4] + x_value[4:].replace("01", "SPR").replace("02", "SUM").replace("03", "AUT").replace("04",
                                                                                                                 "WIN") if x_value[
                                                                                                                           4:] == "04" else x_value[
                                                                                                                                            4:].replace(
                    "01", "SPR").replace("02", "SUM").replace("03", "AUT").replace("04", "WIN") for x_value in
                season_list]
        elif times <= 24:
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
        else:
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

    if timeType == "year":
        year_list = list(range(int(startTime), int(endTime) + 1))
        times = len(year_list)  # 时间类型的维度的个数
        x_axis_space = match_interval(times, [0, 8, 16, 40, 80, 9999999], [1, 2, 5, 10, (times % 80 + 1) * 10],
                                      None)
        if times < 8:
            labels = list(range(startTime, endTime + 1, x_axis_space))
            xticks_major = np.arange(1, len(year_list) + 1)
            xticklabels_major = [str(item) for item in labels]
        elif times >= 8 and times < 16:
            labels = list(range(startTime, endTime + 1, x_axis_space))
            xticks_major = [year_list.index(i) + 1 for i in labels]
            xticklabels_major = [str(item) for item in labels]
            xticks_minor = np.arange(1, len(year_list) + 1)
        elif times >= 16 and times < 40:
            labels = [year for year in year_list if year % x_axis_space == 0]  # 去能被间隔整除的年
            xticks_major = [year_list.index(i) + 1 for i in labels]
            xticklabels_major = [str(item) for item in labels]
            xticks_minor = np.arange(1, len(year_list) + 1)
        elif times >= 40:
            labels = [year for year in year_list if year % x_axis_space == 0]  # 去能被间隔整除的年
            xticks_major = [year_list.index(i) + 1 for i in labels]
            xticklabels_major = [str(item) for item in labels]
            xticks_minor = np.arange(1, len(year_list) + 1)

    return xticks_major, xticklabels_major, xticks_minor


# 根据formatter格式化时间，返回datetime
def strToDate(date, formatter):
    return datetime.datetime.strptime(date, formatter)


# 获取时间戳
def getTimeStamp():
    return int(round(datetime.datetime.now().timestamp() * 1000))


# 日期自增
def time_increase(begin_time, days):
    date = datetime.datetime.fromtimestamp(begin_time.timestamp())
    return (date + datetime.timedelta(days=days)).strftime("%Y-%m-%d")

def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3)) + (255,)

if __name__ == '__main__':
    # page_params = ast.literal_eval(sys.argv[1])

    algorithm_input_data = []
    y_series = [0.75, 1.02, 1.24, 1.09, 0.89, 0.38, 0.19, -0.21, -0.33, 0.15, 0.85, 1.34, 1.06, 0.58, 0.32, 0.84, 1.28,
                1.23, 1.13, 0.91, 0.8, 1.21, 1.28, 1.24, 1.08, 0.29, -0.04, -0.1, 0.1, 0.15, 0.26, 0.45, 0.66, 0.27,
                0.1, 0.43, 0.31, -0.04, -0.16, -0.47, -0.45, -0.51, -0.7, -0.46, -0.49, 999999., 999999., 999999.,
                999999.,
                999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999.,
                999999., 999999.,
                999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999.,
                999999., 999999.,
                999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999.,
                999999., 999999.,
                999999., 999999.]
    y_ltm = [-0.02, 0.12, 0.29, 0.31, 0.26, 0.02, -0.08, -0.31, -0.51, -0.45, -0.32, -0.12, -0.2, -0.46, -0.57, 0.07,
             0.5, 0.46, 0.28, 0.03, -0.09, 0.02, 0.06, -0.12, -0.06, -0.34, -0.46, -0.54, -0.32, -0.32, 0.04, 0.82,
             1.25, 1.01, 0.68, 0.7, 0.54, 0.36, 0.24, -0.14, -0.05, 0.19, 0.15, 0.14, 0.1, 0.17, -0.06, 0.01, -0.09,
             -0.18, -0.23, -0.07, -0.57, -0.58, -0.54, -0.32, -0.21, 0.09, 0, -0.31, -0.26, -0.36, -0.13, 0.05, 0.44,
             0.34, -0.55, -1.17, -1.04, -1.02, -1.46, 999999., 999999., 999999., 999999., 999999., 999999., 999999.,
             999999.,
             999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999.]
    y_b1 = [-0.78, -0.77, -0.66, -0.48, -0.37, -0.34, -0.35, -0.41, -0.69, -1.05, -1.5, -1.59, -1.46, -1.51, -1.47,
            -0.7, -0.29, -0.3, -0.56, -0.85, -0.98, -1.18, -1.16, -1.49, -1.21, -0.98, -0.87, -0.97, -0.75, -0.8, -0.19,
            0.45, 0.66, 0.27, 0.1, 0.43, 0.31, -0.04, -0.16, -0.47, -0.45, -0.51, -0.7, -0.46, -0.49, -0.53, -1.28,
            -0.92, -0.6, -0.71, -1.02, -1.27, -1.78, -1.98, -1.9, -1.54, -1.4, -1.22, -1.51, -1.87, -1.6, -1.18, -0.59,
            -0.59, -0.58, -0.85, -1.92, -2.45, -1.84, -1.39, -1.75, 999999., 999999., 999999., 999999., 999999.,
            999999.,
            999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999.,
            999999.]
    y_b2 = [0.75, 1.02, 1.24, 1.09, 0.89, 0.38, 0.19, -0.21, -0.33, 0.15, 0.85, 1.34, 1.06, 0.58, 0.32, 0.84, 1.28,
            1.23, 1.13, 0.91, 0.8, 1.21, 1.28, 1.24, 1.08, 0.29, -0.04, -0.1, 0.1, 0.15, 0.26, 1.19, 1.83, 1.75, 1.26,
            0.97, 0.77, 0.77, 0.63, 0.19, 0.35, 0.89, 0.99, 0.74, 0.7, 0.87, 1.16, 0.94, 0.42, 0.36, 0.57, 1.14, 0.64,
            0.82, 0.81, 0.9, 0.97, 1.41, 1.51, 1.25, 1.08, 0.47, 0.32, 0.68, 1.46, 1.52, 0.83, 0.12, -0.24, -0.64,
            -1.18, 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999., 999999.,
            999999.,
            999999., 999999., 999999., 999999., 999999., 999999., 999999.]
    # algorithm_input_data.append(x_axis)
    algorithm_input_data.append(y_series)
    algorithm_input_data.append(y_ltm)
    algorithm_input_data.append([y_b1, y_b2])
    algorithm_input_data.append(
        [[-0.79, -0.6, -0.52, -0.55, -0.64, -0.77, -0.83, -0.99, -1.14, -1.22, -1.18, -1.01, -0.79, -0.6, -0.52,
          -0.55], [0.76, 0.56, 0.54, 0.59, 0.67, 0.82, 0.9, 1.09, 1.24, 1.29, 1.18, 1.02, 0.76, 0.56, 0.54, 0.59]])
    page_params = {"main_title": "这里是主标题", "isZero": "True", "islogo": "True",
                   "timeType": "ten", "timeRanges": [20200101, 20220603], #"boxPeriod": [20201118, 20201119],
                   "output_img_name": "aaamon", "yMax": "3.0", "yMin": "-3.0",
                   "output_img_path": "/nfsshare/testSH/",
                   "sub_titles": ["这里是副标题第一行", "这里是副标题第二行"],
                   "unit": "这里是单位",
                   "layers": [{"layer_type": "bar", "isColorDivide": "True", "labelName": "监测(NCEP1)"},
                              {"layer_type": "line", "lineColor": "black", "lineWidth": "1.5",
                               "labelName": "常年值(1991-2020)(NCEP1)",
                               "lineStyle": "-"},
                              {"layer_type": "fill_between", "fillColor": "#CCCCCC", "labelName": "±1σ"},
                              {"layer_type": "box", "labelName": "预测箱线图"}]}
    # 如自定义颜色需要使用十六进制

    me = DrawChartController(sub_local_params=page_params, algorithm_input_data=algorithm_input_data)
    result_dict = me.execute()
