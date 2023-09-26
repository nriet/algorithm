import Ngl
from PIL import Image, ImageDraw
import os
import numpy as np
from com.nriet.algorithm.common.drawComponent.drawService.CommonService import CommonService
from com.nriet.algorithm.common.drawComponent.handler import LogoHandler, TextHandler
from com.nriet.algorithm.common.drawComponent.handler.WorkstationHandler import WorkstationHandler
from com.nriet.algorithm.common.drawComponent.resourceConfig.CommonConfig import common_params_dict
from com.nriet.algorithm.common.drawComponent.resourceConfig.HemisphereConfig import hemisphere_params_dict
from com.nriet.utils import StringUtils, proxyUtils
from com.nriet.algorithm.common.drawComponent.handler.GlobalLabelBarHandler import GlobalLabelBarHandler
from com.nriet.algorithm.common.drawComponent.handler.GeoHandler import GeoHandler
from com.nriet.utils.result.ResponseResultUtils import build_response_dict
from com.nriet.utils.obs.ObsUtils import ObsUtils
from com.nriet.config.PathConfig import CPCS_ROOT_PATH
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
import logging
class HemisphereService(CommonService):

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
        # 是否绘制北极(南极)投影纬度标签 默认不绘制 绘制:True(bool) 不绘制:False
        hemisphere_lat_labels = self.request_dict.get("hemisphere_lat_labels", False)
        layers = self.request_dict['layers']
        raw_lon = self.lon.copy()

        # 1.创建workstation并且配置workstation的底板夜色  (必选)
        wk_params_dict = self.build_workstationHandler_params()
        workstation_handler = WorkstationHandler(output_img_type, temp_img_path, output_img_name,
                                                 wk_params_dict)
        workstation = workstation_handler._get_wk()

        # 2.中国等值图 （必选）
        map_plot = None
        contour_map_layer = layers[0]
        data_source_list = []
        unit_list = []

        if not 'contourMap' in [layer['layer_type'] for layer in layers]:
            logging.info("execute Pure Map layer!")
            class_name = 'MapHandler'
            map_params_dict = hemisphere_params_dict.get('map')
            if layers[0].get("draw_regions"):  # 最低纬度
                min_lon, max_lon, min_lat, max_lat = layers[0].get("draw_regions").split(",")
                if StringUtils.judge_str_is_number(min_lat):
                    map_params_dict['mpMinLatF'] = float(min_lat)  # 北极
                elif StringUtils.judge_str_is_number(max_lat):
                    map_params_dict['mpMaxLatF'] = float(max_lat)  # 南极
                    map_params_dict['mpMinLatF'] = -90.
                    map_params_dict['mpCenterLatF'] = -90.
            # 绘制纬度标签，获取纬度最大值和最小值
            if hemisphere_lat_labels:
                min_lat_tmp = map_params_dict["mpMinLatF"]
                max_lat_tmp = map_params_dict["mpMaxLatF"]
            draw_handler = proxyUtils.create_class_instance(
                '.'.join(['com.nriet.algorithm.common.drawComponent.handler', class_name]), class_name,
                workstation=workstation, plot=None,
                input_data=None,
                params_dict=map_params_dict, layer=contour_map_layer, tmp_service=self)

            map_plot = draw_handler.draw()
        for i, layer in enumerate(layers):
            layer_type = layer['layer_type']
            if layer_type == 'contourMap':
                contour_map_layer = layer
            if layer.get('data_source'):
                data_source_list.append(layer.get('data_source'))

            if layer.get('note'):
                data_source_list.append(layer.get('note'))

            if layer.get('unit'):
                unit_list.append(layer.get('unit'))

            # 半球模板数据和经度，需要首位相接
            if layer_type == "polyMarker":
                pass
            else:
                if (raw_lon.max() - raw_lon.min()) >= 350.0:
                    if isinstance(input_data[i], list):
                        cycle_data = []
                        for data_index, layer_data in enumerate(input_data[i]):
                            cycle_layer_data, cycle_lon = Ngl.add_cyclic(layer_data, raw_lon)
                            cycle_data.append(cycle_layer_data)
                    else:
                        cycle_data, cycle_lon = Ngl.add_cyclic(input_data[i], raw_lon)
                    input_data[i] = cycle_data
                    self.lon_indexes = self.lon = cycle_lon

            # 入参准备阶段--获取模板配置
            params_dict = hemisphere_params_dict.get(layer_type)
            # 入参准备阶段--获取调用handler前的特定参数构建方法
            func = getattr(self, ''.join(['build_', layer_type, '_params']), None)
            if func:
                params_dict = func(layer, params_dict)
            # 绘制纬度标签，获取纬度最大值和最小值
            if layer_type == 'contourMap' and hemisphere_lat_labels:
                min_lat_tmp = params_dict["mpMinLatF"]
                max_lat_tmp = params_dict["mpMaxLatF"]
            # 动态创建Handler实例
            class_name = StringUtils.capitalize_str(layer_type) + 'Handler'
            draw_handler = proxyUtils.create_class_instance('.'.join(['com.nriet.algorithm.common.drawComponent.handler', class_name]), class_name,
                                                            workstation=workstation, plot=map_plot,
                                                            input_data=input_data[i],
                                                            params_dict=params_dict, layer=layer, tmp_service=self)
            # 调用handler绘制图层,返回唯一的、最基础的plot
            map_plot = draw_handler.draw()
        workstation_handler.plot = map_plot

        # 3.0 边界线绘制
        geoline_handler = GeoHandler(workstation, map_plot,
                                     params_dict=hemisphere_params_dict.get('geo'), tmp_service=self)
        geoline_handler.draw()

        # 画4个点的经度显示值
        workstation_handler.add_lon_labels()
        # 在0度经线上绘制纬度标签(仅在北半球或南半球纬度范围内绘制)
        if hemisphere_lat_labels:
            if (min_lat_tmp == -90 and max_lat_tmp <= 0) or (max_lat_tmp == 90 and min_lat_tmp >= 0):
                workstation_handler.add_lat_labels(min_lat_tmp, max_lat_tmp)

        # 绘制图例
        if contour_map_layer['layer_type'] == 'contourMap':
            if contour_map_layer.get('cnLine') == 'True' or contour_map_layer.get('cnLine'):
                pass
            else:
                label_bar_handler = GlobalLabelBarHandler(workstation, map_plot,
                                                          params_dict=hemisphere_params_dict.get('label_bar_global'),
                                                          layer=contour_map_layer, tmp_service=self)
                label_bar_handler.draw()

        # 3.关闭workstation
        workstation_handler.close_workstation()

        # 裁剪图片大小
        im = self.buildImage(temp_img_path, output_img_name, output_img_type)
        draw = ImageDraw.Draw(im)

        # 4.绘制LOGO
        if islogo =="True":
            LogoHandler.add_logos(im, common_params_dict['logo_elements'])

        # 5.绘制Title和数据源&unit
        if len(sub_titles) == 1:
            TextHandler.add_titles(im, draw, main_title, sub_titles, params_dict=common_params_dict['title_elements'])
        else:
            TextHandler.add_titles(im, draw, main_title, sub_titles, params_dict=hemisphere_params_dict['title_elements'])
        TextHandler.add_datasource_unit(im, draw, data_source_list, unit_list,
                                        params_dict=hemisphere_params_dict['datasource_unit'])

        # 加个黑圈圈 706.8‬
        # draw.ellipse((111.9, 115., 819.9, 823), fill =None,outline ='black',width=2)
        draw.ellipse((332, 348., 2465, 2478), fill =None,outline ='black',width=4)

        # 6.保存
        # 是否上传nfsshare
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
                storage_result = ObsUtils().img_save_to_obs(im, output_img_name, output_img_type,expire)

        # 删除临时文件
        try:
            os.remove(temp_img_path + output_img_name + '.' + output_img_type)
        except FileNotFoundError:
            pass
        logging.info("             delete temp file %s" % temp_img_path + output_img_name + '.' + output_img_type)
        return build_response_dict()

    def build_workstationHandler_params(self):
        # imgWidth, imgHeight = (float(x) for x in self.request_dict['output_img_max_width'].split("x"))  # 输出图片的长宽像素
        img_width = int(self.request_dict.get('output_img_max_width', 930))
        img_width = 2800
        wk_params_dict = {
            "wkWidth": img_width
            , "wkHeight": img_width
        }
        return wk_params_dict

    def build_contourMap_params(self, layer=None, params_dict=None):
        if params_dict:
            if layer.get("draw_regions"): #最低纬度
                min_lon,max_lon,min_lat,max_lat = layer.get("draw_regions").split(",")
                if StringUtils.judge_str_is_number(min_lat):
                    params_dict['mpMinLatF'] = float(min_lat) # 北极
                elif StringUtils.judge_str_is_number(max_lat):
                    params_dict['mpMaxLatF'] = float(max_lat) # 南极
                    params_dict['mpMinLatF'] = -90.
                    params_dict['mpCenterLatF'] = -90.
            if layer.get('contourFillMode'):
                params_dict['cnFillMode'] = layer.get('contourFillMode')
            if layer.get('cnLine'):
                if layer.get('cnLine') == 'True':
                    params_dict['cnFillOn'] = False
                    params_dict['cnLinesOn'] = True
                    params_dict['cnLineLabelsOn'] = True
                    params_dict['cnLabelDrawOrder'] = 'PreDraw'
                    params_dict['cnLineDrawOrder'] = 'PreDraw'
                    if layer.get('intervals', None):
                        params_dict['cnLevels'] = np.array(layer.get('intervals'))
                        lineLabels = []
                        for inv in layer.get('intervals'):
                            if str(inv).endswith(".0"):
                                lineLabels.append(str(int(inv)))
                            else:
                                lineLabels.append(str(inv))
                        params_dict['cnLineLabelStrings'] = lineLabels
                        params_dict['cnExplicitLineLabelsOn'] = True

                    if layer.get('contour_line_space', None):
                        params_dict['cnLevelSpacingF'] = float(layer.get('contour_line_space'))

                    if layer.get('contour_line_color', None):
                        params_dict['cnLineColor'] = layer.get('contour_line_color')

                    if layer.get('contour_line_colors', None):
                        params_dict['cnLineColors'] = layer.get('contour_line_colors')

                    if layer.get('line_thickness', None):
                        params_dict['cnLineThicknessF'] = layer.get('line_thickness')

                    if layer.get('line_thicknesses', None):
                        params_dict['cnMonoLineThickness'] = False
                        params_dict['cnLineThicknesses'] = layer.get('line_thicknesses')

                    if layer.get('cnLineMax', None):
                        params_dict['cnLevelSelectionMode'] = 'ManualLevels'
                        params_dict['cnMaxLevelValF'] = layer.get('cnLineMax')

                    if layer.get('cnLineMin', None):
                        params_dict['cnLevelSelectionMode'] = 'ManualLevels'
                        params_dict['cnMinLevelValF'] = layer.get('cnLineMin')

                    if layer.get('cnLabelSize', None):
                        params_dict['cnLineLabelFontHeightF'] = layer.get('cnLabelSize')
        return params_dict

    def build_contour_params(self, layer=None, params_dict=None):
        params_dict['cnLabelDrawOrder'] = 'PostDraw'
        params_dict['cnLineDrawOrder'] = 'PostDraw'
        if layer.get('intervals', None):
            params_dict['cnLevels'] = np.array(layer.get('intervals'))

        if layer.get('contour_line_space', None):
            params_dict['cnLevelSpacingF'] = float(layer.get('contour_line_space'))

        if layer.get('contour_line_color', None):
            params_dict['cnLineColor'] = layer.get('contour_line_color')

        if layer.get('contour_line_colors', None):
            params_dict['cnLineColors'] = layer.get('contour_line_colors')

        if layer.get('line_thickness', None):
            params_dict['cnLineThicknessF'] = layer.get('line_thickness')

        if layer.get('line_thicknesses', None):
            params_dict['cnMonoLineThickness'] = False
            params_dict['cnLineThicknesses'] = layer.get('line_thicknesses')

        if layer.get('cnLineMax', None):
            params_dict['cnLevelSelectionMode'] = 'ManualLevels'
            params_dict['cnMaxLevelValF'] = layer.get('cnLineMax')

        if layer.get('cnLineMin', None):
            params_dict['cnLevelSelectionMode'] = 'ManualLevels'
            params_dict['cnMinLevelValF'] = layer.get('cnLineMin')

        if layer.get('cnLabelSize', None):
            params_dict['cnLineLabelFontHeightF'] = layer.get('cnLabelSize')
        return params_dict

    def buildImage(self, output_img_path, output_img_name, output_img_type):
        im = Image.open(output_img_path + output_img_name + '.' + output_img_type, "r")
        # real_pic_size = (0, 0, 930, 930 * (latRange / lonRange) + 130)
        # im = im.crop(real_pic_size)
        return im

    def build_vector_params(self, layer=None, params_dict=None):
        params_dict['vcRefAnnoString1'] = layer.get('vector_unit')
        if layer.get('vector_scale'):
            params_dict['vcRefAnnoString2'] = layer.get('vector_scale')
            params_dict['vcRefMagnitudeF'] = float(layer.get('vector_scale'))
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
        # 矢量风箭头样式
        if layer.get('vector_style'):
            params_dict['vcGlyphStyle'] = layer.get('vector_style')
            # 纯箭头和空心箭头参数设置相同，但空心箭头和纯箭头箭头大小不一致，配置文件以纯箭头为准，故空心箭头大小需重新设置
            if params_dict['vcGlyphStyle'] == "LineArrow":
                params_dict['vcLineArrowHeadMaxSizeF'] = 0.010
                params_dict['vcLineArrowHeadMinSizeF'] = 0.006
        # 矢量风风速显示范围
        if layer.get("vector_min"):
            params_dict['vcMinMagnitudeF'] = layer.get("vector_min")
        if layer.get("vector_max"):
            params_dict['vcMaxMagnitudeF'] = layer.get("vector_max")
        return params_dict

    def build_polyMarker_params(self, layer, params_dict=None):
        params_dict = {}
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