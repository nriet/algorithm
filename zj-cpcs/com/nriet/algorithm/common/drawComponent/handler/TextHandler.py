from PIL import ImageFont
import time
import logging
import os


def add_titles(im, draw, main_title, sub_titles, params_dict={}):
    start_time = time.time()
    if im is None or draw is None:
        return

    img_width, img_height = im.size
    font_file = params_dict.get('font_file_path')
    font_main_size = params_dict.get('font_main_size')
    font_sub_size = params_dict.get('font_sub_size')
    main_title_font = params_dict.get('font_file_path')
    sub_titles_font = params_dict.get('sub_titles_font')
    title_color = params_dict.get('title_color','black')
    title_leftshift = params_dict.get('title_leftshift',0)
    title_topshift = params_dict.get('title_topshift', 0)
    top_padding = params_dict.get('top_padding')  # 上边距40px
    title_padding = params_dict.get('title_padding')  # 标题间隔5px】
    # 字体
    if main_title_font:
        font_main = ImageFont.truetype(font=main_title_font, size=font_main_size)  # 主标题20px
    else:
        font_main = ImageFont.truetype(font=font_file, size=font_main_size)
    if sub_titles_font:
        font_sub = ImageFont.truetype(font=sub_titles_font, size=font_sub_size)  # 副标题15px
    else:
        font_sub = ImageFont.truetype(font=font_file, size=font_sub_size)  # 副标题15px
    # 写主标题
    main_width, main_height = draw.textsize(main_title, font_main)
    draw.text(((img_width - main_width) / 2 - title_leftshift, top_padding-title_topshift), main_title, font=font_main, fill=title_color)
    # 写副标题
    if sub_titles:
        for subtitle in sub_titles:
            sub_width, sub_height = draw.textsize(subtitle, font_sub)
            sub_height = sub_height
            index = sub_titles.index(subtitle)
            draw.text(
                ((img_width - sub_width) / 2 - title_leftshift,
                 top_padding - title_topshift + main_height + (index + 1) * title_padding + index * sub_height),
                subtitle, font=font_sub, fill=title_color)

    stop_time = time.time()
    cost = stop_time - start_time
    logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))


def add_datasource_unit(im, draw, data_source_list=None, unit_list=None, note_list=None, params_dict={}):
    start_time = time.time()
    if not im or not draw:
        return

    img_width, img_height = im.size
    font_file = params_dict.get('font_file_path')
    font_note_size = params_dict.get('font_note_size')
    font_datasource_size = params_dict.get('font_datasource_size')
    font_unit_size = params_dict.get('font_unit_size')
    interval = params_dict.get('interval')  # 数据源和单位之间的间隙
    top_padding = params_dict.get('top_padding')  # 数据源信息距上距离
    right_padding = params_dict.get('right_padding')  # 距右距离
    unit_interval = params_dict.get('unit_interval')  # unit与unit之间的空格个数
    # 字体
    font_note = ImageFont.truetype(font=font_file, size=font_note_size)
    font_datasource = ImageFont.truetype(font=font_file, size=font_datasource_size)
    font_unit = ImageFont.truetype(font=font_file, size=font_unit_size)

    # 写自由文本
    if note_list:
        data_source_list_length = 0
        if data_source_list:
            data_source_list_length = len(data_source_list)

        for i, note in enumerate(note_list):
            note_width, note_height = draw.textsize(note, font_note)
            draw.text(
                (img_width - note_width - right_padding,
                 top_padding - (data_source_list_length + i) * (font_datasource_size + interval) - 2),
                note, font=font_note,
                fill='black')

    # 写数据源
    if data_source_list:
        for i, data_source in enumerate(data_source_list):
            dataource_width, datasource_height = draw.textsize(data_source, font_datasource)
            draw.text(
                (img_width - dataource_width - right_padding, top_padding - i * (font_datasource_size + interval)),
                data_source, font=font_datasource,
                fill='black')

    # 写单位
    if unit_list:
        complex_unit = (' ' * int(unit_interval / 2)).join(unit_list)
        unit_width, unit_height = draw.textsize(complex_unit, font_unit)
        draw.text((img_width - unit_width - right_padding, top_padding + datasource_height + interval - 2),
                  complex_unit,
                  font=font_unit,
                  fill='black')

    stop_time = time.time()
    cost = stop_time - start_time
    logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))


