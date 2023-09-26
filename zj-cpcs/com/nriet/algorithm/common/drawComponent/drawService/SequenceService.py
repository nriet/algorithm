from com.nriet.algorithm.common.drawComponent.drawService.CommonService import CommonService
from com.nriet.utils.StrSequenceConvertUtils import str_to_sequence
import matplotlib as mpl
import numpy as np
import logging
mpl.use('AGG')
mpl.rcParams['font.sans-serif'] = 'SimHei'
# 修改matplotlib后端输出格式，Cairo渲染器支持png,ps,pdf,svg等光栅图和矢量图输出格式
logging.info(mpl.get_configdir())
logging.info(mpl.get_cachedir())
import matplotlib.pyplot as plt
from com.nriet.utils import StringUtils, proxyUtils
from com.nriet.algorithm.common.drawComponent.resourceConfig.SequenceConfig import sequence_params_dict
import copy
from PIL import Image
class SequenceService(CommonService):
    def draw(self):
        # 0. 局部变量准备
        # 是否绘制logo 默认绘制  绘制：True  不绘制：False
        islogo = self.request_dict.get("islogo", "True")
        layers = self.request_dict['layers']
        input_data = self.input_data
        request_dict= self.request_dict

        output_img_path = request_dict['output_img_path']
        output_img_name = request_dict['output_img_name']
        output_img_type = request_dict['output_img_type']
        output_img_dpi = request_dict.get('output_img_dpi',300)
        output_img_max_width = request_dict.get('output_img_max_width',930)


        # 1. 创建画布
        figure = plt.figure(dpi=int(output_img_dpi))
        sub_plot = figure.add_subplot(111)

        # 2.绘制业务图层
        for index, layer in enumerate(layers):
            layer_type = layer.get('layer_type')

            # 入参准备阶段--获取模板配置
            params_configs = sequence_params_dict.get(layer_type)
            # 入参准备阶段--获取调用handler前的特定参数构建方法
            func = getattr(self, ''.join(['build_', layer_type, '_params']), None)
            if func:
                params_configs,result_input_data = func(layer,params_configs,input_data[0,:,:])
            # 动态创建实例
            class_name = StringUtils.capitalize_str(layer_type) + 'Handler'
            draw_handler = proxyUtils.create_class_instance(
                '.'.join(['com.nriet.algorithm.common.drawComponent.handler', class_name]), class_name,
                workstation = figure, plot = sub_plot,
                input_data = result_input_data,
                params_dict = params_configs,
                layer=layer, tmp_service=self)

            # 调用handler绘制子图，返回画布对象figure
            draw_handler.draw()

        # 3. 添加logos
        if islogo == "True":
            img = Image.open('/usr/local/src/huxin/CPCS/com/nriet/algorithm/common/drawComponent/logoFiles/BCC.png')
            img = np.array(img).astype(np.float) /255
            plt.figimage(img,0,0,origin='lower')
        # plt.figimage()
        # 4. 保存成对应的格式
        sub_plot.legend(loc=2)

        figure.savefig(output_img_path+output_img_name+'.'+output_img_type)

        # 释放所有figure相关资源
        plt.close(figure)


    def build_bar_params(self, layer,params_dict,input_data):
        # 用户自定义属性覆盖默认属性
        cp_params_dict = self.overide_params_dict(layer, params_dict)
        # 整合handler输入数据
        plot_counts, result_input_data = self.collect_handler_input_data(input_data, layer)
        # 整合绘图配置参数
        result_params_list = []
        for count in range(plot_counts):
            result_params_list.append({})

        for key, value in cp_params_dict.items():
            if key in ['layer_type', 'data_rows']:
                continue

            if isinstance(value, list):
                if len(value) != plot_counts:
                    cp_params_dict[key] = value * plot_counts
            else:
                cp_params_dict[key] = [value] * plot_counts

            for factor_index, factor in enumerate(cp_params_dict[key]):
                result_params_list[factor_index][key[:-1]] = factor  # key使用单数形式

        return result_params_list, result_input_data

    def build_scatter_params(self, layer,params_dict):
        pass

    def build_plot_params(self,layer,params_dict,input_data):

        # 用户自定义属性覆盖默认属性
        cp_params_dict = self.overide_params_dict(layer, params_dict)
        #整合handler输入数据
        plot_counts, result_input_data = self.collect_handler_input_data(input_data, layer)

        #整合绘图配置参数
        result_params_list=[]
        for count in range(plot_counts):
             result_params_list.append({})

        for key,value in cp_params_dict.items():
            if key in ['layer_type', 'data_rows']:
                continue

            if isinstance(value,list):
                if len(value) != plot_counts:
                    cp_params_dict[key] = value * plot_counts
            else:
                cp_params_dict[key] = [value] * plot_counts

            for factor_index,factor in enumerate(cp_params_dict[key]):
                result_params_list[factor_index][key[:-1]]=factor#key使用单数形式

        return result_params_list,result_input_data

    def collect_handler_input_data(self, input_data, layer):
        data_rows = layer.get('data_rows')
        # 整合handler输入数据
        if data_rows:
            result_data_rows = str_to_sequence(data_rows)
            plot_counts = len(data_rows)
            result_data_rows.insert(0, 0)
            result_input_data = input_data[:, result_data_rows]
        else:
            plot_counts = input_data.shape[1] - 1  # 没传这个参数，默认视作全部数据列的数量
            result_input_data = input_data
        return plot_counts, result_input_data

    def overide_params_dict(self, layer, params_dict):
        # 复制配置参数
        cp_layer = copy.deepcopy(layer)
        cp_params_dict = copy.deepcopy(params_dict)
        # 用户自定义参数覆盖
        cp_params_dict.update(cp_layer)
        return cp_params_dict

    def build_circle_params(self, layer,params_dict):
        pass
