from PIL import ImageDraw, Image
import os, logging
from com.nriet.algorithm.common.drawComponent.drawService.CommonService import CommonService
from com.nriet.algorithm.common.drawComponent.handler import LogoHandler, TextHandler
from com.nriet.algorithm.common.drawComponent.handler.GeoHandler import GeoHandler
from com.nriet.algorithm.common.drawComponent.handler.SouthSeaHandler import SouthSeaHandler
from com.nriet.algorithm.common.drawComponent.handler.WorkstationHandler import WorkstationHandler
from com.nriet.algorithm.common.drawComponent.resourceConfig.ChinaConfig import china_params_dict
from com.nriet.utils import StringUtils, proxyUtils
from com.nriet.config.PathConfig import CPCS_ROOT_PATH
from com.nriet.utils.result.ResponseResultUtils import build_response_dict
from com.nriet.utils.obs.ObsUtils import ObsUtils
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config


class ChinaTestService(CommonService):

    def draw(self):
        # 0.参数准备
        input_data = self.input_data
        save_to_nfsshare_switch = look_for_single_global_config("SAVE_TO_NFSSHARE_SWITCH")
        save_to_obs_switch = look_for_single_global_config("SAVE_TO_OBS_SWITCH")
        # 是否绘制logo 默认绘制  绘制：True  不绘制：False
        islogo = self.request_dict.get("islogo", "True")
        output_img_type = self.request_dict["output_img_type"]
        expire = self.request_dict.get("expire", 1)
        temp_img_path = CPCS_ROOT_PATH + "com/nriet/test/"
        output_img_path = self.request_dict["output_img_path"]
        output_img_name = self.request_dict["output_img_name"]
        date = self.request_dict.get("date")
        yblx = self.request_dict.get("yblx")
        timeType = self.request_dict.get("timeType")
        var = self.request_dict.get("elements")
        seasonStr = ['春季', '夏季', '秋季', '冬季']
        if var == "avgt":
            main_title = "全国气温距平预测检验(" + yblx + ")"
        elif var == "rain":
            main_title = "全国降水量距平百分率预测检验(" + yblx + ")"
        if timeType == 'mon':
            sub_titles = [str(date)[0:4] + "年" + str(date)[4:6] + "月"]
        elif timeType == 'season':
            ss = int(str(date)[4:6])
            sub_titles = [str(date)[0:4] + "年" + seasonStr[ss - 1]]
        elif timeType == 'day':
            sub_titles = date
        numbers = self.request_dict.get("numbers")

        layers = {}
        layers['draw_regions'] = '60,150,0,60'
        layers['layer_type'] = 'polyMarker'
        layers['marker_size'] = 0.004
        layers['colors'] = [
            [0.0, 0.0, 0.0],
            [0.992156862745098, 0.109803921568627, 0.109803921568627],
            [0.0313725490196078, 0.16078431372549, 1],
            [0, 0.909803921568627, 0],
            [0.752941176470588, 0.752941176470588, 0.752941176470588],  # 异常漏报，灰色，220303改
            # [0.415686274509804, 0.345098039215686, 0.901960784313726], #异常漏报，紫色，原图
            [0.941176470588235, 0.898039215686275, 0.211764705882353]  # 实况缺失
        ]
        layers['intervals'] = [0.5, 1.5, 2.5, 3.5, 4.5]
        layers = [layers]
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

            # 入参准备阶段--获取模板配置
            params_dict = china_params_dict.get(layer_type)
            # 入参准备阶段--获取调用handler前的特定参数构建方法
            func = getattr(self, ''.join(['build_', layer_type, '_params']), None)
            if func:
                pre_params_dict = func(layer)
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
        # label_bar_handler = LabelBarHandler(workstation, map_plot,
        # params_dict=china_params_dict.get('label_bar_test'), layer=first_layer,
        # tmp_service=self)
        # label_bar_handler.draw()

        # 5.南海相关
        south_sea_handler = SouthSeaHandler(workstation, map_plot, input_data,
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
        TextHandler.add_titles(im, draw, main_title, sub_titles, params_dict=china_params_dict['title_jy_elements'])
        # 结束
        # 9.绘制数字
        TextHandler.add_numbers(im, draw, date, timeType, var, numbers, params_dict=china_params_dict['numbers'])
        # 11.叠加中国中文掩膜
        # 新绘图修改
        # img2 = Image.open(CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/imgFiles/china_jy.png")
        img2 = Image.open(CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/imgFiles/china_jy_new.png")
        # 结束
        im.paste(img2, (0, 0, img2.size[0], img2.size[1]), img2)

        # 12.保存
        # if int(save_to_nfsshare_switch) or self.request_dict.get("saveToNfsshare"):
        im.save(output_img_path + output_img_name + '.' + output_img_type)

        # 是否上传至obs
        if int(save_to_obs_switch) or self.request_dict.get("saveToObs"):
            storage_result = ObsUtils().img_save_to_obs(im, output_img_name, output_img_type, int(expire))

        # 删除临时文件
        os.remove(temp_img_path + output_img_name + '.' + output_img_type)
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

    def build_map_params(self, layer):

        return {}

    def build_polyMarker_params(self, layer):
        params_dict = {}
        marker_size = layer.get('marker_size', None)
        marker_type = layer.get('marker_type', None)
        if marker_size:
            params_dict['gsMarkerSizeF'] = marker_size
        if marker_type:
            params_dict['gsMarkerIndex'] = int(marker_type)
        return params_dict
