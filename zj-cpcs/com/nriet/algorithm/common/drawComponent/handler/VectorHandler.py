import Ngl
import numpy as np
import time
import logging
import os

from com.nriet.algorithm.common.drawComponent.handler.CommonHandler import CommonHandler
from com.nriet.utils.ResourcesUtils import create_or_update_resource


class VectorHandler(CommonHandler):

    def __init__(self, workstation, plot=None, input_data=None, params_dict=None, layer=None, tmp_service=None):
        '''
        :param workstation: 工作站对象
        :param plot: 上游的plot对象
        :param input_data: 绘图所需数据
        :param params_dict: 绘图handler所需配置字典
        :param layer: 模板service对象
        '''
        if not params_dict:
            params_dict = {}
        if tmp_service:
            params_dict['vfXArray'] = tmp_service.lon_indexes
            params_dict['vfYArray'] = tmp_service.lat_indexes
            params_dict['vfXCStartV'] = float(np.min(tmp_service.lon_indexes))
            params_dict['vfXCEndV'] = float(np.max(tmp_service.lon_indexes))
            params_dict['vfYCStartV'] = float(np.min(tmp_service.lat_indexes))
            params_dict['vfYCEndV'] = float(np.max(tmp_service.lat_indexes))
        super().__init__(workstation, plot, input_data, params_dict=params_dict)

    def draw(self):
        start_time = time.time()

        resource_config = self.params_dict

        # 构造resource对象

        if not resource_config.get('vcRefMagnitudeF'):
            # vcRefMagnitudeF = np.ceil(np.max(np.sqrt(np.square(self.input_data[0]) + np.square(self.input_data[1]))))
            # 单位风矢量风速为input_data的95百分位数
            vcRefMagnitudeF = np.ceil(np.percentile((np.sqrt(np.square(self.input_data[0]) + np.square(self.input_data[1]))), 95))
            resource_config['vcRefMagnitudeF']= vcRefMagnitudeF
            resource_config['vcRefAnnoString2']= vcRefMagnitudeF


        self.resource = create_or_update_resource(params_dict=resource_config)

        # 绘图
        map_plot = Ngl.vector(self.workstation, self.input_data[0], self.input_data[1], self.resource)

        # plot叠加
        if self.plot:
            Ngl.overlay(self.plot, map_plot)
        else:
            self.plot = map_plot

        stop_time = time.time()
        cost = stop_time - start_time
        logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))

        return self.plot
