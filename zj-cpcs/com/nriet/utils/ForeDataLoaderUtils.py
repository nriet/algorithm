#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/07/09
# @Author : Shiys
# @File : ForeDataLoaderUtils.py


import xarray as xr

import os,logging

from com.nriet.utils import DateUtils

class ForeDataLoaderUtils:
    # 解国家气候中心二代模式BCC_CSM1.1m 含高度层
    def parse_bcccsm11_pres_data(self, dataConfig, forecastTime):
        logging.info("parse_bcccsm11_pres_data")
        # 计算模式预报长度
        foreStartTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), dataConfig.get("startPeriod"))
        foreEndTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"), dataConfig.get("endPeriod"))
        fore_time_list = list(map(int, DateUtils.get_time_list([foreStartTime, foreEndTime], "mon")))

        result_data = []
        # 获取源数据的输入位置
        dataInputPath = dataConfig.get("dataInputPath")
        level_list = dataConfig.get("levels").split(",")
        y_m = str(forecastTime)[0:4]+"_"+str(forecastTime)[4:6]
        for level in level_list:
            dataInputFile = dataInputPath.replace("#H#", level).replace("#YYYY_MM#",y_m)
            if not os.path.isfile(dataInputFile):
                continue
            # 加载数据
            ds = xr.open_dataset(dataInputFile, decode_times=False)
            ds = ds.rename({"time": "validTime"})
            # logging.info(ds)
            data_all = ds[dataConfig.get("var")]
            # 将数组扩维，并设置维度信息
            dim = 'level'
            data = data_all.expand_dims(dim,1)
            data['level'] = [float(level)]
            result_data.append(data)
        # result_data长度为0时，返回None
        if len(result_data) == 0:
            return None
        new_data = xr.concat(result_data, dim="level")
        dim = 'time'
        var_data = new_data.expand_dims(dim)
        var_data['time'] = [int(forecastTime)]
        var_data['validTime'] = fore_time_list
        return var_data

    # 解国家气候中心二代模式BCC_CSM1.1m 地面资料
    def parse_bcccsm11_surf_data(self, dataConfig, forecastTime):
        logging.info("parse_bcccsm11_surf_data")
        # 计算模式预报长度
        foreStartTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"),
                                                      dataConfig.get("startPeriod"))
        foreEndTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"),
                                                    dataConfig.get("endPeriod"))
        fore_time_list = list(map(int, DateUtils.get_time_list([foreStartTime, foreEndTime], "mon")))
        # 获取源数据的输入位置
        dataInputPath = dataConfig.get("dataInputPath")
        y_m = str(forecastTime)[0:4] + "_" + str(forecastTime)[4:6]
        dataInputFile = dataInputPath.replace("#YYYY_MM#", y_m)
        # 文件不存，返回None
        if not os.path.isfile(dataInputFile):
            return None
        # 加载数据
        ds = xr.open_dataset(dataInputFile, decode_times=False)
        ds = ds.rename({"time": "validTime"})
        data_all = ds[dataConfig.get("var")]
        # 将数组扩维，并设置维度信息
        dim = 'time'
        var_data = data_all.expand_dims(dim)
        var_data['time'] = [int(forecastTime)]
        var_data['validTime'] = fore_time_list
        return var_data

    # 国家气候中心二代模式BCC_CSM1.2
    def parse_bcccsm12_data(self, dataConfig, forecastTime):
        logging.info("parse_bcccsm12_data")
        # 计算模式预报长度
        foreStartTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"),
                                                      dataConfig.get("startPeriod"))
        foreEndTime = DateUtils.time_increase(DateUtils.strToDate(forecastTime, "%Y%m%d"),
                                                    dataConfig.get("endPeriod"))
        # exit()
        fore_time_list = list(map(int, DateUtils.get_time_list([foreStartTime, foreEndTime], "day")))
        logging.info(fore_time_list)
        # 获取源数据的输入位置
        dataInputPath = dataConfig.get("dataInputPath")
        foreYear = str(forecastTime)[0:4]
        foreMon = str(forecastTime)[4:6]
        dataInput_ymd = dataInputPath.replace("#YYYY#", foreYear).replace("#MM#", foreMon).replace("#YYYYMMDD#", forecastTime)
        member_list = dataConfig.get("member").split(",")
        result_data = []
        for m in member_list:
            dataInput_m = dataInput_ymd.replace("#N#",m)
            if not os.path.isfile(dataInput_m):
                continue
            # 加载数据
            ds = xr.open_dataset(dataInput_m, decode_times=False)
            ds = ds.rename({"time": "validTime"})
            data_all = ds[dataConfig.get("var")]
            # 将数组扩维，并设置维度信息
            dim = 'ensNo'
            data = data_all.expand_dims(dim)
            data['ensNo'] = [float(m)]
            result_data.append(data)

        # result_data长度为0时，返回None
        if len(result_data) == 0:
            return None
        # 将数组扩维，并设置维度信息
        new_data = xr.concat(result_data, dim="ensNo")
        dim = 'time'
        var_data = new_data.expand_dims(dim)
        var_data['time'] = [int(forecastTime)]
        var_data['validTime'] = fore_time_list
        return var_data

    # 国家气候中心二代模式BCC_CSM1.1m (MODES集合平均)
    # 美国气象环境预报中心NCEP_CFS2(MODES集合平均)
    def parse_bcccsm11_modes_em_data(self, dataConfig, forecastTime):
        logging.info("parse_bcccsm11_modes_em_data")
        # 计算模式预报长度
        foreStartTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"),
                                                      dataConfig.get("startPeriod"))
        foreEndTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"),
                                                    dataConfig.get("endPeriod"))
        fore_time_list = list(map(int, DateUtils.get_time_list([foreStartTime, foreEndTime], "mon")))
        # 获取源数据的输入位置
        dataInputPath = dataConfig.get("dataInputPath")
        # y_m = str(forecastTime)[0:4] + "_" + str(forecastTime)[4:6]
        dataInputFile = dataInputPath.replace("#YYYYMM#", forecastTime).replace("#FYYYYMM#", foreStartTime)
        # 文件不存，返回None
        if not os.path.isfile(dataInputFile):
            return None
        # 加载数据
        ds = xr.open_dataset(dataInputFile, decode_times=False)
        # 要解析的要素不存在时，返回 None
        if dataConfig.get("var") not in list(ds.data_vars.keys()):
            return None
        ds = ds.rename({"time": "validTime"})
        data_all = ds[dataConfig.get("var")]
        # 将数组扩维，并设置维度信息
        dim = 'time'
        var_data = data_all.expand_dims(dim)
        var_data['time'] = [int(forecastTime)]
        var_data['validTime'] = fore_time_list
        return var_data

    # 美国气象环境预报中心NCEP_CFS2(MODES多样本)
    def parse_ncep_cfs2_modes_mb_data(self, dataConfig, forecastTime):
        logging.info("parse_ncep_cfs2_modes_mb_data")
        foreYM = forecastTime[0:6]
        # 计算模式预报长度
        foreStartTime = DateUtils.time_increase_month(DateUtils.strToDate(foreYM, "%Y%m"),
                                                      dataConfig.get("startPeriod"))
        foreEndTime = DateUtils.time_increase_month(DateUtils.strToDate(foreYM, "%Y%m"),
                                                    dataConfig.get("endPeriod"))
        fore_time_list = list(map(int, DateUtils.get_time_list([foreStartTime, foreEndTime], "mon")))
        # 获取源数据的输入位置
        dataInputPath = dataConfig.get("dataInputPath")
        # y_m = str(forecastTime)[0:4] + "_" + str(forecastTime)[4:6]
        dataInputPath_ymd = dataInputPath.replace("#YYYYMMDD#", forecastTime).replace("#FYYYYMM#", foreYM)
        hours = ["00","06","12","18"]
        members = ["01","02","03","04"]
        result_data = []
        for h in hours:
            result_data_member = []
            dataInputPath_h = dataInputPath_ymd.replace("#HH#",h)
            for m in members:
                dataInputFile = dataInputPath_h.replace("#N#",m)
                if not os.path.isfile(dataInputFile):
                    continue
                # 加载数据
                ds = xr.open_dataset(dataInputFile, decode_times=False)
                # 要解析的要素不存在时，跳过当前文件
                if dataConfig.get("var") not in list(ds.data_vars.keys()):
                    continue
                ds = ds.rename({"time": "validTime"})
                data_all = ds[dataConfig.get("var")]
                # 将数组扩维，并设置维度信息
                dim = 'ensNo'
                var_data = data_all.expand_dims(dim)
                var_data['ensNo'] = [float(m)]
                result_data_member.append(var_data)
            if len(result_data_member)==0:
                continue
            member_data = xr.concat(result_data_member, dim='ensNo')
            # 将数组扩维，并设置维度信息
            dim = 'time'
            xdata = member_data.expand_dims(dim)
            xdata['time'] = [int(forecastTime+h)]
            result_data.append(xdata)

        # result_data长度为0时，返回None
        if len(result_data) == 0:
            return None
        var_data = xr.concat(result_data,dim='time')
        var_data['validTime'] = fore_time_list
        return  var_data

    # 国家气候中心二代模式BCC_CSM1.1m (MODES 多样本)
    def parse_bcccsm11_modes_mb_data(self, dataConfig, forecastTime):
        logging.info("parse_bcccsm11_modes_mb_data")
        # 计算模式预报长度
        foreStartTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"),
                                                      dataConfig.get("startPeriod"))
        foreEndTime = DateUtils.time_increase_month(DateUtils.strToDate(forecastTime, "%Y%m"),
                                                    dataConfig.get("endPeriod"))
        fore_time_list = list(map(int, DateUtils.get_time_list([foreStartTime, foreEndTime], "mon")))
        # 获取源数据的输入位置
        dataInputPath = dataConfig.get("dataInputPath")
        # y_m = str(forecastTime)[0:4] + "_" + str(forecastTime)[4:6]
        dataInputFile = dataInputPath.replace("#YYYYMM#", forecastTime).replace("#FYYYYMM#", foreStartTime)
        # 文件不存，返回None
        if not os.path.isfile(dataInputFile):
            return None
        # 加载数据
        ds = xr.open_dataset(dataInputFile, decode_times=False)
        ds = ds.rename({"time": "validTime","lev": "ensNo"})
        data_all = ds[dataConfig.get("var")]
        data_all = data_all.transpose("ensNo", ...)
        # 将数组扩维，并设置维度信息
        dim = 'time'
        var_data = data_all.expand_dims(dim)
        var_data['time'] = [int(forecastTime)]
        var_data['validTime'] = fore_time_list
        return var_data

    # BCC_S2S
    def parse_bcc_s2s_data(self, dataConfig, forecastTime):
        logging.info("parse_bcc_s2s_data")

        # 获取源数据的输入位置
        dataInputPath = dataConfig.get("dataInputPath")
        dataInput_ymd = dataInputPath.replace("#YYYY#", str(forecastTime)[0:4]).replace("#MM#", str(forecastTime)[4:6]).replace("#YYYYMMDD#", forecastTime)
        member_list = dataConfig.get("member").split(",")
        result_data = []
        for m in member_list:
            dataInput_m = dataInput_ymd.replace("#N#", m)
            if not os.path.isfile(dataInput_m):
                continue
            # 加载数据
            ds = xr.open_dataset(dataInput_m)
            if 'foreStartTime' not in locals().keys() or 'foreEndTime' not in locals().keys():
                tt = ds['time']
                foreStartTime = str(tt[0].values)[0:10].replace("-","")
                foreEndTime = str(tt[-1].values)[0:10].replace("-","")
            ds = ds.rename({"time": "validTime"})
            data_all = ds[dataConfig.get("var")]
            # 将数组扩维，并设置维度信息
            dim = 'ensNo'
            data = data_all.expand_dims(dim)
            data['ensNo'] = [float(m)]
            result_data.append(data)

        if len(result_data) == 0:
            return  None
        # 按样本维合并
        new_data = xr.concat(result_data, dim="ensNo")
        dim = 'time'
        var_data = new_data.expand_dims(dim)
        var_data['time'] = [int(forecastTime)]
        # 计算模式预报长度
        fore_time_list = list(map(int, DateUtils.get_time_list([foreStartTime, foreEndTime], "day")))
        var_data['validTime'] = fore_time_list
        return var_data
