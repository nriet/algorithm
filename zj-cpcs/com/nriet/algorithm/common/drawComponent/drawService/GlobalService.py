import Ngl
import numpy as np
from PIL import ImageFont
from PIL import Image, ImageDraw
from com.nriet.config import PathConfig
import math, os,logging
from com.nriet.algorithm.common.drawComponent.drawService.CommonService import CommonService
from com.nriet.algorithm.common.drawComponent.handler import LogoHandler, TextHandler
from com.nriet.algorithm.common.drawComponent.handler.TickMackHandler import TickMackHandler
from com.nriet.algorithm.common.drawComponent.handler.WorkstationHandler import WorkstationHandler
from com.nriet.algorithm.common.drawComponent.handler.GlobalLabelBarHandler import GlobalLabelBarHandler
from com.nriet.algorithm.common.drawComponent.handler.GeoHandler import GeoHandler
from com.nriet.algorithm.common.drawComponent.resourceConfig.CommonConfig import common_params_dict
from com.nriet.algorithm.common.drawComponent.resourceConfig.GlobalConfig import global_params_dict
from com.nriet.utils import StringUtils, proxyUtils
from com.nriet.utils.result.ResponseResultUtils import build_response_dict
from com.nriet.utils.StringUtils import judge_str_is_number
from com.nriet.utils.obs.ObsUtils import ObsUtils
from com.nriet.config.PathConfig import CPCS_ROOT_PATH
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config


