import numpy as np

import logging, Ngl
import time
import copy
import os
import pandas as pd
from com.nriet.algorithm.common.drawComponent.handler.CommonHandler import CommonHandler
from com.nriet.utils.ResourcesUtils import create_or_update_resource
from com.nriet.utils.matchUtils import match_interval_decimal

shape_file_path = "/nfsshare/cdbdata/algorithm/conductor/WMFS/EXTPRE/ysq/map/"

'''
此类用于绘制地理散点叠加图层
'''


class PolyMarkerLineHandler(CommonHandler):
    def __init__(self, workstation, plot=None, input_data=None, layer=None, params_dict=None, tmp_service=None):
        super().__init__(workstation=workstation, plot=plot, params_dict=params_dict)
        self.input_data = input_data
        self.tmp_service = tmp_service
        self.layer = layer

    def draw(self):
        start_time = time.time()
        params_dicts = copy.deepcopy(self.params_dict)
        input_data = copy.deepcopy(self.input_data)
        intervals = copy.deepcopy(self.layer.get('intervals'))
        colors = copy.deepcopy(self.layer.get('colors'))
        resource = create_or_update_resource(params_dict=params_dicts)

        # 获取基本属性
        lons = list(self.tmp_service.station_lon)
        lats = list(self.tmp_service.station_lat)
        data_dict = {
            "data": input_data,
            "lons": lons,
            "lats": lats
        }
        input_data = pd.DataFrame(data_dict)

        '''
        剔除缺测值过后,打点绘图
        '''
        input_data = input_data.dropna(axis=0, how='any')
        data = np.ma.array(input_data.iloc[:, 0])
        lons = np.ma.array(input_data.iloc[:, 1])
        lats = np.ma.array(input_data.iloc[:, 2])
        if not intervals:
            Ngl.add_polymarker(self.workstation, self.plot, lons, lats, resource)
            for index, lon in enumerate(lons):
                resource.gsLineColor = "black"
                if index>0 and lons[index]<500 and lons[index-1]<500:
                    Ngl.add_polyline(self.workstation, self.plot, [lons[index-1],lons[index]], [lats[index-1],lats[index]], resource)
        else:
            intervals.insert(0, -999999.0)
            intervals.append(999999.0)
            # 匹配每一个点之颜色
            real_colors = list(map(lambda x: match_interval_decimal(x, intervals, colors), data))

            # 循环打点
            for index, color in enumerate(real_colors):
                resource.gsMarkerColor = color
                resource.gsLineColor = color
                Ngl.add_polymarker(self.workstation, self.plot, lons[index], lats[index], resource)
                if index>0 and lons[index]<500 and lons[index-1]<500:
                    Ngl.add_polyline(self.workstation, self.plot, [lons[index-1],lons[index]], [lats[index-1],lats[index]], resource)

        stop_time = time.time()
        cost = stop_time - start_time
        logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))

        return self.plot
