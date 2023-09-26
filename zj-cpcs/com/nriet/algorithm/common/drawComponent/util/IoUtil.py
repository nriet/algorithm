# -*- coding: utf-8 -*-
# 构造读写基础类，io交互功能工具类
import os
import datetime
import re
import pandas as pd
import matplotlib as mpl
import calendar
import logging

# 获取配置的站点信息
def getareaStation(name, properiesConfigPath):
    combination_input = '[' + name + ']'
    awsSqlSta = []
    # basefileName = open('/home/nriet/python_qh_new/com/nriet/config/propConfig/properiesConfig.ini', 'r')
    basefileName = open(properiesConfigPath, 'r')
    statmp = basefileName.readlines()
    for i in range(len(statmp)):
        if statmp[i].split(" ")[0].strip() == combination_input:
            # return statmp[i].split(" ")
            basefileName.close()
            f1 = open(statmp[i].split(" ")[1].strip(), "r")
            basefileName.close()
            break
    statmpone = f1.readlines()
    for i in range(len(statmpone)):
        awsSqlSta.append(eval(statmpone[i].split("\t")[0].strip()))
    return awsSqlSta


# 通过[]获取后面信息
def readConfig(configPath, varName):
    try:
        with open(configPath) as fl:
            config = fl.readlines()
            # logging.info config
            for params in config:
                argu = params.split(" ")
                # logging.info isinstance(argu,list)
                if argu[0] == '[' + varName + ']':
                    # logging.info len(argu)
                    if len(argu) == 2:
                        result = argu[len(argu) - 1].strip()
                        return result
                    else:
                        # logging.info argu
                        for i in range(len(argu)):
                            argu[i] = argu[i].strip()
                        result = argu[1:(len(argu))]
                        return result
            fl.close()
    except IOError:
        logging.info("File .ini is missing!")


def readConfig_int(configPath, varName):
    try:
        with open(configPath) as fl:
            config = fl.readlines()
            for params in config:
                argu = params.split(" ")
                # logging.info isinstance(argu,list)
                if argu[0] == '[' + varName + ']':
                    # logging.info len(argu)
                    if len(argu) == 2:
                        result = eval(argu[len(argu) - 1].strip())
                        return result
                    else:
                        # logging.info argu
                        for i in range(len(argu)):
                            # logging.info argu[i]
                            if i > 0:
                                argu[i] = eval(argu[i].strip())
                        # logging.info argu[1:(len(argu))]
                        result = argu[1:(len(argu))]
                        return result
            fl.close()
    except IOError:
        logging.info("File .ini is missing!")


#	    exit()

def readConfig_blank_space(configPath, varName):
    try:
        with open(configPath) as fl:
            config = fl.readlines()
            for params in config:
                argu = params.split(" ")
                # logging.info isinstance(argu,list)
                if argu[0] == '[' + varName + ']':
                    # logging.info len(argu)
                    if len(argu) == 2:
                        result = argu[len(argu) - 1].strip()
                        result = result.replace('_', ' ')
                        return result
                    else:
                        # logging.info argu
                        for i in range(len(argu)):
                            argu[i] = argu[i].strip()
                            argu[i] = argu[i].replace('_', ' ')
                        result = argu[1:(len(argu))]
                        return result
            fl.close()
    except IOError:
        logging.info("File .ini is missing!")


# 对传入的配置文件的读取，这里用‘=’来进行区分，有别于上面的无‘=’的情况,返回的为字符串
def readConfigParam(configPath, varName):
    try:
        with open(configPath) as fl:
            config = fl.readlines()
            # logging.info config
            for params in config:
                argu = params.split("=")
                # logging.info isinstance(argu,list)
                if argu[0] == varName:
                    arguNext = argu[1].split(',')
                    if len(arguNext) == 1:
                        result = arguNext[0].strip()
                        return result
                    else:
                        for i in range(len(arguNext)):
                            arguNext[i] = arguNext[i].strip()
                        result = arguNext[0:(len(arguNext))]
                        return result
    except IOError:
        logging.info("File .ini is missing!")


# 对传入的配置文件的读取，这里用‘=’来进行区分，有别于上面的无‘=’的情况,返回的为字符串
def readConfigParamNew(configPath, varName):
    try:
        with open(configPath) as fl:
            config = fl.readlines()
            # logging.info config
            for params in config:
                argu = params.split("=")
                # logging.info isinstance(argu,list)
                if argu[0] == varName:
                    arguNext = argu[1].split('/')
                    if len(arguNext) == 1:
                        result = arguNext[0].strip()
                        return result
                    else:
                        for i in range(len(arguNext)):
                            arguNext[i] = arguNext[i].strip()
                        result = arguNext[0:(len(arguNext))]
                        return result
    except IOError:
        logging.info("File .ini is missing!")


