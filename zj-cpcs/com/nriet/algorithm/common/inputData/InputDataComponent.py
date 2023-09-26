#!/usr/bin/env python
# -*- coding:utf-8 -*-
from com.nriet.algorithm.Component import Component


class InputDataComponent(Component):

    def __init__(self, lon, lat, time, proData):
        '''
        数据转换和提取类
        :param lon: 经度类型：一维数组ndarray
        :param lat: 维度类型：一维数组ndarray
        :param time: 时间类型：一维数组ndarray
        :param proData:
        '''
        self.lon = lon
        self.lat = lat
        self.time = time
        self.proData = proData

    def execute(self):
        pass
