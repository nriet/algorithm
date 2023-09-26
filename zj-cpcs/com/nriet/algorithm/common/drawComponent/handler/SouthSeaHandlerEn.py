import Ngl
import Nio
import numpy as np
import time
import sys,copy
import os
import logging
from com.nriet.algorithm.common.drawComponent.handler.CommonHandler import CommonHandler
from com.nriet.utils import StringUtils, proxyUtils
from com.nriet.utils.ResourcesUtils import create_or_update_resource

shape_file_path = "/nfsshare/cdbdata/algorithm/conductor/WMFS/EXTPRE/ysq/map/"

'''
此类用于绘制南海相关叠加图层
'''


class SouthSeaHandlerEn(CommonHandler):
    def __init__(self, workstation, plot=None, input_data=None, params_dict=None, layers=None, tmp_service=None):
        super().__init__(workstation, plot, input_data, params_dict=params_dict)
        self.layers = layers
        self.tmp_service = tmp_service

    def draw(self):
        start_time = time.time()
        layers = self.layers
        input_data = self.input_data
        params_dict = self.params_dict

        # 1.绘制南海底板
        map_plot = None
        first_layer = layers[0]  # 默认第一层存在图例

        if not 'contourMap' in [layer['layer_type'] for layer in layers]:
            logging.info("execute Pure Map layer!")
            class_name = 'MapHandler'
            map_params_dict = self.params_dict.get('map')
            pre_map_dict = self.build_map_params(None)
            map_params_dict.update(pre_map_dict)

            draw_handler = proxyUtils.create_class_instance(
                '.'.join(['com.nriet.algorithm.common.drawComponent.handler', class_name]), class_name,
                workstation=self.workstation, plot=None,
                input_data=None,
                params_dict=map_params_dict, layer=first_layer, tmp_service=self.tmp_service)

            map_plot = draw_handler.draw()

        for i, layer in enumerate(layers):
            layer_type = layer['layer_type']
            if layer_type == 'contourMap':
                contour_map_layer = layer

            # 入参准备阶段--获取模板配置
            params_dict = self.params_dict.get(layer_type)
            # 入参准备阶段--获取调用handler前的特定参数构建方法
            func = getattr(self, ''.join(['build_', layer_type, '_params']), None)
            if func:
                pre_params_dict = func(layer)
                params_dict.update(pre_params_dict)
            if layer_type=='polyline': # 南海不做多shp绘制，否则重复绘制，线条颜色过粗
                continue
            class_name = StringUtils.capitalize_str(layers[i]['layer_type']) + 'Handler'
            draw_handler = proxyUtils.create_class_instance('.'.join(['com.nriet.algorithm.common.drawComponent.handler', class_name]), class_name,
                                                            workstation=self.workstation, plot=map_plot,
                                                            input_data=input_data[i],
                                                            params_dict=params_dict,
                                                            layer=layer, tmp_service=self.tmp_service)
            map_plot = draw_handler.draw()  # 一定返回唯一的，首次绘制的plot!

        # 2.绘制南海相关地理线
        geo_line = copy.deepcopy(self.params_dict.get('geo') ) # 多级

        for key, geo_params_dict in geo_line.items():
            file_name = geo_params_dict.pop('file_name')
            geo_type = geo_params_dict.pop('type')
            shape = Nio.open_file(shape_file_path + file_name, "r")
            lon = np.ravel(shape.variables["x"][:])
            lat = np.ravel(shape.variables["y"][:])
            geo_params_dict['gsSegments'] = shape.variables["segments"][:, 0]
            resource = create_or_update_resource(params_dict=geo_params_dict)
            # 2.绘制曲线图
            if geo_type == 'polyline':
                Ngl.add_polyline(self.workstation, map_plot, lon, lat, resource)
            elif geo_type == 'polygon':
                Ngl.add_polygon(self.workstation, map_plot, lon, lat, resource)
            else:
                pass  # point待处理

        # 3. 南海加比例尺
        # south_sea_scale = copy.deepcopy(self.params_dict.get('scale'))
        # scala_figure = south_sea_scale.pop('scala_figure')
        # x, y = south_sea_scale.pop('location').split('x')
        # resource = create_or_update_resource(params_dict=south_sea_scale)
        # Ngl.add_text(self.workstation, map_plot, scala_figure, x, y, resource)

        # 4.南海放在中国的位置
        south_sea_location = copy.deepcopy(self.params_dict.get('location'))
        resource = create_or_update_resource(params_dict=south_sea_location)
        Ngl.add_annotation(self.plot, map_plot, resource)

        stop_time = time.time()
        cost = stop_time - start_time
        logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))

        return self.plot


    def build_vector_params(self, layer=None):
        params_dict = {}
        if layer.get('vector_scale'):
            params_dict['vcRefMagnitudeF'] = float(layer.get('vector_scale'))
        return params_dict

    def build_contourMap_params(self, layer):
        contour_params_dict = {}
        # 栅格图显示
        if layer.get('contourFillMode'):
            contour_params_dict['cnFillMode'] = layer.get('contourFillMode')
        if layer.get('cnLine'):
            if layer.get('cnLine') == 'True':
                contour_params_dict['cnFillOn'] = False
                contour_params_dict['cnLinesOn'] = True
                contour_params_dict['cnLineLabelsOn'] = False
                contour_params_dict['cnLabelDrawOrder'] = 'PreDraw'
                contour_params_dict['cnLineDrawOrder'] = 'PreDraw'
                if layer.get('intervals', None):
                    contour_params_dict['cnLevels'] = np.array(layer.get('intervals'))

                if layer.get('contour_line_space', None):
                    contour_params_dict['cnLevelSpacingF'] = float(layer.get('contour_line_space'))

                if layer.get('contour_line_color', None):
                    contour_params_dict['cnLineColor'] = layer.get('contour_line_color')

                if layer.get('line_thickness', None):
                    contour_params_dict['cnLineThicknessF'] = layer.get('line_thickness')

                if layer.get('cnLineMax', None):
                    contour_params_dict['cnLevelSelectionMode'] = 'ManualLevels'
                    contour_params_dict['cnMaxLevelValF'] = layer.get('cnLineMax')

                if layer.get('cnLineMin', None):
                    contour_params_dict['cnLevelSelectionMode'] = 'ManualLevels'
                    contour_params_dict['cnMinLevelValF'] = layer.get('cnLineMin')

        return contour_params_dict

    def build_map_params(self,layer):

        return  {}

    def build_polyMarker_params(self,layer):
        params_dict = {}
        marker_size = layer.get('marker_size',None)
        marker_type = layer.get('marker_type', None)
        marker_color = layer.get('marker_color', None)
        if marker_type:
            params_dict['gsMarkerIndex'] = int(marker_type)
        if marker_color:
            params_dict['gsMarkerColor'] = marker_color
        if marker_size:
            params_dict['gsMarkerSizeF'] = 0.002
        return params_dict