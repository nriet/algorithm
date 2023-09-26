#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020-02-21
# @Author : chenmeng
# @File : DataScaleConversion.py
import xarray as xr
from com.nriet.algorithm.business.BusComponent import BusComponent
from com.nriet.utils import DateUtils
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config import ResponseCodeAndMsgEum as RCME


# 数据单位转换
class DataScaleConversion(BusComponent):
    def __init__(self, sub_local_params, algorithm_iuput_data):
        self.flow_data = algorithm_iuput_data
        # 待转换的数据
        if isinstance(self.flow_data[0]["outputData"], list):
            self.inputData = self.flow_data[0]["outputData"][0]
        else:
            self.inputData = self.flow_data[0]["outputData"]
        # 待转换数据的尺度类型
        self.timeType = sub_local_params.get("timeType")
        # 需要转换成的尺度类型
        self.convertTimeType = sub_local_params.get("convertTimeType")
        self.output_data = None

    def execute(self):
        flow_data = {}
        if self.timeType == self.convertTimeType:
            flow_data["outputData"] = self.inputData
        else:
            # 日尺度转换到国际候
            if self.timeType == "day" and self.convertTimeType == "fiveYear":
                convert_data = self.day2FiveYear()

            # 日尺度转换到中国候
            if self.timeType == "day" and self.convertTimeType == "five":
                convert_data = self.day2Five()

            # 月尺度转换到季
            if self.timeType == "mon" and self.convertTimeType == "season":
                convert_data = self.month2Season()

            # 月尺度转换到年
            if self.timeType == "mon" and self.convertTimeType == "year":
                convert_data = self.month2Year()

            flow_data["outputData"] = convert_data
        self.output_data = flow_data

    # 日转国际候
    def day2FiveYear(self):
        # 获取国际候的每一候开始日期数组
        five73_start_md = "0101,0106,0111,0116,0121,0126,0131,0205,0210,0215,0220,0225,0302,0307,0312,0317,0322,0327,0401,0406,0411,0416,0421,0426,0501,0506,0511,0516,0521,0526,0531,0605,0610,0615,0620,0625,0630,0705,0710,0715,0720,0725,0730,0804,0809,0814,0819,0824,0829,0903,0908,0913,0918,0923,0928,1003,1008,1013,1018,1023,1028,1102,1107,1112,1117,1122,1127,1202,1207,1212,1217,1222,1227"
        fiv73_start_list = five73_start_md.split(",")
        # 获取国际候的每一候结束日期数组
        five73_end_md = "0105,0110,0115,0120,0125,0130,0204,0209,0214,0219,0224,0301,0306,0311,0316,0321,0326,0331,0405,0410,0415,0420,0425,0430,0505,0510,0515,0520,0525,0530,0604,0609,0614,0619,0624,0629,0704,0709,0714,0719,0724,0729,0803,0808,0813,0818,0823,0828,0902,0907,0912,0917,0922,0927,1002,1007,1012,1017,1022,1027,1101,1106,1111,1116,1121,1126,1201,1206,1211,1216,1221,1226,1231"
        fiv73_end_list = five73_end_md.split(",")
        times_list = list(self.inputData.time.values)
        # 根据数据的日期list计算国际候的开始候
        startFive = ""
        for i, tt in enumerate(times_list):
            if tt[4:] in fiv73_start_list:
                startFive = tt[:4] + str(fiv73_start_list.index(tt[4:]) + 1)
                break
        # 根据据数据的日期list计算国际候的结束候
        endFive = ""
        for i, tt in enumerate(times_list[::-1]):
            if tt[4:] in fiv73_end_list:
                endFive = tt[:4] + str(fiv73_end_list.index(tt[4:]) + 1)
                break
        # 处理异常（未找到转置后的开始国际候 或者 未找到转置后的结束国际候）
        if startFive == "" or endFive == "":
            error_str = "day convert to fiveYear fail!"
            raise AlgorithmException(response_code=RCME.DATA_OUT_OF_SCALE_CODE, response_msg=error_str)
        # 获取转置后的时间数组
        want_fiveYear_list = DateUtils.get_time_list([startFive, endFive], self.convertTimeType)
        data_fiveYear_list = []
        for i, ff in enumerate(want_fiveYear_list):
            t_index = int(ff[4:]) - 1
            tmp_start_day = ff[:4] + fiv73_start_list[t_index]
            tmp_end_day = ff[:4] + fiv73_end_list[t_index]
            tmp_day_list = DateUtils.get_time_list([tmp_start_day, tmp_end_day], self.timeType)
            data_5d = self.inputData.sel(time=tmp_day_list)
            single_data = data_5d.mean(dim="time")
            single_data = single_data.expand_dims('time')
            single_data['time'] = [ff]
            data_fiveYear_list.append(single_data)
        fiveYearData = xr.concat(data_fiveYear_list, dim="time")
        return fiveYearData

    # 日尺度转换到中国候
    def day2Five(self):
        times_list = list(self.inputData.time.values)
        # 根据数据的日期list计算开始候
        startFive = ""
        for i, tt in enumerate(times_list):
            if tt[6:] in ["01", "06", "11", "16", "21", "26"]:
                startFive = DateUtils.day2OtherTime(tt, self.convertTimeType)
                break
        # 根据据数据的日期list计算结束候
        endFive = ""
        for i, tt in enumerate(times_list[::-1]):
            tmdYear, tmdMon, tmdDay = int(tt[0:4]), tt[4:6], tt[6:]
            # 结束日是 "05", "10", "15", "20", "25", "31" 必定是候的结束日
            if tmdDay in ["05", "10", "15", "20", "25", "31"]:
                endFive = DateUtils.day2OtherTime(tt, self.convertTimeType)
                break
            # 结束日是 "30" 且月份是 "04", "06", "09", "11"  必定是候的结束日
            elif tmdDay == "30" and tmdMon in ["04", "06", "09", "11"]:
                endFive = DateUtils.day2OtherTime(tt, self.convertTimeType)
                break
            # 结束日是 "29" 且月份是 "02"  必定是候的结束日
            elif tmdDay == "29" and tmdMon == "02":
                endFive = DateUtils.day2OtherTime(tt, self.convertTimeType)
                break
            # 结束日是 "28" 且月份是 "02" 且是年是平年 必定是候的结束日
            elif tmdDay == "28" and tmdMon == "02":
                if not ((tmdYear % 4 == 0 and tmdYear % 400 == 0) or (tmdYear % 4 == 0 and tmdYear % 100 != 0)):
                    endFive = DateUtils.day2OtherTime(tt, self.convertTimeType)
                    break

        # 处理异常（未找到转置后的开始候 或者 未找到转置后的结束候）
        if startFive == "" or endFive == "":
            error_str = "day convert to fiveYear fail!"
            raise AlgorithmException(response_code=RCME.DATA_OUT_OF_SCALE_CODE, response_msg=error_str)
        # 获取转置后的时间数组
        want_five_list = DateUtils.get_time_list([startFive, endFive], self.convertTimeType)
        data_five_list = []
        for i, ff in enumerate(want_five_list):
            cday_list = DateUtils.otherTime2Day(ff, self.convertTimeType)
            tmp_start_day, tmp_end_day = cday_list[0], cday_list[1]
            tmp_day_list = DateUtils.get_time_list([tmp_start_day, tmp_end_day], self.timeType)
            data_5d = self.inputData.sel(time=tmp_day_list)
            single_data = data_5d.mean(dim="time")
            single_data = single_data.expand_dims('time')
            single_data['time'] = [ff]
            data_five_list.append(single_data)
        fiveData = xr.concat(data_five_list, dim="time")
        return fiveData

    # 月尺度转换到季
    def month2Season(self):
        times_list = list(self.inputData.time.values)
        # 根据数据的日期list计算开始候
        startSea = ""
        for i, tt in enumerate(times_list):
            if tt[4:] in ["03", "06", "09", "12"]:
                startSea = DateUtils.month2OtherTime(tt, self.convertTimeType)
                break
        # 根据据数据的日期list计算结束候
        endSea = ""
        for i, tt in enumerate(times_list[::-1]):
            if tt[4:] in ["05", "08", "11", "02"]:
                endSea = DateUtils.month2OtherTime(tt, self.convertTimeType)
                break


        # 处理异常（未找到转置后的开始季 或者 未找到转置后的结束季）
        if startSea == "" or endSea == "":
            error_str = "day convert to fiveYear fail!"
            raise AlgorithmException(response_code=RCME.DATA_OUT_OF_SCALE_CODE, response_msg=error_str)
        # 获取转置后的时间数组
        want_sea_list = DateUtils.get_time_list([startSea, endSea], self.convertTimeType)
        data_sea_list = []
        for i, sea in enumerate(want_sea_list):
            cmon_list = DateUtils.otherTime2Month(sea, self.convertTimeType)
            tmp_start_mon, tmp_end_mon = cmon_list[0], cmon_list[1]
            tmp_mon_list = DateUtils.get_time_list([tmp_start_mon, tmp_end_mon], self.timeType)
            data_mon = self.inputData.sel(time=tmp_mon_list)
            single_data = data_mon.mean(dim="time")
            single_data = single_data.expand_dims('time')
            single_data['time'] = [sea]
            data_sea_list.append(single_data)
        seasonData = xr.concat(data_sea_list, dim="time")
        return seasonData

    # 月尺度转换到年
    def month2Year(self):
        times_list = list(self.inputData.time.values)
        # 根据数据的日期list计算开始候
        startYear = ""
        for i, tt in enumerate(times_list):
            if tt[4:] == "01":
                startYear = DateUtils.month2OtherTime(tt, self.convertTimeType)
                break
        # 根据据数据的日期list计算结束候
        endYear = ""
        for i, tt in enumerate(times_list[::-1]):
            if tt[4:] == "12":
                endYear = DateUtils.month2OtherTime(tt, self.convertTimeType)
                break

        # 处理异常（未找到转置后的开始季 或者 未找到转置后的结束季）
        if startYear == "" or endYear == "":
            error_str = "day convert to fiveYear fail!"
            raise AlgorithmException(response_code=RCME.DATA_OUT_OF_SCALE_CODE, response_msg=error_str)
        # 获取转置后的时间数组
        want_year_list = DateUtils.get_time_list([startYear, endYear], self.convertTimeType)
        data_year_list = []
        for i, yy in enumerate(want_year_list):
            cmon_list = DateUtils.otherTime2Month(yy, self.convertTimeType)
            tmp_start_mon, tmp_end_mon = cmon_list[0], cmon_list[1]
            tmp_mon_list = DateUtils.get_time_list([tmp_start_mon, tmp_end_mon], self.timeType)
            data_mon = self.inputData.sel(time=tmp_mon_list)
            single_data = data_mon.mean(dim="time")
            single_data = single_data.expand_dims('time')
            single_data['time'] = [yy]
            data_year_list.append(single_data)
        yearData = xr.concat(data_year_list, dim="time")
        return yearData