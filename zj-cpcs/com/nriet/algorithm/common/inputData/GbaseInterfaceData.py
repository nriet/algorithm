# -*- coding:utf-8 -*-
# @Time : 2020/09/01
# @Author : huxin
# @File : StationInterfaceData.py


from com.nriet.algorithm.common.inputData.InputDataComponent import InputDataComponent
from com.nriet.utils.decorator.TimerDecorator import timer_with_param
import numpy as np
import xarray as xr
import logging
from com.nriet.utils import DateUtils
from com.nriet.utils.databaseConnection.MySQLHandler import MysqldbHelper
from com.nriet.config.MySQLConfig import config
from com.nriet.utils.config.ConfigUtils import look_for_gbase_connection_config
from com.nriet.utils.databaseConnection.GbaseHandler import GbaseHandler


class GbaseInterfaceData(InputDataComponent):


    def __init__(self, sub_local_params, algorithm_input_data):
        """
        :param sub_local_params:流程参数，算法运算返回结果
        :param algorithm_input_data:流程数据
        """
        # 查询的表名
        self.tableName = sub_local_params.get("tableName")
        # 查询的表字段
        self.tableField = sub_local_params.get("tableField")
        # 区域
        self.areaCode = sub_local_params.get("areaCode")
        # 统计方法
        self.statisticType = sub_local_params.get("statMethod")
        # 数据计算时间类型
        self.timeTypes = sub_local_params.get("timeType")
        # 数据计算时间范围
        self.timeRanges = sub_local_params.get("timeRanges")
        # 起报时间
        self.reportingTime = sub_local_params.get("reportingTime")
        # 预报时段
        self.forecastPeriod = sub_local_params.get("forecastPeriod")
        # 计算类型
        self.eleType = sub_local_params.get("eleType")
        # 气候态
        self.ltm = sub_local_params.get("ltm", "1981-2010")
        if self.ltm == "":
            self.ltm = "1981-2010"
        # 单位转化 （转化方式_转化值）
        self.unit_convert = sub_local_params.get("unitConvert")
        self.dataSource = sub_local_params.get("dataSource")
        # 初始化数据库连接
        # 大气污染连mysql库， 基础要素连gbase库
        if self.tableName in ["SURF_AQI_CHN_MUL_DAY_TAB", "SURF_AQI_CHN_PREP_DAY_TAB"]:
            self.mydb = MysqldbHelper(config)
        else:
            self.mydb = GbaseHandler(look_for_gbase_connection_config())
            self.tableName = "usr_sod."+self.tableName

        # 输出结果
        self.output_data = None
        self.stationInfoData = None

    @timer_with_param("          get gbase station data by interface") #注解。计算调用站点算法耗时，单位：秒
    def execute(self):
        #加载站点信息
        self.queryStationInfoData()
        #获取数据
        if self.eleType == "LTM":
            res_data = self.queryLtmData()
        else:
            if self.dataSource == "S2S-CUACE":
                res_data = self.queryAQIForeMeanData()
            else:
                res_data = self.queryMeanData()
                if self.eleType == "JP":
                    data_ltm = self.queryLtmData()
                    res_data = res_data - data_ltm
                    if self.tableField in ["V13023","V13305","V13306"]:
                        data_ltm = np.where(data_ltm == 0, 0.1, data_ltm)
                        res_data = res_data / data_ltm * 100
        # 封装返回的结果数据
        output_data=[]
        output_data.append({"outputData": res_data})
        output_data.append({"outputData": self.stationInfoData})
        self.output_data = output_data


    def queryStationInfoData(self):
        areaField = "D_AREACODE"
        if self.areaCode == "CH":
            areaField = "D_PARENTCODE"
        # 基础要素站点信息表
        tableName = "CIPAS_STATION_INFO"
        # 大气污染监测站点信息表
        if self.tableName == "SURF_AQI_CHN_MUL_DAY_TAB":
            tableName = "CIPAS_AQI_STATION_INFO"
        # 大气污染预测站点信息表
        if self.dataSource == "S2S-CUACE":
            tableName = "CIPAS_AQI_PREP_STATION_INFO"
        # 拼接获取站点信息数据的SQL
        sql_str = " SELECT c3.stationId, c3.latitude, c3.lontitude FROM CIPAS_AREA_INFO c1, CIPAS_AREA_STATION c2, "+tableName+" c3" \
                  " WHERE c1.D_AREACODE = c2.D_AREACODE AND c2.stationId = c3.stationId AND c3.stationType = 0" \
                  " AND c1." + areaField + "  = '" + self.areaCode + "'"
        # 查询数据
        sql_result = self.mydb.executeSql(sql_str)
        # 封装数据
        data_info_list = []
        station_list = []
        for i, rr in enumerate(sql_result):
            station_list.append(float(rr["stationId"]))
            data_info_list.append([float(rr["stationId"]), float(rr["latitude"]), float(rr["lontitude"])])
        locs = ['station', 'lat', 'lon']
        statInfoData = xr.DataArray(np.asarray(data_info_list), coords=[station_list, locs], dims=['station', 'space'])
        # 将合数据按站点进行排序，重新整合数据
        b = sorted(enumerate(station_list), key=lambda x: x[1])
        # logging.info(station_list)
        sta_index = [x[0] for x in b]
        statInfoData = statInfoData.isel(station=sta_index)
        self.stationInfoData = statInfoData

    def queryMeanData(self):
        areaField = "D_AREACODE"
        if self.areaCode == "CH":
            areaField = "D_PARENTCODE"

        startTime = DateUtils.dateToStr(DateUtils.strToDate(str(self.timeRanges[0]),"%Y%m%d"),"%Y-%m-%d")
        endTime =  DateUtils.dateToStr(DateUtils.strToDate(str(self.timeRanges[1]),"%Y%m%d"),"%Y-%m-%d")
        # 拼接获取实况数据的SQL
        sql_str = " SELECT dt.stationId, ROUND(" + self.statisticType + "(dt." + self.tableField + "),1) val FROM(" \
            " SELECT DISTINCT t2.stationId, t3.D_DATETIME, t3." + self.tableField + " FROM  CIPAS_AREA_INFO t1,CIPAS_AREA_STATION t2," + self.tableName + " t3 " \
            " WHERE t1.D_AREACODE = t2.D_AREACODE AND t2.stationId = t3.V01301" \
            " AND t3." + self.tableField + " < 99999" \
            " AND t1." + areaField + "  = '" + self.areaCode + "'" \
            " AND (t3.D_DATETIME BETWEEN '" + startTime + "' AND '" + endTime + "')" \
            " ) dt  GROUP BY dt.stationId"
        # 查询数据
        sql_result = self.mydb.executeSql(sql_str)
        # 封装数据
        data_list = []
        station_list = []
        for i, rr in enumerate(sql_result):
            data_list.append(float(rr["val"]))
            station_list.append(float(rr["stationId"]))
        staMeanData = xr.DataArray(np.asarray(data_list), coords=[station_list], dims=['station'])

        # 补全数据
        sta_diff_list1 = list(set(station_list).difference(set(self.stationInfoData.sel(space="station").values)))
        if len(sta_diff_list1)>0:
            station_list = list(set(station_list).difference(set(sta_diff_list1)))
            staMeanData = staMeanData.sel(station=station_list)
        sta_diff_list = list(set(self.stationInfoData.sel(space="station").values).difference(set(station_list)))
        if len(sta_diff_list)>0:
            result_data_m = xr.DataArray(np.full(len(sta_diff_list), np.nan, dtype=np.float32), coords=[sta_diff_list],dims=['station'])
            staMeanData = xr.concat([staMeanData,result_data_m],dim="station")
        # 将合并后的数据按站点进行排序，重新整合数据
        b = sorted(enumerate(staMeanData.station.values), key=lambda x: x[1])
        sta_index = [x[0] for x in b]
        staMeanData = staMeanData.isel(station=sta_index)
        # 能见度单位处理
        if self.tableField in ["V20059", "V20001_701"]:
            staMeanData = staMeanData * 0.001
        # 风速单位处理
        if self.tableField in ["V11002"]:
            staMeanData = staMeanData * 0.1
        return staMeanData

    def queryLtmData(self):
        areaField = "D_AREACODE"
        if self.areaCode == "CH":
            areaField = "D_PARENTCODE"

        startTime = DateUtils.dateToStr(DateUtils.strToDate(str(self.timeRanges[0]), "%Y%m%d"), "%Y-%m-%d")
        endTime = DateUtils.dateToStr(DateUtils.strToDate(str(self.timeRanges[1]), "%Y%m%d"), "%Y-%m-%d")
        # 处理 月、日 条件
        startMon = int(startTime[5:7])
        startDay = int(startTime[8:10])
        endMon = int(endTime[5:7])
        endDay = int(endTime[8:10])
        md_str = ""
        if startMon == endMon:  # 同一月
            md_str = "t3.V04002 = %s AND t3.V04003 BETWEEN %s AND %s" % (startMon, startDay, endDay)
        else:
            # 获取月份数组
            if startMon > endMon:  # 开始月份>结束月份
                mon_list = list(range(startMon, 13))
                mon_list.extend(set(range(1, endMon + 1)))
            else:  # 开始月份< 结束月份
                mon_list = list(range(startMon, endMon + 1))
            # 处理开始月不是从1号开始查询的情况
            if startDay > 1:
                start_str = "(t3.V04002 = %s AND t3.V04003 >= %s)" % (startMon, startDay)
                if len(md_str) == 0:
                    md_str = md_str + start_str
                else:
                    md_str = md_str + " OR " + start_str
                mon_list.remove(startMon)
            # 处理结束月不是查询到最后一天的的情况
            ED_list = [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            ED = ED_list[endMon]
            if endDay < ED:
                end_str = "(t3.V04002 = %s AND t3.V04003 <= %s)" % (endMon, endDay)
                if len(md_str) == 0:
                    md_str = md_str + end_str
                else:
                    md_str = md_str + " OR " + end_str
                mon_list.remove(endMon)
            # 处理中间月
            if len(mon_list) > 0:
                middle_str = "t3.V04002 IN (%s)"
                if len(mon_list) == 1:
                    middle_str = "t3.V04002 = %s"
                middle_str = middle_str % (",".join(list(map(str, mon_list))))
                if len(md_str) == 0:
                    md_str = md_str + middle_str
                else:
                    md_str = md_str + " OR " + middle_str

        # 拼接计算常年值 SQL
        sql_str = "SELECT t.stationId, ROUND(AVG(t.`value`),1) val FROM (" \
            " SELECT s.stationId , s.year_time, " + self.statisticType + "(s." + self.tableField + ") `value` FROM (" \
            " SELECT t2.stationId, t3.D_DATETIME,  t3." + self.tableField + ",t3.V04001 year_time" \
            " FROM  CIPAS_AREA_INFO t1,CIPAS_AREA_STATION t2," + self.tableName + " t3" \
            " WHERE t1.D_AREACODE = t2.D_AREACODE AND t2.stationId = t3.V01301" \
            " AND t1." + areaField + "  = '" + self.areaCode + "'" \
            " AND (t3.V04001 BETWEEN "+self.ltm.split("-")[0]+" AND "+self.ltm.split("-")[1]+" )" \
            " AND (" + md_str + ")" \
            " ) s" \
            "  where s." + self.tableField + " < 99999" \
            " GROUP BY s.stationId,s.year_time" \
            ") t" \
            "  GROUP BY t.stationId"
        logging.info(sql_str)
        # 查询数据
        sql_result = self.mydb.executeSql(sql_str)
        # 封装数据
        data_list = []
        station_list = []
        for i, rr in enumerate(sql_result):
            data_list.append(float(rr["val"]))
            station_list.append(float(rr["stationId"]))
        staLtmData = xr.DataArray(np.asarray(data_list), coords=[station_list], dims=['station'])
        # 补全数据
        sta_diff_list1 = list(set(station_list).difference(set(self.stationInfoData.sel(space="station").values)))
        if len(sta_diff_list1) > 0:
            station_list = list(set(station_list).difference(set(sta_diff_list1)))
            staLtmData = staLtmData.sel(station=station_list)
        sta_diff_list = list(set(self.stationInfoData.sel(space="station").values).difference(set(station_list)))
        if len(sta_diff_list) > 0:
            result_data_m = xr.DataArray(np.full(len(sta_diff_list), np.nan, dtype=np.float32), coords=[sta_diff_list],
                                         dims=['station'])
            staLtmData = xr.concat([staLtmData, result_data_m], dim="station")
        # 将合并后的数据按站点进行排序，重新整合数据
        b = sorted(enumerate(staLtmData.station.values), key=lambda x: x[1])
        # logging.info(station_list)
        sta_index = [x[0] for x in b]
        staLtmData = staLtmData.isel(station=sta_index)
        # 能见度单位处理
        if self.tableField in ["V20059", "V20001_701"]:
            staLtmData = staLtmData * 0.001
        # 风速单位处理
        if self.tableField in ["V11002"]:
            staLtmData = staLtmData * 0.1
        return staLtmData

    def queryAQIForeMeanData(self):
        areaField = "D_AREACODE"
        if self.areaCode == "CH":
            areaField = "D_PARENTCODE"

        startTime = DateUtils.dateToStr(DateUtils.strToDate(str(self.forecastPeriod[0]), "%Y%m%d"), "%Y-%m-%d")
        endTime =  DateUtils.dateToStr(DateUtils.strToDate(str(self.forecastPeriod[1]), "%Y%m%d"), "%Y-%m-%d")
        # 拼接获取实况数据的SQL
        # 大气污染降水预测时间内求和处理
        if self.tableField == 'prate_avg':
            self.statisticType = "SUM"
        else:
            self.statisticType = "AVG"
        sql_str = " SELECT dt.stationId, ROUND(" + self.statisticType + "(dt." + self.tableField + "),1) val FROM(" \
            " SELECT DISTINCT t2.stationId, t3.D_DATETIME, t3." + self.tableField + " FROM  CIPAS_AREA_INFO t1,CIPAS_AREA_STATION t2," + self.tableName + " t3 " \
            " WHERE t1.D_AREACODE = t2.D_AREACODE AND t2.stationId = t3.V01301" \
            " AND t3." + self.tableField + " < 99999" \
            " AND t1." + areaField + "  = '" + self.areaCode + "'" \
            " AND (t3.D_DATETIME_FORECAST BETWEEN '" + startTime + "' AND '" + endTime + "')" \
            " AND t3.D_DATETIME = '"+self.reportingTime+"'" \
            " ) dt  GROUP BY dt.stationId"
        # 查询数据
        # print(sql_str)
        # exit()
        sql_result = self.mydb.executeSql(sql_str)
        # 封装数据
        data_list = []
        station_list = []
        for i, rr in enumerate(sql_result):
            data_list.append(float(rr["val"]))
            station_list.append(float(rr["stationId"]))
        staMeanData = xr.DataArray(np.asarray(data_list), coords=[station_list], dims=['station'])

        # 补全数据
        sta_diff_list1 = list(set(station_list).difference(set(self.stationInfoData.sel(space="station").values)))
        if len(sta_diff_list1)>0:
            station_list = list(set(station_list).difference(set(sta_diff_list1)))
            staMeanData = staMeanData.sel(station=station_list)
        sta_diff_list = list(set(self.stationInfoData.sel(space="station").values).difference(set(station_list)))
        if len(sta_diff_list)>0:
            result_data_m = xr.DataArray(np.full(len(sta_diff_list), np.nan, dtype=np.float32), coords=[sta_diff_list],dims=['station'])
            staMeanData = xr.concat([staMeanData,result_data_m],dim="station")
        # 将合并后的数据按站点进行排序，重新整合数据
        b = sorted(enumerate(staMeanData.station.values), key=lambda x: x[1])
        sta_index = [x[0] for x in b]
        staMeanData = staMeanData.isel(station=sta_index)
        return staMeanData

# if __name__ == '__main__':
#     # , , , statisticType, startTime, endTime
#     sub_local_params={
#         'tableName':'SURF_WEA_GLB_MUL_GSODDAY_TAB'
#         # ,'tableField':'V13023'
#         ,'tableField':'V12001_701'
#         ,'areaCode':'GL'
#         # ,'statMethod':'SUM'
#         ,'statMethod':'AVG'
#         ,'timeType':'day'
#         ,'eleType':'JP'
#         ,'timeRanges':[20210101,20210115]
#     }
#     gid = GbaseInterfaceData(sub_local_params,None)
#     # gid.query_data()
#     try:
#         gid.execute()
#         logging.info(gid.output_data)
#     except AlgorithmException as e:
#         logging.info(e.__str__())
