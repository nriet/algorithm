#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2023/06/14
# @Author : Sbiys
# @File : GainStation2GirdData.py

import numpy as np
import os, sys, json, ast
import xarray as xr
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
from com.nriet.algorithm.business.ExtendedPeriodModeData import ExtendedPeriodModeData
from com.nriet.algorithm.business.StationDataForGbase import StationDataForGbase
from com.nriet.algorithm.business.StationInfoDataForGbase import StationInfoDataForGbase


class GainModesTableData(InputDataComponent):

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
    def init_param(self, params):
        """
        初始化参数
        Args:
            params:

        Returns:

        """
        # page_params = {"timeType": "mon",
        #                "forecastTime": "202304",
        #                "startTime": "202305",
        #                "endTime": "202305",
        #                "dataSource": "NCC,UKMO5",
        #                "dataOutputPath": "/nfsshare/cdbdata/data/dry_data/MCI_20230531.nc",
        #                "areaCode": "33",
        #                "element": "TEMP"}
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
        # 统计量
        self.eleType = params.get("eleType")
        # 区域编码
        self.areaCode = params.get("areaCode")
        self.dataOutputPath = params.get("dataOutputPath")

    # 获取nc数据
    def execute(self, params):
        # 1.初始化参数
        self.init_param(params)
        # 查询浙江省代表站站点信息
        # 组装查询站点信息的参数
        sta_params = {"areaCode": "33", "stationType": "2"}
        sidfg = StationInfoDataForGbase(sta_params, [])
        sidfg.execute()
        stationInfoData = sidfg.output_data["outputData"]
        self.staInfoData = stationInfoData

        result_dict = build_response_dict()
        mode_data_list = []
        datasource_list = self.dataSource.split(",")
        for ds in datasource_list:
            if ds == "CSOD":
                # 推算去年同期开始结束时间
                tmpStartTime = DateUtils.getForwradTime(self.startTime,self.timeType,-12)
                tmpEndTime = DateUtils.getForwradTime(self.endTime,self.timeType,-12)
                moni_data = self.get_station_data(self.timeType,tmpStartTime,tmpEndTime,self.element)
                if not moni_data is None:
                    moni_data = moni_data.expand_dims("modes")
                    moni_data["modes"] = [ds]
                    print(moni_data)
                    mode_data_list.append(moni_data)
            else:
                if ds in ["CPSV3", "CFSV2", "NCC", "CFS2", "JMA3", "UKMO5", "EC5", "CPSV3MON"]:
                    mode_data = self.get_single_data(ds, self.element, self.eleType, self.reportTimeType, self.timeType,
                                                     self.forecastTime, self.startTime, self.endTime, "115,123,27,32")

                else:
                    if ds in ["CFSV2MON"]:
                        mode_data = self.get_single_dm_data(ds, self.element, self.eleType, self.reportTimeType,
                                                            self.timeType, self.forecastTime, self.startTime, self.endTime,
                                                            "115,123,27,32")
                    else:
                        mode_data = self.get_single_mode_data(ds, self.element, self.forecastTime, self.startTime,
                                                              self.endTime, "117,123,27,32")

                if not mode_data is None:
                    g2s_data = mode_data.interp(lat=self.staInfoData.sel(space="lat"), lon=self.staInfoData.sel(space="lon"))
                    g2s_data = xr.DataArray(np.asarray(g2s_data),dims=["station"],coords=[self.staInfoData.station])
                    g2s_data = g2s_data.expand_dims("modes")
                    g2s_data["modes"] = [ds]
                    print(g2s_data)
                    mode_data_list.append(g2s_data)
        modeData = xr.concat(mode_data_list,dim="modes")
        # print(modeData.station.values)
        real_modes = list(modeData.modes.values)
        # exit()
        res_list = []
        # 省
        if self.areaCode =="33":
            # 省
            tmpp = {}
            p_data = modeData.mean(dim="station")
            tmpp["areaCode1"] = "浙江省"
            tmpp["areaCode2"] = "浙江省"
            tmpp["station"] = "/"
            for ds in datasource_list:
                if ds in real_modes:
                    print(ds)
                    tmpp[ds] =  "{:.1f}".format(p_data.sel(modes=ds).values)
                else:
                    tmpp[ds] = "999999"
            res_list.append(tmpp)
            # 市
            city_list = self.city_config["citys"]
            for city in city_list:
                tmpc = {}
                sta = city.get("station").split(",")
                t_data = modeData.sel(station=sta)
                m_data = t_data.mean(dim="station")
                tmpc["areaCode1"] = city.get("cityName")
                tmpc["areaCode2"] = "地区平均"
                tmpc["station"] = "/"
                for ds in datasource_list:
                    if ds in real_modes:
                        tmpc[ds] = "{:.1f}".format(m_data.sel(modes=ds).values)
                    else:
                        tmpc[ds] = "999999"
                res_list.append(tmpc)
                # 县区
                for county in city.get("countys"):
                    tmpcc = {}
                    stac = county.get("station").split(",")
                    tc_data = modeData.sel(station=stac)
                    mc_data = tc_data.mean(dim="station")
                    tmpcc["areaCode1"] = city.get("cityName")
                    tmpcc["areaCode2"] = county.get("countyName")
                    tmpcc["station"] = county.get("station")
                    for ds in datasource_list:
                        if ds in real_modes:
                            tmpcc[ds] = "{:.1f}".format(mc_data.sel(modes=ds).values)
                        else:
                            tmpcc[ds] = "999999"
                    res_list.append(tmpcc)
        # 市
        if len(self.areaCode) == 4:
            city_list = self.city_config["citys"]
            for city in city_list:
                if city.get("cityCode") == self.areaCode:
                    tmpc = {}
                    sta = city.get("station").split(",")
                    t_data = modeData.sel(station=sta)
                    m_data = t_data.mean(dim="station")
                    tmpc["areaCode1"] = city.get("cityName")+"地区平均"
                    tmpc["areaCode2"] = city.get("cityName")+"地区平均"
                    tmpc["station"] = "/"
                    for ds in datasource_list:
                        if ds in real_modes:
                            tmpc[ds] = "{:.1f}".format(m_data.sel(modes=ds).values)
                        else:
                            tmpc[ds] = "999999"
                    res_list.append(tmpc)
                    # 县区
                    for county in city.get("countys"):
                        tmpcc = {}
                        stac = county.get("station").split(",")
                        tc_data = modeData.sel(station=stac)
                        mc_data = tc_data.mean(dim="station")
                        tmpcc["areaCode1"] = city.get("cityName")
                        tmpcc["areaCode2"] = county.get("countyName")
                        tmpcc["station"] = county.get("station")
                        for ds in datasource_list:
                            if ds in real_modes:
                                tmpcc[ds] = "{:.1f}".format(mc_data.sel(modes=ds).values)
                            else:
                                tmpcc[ds] = "999999"
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
                            tc_data = modeData.sel(station=stac)
                            mc_data = tc_data.mean(dim="station")
                            tmpcc["areaCode1"] = city.get("cityName")
                            tmpcc["areaCode2"] = county.get("countyName")
                            tmpcc["station"] = county.get("station")
                            for ds in datasource_list:
                                if ds in real_modes:
                                    tmpcc[ds] = "{:.1f}".format(mc_data.sel(modes=ds).values)
                                else:
                                    tmpcc[ds] = "999999"
                            res_list.append(tmpcc)
                            break
                    break
        # print(res_list)
        creatTxtFile(os.path.dirname(self.dataOutputPath) + "/", os.path.basename(self.dataOutputPath), json.dumps(res_list, ensure_ascii=False))
        result_dict["data"] = res_list
        return result_dict


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

    def get_station_data(self, timeType, startTime, endTime, element):
        try:

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
            alg_input_data = [{"outputData": self.staInfoData}]
            sdfg = StationDataForGbase(moni_params, alg_input_data)
            sdfg.execute()
            moni_data_list = sdfg.output_data["outputData"]
            moni_sk_data = moni_data_list[0]
            moni_ltm_data = moni_data_list[1]
            moni_jp_data = moni_sk_data - moni_ltm_data
            moni_jp_data = moni_jp_data.mean(dim="time")
            return moni_jp_data
        except AlgorithmException as ae:
            logging.info(ae.response_msg)
            return None


if __name__ == "__main__":
    try:
        t1 = DateUtils.getTimeStamp()
        # 获取页面传参
        page_params = ast.literal_eval(sys.argv[1])
        # page_params = {"timeType": "mon",
        #                "reportTimeType": "mon",
        #                "forecastTime": "202304",
        #                "startTime": "202305",
        #                "endTime": "202305",
        #                "dataSource": "CPSV3MON,CFS2,CSOD",
        #                # "dataSource": "MODES_MME,CFS2,EC5,NCC,UKMO5,JMA3,CMMEV2MON,MODES_WMME,SEDES,CPSV3MON",
        #                "dataOutputPath": "/nfsshare/cdbdata/data/dry_data/test_more.json",
        #                "areaCode": "33",
        #                "eleType": "JP",
        #                "element": "AVGT"}
        gs2gd = GainModesTableData()
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
