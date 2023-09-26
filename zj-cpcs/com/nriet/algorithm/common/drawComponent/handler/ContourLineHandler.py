import Ngl
import numpy as np
import time
import logging
import os

from com.nriet.algorithm.common.drawComponent.handler.CommonHandler import CommonHandler
from com.nriet.utils.ResourcesUtils import create_or_update_resource

'''
此类用于绘制 等值线叠加图层
'''


class ContourLineHandler(CommonHandler):

    def __init__(self, workstation, plot=None, input_data=None, params_dict=None, layer=None, tmp_service=None):
        '''
        :param workstation: 工作站对象
        :param plot: 上游的plot对象
        :param input_data: 绘图所需数据
        :param params_dict: 绘图handler所需配置字典
        :param layer: 模板service对象
        '''
        if not params_dict:
            params_dict = {}

        if layer.get('intervals', None):
            params_dict['cnLevels'] = np.array(layer.get('intervals'))
            params_dict['cnExplicitLineLabelsOn'] = True
            lineLabels = []
            for inv in layer.get('intervals'):
                if str(inv).endswith(".0"):
                    lineLabels.append(str(int(inv)))
                else:
                    lineLabels.append(str(inv))
            params_dict['cnLineLabelStrings'] = lineLabels
            if layer.get('contour_line_labels', None):
                params_dict['cnLineLabelStrings'] = list(layer.get('contour_line_labels'))
                params_dict['cnLineLabelInterval'] = 1
                params_dict['cnLineLabelPlacementMode'] = 'constant'
                params_dict['cnLineDashSegLenF'] = 0.08
            if layer.get('cnLineLabelPlacementMode', None):
                params_dict['cnLineLabelPlacementMode'] = layer.get('cnLineLabelPlacementMode')
           
        if layer.get('contour_line_space', None):
            params_dict['cnLevelSpacingF'] = float(layer.get('contour_line_space'))

        if layer.get('cnLabelType', None):
            params_dict['cnLineLabelPlacementMode'] = layer.get('cnLabelType')

        if layer.get('contour_line_color', None):
            if "," in layer.get('contour_line_color'):
                params_dict['cnLineColor'] = list(
                    np.array(layer.get('contour_line_color').split(","), dtype=float) / 255.0)
            else:
                params_dict['cnLineColor'] = layer.get('contour_line_color')

        if layer.get('contour_line_colors', None):
            params_dict['cnMonoLineColor'] = False
            if "," in layer.get('contour_line_colors')[0]:
                params_dict['cnLineColors'] = np.array(
                    [(np.array(eval(x)) / 255.).tolist() for x in layer.get('contour_line_colors')])
            else:
                params_dict['cnLineColors'] = layer.get('contour_line_colors')

        if layer.get('line_thickness', None):
            params_dict['cnLineThicknessF'] = layer.get('line_thickness')

        if layer.get('line_thicknesses', None):
            params_dict['cnMonoLineThickness'] = False
            params_dict['cnLineThicknesses'] = layer.get('line_thicknesses')

        if layer.get('contour_line_types', None):
            params_dict['cnLineDashPatterns'] = layer.get('contour_line_types')

        if layer.get('cnLineMax', None):
            params_dict['cnLevelSelectionMode'] = 'ManualLevels'
            params_dict['cnMaxLevelValF'] = layer.get('cnLineMax')

        if layer.get('cnLineMin', None):
            params_dict['cnLevelSelectionMode'] = 'ManualLevels'
            params_dict['cnMinLevelValF'] = layer.get('cnLineMin')

        if tmp_service:
            params_dict['sfXArray'] = tmp_service.lon_indexes
            params_dict['sfYArray'] = tmp_service.lat_indexes
        # 添加平滑参数
        if layer.get('cnSmoothCoef', None):
            params_dict['cnSmoothingOn'] = True
            params_dict['cnSmoothingDistanceF'] = float(layer.get('cnSmoothCoef'))

        super().__init__(workstation, plot, input_data, params_dict=params_dict)

    def draw(self):
        start_time = time.time()

        resource_config = self.params_dict

        # 构造resource对象
        self.resource = create_or_update_resource(params_dict=resource_config)

        # 绘图
        map_plot = Ngl.contour(self.workstation, self.input_data, self.resource)


        # plot叠加
        if self.plot:
            Ngl.overlay(self.plot, map_plot)
        else:
            self.plot = map_plot

        stop_time = time.time()
        cost = stop_time - start_time
        logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))

        return self.plot
