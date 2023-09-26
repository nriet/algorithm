#!/usr/bin/env python
# -*- coding:utf-8 -*-

import numpy as np


def cut_array(data_list, start_value, end_value):
    '''
    根据数组起始值切割数组
    :param data:array
    :param start_value:
    :param end_value:
    :return: array
    '''

    start = 0
    end = 0
    for i, data in enumerate(data_list):
        if data == start_value:
            start = i
        elif data == end_value:
            end = i
    return data_list[start:end]


def cycle_array(cycle, data, dims, data_size):
    '''
    根据指定维度循环数据
    :param data_size: 分割数组长度
    :param cycle:循环数据维度
    :param data:循环数据
    :param dims:数据维度
    :return:
    '''
    result = []
    for i, dim in enumerate(dims):
        if cycle == dim:
            # dims.remove(cycle)
            if isinstance(data, list):
                for cycle_data in data:
                    for da in np.split(cycle_data, data_size, axis=i):
                        result.append(da)
            else:
                result = np.split(data, data_size, axis=i)
    return result
