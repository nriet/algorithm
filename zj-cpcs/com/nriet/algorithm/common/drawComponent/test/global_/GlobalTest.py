# -*- coding: utf-8 -*-

import sys
import Nio
import logging
# 此处要导入项目目录到linux环境中去，注意项目的具体路径
sys.path.append(r"/home/nriet/PycharmProjects/test-master/main")

from com.nriet.algorithm.common.drawComponent.drawController.DrawControllerTest import DrawController
from com.nriet.algorithm.common.drawComponent.test.section.SectionJson import request_json


def global_test():
    input_data = Nio.open_file('/home/nriet/PycharmProjects/test-master/main/test/global_test.nc', 'r')
    data_list = []
    data = input_data.variables['sst'][:]
    data_list.append(data)
    lon = input_data.variables['lon'][:]
    logging.info(lon.shape)
    lat = input_data.variables['lat'][:]
    DrawControlle = DrawController()
    result = DrawControlle.execute(data_list, lon, lat, request_json)
    logging.info(result)


global_test()
