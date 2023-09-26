#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/2/28
# @Author : xulh
# @File : SysExcepyion.py

import json
from com.nriet.config import ResponseCodeAndMsgEum
from com.nriet.utils.result.ResponseResultUtils import build_response_dict

class SysException(Exception):

    def __init__(self, message=ResponseCodeAndMsgEum.SERVER_HANDLING_ERROR_MSG,code=ResponseCodeAndMsgEum.SERVER_HANDLING_ERROR_CODE,from_tianqin=0):
        '''
        :param message: 异常信息
        '''
        self.response_msg = message
        self.response_code = code
        self.from_tianqin=from_tianqin

    def __str__(self):
        return build_response_dict(response_code=self.response_code,response_msg=self.response_msg,from_tianqin=self.from_tianqin)

