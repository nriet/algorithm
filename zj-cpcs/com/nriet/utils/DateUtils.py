#!/usr/bin/env python
# -*- coding:utf-8 -*-

import datetime
import math
import calendar
import logging
# 根据formatter格式化时间，返回字符串
def dateToStr(date, formatter):
    return date.strftime(formatter)


# 根据formatter格式化时间，返回datetime
def strToDate(date, formatter):
    return datetime.datetime.strptime(date, formatter)


# 获取时间戳
def getTimeStamp():
    return int(round(datetime.datetime.now().timestamp() * 1000))


# 日期自增
def time_increase(begin_time, days):
    date = datetime.datetime.fromtimestamp(begin_time.timestamp())
    return (date + datetime.timedelta(days=days)).strftime("%Y%m%d")


def get_time_list(time_ranges, time_type, formatter=None):
    start_time = time_ranges[0]
    end_time = time_ranges[1]
    time_type = str(time_type).lower()
    time_list = []
    if time_type == "day":
        t1 = strToDate(str(start_time), "%Y%m%d")
        t2 = strToDate(str(end_time), "%Y%m%d")
        t = (t2 - t1).days
        for i in range(t + 1):
            time_list.append(time_increase(t1, i))
    elif time_type == "five":
        t1 = strToDate(str(start_time), "%Y%m%d")
        t2 = strToDate(str(end_time), "%Y%m%d")
        f_year = t2.year - t1.year
        f_start = (t1.month - 1) * 6 + t1.day
        f_end = f_year * 72 + (t2.month - 1) * 6 + t2.day

        # 获取所有年份侯日期
        for y in range(f_year + 1):
            for m in range(1, 13):
                for d in range(1, 7):
                    time_list.append(dateToStr(t1.replace(year=t1.year + y, month=m, day=d), "%Y%m%d"))
        time_list = time_list[f_start - 1:f_end]
    elif time_type == "ten":
        t1 = strToDate(str(start_time), "%Y%m%d")
        t2 = strToDate(str(end_time), "%Y%m%d")
        f_year = t2.year - t1.year
        f_start = (t1.month - 1) * 3 + t1.day
        f_end = f_year * 36 + (t2.month - 1) * 3 + t2.day

        # 获取所有年份旬日期
        for y in range(f_year + 1):
            for m in range(1, 13):
                for d in range(1, 4):
                    time_list.append(dateToStr(t1.replace(year=t1.year + y, month=m, day=d), "%Y%m%d"))
        time_list = time_list[f_start - 1:f_end]
    elif time_type == "mon":
        t1 = strToDate(str(start_time), "%Y%m")
        t2 = strToDate(str(end_time), "%Y%m")
        m_year = t2.year - t1.year

        m_start = t1.month
        m_end = m_year * 12 + t2.month

        for y in range(m_year + 1):
            for m in range(1, 13):
                time_list.append(dateToStr(t1.replace(year=t1.year + y, month=m), "%Y%m"))
        time_list = time_list[m_start - 1:m_end]
    elif time_type == "season":
        t1 = strToDate(str(start_time), "%Y%m")
        t2 = strToDate(str(end_time), "%Y%m")

        s_year = t2.year - t1.year

        if t1.month == 4:
            s_start = 1
        else:
            s_start = t1.month + 1
        if t2.month == 4:
            s_end = s_year * 4
        else:
            s_end = s_year * 4 + t2.month
        for y in range(s_year + 1):
            for s in ["04", "01", "02", "03"]:
                time_list.append(str(t1.year + y) + s)
        time_list = time_list[s_start-1:s_end+1]
    elif time_type == "year":
        for y in range(int(end_time) - int(start_time) + 1):
            time_list.append(str(int(start_time) + y))
    elif time_type == "five73" or time_type == "fiveYear" or time_type == "fiveyear":
        tmpStartYear, tmpStartF = int(str(start_time)[0:4]), int(str(start_time)[4:])
        tmpEndYear, tmpEndF = int(str(end_time)[0:4]), int(str(end_time)[4:])
        for y in range(tmpStartYear, tmpEndYear+1):
            tsf = 1
            if y == tmpStartYear:
                tsf = tmpStartF
            tef = 73
            if y == tmpEndYear:
                tef = tmpEndF
            for f in range(tsf, tef+1):
                time_list.append(str(y)+"{0:02d}".format(f))
    return time_list

