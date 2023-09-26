import numpy as np
import shapefile
import shapely.geometry as sgeom
from shapely.prepared import prep
import math
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


class PolyMarkerHandler(CommonHandler):
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
        region_type_tmp = self.tmp_service.request_dict["region_type"]

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
        寻找缺测值并打点绘图，绘制成灰色:[0.67, 0.67, 0.67]
        '''
        # 查询缺测的行索引及经纬度坐标
        nan_row_indexes = list(np.where(pd.isna(input_data))[0])
        nan_lons = np.ma.array(input_data.iloc[nan_row_indexes, 1])
        nan_lats = np.ma.array(input_data.iloc[nan_row_indexes, 2])
        # 循环打点
        for index, nan_row_index in enumerate(nan_row_indexes):
            resource.gsMarkerColor = [0.67, 0.67, 0.67]
            Ngl.add_polymarker(self.workstation, self.plot, nan_lons[index], nan_lats[index], resource)

        '''
        剔除缺测值过后,打点绘图
        '''
        input_data = input_data.dropna(axis=0, how='any')
        data = np.ma.array(input_data.iloc[:, 0])
        lons = np.ma.array(input_data.iloc[:, 1])
        lats = np.ma.array(input_data.iloc[:, 2])
        if not intervals:
            # 获取中国范围内点的经纬度
            if region_type_tmp == "wholeChina":
                shpFile = "/nfsshare/cdbdata/algorithm/conductor/WMFS/EXTPRE/ysq/map/china/中国融合/中国国界.shp"
                with shapefile.Reader(shpFile) as reader:
                    china = sgeom.shape(reader.shape(0))
                mask_tmp = polygon_to_mask(china, lons, lats)
                lons_tmp = []
                lats_tmp = []
                for i in range(len(mask_tmp)):
                    if mask_tmp[i]:
                        lons_tmp.append(lons[i])
                        lats_tmp.append(lats[i])
                Ngl.add_polymarker(self.workstation, self.plot, lons_tmp, lats_tmp, resource)
            else:
                Ngl.add_polymarker(self.workstation, self.plot, lons, lats, resource)
        else:
            intervals.insert(0, -999999.0)
            intervals.append(999999.0)
            # 将原有循环每个点打点的方式修改为先找出每个颜色的点，然后按颜色循环
            for i in range(len(intervals) - 1):
                minNum = intervals[i]
                maxNum = intervals[i + 1]
                data_tmp = input_data[input_data['data'] > float(minNum)][input_data['data'] <= float(maxNum)]
                lons_tmp = np.ma.array(data_tmp.iloc[:, 1])
                lats_tmp = np.ma.array(data_tmp.iloc[:, 2])
                resource.gsMarkerColor = colors[i]
                Ngl.add_polymarker(self.workstation, self.plot, lons_tmp, lats_tmp, resource)
            # 匹配每一个点之颜色
            # real_colors = list(map(lambda x: match_interval_decimal(x, intervals, colors), data))

            # 循环打点
            # for index, color in enumerate(real_colors):
            #     resource.gsMarkerColor = color
            #     Ngl.add_polymarker(self.workstation, self.plot, lons[index], lats[index], resource)

        stop_time = time.time()
        cost = stop_time - start_time
        logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))

        return self.plot


# 利用多边形生产掩码数组
def polygon_to_mask(polygon, x, y):
    """生成落入多边形的点的掩膜数组."""
    x = np.atleast_1d(x)
    y = np.atleast_1d(y)
    if x.shape != y.shape:
        raise ValueError('x和y的形状不匹配')
    prepared = prep(polygon)

    def recursion(x, y):
        """递归判断坐标为x和y的点集是否落入多边形中."""
        xmin, xmax = x.min(), x.max()
        ymin, ymax = y.min(), y.max()
        xflag = math.isclose(xmin, xmax)
        yflag = math.isclose(ymin, ymax)
        mask = np.zeros(x.shape, dtype=bool)

        # 散点重合为单点的情况.
        if xflag and yflag:
            point = sgeom.Point(xmin, ymin)
            if prepared.contains(point):
                mask[:] = True
            else:
                mask[:] = False
            return mask

        xmid = (xmin + xmax) / 2
        ymid = (ymin + ymax) / 2

        # 散点落在水平和垂直直线上的情况.
        if xflag or yflag:
            line = sgeom.LineString([(xmin, ymin), (xmax, ymax)])
            if prepared.contains(line):
                mask[:] = True
            elif prepared.intersects(line):
                if xflag:
                    m1 = (y >= ymin) & (y <= ymid)
                    m2 = (y >= ymid) & (y <= ymax)
                if yflag:
                    m1 = (x >= xmin) & (x <= xmid)
                    m2 = (x >= xmid) & (x <= xmax)
                if m1.any():
                    mask[m1] = recursion(x[m1], y[m1])
                if m2.any():
                    mask[m2] = recursion(x[m2], y[m2])
            else:
                mask[:] = False
            return mask

        # 散点可以张成矩形的情况.
        box = sgeom.box(xmin, ymin, xmax, ymax)
        if prepared.contains(box):
            mask[:] = True
        elif prepared.intersects(box):
            m1 = (x >= xmid) & (x <= xmax) & (y >= ymid) & (y <= ymax)
            m2 = (x >= xmin) & (x <= xmid) & (y >= ymid) & (y <= ymax)
            m3 = (x >= xmin) & (x <= xmid) & (y >= ymin) & (y <= ymid)
            m4 = (x >= xmid) & (x <= xmax) & (y >= ymin) & (y <= ymid)
            if m1.any():
                mask[m1] = recursion(x[m1], y[m1])
            if m2.any():
                mask[m2] = recursion(x[m2], y[m2])
            if m3.any():
                mask[m3] = recursion(x[m3], y[m3])
            if m4.any():
                mask[m4] = recursion(x[m4], y[m4])
        else:
            mask[:] = False

        return mask

    return recursion(x, y)
