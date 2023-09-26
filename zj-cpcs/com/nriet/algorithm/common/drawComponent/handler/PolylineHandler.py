import numpy as np


import Nio, Ngl
import time
import copy
import os
import logging
from com.nriet.algorithm.common.drawComponent.handler.CommonHandler import CommonHandler
from com.nriet.utils.ResourcesUtils import create_or_update_resource
shape_file_path = "/nfsshare/cdbdata/algorithm/conductor/WMFS/EXTPRE/ysq/map/"

'''
此类用于绘制地理线或者矩形叠加图层
'''


class PolylineHandler(CommonHandler):
    def __init__(self, workstation, plot=None, input_data=None,layer=None,params_dict=None, tmp_service=None):
        super().__init__(workstation=workstation, plot=plot, params_dict=params_dict)
        self.input_data = input_data
        self.tmp_service = tmp_service
        self.layer= layer
    def draw(self):
        start_time = time.time()
        params_dicts = copy.deepcopy(self.params_dict)


        # 考虑是传入的shape文件还是一组二维数据，两者都有可能同时存在

        # 如果是有二维数据
        if self.layer.get('rectangle_list'):
            # 从params_dicts中取出矩形框的resource参数
            rectangle_resource_params = params_dicts.get("rectangle")
            resource = create_or_update_resource(params_dict=rectangle_resource_params)

            # 从layer中取出二维数据
            rectangle_list = self.layer.get('rectangle_list')
            if rectangle_resource_params and (rectangle_list is not None):
                for rectangle in rectangle_list:
                    lon_min, lon_max, lat_min, lat_max = eval(rectangle)
                    lon_min = float(lon_min)
                    lon_max = float(lon_max)
                    lat_min = float(lat_min)
                    lat_max = float(lat_max)
                    lon_down_x_axis = np.linspace(lon_min, lon_max, 10)
                    lon_down_y_axis = np.array([lat_min]*10)
                    lon_up_x_axis = lon_down_x_axis
                    lon_up_y_axis = np.array([lat_max]*10)
                    Ngl.add_polyline(self.workstation, self.plot, lon_down_x_axis, lon_down_y_axis, resource)
                    Ngl.add_polyline(self.workstation, self.plot, lon_up_x_axis, lon_up_y_axis, resource)

                    lat_left_x_axis = np.array([lon_min]*10)
                    lat_left_y_axis = np.linspace(lat_min,lat_max,10)
                    lat_right_x_axis = np.array([lon_max]*10)
                    lat_right_y_axis = lat_left_y_axis
                    Ngl.add_polyline(self.workstation, self.plot, lat_left_x_axis, lat_left_y_axis, resource)
                    Ngl.add_polyline(self.workstation, self.plot, lat_right_x_axis, lat_right_y_axis, resource)

        if self.layer.get('polyline_files'):
            # 从params_dict中取出polyline的resource参数
            polyline_resource_params = params_dicts.get("shp")


            # 绘制每个polyline
            polyline_files = self.layer.get('polyline_files')
            for polyline_file in polyline_files:
                shape = Nio.open_file(shape_file_path + polyline_file, "r")
                lon = np.ravel(shape.variables["x"][:])
                lat = np.ravel(shape.variables["y"][:])
                polyline_resource_params['gsSegments'] = shape.variables["segments"][:, 0]
                resource = create_or_update_resource(params_dict=polyline_resource_params)

                Ngl.add_polyline(self.workstation, self.plot, lon, lat, resource)

        if self.layer.get('shape_template'):
            # 从params_dict中取出polyline的resource参数
            shp_temp_resource_params = params_dicts.get("shp_temp")


            # 绘制每个polyline
            shape_template = self.layer.get('shape_template')
            # 从目录下寻找多个.shp
            shape_files = getFiles("/".join([shape_file_path,shape_template]),".shp")

            for shape_file in shape_files:
                shape = Nio.open_file(shape_file, "r")
                lon = np.ravel(shape.variables["x"][:])
                lat = np.ravel(shape.variables["y"][:])
                shp_temp_resource_params['gsSegments'] = shape.variables["segments"][:, 0]
                resource = create_or_update_resource(params_dict=shp_temp_resource_params)

                Ngl.add_polyline(self.workstation, self.plot, lon, lat, resource)

        stop_time = time.time()
        cost = stop_time - start_time
        logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))

        return self.plot

def getFiles(path, suffix):
    return [os.path.join(root, file) for root, dirs, files in os.walk(path) for file in files if file.endswith(suffix)]

if __name__ == '__main__':
    aaa =getFiles("/".join([shape_file_path,"ydyl"]),suffix=".shp")
    logging.info(aaa)