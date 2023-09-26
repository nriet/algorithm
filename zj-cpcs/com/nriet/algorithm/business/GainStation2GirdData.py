#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2023/06/14
# @Author : Sbiys
# @File : GainStation2GirdData.py

import numpy as np
import os, sys, json, ast
import xarray as xr
import pandas as pd
from scipy.interpolate import Rbf
from metpy.interpolate import remove_nan_observations, interpolate_to_grid
import logging, traceback
logger = logging.getLogger(__name__)
logger.root.setLevel(level=logging.INFO)
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
logging.info(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from com.nriet.algorithm.common.inputData.InputDataComponent import InputDataComponent
from com.nriet.utils import DateUtils
from com.nriet.utils.result.ResponseResultUtils import build_response_dict
from com.nriet.config.ResponseCodeAndMsgEum import PARAMETER_VALUE_MISSING_CODE, \
    PARAMETER_VALUE_MISSING_MSG, CUSTOM_ERROR_CODE, CUSTOM_ERROR_MSG
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException


class GainStation2GirdData(InputDataComponent):

    def __init__(self):
        pass

    def init_param(self, params):
        """
        初始化参数
        Args:
            params:

        Returns:

        """
        # 插值方法
        self.interpolationMethod = params.get("interpolationMethod")
        # 需要插值到的纬度起止点及个数
        self.interLat = params.get("interLat")
        # 需要插值到的经度起止点及个数
        self.interLon = params.get("interLon")
        # 站点数据文件路径（文件格式 站号 经度 纬度 值）
        self.dataInputPath = params.get("dataInputPath")
        # 结果数据输出路径
        self.dataOutputPath = params.get("dataOutputPath")
        # 结果数据变量名
        self.var = params.get("var")
        # 插值后的负值转换成0  转换：1 不转换：0
        self.negativeType = params.get("negativeType", "0")

    # 获取nc数据
    def execute(self, params):
        # 1.初始化参数
        self.init_param(params)
        result_dict = build_response_dict()
        interLats = list(map(float, self.interLat.split(",")))
        interLons = list(map(float, self.interLon.split(",")))
        data = pd.read_table(self.dataInputPath, header=None, encoding='utf-8', sep=" ")
        dataArr1 = np.array(data)
        dataArr = np.asarray(dataArr1[:, 1:], dtype=np.float32)
        zstas2 = dataArr1[:, 0]
        zstas = list(range(1, len(zstas2) + 1))
        zlons = dataArr[:, 0]
        zlats = dataArr[:, 1]
        zvalues = dataArr[:, 2]
        stationData = xr.DataArray(zvalues, coords=[zstas], dims=['station'])
        stationData.values = np.where(stationData.values == 999999, np.nan, stationData.values)
        if self.interpolationMethod == "cressman":
            gridData = self.interp_cressman(stationData, interLats, interLons, zlats, zlons)
        if self.interpolationMethod == "ref":
            gridData = self.interp_ref(stationData, interLats, interLons, zlats, zlons)
        if self.interpolationMethod == "idw":
            gridData = self.interp_idw(stationData, interLats, interLons, zlats, zlons)
        # 负值处理成0
        if self.negativeType == "1":
            gridData = xr.where(gridData < 0, 0, gridData)
        # print(gridData)
        self.writ_nc([gridData], self.var, self.dataOutputPath)
        result_dict["output_file_name"] = self.dataOutputPath
        result_dict["output_img_name"] = self.dataOutputPath.replace(".nc", ".png")
        return result_dict

    def interp_ref(self, inputData, lats, lons, zlat, zlon):
        glon = np.linspace(lons[0], lons[1], lons[2])
        glat = np.linspace(lats[0], lats[1], lats[2])
        olon, olat = np.meshgrid(glon, glat)
        zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, inputData)
        rf = Rbf(zlon1, zlat1, tmpdata.values, kind="thin_plate", smooth=0.2)
        grid1 = rf(olon, olat)
        grid1 = grid1.reshape((int(lats[2]), int(lons[2])))
        interp_grid_data = xr.DataArray(grid1, coords=[glat, glon], dims=['lat', 'lon'])
        return interp_grid_data

    def interp_cressman(self, inputData, lats, lons, zlat, zlon):
        boundary_coords = {"west": lons[0], "south": lats[0], "east": lons[1], "north": lats[1]}
        zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, inputData)
        if lons[0] >= 0:
            zlon1 = np.where(zlon1 < 0, zlon1 + 360, zlon1)
        gx, gy, grid1 = interpolate_to_grid(zlon1, zlat1, tmpdata.values, interp_type='cressman', minimum_neighbors=2,
                                            hres=2,
                                            search_radius=7, boundary_coords=boundary_coords)
        glat = gy[:, 0]
        glon = gx[0]
        interp_grid_data = xr.DataArray(grid1, coords=[glat, glon], dims=['lat', 'lon'])
        return interp_grid_data

    def interp_idw(self, inputData, lats, lons, zlat, zlon):
        glon = np.linspace(lons[0], lons[1], int(lons[2]))
        glat = np.linspace(lats[0], lats[1], int(lats[2]))
        olon, olat = np.meshgrid(glon, glat)
        olon, olat = olon.flatten(), olat.flatten()
        zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, inputData)
        grid1 = simple_idw(zlon1, zlat1, tmpdata.values, olon, olat)
        # print(grid1.shape)
        grid1 = grid1.reshape((int(lats[2]), int(lons[2])))
        interp_grid_data = xr.DataArray(grid1, coords=[glat, glon], dims=['lat', 'lon'])
        return interp_grid_data

    def partitioned_data(self, par_data, regions, drawCenterLon):
        nc_data = par_data.copy()
        # 源数据中的起止经度
        nc_lons = list(nc_data.lon.values)
        nc_start_lon, nc_end_lon = nc_lons[0], nc_lons[-1]
        # 截取数据的起止经纬度
        start_lon, end_lon, start_lat, end_lat = [float(reg) for reg in regions.split(",")]
        if regions is not None:
            # 截取范围开始经度和源数据的开始经度风符号不一致时，需进行经度转换后再截取数据
            # 情况1、截取范围开始经度小于0 源数据的开始经度大于等于0  经度转换成 -180~180
            if start_lon < 0 and nc_start_lon >= 0:
                lonx = nc_data.lon
                lonx = xr.where(lonx > 180, lonx - 360, lonx)
                nc_data["lon"].values = lonx.values
                nc_data = nc_data.sortby(nc_data["lon"])
            #  情况2、截取范围开始经度大于等于0 源数据的开始经度小0  经度转换成 0~3600
            if start_lon >= 0 and nc_start_lon < 0:
                lonx = nc_data.lon
                lonx = xr.where(lonx < 0, lonx + 360, lonx)
                nc_data["lon"].values = lonx.values
                nc_data = nc_data.sortby(nc_data["lon"])
            # 根据传入的范围截取数据
            lon = nc_data["lon"]
            lat = nc_data["lat"]
            lon = lon[(lon >= start_lon) & (lon <= end_lon)]
            lat = lat[(lat >= start_lat) & (lat <= end_lat)]
            nc_data = nc_data.sel(lon=lon, lat=lat)

        # 绘图数据处理
        # 180为中心
        if drawCenterLon and drawCenterLon == "180":
            long = nc_data.lon
            long = xr.where(long < 0, long + 360, long)
            nc_data["lon"].values = long.values
            nc_data = nc_data.sortby(nc_data["lon"])
        # 0为中心
        if drawCenterLon and drawCenterLon == "0":
            long = nc_data.lon
            long = xr.where(long > 180, long - 360, long)
            nc_data["lon"].values = long.values
            nc_data = nc_data.sortby(nc_data["lon"])
        return nc_data

    # 生成netCDF文件
    def writ_nc(self, res_data, resVar, out_file_path):
        # 判断输出目录是否存在，不存在就创建
        str_dir = os.path.dirname(out_file_path)
        if not os.path.exists(str_dir):
            os.makedirs(str_dir)
        # 判断输出文件是否存在，存在则删除
        if os.path.exists(out_file_path):
            os.remove(out_file_path)
        var_list = resVar.split(",")
        output_data = {}
        encoding = {}
        for i, rvar in enumerate(var_list):
            if i < len(res_data):
                output_data[rvar] = res_data[i]
                encoding[rvar] = {'dtype': 'float32', '_FillValue': 999999.0}
        # 生成netCDF文件
        data_set = xr.Dataset(output_data)
        if "time" in data_set.dims:
            data_set.time.values = list(map(int, data_set.time.values))
        if "lat" in data_set.dims:
            encoding["lat"] = {'dtype': 'float32'}
        if "lon" in data_set.dims:
            encoding["lon"] = {'dtype': 'float32'}
        # 设置netcdf的数据属性
        data_set.to_netcdf(out_file_path, encoding=encoding)