# 对传入的配置文件的读取，这里用‘=’来进行区分，有别于上面的无‘=’的情况,返回的为数字类型
def readConfigParamInt(configPath, varName):
    try:
        with open(configPath) as fl:
            config = fl.readlines()
            # logging.info config
            for params in config:
                argu = params.split("=")
                # logging.info isinstance(argu,list)
                if argu[0] == varName:
                    arguNext = argu[1].split(',')
                    if len(arguNext) == 1:
                        result = eval(arguNext[0].strip())
                        return result
                    else:
                        for i in range(len(arguNext)):
                            arguNext[i] = eval(arguNext[i].strip())
                        result = arguNext[0:(len(arguNext))]
                        return result
    except IOError:
        logging.info("File .ini is missing!")


# 替换字符
def strReplace(stringValue, oldStr, newStr):
    return stringValue.replace(oldStr, newStr)


# 从后向前筛选变量名称
def str_back_to_front(strValue, strNum):
    # logging.info 123
    lx = len(strValue)
    lxx = strValue[0:lx - strNum]
    return lxx


# 判断字符串最后是否有阿拉伯数据
def rejectAra(strValue):
    return re.sub(r'([\d]+)', '', strValue).lower()


# 找到第一次字符出现之前的字符串
def str_first_appear(str1, str2):
    return str1[0:str1.find(str2)]


def fcstTime_cal(timeNumHour):
    if timeNumHour < 10:
        timeresult = '0' + str(timeNumHour)
    else:
        timeresult = str(timeNumHour)
    return timeresult


# 根据起报时间与实际的月份，匹配timeind的值
def timeInd_cal(monBegin, monEnd, starttime):
    # logging.info monBegin,monEnd,starttime
    monBeginInd = monBegin - starttime
    if monEnd < starttime:
        monEndInd = monEnd + 12 - starttime
    else:
        monEndInd = monEnd - starttime
    return monBeginInd, monEndInd


def timeIndNum(starttime, prescription):
    if prescription - starttime < 0:
        timeInd = prescription + 12 - starttime
    else:
        timeInd = prescription - starttime
    return timeInd


# 返回预报最新时刻的文件
def laterTimeFiles_fcst(realTimeDate, fcstNum, timeNum, timeHourNum, i, files_Max, fileTimeMax, timeCountMax):
    fcstCountMax = []
    if len(files_Max) > 1:
        for ii in range(len(files_Max) - 1):
            # logging.info files[ii],files[ii+1]
            # os.stat(files[ii])
            files_Max[ii] = files_Max[ii].strip()
            files_Max[ii + 1] = files_Max[ii + 1].strip()
            statinfo1 = os.stat(files_Max[ii])
            statinfo2 = os.stat(files_Max[ii + 1])
            if statinfo1.st_mtime > statinfo2.st_mtime:
                fileNamefcst = files_Max[ii]
            else:
                fileNamefcst = files_Max[ii + 1]
    else:
        fileNamefcst = files_Max[0].strip()
    fileTimeMax[datetime.datetime.strftime((realTimeDate + datetime.timedelta(-fcstNum + i)),
                                           "%Y%m%d%H")] = fileNamefcst

    # logging.info fileTimeMax
    for j in range(timeNum):
        fcstCountMax.append(fcstNum * 24 - i * 24 - j * timeHourNum)
        timeCountMax[datetime.datetime.strftime((realTimeDate + datetime.timedelta(-fcstNum + i)),
                                                "%Y%m%d%H")] = fcstCountMax


# 返回实况最新时刻的文件
def laterTimeFiles_obs(realTimeDate, fcstNum, timeNum, timeHourNum, i, files, fileTimeobs):
    if len(files) > 1:
        for ii in range(len(files) - 1):
            # logging.info files[ii],files[ii+1]
            # os.stat(files[ii])
            files[ii] = files[ii].strip()
            files[ii + 1] = files[ii + 1].strip()
            statinfo1 = os.stat(files[ii])
            statinfo2 = os.stat(files[ii + 1])
            if statinfo1.st_mtime > statinfo2.st_mtime:
                fileNameobs = files[ii]
            else:
                fileNameobs = files[ii + 1]
    else:
        fileNameobs = files[0].strip()
    fileTimeobs[datetime.datetime.strftime((realTimeDate + datetime.timedelta(hours=-timeHourNum * i)),
                                           "%Y%m%d%H")] = fileNameobs