def add_datasource(im, draw, data_source_list=None, params_dict={}):
    start_time = time.time()
    if not im or not draw:
        return

    img_width, img_height = im.size
    font_file = params_dict.get('font_file_path')
    font_datasource_size = params_dict.get('font_datasource_size')

    interval = params_dict.get('interval')  # 数据源和单位之间的间隙
    top_padding = params_dict.get('top_padding')  # 数据源信息距上距离
    right_padding = params_dict.get('right_padding')  # 距右距离

    # 字体
    font_datasource = ImageFont.truetype(font=font_file, size=font_datasource_size)

    # 写数据源
    if data_source_list:
        for i, data_source in enumerate(data_source_list):
            dataource_width, datasource_height = draw.textsize(data_source, font_datasource)
            draw.text(
                (img_width - dataource_width - right_padding,
                 top_padding + i * (font_datasource_size + interval) - font_datasource_size),
                data_source, font=font_datasource,
                fill='black')

    stop_time = time.time()
    cost = stop_time - start_time
    logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))


def add_numbers(im, draw, date, timeType, var, numbers, params_dict=None):
    if params_dict is None:
        params_dict = {}
    start_time = time.time()
    if draw is None:
        return
    font_file = params_dict['font_file_path']
    tx_font_size = params_dict['tx_font_size']
    font_scale = ImageFont.truetype(font=font_file, size=tx_font_size)
    n = numbers[1] + numbers[2]
    # logging.info(date)
    # exit()
    seasonStr = ['春季', '夏季', '秋季', '冬季']
    if timeType == 'mon':
        draw.text([200, 1380], str(date)[0:4] + "." + str(date)[4:6], font=font_scale, fill='black')
    elif timeType == 'season':
        ss = int(str(date)[4:6])
        stri = str(date)[0:4] + "年" + seasonStr[ss - 1]
        draw.text([180, 1380], stri, font=font_scale, fill='black')
    if var == "rain":
        draw.text([130, 1430], "降水预测综合评估", font=font_scale, fill='black')
    elif var == "avgt":
        draw.text([130, 1430], "气温预测综合评估", font=font_scale, fill='black')
    draw.text([200, 1480], "Ps = " + str(numbers[0]), font=font_scale, fill='black')

    draw.text([140, 1530], "趋势预报错误 " + str(numbers[1]), font=font_scale, fill='black')
    draw.text([140, 1597], "趋势预报正确 " + str(numbers[2]), font=font_scale, fill='black')
    draw.text([140, 1664], "一级异常正确 " + str(numbers[3]), font=font_scale, fill='black')
    draw.text([140, 1731], "二级异常正确 " + str(numbers[4]), font=font_scale, fill='black')
    draw.text([140, 1798], "测站实测缺失 " + str(numbers[5]), font=font_scale, fill='black')
    draw.text([140, 1865], "异常漏报站数 " + str(numbers[6]), font=font_scale, fill='black')
    draw.text([70, 1932], "N = " + str(n) + "  M = " + str(numbers[6]), font=font_scale, fill='black')
    draw.text([70, 1999], "N0 = " + str(numbers[2]) + "  N1 = " + str(numbers[3]) + "  N2 = " + str(numbers[4]),
              font=font_scale, fill='black')

    stop_time = time.time()
    cost = stop_time - start_time
    logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))


def add_scale(draw, params_dict=None):
    if params_dict is None:
        params_dict = {}
    start_time = time.time()
    if draw is None:
        return
    font_file = params_dict['font_file_path']
    scala_figure = params_dict['scala_figure']
    tx_font_size = params_dict['tx_font_size']
    location = params_dict['location']
    font_scale = ImageFont.truetype(font=font_file, size=tx_font_size)  # 副标题15px
    draw.textsize(scala_figure, font_scale)
    draw.text(location, scala_figure, font=font_scale, fill='black')

    stop_time = time.time()
    cost = stop_time - start_time
    logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))


