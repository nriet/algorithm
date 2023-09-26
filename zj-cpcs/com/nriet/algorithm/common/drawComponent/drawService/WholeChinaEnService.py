import Ngl
from PIL import ImageDraw, Image
import os,logging
import numpy as np
from com.nriet.algorithm.common.drawComponent.drawService.CommonService import CommonService
from com.nriet.algorithm.common.drawComponent.handler import LogoHandler, TextHandlerEn
from com.nriet.algorithm.common.drawComponent.handler.GeoHandler import GeoHandler
from com.nriet.algorithm.common.drawComponent.handler.LabelBarHandler import LabelBarHandler
from com.nriet.algorithm.common.drawComponent.handler.SouthSeaHandlerEn import SouthSeaHandlerEn
from com.nriet.algorithm.common.drawComponent.handler.WorkstationHandler import WorkstationHandler
from com.nriet.algorithm.common.drawComponent.resourceConfig.ChinaConfig import china_params_dict
from com.nriet.utils import StringUtils, proxyUtils
from com.nriet.config.PathConfig import CPCS_ROOT_PATH
from com.nriet.utils.result.ResponseResultUtils import build_response_dict
from com.nriet.utils.obs.ObsUtils import ObsUtils
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
class WholeChinaEnService(CommonService):

    def draw(self):
        # 0.参数准备
        input_data = self.input_data
        # 是否绘制logo 默认绘制  绘制：True  不绘制：False
        islogo = self.request_dict.get("islogo", "True")
        save_to_nfsshare_switch = look_for_single_global_config("SAVE_TO_NFSSHARE_SWITCH")
        save_to_obs_switch = look_for_single_global_config("SAVE_TO_OBS_SWITCH")
        output_img_type = self.request_dict["output_img_type"]
        temp_img_path = CPCS_ROOT_PATH + "com/nriet/test/"
        output_img_path = self.request_dict["output_img_path"]
        output_img_name = self.request_dict["output_img_name"]
        expire = self.request_dict.get("expire")
        main_title = self.request_dict["main_title"]
        main_title_size = self.request_dict.get("main_title_size")
        sub_titles_size = self.request_dict.get("sub_titles_size")
        sub_titles = self.request_dict.get("sub_titles")
        layers = self.request_dict['layers']

        # 1.创建workstation并且配置workstation的底板夜色  (必选)
        wk_params_dict = self.build_workstationHandler_params()
        workstation_handler = WorkstationHandler(output_img_type, temp_img_path, output_img_name,
                                                 wk_params_dict)
        workstation = workstation_handler._get_wk()

        # 2.中国多业务图层绘制
        map_plot = None
        first_layer = layers[0]  # 默认第一层存在图例
        data_source_list = []
        note_list = []


        if not 'contourMap' in [layer['layer_type'] for layer in layers]:
            logging.info("execute Pure Map layer!")
            class_name = 'MapHandler'
            map_params_dict = china_params_dict.get('map')
            pre_map_dict = self.build_map_params(None)
            map_params_dict.update(pre_map_dict)

            draw_handler = proxyUtils.create_class_instance(
                '.'.join(['com.nriet.algorithm.common.drawComponent.handler', class_name]), class_name,
                workstation=workstation, plot=None,
                input_data=None,
                params_dict=map_params_dict, layer=first_layer, tmp_service=self)

            map_plot = draw_handler.draw()




        for i, layer in enumerate(layers):
            layer_type = layer['layer_type']
            if layer_type == 'contourMap':
                first_layer = layer
            if layer.get('data_source'):
                data_source_list.append(layer.get('data_source'))
            if layer.get('note'):
                note_list.append(layer.get('note'))

            # 入参准备阶段--获取模板配置
            params_dict = china_params_dict.get(layer_type)
            # 入参准备阶段--获取调用handler前的特定参数构建方法
            func = getattr(self, ''.join(['build_', layer_type, '_params']), None)
            if func:
                pre_params_dict = func(layer)
                # polyline 特殊处理
                if layer_type == "polyline":
                    params_dict["shp"].update(pre_params_dict["shp"])
                    params_dict["rectangle"].update(pre_params_dict["rectangle"])
                    params_dict["shp_temp"].update(pre_params_dict["shp_temp"])
                else:
                    params_dict.update(pre_params_dict)

            # 动态创建实例
            class_name = StringUtils.capitalize_str(layer['layer_type']) + 'Handler'
            draw_handler = proxyUtils.create_class_instance(
                '.'.join(['com.nriet.algorithm.common.drawComponent.handler', class_name]), class_name,
                workstation=workstation, plot=map_plot,
                input_data=input_data[i],
                params_dict=params_dict,
                layer=layer, tmp_service=self)
            # 调用handler绘制图层,返回唯一的、最基础的plot
            map_plot = draw_handler.draw()
        workstation_handler.plot = map_plot

        # 3.边界线绘制（可选）
        geoline_handler = GeoHandler(workstation, map_plot,
                                     params_dict=china_params_dict.get('geo'), tmp_service=self)
        geoline_handler.draw()


        # 4.添加中国图例(图例当且仅当绘制色斑图的时候才有)
        if first_layer.get('cnLine'): # 绘制等值线时不添加图例
            if first_layer.get('cnLine') == 'True':
                pass
            else:
                label_bar_handler = LabelBarHandler(workstation, map_plot,
                                                    params_dict=china_params_dict.get('label_bar'), layer=first_layer,
                                                    tmp_service=self)
                label_bar_handler.draw()
        else:
            label_bar_handler = LabelBarHandler(workstation, map_plot,
                                                params_dict=china_params_dict.get('label_bar'), layer=first_layer,
                                                tmp_service=self)
            label_bar_handler.draw()




        # 5.南海相关
        south_sea_handler = SouthSeaHandlerEn(workstation, map_plot, input_data,
                                            china_params_dict.get('south_sea'), layers, self)
        south_sea_handler.draw()

        # 6.关闭workstation
        workstation_handler.close_workstation()

        im = self.buildImage(temp_img_path, output_img_name, output_img_type)
        draw = ImageDraw.Draw(im)
        # 新绘图修改
        # 7.绘制logo
        if islogo == "True":
            LogoHandler.add_logos(im, china_params_dict['logo_elements'])
        # 8.绘制多级标题
        params_dict = china_params_dict['title_elements']
        if main_title_size:
            params_dict["font_main_size"] = int(main_title_size)
        if sub_titles_size:
            params_dict["font_sub_size"] = int(sub_titles_size)
        TextHandlerEn.add_titles(im, draw, main_title, sub_titles, params_dict)
        # 结束
        # 9.绘制比例尺
        # TextHandler.add_scale(draw, china_params_dict['scale'])
        # 10.绘制中文图例
        unit = first_layer.get('unit', '')  # 缺省配置为'单位'

        # 10.1 绘制中文数据源
        note_list.extend(data_source_list)
        if first_layer.get('cnLine'): # 绘制等值线时添加单位
            if first_layer.get('cnLine') == 'True':
                if first_layer.get('unit'):
                    note_list.append(first_layer.get('unit'))
        TextHandlerEn.add_datasource(im, draw, note_list,
                                        params_dict=china_params_dict['datasource'])

        colors = first_layer.get('colors')
        if first_layer.get('cnLine'): # 绘制等值线时不添加单位
            if first_layer.get('cnLine')=='True':
                pass
            else:
                TextHandlerEn.add_legend_unit(im, draw, nboxes=len(colors), unit=unit,
                                    params_dict=china_params_dict['legend_unit'])
        else:
            TextHandlerEn.add_legend_unit(im, draw, nboxes=len(colors), unit=unit,
                                        params_dict=china_params_dict['legend_unit'])
        # 11.叠加中国中文掩膜
        # 新绘图修改
        # img2 = Image.open(CPCS_ROOT_PATH+"com/nriet/algorithm/common/drawComponent/imgFiles/china_test.png")
        # 结束
        # im.paste(img2, (0, 0, img2.size[0], img2.size[1]), img2)

        # 12.保存
        if int(save_to_nfsshare_switch) or self.request_dict.get("saveToNfsshare"):
            im.save(output_img_path + output_img_name + '.' + output_img_type)

        # 是否上传至obs
        if int(save_to_obs_switch) or self.request_dict.get("saveToObs"):
            storage_result = ObsUtils().img_save_to_obs(im, output_img_name, output_img_type)

        # 删除临时文件
        try:
            os.remove(temp_img_path + output_img_name + '.' + output_img_type)
        except FileNotFoundError:
            pass
        logging.info("             delete temp file %s" % temp_img_path + output_img_name + '.' + output_img_type)

        return build_response_dict()

    def build_workstationHandler_params(self):
        # img_width, img_height = (float(x) for x in self.request_dict["output_img_max_width"].split("x"))  # 输出图片的长宽像素
        # 新绘图修改
        img_width = 2800
        # 结束
        wk_params_dict = {
            "wkWidth": img_width
            , "wkHeight": img_width
        }
        return wk_params_dict

    def buildImage(self, output_img_path, output_img_name, output_img_type):
        im = Image.open(output_img_path + output_img_name + '.' + output_img_type, "r")
        # img_width, img_height = (float(x) for x in self.request_dict["output_img_max_width"].split("x"))
        # 新绘图修改
        img_width = 2800
        img_height = 2095
        # 结束

        real_pic_size = (0, (img_width - img_height) / 2, img_width, (img_width + img_height) / 2)
        im = im.crop(real_pic_size)
        return im

    def build_vector_params(self, layer=None):
        params_dict = {}
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
        # 动态改变风场矩形图例位置
        vector_height = (10-696)/696 
        if 'contourMap' in [layer.get('layer_type') for layer in self.request_dict.get('layers')]:
            nboxes = len(self.request_dict.get('layers')[0].get('colors'))
            lb_height = 930 * 0.022 * 0.868 * (nboxes + 3 - (nboxes - 5) / 2.8) + 0.035 * 930 * 96 / 72 / 4
            vector_height = (lb_height+10-696)/696

        params_dict['vcRefAnnoOrthogonalPosF']= vector_height


        return params_dict

    def build_contourMap_params(self, layer):
        contour_params_dict = {}
        # 栅格图显示
        if layer.get('contourFillMode'):
            contour_params_dict['cnFillMode'] = layer.get('contourFillMode')
        if layer.get('cnLine'):
            if layer.get('cnLine')=='True':
                contour_params_dict['cnFillOn'] = False
                contour_params_dict['cnLinesOn'] = True
                contour_params_dict['cnLineLabelsOn'] = True
                contour_params_dict['cnLabelDrawOrder'] = 'PreDraw'
                contour_params_dict['cnLineDrawOrder'] = 'PreDraw'
                if layer.get('intervals', None):
                    contour_params_dict['cnLevels'] = np.array(layer.get('intervals'))

                if layer.get('contour_line_space', None):
                    contour_params_dict['cnLevelSpacingF'] = float(layer.get('contour_line_space'))

                if layer.get('contour_line_color', None):
                    contour_params_dict['cnLineColor'] = layer.get('contour_line_color')

                if layer.get('contour_line_colors', None):
                    contour_params_dict['cnLineColors'] = layer.get('contour_line_colors')

                if layer.get('line_thickness', None):
                    contour_params_dict['cnLineThicknessF'] = layer.get('line_thickness')

                if layer.get('line_thicknesses', None):
                    contour_params_dict['cnMonoLineThickness'] = False
                    contour_params_dict['cnLineThicknesses'] = layer.get('line_thicknesses')

                if layer.get('cnLineMax', None):
                    contour_params_dict['cnLevelSelectionMode'] = 'ManualLevels'
                    contour_params_dict['cnMaxLevelValF'] = layer.get('cnLineMax')

                if layer.get('cnLineMin', None):
                    contour_params_dict['cnLevelSelectionMode'] = 'ManualLevels'
                    contour_params_dict['cnMinLevelValF'] = layer.get('cnLineMin')

                if layer.get('cnLabelSize', None):
                    contour_params_dict['cnLineLabelFontHeightF'] = layer.get('cnLabelSize')


        return contour_params_dict

    def build_map_params(self,layer):

        return  {}

    def build_polyline_params(self,layer):
        params_dict = {}
        rectangle_resource_params = {}
        polyline_resource_params = {}
        shape_template_params = {}
        if layer.get('rectangle_list'):
            # 如有多边框需求
            if layer.get("rectangle_color"):
                rectangle_resource_params['gsLineColor'] = layer.get("rectangle_color")
            if layer.get("rectangle_thickness"):
                rectangle_resource_params['gsLineThicknessF'] = float(layer.get("rectangle_thickness"))
            if layer.get("rectangle_dashPattern"):
                rectangle_resource_params['gsLineDashPattern'] = float(layer.get("rectangle_dashPattern"))

        # 如有多polyline需求
        if layer.get('polyline_files'):
            if layer.get("polyline_color"):
                polyline_resource_params['gsLineColor'] = layer.get("polyline_color")
            if layer.get("polyline_thickness"):
                polyline_resource_params['gsLineThicknessF'] = float(layer.get("polyline_thickness"))
            if layer.get("polyline_dashPattern"):
                rectangle_resource_params['gsLineDashPattern'] = float(layer.get("polyline_dashPattern"))

        # 如有一组自定义模板的shp需求。如一带一路这一套的模板
        if layer.get("shape_template"):
            if layer.get("shape_template_color"):
                shape_template_params['gsLineColor'] = layer.get("shape_template_color")
            if layer.get("shape_template_thickness"):
                shape_template_params['gsLineThicknessF'] = float(layer.get("shape_template_thickness"))
            if layer.get("shape_template_dashPattern"):
                shape_template_params['gsLineDashPattern'] = float(layer.get("shape_template_dashPattern"))

        params_dict['rectangle'] = rectangle_resource_params
        params_dict['shp'] = polyline_resource_params
        params_dict['shp_temp'] = shape_template_params

        return params_dict

    def build_polyMarker_params(self,layer):
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