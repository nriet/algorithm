import Ngl
import numpy as np
import time
import logging
import os,copy

from com.nriet.algorithm.common.drawComponent.handler.CommonHandler import CommonHandler
from com.nriet.utils.ResourcesUtils import create_or_update_resource

'''
此类用于画图例叠加图层
'''


class GlobalLabelBarHandler(CommonHandler):
    def __init__(self, workstation, plot=None, input_data=None, params_dict=None, layer=None, tmp_service=None):
        if params_dict:
            params_dict = copy.deepcopy(params_dict)
        super(GlobalLabelBarHandler, self).__init__(workstation=workstation, plot=plot, params_dict=params_dict)
        self.output_img_name = tmp_service.request_dict['output_img_name']
        self.location_params_dict = params_dict.pop('labelbar_location')
        self.params_dict = params_dict
        if layer:
            self.layer = layer
            self.colors = layer.get('colors')
            self.legend_labels = layer.get('intervals') # 默认使用图例的intervals
            # 若自定义英文标签存在时，使用自定义英文标签
            if layer.get('en_legend_labels'):
                self.legend_labels = layer.get('en_legend_labels')
            # 若自定义中文标签存在时，使用自定义中文标签
            if layer.get('ch_legend_labels'):
                self.legend_labels = layer.get('ch_legend_labels')


    def draw(self):
        start_time = time.time()
        params_dict = self.params_dict
        # 中文标签 先不绘制标签值
        if self.layer.get('ch_legend_labels'):
            legend_labels = ["" for item in self.legend_labels]
            # 是否绘制缺测标签
            if str(self.layer.get('isNaN', "False")) == "True":
                self.colors.insert(0, [0.67, 0.67, 0.67])
                legend_labels.insert(0, "")
        else:
            legend_labels = [str(int(i)) if not isinstance(i,str) and i % 1 == 0 else str(i) for i in self.legend_labels]
            # 是否绘制缺测标签
            if str(self.layer.get('isNaN', "False")) == "True":
                self.colors.insert(0, [0.67, 0.67, 0.67])
                legend_labels.insert(0, 'NaN')
        colors = np.array(self.colors)
        cn_fill_colors = np.arange(0, len(colors), 1)
        nboxes = np.shape(cn_fill_colors)[0]
        # 若图例标签个数和图例颜色个数相等时，标签放在颜色下面
        if len(legend_labels) == len(colors):
            params_dict['lbLabelAlignment'] = "BoxCenters"
        params_dict['lbFillColors'] = colors
        params_dict['lbLabelStrings'] = legend_labels
        lbres = create_or_update_resource(params_dict=params_dict)
        # logging.info(params_dict)
        # exit()
        lbid = Ngl.labelbar_ndc(self.workstation, nboxes, legend_labels, 0, 0, lbres)

        # 5.色标位置配置
        lblres = create_or_update_resource(params_dict=self.location_params_dict)
        Ngl.add_annotation(self.plot, lbid, lblres)
        # logging.info(1111111111111)
        # exit()

        stop_time = time.time()
        cost = stop_time - start_time
        logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))
