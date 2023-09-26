import Ngl
import time
import logging
import os,copy
from com.nriet.algorithm.common.drawComponent.handler.CommonHandler import CommonHandler
from com.nriet.utils.ResourcesUtils import create_or_update_resource
from com.nriet.algorithm.common.drawComponent.handler.LabelBarHandler import LabelBarHandler
from com.nriet.algorithm.common.drawComponent.resourceConfig.CommonConfig import common_params_dict

class MapHandler(CommonHandler):
    def __init__(self, workstation, plot=None, input_data=None, params_dict=None, layer=None, tmp_service=None):
        '''

        :param workstation: 工作站对象
        :param plot: 上游的plot对象
        :param input_data: 绘图所需数据
        :param params_dict: 绘图handler所需配置字典
        :param layer: 模板service对象
        '''
        super().__init__(workstation, plot, input_data, params_dict=params_dict)
        self.layer = layer
        self.tmp_service = tmp_service

    def draw(self):
        start_time = time.time()
        resource_config = self.params_dict
        # 构造resource对象
        self.resource = create_or_update_resource(params_dict=resource_config)

        # 绘图
        map_plot = Ngl.map(self.workstation, self.resource)


        if self.layer.get('layer_type') == 'polyMarker' and self.tmp_service.request_dict['region_type'] == 'global':
            if self.layer.get("colors"):
                colors = copy.deepcopy(self.layer.get("colors"))
                intervals = copy.deepcopy(self.layer.get("intervals"))

                # 默认缺测点全部绘制。
                colors.insert(0,[0.67,0.67,0.67]) #缺测灰

                intervals.insert(0,"NaN")
                intervals.insert(0,"")
                intervals.append("")
                intervals = [str(int(i)) if not isinstance(i, str) and i % 1 == 0 else str(i) for i in intervals]
                # intervals = [str(interval) for interval in intervals]
                copy_layer = copy.deepcopy(self.layer)

                copy_layer['legend_labels']=intervals
                copy_layer['colors'] = colors

                if self.layer.get('legend_labels'):
                    copy_layer['legend_labels'] = ["" for item in self.layer.get('legend_labels')]
                    # copy_layer['legend_labels'] = self.layer.get('legend_labels')
                    label_bar_handler = LabelBarHandler(self.workstation, map_plot,
                                                        params_dict=common_params_dict.get('label_bar_marker'),
                                                        layer=copy_layer,
                                                        tmp_service=self.tmp_service)
                else:
                    label_bar_handler = LabelBarHandler(self.workstation, map_plot,
                                                        params_dict=common_params_dict.get('label_bar'), layer=copy_layer,
                                                        tmp_service=self.tmp_service)
                label_bar_handler.draw()

        # plot叠加
        if self.plot:
            Ngl.overlay(self.plot, map_plot)
        else:
            self.plot = map_plot

        stop_time = time.time()
        cost = stop_time - start_time
        logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))

        return self.plot