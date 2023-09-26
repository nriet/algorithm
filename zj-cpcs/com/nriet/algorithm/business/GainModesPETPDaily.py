#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time: 2023/7/18
# @Author: xue
# @File: GainModesPETPDaily.py
import datetime
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
from com.nriet.algorithm.business.ExtendedPeriodModeData import ExtendedPeriodModeData
from com.nriet.utils.fileUtils import creatTxtFile
from com.nriet.algorithm.common.inputData.InputDataComponent import InputDataComponent
from com.nriet.utils import DateUtils
from com.nriet.config import PathConfig
from com.nriet.utils.result.ResponseResultUtils import build_response_dict
from com.nriet.config.ResponseCodeAndMsgEum import PARAMETER_VALUE_MISSING_CODE, \
    PARAMETER_VALUE_MISSING_MSG, CUSTOM_ERROR_CODE, CUSTOM_ERROR_MSG
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.utils.databaseConnection.GbaseHandler import GbaseHandler
from com.nriet.utils.config.ConfigUtils import look_for_gbase_connection_config


class GainModesPETPDaily(InputDataComponent):

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
        """初始化参数"""
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
        self.eleType = "SK"
        # 区域编码
        self.areaCode = params.get("areaCode")
        self.dataOutputPath = params.get("dataOutputPath")

    # 获取nc数据
    def execute(self, params):
        self.init_param(params)
        result_dict = build_response_dict()
        # 获取模式数据
        mode_data = self.get_single_data(self.dataSource, self.element, self.eleType, self.reportTimeType, self.timeType,
                                         self.forecastTime, self.startTime, self.endTime, "115,123,27,32")
        moni_all = []
        zlats = None
        zlons = None
        sk_sta_list = None
        for tt in range(44):
            date_time = (datetime.datetime.strptime(self.startTime, "%Y%m%d") + datetime.timedelta(days=tt)).strftime("%Y-%m-%d")
            #  获取代表站气温实况数据
            sql_sk_tmplate = " SELECT t1.V01301 stationId, max(t3.lat) lat, max(t3.lon) lon, ROUND(AVG(t1.V12001_701), 2) val FROM SURF_WEA_ZJ_MUL_DAY_TAB t1, othe_zj_aws_station_tab t3 WHERE t1.V01301 = t3.station_id AND t3.station_type = '2' AND t1.D_DATETIME BETWEEN '%s' AND '%s' GROUP BY t1.V01301 ORDER BY t1.V01301 ;"
            sql_sk = sql_sk_tmplate % (date_time, date_time)
            print("moni_mean_sql==>" + sql_sk)
            sql_sk_result = self.gbase_handler.executeSql(sql_sk)
            # print(sql_sk_result)
            # 解析查询的结果数据封装成二维数组
            sql_data_sk = pd.DataFrame(list(sql_sk_result))
            sqlData_sk = np.array(sql_data_sk)
            sk_sta_list = sqlData_sk[:, 0]
            zlons = np.asarray(sqlData_sk[:, 2], dtype=np.float32)
            zlats = np.asarray(sqlData_sk[:, 1], dtype=np.float32)
            moni_mean_data = xr.DataArray(np.asarray(sqlData_sk[:, 3], dtype=np.float32), coords=[sk_sta_list], dims=['station'])
            print(moni_mean_data)
            moni_all.append(moni_mean_data)
        moni_mean_data = xr.concat(moni_all, dim='time')
        # 模式插值到站点数据
        lats = xr.DataArray(np.asarray(zlats, dtype=np.float32), coords=[sk_sta_list], dims=['station'])
        lons = xr.DataArray(np.asarray(zlons, dtype=np.float32), coords=[sk_sta_list], dims=['station'])
        m2s_data = mode_data.interp(lat=lats, lon=lons)

        tmp_time_list = DateUtils.get_time_list([self.startTime, self.endTime], time_type=self.timeType)

        # 预测数据m2s_data,距平moni_jp_data
        result_dict = {}
        result_dict["xAxisData"] = [t[0:4] + '-' + t[4:6] + '-' + t[6:8] for t in tmp_time_list]

        # 省
        if self.areaCode == "33":
            sta = list(set(moni_mean_data['station'].values).intersection(m2s_data['station'].values))
            m2s_data = m2s_data.sel(station=sta)
            moni_mean_data = moni_mean_data.sel(station=sta)
            result_dict["SCC"] = ["{:.1f}".format(i) for i in self.get_scc(m2s_data, moni_mean_data).values]
            result_dict["SRMSE"] = ["{:.1f}".format(i) for i in self.get_srmse(m2s_data, moni_mean_data).values]
        # 市
        if len(self.areaCode) == 4:
            city_list = self.city_config["citys"]
            for city in city_list:
                if city.get("cityCode") == self.areaCode:
                    sta = city.get("station").split(",")
                    sta = list(set(sta).intersection(m2s_data['station'].values))
                    m2s_data = m2s_data.sel(station=sta)
                    moni_mean_data = moni_mean_data.sel(station=sta)
                    result_dict["SCC"] = ["{:.1f}".format(i) for i in self.get_scc(m2s_data, moni_mean_data).values]
                    result_dict["SRMSE"] = ["{:.1f}".format(i) for i in self.get_srmse(m2s_data, moni_mean_data).values]  # 县
        if len(self.areaCode) == 6:
            city_list = self.city_config["citys"]
            for city in city_list:
                if city.get("cityCode") == self.areaCode[0:4]:
                    for county in city.get("countys"):
                        if county.get("countyCode") == self.areaCode:
                            stac = county.get("station").split(",")
                            stac = list(set(stac).intersection(m2s_data['station'].values))
                            m2s_data = m2s_data.sel(station=stac)
                            moni_mean_data = moni_mean_data.sel(station=stac)
                            # result_dict["SCC"] = [ j if j!="nan" else "" for j in ["{:.1f}".format(i) for i in self.get_scc(m2s_data,moni_mean_data).values]]
                            result_dict["ERR"] = [j if j != "nan" else "" for j in
                                                  ["{:.1f}".format(i) for i in self.get_err(m2s_data, moni_mean_data)[:, 0].values]]
                            result_dict["SRMSE"] = ["{:.1f}".format(i) for i in self.get_srmse(m2s_data, moni_mean_data).values]
        creatTxtFile(os.path.dirname(self.dataOutputPath) + "/", os.path.basename(self.dataOutputPath), json.dumps(result_dict, ensure_ascii=False))

        # tcc = self.get_tcc(m2s_data, moni_data)
        # tcc.attrs['lats'] = zlats
        # tcc.attrs['lons'] = zlons
        # interLats = [27, 32, 51]
        # interLons = [117, 123, 61]
        # resultData = self.interp_idw(tcc, interLats, interLons, zlats, zlons)
        # resultData = resultData.sortby(resultData["lat"], ascending=False)
        # print(resultData)
        # self.writ_nc([resultData], 'avgt', out_file_path=out_path)

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
        if "station" in data_set.dims:
            data_set.station.values = list(map(int, data_set.station.values))
            encoding["station"] = {'dtype': 'int32', '_FillValue': 999999.0}
        # 设置netcdf的数据属性
        data_set.to_netcdf(out_file_path, encoding=encoding)

    def get_single_data(self, data_source, element, eleType, reportTimeType, timeType, forecastTime, startTime, endTime, region):
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

    def get_scc(self, forcast, sk):
        forcast_mean = np.mean(forcast, axis=1)
        sk_mean = np.mean(sk, axis=1)
        f = forcast - forcast_mean
        o = sk - sk_mean
        a = np.sum(f * o, axis=1)
        b = np.sqrt(np.sum(f ** 2, axis=1) * np.sum(o ** 2, axis=1))
        return a / b

    def get_srmse(self, forcast, sk):
        a = np.sum((forcast - sk) ** 2, axis=1)
        b = np.size(sk[0, :])
        return np.sqrt(a / b)

    def get_err(self, forcast, sk):
        return forcast - sk

    def get_tcc(self, forcast, sk):
        f = forcast - np.nanmean(forcast, axis=0)
        o = sk - np.nanmean(sk, axis=0)
        a = np.sum(f * o, axis=0)
        b = np.sum(f * f, axis=0) * np.sum(o * o, axis=0)
        return a / np.sqrt(b)

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
        # out_path = "/nfsshare/cdbdata/data/dry_data/tcc-2023-05-01_cfsv2.nc"
        # page_params = {"timeType": "day",
        #                "reportTimeType": "day",
        #                "forecastTime": "20230501",
        #                "startTime": "20230502",
        #                "endTime": "20230614",
        #                "dataSource": "CFSV2",
        #                "dataOutputPath": "/nfsshare/cdbdata/data/dry_data/chart_scc2.json",
        #                "var": "avgt",
        #                "areaCode": "33",
        #                "element": "AVGT"}

        gainModesPETPDaily = GainModesPETPDaily()
        result_dict = gainModesPETPDaily.execute(page_params)
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
