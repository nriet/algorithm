#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/02/28
# @Author : xulh
# @File : SubWorkFlowDto.py

class SubWorkFlowDto:

    def __init__(self, work_flow_dto, sun_flow_order):
        self.work_flow_dto = work_flow_dto
        self.sub_local_params = work_flow_dto.getParam("work_flow_params")[sun_flow_order]
