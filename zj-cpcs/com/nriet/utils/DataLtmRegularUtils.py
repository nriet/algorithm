#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/07/09
# @Author : Shiys
# @File : DataLtmRegularUtils.py


import xarray as xr
import calendar,logging
import os
import numpy as np
from com.nriet.utils import DateUtils
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import FILE_NOT_FOUND_ERROR_CODE,PARAMETER_VALUE_ERROR_CODE

class DataLtmRegularUtils:
    # 生成netCDF文件
    def writ_nc(self, res_data, resVar, out_file_path, latlonType=None):
        # 判断输出目录是否存在，不存在就创建
        str_dir = os.path.dirname(out_file_path)
        # logging.info(out_file_path)
        if not os.path.exists(str_dir):
            os.makedirs(str_dir)
        # 判断输出文件是否存在，存在则删除
        if os.path.exists(out_file_path):
            os.remove(out_file_path)
        # 生成netCDF文件
        data_set = xr.Dataset({resVar: res_data})
        # 设置netcdf的数据属性
        encoding = {resVar: {'dtype': 'float32', '_FillValue': 999999.0},
                    "time": {'dtype': 'float64'}
                    }
        if latlonType:
            # logging.info(latlonType)
            encoding["lat"] = {'dtype': latlonType}
            encoding["lon"] = {'dtype': latlonType}
        data_set.to_netcdf(out_file_path, encoding=encoding)
        res_str = "Climate file [%s] regulation completed!" % out_file_path
        logging.info(res_str)

    # 根据规整后的数据规整常年值（日尺度）
    def regular_day_ltm_data(self, dataConfig, timeType, startYear, endYear):
        logging.info("regular_day_ltm_data")
        result_data_list = []
        for year in range(startYear, endYear + 1):   #循环年份
            year_data_list = []
            for mon in range(1,13):
                mon_days = calendar.monthrange(year, mon)[1]  # 计算当前月的总天数
                mon_time_list = np.linspace(1,mon_days,mon_days)+mon*100
                # logging.info(mon_time_list)
                ym = str(year) + "_" + "{0:02d}".format(mon)
                # 获取源数据的输入位置
                dataInputPath_ym = dataConfig.get("dataInputPath").replace("#YYYY_MM#", ym)
                logging.info(dataInputPath_ym)
                if os.path.exists(dataInputPath_ym):
                    # 加载数据
                    ds = xr.open_dataset(dataInputPath_ym)
                    data = ds[dataConfig.get("var")]
                    # logging.info(data)
                    data = data[:mon_days, ...]
                    data.time.values = mon_time_list
                    # logging.info(data)
                    year_data_list.append(data)

            if len(year_data_list) > 0:
                # 将时间维合并
                year_data = xr.concat(year_data_list, dim='time')
                # 扩展年份维
                year_data = year_data.expand_dims('year')
                year_data['year'] = [year]
                result_data_list.append(year_data)

        if len(result_data_list) > 0:
            # 将年份维合并
            result_data = xr.concat(result_data_list, dim='year')
            # logging.info(result_data)
            # 对年份维求平均
            res_data = result_data.mean(dim='year',keep_attrs = True)
            # 重置常年值文件的时间维
            res_data.time.values = np.linspace(1,366,366)
            # logging.info(res_data)
            # exit()
            # 获取常年值输出位置
            dataOutputPath = dataConfig.get("dataOutputPath").replace("#LY#", str(startYear)+"-"+str(endYear))
            self.writ_nc(res_data, dataConfig.get("var"), dataOutputPath)

    # 根据规整后的数据规整常年值(除日尺度外)
    def regular_other_ltm_data(self, dataConfig, timeType, startYear, endYear):
        logging.info("regular_other_ltm_data")
        result_data_list = []
        time_type_list = ["day","pen","five", "ten", "mon", "season", "year"]
        ml_list = [366,73, 72, 36, 12, 4, 1]
        ml = ml_list[time_type_list.index(timeType)]
        time_list = np.linspace(1,ml,ml,dtype=np.float32)
        for year in range(startYear, endYear + 1):  # 循环年份
            # 获取源数据的输入位置
            dataInputPath_year = dataConfig.get("dataInputPath").replace("#YYYY#", str(year))
            if os.path.exists(dataInputPath_year):
                # 加载数据
                ds = xr.open_dataset(dataInputPath_year)
                data = ds[dataConfig.get("var")]
                data.time.values = time_list
                # 扩展年份维
                year_data = data.expand_dims('year')
                year_data['year'] = [year]
                result_data_list.append(year_data)

        if len(result_data_list) > 0:
            # 将年份维合并
            result_data = xr.concat(result_data_list, dim='year')
            # logging.info(result_data)
            # 对年份维求平均
            res_data = result_data.mean(dim='year', keep_attrs=True)
            # logging.info(res_data)
            # 获取常年值输出位置
            dataOutputPath = dataConfig.get("dataOutputPath").replace("#LY#", str(startYear) + "-" + str(endYear))
            self.writ_nc(res_data, dataConfig.get("var"), dataOutputPath)

    # 根据规整后的数据规整常年值_高分辨率(除日尺度外)
    def regular_other_ltm_data_hd(self, dataConfig, timeType, startYear, endYear):
        logging.info("regular_other_ltm_data_hd")
        result_data_list = []
        time_type_list = ["pen", "five", "ten", "mon", "season", "year"]
        ml_list = [73, 72, 36, 12, 4, 1]
        ml = ml_list[time_type_list.index(timeType)]
        dataInputPath_1991 = dataConfig.get("dataInputPath").replace("#YYYY#", "1991")
        ds1 = xr.open_dataset(dataInputPath_1991)
        lat_value = ds1["lat"].values
        for m in range(1, ml + 1):
            mdata_list = []
            for year in range(startYear, endYear + 1):  # 循环年份
                # 获取源数据的输入位置
                dataInputPath_year = dataConfig.get("dataInputPath").replace("#YYYY#", str(year))
                if os.path.exists(dataInputPath_year):
                    # 加载数据
                    ds = xr.open_dataset(dataInputPath_year)
                    data = ds[dataConfig.get("var")]
                    data = data[m - 1:m, ...]
                    data.time.values = [m]
                    data.lat.values = lat_value
                    # logging.info(data)

                    # 扩展年份维
                    year_data = data.expand_dims('year')
                    year_data['year'] = [year]
                    mdata_list.append(year_data)
            if len(mdata_list) > 0:
                # 将年份维合并
                res_mdata = xr.concat(mdata_list, dim='year')
                # 对年份维求平均
                res_mdata = res_mdata.mean(dim='year', keep_attrs=True)
                result_data_list.append(res_mdata)

        if len(result_data_list) > 0:
            # 将时间维合并
            res_data = xr.concat(result_data_list, dim='time')
            # logging.info(res_data)
        # 获取常年值输出位置
        dataOutputPath = dataConfig.get("dataOutputPath").replace("#LY#", str(startYear) + "-" + str(endYear))
        self.writ_nc(res_data, dataConfig.get("var"), dataOutputPath)

    # 根据规整后的数据规整常年值_高分辨率(日尺度)
    def regular_day_ltm_data_hd(self, dataConfig, timeType, startYear, endYear):
        logging.info("regular_day_ltm_data_hd")
        result_data_list = []
        time_list = ["0101", "0102", "0103", "0104", "0105", "0106", "0107", "0108", "0109", "0110", "0111",
                      "0112", "0113", "0114", "0115", "0116", "0117", "0118", "0119", "0120", "0121", "0122",
                      "0123", "0124", "0125", "0126", "0127", "0128", "0129", "0130", "0131",
                      "0201", "0202", "0203", "0204", "0205", "0206", "0207", "0208", "0209", "0210", "0211",
                      "0212", "0213", "0214", "0215", "0216", "0217", "0218", "0219", "0220", "0221", "0222",
                      "0223", "0224", "0225", "0226", "0227", "0228", "0229",
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

        for index,md in enumerate(time_list):
            mm = md[0:2]
            dd = int(md[2:])
            mdata_list = []
            for year in range(startYear, endYear + 1):  # 循环年份
                # 平年无2月29号 特殊处理
                if md == '0209' and not calendar.isleap(year):
                    continue
                # 获取源数据的输入位置
                dataInputPath_ym = dataConfig.get("dataInputPath").replace("#YYYY_MM#", str(year)+"_"+mm)
                if os.path.exists(dataInputPath_ym):
                    # 加载数据
                    ds = xr.open_dataset(dataInputPath_ym)
                    data = ds[dataConfig.get("var")]
                    data  = data[dd-1:dd, ...]
                    # 扩展年份维
                    year_data = data.expand_dims('year')
                    year_data['year'] = [year]
                    mdata_list.append(year_data)
            if len(mdata_list) > 0:
                # 将年份维合并
                res_mdata = xr.concat(mdata_list, dim='year')
                # 对年份维求平均
                res_mdata = res_mdata.mean(dim='year', keep_attrs=True)
                res_mdata.time.values = [index+1]
                result_data_list.append(res_mdata)

        if len(result_data_list) > 0:
            # 将时间维合并
            res_data = xr.concat(result_data_list, dim='time')
            # logging.info(res_data)
        # 获取常年值输出位置
        dataOutputPath = dataConfig.get("dataOutputPath").replace("#LY#",str(startYear) + "-" + str(endYear))
        self.writ_nc(res_data, dataConfig.get("var"), dataOutputPath)

    # 根据逐月的常年值数据规整BCC-CSM1.3m模式的常年值数据
    def regular_bcccsm13m_ltm_data(self, dataConfig, timeType, startYear, endYear):
        logging.info("regular_bcccsm13m_ltm_data")
        result_data_list = []
        ltm_time = None
        for m in range(1, 13):
            # 获取源数据的输入位置
            dataInputPath_mm = dataConfig.get("dataInputPath").replace("#MM#", "{0:02d}".format(m))
            if os.path.exists(dataInputPath_mm):
                ds = xr.open_dataset(dataInputPath_mm)
                # 重置变量名和维的名称
                if dataConfig.get("original"):
                    if dataConfig.get("original").get("var"):
                        org_var_list = dataConfig.get("original").get("var").split(",")
                        for org_var in org_var_list:
                            if org_var in ds.data_vars:
                                ds = ds.rename({org_var: dataConfig.get("var")})
                    if dataConfig.get("original").get("lat") and dataConfig.get("original").get("lat") in ds.dims:
                        ds = ds.rename({dataConfig.get("original").get("lat"): "lat"})
                    if dataConfig.get("original").get("lon") and dataConfig.get("original").get("lon") in ds.dims:
                        ds = ds.rename({dataConfig.get("original").get("lon"): "lon"})

                ds = ds.rename({"time": "forcast_time"})
                if ltm_time is None:
                    ltm_time = ds["forcast_time"]
                result_data = ds[dataConfig.get("var")]
                if dataConfig.get("level"):
                    result_data = result_data.sel(level=float(dataConfig.get("level")))
                logging.info("原始数据的大小范围在%s~%s..." % (result_data.min().values, result_data.max().values))
                if dataConfig.get("unitConvert"):
                    result_data.attrs['unit'] = dataConfig.get("unitConvert").get("unitName")
                    unitConverts = dataConfig.get("unitConvert").get("unitProc").split("-")
                    convert_type, convert_value = unitConverts[0].split("_")
                    logging.info("%s开始单位转换...转换公式为%s" % (dataConfig.get("var"), unitConverts))
                    data_allx = convert_data(result_data, convert_type, convert_value)
                    if len(unitConverts) == 2:
                        if unitConverts[1] == "mon":
                            fore_time_list = data_allx.forcast_time.values
                            for k, foreTime in enumerate(fore_time_list):
                                logging.info(foreTime)
                                year, mon = int(str(foreTime)[0:4]), int(str(foreTime)[5:7])
                                mon_days = calendar.monthrange(year, mon)[1]
                                logging.info(mon_days)
                                data_allx[k] = data_allx[k] * mon_days
                    data_allx.attrs = result_data.attrs
                    result_data = data_allx
                    logging.info("转换后的数据大小范围在%s~%s..." % (result_data.min().values, result_data.max().values))
                result_data["forcast_time"] = ltm_time
                #扩展起报时间维
                res_mdata = result_data.expand_dims('time')
                res_mdata['time'] = [m]
                result_data_list.append(res_mdata)

        if len(result_data_list) > 0:
            # 将时间维合并
            res_data = xr.concat(result_data_list, dim='time')
            # logging.info(res_data)
        # 获取常年值输出位置
        dataOutputPath = dataConfig.get("dataOutputPath").replace("#LY#", str(startYear) + "-" + str(endYear))
        self.writ_nc(res_data, dataConfig.get("var"), dataOutputPath,"float32")



# keys = ["11", "33", "44"]
# logging.info(keys)
# keys.insert(1,"22s")
# logging.info(".".join(keys).upper())
# DLRU = DataLtmRegularUtils()
# data_config={}
# data_config["dataInputPath"] = "/nfsshare/cdbdata/data/NCEPRA/surface/slp/day/#YYYY_MM#.nc"
# data_config["var"] = "slp"
# data_config["dataOutputPath"]="/nfsshare/cdbdata/data/NCEPRA/surface/slp/ltm/day_#LY#.nc"
# # data_config[""]=""
# timeType="day"
# start_year = 1991
# end_year = 2020
# DLRU.regular_day_ltm_data_hd(data_config,timeType,start_year,end_year)