def add_legend_unit(im, draw, nboxes, unit, params_dict=None, legends=None, isNaN="False"):
    start_time = time.time()
    if im is None or draw is None:
        return
    if params_dict is None:
        params_dict = {}
    img_width, img_height = im.size
    font_file = params_dict.get('font_file_path')
    lb_legend_font_size = params_dict.get('lb_legend_font_size')
    lb_unit_font_size = params_dict.get('lb_unit_font_size')
    interval = params_dict.get('interval')
    inner_top_padding = params_dict.get('inner_top_padding')
    outer_left_padding = params_dict.get('outer_left_padding')
    outer_buttom_padding = params_dict.get('outer_buttom_padding')

    font_lb_legend = ImageFont.truetype(font=font_file, size=lb_legend_font_size)
    font_lb_unit = ImageFont.truetype(font=font_file, size=lb_unit_font_size)
    lb_legend_width, lb_legend_height = draw.textsize('图例', font_lb_legend)
    lb_unit_width, lb_unit_height = draw.textsize(unit, font_lb_unit)

    lb_width = img_width * 0.11
    lb_height = img_width * 0.022 * 0.868 * (nboxes + 3 - (nboxes - 5) / 2.8) + 0.035 * 930 * 96 / 72 / 4
    if nboxes > 14:
        vpHeightF = 0.263252
    else:
        vpHeightF = 0.022 * 0.868 * (nboxes + 3 - (nboxes - 5) / 2.8)
    label_height = img_width*vpHeightF / (nboxes+1)
    if legends and str(isNaN) == "True":
        legends.insert(0,"缺测")
        # label_height = img_width*vpHeightF / (nboxes+2)
    yy1 = img_height-100
    if legends:
        for ii, legStr in enumerate(legends):
            yy = yy1 - ii * label_height + ii * 5.5
            draw.text([lb_width/2+outer_left_padding, int(yy)], legStr, font=font_lb_unit, fill='black')
    # 新绘图修改
    if nboxes > 14:
        draw.text(((lb_width - lb_legend_width) / 2 + outer_left_padding,
                   1355.5532), '图例',
                  font=font_lb_legend,
                  fill='black')
        draw.text(((lb_width - lb_unit_width) / 2 + outer_left_padding,
                   1414.5532), unit,
                  font=font_lb_unit, fill='black')
    else:
        draw.text(((lb_width - lb_legend_width) / 2 + outer_left_padding,
                   img_height - (lb_height - inner_top_padding + outer_buttom_padding) - (14 - nboxes) * 5), '图例',
                  font=font_lb_legend,
                  fill='black')
        draw.text(((lb_width - lb_unit_width) / 2 + outer_left_padding,
                   img_height - (lb_height - inner_top_padding - lb_legend_height - interval + outer_buttom_padding) - (
                               14 - nboxes) * 5), unit,
                  font=font_lb_unit, fill='black')
    # 结束
    stop_time = time.time()
    cost = stop_time - start_time
    logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))

def add_legends(im, draw, legends, params_dict={}):
    start_time = time.time()
    if im is None or draw is None:
        return

    font_file = params_dict.get('font_file_path')
    font_main_size = params_dict.get('font_main_size')
    # 字体
    font_main = ImageFont.truetype(font=font_file, size=font_main_size)  # 主标题20px

    img_width, img_height = im.size
    # 写副标题
    xx = 140
    yy = img_height - 210
    if legends:
        for subtitle in legends:
            xx = xx + 580
            draw.text([int(xx), int(yy)], subtitle, font=font_main, fill='black')

    stop_time = time.time()
    cost = stop_time - start_time
    logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))

def add_gl_common_legends(im, draw, legends, params_dict=None, vpWidthF=None, isNaN="False"):
    start_time = time.time()
    if im is None or draw is None:
        return
    # 追加缺测图例
    if str(isNaN) == "True":
        legends.insert(0,"缺测")
    font_file = params_dict.get('font_file_path')
    font_main_size = params_dict.get('font_sub_size')
    # 字体
    font_main = ImageFont.truetype(font=font_file, size=font_main_size)  # 主标题20px
    img_width, img_height = im.size
    legend_width = vpWidthF * img_width
    label_width = legend_width/len(legends)
    # 写副标题
    xx = (img_width - legend_width) /2  + label_width / 3
    yy = img_height -80
    if legends:
        for ii, subtitle in enumerate(legends):
            xx1 = xx + ii*label_width
            draw.text([int(xx1), int(yy)], subtitle, font=font_main, fill='black')

    stop_time = time.time()
    cost = stop_time - start_time
    logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))
