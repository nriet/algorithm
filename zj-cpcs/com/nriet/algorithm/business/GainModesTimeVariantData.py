#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2023/06/14
# @Author : Sbiys
# @File : GainModesTimeVariantData.py

import numpy as np
import os, sys, json, ast
import xarray as xr
import pandas as pd
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
from com.nriet.utils.fileUtils import creatTxtFile
from com.nriet.utils.databaseConnection.GbaseHandler import GbaseHandler
from com.nriet.utils.config.ConfigUtils import look_for_gbase_connection_config
from com.nriet.algorithm.business.ExtendedPeriodModeData import ExtendedPeriodModeData


class GainModesTimeVariantData(InputDataComponent):

    def __init__(self):
        # 初始化数据库连接
        self.gbase_handler = GbaseHandler(look_for_gbase_connection_config())
        # 加载数据源配置
        dataSourceConfigPath = PathConfig.CPCS_ROOT_PATH + 'com/nriet/config/dataSourceConfig.json'
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
        # 时间尺度
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
        # 统计量
        self.eleType = params.get("eleType")
        # 区域编码
        self.areaCode = params.get("areaCode")
        self.dataOutputPath = params.get("dataOutputPath")

    # 获取nc数据
    def execute(self, params):
        # 1.初始化参数
        self.init_param(params)
        result_dict = build_response_dict()
        # 纯监测处理
        if not self.reportTimeType:
            xStartTime,xEndTime = self.startTime, self.endTime
            # 日尺度站点数据获取
            if self.timeType == "day":
                if self.element == "RAIN":
                    tableField = "V13305"
                if self.element == "AVGT":
                    tableField = "V12001_701"
                # 针对降水 特殊处理
                if tableField == "V13305":
                    tableField_s = "(case when t1.V13305=32700 then 0.1 else t1.V13305 end)"
                else:
                    tableField_s = "t1." + tableField
                #  获取12个月的监测站点实况数据
                sql_sk_tmplate = "SELECT SUBSTRING(t1.D_DATETIME, 1, 10) D_DATETIME, ROUND(AVG(%s), 2) val FROM SURF_WEA_ZJ_MUL_DAY_TAB t1, othe_zj_aws_station_tab t3 WHERE t1.V01301 = t3.station_id AND t1.%s != 32766 AND t3.station_type = '2' AND t3.area_code LIKE '%s%%' AND t1.D_DATETIME BETWEEN '%s' AND '%s' GROUP BY t1.D_DATETIME"
                sql_sk = sql_sk_tmplate % (tableField_s, tableField, self.areaCode,
                                        DateUtils.time_format_en(xStartTime, self.timeType, "-"),
                                        DateUtils.time_format_en(xEndTime, self.timeType, "-"))
                print("modeData==>" + sql_sk)
                sql_sk_result = self.gbase_handler.executeSql(sql_sk)
                sk_data = {}
                for skr in sql_sk_result:
                    sk_data[skr["D_DATETIME"].replace("-", "")] = float(skr["val"])

            res_moni_data = []
            res_time_list = DateUtils.get_time_list([xStartTime, xEndTime], self.timeType)
            for tt in res_time_list:
                if tt in sk_data.keys():
                    res_moni_data.append("{:.2f}".format(sk_data[tt]))
                else:
                    res_moni_data.append("")

            res_data_dict = {}
            res_data_dict["moni"] = res_moni_data
            res_data_dict["xAxisData"] = [DateUtils.time_format_en(tt, self.timeType, "-") for tt in res_time_list]
            res_data_dict["xAxisDataCh"] = [DateUtils.time_format_ch(tt, self.timeType) for tt in res_time_list]
            res_data_dict["subTitle"] = DateUtils.time_format_ch(xStartTime,self.timeType) + "-" + DateUtils.time_format_ch(xEndTime, self.timeType)
            creatTxtFile(os.path.dirname(self.dataOutputPath) + "/", os.path.basename(self.dataOutputPath),json.dumps(res_data_dict, ensure_ascii=False))
            result_dict["data"] = res_data_dict
            return result_dict

        ################# 以下是监测预测一体的处理 ###############################
        # 季节模式的预测数据获取
        if self.reportTimeType == "mon":
            # 根据起报时间往前推算6个月
            tmpStartTime = DateUtils.getForwradTime(self.forecastTime,self.timeType,-5)
            tmpEndTime = self.forecastTime
            time_list = DateUtils.get_time_list([tmpStartTime,tmpEndTime],self.timeType)
            print(time_list)
            # 获取6个月的模式数据并插值到站点
            mode_data_list = []
            for tt in time_list:
                tmpForeTime = DateUtils.getForwradTime(tt,self.timeType,1)
                mode_data = self.get_single_mode_data(self.dataSource,self.element,tt,tmpForeTime,tmpForeTime,"117,123,27,32")
                mode_data = mode_data.mean(dim="time")
                g2s_data = mode_data.interp(lat=self.staInfoData.sel(space="lat"), lon=self.staInfoData.sel(space="lon"))
                g2s_data = g2s_data.expand_dims("time")
                g2s_data["time"] = [tt]
                # print(g2s_data)
                mode_data_list.append(g2s_data)
            # 获取当前起报时间预报未来N个月的模式数据
            tmpDataCfg = self.datasource_config[self.dataSource.upper() + "_" + self.element.upper()]
            foreStartTime = DateUtils.getForwradTime(self.forecastTime, self.timeType, 1)
            foreEndTime = DateUtils.getForwradTime(self.forecastTime, self.timeType, int(tmpDataCfg["end"]))
            curr_mode_data = self.get_single_mode_data(self.dataSource, self.element, self.forecastTime, foreStartTime, foreEndTime, "117,123,27,32")
            curr_g2s_data = curr_mode_data.interp(lat=self.staInfoData.sel(space="lat"), lon=self.staInfoData.sel(space="lon"))
            mode_data_list.append(curr_g2s_data)
            modeData = xr.concat(mode_data_list,dim="time")
            xStartTime,xEndTime = tmpStartTime, foreEndTime

        # 次季节模式的预测数据获取(日预报日)
        if self.reportTimeType == "day" and self.timeType == "day":
            if self.startTime == self.endTime:
                # 获取当前起报时间预报未来N个月的模式数据
                tmpDataCfg = self.datasource_config[self.dataSource.upper() + "_" + self.element.upper()+"_DAY"]
                foreStartTime = DateUtils.getForwradTime(self.forecastTime, self.timeType, 1)
                foreEndTime = DateUtils.getForwradTime(self.forecastTime, self.timeType, int(tmpDataCfg["end"]))
            else:
                foreStartTime = self.startTime
                foreEndTime = self.endTime
            curr_mode_data = self.get_single_data(self.dataSource, self.element, self.eleType, self.reportTimeType,
                                                  self.timeType, self.forecastTime, foreStartTime, foreEndTime,
                                                  "115,123,27,32")
            modeData = curr_mode_data.interp(lat=self.staInfoData.sel(space="lat"),
                                                  lon=self.staInfoData.sel(space="lon"))
            xStartTime, xEndTime = foreStartTime, foreEndTime

        # 次季节模式的预测数据获取(日预报月)
        if self.reportTimeType == "day" and self.timeType == "mon":
            # 根据起报时间往前推算12个月
            tmpStartTime = DateUtils.getForwradTime(self.endTime, self.timeType, -12)
            tmpEndTime = DateUtils.getForwradTime(self.endTime, self.timeType, -1)
            time_list = DateUtils.get_time_list([tmpStartTime, tmpEndTime], self.timeType)
            print(time_list)
            # 获取12个月的模式数据并插值到站点
            mode_data_list = []
            for tt in time_list:
                tmpForeTime = DateUtils.otherTime2Day(DateUtils.getForwradTime(tt, self.timeType, -1),self.timeType)[1]
                if self.dataSource in ["CFSV2MON"]:
                    mode_data = self.get_single_dm_data(self.dataSource, self.element, self.eleType,
                                                        self.reportTimeType, self.timeType, tmpForeTime, tt, tt,
                                                        "115,125,25,34")
                else:
                    mode_data = self.get_single_data(self.dataSource, self.element, self.eleType, self.reportTimeType,
                                                          self.timeType, tmpForeTime, tt, tt, "115,125,25,34")
                if not mode_data is None:
                    mode_data = mode_data.mean(dim="time")
                    g2s_data = mode_data.interp(lat=self.staInfoData.sel(space="lat"),lon=self.staInfoData.sel(space="lon"))
                    g2s_data = g2s_data.expand_dims("time")
                    g2s_data["time"] = [tt]
                    # print(g2s_data)
                    mode_data_list.append(g2s_data)
            foreStartTime = self.startTime
            foreEndTime = self.endTime
            if self.dataSource in ["CFSV2MON"]:
                curr_mode_data = self.get_single_dm_data(self.dataSource, self.element, self.eleType,
                                                         self.reportTimeType, self.timeType, self.forecastTime,
                                                         foreStartTime, foreEndTime, "115,125,25,34")
            else:
                curr_mode_data = self.get_single_data(self.dataSource, self.element, self.eleType, self.reportTimeType,
                                                      self.timeType, self.forecastTime, foreStartTime, foreEndTime,
                                                      "115,125,25,34")

            if not curr_mode_data is None:
                curr_mode_data = curr_mode_data.mean(dim="time")
                curr_g2s_data = curr_mode_data.interp(lat=self.staInfoData.sel(space="lat"),
                                                      lon=self.staInfoData.sel(space="lon"))
                curr_g2s_data = curr_g2s_data.expand_dims("time")
                curr_g2s_data["time"] = [foreEndTime]
                mode_data_list.append(curr_g2s_data)

            modeData = xr.concat(mode_data_list, dim="time")
            xStartTime, xEndTime = tmpStartTime, foreEndTime

        # 根据区域编码筛选市县的代表站数据
        if self.areaCode != "33":
            city_list = self.city_config["citys"]
            for city in city_list:
                # 获取市代表站
                if len(self.areaCode) == 4 and city.get("cityCode") == self.areaCode:
                    sta_list = city.get("station").split(",")
                    break
                if len(self.areaCode) == 6 and city.get("cityCode") == self.areaCode[0:4]:
                    for county in city.get("countys"):
                        if county.get("countyCode") == self.areaCode:
                            sta_list = county.get("station").split(",")
                            break
            # print(sta_list)
            modeData = modeData.sel(station=sta_list)
        # 对代表站进行平均
        modeData = modeData.mean(dim="station")

        # 监测数据
        # 月尺度站点监测数据获取
        if self.timeType == "mon":
            #  获取12个月的监测站点实况数据
            sql_sk_tmplate = "SELECT SUBSTRING(t1.D_DATETIME, 1, 7) D_DATETIME, ROUND(AVG(t1.V12001_701), 2) val FROM SURF_WEA_ZJ_MUL_MON_TAB t1, othe_zj_aws_station_tab t3 WHERE t1.V01301 = t3.station_id AND t1.V12001_701 < 99999 AND t3.station_type = '2' AND t3.area_code LIKE '%s%%' AND t1.D_DATETIME BETWEEN '%s-01' AND '%s-01' GROUP BY t1.D_DATETIME"
            sql_sk = sql_sk_tmplate%(self.areaCode,DateUtils.time_format_en(xStartTime,self.timeType,"-"),DateUtils.time_format_en(xEndTime,self.timeType,"-"))
            print("modeData==>"+sql_sk)
            sql_sk_result = self.gbase_handler.executeSql(sql_sk)
            sk_data = {}
            for skr in sql_sk_result:
                sk_data[skr["D_DATETIME"].replace("-","")] = float(skr["val"])

            #  获取12个月的监测站点常年值数据
            sql_ltm_tmplate = "SELECT t1.D_TIME D_DATETIME, ROUND(AVG(t1.d_value), 2) val FROM SURF_CLI_ZJ_MMON_1991_2020_TAB t1, othe_zj_aws_station_tab t3 WHERE t1.V01301 = t3.station_id AND t3.station_type = '2' AND t3.area_code LIKE '%s%%' AND t1.D_ELEMENT = 'V12001_701' GROUP BY t1.D_TIME"
            sql_ltm = sql_ltm_tmplate %(self.areaCode)
            print("ltm==>"+sql_ltm)
            sql_ltm_result = self.gbase_handler.executeSql(sql_ltm)
            ltm_data = {}
            for slr in sql_ltm_result:
                ltm_data[slr["D_DATETIME"]] = float(slr["val"])
        # 日尺度站点数据获取
        if self.timeType == "day":
            #  获取12个月的监测站点实况数据
            sql_sk_tmplate = "SELECT SUBSTRING(t1.D_DATETIME, 1, 10) D_DATETIME, ROUND(AVG(t1.V12001_701), 2) val FROM SURF_WEA_ZJ_MUL_DAY_TAB t1, othe_zj_aws_station_tab t3 WHERE t1.V01301 = t3.station_id AND t1.V12001_701 < 99999 AND t3.station_type = '2' AND t3.area_code LIKE '%s%%' AND t1.D_DATETIME BETWEEN '%s' AND '%s' GROUP BY t1.D_DATETIME"
            sql_sk = sql_sk_tmplate%(self.areaCode,DateUtils.time_format_en(xStartTime,self.timeType,"-"),DateUtils.time_format_en(xEndTime,self.timeType,"-"))
            print("modeData==>"+sql_sk)
            sql_sk_result = self.gbase_handler.executeSql(sql_sk)
            sk_data = {}
            for skr in sql_sk_result:
                sk_data[skr["D_DATETIME"].replace("-","")] = float(skr["val"])

            #  获取12个月的监测站点常年值数据
            sql_ltm_tmplate = "SELECT t1.D_TIME D_DATETIME, ROUND(AVG(t1.d_value), 2) val FROM SURF_CLI_ZJ_MDAY_1991_2020_TAB t1, othe_zj_aws_station_tab t3 WHERE t1.V01301 = t3.station_id AND t3.station_type = '2' AND t3.area_code LIKE '%s%%' AND t1.D_ELEMENT = 'V12001_701' GROUP BY t1.D_TIME"
            sql_ltm = sql_ltm_tmplate %(self.areaCode)
            print("ltm==>"+sql_ltm)
            sql_ltm_result = self.gbase_handler.executeSql(sql_ltm)
            ltm_data = {}
            for slr in sql_ltm_result:
                ltm_data[slr["D_DATETIME"]] = float(slr["val"])

        res_moni_data=[]
        res_fore_data=[]
        res_time_list = DateUtils.get_time_list([xStartTime, xEndTime], self.timeType)
        split_time = DateUtils.time_format_en(self.forecastTime,self.timeType,"-")
        if self.reportTimeType == "day" and self.timeType == "mon":
            self.forecastTime = self.forecastTime[0:6]
            split_time = DateUtils.time_format_en(self.forecastTime, self.timeType, "-")
        for tt in res_time_list:
            if tt in sk_data.keys():
                if self.reportTimeType == "day" and self.timeType == "day" and self.startTime == self.endTime:
                    res_moni_data.append("{:.2f}".format(sk_data[tt]))
                else:
                    res_moni_data.append("{:.2f}".format(sk_data[tt] - ltm_data[tt[4:]]))

                if tt >= self.forecastTime:
                    split_time = DateUtils.time_format_en(tt,self.timeType,"-")
            else:
                res_moni_data.append("")
            if tt in modeData.time.values:
                res_fore_data.append("{:.2f}".format(modeData.sel(time=tt).values))
            else:
                res_fore_data.append("")

        res_data_dict={}
        res_data_dict["moni"] = res_moni_data
        res_data_dict["fore"] = res_fore_data
        res_data_dict["xAxisData"] = [DateUtils.time_format_en(tt,self.timeType,"-") for tt in res_time_list]
        res_data_dict["xAxisDataCh"] = [DateUtils.time_format_ch(tt,self.timeType) for tt in res_time_list]
        res_data_dict["subTitle"] = DateUtils.time_format_ch(xStartTime,self.timeType)+"-"+DateUtils.time_format_ch(xEndTime,self.timeType)
        res_data_dict["splitLine"] = split_time
        creatTxtFile(os.path.dirname(self.dataOutputPath) + "/", os.path.basename(self.dataOutputPath), json.dumps(res_data_dict, ensure_ascii=False))
        result_dict["data"] = res_data_dict
        return result_dict


    def get_single_mode_data(self,data_source, element, forecastTime, startTime, endTime, region):
        dataCfg = self.datasource_config[data_source.upper()+"_"+element.upper()]
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
        print(dataInputPath_ym)
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
        # modedata = modedata.mean(dim="time")
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
        foreGridData = self.partitioned_data(foreGridData,region)
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
        modedata = modedata.expand_dims("time")
        modedata["time"] = [endTime]
        # 数据的纬度处理成从北到南（即从大到小）
        modedata = modedata.sortby(modedata["lat"], ascending=False)
        return modedata


if __name__ == "__main__":
    try:
        t1 = DateUtils.getTimeStamp()
        # 获取页面传参
        page_params = ast.literal_eval(sys.argv[1])
        # page_params = {"reportTimeType": "",
        #                 "timeType": "day",
        #                "forecastTime": "",
        #                "startTime": "20230511",
        #                "endTime": "20230531",
        #                "dataSource": "CSOD",
        #                # "dataSource": "MODES_MME,MODES_CFS2,MODES_EC5,MODES_NCC,MODES_UKMO5,MODES_JMA3,CMMEV2_MME,MODES_WMME,SEDES,ZJPPC",
        #                "dataOutputPath": "/nfsshare/cdbdata/data/dry_data/test_more.json",
        #                "areaCode": "3305",
        #                "eleType": "SK",
        #                "element": "RAIN"}
        gs2gd = GainModesTimeVariantData()
        result_dict = gs2gd.execute(page_params)
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
