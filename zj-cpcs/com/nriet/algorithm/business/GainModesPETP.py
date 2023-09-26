#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time: 2023/7/17
# @Author: xue
# @File: GainModesExamination.py
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
    PARAMETER_VALUE_MISSING_MSG, CUSTOM_ERROR_CODE, CUSTOM_ERROR_MSG
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.utils.fileUtils import creatTxtFile
from com.nriet.algorithm.business.ExtendedPeriodModeData import ExtendedPeriodModeData
from com.nriet.algorithm.business.StationDataForGbase import StationDataForGbase
from com.nriet.algorithm.business.StationInfoDataForGbase import StationInfoDataForGbase


class GainModesPETP(InputDataComponent):

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
        # page_params = {
        #     "forecastTime": "20230501", # 起报时间
        #     "forecastPeriod": "0130",  # 0130，1030，预报时段
        #     "dataSource": "CFSV2", # 数据源
        #     # "dataSource": "CFSV2,ECMWF,CMA-CPSv3,Fgoals-f2,BCC-CSM2-HR",
        #     "dataOutputPath": "/nfsshare/cdbdata/data/dry_data/test_more1.json",
        #     "areaCode": "33", # 行政区ID
        #     "element": "AVGT"} # 预报时次
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
        # # 统计量
        self.eleType = params.get("eleType")
        # 区域编码
        self.areaCode = params.get("areaCode")
        # 时间相关系数 不返回：0   返回：1  默认不返回
        self.isTcc = params.get("isTcc","0")
        # 表格数据输出位置
        self.dataOutputPath = params.get("dataOutputPath")

    # 获取nc数据
    def execute(self, params):
        # 1.初始化参数
        self.init_param(params)
        result_dict = build_response_dict()
        # 获取站点监测数据
        moni_data_list = self.get_station_data(self.timeType, self.startTime, self.endTime, self.element)
        moni_sk_data = moni_data_list[0]
        moni_ltm_data = moni_data_list[1]
        staInfoData = moni_data_list[2]
        moni_jp_data = moni_sk_data - moni_ltm_data
        moni_sk_data_m = moni_sk_data.mean(dim="time")
        moni_jp_data_m = moni_jp_data.mean(dim="time")
        # 获取模式数据
        if self.dataSource in ["CFSV2", "CPSV3", "NCC", "CFS2", "JMA3", "UKMO5", "EC5"]:
            mode_sk_data = self.get_single_data(self.dataSource, self.element, "SK", self.reportTimeType,
                                             self.timeType, self.forecastTime, self.startTime, self.endTime,
                                             "115,125,25,34")
            # 模式插值到站点数据
            m2s_sk_data = mode_sk_data.interp(lat=staInfoData.sel(space="lat"), lon=staInfoData.sel(space="lon"))

            mode_jp_data = self.get_single_data(self.dataSource, self.element, "JP", self.reportTimeType,
                                             self.timeType, self.forecastTime, self.startTime, self.endTime,
                                             "115,125,25,34")
            # 模式插值到站点数据
            m2s_jp_data = mode_jp_data.interp(lat=staInfoData.sel(space="lat"), lon=staInfoData.sel(space="lon"))
            m2s_sk_data_m = m2s_sk_data.mean(dim="time")
            m2s_jp_data_m = m2s_jp_data.mean(dim="time")
        if self.dataSource in ["CFSV2MON"]:
            mode_jp_data = self.get_single_dm_data(self.dataSource, self.element, self.reportTimeType,
                                                self.timeType, self.forecastTime, self.startTime, self.endTime,
                                                "115,125,25,34")
            # 模式插值到站点数据
            m2s_jp_data = mode_jp_data.interp(lat=staInfoData.sel(space="lat"), lon=staInfoData.sel(space="lon"))
            m2s_sk_data = m2s_jp_data + moni_ltm_data
            m2s_sk_data_m = m2s_sk_data.mean(dim="time")
            m2s_jp_data_m = m2s_jp_data.mean(dim="time")
        if self.dataSource in ["MODE_WMME", "MODE_MME", "CMMEV2MON", "SEDES"]:
            mode_jp_data = self.get_single_mode_data(self.dataSource, self.element, self.reportTimeType,
                                                  self.timeType, self.forecastTime, self.startTime, self.endTime,
                                                  "115,125,25,34")
            # 模式插值到站点数据
            m2s_jp_data = mode_jp_data.interp(lat=staInfoData.sel(space="lat"), lon=staInfoData.sel(space="lon"))
            m2s_sk_data = m2s_jp_data + moni_ltm_data
            m2s_sk_data_m = m2s_sk_data.mean(dim="time")
            m2s_jp_data_m = m2s_jp_data.mean(dim="time")

        # 计算TCC
        if self.isTcc == "1":
            tcc_data = AlgorithmUtils.cal_tcc(moni_sk_data, m2s_sk_data)
        # 计算ERR
        err_data = AlgorithmUtils.cal_err_symbol(moni_sk_data_m, m2s_sk_data_m,"ERR")
        # 计算RERR
        rerr_data = AlgorithmUtils.cal_err_symbol(moni_sk_data_m, m2s_sk_data_m,"RERR")
        # 计算符号判定
        symbol_data = AlgorithmUtils.cal_err_symbol(moni_sk_data_m, m2s_sk_data_m, "SYMBOL")
        # 模式插值到站点数据
        logging.info("xxxxxxxx2")
        res_list = []
        # 省
        if self.areaCode == "33":
            # 省
            tmpp = {}
            p_err = err_data.mean(dim="station")
            p_rerr = rerr_data.mean(dim="station")
            p_symbol = symbol_data.mean(dim="station")
            if self.isTcc == "1":
                p_tcc = tcc_data.mean(dim="station")
            tmpp["areaCode1"] = "浙江省"
            tmpp["areaCode2"] = "浙江省"
            tmpp["station"] = "/"
            tmpp["score"] = "PS评分：{:.1f}\nPC评分：{:.1f}\nACC：{:.1f}\nSCC：{:.1f}\nSRMSE：{:.1f}".format(
                AlgorithmUtils.cal_ps(moni_jp_data_m, m2s_jp_data_m, "T"),
                AlgorithmUtils.cal_pc(moni_jp_data_m, m2s_jp_data_m),
                AlgorithmUtils.cal_acc(moni_jp_data_m, m2s_jp_data_m),
                AlgorithmUtils.cal_acc(moni_sk_data_m, m2s_sk_data_m),
                AlgorithmUtils.cal_rmse(moni_sk_data_m, m2s_sk_data_m)
            )
            tmpp["jdwc"] = "999999" if np.isnan(p_err) else "{:.1f}".format(p_err.values)
            tmpp["xdwc"] = "999999" if np.isnan(p_rerr) else "{:.1f}".format(p_rerr.values)+"%"
            tmpp["fhpd"] = "999999" if np.isnan(p_symbol) else "同号" if p_symbol >= 0 else "异号"
            if self.isTcc == "1":
                tmpp["tcc"] = "999999" if np.isnan(p_tcc) else "{:.1f}".format(p_tcc.values)
            res_list.append(tmpp)
            # 市
            city_list = self.city_config["citys"]
            for city in city_list:
                tmpc = {}
                sta = city.get("station").split(",")
                sta = list(set(sta).intersection(moni_jp_data_m['station'].values))
                f_jp_data = m2s_jp_data_m.sel(station=sta)
                f_sk_data = m2s_sk_data_m.sel(station=sta)
                m_jp_data = moni_jp_data_m.sel(station=sta)
                m_sk_data = moni_sk_data_m.sel(station=sta)
                c_err = err_data.sel(station=sta).mean(dim="station")
                c_rerr = rerr_data.sel(station=sta).mean(dim="station")
                c_symbol = symbol_data.sel(station=sta).mean(dim="station")
                if self.isTcc == "1":
                    c_tcc = tcc_data.sel(station=sta).mean(dim="station")
                tmpc["areaCode1"] = city.get("cityName")
                tmpc["areaCode2"] = "地区平均"
                tmpc["station"] = "/"
                tmpc["score"] = "PS评分：{:.1f}\nPC评分：{:.1f}\nACC：{:.1f}\nSCC：{:.1f}\nSRMSE：{:.1f}".format(
                    AlgorithmUtils.cal_ps(m_jp_data, f_jp_data, "T"),
                    AlgorithmUtils.cal_pc(m_jp_data, f_jp_data),
                    AlgorithmUtils.cal_acc(m_jp_data, f_jp_data),
                    AlgorithmUtils.cal_acc(m_sk_data, f_sk_data),
                    AlgorithmUtils.cal_rmse(m_sk_data, f_sk_data)
                )
                tmpc["jdwc"] = "999999" if np.isnan(c_err) else "{:.1f}".format(c_err.values)
                tmpc["xdwc"] = "999999" if np.isnan(c_rerr) else "{:.1f}".format(c_rerr.values) + "%"
                tmpc["fhpd"] = "999999" if np.isnan(c_symbol) else "同号" if c_symbol >= 0 else "异号"
                if self.isTcc == "1":
                    tmpc["tcc"] = "999999" if np.isnan(c_tcc) else "{:.1f}".format(c_tcc.values)
                res_list.append(tmpc)
                # 县区
                for county in city.get("countys"):
                    tmpcc = {}
                    stac = county.get("station").split(",")
                    stac = list(set(stac).intersection(moni_jp_data_m['station'].values))
                    cc_err = err_data.sel(station=stac).mean(dim="station")
                    cc_rerr = rerr_data.sel(station=stac).mean(dim="station")
                    cc_symbol = symbol_data.sel(station=stac).mean(dim="station")
                    if self.isTcc == "1":
                        cc_tcc = tcc_data.sel(station=stac).mean(dim="station")
                    tmpcc["areaCode1"] = city.get("cityName")
                    tmpcc["areaCode2"] = county.get("countyName")
                    tmpcc["station"] = county.get("station")
                    tmpcc["score"] = ""
                    tmpcc["jdwc"] = "999999" if np.isnan(cc_err) else "{:.1f}".format(cc_err.values)
                    tmpcc["xdwc"] = "999999" if np.isnan(cc_rerr) else "{:.1f}".format(cc_rerr.values) + "%"
                    tmpcc["fhpd"] = "999999" if np.isnan(cc_symbol) else "同号" if cc_symbol >= 0 else "异号"
                    if self.isTcc == "1":
                        tmpcc["tcc"] = "999999" if np.isnan(cc_tcc) else "{:.1f}".format(cc_tcc.values)
                    res_list.append(tmpcc)
        # 市
        if len(self.areaCode) == 4:
            city_list = self.city_config["citys"]
            for city in city_list:
                if city.get("cityCode") == self.areaCode:
                    tmpc = {}
                    sta = city.get("station").split(",")
                    sta = list(set(sta).intersection(moni_jp_data_m['station'].values))
                    f_jp_data = m2s_jp_data_m.sel(station=sta)
                    f_sk_data = m2s_sk_data_m.sel(station=sta)
                    m_jp_data = moni_jp_data_m.sel(station=sta)
                    m_sk_data = moni_sk_data_m.sel(station=sta)
                    c_err = err_data.sel(station=sta).mean(dim="station")
                    c_rerr = rerr_data.sel(station=sta).mean(dim="station")
                    c_symbol = symbol_data.sel(station=sta).mean(dim="station")
                    if self.isTcc == "1":
                        c_tcc = tcc_data.sel(station=sta).mean(dim="station")
                    tmpc["areaCode1"] = city.get("cityName")
                    tmpc["areaCode2"] = "地区平均"
                    tmpc["station"] = "/"
                    tmpc["score"] = "PS评分：{:.1f}\nPC评分：{:.1f}\nACC：{:.1f}\nSCC：{:.1f}\nSRMSE：{:.1f}".format(
                        AlgorithmUtils.cal_ps(m_jp_data, f_jp_data, "T"),
                        AlgorithmUtils.cal_pc(m_jp_data, f_jp_data),
                        AlgorithmUtils.cal_acc(m_jp_data, f_jp_data),
                        AlgorithmUtils.cal_acc(m_sk_data, f_sk_data),
                        AlgorithmUtils.cal_rmse(m_sk_data, f_sk_data)
                    )
                    tmpc["jdwc"] = "999999" if np.isnan(c_err) else "{:.1f}".format(c_err.values)
                    tmpc["xdwc"] = "999999" if np.isnan(c_rerr) else "{:.1f}".format(c_rerr.values) + "%"
                    tmpc["fhpd"] = "999999" if np.isnan(c_symbol) else "同号" if c_symbol >= 0 else "异号"
                    if self.isTcc == "1":
                        tmpc["tcc"] = "999999" if np.isnan(c_tcc) else "{:.1f}".format(c_tcc.values)
                    res_list.append(tmpc)
                    # 县区
                    for county in city.get("countys"):
                        tmpcc = {}
                        stac = county.get("station").split(",")
                        stac = list(set(stac).intersection(moni_jp_data_m['station'].values))
                        cc_err = err_data.sel(station=stac).mean(dim="station")
                        cc_rerr = rerr_data.sel(station=stac).mean(dim="station")
                        cc_symbol = symbol_data.sel(station=stac).mean(dim="station")
                        if self.isTcc == "1":
                            cc_tcc = tcc_data.sel(station=stac).mean(dim="station")
                        tmpcc["areaCode1"] = city.get("cityName")
                        tmpcc["areaCode2"] = county.get("countyName")
                        tmpcc["station"] = county.get("station")
                        tmpcc["score"] = ""
                        tmpcc["jdwc"] = "999999" if np.isnan(cc_err) else "{:.1f}".format(cc_err.values)
                        tmpcc["xdwc"] = "999999" if np.isnan(cc_rerr) else "{:.1f}".format(cc_rerr.values) + "%"
                        tmpcc["fhpd"] = "999999" if np.isnan(cc_symbol) else "同号" if cc_symbol >= 0 else "异号"
                        if self.isTcc == "1":
                            tmpcc["tcc"] = "999999" if np.isnan(cc_tcc) else "{:.1f}".format(cc_tcc.values)
                        res_list.append(tmpcc)
                    break
        # 县
        if len(self.areaCode) == 6:
            city_list = self.city_config["citys"]
            for city in city_list:
                if city.get("cityCode") == self.areaCode[0:4]:
                    # 县区
                    for county in city.get("countys"):
                        if county.get("countyCode") == self.areaCode:
                            tmpcc = {}
                            stac = county.get("station").split(",")
                            stac = list(set(stac).intersection(moni_jp_data_m['station'].values))
                            cc_err = err_data.sel(station=stac).mean(dim="station")
                            cc_rerr = rerr_data.sel(station=stac).mean(dim="station")
                            cc_symbol = symbol_data.sel(station=stac).mean(dim="station")
                            if self.isTcc == "1":
                                cc_tcc = tcc_data.sel(station=stac).mean(dim="station")
                            tmpcc["areaCode1"] = city.get("cityName")
                            tmpcc["areaCode2"] = county.get("countyName")
                            tmpcc["station"] = county.get("station")
                            tmpcc["score"] = ""
                            tmpcc["jdwc"] = "999999" if np.isnan(cc_err) else "{:.1f}".format(cc_err.values)
                            tmpcc["xdwc"] = "999999" if np.isnan(cc_rerr) else "{:.1f}".format(cc_rerr.values) + "%"
                            tmpcc["fhpd"] = "999999" if np.isnan(cc_symbol) else "同号" if cc_symbol >= 0 else "异号"
                            if self.isTcc == "1":
                                tmpcc["tcc"] = "999999" if np.isnan(cc_tcc) else "{:.1f}".format(cc_tcc.values)
                            res_list.append(tmpcc)
                            break
                    break
        # print(res_list)
        creatTxtFile(os.path.dirname(self.dataOutputPath) + "/", os.path.basename(self.dataOutputPath),
                     json.dumps(res_list, ensure_ascii=False))

        result_dict["data"] = res_list
        return result_dict

    def get_single_mode_data(self, data_source, element, reportTimeType, timeType, forecastTime, startTime, endTime,
                             region):
        dataCfg = self.datasource_config[data_source.upper() + "_" + element.upper() + "_" + reportTimeType.upper()]
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
        return modedata

    def get_single_dm_data(self, data_source, element, reportTimeType, timeType, forecastTime, startTime,
                           endTime, region):
        dataCfg = self.datasource_config[data_source.upper() + "_" + element.upper() + "_" + reportTimeType.upper()]
        dataInputPath = dataCfg["dataInputPath"]
        dataInputPath_ym = dataInputPath.replace("#YYYYMMDD#", forecastTime).replace("#YYYYMM#", endTime).replace(
            "#YYYY#", forecastTime[0:4])
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

    def get_station_data(self, timeType, startTime, endTime, element):
        try:
            # 查询浙江省代表站站点信息
            # 组装查询站点信息的参数
            sta_params={"areaCode":"33", "stationType":"2"}
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
            moni_params["areaCode"] = "33"
            moni_params["stationType"] = "2"
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
        # page_params = {"eleType": "SK",
        #                "dataOutputPath": "/zj_climate/monitor/tempFile/NC/aa0d56f6-e384-48d2-b4b6-3a78e0bef405.json",
        #                "areaCode": "3301", "forecastTime": "20230501", "timeType": "day", "startTime": "20230601",
        #                "endTime": "20230610", "reportTimeType": "day", "dataSource": "CPSV3", "element": "AVGT", "isTcc": "1"}
        modesPETP = GainModesPETP()
        result_dict = modesPETP.execute(page_params)
        t2 = DateUtils.getTimeStamp()
        logging.info("获取模式表格数据总耗时: %s ms" % (str(t2 - t1)))
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
