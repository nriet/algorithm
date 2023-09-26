import logging
import os
import math
import Ngl, logging
import numpy as np
from PIL import Image, ImageDraw

from com.nriet.algorithm.common.drawComponent.drawService.CommonService import CommonService
from com.nriet.algorithm.common.drawComponent.handler import LogoHandler, TextHandler
from com.nriet.algorithm.common.drawComponent.handler.GlobalLabelBarHandler import GlobalLabelBarHandler
from com.nriet.algorithm.common.drawComponent.handler.WorkstationHandler import WorkstationHandler
from com.nriet.algorithm.common.drawComponent.resourceConfig.SectionConfig import section_params_dict
from com.nriet.algorithm.common.drawComponent.util.LonLatUtils import get_lon_lat
from com.nriet.config.PathConfig import CPCS_ROOT_PATH
from com.nriet.utils import StringUtils, proxyUtils
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
from com.nriet.utils.obs.ObsUtils import ObsUtils
from com.nriet.utils.result.ResponseResultUtils import build_response_dict


class SectionService(CommonService):

    def draw(self):
        # 0.参数准备
        input_data = self.input_data
        # 是否绘制logo 默认绘制  绘制：True  不绘制：False
        islogo = self.request_dict.get("islogo", "True")
        output_img_type = self.request_dict["output_img_type"]
        output_img_path = self.request_dict["output_img_path"]
        output_img_name = self.request_dict["output_img_name"]
        expire = self.request_dict.get("expire")
        temp_img_path = CPCS_ROOT_PATH + "com/nriet/test/"
        main_title = self.request_dict["main_title"]
        sub_titles = self.request_dict.get("sub_titles")
        layers = self.request_dict['layers']

        # 输入数据的check，如果任意维度的长度小于3则抛出异常
        if isinstance(input_data[0], list):
            if np.sum(np.array(input_data[0][0].shape) < 3) > 0:
                logging.info("input_data dims is less than 3")
                raise Exception("input_data dims is less than 3")
        else:
            if np.sum(np.array(input_data[0].shape) < 3) > 0:
                logging.info("input_data dims is less than 3")
                raise Exception("input_data dims is less than 3")

        # 1.创建workstation
        wk_params_dict = self.build_workstationHandler_params()
        workstation_handler = WorkstationHandler(output_img_type, temp_img_path, output_img_name,
                                                 wk_params_dict)
        workstation = workstation_handler._get_wk()

        # 2.业务多图层绘制
        map_plot = None
        data_source_list = []
        unit_list = []
        note_list = []

        contour_map_layer = None
        for i, layer in enumerate(layers):
            layer_type = layer['layer_type']
            if layer_type == 'contour':
                contour_map_layer = layer
            if layer.get('data_source'):
                data_source_list.append(layer.get('data_source'))
            if layer.get('unit'):
                unit_list.append(layer.get('unit'))
            if layer.get('note'):
                note_list.append(layer.get('note'))

            # 入参准备阶段--获取模板配置
            params_dict = section_params_dict.get(layer_type)
            # 入参准备阶段--获取调用handler前的特定参数构建方法
            func = getattr(self, ''.join(['build_', layer_type, '_params']), None)
            if func:
                params_dict = func(layer, params_dict)
            # 动态创建Handler实例
            class_name = StringUtils.capitalize_str(layer_type) + 'Handler'
            draw_handler = proxyUtils.create_class_instance(
                '.'.join(['com.nriet.algorithm.common.drawComponent.handler', class_name]), class_name,
                workstation=workstation, plot=map_plot,
                input_data=input_data[i],
                params_dict=params_dict, layer=layer, tmp_service=self)
            # 调用handler绘制图层,返回唯一的、最基础的plot
            map_plot = draw_handler.draw()
            del draw_handler
        workstation_handler.plot = map_plot

        # 绘制图例
        if contour_map_layer:
            if contour_map_layer['layer_type'] == 'contour':
                label_bar_handler = GlobalLabelBarHandler(workstation, map_plot,
                                                          params_dict=section_params_dict.get('label_bar_global'),
                                                          layer=contour_map_layer, tmp_service=self)
                label_bar_handler.draw()

        # 2.1 处理任意多个横竖线
        if self.request_dict.get('line_dims'):
            polyline_resource = self.build_polyline_resource()
            for line_index, line_dim in enumerate(self.request_dict.get('line_dims')):
                line_value = self.request_dict.get('line_values')[line_index]
                if line_dim not in ['level', 'lat', 'time']:
                    logging.info("Polyline cannot be drawn for dim is %s !" % line_dim)
                    continue
                else:
                    self.draw_polyline(workstation, workstation_handler.plot, line_dim, line_value, polyline_resource)
            logging.info('All polylines have been drawn !')

        # 3.关闭workstation
        workstation_handler.close_workstation()
        del workstation_handler

        # 裁剪图片大小
        im = self.buildImage(temp_img_path, output_img_name, output_img_type)
        draw = ImageDraw.Draw(im)

        # 4.绘制LOGO
        if islogo == "True":
            LogoHandler.add_logos(im, section_params_dict['logo_elements'])

        # 5.绘制Title和数据源&unit
        if len(sub_titles) == 1:
            TextHandler.add_titles(im, draw, main_title, sub_titles,
                                   params_dict=section_params_dict['title_elements_2'])
        else:
            TextHandler.add_titles(im, draw, main_title, sub_titles, params_dict=section_params_dict['title_elements'])

        TextHandler.add_datasource_unit(im, draw, data_source_list, unit_list, note_list,
                                        params_dict=section_params_dict['datasource_unit'])
        # 6.保存
        save_to_nfsshare_switch = look_for_single_global_config("SAVE_TO_NFSSHARE_SWITCH")
        save_to_obs_switch = look_for_single_global_config("SAVE_TO_OBS_SWITCH")
        if int(save_to_nfsshare_switch) or self.request_dict.get("saveToNfsshare"):
            im.save(output_img_path + output_img_name + '.' + output_img_type)
            if self.request_dict.get("output_img_type_eps") and int(self.request_dict.get("output_img_type_eps")) == 1:
                fig = Image.open(output_img_path + output_img_name + '.' + output_img_type)
                if fig.mode in ('RGBA', 'LA'):
                    fig = fig.convert('RGB')
                fig.save(output_img_path + output_img_name + '.eps')
                fig.close()

        # 是否上传至obs
        if int(save_to_obs_switch) or self.request_dict.get("saveToObs"):
            if self.request_dict.get("output_img_type_eps") and int(self.request_dict.get("output_img_type_eps")) == 1:
                if im.mode in ('RGBA', 'LA'):
                    im = im.convert('RGB')
                storage_result = ObsUtils().img_save_to_obs(im, output_img_name, "eps", expire)
            else:
                storage_result = ObsUtils().img_save_to_obs(im, output_img_name, output_img_type, expire)

        # 删除临时文件
        try:
            os.remove(temp_img_path + output_img_name + '.' + output_img_type)
        except FileNotFoundError:
            pass
        logging.info("             delete temp file %s" % temp_img_path + output_img_name + '.' + output_img_type)

        return build_response_dict()

    def build_polyline_resource(self):
        polyline_resource = Ngl.Resources()
        polyline_resource.gsLineColor = 'black'
        polyline_resource.gsLineDashPattern = 5
        polyline_resource.gsLineThicknessF = 3.0
        if self.request_dict.get('line_colors'):
            polyline_resource.gsLineColor = self.request_dict.get('line_colors')
        if self.request_dict.get('line_patterns'):
            polyline_resource.gsLineDashPattern = int(self.request_dict.get('line_patterns'))
        if self.request_dict.get('line_thick'):
            polyline_resource.gsLineThicknessF = self.request_dict.get('line_thick')
        return polyline_resource

    def build_workstationHandler_params(self):
        # imgWidth, imgHeight = (float(x) for x in self.request_dict['output_img_max_width'].split("x"))  # 输出图片的长宽像素
        img_width = 1200
        wk_params_dict = {
            "wkWidth": img_width
            , "wkHeight": img_width
        }
        return wk_params_dict

    def build_contour_params(self, layer=None, params_dict=None):
        if params_dict:
            if layer.get('draw_regions'):  # 有的话，给的是具体的值！ 而不是下标！
                # draw_regions = layer.get("draw_regions")
                # if type(draw_regions) == 'str':
                #     start_lon, end_lon, start_lat, end_lat = layer['draw_regions'].split(",")
                # elif type(draw_regions) == 'tuple':
                #     start_lon, end_lon, start_lat, end_lat = layer['draw_regions']

                # start_lon, end_lon, start_lat, end_lat = layer['draw_regions'].split(",")
                # start_lon = float(start_lon) if start_lon.isdigit() else self.lon_indexes[0]
                # end_lon = float(end_lon) if end_lon.isdigit() else self.lon_indexes[-1]
                # start_lat = float(start_lat) if start_lat.isdigit() else self.lat_indexes[0]
                # end_lat = float(end_lat)if end_lat.isdigit() else self.lat_indexes[-1]

                # end_lat, end_lon, start_lat, start_lon = self.convert_start_end(end_lat, end_lon, start_lat, start_lon)

                end_lat, end_lon, start_lat, start_lon = get_lon_lat(layer, self.dims, self.lon, self.lon_indexes,
                                                                     self.lat, self.lat_indexes)

                params_dict['trXMinF'] = start_lon
                params_dict['trXMaxF'] = end_lon
                params_dict['trYMinF'] = start_lat
                params_dict['trYMaxF'] = end_lat
            else:
                params_dict['trXMinF'] = min(self.lon_indexes)
                params_dict['trXMaxF'] = max(self.lon_indexes)
                params_dict['trYMinF'] = min(self.lat_indexes)
                params_dict['trYMaxF'] = max(self.lat_indexes)

            params_dict['tmXBValues'] = self.request_dict.get('x_values')
            params_dict['tmYLValues'] = self.request_dict.get('y_values')
            if self.request_dict.get('x_sub_values'):
                params_dict['tmXBMinorValues'] = self.request_dict.get('x_sub_values')
            else:
                params_dict['tmXBMinorOn'] = False
            if self.request_dict.get('y_sub_values'):
                params_dict['tmYLMinorValues'] = self.request_dict.get('y_sub_values')
            else:
                params_dict['tmYLMinorOn'] = False

            params_dict['tmXBLabels'] = self.request_dict.get('x_labels')
            params_dict['tmYLLabels'] = self.request_dict.get('y_labels')
            params_dict['tiYAxisString'] = self.request_dict.get('y_left_title', "")
            if self.request_dict.get('y_title'):
                params_dict['tiXAxisOn'] = True
                params_dict['tiXAxisString'] = self.request_dict.get('y_title')
            if self.request_dict.get('y_right_axis'):
                params_dict['vpXF'] = 0.1
                params_dict['vpYF'] = 0.888172,
                params_dict['vpWidthF'] = 0.832720
                params_dict['vpHeightF'] = 0.546651
                params_dict['tmYROn'] = True
                params_dict['tmYRMode'] = 'Explicit'
                params_dict['tmYUseLeft'] = False
                params_dict['tmYRLabelsOn'] = True
                params_dict['tmYRLabels'] = self.request_dict.get('y_right_labels')
                values_tmp = self.request_dict.get('y_right_values')
                # 压高公式计算不同海拔高度所在的气压层
                params_dict['tmYRValues'] = [round(math.log10(1013.25 * (1 - i * 0.0065 / 288.15) ** 5.25145), 6) * 1000
                                             for i in values_tmp]

            y_dim = self.dims[0]
            if y_dim not in ['level', 'time']:
                params_dict['trYReverse'] = False

        return params_dict

    def build_contourLine_params(self, layer=None, params_dict=None):
        if params_dict:
            if layer.get('draw_regions'):  # 有的话，给的是具体的值！ 而不是下标！
                end_lat, end_lon, start_lat, start_lon = get_lon_lat(layer, self.dims, self.lon, self.lon_indexes,
                                                                     self.lat, self.lat_indexes)

                params_dict['trXMinF'] = start_lon
                params_dict['trXMaxF'] = end_lon
                params_dict['trYMinF'] = start_lat
                params_dict['trYMaxF'] = end_lat
            else:
                params_dict['trXMinF'] = min(self.lon_indexes)
                params_dict['trXMaxF'] = max(self.lon_indexes)
                params_dict['trYMinF'] = min(self.lat_indexes)
                params_dict['trYMaxF'] = max(self.lat_indexes)

            # 如果没有countor layer ,坐标轴也得化
            if 'contour' not in [layer.get('layer_type') for layer in self.request_dict.get('layers')]:
                logging.info('product img has not contour layer!')
                params_dict['pmTickMarkDisplayMode'] = 'Always'

                params_dict['tmXBValues'] = self.request_dict.get('x_values')
                params_dict['tmYLValues'] = self.request_dict.get('y_values')
                if self.request_dict.get('x_sub_values'):
                    params_dict['tmXBMinorValues'] = self.request_dict.get('x_sub_values')
                else:
                    params_dict['tmXBMinorOn'] = False
                if self.request_dict.get('y_sub_values'):
                    params_dict['tmYLMinorValues'] = self.request_dict.get('y_sub_values')
                else:
                    params_dict['tmYLMinorOn'] = False

                params_dict['tmXBLabels'] = self.request_dict.get('x_labels')
                params_dict['tmYLLabels'] = self.request_dict.get('y_labels')
                params_dict['tiYAxisString'] = self.request_dict.get('y_left_title', "")
                if self.request_dict.get('y_title'):
                    params_dict['tiXAxisOn'] = True
                    params_dict['tiXAxisString'] = self.request_dict.get('y_title')
                if self.request_dict.get('y_right_axis'):
                    params_dict['vpXF'] = 0.1
                    params_dict['vpYF'] = 0.888172,
                    params_dict['vpWidthF'] = 0.832720
                    params_dict['vpHeightF'] = 0.546651
                    params_dict['tmYROn'] = True
                    params_dict['tmYRMode'] = 'Explicit'
                    params_dict['tmYUseLeft'] = False
                    params_dict['tmYRLabelsOn'] = True
                    params_dict['tmYRLabels'] = self.request_dict.get('y_right_labels')
                    values_tmp = self.request_dict.get('y_right_values')
                    # 压高公式计算不同海拔高度所在的气压层
                    params_dict['tmYRValues'] = [
                        round(math.log10(1013.25 * (1 - i * 0.0065 / 288.15) ** 5.25145), 6) * 1000
                        for i in values_tmp]

                y_dim = self.dims[0]
                if y_dim not in ['level', 'time']:
                    params_dict['trYReverse'] = False

        return params_dict

    def convert_start_end(self, end_lat, end_lon, start_lat, start_lon):
        # 考虑数据类型
        if start_lon.isdigit():
            if self.dims[1] == 'time':
                start_lon = int(start_lon)
                start_lon = list(self.lon).index(start_lon)
            else:
                start_lon = float(start_lon)

        else:
            start_lon = self.lon_indexes[0]
        if end_lon.isdigit():
            if self.dims[1] == 'time':
                end_lon = int(end_lon)
                end_lon = list(self.lon).index(end_lon)
            else:
                end_lon = float(end_lon)

        else:
            end_lon = self.lon_indexes[-1]
        # 考虑数据类型
        if start_lat.isdigit():
            if self.dims[0] == 'time':
                start_lat = int(start_lat)
                start_lat = list(self.lat).index(start_lat)
            else:
                start_lat = float(start_lat)

        else:
            start_lat = self.lat_indexes[0]
        if end_lat.isdigit():
            if self.dims[0] == 'time':
                end_lat = int(end_lat)
                end_lat = list(self.lat).index(end_lat)
            else:
                end_lat = float(end_lat)
        else:
            end_lat = self.lon_indexes[-1]
        return end_lat, end_lon, start_lat, start_lon

    def build_vector_params(self, layer=None, params_dict=None):
        if params_dict:
            if layer.get('draw_regions'):
                # draw_regions = layer.get("draw_regions")
                # if type(draw_regions) == 'str':
                #     start_lon, end_lon, start_lat, end_lat = layer['draw_regions'].split(",")
                # elif type(draw_regions) == 'tuple':
                #     start_lon, end_lon, start_lat, end_lat = layer['draw_regions']

                end_lat, end_lon, start_lat, start_lon = get_lon_lat(layer, self.dims, self.lon, self.lon_indexes,
                                                                     self.lat, self.lat_indexes)

                # start_lon = list(self.lon).index(float(start_lon)) if is_number(start_lon) else self.lon_indexes[0]
                # end_lon = list(self.lon).index(float(end_lon)) if is_number(end_lon) else self.lon_indexes[-1]
                # start_lat = list(self.lat).index(float(start_lat)) if is_number(start_lat) else self.lat_indexes[0]
                # end_lat = list(self.lat).index(float(end_lat)) if is_number(end_lat) else self.lat_indexes[-1]
                #
                # end_lat, end_lon, start_lat, start_lon = self.convert_start_end(end_lat, end_lon, start_lat, start_lon)

                params_dict['vfXCStartV'] = start_lon
                params_dict['vfXCEndV'] = end_lon
                params_dict['vfYCStartV'] = start_lat
                params_dict['vfYCEndV'] = end_lat
            params_dict['vcRefAnnoString1'] = layer.get('vector_unit')
            if layer.get('vector_scale'):
                params_dict['vcRefAnnoString2'] = layer.get('vector_scale')
                params_dict['vcRefMagnitudeF'] = float(layer.get('vector_scale'))
            if layer.get('vector_string1'):
                params_dict['vcRefAnnoString1'] = layer.get('vector_string1')
            if layer.get('vector_distance'):
                params_dict['vcMinDistanceF'] = float(layer.get('vector_distance'))
            if layer.get('vector_location'):
                if layer.get('vector_location') == "BottomRight":
                    params_dict['vcRefAnnoOrthogonalPosF'] = -0.12
                    params_dict['vcRefAnnoSide'] = "Bottom"
                    params_dict['vcRefAnnoJust'] = layer.get('vector_location')
            if layer.get('vector_string2'):
                params_dict['vcRefAnnoString2'] = layer.get('vector_string2')
            # 矢量风颜色
            if layer.get('vector_color'):
                if "," in layer.get('vector_color'):
                    params_dict['vcLineArrowColor'] = list(
                        np.array(layer.get('vector_color').split(","), dtype=float) / 255.0)
                else:
                    params_dict['vcLineArrowColor'] = layer.get('vector_color')
            # 矢量风疏密度
            if layer.get('vector_distance'):
                params_dict['vcMinDistanceF'] = float(layer.get('vector_distance'))

            # 风杆类型
            if layer.get('vectorMode'):
                if layer.get('vectorMode') == 'WindBarb':
                    params_dict['vcGlyphStyle'] = 'WindBarb'
                    params_dict['vcWindBarbTickSpacingF'] = 0.1  # 每一根风羽箭头上的羽毛间距
                    params_dict['vcWindBarbCalmCircleSizeF'] = -1  # 圆形图大小，-1为黑点
                    params_dict['vcWindBarbLineThicknessF'] = 2  # 风杆粗细
                    params_dict['vcWindBarbTickLengthF'] = 0.3  # 羽毛长度
                    params_dict['vcWindBarbScaleFactorF'] = 2.5  # 风系数 国际标准和国内标准的转换
                    params_dict['vcRefLengthF'] = 0.023  # 风杆长度
                    if layer.get('windLength'):
                        params_dict['vcRefLengthF'] = float(layer.get('windLength'))

                    if layer.get('barLength'):
                        params_dict['vcWindBarbTickLengthF'] = float(layer.get('barLength'))

            # 如果没有countor layer ,坐标轴也得化
            if 'contour' not in [layer.get('layer_type') for layer in self.request_dict.get('layers')]:
                logging.info('product img has not contour layer!')
                params_dict['pmTickMarkDisplayMode'] = 'Always'

                params_dict['tmXBValues'] = self.request_dict.get('x_values')
                params_dict['tmYLValues'] = self.request_dict.get('y_values')
                if self.request_dict.get('x_sub_values'):
                    params_dict['tmXBMinorValues'] = self.request_dict.get('x_sub_values')
                else:
                    params_dict['tmXBMinorOn'] = False
                if self.request_dict.get('y_sub_values'):
                    params_dict['tmYLMinorValues'] = self.request_dict.get('y_sub_values')
                else:
                    params_dict['tmYLMinorOn'] = False

                params_dict['tmXBLabels'] = self.request_dict.get('x_labels')
                params_dict['tmYLLabels'] = self.request_dict.get('y_labels')
                params_dict['tiYAxisString'] = self.request_dict.get('y_left_title', "")
                y_dim = self.dims[0]
                if y_dim not in ['level', 'time']:
                    params_dict['trYReverse'] = False

        return params_dict

    def buildImage(self, output_img_path, output_img_name, output_img_type):
        im = Image.open(output_img_path + output_img_name + '.' + output_img_type, "r")
        real_pic_size = (0, 0, 1200, 947)
        im = im.crop(real_pic_size)
        return im

    def draw_polyline(self, workstation, plot, dim, value, polyline_resource=None):
        if self.dims.index(dim):  # dims包含的是[y_dim,x_dim] ,故返回1表示为此dim为x轴的坐标类型
            # 准备polyline的y轴取值范围
            yy = [Ngl.get_float(plot, 'trYMinF'), Ngl.get_float(plot, 'trYMaxF')]
            # 准备ployline的x轴取值范围
            if dim == 'time':
                value = list(self.lon).index(int(value))
            xx = [float(value), float(value)]

        else:
            # 准备polyline的x轴取值范围
            xx = [Ngl.get_float(plot, 'trXMinF'), Ngl.get_float(plot, 'trXMaxF')]
            # 准备polyline的y轴取值范围
            if dim == 'time':
                value = list(self.lat).index(int(value))
            yy = [float(value), float(value)]

            # 绘制polyline
        if not polyline_resource:
            polyline_resource = self.build_polyline_resource()
        Ngl.add_polyline(workstation, plot, xx, yy, polyline_resource)

    @DeprecationWarning
    def build_tickmack_params(self, params_dict, plot):
        params_dict['tmXBValues'] = self.request_dict.get('x_values')
        params_dict['tmYLValues'] = self.request_dict.get('y_values')
        params_dict['tmXBLabels'] = self.request_dict.get('x_labels')
        params_dict['tmYLLabels'] = self.request_dict.get('y_labels')
        # 获取坐标轴刻画位置、长度属性等
        map_attrs = ["vpXF", "vpYF", "vpWidthF", "vpHeightF", "trXMinF", "trXMaxF", "trYMinF", "trYMaxF"]
        for attr in map_attrs:
            params_dict[attr] = Ngl.get_float(plot, attr)

    def build_polyMarker_params(self, layer, params_dict):
        marker_size = layer.get('marker_size', None)
        marker_type = layer.get('marker_type', None)
        marker_thick = layer.get('marker_thick', None)
        marker_color = layer.get('marker_color', None)
        if marker_size:
            params_dict['gsMarkerSizeF'] = marker_size
        if marker_type:
            params_dict['gsMarkerIndex'] = int(marker_type)
        if marker_thick:
            params_dict['gsMarkerThicknessF'] = int(marker_thick)
        if marker_color:
            params_dict['gsMarkerColor'] = marker_color
        return params_dict
