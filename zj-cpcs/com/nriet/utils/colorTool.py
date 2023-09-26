#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2019/10/21
# @Author : xulh
# @File : colorTool.py

import numpy as np
import logging
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import SERVER_HANDLING_ERROR_CODE

import traceback

def getColorCfg(colorFi):
    # logging.info("vals:"+colorFi)
    try:
        with open(colorFi, "r",encoding='utf-8') as vals:
            return vals.readlines()
    except Exception as e :
        logging.error(traceback.format_exc())
        raise AlgorithmException(response_code=SERVER_HANDLING_ERROR_CODE, response_msg=e.__str__())


def getColorMap(colorFi):
    vals = getColorCfg(colorFi)

    level_length = len(vals[4].split(","))
    # i_colorNum = len(vals) - level_length
    af_colorMap = np.full((level_length+1, 3), 255.)
    j = 0
    while (j<=level_length):
        af_colorTmp = vals[len(vals) - level_length-1+j].split(",")
        af_colorMap[j, 0] = float(af_colorTmp[0]) / 255.
        af_colorMap[j, 1] = float(af_colorTmp[1]) / 255.
        af_colorMap[j, 2] = float(af_colorTmp[2]) / 255.
        j = j + 1
    # logging.info(af_colorMap)
    return af_colorMap


def getColorValueDef(colorFi):
    try:
        vals = getColorCfg(colorFi)
        af_colorValueDef = list(map(lambda x: eval(x), vals[4].split(",")))
    except Exception as e:
        logging.error(traceback.format_exc())
        raise AlgorithmException(response_code=SERVER_HANDLING_ERROR_CODE, response_msg=e.__str__())
    return np.array(af_colorValueDef)


def getColorOrder(colorFi):
    vals = getColorCfg(colorFi)
    ai_colorOrder = list(map(lambda x: int(x), vals[2].split(",")))
    # logging.info(np.array(ai_colorOrder)+5)
    return np.array(ai_colorOrder) + 5


def getLegendLabelsDef(colorFi):
    try:
        vals = getColorCfg(colorFi)
        af_legendLabelsDef = []
        colorLevels =vals[4].split(",")
        for i, cl in enumerate(colorLevels):
            if i == 0:
                af_legendLabelsDef.append("<"+colorLevels[i])
            if 0 < i < len(colorLevels) - 1:
                af_legendLabelsDef.append(colorLevels[i - 1] + "~F34~*~F~" + colorLevels[i])
            if i == len(colorLevels) - 1:
                af_legendLabelsDef.append(colorLevels[i - 1] + "~F34~*~F~" + colorLevels[i].strip())
                af_legendLabelsDef.append( ">" + colorLevels[i].strip())
        # print(len(colorLevels))
        # print(len(af_legendLabelsDef))
        # exit()
    except Exception as e:
        logging.error(traceback.format_exc())
        raise AlgorithmException(response_code=SERVER_HANDLING_ERROR_CODE, response_msg=e.__str__())
    return np.array(af_legendLabelsDef)


def getZdyLegendLabelsDef(colorLevels):
    try:
        af_legendLabelsDef = []
        colorLevels = [str(int(cl)) if not isinstance(cl, str) and cl % 1 == 0 else str(cl) for cl in colorLevels]
        for i, cl in enumerate(colorLevels):
            if i == 0:
                af_legendLabelsDef.append("<"+colorLevels[i])
            if 0 < i < len(colorLevels) - 1:
                af_legendLabelsDef.append(colorLevels[i - 1] + "~F34~*~F~" + colorLevels[i])
            if i == len(colorLevels) - 1:
                af_legendLabelsDef.append(colorLevels[i - 1] + "~F34~*~F~" + colorLevels[i].strip())
                af_legendLabelsDef.append( ">" + colorLevels[i].strip())
        # print(len(colorLevels))
        # print(len(af_legendLabelsDef))
        # exit()
    except Exception as e:
        logging.error(traceback.format_exc())
        raise AlgorithmException(response_code=SERVER_HANDLING_ERROR_CODE, response_msg=e.__str__())
    return np.array(af_legendLabelsDef)