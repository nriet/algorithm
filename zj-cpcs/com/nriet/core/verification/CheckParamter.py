#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/02/21
# @Author : xulh

import ast


def check_page_param(localParam):
    '''
    关于页面参数的强校验
    :param localParam: 前台页面参数字典
    :return: 校验结果字典
    '''
    result_dict={"is_success":True,"error_msg":""}

    param_name_list = ["dataSource", "elements", "bussId", "timeType", "timeRanges"]
    if not localParam:
        for param_name in param_name_list:
            if not localParam.keys().__contains__(param_name):
                result_dict['is_success'] = False
                result_dict['error_msg'] = '参数校验失败,页面参数缺少%s' % param_name
    return result_dict


