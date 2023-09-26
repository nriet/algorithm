#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time: 2023/7/17
# @Author: Shiys
# @File: GainMultiTimeTestData.py
import ast
import json
import logging
import os
import sys
import traceback

import numpy as np
import pandas as pd
import xarray as xr
from metpy.interpolate import remove_nan_observations
logger = logging.getLogger(__name__)
logger.root.setLevel(level=logging.INFO)
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
logging.info(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from com.nriet.algorithm.common.inputData.InputDataComponent import InputDataComponent
from com.nriet.utils import DateUtils, AlgorithmUtils
from com.nriet.config import PathConfig
from com.nriet.utils.result.ResponseResultUtils import build_response_dict
from com.nriet.config.ResponseCodeAndMsgEum import PARAMETER_VALUE_MISSING_CODE, \
    PARAMETER_VALUE_MISSING_MSG, CUSTOM_ERROR_CODE, CUSTOM_ERROR_MSG, DB_DATA_NOT_FOUND_ERROR_CODE
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.utils.fileUtils import creatTxtFile
from com.nriet.algorithm.business.ExtendedPeriodModeData import ExtendedPeriodModeData
from com.nriet.algorithm.business.StationDataForGbase import StationDataForGbase
from com.nriet.algorithm.business.StationInfoDataForGbase import StationInfoDataForGbase


class GainMultiTimeFloodSeasonTestData(InputDataComponent):

    def __init__(self):
        # 加载数据源配置
        dataSourceConfigPath = PathConfig.CPCS_ROOT_PATH + 'com/nriet/config/dataSourceConfig3.json'
        with open(dataSourceConfigPath, "r", encoding='UTF-8') as f:
            datasourcestr = f.read()
        self.datasource_config = json.loads(datasourcestr)
        # 加载城市数据源配置
        cityConfigPath = PathConfig.CPCS_ROOT_PATH + 'com/nriet/config/cityConfig.json'
        with open(cityConfigPath, "r", encoding='UTF-8') as f:
            citystr = f.read()
        self.city_config = json.loads(citystr)
        # 加载代表站数据
        dbzpath = PathConfig.CPCS_ROOT_PATH + 'com/nriet/config/ZJDBZ.txt'
        data = pd.read_table(dbzpath, header=None, encoding='utf-8', sep=" ")
        stationInfo = np.array(data)
        locs = ['station', 'lon', 'lat']
        stations = stationInfo[:, 0]
        stationInfoData = xr.DataArray(stationInfo, coords=[stations, locs], dims=['station', 'space'])
        self.staInfoData = stationInfoData
        pass

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
        # 检验方法
        self.methodType = params.get("methodType")
        # 区域编码
        self.areaCode = params.get("areaCode")
        # 表格数据输出位置
        self.dataOutputPath = params.get("dataOutputPath")

    # 获取nc数据
    def execute(self, params):
        # 1.初始化参数
        self.init_param(params)
        result_dict = build_response_dict()
        # 根据起报起止时间和预报时效推算出监测数据的最大集的起止时间
        forecastStartTime, forecastEndTime = self.forecastTime.split(",")[0], self.forecastTime.split(",")[1]
        forecast_time_list = DateUtils.get_time_list([forecastStartTime,forecastEndTime],self.reportTimeType)
        xunqi_forecast_time_list = []
        for ft in forecast_time_list:
            if ft[4:] in ["02","03","04","05","06","07"]:
                xunqi_forecast_time_list.append(ft)
        print(xunqi_forecast_time_list)
        moniStartTime = xunqi_forecast_time_list[0][0:4]+"05"
        moniEndTime = xunqi_forecast_time_list[-1][0:4]+"09"
        print(moniStartTime,moniEndTime)
        # 获取站点监测数据
        moni_data_list = self.get_station_data("mon", moniStartTime, moniEndTime, self.element, self.areaCode)
        moni_sk_data = moni_data_list[0]
        moni_ltm_data = moni_data_list[1]
        staInfoData = moni_data_list[2]
        moni_data = moni_sk_data
        if self.methodType in ["PS","PC","ACC","SYMBOLRATE"]:
            moni_data = moni_data - moni_ltm_data
        # 获取模式数据
        data_source_list = self.dataSource.split(",")
        jy_data = np.full((len(xunqi_forecast_time_list), len(data_source_list)), np.nan)
        for i, forecat_time in enumerate(xunqi_forecast_time_list):
            forecatYear, forecatMon = forecat_time[0:4], forecat_time[4:]
            if forecatMon in ["02","03","04"]:
                tmpStartTime = forecatYear+"05"
                tmpEndTime = forecatYear+"09"
            if forecatMon in ["05","06","07"]:
                tmpStartTime = forecatYear+"0"+ str(int(forecatMon)+1)
                tmpEndTime = forecatYear+"09"
            tmp_time_list = DateUtils.get_time_list([tmpStartTime,tmpEndTime],"mon")
            print(forecat_time,tmpStartTime,tmpEndTime)
            moni_data_m = moni_data.sel(time=tmp_time_list)
            moni_data_avg = moni_data_m.mean(dim="time")
            if self.methodType in ["SCC", "SRMSE"]:
                moni_ltm_data_m = moni_ltm_data.sel(time=tmp_time_list)
            for j, data_source in enumerate(data_source_list):
                if forecatMon == "02" and data_source in ["JMA3", "UKMO5", "EC5","MODES_WMME", "MODES_MME", "CMMEV2MON", "SEDES", "CPSV3MON"]:
                    continue
                if forecatMon == "03" and data_source in ["UKMO5","MODES_WMME", "MODES_MME", "SEDES"]:
                    continue
                if data_source in ["CFSV2", "CPSV3", "NCC", "CFS2", "JMA3", "UKMO5", "EC5", "CPSV3MON"]:
                    if self.methodType in ["PS", "PC", "ACC","SYMBOLRATE"]:
                        staticType = "JP"
                    if self.methodType in ["SCC", "SRMSE"]:
                        staticType = "SK"
                    mode_data = self.get_single_data(data_source, self.element, staticType, self.reportTimeType,
                                                     "mon", forecat_time, tmpStartTime, tmpEndTime,
                                                     "115,125,25,34")
                    if mode_data is None:
                        continue
                    # 模式插值到站点数据
                    m2s_data = mode_data.interp(lat=staInfoData.sel(space="lat"), lon=staInfoData.sel(space="lon"))
                    m2s_data_avg = m2s_data.mean(dim="time")
                if data_source in ["CFSV2MON"]:
                    mode_data = self.get_single_dm_data(data_source, self.element, self.reportTimeType,
                                                        "mon", forecat_time, tmpStartTime, tmpEndTime,
                                                        "115,125,25,34")
                    if mode_data is None:
                        continue
                    # 模式插值到站点数据
                    m2s_data = mode_data.interp(lat=staInfoData.sel(space="lat"), lon=staInfoData.sel(space="lon"))
                    if self.methodType in ["SCC", "SRMSE"]:
                        m2s_data = m2s_data + moni_ltm_data_m
                    m2s_data_avg = m2s_data.mean(dim="time")
                if data_source in ["MODES_WMME", "MODES_MME", "CMMEV2MON", "SEDES"]:
                    mode_data = self.get_single_mode_data(data_source, self.element, self.reportTimeType,
                                                          "mon", forecat_time, tmpStartTime, tmpEndTime,
                                                          "115,125,25,34")
                    if mode_data is None:
                        continue
                    # 模式插值到站点数据
                    m2s_data = mode_data.interp(lat=staInfoData.sel(space="lat"), lon=staInfoData.sel(space="lon"))
                    if self.methodType in ["SCC", "SRMSE"]:
                        m2s_data = m2s_data + moni_ltm_data_m
                    m2s_data_avg = m2s_data.mean(dim="time")

                if self.methodType == "PS":
                    jy_val = AlgorithmUtils.cal_ps(moni_data_avg,m2s_data_avg,"T")
                if self.methodType == "PC":
                    jy_val = AlgorithmUtils.cal_pc(moni_data_avg,m2s_data_avg)
                if self.methodType == "ACC":
                    jy_val = AlgorithmUtils.cal_acc(moni_data_avg,m2s_data_avg)
                if self.methodType == "SCC":
                    jy_val = AlgorithmUtils.cal_acc(moni_data_avg,m2s_data_avg)
                if self.methodType == "SRMSE":
                    jy_val = AlgorithmUtils.cal_rmse(moni_data_avg,m2s_data_avg)
                if self.methodType == "SYMBOLRATE":
                    jy_val = AlgorithmUtils.cal_symbolrate(moni_data_avg, m2s_data_avg)
                jy_data[i][j] = jy_val
        print(jy_data)
        jy_data = xr.DataArray(jy_data,coords=[xunqi_forecast_time_list,data_source_list],dims=["time","model"])
        jy_data = xr.where(np.isnan(jy_data),999999,jy_data)

        res_data_dict = {}
        for ds in data_source_list:
            res_data_dict[ds] = ["" if jd==999999 else str(jd) for jd in jy_data.sel(model=ds).values.tolist()]
        # 时间标题及x轴设置
        res_data_dict["xAxisData"] = [DateUtils.time_format_en(tt, "mon", "-") for tt in xunqi_forecast_time_list]
        res_data_dict["xAxisDataCh"] = [DateUtils.time_format_ch(tt, "mon") for tt in xunqi_forecast_time_list]
        subTitle = "起报时段：" + DateUtils.time_format_ch(forecastStartTime,self.reportTimeType) + "-" + DateUtils.time_format_ch(forecastEndTime, self.reportTimeType)
        subTitle = subTitle + " 检验时段：汛期"
        res_data_dict["subTitle"] = subTitle
        creatTxtFile(os.path.dirname(self.dataOutputPath) + "/", os.path.basename(self.dataOutputPath), json.dumps(res_data_dict, ensure_ascii=False))
        result_dict["data"] = res_data_dict
        return result_dict

    def get_single_mode_data(self, data_source, element, reportTimeType, timeType, forecastTime, startTime, endTime,
                             region):
        dataCfg = self.datasource_config[data_source.upper() + "_" + element.upper() + "_" + reportTimeType.upper()]
        dataInputPath = dataCfg["dataInputPath"]
        var = dataCfg["var"]
        fStartMon = int(dataCfg["start"])
        fEndMon = int(dataCfg["end"])
        dataInputPath_ym = dataInputPath.replace("#YYYYMM#", forecastTime)
        if not os.path.exists(dataInputPath_ym):
            return None
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
        return modedata

    def get_single_dm_data(self, data_source, element, reportTimeType, timeType, forecastTime, startTime,
                           endTime, region):
        dataCfg = self.datasource_config[data_source.upper() + "_" + element.upper() + "_" + reportTimeType.upper()]
        dataInputPath = dataCfg["dataInputPath"]
        dataInputPath_ym = dataInputPath.replace("#YYYYMMDD#", forecastTime).replace("#YYYYMM#", endTime).replace(
            "#YYYY#", forecastTime[0:4])
        if not os.path.exists(dataInputPath_ym):
            return None
        unitConvert = dataCfg["unitConvert"]
        var = dataCfg["var"]
        ds = xr.open_dataset(dataInputPath_ym, decode_times=False)
        modedata = ds[var]
        modedata = self.partitioned_data(modedata, region)
        modedata = modedata.expand_dims("time")
        modedata['time'] = [endTime]
        # 数据的纬度处理成从北到南（即从大到小）
        modedata = modedata.sortby(modedata["lat"], ascending=False)
        return modedata

    def get_single_data(self, data_source, element, eleType, reportTimeType, timeType, forecastTime, startTime, endTime,
                        region):
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
        logging.info(
            "预报时间尺度【%s】转换到起报时间尺度【%s】后的预报时间范围是==>[%s,%s]" % (timeType, reportTimeType, tmp_start_time, tmp_end_time))
        #
        dataCfg = self.datasource_config[data_source.upper() + "_" + element.upper() + "_" + reportTimeType.upper()]
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
        try:
            epmd = ExtendedPeriodModeData(sub_local_params, algorithm_input_data)
            epmd.execute()
        except AlgorithmException as ae:
            logging.info(ae.response_msg)
            return None
        fore_data = epmd.output_data["outputData"]

        if eleType == "SK":
            foreGridData = fore_data[0]

        if eleType == "JP":
            foreGridData = fore_data[0]
            foreLtmGridData = fore_data[1]
            if element in ["PRATE"]:
                foreGridData = (foreGridData - foreLtmGridData) / foreLtmGridData * 100
            else:
                foreGridData = foreGridData - foreLtmGridData

        if eleType == "LTM":
            foreGridData = fore_data[0]

        # 经度转换成西经——>东经 并根据范围截取数据
        foreGridData = self.partitioned_data(foreGridData, region)
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

    def get_station_data(self, timeType, startTime, endTime, element, areaCode):
        try:
            # 查询浙江省代表站站点信息
            # 组装查询站点信息的参数
            sta_params={"areaCode":areaCode, "stationType":"1"}
            sidfg = StationInfoDataForGbase(sta_params, [])
            sidfg.execute()
            stationDataInfo = sidfg.output_data["outputData"]
            # 查询浙江省代表站的站点数据（实况及常年值）
            # 组装查询站点数据的参数
            moni_params = {}
            moni_params["timeType"] = timeType
            moni_params["timeRanges"] = [startTime, endTime]
            moni_params["elements"] = element
            moni_params["dataSource"] = "CSOD"
            moni_params["areaCode"] = areaCode
            moni_params["stationType"] = "1"
            moni_params["eleType"] = "SK,LTM"
            moni_params["statisticType"] = "AVG"
            moni_params["ltm"] = "1991-2020"
            alg_input_data = [{"outputData": stationDataInfo}]
            sdfg = StationDataForGbase(moni_params, alg_input_data)
            sdfg.execute()
            moni_data_list = sdfg.output_data["outputData"]
            moni_data_list.append(stationDataInfo)
            return moni_data_list
        except AlgorithmException as ae:
            logging.info(ae.response_msg)
            return None

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
        # page_params = {"dataOutputPath":"/zj_climate/monitor/tempFile/NC/0fc14e95-660f-429c-aae8-774f71a343dc.json","areaCode":"33","methodType":"PS","forecastTime":"202304,202304","timeType":"mon","startTime":"1","endTime":"1","reportTimeType":"mon","dataSource":"CFS2,NCC,UKMO5","element":"AVGT"}
        # page_params = {
        #                "dataOutputPath": "/zj_climate/monitor/tempFile/NC/aa0d56f6-e384-48d2-b4b6-3a78e0bef405.json",
        #                "areaCode": "33",
        #                "reportTimeType": "mon",
        #                "forecastTime": "202201,202304",
        #                "timeType": "xunqi",
        #                "dataSource": "MODES_MME,EC5,CFS2,NCC,UKMO5,JMA3,CMMEV2MON,MODES_WMME,CPSV3MON,SEDES",
        #                # "dataSource": "UKMO5,JMA3,CFS2",
        #                "element": "AVGT",
        #                "methodType": "SCC"}
        gmttd = GainMultiTimeFloodSeasonTestData()
        result_dict = gmttd.execute(page_params)
        t2 = DateUtils.getTimeStamp()
        logging.info("获取模式多时次检验数据总耗时: %s ms" % (str(t2 - t1)))
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
