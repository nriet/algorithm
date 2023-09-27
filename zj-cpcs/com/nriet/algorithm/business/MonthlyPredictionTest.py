#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2023/06/14
# @Author : Shiys
# @File : GainStation2GirdData.py

import os, sys, json, ast
import xarray as xr
import numpy as np
import pandas as pd
from metpy.interpolate import remove_nan_observations
import logging, traceback
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
from com.nriet.utils.databaseConnection.GbaseHandler import GbaseHandler
from com.nriet.utils.config.ConfigUtils import look_for_gbase_connection_config
from com.nriet.algorithm.business.ExtendedPeriodModeData import ExtendedPeriodModeData
from com.nriet.algorithm.business.StationDataForGbase import StationDataForGbase
from com.nriet.algorithm.business.StationInfoDataForGbase import StationInfoDataForGbase


class MonthlyPredictionTest(InputDataComponent):

    def __init__(self, sub_local_params, algorithm_iuput_data):
        # 初始化数据库连接
        self.gbase_handler = GbaseHandler(look_for_gbase_connection_config())
        # 加载数据源配置
        dataSourceConfigPath = PathConfig.CPCS_ROOT_PATH + 'com/nriet/config/dataSourceConfig3.json'
        with open(dataSourceConfigPath, "r", encoding='UTF-8') as f:
            datasourcestr = f.read()
        self.datasource_config = json.loads(datasourcestr)
        # 起报时间尺度
        self.reportTimeType = sub_local_params.get("reportTimeType").lower()
        # 起报时间
        self.forecastTime = sub_local_params.get("forecastTime")
        # 预报时间尺度
        self.timeType = sub_local_params.get("timeType").lower()
        # 预报开始时间
        self.startTime = sub_local_params.get("startTime")
        # 预报结束时间
        self.endTime = sub_local_params.get("endTime")
        # 数据源源
        self.dataSource = sub_local_params.get("dataSource")
        # 要素
        self.element = sub_local_params.get("element")
        # 统计方法
        self.eleType = sub_local_params.get("eleType")

        # 区域编码
        self.areaCode = sub_local_params.get("areaCode")
        # 站点类型 区域站：1   代表站：2  默认代表站
        self.stationType = sub_local_params.get("stationType", "2")
        self.output_data = None

    # 获取nc数据
    def execute(self):

        result_dict = build_response_dict()
        # 获取站点监测数据
        moni_data_list = self.get_station_data(self.timeType, self.startTime, self.endTime, self.element)
        moni_sk_data = moni_data_list[0]
        moni_ltm_data = moni_data_list[1]
        staInfoData = moni_data_list[2]
        staLons = staInfoData.sel(space="lon")
        staLats = staInfoData.sel(space="lat")
        if self.eleType != "TCC" and self.eleType != "TRMSE":
            moni_sk_data = moni_sk_data.mean(dim="time")
            moni_ltm_data = moni_ltm_data.mean(dim="time")
        # #  获取站点的实况数据
        # moni_sk_data, staLons, staLats = self.get_station_mean_data(self.timeType, self.startTime, self.endTime,
        #                                                             self.element, self.areaCode, self.stationType)
        # #  获取站点的常年值数据
        # moni_ltm_data = self.get_station_ltm_data(self.timeType, self.startTime, self.endTime, self.element,
        #                                           self.areaCode, self.stationType)
        moni_ltm_data = moni_ltm_data.sel(station = moni_sk_data.station)
        logging.info(moni_sk_data)
        logging.info(moni_ltm_data)
        if self.eleType == "SYMBOL":
            moni_data = moni_sk_data - moni_ltm_data
        else:
            moni_data = moni_sk_data

        # 获取模式数据
        if self.dataSource in ["CFSV2","CPSV3","NCC","CFS2","JMA3","UKMO5","EC5","CPSV3MON"]:
            staticType = "JP" if self.eleType == "SYMBOL" else "SK"
            mode_data = self.get_single_data(self.dataSource, self.element, staticType, self.reportTimeType,
                                             self.timeType, self.forecastTime, self.startTime, self.endTime,
                                             "115,125,25,34")
        if self.dataSource in ["CFSV2MON"]:
            mode_data = self.get_single_dm_data(self.dataSource, self.element, self.reportTimeType,
                                             self.timeType, self.forecastTime, self.startTime, self.endTime,
                                             "115,125,25,34")
        if self.dataSource in ["MODES_WMME","MODES_MME","CMMEV2MON","SEDES"]:
            mode_data = self.get_single_mode_data(self.dataSource, self.element, self.reportTimeType,
                                             self.timeType, self.forecastTime, self.startTime, self.endTime,
                                             "115,125,25,34")
        # if self.dataSource not in ["CFSV2MON"]:
        #     mode_data = mode_data.mean(dim=["time"])
        if self.eleType != "TCC" and self.eleType != "TRMSE":
            mode_data = mode_data.mean(dim="time")
        # 模式插值到站点数据
        m2s_data = mode_data.interp(lat=staLats,lon=staLons)

        if self.dataSource in ["CFSV2MON","MODES_WMME","MODES_MME","CMMEV2MON","SEDES"] and self.eleType in ["ERR","RERR","TCC"]:
            m2s_data = m2s_data + moni_ltm_data
        if self.eleType != "TCC" and self.eleType != "TRMSE":
            resultData = AlgorithmUtils.cal_err_symbol(moni_data, m2s_data, self.eleType)
        elif self.eleType == "TCC":
            resultData = AlgorithmUtils.cal_tcc(moni_data, m2s_data)
        elif self.eleType == "TRMSE":
            resultData = AlgorithmUtils.cal_trmse(moni_data, m2s_data)

        # 符号判定
        if self.eleType == "SYMBOL":
            resultData.attrs['lats'] = staLats.values
            resultData.attrs['lons'] = staLons.values
        else:
            # 非符号判定结果需重新插值到格点数据
            interLats = [27, 32, 51]
            interLons = [117, 123, 61]
            resultData = self.interp_idw(resultData, interLats, interLons, staLats.values, staLons.values)
            resultData = resultData.sortby(resultData["lat"], ascending=False)
        print(resultData)
        self.output_data ={"outputData":resultData}

    def get_single_mode_data(self,data_source, element, reportTimeType, timeType, forecastTime, startTime, endTime, region):
        dataCfg = self.datasource_config[data_source.upper()+"_"+element.upper()+"_"+reportTimeType.upper()]
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
        # modedata = modedata.mean(dim="time")
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

    #  获取监测站点实况数据
    def get_station_mean_data(self, timeType, startTime, endTime, element, areaCode, stationType):

        if timeType == "day":
            tableName = "SURF_WEA_ZJ_MUL_DAY_TAB"
            tmpStartTime = DateUtils.time_format_en(startTime, timeType, "-")
            tmpEndTime = DateUtils.time_format_en(endTime, timeType, "-")

        if timeType == "mon":
            # tableName = "SURF_WEA_ZJ_MUL_MON_TAB"
            # tmpStartTime = DateUtils.time_format_en(self.startTime,self.timeType,"-")+"-01"
            # tmpEndTime = DateUtils.time_format_en(self.endTime,self.timeType,"-")+"-01"
            tableName = "SURF_WEA_ZJ_MUL_DAY_TAB"
            tmpStartTime = DateUtils.time_format_en(DateUtils.otherTime2Day(startTime, timeType)[0], "day", "-")
            tmpEndTime = DateUtils.time_format_en(DateUtils.otherTime2Day(endTime, timeType)[1], "day", "-")

        if element == "AVGT":
            tableField = "V12001_701"
            staticStr = "AVG"

        if element == "RAIN":
            tableField = "V13305"
            staticStr = "SUM"
        sql_sk_tmplate = " SELECT t1.V01301 stationId, max(t3.lat) lat, max(t3.lon) lon, ROUND(%s(t1.%s), 2) val FROM %s t1, t_msis_cd_aws_station t3 WHERE t1.V01301 = t3.station_id  AND t1.%s <99999 AND t3.station_type = '%s' AND t3.area_code like '%s%%' AND t1.D_DATETIME BETWEEN '%s' AND '%s' GROUP BY t1.V01301 ORDER BY t1.V01301"
        sql_sk = sql_sk_tmplate % (staticStr, tableField, tableName, tableField, stationType, areaCode, tmpStartTime, tmpEndTime)
        print("moni_mean_sql==>" + sql_sk)
        sql_sk_result = self.gbase_handler.executeSql(sql_sk)
        if len(sql_sk_result) == 0:
            error_str = "当前SQL==>[%s]未查询到数据！" % sql_sk
            raise AlgorithmException(response_code=DB_DATA_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 解析查询的结果数据封装成二维数组
        sql_data_sk = pd.DataFrame(list(sql_sk_result))
        sqlData_sk = np.array(sql_data_sk)
        sk_sta_list = sqlData_sk[:, 0]
        moni_mean_data = xr.DataArray(np.asarray(sqlData_sk[:, 3], dtype=np.float32), coords=[sk_sta_list],
                                      dims=['station'])
        zlats = xr.DataArray(np.asarray(sqlData_sk[:, 1], dtype=np.float32), coords=[sk_sta_list],
                                      dims=['station'])
        zlons = xr.DataArray(np.asarray(sqlData_sk[:, 2], dtype=np.float32), coords=[sk_sta_list],
                                      dims=['station'])
        return moni_mean_data, zlons, zlats

    #  获取监测站点常年值数据
    def get_station_ltm_data(self, timeType, startTime, endTime, element, areaCode, stationType):
        # 常年值表名称
        if timeType == "day":
            tableName = "SURF_CLI_ZJ_MDAY_1991_2020_TAB"
        if timeType == "mon":
            tableName = "SURF_CLI_ZJ_MMON_1991_2020_TAB"

        # 查询的表字段及对时间的统计方法
        if element == "AVGT":
            tableField = "V12001_701"
            staticStr = "AVG"
        if element == "RAIN":
            tableField = "V13305"
            staticStr = "SUM"

        # 查询的时间条件
        startMD, endMD = startTime[4:],endTime[4:]
        if int(startMD) > int(endMD):
            MS = '0101' if timeType=="day" else '01'
            ME = '1231' if timeType=="day" else '12'
            timeConditionStr = "((t1.D_TIME BETWEEN '%s' AND '%s') OR (t1.D_TIME BETWEEN '%s' AND '%s'))" % (startMD, ME, MS, endMD)
        else:
            timeConditionStr = "(t1.D_TIME BETWEEN '%s' AND '%s')" % (startMD, endMD)
        sql_ltm_tmplate = " SELECT t1.V01301 stationId, max(t3.lat) lat, max(t3.lon) lon, ROUND(%s(t1.d_value), 2) val FROM %s t1, othe_zj_aws_station_tab t3 WHERE t1.V01301 = t3.station_id AND t3.station_type = '%s' AND %s AND t1.D_ELEMENT = '%s' AND t3.area_code like '%s%%' GROUP BY t1.V01301 ORDER BY t1.V01301"
        sql_ltm = sql_ltm_tmplate % (staticStr, tableName, stationType, timeConditionStr, tableField, areaCode)
        print("moni_ltm_sql==>" + sql_ltm)
        sql_ltm_result = self.gbase_handler.executeSql(sql_ltm)
        if len(sql_ltm_result) == 0:
            error_str = "当前SQL==>[%s]未查询到数据！" % sql_ltm
            raise AlgorithmException(response_code=DB_DATA_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 解析查询的结果数据封装成二维数组
        sql_data_ltm = pd.DataFrame(list(sql_ltm_result))
        sqlData_ltm = np.array(sql_data_ltm)
        ltm_sta_list = sqlData_ltm[:, 0]
        moni_ltm_data = xr.DataArray(np.asarray(sqlData_ltm[:, 3], dtype=np.float32), coords=[ltm_sta_list],
                                      dims=['station'])
        return moni_ltm_data

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
        # out_path = "/nfsshare/cdbdata/data/modes3/%s_AVGT_MON_202304_202305_202305_%s.nc"
        # page_params = {
        #                 "reportTimeType": "day",
        #                 "timeType": "day",
        #                "forecastTime": "20230501",
        #                "startTime": "20230510",
        #                "endTime": "20230520",
        #                "dataSource": "CPSV3",
        #                "stationType": "2",
        #                "eleType": "TCC",
        #                "areaCode": "33",
        #                "element": "AVGT"}
        # monthlyPredictionTest = MonthlyPredictionTest(page_params, [])
        # monthlyPredictionTest.execute()
        #
        # mode_list =["NCC","JMA3","UKMO5","EC5","CFS2","MODES_MME","MODES_WMME","CMMEV2MON","SEDES"]
        # eleType_list = ["ERR","RERR","SYMBOL"]
        # mode_list = ["NCC"]
        # eleType_list = ["SYMBOL"]

        # for mode in mode_list:
        #     for eleType in eleType_list:
        #         page_params["dataSource"] = mode
        #         page_params["eleType"] = eleType
        #         page_params["dataOutputPath"] = out_path %(mode,eleType)
        #         print(page_params)
        #         monthlyPredictionTest = MonthlyPredictionTest(page_params,[])
        #         monthlyPredictionTest.execute()
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
    # print(json.dumps(result_dict, ensure_ascii=False))
    # logging.info(json.dumps(result_dict, ensure_ascii=False))
