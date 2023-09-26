#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2019/10/21
# @Author : xulh
# @File : fileUtils.py

import numpy as np
import json
import os
from com.nriet.utils.obs.ObsUtils import ObsUtils
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
from netCDF4 import Dataset
from com.nriet.utils import DateUtils


# 读取json文件
def readJson(filePath):
    file = open(filePath, "rb")
    return json.load(file)


# 产品生成频次
def getProDuty(dateType):
    duty = ""
    if dateType == "day":
        duty = 3
    elif dateType == "five":
        duty = 4
    elif dateType == "mon":
        duty = 7
    elif dateType == "season":
        duty = 8
    elif dateType == "year":
        duty = 9
    return duty


# 单位转化
def convert_data(data, convert_type, convert_value):
    if convert_type == "add":
        data = data + float(convert_value)
    if convert_type == "minus":
        data = data - float(convert_value)
    if convert_type == "multiply":
        data = data * float(convert_value)
    if convert_type == "divide" and convert_value != 0:
        data = data / float(convert_value)

    return data


# 数据转化：平均，和，最大，最小
def data_convert(data, convert_type):
    if convert_type == "avg":
        data = data.mean(dim="time")
    if convert_type == "min":
        data = data.min(dim="time")
    if convert_type == "max":
        data = data.max(dim="time")
    if convert_type == "sum":
        data = data.sum(dim="time")

    return data


# creat ncFile
def creatNcFile(fileName, time, lon, lat, data):
    ncFile = Dataset(fileName, "w", format="NETCDF4")
    # ncFile.createDimension("time", len(time))
    ncFile.createDimension("lat", len(lat))
    ncFile.createDimension("lon", len(lon))
    # ncFile.createDimension("olr", len(data))

    # ncFile.createVariable("time", np.double, ("time"))
    ncFile.createVariable("lat", np.double, ("lat"))
    ncFile.createVariable("lon", np.double, ("lon"))
    ncFile.createVariable("olr", np.double, ("lat", "lon"))

    # ncFile.variables["time"][:] = time
    ncFile.variables["lat"][:] = lat
    ncFile.variables["lon"][:] = lon
    ncFile.variables["olr"][:] = data

    ncFile.close()


# creat txt file
def creatTxtFile(filePath, fileName, content=""):
    if not os.path.isdir(filePath):
        os.makedirs(filePath)
    # f = open(filePath + fileName, "w")
    with open(filePath + fileName, "w") as f:
        f.write(content)
    # f.close()


# 上传txt文件到obs
def creat_txt_file_to_obs(filePath, fileName, content=None, expire: int = None):
    if not content:
        content = ""
    content_bytes = bytes(content, encoding="utf8")
    obs_bucket_name = look_for_single_global_config("OBS_BUCKET_NAME")
    obs_expire = int(look_for_single_global_config("OBS_DEFAULT_EXPIRE") if expire is None else expire)
    ObsUtils().upload_file(obs_bucket_name, filePath + fileName, content_bytes, obs_expire)


# 替换txt文件指定行内容，start：开始行；end：结束行；filename：文件路径；content：要替换的内容
def replaceTxtContent(fileName, start, end, content):
    # f = open(fileName, "r")
    with open(fileName, "r") as f:
        fContent = f.readlines()
        lContent = ""
        fileStr = ""
        for i, line in enumerate(fContent):
            fileStr = fileStr + line.replace("\n", "\r\n")
            if start <= i <= end:
                lContent = lContent + line.replace("\n", "\r\n")
        newContent = fileStr.replace(lContent, content)
        # f1 = open(fileName, "w")
        with open(fileName, "w") as f1:
            f1.write(newContent)
        # f.close()
        # f1.close()


# 替换txt文件指定行内容，start_time,end_time：文本内容替换的时间间隔；filename：文件路径；content：要替换的内容
def relpace_content(file_name, start_time, end_time, content):
    f = open(file_name, "r")
    fContent = f.readlines()
    start = 0
    end = 0
    for i, line in enumerate(fContent):
        line_start = line.split(" ")[0]
        if line_start == str(start_time):
            start = i
        if line_start == str(end_time):
            end = i
    f.close()
    replaceTxtContent(file_name, start, end, content)


# 判断目录存在
def dir_exists(str_dir: str) -> bool:
    if os.path.exists(str_dir):
        return True
    else:
        return False


# 判断文件存在
def file_exists(str_file) -> bool:
    if dir_exists(str_file) and os.path.isfile(str_file):
        return True
    else:
        return False


# 获取目录和文件名
def get_dir_and_filename_stringify(path: str) -> dict:
    _dir = os.path.dirname(path)
    _filename = os.path.basename(path)
    return {
        "dir": _dir,
        "fn": _filename
    }


# 根据时间尺度及起止时间判断NAS文件是否存在
def check_file_exists(dataInputPath, timeType, startTime, endTime) -> bool:
    if timeType == "day" and dataInputPath.find("/STATION/") == -1:
        date_list1 = DateUtils.get_time_list([startTime[0:6], endTime[0:6]], "mon")
        date_list = []
        for dateStr in date_list1:
            date_list.append(dateStr[0:4] + "_" + dateStr[4:])
    else:
        date_list = DateUtils.get_time_list([startTime[0:4], endTime[0:4]], "year")
    fileIsExist = False
    for dl in date_list:
        dataInputFile = dataInputPath + dl + ".nc"
        if dir_exists(dataInputFile) and os.path.isfile(dataInputFile):
            fileIsExist = True
            break
    return fileIsExist
