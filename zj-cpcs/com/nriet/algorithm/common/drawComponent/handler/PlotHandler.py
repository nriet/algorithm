from com.nriet.algorithm.common.drawComponent.handler.CommonHandler import CommonHandler
import numpy as np
import logging
class PlotHandler(CommonHandler):

    def __init__(self, workstation, plot=None, input_data=None, params_dict=None, layer=None, tmp_service=None):
        '''
        :param workstation: 画布对象
        :param plot: 当前要处理的子图对象
        :param input_data: 绘图所需数据
        :param params_dict: 绘图handler所需配置列表(注意此处是列表！)，列表中的每个元素是每条折线的绘制属性
        :param layer: 图层对象
        '''
        if not params_dict:
            params_dict = []
        self.layer = layer
        self.tmp_service = tmp_service
        super().__init__(workstation, plot, input_data, params_dict=params_dict)

    def draw(self):
        input_data = self.input_data
        layer = self.layer
        subplot = self.plot
        params_config_list = self.params_dict
        tmp_service = self.tmp_service



        # if layer_sub_titles:
        #     layer_sub_titles.insert(0,layer_main_title)
        #     layer_main_title = '\n'.join(layer_sub_titles)

        layer_y_left_title = tmp_service.request_dict.get('y_left_title')
        layer_x_buttom_title = tmp_service.request_dict.get('x_buttom_title')



        logging.info(input_data)



        x_data = input_data[:, 0]
        for i in range(np.shape(input_data)[1]-1):
            subplot.plot(x_data, input_data[:, i+1],**params_config_list[i])

        subplot.set_xticklabels(['one', 'two', 'three', 'four', 'five'])