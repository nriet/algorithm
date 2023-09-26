import logging
import os
import Ngl
import numpy as np

from com.nriet.utils.ResourcesUtils import create_or_update_resource


class WorkstationHandler:
    def __init__(self
                 , output_img_type=''  # 最终输出图片格式 例:png
                 , output_img_path=''  # 最终输出图片位置，例:/usr/local/example
                 , output_img_name=''
                 , wK_res_params={}  # workstation的Resource相关配置参数
                 , plot=None):

        self.__wk_res = create_or_update_resource(None, wK_res_params)
        # 判断文件路径是否存在，如果不存在，则创建，此处是创建多级目录

        if not os.path.isdir(output_img_path):
            os.makedirs(output_img_path)
        logging.info("             output_img_path is :%s" % output_img_path)

        self.__wk = Ngl.open_wks(output_img_type, output_img_path + output_img_name, self.__wk_res)
        # Ngl.define_colormap(self.__wk, colors)  #这里不能设置颜色！！
        self.plot = plot
        logging.info("             workstation init finished!")

    def _get_wk_res(self):
        return self.__wk_res

    def _set_wk_res(self, res):
        self.__wk_res = res

    def _get_wk(self):
        return self.__wk

    def _set_wk(self, wk):
        self.__wk = wk

    def close_workstation(self):
        # Ngl绘图结束
        Ngl.draw(self.plot)
        Ngl.frame(self.__wk)
        Ngl.delete_wks(self.__wk)
        # Ngl.end()  千万别用这个玩意，会导致多线程条件下画不出多个图出来！！！！

    def add_lon_labels(self):
        lon_values = np.arange(0, 357.5, 90)
        lon_labels = []
        for lon_value in lon_values:
            if lon_value == 0 or lon_value == 180:
                lon_labels.append("{:g}".format(lon_value))
            else:
                if lon_value < 180:
                    lon_labels.append("{:g}W".format(abs(lon_value)))
                elif lon_value > 180:
                    lon_labels.append("{:g}E".format(abs(360 - lon_value)))

        xndc = [0.107, 0.5, 0.90, 0.5]
        yndc = [0.495, 0.887, 0.495, 0.10]

        txres = Ngl.Resources()
        txres.txFontHeightF = 0.015
        for i, lon_label in enumerate(lon_labels):
            # txres.txJust = just_strs[i]
            Ngl.text_ndc(self.__wk, lon_label, xndc[i], yndc[i], txres)

        return

    def add_lat_labels(self, min_lat, max_lat):
        lat_values = []
        lat_labels = []
        # 设置需要绘制纬度标签及对应的纬度值
        # 南极
        if min_lat == -90:
            if -10 < max_lat <= 0:
                lat_values = [-10, -30, -60]
                lat_labels = ['10S', '30S', '60S']
            elif -30 < max_lat <= -10:
                lat_values = [-30, -60]
                lat_labels = ['30S', '60S']
            elif -60 < max_lat <= -30:
                lat_values = [-60]
                lat_labels = ['60S']
        # 北极
        if max_lat == 90:
            if 0 <= min_lat < 10:
                lat_values = [10, 30, 60]
                lat_labels = ['10N', '30N', '60N']
            elif 10 <= min_lat < 30:
                lat_values = [30, 60]
                lat_labels = ['30N', '60N']
            elif 30 <= min_lat < 60:
                lat_values = [60]
                lat_labels = ['60N']

        # 绘制标签
        txres = Ngl.Resources()
        txres.txFontHeightF = 0.01
        txres.txFontOpacityF = 0.5
        for i, lat_label in enumerate(lat_labels):
            Ngl.add_text(self.__wk, self.plot, lat_label, 0, lat_values[i], txres)

        return
