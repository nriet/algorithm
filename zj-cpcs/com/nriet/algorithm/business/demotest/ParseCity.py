#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2023/06/14
# @Author : Sbiys
# @File : GainStation2GirdData.py

# city_list = ["杭州市","宁波市","温州市","嘉兴市","湖州市","绍兴市","金华市","衢州市","舟山市","台州市","丽水市"]
city_list = []

with open("浙江区县代表站.txt",encoding="utf-8") as f:
    lines_list = f.readlines()

# print(lines_list)
city = "杭州市"
county_list = []
station_list = []
for line in lines_list:
    one_lines = line.strip().split()
    if one_lines[0] == city:
        tmp_county = {}
        tmp_county["countyName"] = one_lines[1]
        tmp_county["countyCode"] = one_lines[3]
        tmp_county["station"] = one_lines[2]
        county_list.append(tmp_county)
        station_list.append(one_lines[2])
    else:
        tmp_city={}
        tmp_city["cityName"] = city
        tmp_city["cityCode"] = county_list[0]["countyCode"][0:4]
        tmp_city["station"] = ",".join(station_list)
        tmp_city["countys"] = county_list
        city_list.append(tmp_city)
        county_list =[]
        station_list =[]
        tmp_county = {}
        tmp_county["countyName"] = one_lines[1]
        tmp_county["countyCode"] = one_lines[3]
        tmp_county["station"] = one_lines[2]
        county_list.append(tmp_county)
        station_list.append(one_lines[2])
        city = one_lines[0]

json_data = {"provName":"浙江省","provCode":"33","citys":city_list}
print(json_data)