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
    PARAMETER_VALUE_MISSING_MSG, CUSTOM_ERROR_CODE, CUSTOM_ERROR_MSG, DB_DATA_NOT_FOUND_ERROR_CODE
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.utils.fileUtils import creatTxtFile
from com.nriet.utils.databaseConnection.GbaseHandler import GbaseHandler
from com.nriet.utils.config.ConfigUtils import look_for_gbase_connection_config
from com.nriet.algorithm.business.ExtendedPeriodModeData import ExtendedPeriodModeData


class GainModesTimeVariantTestData(InputDataComponent):

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
        # # 统计量
        self.eleType = params.get("eleType")
        # 区域编码
        self.areaCode = params.get("areaCode")
        # 检验方法
        self.methodType = params.get("methodType")
        self.dataOutputPath = params.get("dataOutputPath")

    # 获取nc数据
    def execute(self, params):
        # 1.初始化参数
        self.init_param(params)
        result_dict = build_response_dict()
        # 次季节模式的预测数据获取(日预报月)
        if self.reportTimeType == "day" and self.timeType == "mon":
            # 起报时间的当前月1号
            tmpForeStartTime = self.forecastTime[0:6]+"01"
            tmpForeEndTime = self.forecastTime
            fore_time_list = DateUtils.get_time_list([tmpForeStartTime, tmpForeEndTime], self.reportTimeType)
            print(fore_time_list)
            # 获取12个月的模式数据并插值到站点
            mode_data_list = []
            for ftt in fore_time_list:
                if self.dataSource in ["CFSV2MON"]:
                    mode_data = self.get_single_dm_data(self.dataSource, self.element, self.eleType,
                                                        self.reportTimeType, self.timeType, ftt, self.startTime, self.endTime,
                                                        "115,125,25,34")
                else:
                    mode_data = self.get_single_data(self.dataSource, self.element, self.eleType, self.reportTimeType,
                                                          self.timeType, ftt, self.startTime, self.endTime, "115,125,25,34")
                if not mode_data is None:
                    mode_data = mode_data.mean(dim="time")
                    g2s_data = mode_data.interp(lat=self.staInfoData.sel(space="lat"),lon=self.staInfoData.sel(space="lon"))
                    g2s_data = g2s_data.expand_dims("time")
                    g2s_data["time"] = [ftt]
                    # print(g2s_data)
                    mode_data_list.append(g2s_data)
            modeData = xr.concat(mode_data_list, dim="time")
            xStartTime, xEndTime = tmpForeStartTime, tmpForeEndTime

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
        if self.methodType in ["ERR", "RERR", "SYMBOL"]:
            modeData = modeData.mean(dim="station")
        print(modeData)

        #  获取代表站气温实况数据
        if self.timeType == "day":
            tableName = "SURF_WEA_ZJ_MUL_DAY_TAB"
            tmpStartTime = DateUtils.time_format_en(self.startTime, self.timeType, "-")
            tmpEndTime = DateUtils.time_format_en(self.endTime, self.timeType, "-")
        if self.timeType == "mon":
            # tableName = "SURF_WEA_ZJ_MUL_MON_TAB"
            # tmpStartTime = DateUtils.time_format_en(self.startTime,self.timeType,"-")+"-01"
            # tmpEndTime = DateUtils.time_format_en(self.endTime,self.timeType,"-")+"-01"
            tableName = "SURF_WEA_ZJ_MUL_DAY_TAB"
            tmpStartTime = DateUtils.time_format_en(DateUtils.otherTime2Day(self.startTime, self.timeType)[0], "day",
                                                    "-")
            tmpEndTime = DateUtils.time_format_en(DateUtils.otherTime2Day(self.endTime, self.timeType)[1], "day", "-")
        sql_sk_tmplate = " SELECT t1.V01301 stationId, max(t3.lat) lat, max(t3.lon) lon, ROUND(AVG(t1.V12001_701), 2) val FROM %s t1, othe_zj_aws_station_tab t3 WHERE t1.V01301 = t3.station_id AND t3.station_type = '2' AND t3.area_code like '%s%%' AND t1.D_DATETIME BETWEEN '%s' AND '%s' GROUP BY t1.V01301 ORDER BY t1.V01301"
        sql_sk = sql_sk_tmplate % (tableName, self.areaCode, tmpStartTime, tmpEndTime)
        print("moni_mean_sql==>" + sql_sk)
        sql_sk_result = self.gbase_handler.executeSql(sql_sk)
        if len(sql_sk_result) == 0:
            error_str = "当前SQL==>[%s]未查询到数据！" % sql_sk
            raise AlgorithmException(response_code=DB_DATA_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        # 解析查询的结果数据封装成二维数组
        sql_data_sk = pd.DataFrame(list(sql_sk_result))
        sqlData_sk = np.array(sql_data_sk)
        sk_sta_list = sqlData_sk[:, 0]
        zlons = np.asarray(sqlData_sk[:, 2], dtype=np.float32)
        zlats = np.asarray(sqlData_sk[:, 1], dtype=np.float32)
        moni_mean_data = xr.DataArray(np.asarray(sqlData_sk[:, 3], dtype=np.float32), coords=[sk_sta_list],
                                      dims=['station'])
        # 对代表站进行平均
        if self.methodType in ["ERR","RERR","SYMBOL"]:
            moni_mean_data = moni_mean_data.mean(dim="station")
        else:
            modeData = modeData.sel(station=moni_mean_data.station.values)
        print(moni_mean_data)
        res_data_list = []
        res_time_list = DateUtils.get_time_list([xStartTime, xEndTime], self.reportTimeType)
        for tt in res_time_list:
            if tt in modeData.time.values:
                if self.methodType == "PS":
                    res_data_list.append("")
                if self.methodType == "PC":
                    res_data_list.append("")
                if self.methodType == "ACC":
                    res_data_list.append("")
                if self.methodType == "SCC":
                    res_data_list.append("{:.1f}".format(self.get_scc(modeData.sel(time=tt), moni_mean_data).values))
                if self.methodType == "SRMSE":
                    res_data_list.append("{:.1f}".format(self.get_rmse(modeData.sel(time=tt), moni_mean_data).values))
                if self.methodType == "ERR":
                    res_data_list.append(self.get_err(modeData.sel(time=tt).values, moni_mean_data.values))
                if self.methodType == "RERR":
                    res_data_list.append(self.get_rerr(modeData.sel(time=tt).values, moni_mean_data.values))
                if self.methodType == "SYMBOL":
                    res_data_list.append(self.get_symbol(modeData.sel(time=tt).values, moni_mean_data.values))
            else:
                res_data_list.append("")

        res_data_dict={}
        res_data_dict[self.methodType] = res_data_list
        res_data_dict["xAxisData"] = [DateUtils.time_format_en(tt,self.reportTimeType,"-") for tt in res_time_list]
        res_data_dict["xAxisDataCh"] = [DateUtils.time_format_ch(tt,self.reportTimeType) for tt in res_time_list]
        res_data_dict["subTitle"] = DateUtils.time_format_ch(xStartTime,self.reportTimeType)+"-"+DateUtils.time_format_ch(xEndTime,self.reportTimeType)
        creatTxtFile(os.path.dirname(self.dataOutputPath) + "/", os.path.basename(self.dataOutputPath), json.dumps(res_data_dict, ensure_ascii=False))
        result_dict["data"] = res_data_dict
        return result_dict

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
        if not os.path.exists(dataInputPath_ym):
            return None
        ds = xr.open_dataset(dataInputPath_ym, decode_times=False)
        modedata = ds[var]
        modedata = self.partitioned_data(modedata, region)
        modedata = modedata.expand_dims("time")
        modedata["time"] = [endTime]
        # 数据的纬度处理成从北到南（即从大到小）
        modedata = modedata.sortby(modedata["lat"], ascending=False)
        return modedata

    def get_err(self, p, o):
        return "{:.1f}".format(p - o)

    def get_rerr(self, p, o):
        tmp = p - o
        o_data = np.where(o == 0, np.nan, o)
        return "{:.1f}".format(tmp / o_data * 100)

    def get_symbol(self, p, o):
        # 符号判定
        if p != 0 and o != 0:
            if p * o > 0:
                symbol = 1
            else:
                symbol = -1
        elif p == 0 and o != 0:
            if o > 0:
                symbol = 1
            else:
                symbol = -1
        elif p != 0 and o == 0:
            if p > 0:
                symbol = 1
            else:
                symbol = -1
        else:
            symbol = 1
        return str(symbol)

    def get_scc(self, forcast, sk):
        forcast_mean = np.mean(forcast)
        sk_mean = np.mean(sk)
        f = forcast - forcast_mean
        o = sk - sk_mean
        a = np.sum(f * o)
        b = np.sqrt(np.sum(f ** 2) * np.sum(o ** 2))
        return a / b

    def get_rmse(self, forcast, sk):
        a = np.sum((forcast - sk) ** 2)
        return np.sqrt(a / len(forcast))


if __name__ == "__main__":
    try:
        t1 = DateUtils.getTimeStamp()
        # 获取页面传参
        page_params = ast.literal_eval(sys.argv[1])
        # page_params = {"reportTimeType": "day",
        #                 "timeType": "mon",
        #                "forecastTime": "20230531",
        #                "startTime": "202306",
        #                "endTime": "202306",
        #                "dataSource": "CPSV3",
        #                # "dataSource": "MODES_MME,MODES_CFS2,MODES_EC5,MODES_NCC,MODES_UKMO5,MODES_JMA3,CMMEV2_MME,MODES_WMME,SEDES,ZJPPC",
        #                "dataOutputPath": "/nfsshare/cdbdata/data/dry_data/test_more11.json",
        #                "areaCode": "3305",
        #                "methodType": "RMSE",
        #                "eleType": "SK",
        #                "element": "AVGT"}
        gs2gd = GainModesTimeVariantTestData()
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
