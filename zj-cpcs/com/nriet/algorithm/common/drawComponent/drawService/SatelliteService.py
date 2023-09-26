import Ngl
from PIL import Image, ImageDraw
import os,logging
import numpy as np
from com.nriet.algorithm.common.drawComponent.drawService.CommonService import CommonService
from com.nriet.algorithm.common.drawComponent.handler import LogoHandler, TextHandler
from com.nriet.algorithm.common.drawComponent.handler.WorkstationHandler import WorkstationHandler
from com.nriet.algorithm.common.drawComponent.resourceConfig.CommonConfig import common_params_dict
from com.nriet.algorithm.common.drawComponent.resourceConfig.SatelliteConfig  import satellite_params_dict
from com.nriet.utils import StringUtils, proxyUtils
from com.nriet.utils.result.ResponseResultUtils import build_response_dict
from com.nriet.utils.obs.ObsUtils import ObsUtils
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
from com.nriet.config.PathConfig import CPCS_ROOT_PATH
class SatelliteService(CommonService):

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
        satellite_center_lon = self.request_dict.get("satellite_center_lon")
        satellite_center_lat = self.request_dict.get("satellite_center_lat")
        layers = self.request_dict['layers']
        raw_lon = self.lon.copy()

        # 1.创建workstation并且配置workstation的底板夜色  (必选)
        wk_params_dict = self.build_workstationHandler_params()
        workstation_handler = WorkstationHandler(output_img_type, temp_img_path, output_img_name,
                                                 wk_params_dict)
        workstation = workstation_handler._get_wk()

        # 2.中国等值图 （必选）
        map_plot = None
        contour_map_layer = layers[0]  # 色斑层绘图层,默认第一层
        data_source_list = []
        unit_list = []
        note_list = []

        if not 'contourMap' in [layer['layer_type'] for layer in layers]:
            logging.info("execute Pure Map layer!")
            class_name = 'MapHandler'
            map_params_dict = satellite_params_dict.get('map')
            map_params_dict['mpCenterLonF'] = (float(satellite_center_lon))
            map_params_dict['mpCenterLatF'] = (float(satellite_center_lat))
            # pre_map_dict = self.build_map_params(contour_map_layer)
            # map_params_dict.update(pre_map_dict)

            draw_handler = proxyUtils.create_class_instance(
                '.'.join(['com.nriet.algorithm.common.drawComponent.handler', class_name]), class_name,
                workstation=workstation, plot=None,
                input_data=None,
                params_dict=map_params_dict, layer=contour_map_layer, tmp_service=self)

            map_plot = draw_handler.draw()



        for i, layer in enumerate(layers):
            layer_type = layer['layer_type']

            if layer.get('data_source'):
                data_source_list.append(layer.get('data_source'))

            if layer.get('unit'):
                unit_list.append(layer.get('unit'))

            if layer.get('note'):
                note_list.append(layer.get('note'))

            # 半球模板数据和经度，需要首位相接
            if layer_type == "polyMarker":
                pass
            else:
                if(raw_lon.max()-raw_lon.min())>=350.0:
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
            params_dict = satellite_params_dict.get(layer_type)
            # 入参准备阶段--获取调用handler前的特定参数构建方法
            func = getattr(self, ''.join(['build_', layer_type, '_params']), None)
            if func:
                pre_params_dict = func(layer, params_dict)
                # polyline 特殊处理
                if layer_type == "polyline":
                    params_dict["shp"].update(pre_params_dict["shp"])
                    params_dict["rectangle"].update(pre_params_dict["rectangle"])
                    params_dict["shp_temp"].update(pre_params_dict["shp_temp"])
                else:
                    params_dict.update(pre_params_dict)
            # 动态创建Handler实例
            class_name = StringUtils.capitalize_str(layer_type) + 'Handler'
            draw_handler = proxyUtils.create_class_instance('.'.join(['com.nriet.algorithm.common.drawComponent.handler', class_name]), class_name,
                                                            workstation=workstation, plot=map_plot,
                                                            input_data=input_data[i],
                                                            params_dict=params_dict, layer=layer, tmp_service=self)
            # 调用handler绘制图层,返回唯一的、最基础的plot
            map_plot = draw_handler.draw()
        workstation_handler.plot = map_plot


        # 3.关闭workstation
        workstation_handler.close_workstation()

        # 裁剪图片大小
        im = self.buildImage(temp_img_path, output_img_name, output_img_type)
        draw = ImageDraw.Draw(im)

        # 4.绘制LOGO
        if islogo == "True":
            LogoHandler.add_logos(im, common_params_dict['logo_elements'])

        # 5.绘制Title和数据源&unit
        TextHandler.add_titles(im, draw, main_title, sub_titles, params_dict=common_params_dict['title_elements'])
        TextHandler.add_datasource_unit(im, draw, data_source_list, unit_list,
                                        params_dict=satellite_params_dict['datasource_unit'])

        # 截取长方体，争取把黑边隐藏掉
        # 因为pnyngl库绘制的时候有矩形框，只能外部加个白色框给掩盖掉
        draw.rectangle((323., 337., 2403, 2418), fill =None,outline ='white',width=3)

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
        img_width = 2700
        wk_params_dict = {
            "wkWidth": img_width
            , "wkHeight": img_width
        }
        return wk_params_dict


    def build_contour_params(self, layer=None, params_dict=None):
        if layer.get('contourFillMode'):
            params_dict['cnFillMode'] = layer.get('contourFillMode')
        if layer.get('cnLine'):
            if layer.get('cnLine') == 'True':
                params_dict['cnFillOn'] = False
                params_dict['cnLinesOn'] = True
                params_dict['cnLineLabelsOn'] = True
                # params_dict['cnLabelDrawOrder'] = 'PreDraw'
                # params_dict['cnLineDrawOrder'] = 'PreDraw'
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

    # def build_map_params(self,contour_map_layer=None,params_dict=None):
    #     map_params_dict={}
    #     map_params_dict['mpCenterLonF']= self.satellite_center_lon
    #     map_params_dict['mpCenterLatF']= self.satellite_center_lon

        return map_params_dict

    def build_vector_params(self, layer=None,params_dict=None):
        params_dict = {}
        # end_lat, end_lon, start_lat, start_lon = self.get_start_end(layer)
        #
        # lon_range = end_lon - start_lon
        # lat_range = end_lat - start_lat
        # params_dict['trXMinF'] = start_lon
        # params_dict['trXMaxF'] = end_lon
        # params_dict['trYMinF'] = start_lat
        # params_dict['trYMaxF'] = end_lat
        # params_dict['vpHeightF'] = 0.817204 / (lon_range / lat_range),
        # params_dict['vfXCStartV'] = start_lon
        # params_dict['vfXCEndV'] = end_lon
        # params_dict['vfYCStartV'] = start_lat
        # params_dict['vfYCEndV'] = end_lat
        # params_dict['vcRefAnnoString1'] = layer.get('vector_unit')
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
        return params_dict

    def build_streamLine_params(self, layer=None,param=None):
        params_dict = {}
        # end_lat, end_lon, start_lat, start_lon = self.get_start_end(layer)
        #
        # lon_range = end_lon - start_lon
        # lat_range = end_lat - start_lat
        # params_dict['trXMinF'] = start_lon
        # params_dict['trXMaxF'] = end_lon
        # params_dict['trYMinF'] = start_lat
        # params_dict['trYMaxF'] = end_lat
        # params_dict['vpHeightF'] = 0.817204 / (lon_range / lat_range),
        # params_dict['vfXCStartV'] = start_lon
        # params_dict['vfXCEndV'] = end_lon
        # params_dict['vfYCStartV'] = start_lat
        # params_dict['vfYCEndV'] = end_lat
        if layer.get('stLineSpace'):
            params_dict['stLineStartStride']=layer.get('stLineSpace')
        if layer.get('stArrowSpace'):
            params_dict['stArrowStride'] = layer.get('stArrowSpace')
        return params_dict


    def build_polyMarker_params(self,layer,params_dict=None):
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


    def buildImage(self, output_img_path, output_img_name, output_img_type):
        im = Image.open(output_img_path + output_img_name + '.' + output_img_type, "r")
        # real_pic_size = (0, 0, 930, 930 * (latRange / lonRange) + 130)
        # im = im.crop(real_pic_size)
        return im
