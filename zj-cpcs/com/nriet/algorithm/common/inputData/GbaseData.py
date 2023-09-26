# -*- coding:utf-8 -*-
# @Time : 2020/09/01
# @Author : huxin
# @File : GbaseData.py


import os, json
import numpy as np
import xarray as xr
import pandas as pd
import logging
logger = logging.getLogger(__name__)
logger.root.setLevel(level=logging.INFO)
from com.nriet.algorithm.common.inputData.InputDataComponent import InputDataComponent
from com.nriet.utils.decorator.TimerDecorator import timer_with_param
from com.nriet.utils import DateUtils
from com.nriet.config.ResponseCodeAndMsgEum import CUSTOM_ERROR_CODE, DB_DATA_NOT_FOUND_ERROR_CODE
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.utils.config.ConfigUtils import look_for_gbase_connection_config
from com.nriet.utils.databaseConnection.GbaseHandler import GbaseHandler


class GbaseData(InputDataComponent):

    def __init__(self, sub_local_params, algorithm_input_data):
        """
        :param sub_local_params:流程参数，算法运算返回结果
        :param algorithm_input_data:流程数据
        """
        # 数据源
        self.dataSource = sub_local_params.get("dataSource")
        # 要素
        self.elements = sub_local_params.get("elements")
        # 加载Gbase要素配置map
        basedir = os.path.abspath(os.path.dirname(__file__))
        basedir = basedir[0:basedir.rfind("/com/")]
        configPath = basedir + "/com/nriet/config/gbaseElementConfig.json"
        logging.info(configPath)

        with open(configPath, "r") as f:
            datastr = f.read()
            # logging.info(datastr)
        self.gbase_element_config = json.loads(datastr)
        # 区域
        self.areaCode = sub_local_params.get("areaCode")
        # 统计方法
        self.statisticType = sub_local_params.get("statisticType")
        # 数据计算时间类型
        self.timeTypes = sub_local_params.get("timeType")
        # 数据计算时间范围
        self.timeRanges = sub_local_params.get("timeRanges")
        # 计算类型
        self.eleType = sub_local_params.get("eleType")
        # 气候态
        self.ltm = sub_local_params.get("ltm", "1981-2010")
        # 单位转化 （转化方式_转化值）
        self.unit_convert = sub_local_params.get("unitConvert")
        self.stationStr = sub_local_params.get("stationStr")
        # 初始化数据库连接
        self.mydb = GbaseHandler(look_for_gbase_connection_config())

        # 输出结果
        self.output_data = None
        self.stationInfoData = None

    @timer_with_param("          get gbase station data by interface") #注解。计算调用站点算法耗时，单位：秒
    def execute(self):
        output_data = []
        #加载站点信息
        self.queryStationInfoData()
        if self.eleType.find("SK") != -1:
            # 获取数据
            res_data_mean = self.query_mean_data(self.timeTypes, str(self.timeRanges[0]), str(self.timeRanges[1]), self.dataSource, self.elements,self.areaCode,self.stationStr,self.statisticType)
            # 封装返回的结果数据
            output_data.append({"outputData": res_data_mean})
        if self.eleType.find("LTM") != -1:
            # 获取数据
            res_data_ltm = self.query_ltm_data(self.timeTypes, str(self.timeRanges[0]), str(self.timeRanges[1]),
                                            self.dataSource, self.elements, self.areaCode, self.stationStr,
                                            self.statisticType, self.ltm)
            # 封装返回的结果数据
            output_data.append({"outputData": res_data_ltm})
        # output_data.append({"outputData": self.stationInfoData})
        self.output_data = output_data

    def queryStationInfoData(self):
        areaField = "D_AREACODE"
        if self.areaCode == "CH":
            areaField = "D_PARENTCODE"
        # 基础要素站点信息表
        tableName = "CIPAS_STATION_INFO"
        if self.areaCode == "AQI_CH":
            tableName = "CIPAS_STATION_INFO"
        if self.stationStr:
            sql_str = " SELECT c3.stationId, c3.latitude, c3.lontitude FROM " + tableName + " c3" \
                      " WHERE 1=1 AND c3.stationType = 0 " \
                      " AND c3.stationId in ('" + self.stationStr.replace(",", "','") + "')"
        else:
            sql_str = " SELECT c3.stationId, c3.latitude, c3.lontitude FROM CIPAS_AREA_INFO c1, CIPAS_AREA_STATION c2, "+tableName+" c3" \
                      " WHERE c1.D_AREACODE = c2.D_AREACODE AND c2.stationId = c3.stationId AND c3.stationType = 0" \
                      " AND c1." + areaField + "  = '" + self.areaCode + "'"
        # print(sql_str)
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

    def query_mean_data(self, timeType, startTime, endTime, dataSource, elements, areaCode, stationStr, statisticType):
        key = dataSource.upper()+"_"+elements.upper()+"_"+timeType.upper()
        logger.info(key)
        sta_list = list(map(int, self.stationInfoData.sel(space="station").values))
        time_list = DateUtils.get_time_list([startTime, endTime], timeType)
        # 查询的要素的表字段
        tableField = self.gbase_element_config.get(key).get("tableField")
        # 各尺度的时间分组处理
        if timeType == "day":
            wantTimeStr = "SUBSTRING(t3.D_DATETIME, 1, 10) want_time"
        if timeType == "five":
            wantTimeStr = "CASE WHEN t3.V04003 BETWEEN 1 AND 5 THEN CONCAT( SUBSTRING(t3.D_DATETIME,1,7),'-01') WHEN t3.V04003 BETWEEN 6 AND 10 THEN CONCAT( SUBSTRING(t3.D_DATETIME,1,7),'-02') WHEN t3.V04003 BETWEEN 11 AND 15 THEN CONCAT( SUBSTRING(t3.D_DATETIME,1,7),'-03') WHEN t3.V04003 BETWEEN 16 AND 20 THEN CONCAT( SUBSTRING(t3.D_DATETIME,1,7),'-04') WHEN t3.V04003 BETWEEN 21 AND 25 THEN CONCAT( SUBSTRING(t3.D_DATETIME,1,7),'-05') WHEN t3.V04003 > 25 THEN CONCAT( SUBSTRING(t3.D_DATETIME,1,7),'-06') END want_time"
        if timeType == "ten":
            wantTimeStr = "CASE WHEN t3.V04003 BETWEEN 1 AND 10 THEN CONCAT( SUBSTRING(t3.D_DATETIME,1,7),'-01') WHEN t3.V04003 BETWEEN 11 AND 20 THEN CONCAT( SUBSTRING(t3.D_DATETIME,1,7),'-02') WHEN t3.V04003 > 20 THEN CONCAT( SUBSTRING(t3.D_DATETIME,1,7),'-03') END want_time"
        if timeType == "mon":
            wantTimeStr = "SUBSTRING(t3.D_DATETIME, 1, 7) want_time"
        if timeType == "season":
            wantTimeStr = "CASE WHEN t3.V04002 BETWEEN 3 AND 5 THEN CONCAT(t3.V04001, '-01') WHEN t3.V04002 BETWEEN 6 AND 8 THEN CONCAT(t3.V04001, '-02') WHEN t3.V04002 BETWEEN 9 AND 11 THEN CONCAT(t3.V04001, '-03') WHEN t3.V04002 BETWEEN 1 AND 2 THEN CONCAT(t3.V04001, '-04') WHEN t3.V04002 = 12 THEN CONCAT(t3.V04001 + 1, '-04') END want_time"
        if timeType == "year":
            wantTimeStr = "t3.V04001 want_time"
        # 查询的表名
        tableName = self.gbase_element_config.get(key).get("tableName")
        # 区域站点设置
        if stationStr:
            staConditionStr = "t3.V01301 in ('%s')" % stationStr.replace(",", "', '")
        else:
            if areaCode == "CH":
                staConditionStr = "t1.D_PARENTCODE = '%s'" % areaCode
            else:
                staConditionStr = "t1.D_AREACODE = '%s'" % areaCode
        # 将其它尺度类型的日期转换成日
        # 日、候、旬 转换成日
        if timeType in ["day", "five", "ten"]:
            if timeType != "day":
                tempStartTime = DateUtils.dateToStr(DateUtils.strToDate(DateUtils.otherTime2Day(startTime, timeType)[0], "%Y%m%d"), "%Y-%m-%d")
                tempEndTime = DateUtils.dateToStr(DateUtils.strToDate(DateUtils.otherTime2Day(endTime, timeType)[-1], "%Y%m%d"), "%Y-%m-%d")
            else:
                tempStartTime = DateUtils.dateToStr(DateUtils.strToDate(startTime, "%Y%m%d"), "%Y-%m-%d")
                tempEndTime = DateUtils.dateToStr(DateUtils.strToDate(endTime, "%Y%m%d"), "%Y-%m-%d")
        #  月、季、年 转换成月
        if timeType in ["mon", "season", "year"]:
            if timeType != "mon":
                tempStartTime = DateUtils.dateToStr(DateUtils.strToDate(DateUtils.otherTime2Month(startTime, timeType)[0], "%Y%m"), "%Y-%m")
                tempEndTime = DateUtils.dateToStr(DateUtils.strToDate(DateUtils.otherTime2Month(endTime, timeType)[-1], "%Y%m"), "%Y-%m")
            else:
                tempStartTime = DateUtils.dateToStr(DateUtils.strToDate(startTime, "%Y%m"), "%Y-%m")
                tempEndTime = DateUtils.dateToStr(DateUtils.strToDate(endTime, "%Y%m"), "%Y-%m")
            tempStartTime = tempStartTime+"-01"
            tempEndTime = tempEndTime+"-01"
        # 按区域查询实况数据的sql模板
        sql_tmplate = "SELECT a.stationId, a.want_time D_DATETIME, %s(a.val) val FROM ( SELECT t3.V01301 stationId, t3.D_DATETIME, %s val,%s FROM CIPAS_STATION_INFO t4,CIPAS_AREA_INFO t1, CIPAS_AREA_STATION t2, %s t3 WHERE t1.D_AREACODE = t2.D_AREACODE AND t2.stationId = t3.V01301 AND t2.stationId = t4.stationId AND t4.stationType = 0 AND %s AND t3.D_DATETIME BETWEEN '%s' AND '%s' ) a WHERE a.val < 99999 GROUP BY a.want_time, a.stationId"
        # 按站点查询实况数据的sql模板
        if stationStr:
            sql_tmplate = "SELECT a.stationId, a.want_time D_DATETIME, %s(a.val) val FROM ( SELECT t3.V01301 stationId, t3.D_DATETIME, %s val,%s FROM %s t3 WHERE 1=1 AND %s AND t3.D_DATETIME BETWEEN '%s' AND '%s' ) a WHERE a.val < 99999 GROUP BY a.want_time, a.stationId"
        # 针对降水 特殊处理
        if tableField == "V13305":
            tableField_s = "(case when t3.V13305=999990 then 0.1 when t3.V13305 like '9998%' then 0 when t3.V13305 like '9996%' then t3.V13305-999600 when t3.V13305 like '9997%' then t3.V13305-999700 else t3.V13305 end)"
        else:
            tableField_s = "t3."+tableField
        # 替换sql模板里的占位符(统计方法,表字段,各尺度的时间分组，表名，区域站点)，生成完整的SQL语句
        sql_str = sql_tmplate % (statisticType, tableField_s, wantTimeStr, tableName, staConditionStr, tempStartTime, tempEndTime)
        logging.info("从Gbase库查询实况的数据SQL==> "+sql_str)
        # 执行sql查询数据
        s1 = DateUtils.getTimeStamp()
        sql_result = self.mydb.executeSql(sql_str)
        if len(sql_result)==0:
            error_str = "当前SQL==>[%s]未查询到数据！"%sql_str
            raise AlgorithmException(response_code=DB_DATA_NOT_FOUND_ERROR_CODE, response_msg=error_str)
        s2 = DateUtils.getTimeStamp()
        logging.info("          %s 耗时: %s ms" % ("从Gbase库查询实况的数据", str(s2 - s1)))

        # 解析查询的结果数据封装成二维数组
        sql_data = pd.DataFrame(list(sql_result))
        sqlData = np.array(sql_data)
        locs = ['station', 'time', 'val']
        sql_time_list = sqlData[:, 1]
        sqlData = xr.DataArray(sqlData, coords=[sql_time_list, locs], dims=['sql_time', 'space'])
        res_data1 = []
        nan_data = xr.DataArray(np.full((1, len(sta_list)), np.nan, dtype=np.float32), coords=[["999"], sta_list],
                                dims=['time', 'station'])
        res_data1.append(nan_data)
        for ii, tt in enumerate(time_list):
            tmpTime = DateUtils.time_format_en(tt, timeType, "-")
            if tmpTime in sql_time_list:
                # print(tmpTime)
                data_t = sqlData.sel(sql_time=tmpTime)
                if len(data_t.shape) == 1:
                    sta_t = list(map(int,[data_t.sel(space='station').values.tolist()]))
                    val_t = list(map(float, [data_t.sel(space='val').values.tolist()]))
                    tmpdata = xr.DataArray(val_t, coords=[sta_t], dims=['station'])
                    # 将数组扩维
                    newdata = tmpdata.expand_dims("time")
                else:
                    sta_t = list(map(int, data_t.sel(space='station').values))
                    val_t = list(map(float, data_t.sel(space='val').values))
                    tmpdata = xr.DataArray(val_t, coords=[sta_t], dims=['station'])
                    # 将数组扩维
                    newdata = tmpdata.expand_dims("time")
            else:
                newdata = nan_data.copy()
            # 设置时间维度信息
            newdata["time"] = [tt]
            res_data1.append(newdata)
        # 将时间维合并
        res_data = xr.concat(res_data1, dim="time")
        res_data = res_data.sel(time=time_list)
        if stationStr:
            stax_list = list(map(int,stationStr.split(",")))
            res_data = res_data.sel(station= stax_list)
            res_data.attrs['lats'] = list(self.stationInfoData.sel(station= stax_list,space="lat").values)
            res_data.attrs['lons'] = list(self.stationInfoData.sel(station= stax_list,space="lon").values)
        else:
            res_data.attrs['lats'] = list(self.stationInfoData.sel(space="lat").values)
            res_data.attrs['lons'] = list(self.stationInfoData.sel(space="lon").values)
        # logging.info(res_data.shape)
        # logging.info(res_data)
        s3 = DateUtils.getTimeStamp()
        logging.info("          %s 耗时: %s ms" % ("解析SQL查询的Gbase实况结果数据", str(s3 - s2)))
        return res_data

    def query_ltm_data(self, timeType, startTime, endTime, dataSource, elements, areaCode, stationStr, statisticType, ltm):
        key = ""
        sta_list = list(map(int, self.stationInfoData.sel(space="station").values))
        time_list = DateUtils.get_time_list([startTime, endTime], timeType)
        sta_data = np.full((len(time_list), len(sta_list)), np.nan, dtype=np.float32)
        # # 统计方法

        gbaseltmCfg = self.gbase_element_config.get(dataSource.upper()+"_"+elements.upper()+"_"+timeType.upper()).get("ltmCfg")
        if gbaseltmCfg is None:
            raise AlgorithmException(response_code=CUSTOM_ERROR_CODE,
                                     response_msg='Cannot find gbase ltm config,dataSourceName is %s ,elementName is %s'
                                                  % (dataSource.upper(), elements.upper()))
        ltmKey = statisticType.upper()+"_"+ltm.upper()
        eleLtmCfg = gbaseltmCfg.get(ltmKey)
        if eleLtmCfg is None:
            raise AlgorithmException(response_code=CUSTOM_ERROR_CODE, response_msg="Cannot find gbase ltm config,dataSourceName is %s ,elementName is %s,timeType is %s ,statisticType is %s ,ltm is %s"% (dataSource.upper(), elements.upper(), timeType.upper(), statisticType.upper(), ltm.upper()))
        # 查询序号的表字段
        indexFie1d = "1"
        if eleLtmCfg.get("indexField"):
            indexFie1d = "t3." + eleLtmCfg.get("indexField")
        # 查询的要素的表字段
        tableField = eleLtmCfg.get("tableField")
        # 查询的表名
        tableName = eleLtmCfg.get("tableName")
        # 区域站点设置
        if stationStr:
            staConditionStr = "t3.V01301 in ('%s')" % stationStr.replace(",", "', '")
        else:
            if areaCode == "CH":
                staConditionStr = "t1.D_PARENTCODE = '%s'" % areaCode
            else:
                staConditionStr = "t1.D_AREACODE = '%s'" % areaCode
        indexConditionStr = ""
        # # 各尺度的常年值获取范围处理
        if timeType == "day":
            mmdd_list = ["0101", "0102", "0103", "0104", "0105", "0106", "0107", "0108", "0109", "0110", "0111",
             "0112", "0113", "0114", "0115", "0116", "0117", "0118", "0119", "0120", "0121", "0122",
             "0123", "0124", "0125", "0126", "0127", "0128", "0129", "0130", "0131",
             "0201", "0202", "0203", "0204", "0205", "0206", "0207", "0208", "0209", "0210", "0211",
             "0212", "0213", "0214", "0215", "0216", "0217", "0218", "0219", "0220", "0221", "0222",
             "0223", "0224", "0225", "0226", "0227", "0228",
             "0301", "0302", "0303", "0304", "0305", "0306", "0307", "0308", "0309", "0310", "0311",
             "0312", "0313", "0314", "0315", "0316", "0317", "0318", "0319", "0320", "0321", "0322",
             "0323", "0324", "0325", "0326", "0327", "0328", "0329", "0330", "0331",
             "0401", "0402", "0403", "0404", "0405", "0406", "0407", "0408", "0409", "0410", "0411",
             "0412", "0413", "0414", "0415", "0416", "0417", "0418", "0419", "0420", "0421", "0422",
             "0423", "0424", "0425", "0426", "0427", "0428", "0429", "0430",
             "0501", "0502", "0503", "0504", "0505", "0506", "0507", "0508", "0509", "0510", "0511",
             "0512", "0513", "0514", "0515", "0516", "0517", "0518", "0519", "0520", "0521", "0522",
             "0523", "0524", "0525", "0526", "0527", "0528", "0529", "0530", "0531",
             "0601", "0602", "0603", "0604", "0605", "0606", "0607", "0608", "0609", "0610", "0611",
             "0612", "0613", "0614", "0615", "0616", "0617", "0618", "0619", "0620", "0621", "0622",
             "0623", "0624", "0625", "0626", "0627", "0628", "0629", "0630",
             "0701", "0702", "0703", "0704", "0705", "0706", "0707", "0708", "0709", "0710", "0711",
             "0712", "0713", "0714", "0715", "0716", "0717", "0718", "0719", "0720", "0721", "0722",
             "0723", "0724", "0725", "0726", "0727", "0728", "0729", "0730", "0731",
             "0801", "0802", "0803", "0804", "0805", "0806", "0807", "0808", "0809", "0810", "0811",
             "0812", "0813", "0814", "0815", "0816", "0817", "0818", "0819", "0820", "0821", "0822",
             "0823", "0824", "0825", "0826", "0827", "0828", "0829", "0830", "0831",
             "0901", "0902", "0903", "0904", "0905", "0906", "0907", "0908", "0909", "0910", "0911",
             "0912", "0913", "0914", "0915", "0916", "0917", "0918", "0919", "0920", "0921", "0922",
             "0923", "0924", "0925", "0926", "0927", "0928", "0929", "0930",
             "1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010", "1011",
             "1012", "1013", "1014", "1015", "1016", "1017", "1018", "1019", "1020", "1021", "1022",
             "1023", "1024", "1025", "1026", "1027", "1028", "1029", "1030", "1031",
             "1101", "1102", "1103", "1104", "1105", "1106", "1107", "1108", "1109", "1110", "1111",
             "1112", "1113", "1114", "1115", "1116", "1117", "1118", "1119", "1120", "1121", "1122",
             "1123", "1124", "1125", "1126", "1127", "1128", "1129", "1130",
             "1201", "1202", "1203", "1204", "1205", "1206", "1207", "1208", "1209", "1210", "1211",
             "1212", "1213", "1214", "1215", "1216", "1217", "1218", "1219", "1220", "1221", "1222",
             "1223", "1224", "1225", "1226", "1227", "1228", "1229", "1230", "1231"]
        if timeType == "five":
            mmdd_list = ["0101", "0102", "0103", "0104", "0105", "0106", "0201", "0202", "0203", "0204", "0205", "0206",
                      "0301", "0302", "0303", "0304", "0305", "0306", "0401", "0402", "0403", "0404", "0405", "0406",
                      "0501", "0502", "0503", "0504", "0505", "0506", "0601", "0602", "0603", "0604", "0605", "0606",
                      "0701", "0702", "0703", "0704", "0705", "0706", "0801", "0802", "0803", "0804", "0805", "0806",
                      "0901", "0902", "0903", "0904", "0905", "0906", "1001", "1002", "1003", "1004", "1005", "1006",
                      "1101", "1102", "1103", "1104", "1105", "1106", "1201", "1202", "1203", "1204", "1205", "1206"]
        if timeType == "ten":
            mmdd_list = ["0101", "0102", "0103", "0201", "0202", "0203", "0301", "0302", "0303", "0401", "0402", "0403",
                       "0501", "0502", "0503", "0601", "0602", "0603", "0701", "0702", "0703", "0801", "0802", "0803",
                       "0901", "0902", "0903", "1001", "1002", "1003", "1101", "1102", "1103", "1201", "1202", "1203"]
        if timeType == "mon":
            mmdd_list = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
        if timeType == "season":
            mmdd_list = ["01", "02", "03", "04"]
        if timeType == "year":
            mmdd_list = ["01"]

        # 按区域查询实况数据的sql模板
        sql_tmplate = "SELECT t3.V01301 stationId, %s orderNumber, t3.%s val FROM CIPAS_STATION_INFO t4, CIPAS_AREA_INFO t1, CIPAS_AREA_STATION t2, %s t3 WHERE t1.D_AREACODE = t2.D_AREACODE AND t2.stationId = t3.V01301 AND t2.stationId = t4.stationId AND t4.stationType = 0  and t3.%s < 99999 AND %s %s"
        # 按站点查询实况数据的sql模板
        if stationStr:
            sql_tmplate = "SELECT t3.V01301 stationId, %s orderNumber, t3.%s val FROM %s t3 WHERE 1 = 1 AND t3.%s < 99999 AND %s %s"
        # 替换sql模板里的占位符(序号,表字段，表名，表字段，区域站点, 常年值日期条件)，生成完整的SQL语句
        sql_str = sql_tmplate % (indexFie1d, tableField, tableName, tableField, staConditionStr, indexConditionStr)
        if timeType != "year":
            startXh = mmdd_list.index(startTime[4:]) + 1
            endXh = mmdd_list.index(endTime[4:]) + 1
            if startXh > endXh:
                sql_str = sql_str + "and (" + indexFie1d + " >= " + str(startXh) + " OR " + indexFie1d + "<=" + str(
                    endXh) + ")"
            else:
                sql_str = sql_str + "and (" + indexFie1d + " between " + str(startXh) + " and " + str(endXh) + ")"
        logging.info("从Gbase库查询常年值的数据SQL==> " + sql_str)
        # 执行sql查询数据
        s1 = DateUtils.getTimeStamp()
        sql_result = self.mydb.executeSql(sql_str)
        s2 = DateUtils.getTimeStamp()
        logging.info("          %s 耗时: %s ms" % ("从Gbase库查询常年值的数据", str(s2 - s1)))

        # 解析查询的结果数据封装成二维数组
        sql_data = pd.DataFrame(list(sql_result))
        sqlData = np.array(sql_data)
        locs = ['station', 'orderNumber', 'val']
        sql_time_list = sqlData[:, 1]
        sqlData = xr.DataArray(sqlData, coords=[sql_time_list, locs], dims=['sql_time', 'space'])
        res_data1 = []
        nan_data = xr.DataArray(np.full((1, len(sta_list)), np.nan, dtype=np.float32), coords=[["999"], sta_list],
                                dims=['time', 'station'])
        res_data1.append(nan_data)
        for ii, tt in enumerate(time_list):
            if timeType != "year":
                if tt[4:] == "0229":
                    tmpTime = -1
                else:
                    tmpTime = mmdd_list.index(tt[4:]) + 1
            else:
                tmpTime = 1
            if tmpTime in sql_time_list:
                data_t = sqlData.sel(sql_time=tmpTime)
                sta_t = list(map(int, data_t.sel(space='station').values))
                val_t = list(map(float, data_t.sel(space='val').values))
                tmpdata = xr.DataArray(val_t, coords=[sta_t], dims=['station'])
                # 将数组扩维
                newdata = tmpdata.expand_dims("time")
            else:
                newdata = nan_data.copy()
            # 设置时间维度信息
            newdata["time"] = [tt]
            res_data1.append(newdata)
        s3 = DateUtils.getTimeStamp()
        logging.info("          %s 耗时: %s ms" % ("解析SQL查询的Gbase常年值的结果数据", str(s3 - s2)))
        # 将时间维合并
        res_data = xr.concat(res_data1, dim="time")
        res_data = res_data.sel(time=time_list)
        if stationStr:
            stax_list = list(map(int,stationStr.split(",")))
            res_data = res_data.sel(station= stax_list)
            res_data.attrs['lats'] = list(self.stationInfoData.sel(station= stax_list,space="lat").values)
            res_data.attrs['lons'] = list(self.stationInfoData.sel(station= stax_list,space="lon").values)
        else:
            res_data.attrs['lats'] = list(self.stationInfoData.sel(space="lat").values)
            res_data.attrs['lons'] = list(self.stationInfoData.sel(space="lon").values)
        logging.info(res_data.shape)
        return res_data


if __name__ == '__main__':

    # ax = [{"xx": "1", "aa": "2"},{"xx": "2", "aa": "4"}]
    # axm = {}
    # for a in ax:
    #     axm[a["xx"]+"_"+a["aa"]] = a
    # print(axm)
    # exit()
    sub_local_params = {
        'dataSource': 'CSOD',
        'elements': 'RAIN',
        'statisticType': 'SUM',
        'areaCode': 'CH',
        # 'stationStr': '59954,50136,59951,50137,50246,50247,59945,59948',
        'eleType': 'SK',
        'timeType': 'day',
        'ltm': '1991-2020',
        'timeRanges': [20180101, 20180103]
    }
    gid = GbaseData(sub_local_params, None)
    gid.execute()
    # print(gid.output_data)
    # with open("/nfsshare/testSH/GSOD_20220223_sta.txt", "w", encoding="utf-8") as f:
    #     f.write(",".join(list(map(str,gid.output_data[1]['outputData'][:].values))))
    # print(",".join(list(map(str,gid.output_data[0]['outputData'][0].values))))
    # gid.query_data()
    # try:
    #     gid.execute()
    #     logging.info(gid.output_data)
    # except AlgorithmException as e:
    #     logging.info(e.__str__())