# 构造输入变量的pandas数组
def inPutPd(valueType):
    arrayOne = valueType.split(',')
    arrayIndex = []
    arrayValue = []
    for i in range(len(arrayOne)):
        # logging.info arrayOne[i]
        arrayTwo = arrayOne[i].split('=')
        # logging.info arrayTwo
        arrayIndex.append(arrayTwo[0])
        arrayValue.append(arrayTwo[1])
    array_pd = pd.Series(arrayValue, index=arrayIndex)

    return array_pd


# 颜色反转
def reverse_colormap(cmap, name='my_cmap_r'):
    reverse = []
    k = []
    cmap = mpl.cm.get_cmap(cmap)
    # logging.info cmap
    for key in cmap._segmentdata:
        k.append(key)
        channel = cmap._segmentdata[key]
        data = []
        for t in channel:
            data.append((1 - t[0], t[2], t[1]))
        reverse.append(sorted(data))
    LinearL = dict(zip(k, reverse))
    my_cmap_r = mpl.colors.LinearSegmentedColormap(name, LinearL)
    return my_cmap_r


# 根据一年的第几天，返回日期形式的变量
def out_date(year, day):
    fir_day = datetime.datetime(year, 1, 1)
    zone = datetime.timedelta(days=day - 1)
    return datetime.datetime.strftime(fir_day + zone, '%m%d')


# 设置变量显示的数量
def label_number(cb, num):
    # tick_locator=mpl.ticker.MaxNLocator(nbins=num)
    tick_locator = mpl.ticker.MultipleLocator(base=num)
    # logging.info num
    cb.locator = tick_locator
    # cb.update_ticks()


# 根据起始结束的月份，算得对应的天（这里对平年做了特殊处理，因为自动站的平年是包括2.29的），终止日根据结束月，算的月最后一天对应的天
def dayCal(year, monBegin, monEnd):
    if calendar.isleap(year):
        dayBegin = int(datetime.datetime(year, monBegin, 1).strftime('%j'))
        dayEnd = int(datetime.datetime(year, monEnd, calendar.monthrange(year, monEnd)[1]).strftime('%j'))
    elif monBegin <= 2 and monEnd <= 2:
        dayBegin = int(datetime.datetime(year, monBegin, 1).strftime('%j'))
        dayEnd = int(datetime.datetime(year, monEnd, calendar.monthrange(year, monEnd)[1]).strftime('%j'))
    elif monBegin <= 2 and monEnd > 2:
        dayBegin = int(datetime.datetime(year, monBegin, 1).strftime('%j'))
        dayEnd = int(datetime.datetime(year, monEnd, calendar.monthrange(year, monEnd)[1]).strftime('%j')) + 1
    else:
        dayBegin = int(datetime.datetime(year, monBegin, 1).strftime('%j')) + 1
        dayEnd = int(datetime.datetime(year, monEnd, calendar.monthrange(year, monEnd)[1]).strftime('%j')) + 1

    return dayBegin, dayEnd


# 根据业务传入的日期格式，返回相应的year、month与day的值,这里可以重点关注下map函数
def datetimeCal(strTime):
    dateList = strTime.split("-")
    dateNum = map(int, dateList)
    return dateNum


# 根据起始结束的几月几号，算得对应的天（这里对平年做了特殊处理，因为自动站的平年是包括2.29的）,此处为通用的方法,这个方法是根据数据存放的逻辑来处理的
def dayCommonCal(year, monBegin, day):
    if calendar.isleap(year):
        dayBegin = int(datetime.datetime(year, monBegin, day).strftime('%j'))
    elif monBegin <= 2:
        dayBegin = int(datetime.datetime(year, monBegin, day).strftime('%j'))
    else:
        dayBegin = int(datetime.datetime(year, monBegin, day).strftime('%j')) + 1

    return dayBegin


# 按照顺序，varName为变量，timeCount为时间段，timeType为取值时间（day.min.year）
def pathReplace(varPath, varName, timeCount, timeType):
    if varName != None:
        varPath = strReplace(varPath, '#Q', varName)
    if timeCount != None:
        varPath = strReplace(varPath, '#TC', timeCount)
    if timeType != None:
        varPath = strReplace(varPath, '#TY', timeType)
    return varPath