def time_increase_month(date, offset):
    month = date.month
    year = date.year
    if(offset >= 0):
        for i in range(offset):
            month = month + 1
            if month == 13:
                year = year + 1
                month = 1
    else:
        for i in range(abs(offset)):
            month = month - 1
            if month == 0:
                year = year - 1
                month = 12
    return datetime.date(year, month, 1).strftime('%Y%m')

def get_time_index(want_times, timeType):
    # logging.info(want_times)
    file_days_time = ["0101", "0102", "0103", "0104", "0105", "0106", "0107", "0108", "0109", "0110", "0111",
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
    file_fives_time = ["0101", "0102", "0103", "0104", "0105", "0106", "0201", "0202", "0203", "0204", "0205", "0206",
                      "0301", "0302", "0303", "0304", "0305", "0306", "0401", "0402", "0403", "0404", "0405", "0406",
                      "0501", "0502", "0503", "0504", "0505", "0506", "0601", "0602", "0603", "0604", "0605", "0606",
                      "0701", "0702", "0703", "0704", "0705", "0706", "0801", "0802", "0803", "0804", "0805", "0806",
                      "0901", "0902", "0903", "0904", "0905", "0906", "1001", "1002", "1003", "1004", "1005", "1006",
                      "1101", "1102", "1103", "1104", "1105", "1106", "1201", "1202", "1203", "1204", "1205", "1206"]
    file_tens_time = ["0101", "0102", "0103", "0201", "0202", "0203", "0301", "0302", "0303", "0401", "0402", "0403",
                       "0501", "0502", "0503", "0601", "0602", "0603", "0701", "0702", "0703", "0801", "0802", "0803",
                       "0901", "0902", "0903", "1001", "1002", "1003", "1101", "1102", "1103", "1201", "1202", "1203"]
    file_mons_time = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    file_seasons_time = ["01", "02", "03", "04"]

    if(timeType =="year"):
        index = [0]
    else:
        if (timeType == "day"):
            file_times = file_days_time
        if (timeType == "five"):
            file_times = file_fives_time
        if (timeType == "ten"):
            file_times = file_tens_time
        if (timeType == "mon"):
            file_times = file_mons_time
        if (timeType == "season"):
            file_times = file_seasons_time
        index = []
        for w_time in want_times:
            index.append(file_times.index(w_time[4:]))
    return index

# 根据时间尺度、当前年份和开始时间获取当前年的开始时间
def get_begin_date(year, startTime, timeType):
    tmpYear = startTime[0:4]
    if (year == tmpYear):
        if (timeType != "year"):
            tStartTime = year + startTime[4:]
        else:
            tStartTime = year
    else:
        if (timeType == "day"):
            tStartTime = year + "0101"
        if (timeType == "five"):
            tStartTime = year + "0101"
        if (timeType == "ten"):
            tStartTime = year + "0101"
        if (timeType == "mon"):
            tStartTime = year + "01"
        if (timeType == "season"):
            tStartTime = year + "04"
        if (timeType == "year"):
            tStartTime = year
    return tStartTime

# 根据时间尺度、当前年份和结束时间获取当前年的结束时间
def get_end_date(year, endTime, timeType):
    tmpYear = endTime[0:4]
    if (year == tmpYear):
        if (timeType != "year"):
            tEndTime = year + endTime[4:]
        else:
            tEndTime = year
    else:
        if (timeType == "day"):
            tEndTime = year + "1231"
        if (timeType == "five"):
            tEndTime = year + "1206"
        if (timeType == "ten"):
            tEndTime = year + "1203"
        if (timeType == "mon"):
            tEndTime = year + "12"
        if (timeType == "season"):
            tEndTime = year + "03"
        if (timeType == "year"):
            tEndTime = year
    return tEndTime

# 将日转换为其它尺度的日期
def day2OtherTime(timeStr, timeType):
    res_time = timeStr
    tmpYear = timeStr[0:4]
    tmpMon = timeStr[4:6]
    tmpDay = timeStr[6:]
    if timeType == "five":
        five = math.ceil(int(tmpDay)/5)
        if tmpDay == '31':
            five = five - 1
        res_time = tmpYear + tmpMon + "0" + str(five)
    if timeType == "mon":
        res_time = tmpYear + tmpMon
    return res_time
# 将日转换为其它尺度的日期
def otherTime2Day(timeStr, timeType):
    res_time = []
    # 候
    if timeType == "five":
        tmpYear = timeStr[0:4]
        tmpMon = timeStr[4:6]
        tmpFive = timeStr[6:]
        startDay = (int(tmpFive) - 1) * 5 + 1
        if tmpFive == "06":
            endDay = calendar.monthrange(int(tmpYear), int(tmpMon))[1]
        else:
            endDay = int(tmpFive) * 5
        if startDay < 10:
            res_time.append(tmpYear + tmpMon + "0" + str(startDay))
        else:
            res_time.append(tmpYear + tmpMon + str(startDay))
        if endDay < 10:
            res_time.append(tmpYear + tmpMon + "0" + str(endDay))
        else:
            res_time.append(tmpYear + tmpMon + str(endDay))
    # 国际候
    if timeType == "fiveYear":
        # 获取国际候的每一候开始日期数组
        five73_start_md = "0101,0106,0111,0116,0121,0126,0131,0205,0210,0215,0220,0225,0302,0307,0312,0317,0322,0327,0401,0406,0411,0416,0421,0426,0501,0506,0511,0516,0521,0526,0531,0605,0610,0615,0620,0625,0630,0705,0710,0715,0720,0725,0730,0804,0809,0814,0819,0824,0829,0903,0908,0913,0918,0923,0928,1003,1008,1013,1018,1023,1028,1102,1107,1112,1117,1122,1127,1202,1207,1212,1217,1222,1227"
        fiv73_start_list = five73_start_md.split(",")
        # 获取国际候的每一候结束日期数组
        five73_end_md = "0105,0110,0115,0120,0125,0130,0204,0209,0214,0219,0224,0301,0306,0311,0316,0321,0326,0331,0405,0410,0415,0420,0425,0430,0505,0510,0515,0520,0525,0530,0604,0609,0614,0619,0624,0629,0704,0709,0714,0719,0724,0729,0803,0808,0813,0818,0823,0828,0902,0907,0912,0917,0922,0927,1002,1007,1012,1017,1022,1027,1101,1106,1111,1116,1121,1126,1201,1206,1211,1216,1221,1226,1231"
        fiv73_end_list = five73_end_md.split(",")
        tmpYear = timeStr[0:4]
        tmpGjh = int(timeStr[4:6])
        res_time.append(tmpYear+fiv73_start_list[tmpGjh-1])
        res_time.append(tmpYear+fiv73_end_list[tmpGjh-1])
    # 旬
    if timeType == "ten":
        tmpYear = timeStr[0:4]
        tmpMon = timeStr[4:6]
        tmpTen = timeStr[6:]
        startDay = (int(tmpTen) - 1) * 10 + 1
        if tmpTen == "03":
            endDay = calendar.monthrange(int(tmpYear), int(tmpMon))[1]
        else:
            endDay = int(tmpTen) * 10
        if startDay < 10:
            res_time.append(tmpYear + tmpMon + "0" + str(startDay))
        else:
            res_time.append(tmpYear + tmpMon + str(startDay))
        if endDay < 10:
            res_time.append(tmpYear + tmpMon + "0" + str(endDay))
        else:
            res_time.append(tmpYear + tmpMon + str(endDay))
    # 月
    if timeType == "mon":
        tmpYear = timeStr[0:4]
        tmpMon = timeStr[4:6]
        res_time.append(timeStr+"01")
        res_time.append(timeStr+"{0:02d}".format(calendar.monthrange(int(tmpYear), int(tmpMon))[1]))
    # 季
    if timeType == "season":
        tmpYear = timeStr[0:4]
        tmpSea = timeStr[4:6]
        if tmpSea == "04":
            res_time.append(str(int(tmpYear) - 1) + "1201")
            res_time.append(tmpYear + "02"+"{0:02d}".format(calendar.monthrange(int(tmpYear), int(2))[1]))
        else:
            res_time.append(tmpYear + "{0:02d}".format(int(tmpSea) * 3)+"01")
            res_time.append(tmpYear + "{0:02d}".format(int(tmpSea) * 3 + 2)+"{0:02d}".format(calendar.monthrange(int(tmpYear), int(tmpSea) * 3 + 2)[1]))
    # 年
    if timeType == "year":
        res_time.append(timeStr+"0101")
        res_time.append(timeStr+"1231")
    return res_time

# 将月转换为其它尺度的日期（季、年）
def month2OtherTime(timeStr, timeType):
    res_time = timeStr
    tmpYear, tmpMon= timeStr[0:4], timeStr[4:6]
    # 季
    if timeType == "season":
        if tmpMon in ["03", "04", "05"]:
           res_time = tmpYear+"01"
        elif tmpMon in ["06", "07", "08"]:
            res_time = tmpYear + "02"
        elif tmpMon in ["09", "10", "11"]:
            res_time = tmpYear + "03"
        elif tmpMon in ["01", "02"]:
            res_time = tmpYear + "04"
        else:
            res_time = str(int(tmpYear)+1) + "04"
    # 年
    if timeType == "year":
        res_time = tmpYear
    return res_time

# 将其它尺度（季、年）的日期转换成月
def otherTime2Month(timeStr, timeType):
    res_time = []
    # 季
    if timeType == "season":
        tmpYear, tmpSea = timeStr[0:4], timeStr[4:6]
        if tmpSea == "04":
            res_time.append(str(int(tmpYear)-1) + "12")
            res_time.append(tmpYear + "02")
        else:
            res_time.append(tmpYear + "{0:02d}".format(int(tmpSea)*3))
            res_time.append(tmpYear + "{0:02d}".format(int(tmpSea)*3+2))
    # 年
    if timeType == "year":
        res_time.append(timeStr + "01")
        res_time.append(timeStr + "12")

    return res_time


# 日期转换成带中文
def time_format_ch(timeStr, timeType):
    res_time = ""
    if timeType == "day":
        res_time = timeStr[0:4] + "年" + timeStr[4:6] + "月" + timeStr[6:] + "日"
    if timeType == "five":
        res_time = timeStr[0:4] + "年" + timeStr[4:6] + "月" + timeStr[6:] + "候"
    if timeType == "ten":
        ten = timeStr[6:]
        ten_str = ""
        if ten == "01":
            ten_str = "上旬"
        if ten == "02":
            ten_str = "中旬"
        if ten == "03":
            ten_str = "下旬"
        res_time = timeStr[0:4] + "年" + timeStr[4:6] + "月" + ten_str
    if timeType == "mon":
        res_time = timeStr[0:4] + "年" + timeStr[4:] + "月"
    if timeType == "season":
        sea = timeStr[4:]
        sea_str = ""
        if sea == "01":
            sea_str = "春季"
        if sea == "02":
            sea_str = "夏季"
        if sea == "03":
            sea_str = "秋季"
        if sea == "04":
            sea_str = "冬季"
        res_time = timeStr[0:4] + "年" + sea_str
    if timeType == "year":
        res_time = timeStr[0:4] + "年"
    if timeType == "week":
        res_time = "未来" + timeStr + "周"
    if timeType == "five5":
        res_time = "未来" + timeStr + "候"
    return res_time


# 根据尺度获取系统当前时间
def getCurrTime(time_type):
    curr_time = ""
    if time_type == "day":
        curr_time = datetime.datetime.now().strftime("%Y%m%d")
    if time_type == "mon":
        curr_time = datetime.datetime.now().strftime("%Y%m")
    if time_type == "year":
        curr_time = datetime.datetime.now().strftime("%Y")
    return curr_time


# 根据根据起始日推算未来或过去周
def day2Week(timeStr, weeks):
    res_time = []
    # 计算当前日期是周几
    startDate = strToDate(str(timeStr), "%Y%m%d")
    weekday = startDate.weekday()
    # print(weekday)
    # 计算当前时间距离下一个周一的间隔
    w_space = 7 - weekday
    # 推算未来N周的周一距当前日期的间隔
    s_w = (int(weeks)-2)*7 + w_space
    # 计算未来N周起止日期
    start_week_time = time_increase(startDate, s_w)
    end_week_time = time_increase(startDate, s_w+6)
    res_time.append(start_week_time)
    res_time.append(end_week_time)
    return res_time


# 日期转换成带中文
def time_format_en(timeStr, timeType,formatType):
    res_time = ""
    if timeType == "day":
        res_time = timeStr[0:4] + formatType + timeStr[4:6] + formatType + timeStr[6:]
    if timeType == "five":
        res_time = timeStr[0:4] + formatType + timeStr[4:6] + formatType + timeStr[6:]
    if timeType == "ten":
        res_time = timeStr[0:4] + formatType + timeStr[4:6] + formatType + timeStr[6:]
    if timeType == "mon":
        res_time = timeStr[0:4] + formatType + timeStr[4:]
    if timeType == "season":
        res_time = timeStr[0:4] + formatType + timeStr[4:]
    if timeType == "year":
        res_time = timeStr[0:4]
    return res_time


def getDaysOfYear(timeStr):
    timeStr = timeStr.replace("-","")
    year, month, day = int(timeStr[0:4]), int(timeStr[4:6]),int(timeStr[6:])
    if year %4 ==0 and year %100 ==0 or year %400 ==0:
        day_second = 29
    else:
        day_second = 28
    days_month = (31,day_second,31,30,31,30,31,31,30,31,30,31)
    total_days = 0
    total_days += sum(days_month[:month-1])
    total_days += day
    return total_days

def getForwradTime(timeStr, time_type, offset):
    resTime = timeStr
    if time_type == 'day':
        curr_day_date = datetime.datetime.strptime(timeStr, "%Y%m%d")
        resTime = (curr_day_date + datetime.timedelta(days=offset)).strftime("%Y%m%d")

    if time_type == 'five':
        year, month, five = int(timeStr[0:4]), int(timeStr[4:6]), int(timeStr[6:8])
        if (offset >= 0):
            for i in range(offset):
                five = five + 1
                if five == 7:
                    five = 1
                    month = month + 1
                if month == 13:
                    year = year + 1
                    month = 1
        else:
            for i in range(abs(offset)):
                five = five - 1
                if five == 0:
                    five = 6
                    month = month - 1
                if month == 0:
                    year = year - 1
                    month = 12
        resTime = str(year) + "{0:02d}".format(month) + "{0:02d}".format(five)

    if time_type == 'ten':
        year, month, ten = int(timeStr[0:4]), int(timeStr[4:6]), int(timeStr[6:8])
        if (offset >= 0):
            for i in range(offset):
                ten = ten + 1
                if ten == 4:
                    ten = 1
                    month = month + 1
                if month == 13:
                    year = year + 1
                    month = 1
        else:
            for i in range(abs(offset)):
                ten = ten - 1
                if ten == 0:
                    ten = 3
                    month = month - 1
                if month == 0:
                    year = year - 1
                    month = 12
        resTime = str(year) + "{0:02d}".format(month) + "{0:02d}".format(ten)

    if time_type == 'mon':
        curr_month_date = datetime.datetime.strptime(timeStr, "%Y%m")
        month = curr_month_date.month
        year = curr_month_date.year
        if (offset >= 0):
            for i in range(offset):
                month = month + 1
                if month == 13:
                    year = year + 1
                    month = 1
        else:
            for i in range(abs(offset)):
                month = month - 1
                if month == 0:
                    year = year - 1
                    month = 12
        resTime = datetime.date(year, month, 1).strftime('%Y%m')

    if time_type == "season":
        syear, sea = int(timeStr[0:4]), int(timeStr[4:6])
        tsea = sea + offset
        if tsea < 0:
            pre_year = (tsea * -1) // 4 + 1;
            if sea == 4:
                pre_year = pre_year + 1;
            else:
                if (tsea * -1) % 4 == 0:
                    pre_year = pre_year - 1
            pre_ff = 4 - (tsea * -1) % 4
            resTime = str(syear - pre_year) + "0" + str(pre_ff)
        elif tsea > 0:
            pre_year = tsea // 4
            if sea == 4:
                pre_year = pre_year - 1
            pre_ff = tsea % 4
            if pre_ff == 0:
                pre_ff = 4
            resTime = str(syear + pre_year) + "0" + str(pre_ff)
        else:
            resTime = str(syear) + "04"

    if time_type == 'year':
        resTime = str(int(timeStr) + offset)
    return resTime
def isLeapYear(yearStr):
    leapFlag = False
    year = int(yearStr)
    if year %4 == 0 and year % 100 != 0 or year % 400 == 0:
        leapFlag = True
    return leapFlag

# 根据根据起始日计算临近的周一或周四
def getNearWeek1or4(timeStr):
    res_time = []
    # 计算当前日期是周几
    startDate = strToDate(str(timeStr), "%Y%m%d")
    weekday = startDate.weekday()
    # 周一、周四
    if weekday in [0, 3]:
        w_space = 0
    # 周二、周三
    if weekday in [1, 2]:
        w_space = 0 - weekday
    # 周五、周六、周日
    if weekday in [4, 5, 6]:
        w_space = 3 - weekday
    # 计算未来N周起止日期
    week_time = time_increase(startDate, w_space)
    # print(timeStr,weekday,week_time)
    return week_time

def getForwradWeek1or4(timeStr,offset):
    res_time = []
    # 计算当前日期是周几
    startDate = strToDate(str(timeStr), "%Y%m%d")
    weekday = startDate.weekday()
    if (offset >=0):
        for i in range(offset):
            if weekday == 3:
                sp = 4
            if weekday == 0:
                sp = 3
            startDate = startDate + datetime.timedelta(days=sp)
            weekday = startDate.weekday()
    else:
        for i in range(abs(offset)):
            if weekday == 3:
                sp = -3
            if weekday == 0:
                sp = -4
            startDate = startDate + datetime.timedelta(days=sp)
            weekday = startDate.weekday()
    week_time = startDate.strftime("%Y%m%d")
    # print(timeStr,offset,week_time)
    return week_time

# 根据根据起始日推算未来或过去的滚动候日期
def day2RunFive(timeStr, offset):
    res_time = []
    startIndex = (int(offset)-1)*5+1
    endIndex = int(offset)*5
    start_five5_time = getForwradTime(timeStr, "day", startIndex)
    end_five5_time = getForwradTime(timeStr, "day", endIndex)
    res_time.append(start_five5_time)
    res_time.append(end_five5_time)
    return res_time

# 根据起报时间及预报周，计算预报周包含下个月的周，周至少有4天在下个月才进行保留
def getNextMonWeek(timeStr, weeks):
    res_week = ""
    start_week = int(weeks)
    # 计算当前日期是周几
    startDate = strToDate(str(timeStr), "%Y%m%d")
    weekday = startDate.weekday()
    if weekday == 3:
        end_week = 5
    else:
        end_week = 4
    curr_ym = timeStr[0:6]
    for w in range(start_week,end_week+1):
        curr_ym_num = 0
        tmp_wt_list = get_time_list(day2Week(timeStr, str(w)), "day")
        for wt in tmp_wt_list:
            if wt[0:6]==curr_ym:
                curr_ym_num = curr_ym_num+1
        if curr_ym_num < 4:
            res_week = str(w)
            break
    return res_week
