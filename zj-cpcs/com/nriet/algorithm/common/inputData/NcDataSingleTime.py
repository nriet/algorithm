#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/04/29
# @Author : huyh
# @File : NcDataSingleTime.py

import numpy as np
import Nio
import xarray as xr
import os

from com.nriet.algorithm.common.inputData.InputDataComponent import InputDataComponent
from com.nriet.utils import fileUtils, DateUtils
from com.nriet.utils.decorator.TimerDecorator import timer_with_param
from com.nriet.utils.fileUtils import convert_data
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import FILE_NOT_FOUND_ERROR_CODE

class NcDataSingleTime(InputDataComponent):

    def __init__(self, sub_local_params, algorithm_input_data):
        """
        :param sub_local_params:流程参数，算法运算返回结果
        :param algorithm_input_data:流程数据
        """
        # 数据路径
        self.dataInputPaths = sub_local_params["dataInputPaths"]
        # 气候态数据
        self.ltmDataInputPaths = sub_local_params.get("ltmDataInputPaths")
        # 数据计算时间范围
        self.timeRanges = sub_local_params.get("timeRanges")
        # 数据计算时间类型
        self.timeTypes = sub_local_params.get("timeType")
        # 数据要素
        self.elements = sub_local_params["elements"]
        self.level = sub_local_params.get("levels")
        self.regions = sub_local_params.get("regions")
        # 单位转化 （转化方式_转化值）
        self.unit_convert = sub_local_params.get("unitConvert")
        self.output_data = None

    # 获取nc数据
    @timer_with_param("get NC data")
    def execute(self):
        outputData = {}
        data_list = []

        file_time = DateUtils.get_time_list(self.timeRanges, self.timeTypes)
        if self.level:
            if self.dataInputPaths.find("low") == -1:
                tmpdata = xr.open_dataset("/nfsshare1/cdbdata/data/NEMO/highres/subsst/ltm/day/0101.nc")[self.elements][:]
                lon = tmpdata['lon'].values
                lat = tmpdata['lat'].values
                level = tmpdata['level'].values
                shapes = list([1, len(level), len(lat), len(lon)])
            else:
                tmpdata = xr.open_dataset("/nfsshare1/cdbdata/data/NEMO/lowres/subsst/ltm/day/0101.nc")[self.elements][:]
                lon = tmpdata['lon'].values
                lat = tmpdata['lat'].values
                level = tmpdata['level'].values
                shapes = list([1, len(level), len(lat), len(lon)])
            # 打开文件并读取数据
            if self.dataInputPaths:
                tmp_list = []
                for i, time in enumerate(file_time):
                    if self.timeTypes=="day":
                        out = self.dataInputPaths + time[0:4] + "/" + time[4:6] + "/" + time + ".nc"
                    else:
                        out = self.dataInputPaths + time[0:4] + "/"+ time + ".nc"
                    if os.path.exists(out):
                        ds = xr.open_dataset(out)
                        ncData = ds[self.elements]
                    else:
                        ncData = np.full(shapes,np.nan)
                        ncData = xr.DataArray(ncData.copy(), coords=[[1],level,lat,lon], dims=['time','level','lat','lon'])

                    ncData['time'].values = [time]
                    tmp_list.append(ncData)

                returnData = xr.concat(tmp_list, dim='time')
                returnData = self.partitioned_data(returnData)

                if self.unit_convert:
                    convert_type, convert_value = self.unit_convert.split("_")
                    returnData = convert_data(returnData, convert_type, convert_value)

                data_list.append(returnData)
        else:
            if self.dataInputPaths.find("low") == -1:
                tmpdata = xr.open_dataset("/nfsshare1/cdbdata/data/NEMO/highres/sst/ltm/day/0101.nc")['sst'][:]
                lon = tmpdata['lon'].values
                lat = tmpdata['lat'].values
                shapes = list([1, len(lat), len(lon)])
            else:
                tmpdata = xr.open_dataset("/nfsshare1/cdbdata/data/NEMO/lowres/sst/ltm/day/0101.nc")['sst'][:]
                lon = tmpdata['lon'].values
                lat = tmpdata['lat'].values
                shapes = list([1, len(lat), len(lon)])
            # 打开文件并读取数据
            if self.dataInputPaths:
                tmp_list = []
                for i, time in enumerate(file_time):
                    if self.timeTypes=="day":
                        out = self.dataInputPaths + time[0:4] + "/" + time[4:6] + "/" + time + ".nc"
                    else:
                        out = self.dataInputPaths + time[0:4] + "/"+ time + ".nc"
                    if os.path.exists(out):
                        ds = xr.open_dataset(out)
                        ncData = ds[self.elements]
                    else:
                        ncData = np.full(shapes,np.nan)
                        ncData = xr.DataArray(ncData.copy(), coords=[[1],lat,lon], dims=['time','lat','lon'])

                    ncData['time'].values = [time]
                    tmp_list.append(ncData)

                returnData = xr.concat(tmp_list, dim='time')
                returnData = self.partitioned_data(returnData)

                if self.unit_convert:
                    convert_type, convert_value = self.unit_convert.split("_")
                    returnData = convert_data(returnData, convert_type, convert_value)

                data_list.append(returnData)

        if self.ltmDataInputPaths:
            tmp_list = []
            for i, time in enumerate(file_time):
                if self.timeTypes == "year":
                    outjp = self.ltmDataInputPaths + "year/year_1981-2010.nc"
                else:
                    outjp = self.ltmDataInputPaths + self.timeTypes + "/" + time[4:] + ".nc"

                ncDataJp = xr.open_dataset(outjp)[self.elements][:]
                ncDataJp = ncDataJp.expand_dims(time=1, axis=0)

                ncDataJp['time'].values = [time]
                tmp_list.append(ncDataJp)

            returnDataJp = xr.concat(tmp_list, dim='time')
            returnDataJp = self.partitioned_data(returnDataJp)

            if self.unit_convert:
                convert_type, convert_value = self.unit_convert.split("_")
                returnDataJp = convert_data(returnDataJp, convert_type, convert_value)

            data_list.append(returnDataJp)

        outputData["outputData"] = data_list
        self.output_data = outputData

        # return self.proData

    # 截取数据
    def intercept_data(self, data, start_value, end_value, dims, dim):
        '''

        :param data: 截取数据
        :param start_value: 开始值
        :param end_value: 结束值
        :param dim: 截取维度
        :param dims: 数据维度
        :return:
        '''
        intercept_data = data[dim]
        end_index = 0
        count = 0
        dim_order = 0
        for data_index, intercept_data_value in enumerate(intercept_data):
            if start_value <= intercept_data_value <= end_value:
                count = count + 1
                end_index = data_index
        for dims_index, dim_item in enumerate(dims):
            if dim_item == dim:
                dim_order = dims_index

        # 判断数据维度
        if dim_order == 0:
            data[self.elements] = data[self.elements][end_index - count + 1:end_index + 1]
        elif dim_order == 1:
            data[self.elements] = data[self.elements][:, end_index - count + 1:end_index + 1]
        elif dim_order == 2:
            data[self.elements] = data[self.elements][:, :, end_index - count + 1:end_index + 1]
        elif dim_order == 3:
            data[self.elements] = data[self.elements][:, :, :, end_index - count + 1:end_index + 1]
        data[dim] = data[dim][end_index - count + 1:end_index + 1]

        return data

    def partitioned_data(self, data):
        nc_data = data
        if self.level:
            # if isinstance(self.level,int):
            #     self.level = [self.level,self.level]
            # start_level, end_level = [float(level) for level in self.level]
            if not self.level.__contains__(","):
                self.level = self.level + "," + self.level
            start_level, end_level = [float(level) for level in self.level.split(",")]
            level = data["level"]
            level = level[(level >= start_level) & (level <= end_level)]
            nc_data = nc_data.sel(level=level)
            # self.intercept_data(data, start_level, end_level, dims, "level")
        if self.regions:
            start_lon, end_lon, start_lat, end_lat = [float(region) for region in self.regions.split(",")]

            lon = data["lon"]
            lat = data["lat"]
            lon = lon[(lon >= start_lon) & (lon <= end_lon)]
            lat = lat[(lat >= start_lat) & (lat <= end_lat)]
            nc_data = nc_data.sel(lon=lon, lat=lat)
            # self.intercept_data(data, start_lon, end_lon, dims, "lon")
            # self.intercept_data(data, start_lat, end_lat, dims, "lat")
        return nc_data

# if __name__ == '__main__':
#     sub_local_params = {
#         "elements": "sst",
#         "dataInputPaths": "/nfsshare/cdbdata/data/NEMO/lowres/sst/day/",
#         # "dataInputPaths": "",
#         "ltmDataInputPaths":"/nfsshare/cdbdata/data/NEMO/lowres/sst/ltm/",
#         "timeRanges": ['20200405','20200411'],
#         "timeType": "day",
#         "regions": "30,180,-20,60",
#         "unitConvert": "",
#         "levels": ""
#     }
#     algorithm_input_data = []
#     a = NcDataSingleTime(sub_local_params,algorithm_input_data)
#     a.execute()
#     print(a.output_data)