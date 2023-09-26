import numpy as np


import Nio, Ngl
import time
import copy
import os
import logging
from com.nriet.algorithm.common.drawComponent.handler.CommonHandler import CommonHandler
from com.nriet.utils.ResourcesUtils import create_or_update_resource
from com.nriet.utils.matchUtils import match_interval
shape_file_path = "/nfsshare/cdbdata/algorithm/conductor/WMFS/EXTPRE/ysq/map/"

'''
此类用于绘制地理线叠加图层
'''


class GeoHandler(CommonHandler):
    def __init__(self, workstation, plot=None, input_data=None,layer=None,params_dict=None, tmp_service=None):
        super().__init__(workstation=workstation, plot=plot, params_dict=params_dict)
        self.input_data = input_data
        self.tmp_service = tmp_service
        self.layer= layer
    def draw(self):
        start_time = time.time()
        params_dicts = copy.deepcopy(self.params_dict)

        if self.input_data:#如果传入了绘图数据，则根据绘图数据绘图，否则按照默认的模板配置绘图层
            # 获取基本属性
            lons = self.tmp_service.lon
            lats = self.tmp_service.lat
            intervals = params_dicts.pop('intervals')
            colors = params_dicts.pop('colors')

            # 创建资源对象Resource 应该包含gsMarkerIndex，gsMarkerSizeF，gsMarkerColor
            resource = create_or_update_resource(params_dict=params_dicts)

            # 对input_data,进行颜色替换
            real_colors = list(map(lambda x:match_interval(x,intervals,colors),self.input_data))

            # 循环打点
            for index,color in real_colors:
                resource.gsMarkerColor = color
                Ngl.add_polymarker(self.workstation,self.plot,lons[index],lats[index],resource)


        else:
            for key, params_dict in params_dicts.items():
                file_name = params_dict.pop('file_name')
                draw_type = params_dict.pop('type')
                shape = Nio.open_file(shape_file_path + file_name, "r")
                lon = np.ravel(shape.variables["x"][:])
                lat = np.ravel(shape.variables["y"][:])
                params_dict['gsSegments'] = shape.variables["segments"][:, 0]
                resource = create_or_update_resource(params_dict=params_dict)
                # 2.绘制曲线图
                if draw_type == 'polyline':
                    Ngl.add_polyline(self.workstation, self.plot, lon, lat, resource)
                elif draw_type == 'polygon':
                    Ngl.add_polygon(self.workstation, self.plot, lon, lat, resource)
                else:
                    pass  # point待处理

        stop_time = time.time()
        cost = stop_time - start_time
        logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))

        return self.plot