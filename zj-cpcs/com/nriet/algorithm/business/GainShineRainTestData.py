#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2023/06/14
# @Author : Sbiys
# @File : GainShineRainTestData.py

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
from com.nriet.algorithm.business.StationDataForGbase import StationDataForGbase
from com.nriet.algorithm.business.StationInfoDataForGbase import StationInfoDataForGbase



class GainShineRainTestData(InputDataComponent):

    def __init__(self):
        # 初始化数据库连接
        self.gbase_handler = GbaseHandler(look_for_gbase_connection_config())
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

        # 获取站点监测数据
        moni_data_list = self.get_station_data(self.timeType, self.startTime, self.endTime, self.element, "33")
        moni_data = moni_data_list[0]
        staInfoData = moni_data_list[1]
        # logging.info(moni_data)
        # logging.info(staInfoData)

        dataSource_list = self.dataSource.split(",")
        shineRainProbData_list = []
        # 循环模式数据源统计各模式的晴雨概率数据
        for ds in dataSource_list:
            mode_data = self.get_single_data(ds, self.element, self.reportTimeType, self.timeType, self.forecastTime,
                                             self.startTime, self.endTime, "115,123,27,32")
            if not mode_data is None:
                modeData = mode_data.interp(lat=staInfoData.sel(space="lat"), lon=staInfoData.sel(space="lon"))
                # modeData["station"] = staInfoData.station
                modeData = xr.where(modeData >= 1, 1, 0)
                probData = modeData.sum(dim=["ens"])/len(modeData.ens.values)*100
                probData = probData.expand_dims("modes")
                probData["modes"] = [ds]
                shineRainProbData_list.append(probData)
                # logging.info(probData)
        # 统计多个模式集合平均的晴雨概率数据
        shineRainProbData = xr.concat(shineRainProbData_list, dim="modes")
        # logging.info(shineRainProbData)
        fore_prob_data = shineRainProbData.mean(dim=["modes"])
        # logging.info(fore_prob_data)
        # 监测有降水且晴雨概率预测值超过50%则预测准确 或者 监测无降水且晴雨概率预测值小于等于50%则预测准确
        test_data = np.full((fore_prob_data.shape), np.nan)
        for i in range(fore_prob_data.shape[0]):
            for j in range(fore_prob_data.shape[1]):
                if not np.isnan(moni_data[i,j]) and not np.isnan(fore_prob_data[i,j]):
                    # logging.info(" moni:"+str(moni_data[i,j].values)+" fore:"+str(fore_prob_data[i,j].values))
                    if (moni_data[i,j]>=0.1 and fore_prob_data[i,j]>=50) or (moni_data[i,j]<0.1 and fore_prob_data[i,j]<50):
                        test_data[i, j]=1
                    else:
                        test_data[i, j] = 0
                    # logging.info(" test:" + str(test_data[i, j]))
        test_data = xr.DataArray(test_data, coords=[fore_prob_data["time"],fore_prob_data["station"]], dims=["time","station"])
        # logging.info(test_data)
        #统计各站的预测准确概率 预测准确天数/总天数*100
        tmpdata = test_data.mean(dim=["time"])
        tmpdata = tmpdata.where(np.isnan(tmpdata), 1)
        test_data = test_data.sum(dim=["time"])/test_data.shape[0]*100
        test_data = test_data * tmpdata
        # logging.info(test_data)
        # 封装省市县的检验表格数据
        res_list = []
        # 省
        if self.areaCode == "33":
            # 省
            tmpp = {}
            p_data = test_data.mean(dim="station")
            tmpp["areaCode1"] = "浙江省"
            tmpp["areaCode2"] = "浙江省"
            tmpp["station"] = "/"
            tmpp["jy"] = "999999" if np.isnan(p_data) else "{:.1f}".format(p_data.values)
            res_list.append(tmpp)
            # 市
            city_list = self.city_config["citys"]
            for city in city_list:
                tmpc = {}
                sta = city.get("station").split(",")
                t_data = test_data.sel(station=sta)
                m_data = t_data.mean(dim="station")
                tmpc["areaCode1"] = city.get("cityName")
                tmpc["areaCode2"] = "地区平均"
                tmpc["station"] = "/"
                tmpc["jy"] = "999999" if np.isnan(m_data) else "{:.1f}".format(m_data.values)
                res_list.append(tmpc)
                # 县区
                for county in city.get("countys"):
                    tmpcc = {}
                    stac = county.get("station").split(",")
                    tc_data = test_data.sel(station=stac)
                    mc_data = tc_data.mean(dim="station")
                    tmpcc["areaCode1"] = city.get("cityName")
                    tmpcc["areaCode2"] = county.get("countyName")
                    tmpcc["station"] = county.get("station")
                    tmpcc["jy"] = "999999" if np.isnan(mc_data) else "{:.1f}".format(mc_data.values)
                    res_list.append(tmpcc)
        # 市
        if len(self.areaCode) == 4:
            city_list = self.city_config["citys"]
            for city in city_list:
                if city.get("cityCode") == self.areaCode:
                    tmpc = {}
                    sta = city.get("station").split(",")
                    t_data = test_data.sel(station=sta)
                    m_data = t_data.mean(dim="station")
                    tmpc["areaCode1"] = city.get("cityName") + "地区平均"
                    tmpc["areaCode2"] = city.get("cityName") + "地区平均"
                    tmpc["station"] = "/"
                    tmpc["jy"] = "999999" if np.isnan(m_data) else "{:.1f}".format(m_data.values)
                    res_list.append(tmpc)
                    # 县区
                    for county in city.get("countys"):
                        tmpcc = {}
                        stac = county.get("station").split(",")
                        tc_data = test_data.sel(station=stac)
                        mc_data = tc_data.mean(dim="station")
                        tmpcc["areaCode1"] = city.get("cityName")
                        tmpcc["areaCode2"] = county.get("countyName")
                        tmpcc["station"] = county.get("station")
                        tmpcc["jy"] = "999999" if np.isnan(mc_data) else "{:.1f}".format(mc_data.values)
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
                            tc_data = test_data.sel(station=stac)
                            mc_data = tc_data.mean(dim="station")
                            tmpcc["areaCode1"] = city.get("cityName")
                            tmpcc["areaCode2"] = county.get("countyName")
                            tmpcc["station"] = county.get("station")
                            tmpcc["jy"] = "999999" if np.isnan(mc_data) else "{:.1f}".format(mc_data.values)
                            res_list.append(tmpcc)
                            break
                    break
        # 保存表格数据
        creatTxtFile(os.path.dirname(self.dataOutputPath) + "/", os.path.basename(self.dataOutputPath), json.dumps(res_list, ensure_ascii=False))
        # result_dict["data"] = res_list
        return result_dict

    def get_single_data(self,data_source, element, reportTimeType, timeType, forecastTime, startTime, endTime, region):
        dataCfg = self.datasource_config[data_source.upper() + "_" + element.upper() + "_" + reportTimeType.upper()]
        dataInputPath = dataCfg["dataInputPath"]
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
        sub_local_params["forecastPeriod"] = [startTime, endTime]
        sub_local_params["dataSet"] = "ens"
        sub_local_params["elements"] = var
        sub_local_params["unitConvert"] = unitConvert
        sub_local_params["whetherMakeup"] = "True"
        sub_local_params["dataInputPaths"] = dataInputPath
        algorithm_input_data = []
        try:
            epmd = ExtendedPeriodModeData(sub_local_params, algorithm_input_data)
            epmd.execute()
        except AlgorithmException as ae:
            logging.info(ae.response_msg)
            return None
        fore_data = epmd.output_data["outputData"]
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

    def get_station_data(self, timeType, startTime, endTime, element, areaCode):
        try:
            # 查询浙江省代表站站点信息
            # 组装查询站点信息的参数
            sta_params={"areaCode":areaCode, "stationType":"2"}
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
            moni_params["eleType"] = "SK"
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


if __name__ == "__main__":
    try:
        t1 = DateUtils.getTimeStamp()
        # 获取页面传参
        page_params = ast.literal_eval(sys.argv[1])
        # page_params = {"reportTimeType": "day",
        #                 "timeType": "day",
        #                "forecastTime": "20230504",
        #                "startTime": "20230511",
        #                "endTime": "20230530",
        #                "dataSource": "CFSV2,CPSV3,ECMWF",
        #                "dataOutputPath": "/nfsshare/cdbdata/data/dry_data/test_shine_rain_data.json",
        #                "areaCode": "3305",
        #                "element": "RAIN"}
        gs2gd = GainShineRainTestData()
        result_dict = gs2gd.execute(page_params)
        t2 = DateUtils.getTimeStamp()
        logging.info("获取晴雨概率预测检验表格数据总耗时: %s ms" % (str(t2 - t1)))
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
