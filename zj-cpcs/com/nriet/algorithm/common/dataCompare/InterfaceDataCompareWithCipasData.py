# -*- coding:utf-8 -*-
# @Time : 2020/09/16
# @Author : huxin
# @File : InterfaceDataCompareWithCipasData.py
import logging
from com.nriet.utils.dataInterface.NumpyDataCompareUtils import numpy_nan_equal
class InterfaceDataCompareWithCipasData():
    def __init__(self,sub_local_params, algorithm_input_data):
        self.compare_values_A = algorithm_input_data[0]['outputData'].values
        self.compare_values_B = algorithm_input_data[1]['outputData'].values

    def execute(self):
        logging.info('Judging compare_values_A equals to compare_values_B')
        logging.info(numpy_nan_equal(self.compare_values_A,self.compare_values_B))