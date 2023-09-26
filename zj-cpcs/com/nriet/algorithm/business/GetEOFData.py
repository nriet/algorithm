#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/02/21
# @Author : Eldan
# @File : GetEOFData.py
from com.nriet.algorithm.business.BusComponent import BusComponent
import xarray as xr


# 获取EOF模态数据
class GetEOFData(BusComponent):
    def __init__(self, sub_local_params, algorithm_input_data):
        """
            :param sub_local_params:流程参数，算法运算返回结果
            :param algorithm_input_data:流程数据
        """
        # 数据路径
        self.dataInputPaths = sub_local_params.get("dataInputPaths")
        # 经纬度范围
        self.regions = sub_local_params.get("regions")
        # 输出数据
        self.output_data = None

    def execute(self):
        # 解析经纬度范围
        start_lon, end_lon, start_lat, end_lat = [float(region) for region in self.regions.split(",")]
        # 替换模式占位符
        dataInputPaths = self.dataInputPaths
        # 加载数据
        ds = xr.open_dataset(dataInputPaths)
        # 获取经纬度和相应的要素值
        lat = ds.lat
        lon = ds.lon
        res_data = ds["ssta"]
        # 截取指定区域范围的数据
        lon_range = lon[(lon >= start_lon) & (lon <= end_lon)]
        lat_range = lat[(lat >= start_lat) & (lat <= end_lat)]
        res_data = res_data.sel(lon=lon_range, lat=lat_range)
        # 输出结果
        self.output_data = {"outputData": res_data}
