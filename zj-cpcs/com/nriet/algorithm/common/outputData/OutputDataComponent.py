#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/01/09
# @Author : xulh
# @File : CommonFileHander.py
from com.nriet.algorithm.Component import Component


class OutputDataComponent(Component):

    def __init__(self, filePath, fileName, data=None):
        self.filePath = filePath
        self.fileName = fileName
        self.data = data

    def execute(self):
        pass