def simple_idw(x, y, z, xi, yi):
    dist = distance_matrix(x, y, xi, yi)
    weights = 1.0 / dist ** 20
    weights /= weights.sum(axis=0)
    zi = np.dot(weights.T, z)
    return zi


def distance_matrix(x0, y0, x1, y1):
    obs = np.vstack((x0, y0)).T
    interp = np.vstack((x1, y1)).T
    d0 = np.subtract.outer(obs[:, 0], interp[:, 0])
    d1 = np.subtract.outer(obs[:, 1], interp[:, 1])
    return np.hypot(d0, d1)


if __name__ == "__main__":
    try:
        t1 = DateUtils.getTimeStamp()
        # 获取页面传参
        page_params = ast.literal_eval(sys.argv[1])
        # page_params = {"interpolationMethod": "idw","interLon": "117,123,61","interLat": "27,32,51","dataOutputPath": "/nfsshare/cdbdata/data/dry_data/eabeebc5-416c-45c5-8707-6aae4d1b0862.nc","dataInputPath": "/nfsshare/cdbdata/data/dry_data/eabeebc5-416c-45c5-8707-6aae4d1b0862.txt", "var": "moni_sb", "negativeType": "0"}
        gs2gd = GainStation2GirdData()
        result_dict = gs2gd.execute(page_params)
        t2 = DateUtils.getTimeStamp()
        logging.info("获取站点插值格点总耗时: %s ms" % (str(t2 - t1)))
    except AlgorithmException as ae:
        logging.error(traceback.format_exc())
        result_dict = ae.__str__()
    except IndentationError as ie:
        logging.error(traceback.format_exc())
        result_dict = build_response_dict(response_code=PARAMETER_VALUE_MISSING_CODE,
                                          response_msg=PARAMETER_VALUE_MISSING_MSG % "methodName")
    except Exception as e:
        logging.error(traceback.format_exc())
        result_dict = build_response_dict(response_code=CUSTOM_ERROR_CODE, response_msg=CUSTOM_ERROR_MSG)
    # 输出结果信息
    print(json.dumps(result_dict, ensure_ascii=False))
    # logging.info(json.dumps(result_dict, ensure_ascii=False))
