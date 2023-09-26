from intervals import IntInterval
from intervals import DecimalInterval
import logging
def match_interval(query_value, range_values, match_values, default_value=0.0):
    """
    获取给定值在某个区间所对应的值
    :param query_value: 给定值
    :param range_values: 区间范围组
    :param match_values: 匹配值组
    :param default_value: 未匹配到的默认值
    :return:  返回对应值,没有匹配到则返回None
    """
    list_interval = []
    for i in range(len(range_values)):
        if i != len(range_values) - 1:
            data_range = IntInterval.closed_open(range_values[i], range_values[i + 1])
            list_interval.append(data_range)
    match_value = default_value
    for i in range(len(list_interval)):
        if query_value in list_interval[i]:
            match_value = match_values[i]
    return match_value

def match_interval_decimal(query_value, range_values, match_values, default_value=0.0):
    """
    获取给定值在某个区间所对应的值,注意这里的values都是小数值
    :param query_value: 给定值
    :param range_values: 区间范围组
    :param match_values: 匹配值组
    :param default_value: 未匹配到的默认值
    :return:  返回对应值,没有匹配到则返回None
    """
    list_interval = []
    for i in range(len(range_values)):
        if i != len(range_values) - 1:
            data_range = DecimalInterval.closed_open(range_values[i], range_values[i + 1])
            list_interval.append(data_range)
    match_value = default_value
    for i in range(len(list_interval)):
        if float(query_value) in list_interval[i]:
            match_value = match_values[i]
    return match_value

import numpy as np


if __name__ == '__main__':

    a = [0, 8, 16, 41, 90, 181, 361]
    b = [[1,2], [2,3], [3,4], [4,5], [5,6], [7,8]]
    np_data = np.linspace(1,20,10)

    logging.info(list(map(lambda x:match_interval(x,a,b),np_data)))
    logging.info([match_interval(data,a,b)for data in np_data])
