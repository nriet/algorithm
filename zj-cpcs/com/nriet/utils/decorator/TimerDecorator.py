#!/usr/bin/env python
# -*- coding:utf-8 -*-

import functools
import logging
from com.nriet.utils import fileUtils, DateUtils


def timer_with_param(param):
    def timer_param(func):
        @functools.wraps(func)
        def call_fun(*args, **kwargs):
            startTime = DateUtils.getTimeStamp()
            func(*args, **kwargs)
            endTime = DateUtils.getTimeStamp()
            logging.info("          %s run time: %s ms" %(param, str(endTime - startTime)))

        return call_fun

    return timer_param


def timer(func):
    '''
    计时修饰器
    :param func: 调用修饰器的方法
    :return:
    '''

    @functools.wraps(func)
    def call_fun(*args, **kwargs):
        startTime = DateUtils.getTimeStamp()
        func(*args, **kwargs)
        endTime = DateUtils.getTimeStamp()
        logging.info("process run time:", endTime - startTime)

    return call_fun