class GlobalService(CommonService):

    def draw(self):
        # 0.参数准备
        input_data = self.input_data
        # 是否绘制logo 默认绘制  绘制：True  不绘制：False
        islogo = self.request_dict.get("islogo", "True")
        # islogo = "False"
        output_img_type = self.request_dict["output_img_type"]
        output_img_path = self.request_dict["output_img_path"]
        output_img_name = self.request_dict["output_img_name"]
        expire = self.request_dict.get("expire")
        temp_img_path = CPCS_ROOT_PATH + "com/nriet/test/"
        main_title = self.request_dict["main_title"]
        sub_titles = self.request_dict.get("sub_titles")
        layers = self.request_dict['layers']
        isProvince = self.request_dict.get("isProvince", False)

        # 1.创建workstation并且配置workstation的底板夜色  (必选)
        wk_params_dict = self.build_workstationHandler_params()
        # 纬度范围和经度范围比值
        rate = (np.max(self.lat) - np.min(self.lat)) / (np.max(self.lon) - np.min(self.lon))
        # 经纬度范围相等时，图片高度设置为3100
        if rate == 1:
            wk_params_dict['wkHeight'] = 3100
        workstation_handler = WorkstationHandler(output_img_type, temp_img_path, output_img_name,
                                                 wk_params_dict)
        workstation = workstation_handler._get_wk()

        # 2.全球任意经纬度多业务图层绘制
        map_plot = None
        contour_map_layer = layers[0]  # 色斑层绘图层,默认第一层
        data_source_list = []
        unit_list = []
        note_list = []

        if not 'contourMap' in [layer['layer_type'] for layer in layers]:
            logging.info("execute Pure Map layer!")
            class_name = 'MapHandler'
            map_params_dict = global_params_dict.get('map')
            pre_map_dict = self.build_map_params(contour_map_layer)
            map_params_dict.update(pre_map_dict)

            # 经纬度范围相等时，调整图表位置
            if rate == 1 and map_params_dict.get('vpYF'):
                map_params_dict['vpYF'] = 0.95
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
            if layer.get('unit'):
                unit_list.append(layer.get('unit'))
            if layer.get('note'):
                note_list.append(layer.get('note'))

            # 入参准备阶段--获取模板配置
            params_dict = global_params_dict.get(layer_type)
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

            # 动态创建Handler实例
            class_name = StringUtils.capitalize_str(layer_type) + 'Handler'
            # 经纬度范围相等时，调整图表位置
            if rate == 1 and params_dict.get('vpYF'):
                params_dict['vpYF'] = 0.95
            draw_handler = proxyUtils.create_class_instance(
                '.'.join(['com.nriet.algorithm.common.drawComponent.handler', class_name]), class_name,
                workstation=workstation, plot=map_plot,
                input_data=input_data[i],
                params_dict=params_dict, layer=layer, tmp_service=self)
            # 调用handler绘制图层,返回唯一的、最基础的plot
            map_plot = draw_handler.draw()
        workstation_handler.plot = map_plot

        # 3.0 边界线绘制
        if isProvince is False:
            if global_params_dict.get('geo').get('lake') is not None:
                del global_params_dict.get('geo')["lake"]
                del global_params_dict.get('geo')["province"]
                del global_params_dict.get('geo')["HongKong"]
        geoline_handler = GeoHandler(workstation, map_plot,
                                     params_dict=global_params_dict.get('geo'), tmp_service=self)
        geoline_handler.draw()

        # 绘制坐标轴
        global_tickmack_dict = global_params_dict.get('tickmack')
        self.build_tickMack_params(global_tickmack_dict, map_plot)
        tickmack_handler = TickMackHandler(workstation, map_plot, params_dict=global_tickmack_dict, tmp_service=self)
        tickmack_handler.add_map_tickmarks()

        # 绘制图例
        if contour_map_layer['layer_type'] == 'contourMap':
            global_label_bar_dict = global_params_dict.get('label_bar_global')
            # 经纬度范围相等时，调整图例位置
            if rate == 1:
                global_label_bar_dict['labelbar_location']['amOrthogonalPosF'] = 0.6
            label_bar_handler = GlobalLabelBarHandler(workstation, map_plot,
                                                      params_dict=global_label_bar_dict,
                                                      layer=contour_map_layer, tmp_service=self)
            label_bar_handler.draw()
        # 3.1 关闭workstation
        workstation_handler.close_workstation()

        # 裁剪图片大小
        im = self.buildImage(temp_img_path, output_img_name, output_img_type, contour_map_layer)
        draw = ImageDraw.Draw(im)

        # 4.绘制LOGO
        if islogo =="True":
            LogoHandler.add_logos(im, common_params_dict['logo_elements'])

        # 如果绘制台风轨迹则添加台风图例
        if contour_map_layer['layer_type'] == 'polyMarkerLine':
            # 新绘图修改
            img2 = Image.open(CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/imgFiles/typhoon_ver.png")
            img2_x, img2_y = img2.size
            # 台风图例放大
            img2 = img2.resize((int(img2_x * 3), int(img2_y * 3)), Image.ANTIALIAS)
            # 结束
            im.paste(img2, (int(im.size[0] / 2 - img2.size[0] / 2), im.size[1] - img2.size[1] - 100), img2)
            # 添加台风名称
            font_file = PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC"
            font = ImageFont.truetype(font=font_file, size=24)
            lats = self.station_lat
            lons = self.station_lon
            end_lat, end_lon, start_lat, start_lon = self.get_start_end(layer)
            name = 0
            names = layer.get("line_name")
            for index, lon in enumerate(lons):
                if index == 0:
                    name = name + 1
                    draw.text(
                        (0.866 * 2800 * (lon - start_lon) / (end_lon - start_lon) + 0.083 * 2800 - 10 + 10,
                         0.866 * 2800 * (end_lat - lats[index]) / (end_lon - start_lon) + 2800 * (1 - 0.892473) + 3 - 30),
                        names[name - 1], font=font, fill='black')
                if index > 0 and lons[index] < 500 and lons[index - 1] > 500:
                    name = name + 1
                    draw.text(
                        (0.866 * 2800 * (lon - start_lon) / (end_lon - start_lon) + 0.083 * 2800 - 10 + 10,
                         0.866 * 2800 * (end_lat - lats[index]) / (end_lon - start_lon) + 2800 * (1 - 0.892473) + 3 - 30),
                        names[name - 1], font=font, fill='black')

        # 若打点图层含有legend_labels时，需要标注中文
        if contour_map_layer.get('legend_labels'):
            TextHandler.add_legends(im, draw, contour_map_layer['legend_labels'], common_params_dict['title_elements'])
        # 若图层含有ch_legend_labels时，需要标注中文
        if contour_map_layer.get('ch_legend_labels'):
            TextHandler.add_gl_common_legends(im, draw, contour_map_layer['ch_legend_labels'],
                                    common_params_dict['title_elements'],
                                              global_params_dict.get('label_bar_global').get('vpWidthF'),
                                              contour_map_layer.get('isNaN'))
        # 5.绘制Title和数据源&unit
        if len(sub_titles) == 1:
            TextHandler.add_titles(im, draw, main_title, sub_titles,
                                   params_dict=common_params_dict['title_elements'])
        else:
            TextHandler.add_titles(im, draw, main_title, sub_titles, params_dict=global_params_dict['title_elements'])

        TextHandler.add_datasource_unit(im, draw, data_source_list, unit_list, note_list,
                                        params_dict=global_params_dict['datasource_unit'])
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
        # img_width = int(self.request_dict.get('output_img_max_width', 2700))
        img_width = 2800
        wk_params_dict = {
            "wkWidth": img_width
            , "wkHeight": img_width
        }
        return wk_params_dict

    def build_contourMap_params(self, layer):
        # start_lon, end_lon, start_lat, end_lat = [float(region) for region in layer['draw_regions'].split(",")]
        end_lat, end_lon, start_lat, start_lon = self.get_start_end(layer)

        lon_range = end_lon - start_lon
        lat_range = end_lat - start_lat

        # 解决全球范围绘图180°出现两根线的问题（数据没有360°导致的）
        if end_lon - start_lon < 350.0:
            lonSpacing = math.ceil((end_lon - start_lon) / 2)
        else:
            lonSpacing = 180.0

        if end_lat - start_lat < 170:
            latSpacing = math.ceil((end_lat - start_lat) / 2)
        else:
            latSpacing = 90.0

        contour_params_dict = {
            # 绘图尺寸相关
            "mpMinLonF": start_lon,
            "mpMaxLonF": end_lon,
            "mpMinLatF": start_lat,
            "mpMaxLatF": end_lat,
            "mpCenterLonF": (end_lon + start_lon) / 2,
            'mpLeftCornerLatF': start_lat,
            'mpRightCornerLatF': end_lat,
            'mpLeftCornerLonF': start_lon,
            'mpRightCornerLonF': end_lon,
            'mpLimitMode': 'Corners ',
            # "mpCenterLonF": 0,
            "vpHeightF": 0.817204 / (lon_range / lat_range),
            "mpGridLonSpacingF": lonSpacing,  # 中间虚线位置--经度
            "mpGridLatSpacingF": latSpacing,  # 中间虚线位置--纬度

        }
        if self.request_dict.get('map_grid'):
            contour_params_dict['mpGridAndLimbOn'] = False
        # 如果有风场图层，则无需绘制中央经纬线
        if 'vector' in [layer.get('layer_type') for layer in self.request_dict.get('layers')]:
            # contour_params_dict.pop('mpGridLonSpacingF')
            # contour_params_dict.pop('mpGridLatSpacingF')
            contour_params_dict['mpGridAndLimbOn'] = False

        # 色斑只显示的区域，其他的地区被掩膜覆盖
        if layer.get('map_masking_areas'):
            contour_params_dict["mpAreaMaskingOn"] = True  # 如果要掩膜，这个是必须的
            contour_params_dict["mpFillOn"] = True  # 如果要掩膜，这个是必须的
            contour_params_dict["mpMaskAreaSpecifiers"] = layer.get('map_masking_areas')

        # 栅格图显示
        if layer.get('contourFillMode'):
            contour_params_dict['cnFillMode'] = layer.get('contourFillMode')

        # 平滑系数
        if layer.get('cnSmoothCoef'):
            contour_params_dict['cnSmoothingOn'] = True
            contour_params_dict['cnSmoothingDistanceF'] = float(layer.get('cnSmoothCoef'))

        return contour_params_dict

    def get_start_end(self, layer):
        if layer.get("draw_regions"):
            # draw_regions = layer.get("draw_regions")
            # if type(draw_regions) == 'str':
            #     start_lon, end_lon, start_lat, end_lat = layer['draw_regions'].split(",")
            # elif type(draw_regions) == 'tuple':
            #     start_lon, end_lon, start_lat, end_lat = layer['draw_regions']

            start_lon, end_lon, start_lat, end_lat = layer['draw_regions'].split(",")
            start_lon = float(start_lon) if judge_str_is_number(start_lon) else np.min(self.lon)
            end_lon = float(end_lon) if judge_str_is_number(end_lon) else np.max(self.lon)
            start_lat = float(start_lat) if judge_str_is_number(start_lat) else np.min(self.lat)
            end_lat = float(end_lat) if judge_str_is_number(end_lat) else np.max(self.lat)
        else:
            start_lon = np.min(self.lon)
            end_lon = np.max(self.lon)
            start_lat = np.min(self.lat)
            end_lat = np.max(self.lat)
        return end_lat, end_lon, start_lat, start_lon

    def buildImage(self, output_img_path, output_img_name, output_img_type, contour_map_layer):
        end_lat, end_lon, start_lat, start_lon = self.get_start_end(contour_map_layer)

        lon_range = end_lon - start_lon
        lat_range = end_lat - start_lat

        im = Image.open(output_img_path + output_img_name + '.' + output_img_type, "r")
        # 经纬度范围相等时，修改图片剪裁范围（色斑图需显示图例）
        if lat_range / lon_range == 1:
            if contour_map_layer.get('layer_type') and contour_map_layer.get('layer_type') == 'contourMap':
                real_pic_size = (0, 30, 2800, 2800 * (lat_range / lon_range) + 200)
            else:
                real_pic_size = (0, 30, 2800, 2800 * (lat_range / lon_range) + 150)
        else:
            real_pic_size = (0, 30, 2800, 2800 * (lat_range / lon_range) + 370)
        im = im.crop(real_pic_size)
        return im

    def build_tickMack_params(self, params_dict, plot):

        params_dict['tmXBValues'] = self.request_dict.get('x_values')
        params_dict['tmYLValues'] = self.request_dict.get('y_values')
        params_dict['tmXBLabels'] = self.request_dict.get('x_labels')
        params_dict['tmYLLabels'] = self.request_dict.get('y_labels')
        if self.request_dict.get('x_sub_values'):
            params_dict['tmXBMinorValues'] = self.request_dict.get('x_sub_values')
        else:
            params_dict['tmXBMinorOn'] = False
        if self.request_dict.get('y_sub_values'):
            params_dict['tmYLMinorValues'] = self.request_dict.get('y_sub_values')
        else:
            params_dict['tmYLMinorOn'] = False

        # 获取坐标轴刻画位置、长度属性等
        map_attrs = ["vpXF", "vpYF", "vpWidthF", "vpHeightF", "trXMinF", "trXMaxF", "trYMinF", "trYMaxF"]
        for attr in map_attrs:
            params_dict[attr] = Ngl.get_float(plot, attr)

    def build_vector_params(self, layer=None):
        params_dict = {}
        end_lat, end_lon, start_lat, start_lon = self.get_start_end(layer)

        lon_range = end_lon - start_lon
        lat_range = end_lat - start_lat
        params_dict['trXMinF'] = start_lon
        params_dict['trXMaxF'] = end_lon
        params_dict['trYMinF'] = start_lat
        params_dict['trYMaxF'] = end_lat
        params_dict['vpHeightF'] = 0.817204 / (lon_range / lat_range),
        params_dict['vfXCStartV'] = start_lon
        params_dict['vfXCEndV'] = end_lon
        params_dict['vfYCStartV'] = start_lat
        params_dict['vfYCEndV'] = end_lat
        params_dict['vcRefAnnoString1'] = layer.get('vector_unit')
        if layer.get('vector_scale'):
            params_dict['vcRefAnnoString2'] = layer.get('vector_scale')
            # 替换掉vector_scale里的m/s
            params_dict['vcRefMagnitudeF'] = float(layer.get('vector_scale').replace("m/s",""))
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
        # 矢量风图标水平位置
        if layer.get('vector_parallel'):
            params_dict['vcRefAnnoParallelPosF'] = float(layer.get('vector_parallel'))
        # 矢量风箭头样式
        if layer.get('vector_style'):
            params_dict['vcGlyphStyle'] = layer.get('vector_style')
            # 纯箭头和空心箭头参数设置相同，但空心箭头和纯箭头箭头大小不一致，配置文件以纯箭头为准，故空心箭头大小需重新设置
            if params_dict['vcGlyphStyle'] == "LineArrow":
                params_dict['vcLineArrowHeadMaxSizeF'] = 0.012
                params_dict['vcLineArrowHeadMinSizeF'] = 0.008
        # 矢量风风速显示范围
        if layer.get("vector_min"):
            params_dict['vcMinMagnitudeF'] = layer.get("vector_min")
        if layer.get("vector_max"):
            params_dict['vcMaxMagnitudeF'] = layer.get("vector_max")

        return params_dict

    def build_streamLine_params(self, layer=None):
        params_dict = {}
        end_lat, end_lon, start_lat, start_lon = self.get_start_end(layer)

        lon_range = end_lon - start_lon
        lat_range = end_lat - start_lat
        params_dict['trXMinF'] = start_lon
        params_dict['trXMaxF'] = end_lon
        params_dict['trYMinF'] = start_lat
        params_dict['trYMaxF'] = end_lat
        params_dict['vpHeightF'] = 0.817204 / (lon_range / lat_range),
        params_dict['vfXCStartV'] = start_lon
        params_dict['vfXCEndV'] = end_lon
        params_dict['vfYCStartV'] = start_lat
        params_dict['vfYCEndV'] = end_lat
        if layer.get('stLineSpace'):
            params_dict['stLineStartStride'] = layer.get('stLineSpace')
        if layer.get('stArrowSpace'):
            params_dict['stArrowStride'] = layer.get('stArrowSpace')
        return params_dict

    def build_map_params(self, contour_map_layer):
        end_lat, end_lon, start_lat, start_lon = self.get_start_end(contour_map_layer)

        lon_range = end_lon - start_lon
        lat_range = end_lat - start_lat

        # 解决全球范围绘图180°出现两根线的问题（数据没有360°导致的）
        if end_lon - start_lon < 350.0:
            lonSpacing = math.ceil((end_lon - start_lon) / 2)
        else:
            lonSpacing = 180.0

        if end_lat - start_lat < 170:
            latSpacing = math.ceil((end_lat - start_lat) / 2)
        else:
            latSpacing = 90.0

        map_params_dict = {
            # 绘图尺寸相关
            "mpMinLonF": start_lon,
            "mpMaxLonF": end_lon,
            "mpMinLatF": start_lat,
            "mpMaxLatF": end_lat,
            "mpCenterLonF": (end_lon + start_lon) / 2,
            'mpLeftCornerLatF': start_lat,
            'mpRightCornerLatF': end_lat,
            'mpLeftCornerLonF': start_lon,
            'mpRightCornerLonF': end_lon,
            'mpLimitMode': 'Corners ',
            # "mpCenterLonF": 0,
            "vpHeightF": 0.866 / (lon_range / lat_range),
            "mpGridLonSpacingF": lonSpacing,  # 中间虚线位置--经度
            "mpGridLatSpacingF": latSpacing,  # 中间虚线位置--纬度
        }
        if self.request_dict.get('map_grid'):
            map_params_dict['mpGridAndLimbOn'] = False
        # 如果有风场图层，则无需绘制中央经纬线
        if 'vector' in [layer.get('layer_type') for layer in self.request_dict.get('layers')]:
            # map_params_dict.pop('mpGridLonSpacingF')
            # map_params_dict.pop('mpGridLatSpacingF')
            map_params_dict['mpGridAndLimbOn'] = False

        return map_params_dict

    def build_polyline_params(self, layer):
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

    def build_polyMarker_params(self, layer):
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

    def build_polyMarkerLine_params(self, layer):
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

    # def png_to_eps(self, im, output_img_path, output_img_name, output_img_type):
    #     im.save(output_img_path + output_img_name + '.' + output_img_type)
    #     fig = Image.open(output_img_path + output_img_name + '.' + output_img_type)
    #     if fig.mode in ('RGBA', 'LA'):
    #         fig = fig.convert('RGB')
    #     self.png_to_eps(output_img_path, output_img_name, output_img_type)
    #     fig.save(output_img_path + output_img_name + '.eps')
    #     fig.close()
