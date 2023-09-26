#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2023/06/14
# @Author : Sbiys
# @File : GainStation2GirdData.py

import os, sys, json, ast
import xarray as xr
import numpy as np
import logging, traceback
logger = logging.getLogger(__name__)
logger.root.setLevel(level=logging.INFO)
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
logging.info(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from com.nriet.algorithm.common.inputData.InputDataComponent import InputDataComponent
from com.nriet.utils import DateUtils
from com.nriet.config import PathConfig
from com.nriet.utils.GridDataUtils import GridDataUtils
from com.nriet.utils.fileUtils import convert_data
from com.nriet.utils.result.ResponseResultUtils import build_response_dict
from com.nriet.config.ResponseCodeAndMsgEum import PARAMETER_VALUE_MISSING_CODE, \
    PARAMETER_VALUE_MISSING_MSG, CUSTOM_ERROR_CODE, CUSTOM_ERROR_MSG
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException


class GainMonitorGridData(InputDataComponent):

    def __init__(self):
        # 加载数据源配置
        dataSourceConfigPath = PathConfig.CPCS_ROOT_PATH + 'com/nriet/config/dataSourceConfig.json'
        with open(dataSourceConfigPath, "r", encoding='UTF-8') as f:
            datasourcestr = f.read()
        self.datasource_config = json.loads(datasourcestr)
        # 初始化获取格点数据的工具类
        self.GDU = GridDataUtils()


    def init_param(self, params):
        """
        初始化参数
        Args:
            params:

        Returns:

        """
        # 时间尺度
        self.timeType = params.get("timeType")
        # 起报时间
        self.forecastTime = params.get("forecastTime")
        # 预报开始时间
        self.startTime = params.get("startTime")
        # 预报结束时间
        self.endTime = params.get("endTime")
        # 数据源源
        self.dataSource = params.get("dataSource")
        # 要素
        self.elements = params.get("elements")
        # 统计量类型
        self.eleType = params.get("eleType")
        # 经纬度范围
        self.regions = params.get("regions")
        # 常年值
        self.ltm = params.get("ltm","1991-2020")
        # 高度层
        self.level = params.get("level")
        self.logicValue = params.get("logicValue")
        # 绘图数据中心经度   180 或 0  默认180
        self.drawCenterLon = params.get("drawCenterLon")
        # 位势高度数据单位特殊处理
        self.hgtUnitConvert = params.get("hgtUnitConvert")
        # 数据文件输出位置
        self.dataOutputPath = params.get("dataOutputPath")
        # 数据文件的变量名
        self.resVar = params.get("resVar")


    # 获取nc数据
    def execute(self, params):
        # 1.初始化参数
        self.init_param(params)
        result_dict = build_response_dict()
        key = self.dataSource.upper()+"_"+self.elements.upper()+"_"+self.timeType.upper()
        ele_config = self.datasource_config.get(key)
        data_list = self.get_data_from_nas(time_type=self.timeType, start_time=self.startTime,
                                           end_time=self.endTime, ele=self.elements,
                                           regions=self.regions, level=self.level, eleType=self.eleType,
                                           unitConvert=ele_config["unitConvert"],
                                           dataInputPaths=ele_config["dataInputPath"],
                                           ltmDataInputPaths=ele_config["ltmDataInputPath"], var=ele_config["var"],
                                           climateYear=self.ltm,logicValue=self.logicValue)
        # print(data_list)
        self.writ_nc(data_list, self.resVar, self.dataOutputPath)
        result_dict["output_file_name"] = self.dataOutputPath
        result_dict["output_img_name"] = self.dataOutputPath.replace(".nc", ".png")
        return result_dict

    def get_data_from_nas(self, time_type: str, start_time: str, end_time: str, ele: str, regions: str,
                          level: str, eleType: str, unitConvert: str, dataInputPaths: str, ltmDataInputPaths: str,
                          var: str, climateYear: str = None,logicValue: str = None):
        nas_data_list = []
        if ele in ["WIND"]:
            tmp_var_list = var.split(",")
            tmp_dataInputPaths_list = dataInputPaths.split(",")
            tmp_ltmDataInputPaths_list = ltmDataInputPaths.split(",")
            for k, tmpVar in enumerate(tmp_var_list):
                nas_data = self.get_single_data(ele, tmp_dataInputPaths_list[k], tmp_ltmDataInputPaths_list[k],
                                                time_type, start_time, end_time, tmpVar, regions, level, eleType,
                                                unitConvert, climateYear,logicValue)
                nas_data_list.append(nas_data)
        else:
            nas_data = self.get_single_data(ele, dataInputPaths, ltmDataInputPaths, time_type, start_time, end_time,
                                            var, regions, level, eleType, unitConvert, climateYear,logicValue)
            nas_data_list.append(nas_data)
        return nas_data_list

    def get_single_data(self, elementName, dataInputPath, ltmDataInputPath, timeType, startTime, endTime, var, regions,
                        levels, eleType, unitConvert, climateYear,logicValue):
        # 降水距平百分率的处理
        if elementName in ["PRATE", "PR_WTR", "PRECIP", "STA_PRATE"] and eleType == "JP":
            eleType = "AP"
        # 获取数据范围处理
        org_regions = regions
        start_lon, end_lon, start_lat, end_lat = [float(region) for region in regions.split(",")]
        if start_lon < 0 or end_lon < 0:
            regions = "0,360,-90,90"
        # 设置降维的维度及方法
        stat_type_list = []
        stat_dim_list = []
        # 针对时间维的处理
        # 降水 累积能量 活动路径密度
        if elementName in ["PRATE", "PR_WTR", "PRECIP", "ACE", "HDLJMD", "SSRD"]:
            stat_dim_list.append("time")
            stat_type_list.append("sum")
        else:
            stat_dim_list.append("time")
            stat_type_list.append("avg")
        # 对层次的处理
        if levels == "0000":
            levels = ""
        # 若传递高度层，则需要对高度层求平均
        if levels:
            stat_dim_list.append("level")
            stat_type_list.append("avg")

        # 根据统计类型计算数据
        # 实况
        if eleType == "SK":
            if elementName in ["RDAY","HTDAY"]:
                gridData = self.get_single_mean_rs(dataInputPath, timeType, startTime, endTime, var, regions, levels,
                                                     unitConvert,elementName,logicValue)
            else:
                gridData = self.get_single_mean_data(dataInputPath, timeType, startTime, endTime, var, regions, levels,
                                                     unitConvert)
                gridData = self.reduced_dimension(gridData, stat_type_list, stat_dim_list)
        # 气候态
        if eleType == "LTM":
            gridData = self.get_single_ltm_data(ltmDataInputPath, timeType, startTime, endTime, var, regions, levels,
                                                 unitConvert, climateYear)
            gridData = self.reduced_dimension(gridData, stat_type_list, stat_dim_list)
        # 距平
        if eleType == "JP":
            gridData = self.get_single_mean_data(dataInputPath, timeType, startTime, endTime, var, regions, levels,
                                                  unitConvert)
            # 20℃等温线数据本身就是距平数据，不需要减常年值，其它要素则需要减常年值
            if self.elements != "DEPTH20":
                ltm_data = self.get_single_ltm_data(ltmDataInputPath, timeType, startTime, endTime, var, regions,
                                                    levels, unitConvert, climateYear)
                gridData = gridData - ltm_data
            gridData = self.reduced_dimension(gridData, stat_type_list, stat_dim_list)
        # 距平百分率
        if eleType == "AP":
            gridData = self.get_single_mean_data(dataInputPath, timeType, startTime, endTime, var, regions, levels,
                                                 unitConvert)
            ltm_data = self.get_single_ltm_data(ltmDataInputPath, timeType, startTime, endTime, var, regions, levels,
                                                unitConvert, climateYear)
            gridData = self.reduced_dimension(gridData, stat_type_list, stat_dim_list)
            ltm_data = self.reduced_dimension(ltm_data, stat_type_list, stat_dim_list)
            ltm_data = np.where(ltm_data == 0, 0.1, ltm_data)
            gridData = (gridData - ltm_data) * 100 / ltm_data
        #  根据范围截取数据
        gridData = self.partitioned_data(gridData, org_regions)
        # 绘图数据处理
        if self.drawCenterLon and self.drawCenterLon == "180":
            long = gridData.lon
            long = xr.where(long < 0, long + 360, long)
            gridData["lon"].values = long.values
            gridData = gridData.sortby(gridData["lon"])
        # 数据的纬度处理成从北到南（即从大到小）
        gridData = gridData.sortby(gridData["lat"], ascending=False)

        return gridData

    def get_single_mean_data(self, dataInputPath, timeType, startTime, endTime, var, regions, levels, unitConvert):
        grid_mean_data = self.GDU.get_grid_mean_data(dataInputPath, timeType, startTime, endTime, var, regions, levels)
        # 单位处理
        if unitConvert and grid_mean_data.any():
            convert_type, convert_value = unitConvert.split("_")
            grid_mean_data = convert_data(grid_mean_data, convert_type, convert_value)
        # 位势高度单位特殊处理
        if self.hgtUnitConvert and grid_mean_data.any():
            convert_type, convert_value = self.hgtUnitConvert.split("_")
            grid_mean_data = convert_data(grid_mean_data, convert_type, convert_value)
        return grid_mean_data

    def get_single_ltm_data(self, ltmDataInputPath, timeType, startTime, endTime, var, regions, levels, unitConvert, climateYear):
        grid_ltm_data = self.GDU.get_grid_ltm_data(ltmDataInputPath, timeType, startTime, endTime, var, regions,
                                                   levels, climateYear)
        # 单位处理
        if unitConvert and grid_ltm_data.any():
            convert_type, convert_value = unitConvert.split("_")
            grid_ltm_data = convert_data(grid_ltm_data, convert_type, convert_value)
        # 位势高度单位特殊处理
        if self.hgtUnitConvert and grid_ltm_data.any():
            convert_type, convert_value = self.hgtUnitConvert.split("_")
            grid_ltm_data = convert_data(grid_ltm_data, convert_type, convert_value)
        return grid_ltm_data

    def get_single_mean_rs(self, dataInputPath, timeType, startTime, endTime, var, regions, levels, unitConvert, elements, logicValue):
        m_level = "" if levels=="0000" else levels
        grid_mean_data = self.GDU.get_grid_mean_data(dataInputPath, timeType, startTime, endTime, var, regions, m_level)
        # 单位处理
        if unitConvert and grid_mean_data.any():
            convert_type, convert_value = unitConvert.split("_")
            grid_mean_data = convert_data(grid_mean_data, convert_type, convert_value)
        # 降水日数
        if elements == "RDAY":
            # 缺测设置为0
            grid_mean_data = xr.where(np.isnan(grid_mean_data), 0, grid_mean_data)
            #解析统计逻辑和阈值
            logicType = logicValue[0:2]
            thresholdValue = float(logicValue[2:])
            if logicType == "ge":
                grid_mean_data = xr.where(grid_mean_data >= thresholdValue, 1, 0)
            if logicType == "gt":
                grid_mean_data = xr.where(grid_mean_data > thresholdValue, 1, 0)
            grid_mean_data = grid_mean_data.sum(dim="time")
        # 高温日数
        if elements == "HTDAY":
            # 缺测设置为0
            grid_mean_data = xr.where(np.isnan(grid_mean_data), 0, grid_mean_data)
            # 解析统计逻辑和阈值
            logicType = logicValue[0:2]
            thresholdValue = float(logicValue[2:])
            if logicType == "ge":
                grid_mean_data = xr.where(grid_mean_data >= thresholdValue, 1, 0)
            if logicType == "gt":
                grid_mean_data = xr.where(grid_mean_data > thresholdValue, 1, 0)
            grid_mean_data = grid_mean_data.sum(dim="time")
        return grid_mean_data

    def partitioned_data(self, par_data, regions):
        nc_data = par_data
        start_lon, end_lon, start_lat, end_lat = [float(region) for region in regions.split(",")]
        if regions is not None:
            # 若开始经度或结束经度小于0  根据范围截取数据
            if start_lon < 0 or end_lon < 0:
                # 经度转换成 西经—>东经
                lonx = nc_data.lon
                lonx = xr.where(lonx > 180, lonx - 360, lonx)
                nc_data["lon"].values = lonx.values
                nc_data = nc_data.sortby(nc_data["lon"])
                lon = nc_data["lon"]
                lat = nc_data["lat"]
                lon = lon[(lon >= start_lon) & (lon <= end_lon)]
                lat = lat[(lat >= start_lat) & (lat <= end_lat)]
                nc_data = nc_data.sel(lon=lon, lat=lat)
                # 经度转换成 0—>360
                long = nc_data.lon
                long = xr.where(long < 0, long + 360, long)
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

    # 数据降维
    def reduced_dimension(self, data, statTypes, statDims):
        reDimData = data
        for i, dim in enumerate(statDims):
            stat = statTypes[i]
            if stat == "avg":
                if np.isnan(np.nanmean(reDimData.values)):
                    reDimData = reDimData.mean(dim=dim, keep_attrs=True)
                    reDimData.values = np.full(reDimData.shape, np.nan)
                else:
                    reDimData = reDimData.mean(dim=dim, keep_attrs=True)
            elif stat == "min":
                if np.isnan(np.nanmean(reDimData.values)):
                    reDimData = reDimData.min(dim=dim, keep_attrs=True)
                    reDimData.values = np.full(reDimData.shape, np.nan)
                else:
                    reDimData = reDimData.min(dim=dim, keep_attrs=True)
            elif stat == "max":
                if np.isnan(np.nanmean(reDimData.values)):
                    reDimData = reDimData.max(dim=dim, keep_attrs=True)
                    reDimData.values = np.full(reDimData.shape, np.nan)
                else:
                    reDimData = reDimData.max(dim=dim, keep_attrs=True)
            elif stat == "sum":
                # 降维求和修改 胡玉恒 20210413
                tmpdata = reDimData.mean(dim=dim, skipna=True, keep_attrs=True)
                tmpdata = tmpdata.where(np.isnan(tmpdata), 1)
                reDimData = reDimData.sum(dim=dim, skipna=True, keep_attrs=True)
                reDimData = reDimData * tmpdata
        return reDimData


if __name__ == "__main__":
    try:
        t1 = DateUtils.getTimeStamp()
        # 获取页面传参
        page_params = ast.literal_eval(sys.argv[1])
        # page_params = {"timeType": "day",
        #                "startTime": "20200201",
        #                "endTime": "20200215",
        #                "dataSource": "CLDAS",
        #                "eleType": "SK",
        #                "logicValue": "ge1",
        #                "regions": "115,125,25,34",
        #                "ltm": "1991-2020",
        #                "elements": "RDAY",
        #                "level": "0000",
        #                "dataOutputPath": "/nfsshare/cdbdata/data/dry_data/test_jsrs_sk.nc",
        #                "resVar": "jsrs_sk"}
        gs2gd = GainMonitorGridData()
        result_dict = gs2gd.execute(page_params)
        t2 = DateUtils.getTimeStamp()
        logging.info("获取监测格点色斑数据总耗时: %s ms" % (str(t2 - t1)))
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
