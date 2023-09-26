#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2023/06/14
# @Author : Sbiys
# @File : GainPinciData.py

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


class GainPinciData(InputDataComponent):

    def __init__(self):
        # 初始化数据库连接
        self.gbase_handler = GbaseHandler(look_for_gbase_connection_config())
        # 加载城市数据源配置
        cityConfigPath = PathConfig.CPCS_ROOT_PATH + 'com/nriet/config/cityConfig.json'
        with open(cityConfigPath, "r", encoding='UTF-8') as f:
            citystr = f.read()
        self.city_config = json.loads(citystr)
        pass

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
        self.element = params.get("element")
        # 区域编码
        self.areaCode = params.get("areaCode")
        self.dataOutputPath = params.get("dataOutputPath")

    # 获取nc数据
    def execute(self, params):
        # 1.初始化参数
        self.init_param(params)
        result_dict = build_response_dict()
        startYear = "1971"
        endYear = DateUtils.getForwradTime(self.endTime[0:4],"year",-1)
        mm = self.endTime[4:]
        #  获取历年各区气温实况数据
        sql_sk_tmplate = "SELECT SUBSTR(t1.V04001 FROM 1 FOR 4) year, t1.V01301 stationId, ROUND(AVG(t1.V12001_701), 2) val FROM SURF_WEA_ZJ_MUL_MON_TAB t1, othe_zj_aws_station_tab t3 WHERE t1.V01301 = t3.station_id AND t3.station_type = '1' AND t3.area_code LIKE '33%%' AND t1.V04001 BETWEEN '%s' AND '%s' AND t1.v04002 = '%s' GROUP BY t1.V04001, t1.V01301"
        sql_sk = sql_sk_tmplate%(startYear,endYear,mm)
        print("modeData==>" + sql_sk)
        sql_sk_result = self.gbase_handler.executeSql(sql_sk)
        # print(sql_sk_result)
        station_list = self.get_gjz_sta_list()
        time_list = DateUtils.get_time_list([startYear,endYear],"year")
        # 解析查询的结果数据封装成二维数组
        sql_data = pd.DataFrame(list(sql_sk_result))
        sqlData = np.array(sql_data)
        locs = ['year', 'stationId', 'val']
        sql_time_list = sqlData[:, 0]
        sqlData = xr.DataArray(sqlData, coords=[sql_time_list, locs], dims=['sql_time', 'space'])
        res_data1 = []
        nan_data = xr.DataArray(np.full((1, len(station_list)), np.nan, dtype=np.float32), coords=[["999"], station_list],
                                dims=['time', 'station'])
        res_data1.append(nan_data)
        for ii, tt in enumerate(time_list):
            tmpTime = tt
            if tmpTime in sql_time_list:
                data_t = sqlData.sel(sql_time=tmpTime)
                sta_t = list(map(str, data_t.sel(space='stationId').values))
                val_t = list(map(float, data_t.sel(space='val').values))
                tmpdata = xr.DataArray(val_t, coords=[sta_t], dims=['station'])
                # 将数组扩维
                newdata = tmpdata.expand_dims("time")
            else:
                newdata = nan_data
            # 设置时间维度信息
            newdata["time"] = [tt]
            res_data1.append(newdata)
        # 将时间维合并
        moni_sk_data = xr.concat(res_data1, dim="time")
        moni_sk_data = moni_sk_data.sel(time=time_list)
        # print(moni_sk_data)

        #  获取各区气温常年值数据
        sql_ltm_tmplate = "SELECT t1.V01301 stationId, ROUND(AVG(t1.D_VALUE), 2) val FROM SURF_CLI_ZJ_MMON_1991_2020_TAB t1, othe_zj_aws_station_tab t3 WHERE t1.V01301 = t3.station_id AND t3.station_type = '1' AND t3.area_code LIKE '33%%' AND t1.D_ELEMENT = 'V12001_701' AND t1.D_TIME = '%s' GROUP BY t1.V01301"
        sql_ltm = sql_ltm_tmplate%(mm)
        print("ltm==>" + sql_ltm)
        sql_ltm_result = self.gbase_handler.executeSql(sql_ltm)
        # print(sql_ltm_result)
        ltm_data = np.full(len(station_list), np.nan, dtype=np.float32)
        for kk, ac in enumerate(station_list):
            for slr in sql_ltm_result:
                if ac == slr["stationId"]:
                    ltm_data[kk] = float(slr["val"])
                    break
        moni_ltm_data = xr.DataArray(ltm_data, coords=[station_list], dims=['station'])
        # print(moni_ltm_data)
        moni_jp_data = moni_sk_data - moni_ltm_data
        print(moni_jp_data)
        # exit()

        res_dict = {}
        xAxisData_list = []
        more_list= []
        less_list= []
        if self.areaCode == "33":
            # 省
            xAxisData_list.append("浙江省")
            more_list.append(str(len(np.where(moni_jp_data.mean(dim="station") >= 0)[0])))
            less_list.append(str(len(np.where(moni_jp_data.mean(dim="station") < 0)[0])))
            # 市
            city_list = self.city_config["citys"]
            for city in city_list:
                xAxisData_list.append(city.get("cityName"))
                tmpCity = moni_jp_data.sel(station=city.get("gjz").split(","))
                more_list.append(str(len(np.where(tmpCity.mean(dim="station") >= 0)[0])))
                less_list.append(str(len(np.where(tmpCity.mean(dim="station") < 0)[0])))

        # 市
        if len(self.areaCode) == 4:
            city_list = self.city_config["citys"]
            for city in city_list:
                if city.get("cityCode") == self.areaCode:
                    xAxisData_list.append(city.get("cityName"))
                    tmpCity = moni_jp_data.sel(station=city.get("gjz").split(","))
                    more_list.append(str(len(np.where(tmpCity.mean(dim="station") >= 0)[0])))
                    less_list.append(str(len(np.where(tmpCity.mean(dim="station") < 0)[0])))
                    # 县区
                    for county in city.get("countys"):
                        xAxisData_list.append(county.get("countyName"))
                        tmpCounty = moni_jp_data.sel(station=county.get("gjz").split(","))
                        more_list.append(str(len(np.where(tmpCounty.mean(dim="station") >= 0)[0])))
                        less_list.append(str(len(np.where(tmpCounty.mean(dim="station") < 0)[0])))
                    break
        # 县
        if len(self.areaCode) == 6:
            city_list = self.city_config["citys"]
            for city in city_list:
                if city.get("cityCode") == self.areaCode[0:4]:
                    # 县区
                    for county in city.get("countys"):
                        if county.get("countyCode") == self.areaCode:
                            xAxisData_list.append(county.get("countyName"))
                            tmpCounty = moni_jp_data.sel(station=county.get("gjz").split(","))
                            more_list.append(str(len(np.where(tmpCounty.mean(dim="station") >= 0)[0])))
                            less_list.append(str(len(np.where(tmpCounty.mean(dim="station") < 0)[0])))
                            break
                    break


        # print(res_list)
        res_dict["xAxisData"]= xAxisData_list
        res_dict["more"]= more_list
        res_dict["less"]= less_list
        res_dict["subTitle"] = self.endTime[4:]+"月 "+startYear+"-"+endYear+"年"
        creatTxtFile(os.path.dirname(self.dataOutputPath) + "/", os.path.basename(self.dataOutputPath), json.dumps(res_dict, ensure_ascii=False))
        result_dict["data"] = res_dict
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

    def get_gjz_sta_list(self):
        res_sta_list = []
        city_list = self.city_config["citys"]
        for city in city_list:
            res_sta_list.append(city.get("gjz"))
            # print(city.get("cityName")+":"+city.get("gjz"))
        res_sta_list = list(set(",".join(res_sta_list).split(",")))
        res_sta_list.sort()
        return res_sta_list


if __name__ == "__main__":
    try:
        t1 = DateUtils.getTimeStamp()
        # 获取页面传参
        page_params = ast.literal_eval(sys.argv[1])
        # page_params = {"timeType": "mon",
        #                "forecastTime": "202304",
        #                "startTime": "202305",
        #                "endTime": "202305",
        #                "dataSource": "ZJPPC",
        #                "dataOutputPath": "/nfsshare/cdbdata/data/dry_data/test2.json",
        #                "areaCode": "33",
        #                "element": "TMP"}
        gs2gd = GainPinciData()
        result_dict = gs2gd.execute(page_params)
        t2 = DateUtils.getTimeStamp()
        logging.info("获取频次数据总耗时: %s ms" % (str(t2 - t1)))
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
