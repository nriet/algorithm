# -*- coding: utf-8 -*-

import sys
import Nio
import logging
# 此处要导入项目目录到linux环境中去，注意项目的具体路径
sys.path.append(r"/home/nriet/PycharmProjects/test-master/main")

from com.nriet.algorithm.common.drawComponent.drawController.DrawControllerTest import DrawController
from com.nriet.algorithm.common.drawComponent.drawService.SectionService import SectionService
from com.nriet.algorithm.common.drawComponent.test.section.SectionJson import request_json


def section_test():

    input_data = Nio.open_file(
        '/usr/local/src/huxin/CPCS/com/nriet/algorithm/common/drawComponent/test/section/section_vector_test.nc',
        'r')
    data_list = []
    val = input_data.variables
    contour_data = input_data.variables['jp_omega'][:]
    vector_data = [input_data.variables['jp_uwnd'][:], contour_data * -1]
    data_list.append(contour_data)
    data_list.append(vector_data)
    lon = input_data.variables['lon'][:]
    lat = input_data.variables['level'][:]
    lon_indexes = lon
    lat_indexes = lat

    dc = SectionService(data_list,lon,lat,lon_indexes,lat_indexes,request_json,dims=['level','lon'])


    result = dc.draw()

    del dc
    del data_list
    del lon
    del lat
    del lon_indexes
    del lat_indexes
    # del request_json
    logging.info(result)

def section_test1():
    dc = DrawController()
    input_data = Nio.open_file(
        '/home/xulh/mnt/python/ncc/研发/系统代码/CPCS/com/nriet/algorithm/common/drawComponent/test/section/subuv202001jp.nc',
        'r')


    data_list = []
    contour_data = input_data.variables['subsst'][:]
    vector_data = [input_data.variables['u'][:], input_data.variables['v'][:]]
    data_list.append(contour_data)
    data_list.append(vector_data)
    lon = input_data.variables['lon'][:]
    lat = input_data.variables['level'][:]
    result = dc.execute(data_list, lon, lat, request_json)
    logging.info(result)


for i in range(10):
    section_test()