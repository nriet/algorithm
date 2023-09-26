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
from com.nriet.utils.result.ResponseResultUtils import build_response_dict
from com.nriet.config.ResponseCodeAndMsgEum import PARAMETER_VALUE_MISSING_CODE, \
    PARAMETER_VALUE_MISSING_MSG, CUSTOM_ERROR_CODE, CUSTOM_ERROR_MSG
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.algorithm.business.ExtendedPeriodModeData import ExtendedPeriodModeData


class GainSingleModeData(InputDataComponent):

    def __init__(self):
        # 加载数据源配置
        dataSourceConfigPath = PathConfig.CPCS_ROOT_PATH + 'com/nriet/config/dataSourceConfig3.json'
        with open(dataSourceConfigPath, "r", encoding='UTF-8') as f:
            datasourcestr = f.read()
        self.datasource_config = json.loads(datasourcestr)


    def init_param(self, params):
        """
        初始化参数
        Args:
            params:

        Returns:

        """
        # 起报时间尺度
        self.reportTimeType = params.get("reportTimeType")
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
        self.element = params.get("element")
        # 统计方式
        self.eleType = params.get("eleType")
        # 区域编码
        self.areaCode = params.get("areaCode")
        # 绘图数据中心经度   180 或 0  默认180
        self.drawCenterLon = params.get("drawCenterLon")

        self.dataOutputPath = params.get("dataOutputPath")
        self.var = params.get("var")

    # 获取nc数据
    def execute(self, params):
        # 1.初始化参数
        self.init_param(params)
        result_dict = build_response_dict()
        if self.dataSource in ["CPSV3","CFSV2","NCC","CFS2","JMA3","UKMO5","EC5","CPSV3MON"]:
            mode_data = self.get_single_data(self.dataSource, self.element, self.eleType, self.reportTimeType,
                                             self.timeType, self.forecastTime, self.startTime, self.endTime,
                                             "115,125,25,34")

        if self.dataSource in ["CFSV2MON"]:
            mode_data = self.get_single_dm_data(self.dataSource, self.element, self.eleType, self.reportTimeType,
                                             self.timeType, self.forecastTime, self.startTime, self.endTime,
                                             "115,125,25,34")
        if self.dataSource in ["MODE_WMME","MODE_MME","CMMEV2MON","SEDES"]:
            mode_data = self.get_single_mode_data(self.dataSource, self.element, self.forecastTime, self.startTime,
                                                  self.endTime, "115,123,27,32")

        glon = np.linspace(117, 123, 61)
        glat = np.linspace(27, 32, 51)
        mode_data = mode_data.interp(lat=glat,lon=glon)
        mode_data = mode_data.sortby(mode_data["lat"], ascending=False)
        # print(mode_data)
        self.writ_nc([mode_data], self.var, self.dataOutputPath)
        # print(res_list)
        result_dict["output_file_name"] = self.dataOutputPath
        result_dict["output_img_name"] = self.dataOutputPath.replace(".nc", ".png")
        return result_dict

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

    def get_single_mode_data(self,data_source, element, forecastTime, startTime, endTime, region):
        dataCfg = self.datasource_config[data_source.upper()+"_"+element.upper()+"_MON"]
        dataInputPath = dataCfg["dataInputPath"]
        var = dataCfg["var"]
        fStartMon = int(dataCfg["start"])
        fEndMon = int(dataCfg["end"])
        dataInputPath_ym = dataInputPath.replace("#YYYYMM#", forecastTime)
        foreStartTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), fStartMon)
        foreEndTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), fEndMon)
        # print(forecastTime,foreStartTime,foreEndTime)
        # 获取模式预报起止时间内所有预报时间
        time_list = DateUtils.get_time_list([foreStartTime, foreEndTime], "mon")
        startIndex = time_list.index(startTime)
        endIndex = time_list.index(endTime)
        ds = xr.open_dataset(dataInputPath_ym, decode_times=False)
        lat = ds.lat
        lon = ds.lon
        tmpdata = ds[var]
        # 截取指定区域范围的数据
        startLon, endLon, startLat, endLat = [float(value) for value in region.split(',')]
        lon_range = lon[(lon >= startLon) & (lon <= endLon)]
        lat_range = lat[(lat >= startLat) & (lat <= endLat)]
        tmpdata = tmpdata.sel(lon=lon_range, lat=lat_range)
        # print(tmpdata)
        modedata = tmpdata[startIndex:endIndex + 1]
        # 重置时间维信息
        modedata['time'] = time_list[startIndex:endIndex + 1]
        modedata = modedata.mean(dim="time")
        return modedata

    def get_single_data(self,data_source, element, eleType, reportTimeType, timeType, forecastTime, startTime, endTime, region):
        logging.info("预报时间尺度【%s】转换到起报时间尺度【%s】前的预报时间范围是==>[%s,%s]" % (timeType, reportTimeType, startTime, endTime))
        tmp_start_time, tmp_end_time = startTime, endTime
        # 将预报时间尺度转换到起报时间尺度查询数据
        if reportTimeType == "day" and timeType != "day":
            if timeType == "week":
                tmp_start_time = DateUtils.day2Week(forecastTime, startTime)[0]
                tmp_end_time = DateUtils.day2Week(forecastTime, endTime)[1]
            else:
                tmp_start_time = DateUtils.otherTime2Day(startTime, timeType)[0]
                tmp_end_time = DateUtils.otherTime2Day(endTime, timeType)[1]
        if reportTimeType == "mon" and timeType != "mon":
            tmp_start_time = DateUtils.otherTime2Month(startTime, timeType)[0]
            tmp_end_time = DateUtils.otherTime2Month(endTime, timeType)[1]
        logging.info("预报时间尺度【%s】转换到起报时间尺度【%s】后的预报时间范围是==>[%s,%s]" % (timeType, reportTimeType, tmp_start_time, tmp_end_time))
        #
        dataCfg = self.datasource_config[data_source.upper() + "_" + element.upper() + "_"+reportTimeType.upper()]
        dataInputPath = dataCfg["dataInputPath"]
        ltmDataInputPath = dataCfg["ltmDataInputPath"]
        unitConvert = dataCfg["unitConvert"]
        var = dataCfg["var"]
        start_lon, end_lon, start_lat, end_lat = [float(region) for region in region.split(",")]
        sub_local_params = {}
        sub_local_params["patternDataName"] = data_source
        # 若开始经度 或 结束经度小于0  取全球数据
        if start_lon < 0 or end_lon < 0:
            sub_local_params["regions"] = "0,360,-90,90"
        else:
            sub_local_params["regions"] = region
        sub_local_params["reportingTime"] = forecastTime
        sub_local_params["forecastPeriod"] = [tmp_start_time, tmp_end_time]
        # sub_local_params["forecastPeriod"] = self.timeRanges
        sub_local_params["dataSet"] = "mn"
        sub_local_params["elements"] = var
        sub_local_params["unitConvert"] = unitConvert
        sub_local_params["whetherMakeup"] = "True"


        if eleType == "SK":
            sub_local_params["dataInputPaths"] = dataInputPath
        if eleType == "JP":
            sub_local_params["dataInputPaths"] = dataInputPath
            sub_local_params["ltmDataInputPaths"] = ltmDataInputPath
        if eleType == "LTM":
            sub_local_params["ltmDataInputPaths"] = ltmDataInputPath
        algorithm_input_data = []
        epmd = ExtendedPeriodModeData(sub_local_params, algorithm_input_data)
        epmd.execute()
        fore_data = epmd.output_data["outputData"]

        if eleType == "SK":
            foreGridData = fore_data[0]
            # 降水求和 其他要素求平均
            if element in ["PRATE"]:
                # 降维求和修改 胡玉恒 20210413
                tmpdata = foreGridData.mean(dim="time")
                tmpdata = tmpdata.where(np.isnan(tmpdata), 1)
                foreGridData = foreGridData.sum(dim="time")
                foreGridData = foreGridData * tmpdata
            else:
                foreGridData = foreGridData.mean(dim="time")

        if eleType == "JP":
            foreGridData = fore_data[0]
            foreLtmGridData = fore_data[1]
            if element in ["PRATE"]:
                # 降维求和修改 胡玉恒 20210413
                tmpdata = foreGridData.mean(dim="time")
                tmpdata = tmpdata.where(np.isnan(tmpdata), 1)
                foreGridData = foreGridData.sum(dim="time")
                foreGridData = foreGridData * tmpdata

                tmpltmdata = foreLtmGridData.mean(dim="time")
                tmpltmdata = tmpltmdata.where(np.isnan(tmpltmdata), 1)
                foreLtmGridData = foreLtmGridData.sum(dim="time")
                foreLtmGridData = foreLtmGridData * tmpltmdata

                foreGridData = (foreGridData - foreLtmGridData) / foreLtmGridData * 100
            else:
                foreGridData = foreGridData.mean(dim="time")
                foreLtmGridData = foreLtmGridData.mean(dim="time")
                foreGridData = foreGridData - foreLtmGridData

        if eleType == "LTM":
            foreGridData = fore_data[0]

            # 降水求和 其他要素求平均
            if element in ["PRATE"]:
                # 降维求和修改 胡玉恒 20210413
                tmpdata = foreGridData.mean(dim="time")
                tmpdata = tmpdata.where(np.isnan(tmpdata), 1)
                foreGridData = foreGridData.sum(dim="time")
                foreGridData = foreGridData * tmpdata
            else:
                foreGridData = foreGridData.mean(dim="time")
        # 经度转换成西经——>东经 并根据范围截取数据
        foreGridData = self.partitioned_data(foreGridData,region)
        # 绘图数据处理
        if self.drawCenterLon and self.drawCenterLon == "180":
            long = foreGridData.lon
            long = xr.where(long < 0, long + 360, long)
            foreGridData["lon"].values = long.values
            foreGridData = foreGridData.sortby(foreGridData["lon"])
        # 数据的纬度处理成从北到南（即从大到小）
        foreGridData = foreGridData.sortby(foreGridData["lat"], ascending=False)
        return foreGridData

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

    def get_single_dm_data(self,data_source, element, eleType, reportTimeType, timeType, forecastTime, startTime, endTime, region):
        dataCfg = self.datasource_config[data_source.upper() + "_" + element.upper() + "_"+reportTimeType.upper()]
        dataInputPath = dataCfg["dataInputPath"]
        dataInputPath_ym = dataInputPath.replace("#YYYYMMDD#", forecastTime).replace("#YYYYMM#", endTime).replace("#YYYY#", forecastTime[0:4])
        unitConvert = dataCfg["unitConvert"]
        var = dataCfg["var"]
        ds = xr.open_dataset(dataInputPath_ym, decode_times=False)
        modedata = ds[var]
        modedata = self.partitioned_data(modedata, region)
        # 数据的纬度处理成从北到南（即从大到小）
        modedata = modedata.sortby(modedata["lat"], ascending=False)
        return modedata


if __name__ == "__main__":
    try:
        t1 = DateUtils.getTimeStamp()
        # 获取页面传参
        page_params = ast.literal_eval(sys.argv[1])
        # page_params = {"reportTimeType": "mon",
        #                "timeType": "mon",
        #                "forecastTime": "202304",
        #                "startTime": "202305",
        #                "endTime": "202305",
        #                "dataSource": "UKMO5",
        #                "dataOutputPath": "/nfsshare/cdbdata/data/dry_data/txex1.nc",
        #                "var": "avgt",
        #                "eleType": "JP",
        #                "areaCode": "33",
        #                "element": "AVGT"}
        gs2gd = GainSingleModeData()
        result_dict = gs2gd.execute(page_params)
        t2 = DateUtils.getTimeStamp()
        logging.info("获取模式色斑数据总耗时: %s ms" % (str(t2 - t1)))
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
