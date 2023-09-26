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


class NorthLabelBarHandler(CommonHandler):
    def __init__(self, workstation, plot=None, input_data=None, params_dict=None, layer=None, tmp_service=None):
        if params_dict:
            params_dict = copy.deepcopy(params_dict)
        super(NorthLabelBarHandler, self).__init__(workstation=workstation, plot=plot, params_dict=params_dict)
        self.output_img_name = tmp_service.request_dict['output_img_name']
        self.location_params_dict = params_dict.pop('labelbar_location')
        self.params_dict = params_dict
        if layer:
            self.colors = layer.get('colors')
            self.legend_labels = layer.get('intervals')

    def draw(self):
        start_time = time.time()

        params_dict = self.params_dict
        legend_labels = ['9.1', '', '9.21', '',
                            '10.11', '', '11.01', '',
                            '11.21', '', '12.11', '',
                            '01.01', '', '01.20']
        colors = np.array(self.colors)
        cn_fill_colors = np.arange(0, len(colors), 1)

        nboxes = np.shape(cn_fill_colors)[0]
       
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
