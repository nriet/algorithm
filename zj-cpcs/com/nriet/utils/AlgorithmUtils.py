#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2023/08/08
# @Author : Sbiys
# @File : AlgorithmUtils.py

import numpy as np
from scipy.stats import pearsonr
import pandas as pd
import xarray as xr

# 统计PC评分
def cal_pc(moniData, foreData):
    """ 统计PC评分

        Parameters
        ----------
        moniData : DataArray
            含有站点维的一维DataArray数组， 站点维要与foreData的站点维一致
        foreData : DataArray
            含有站点维的一维DataArray数组，站点维要与moniData的站点维一致

        Returns
        -------
        obj : float
            保留1位小数的Pc评分值
    """
    tmp_moniData = np.array(moniData)
    tmp_foreData = np.array(foreData)
    M = 0
    N = len(tmp_moniData) - np.isnan(tmp_foreData).sum()
    for m, f in zip(tmp_moniData, tmp_foreData):
        if (m >= 0 and f >= 0) or (m < 0 and f < 0):
            M += 1
    pc = M / N * 100
    return round(pc, 1)

# 统计PS评分
def cal_ps(moniData, foreData, type):
    """ 统计PS评分

        Parameters
        ----------
        moniData : DataArray
            含有站点维的一维DataArray数组， 站点维要与foreData的站点维一致
        foreData : DataArray
            含有站点维的一维DataArray数组，站点维要与moniData的站点维一致
        type : string
            统计xx量的PS评分 R: 降水距平百分率， T: 气温距平

        Returns
        -------
        obj : float
            保留1位小数的Ps评分值
    """
    tmp_moniData = np.array(moniData)
    tmp_foreData = np.array(foreData)
    N0 = N1 = N2 = d = M = 0
    # 降水Ps评分统计
    if type == "R":
        for i in range(len(tmp_moniData)):
            # 判断实况缺测
            if np.isnan(tmp_moniData[i]):
                d += 1
                continue

            # 判断趋势预报是否正确
            if tmp_moniData[i] >= 0 and tmp_foreData[i] >= 0 or (tmp_moniData[i] < 0 and tmp_foreData[i] < 0):
                N0 += 1

            # 判断一级异常
            if (0.2 <= tmp_moniData[i] < 0.5 and 0.2 <= tmp_foreData[i] < 0.5) or \
                    (-0.5 < tmp_moniData[i] <= -0.2 and -0.5 < tmp_foreData[i] <= -0.2):
                N1 += 1

            # 判断二级异常
            if (tmp_moniData[i] >= 0.5 and tmp_foreData[i] >= 0.5) or (
                    tmp_moniData[i] <= -0.5 and tmp_foreData[i] <= -0.5):
                N2 += 1

            # 判断异常漏报：没有预报二级异常，实况绝对值>=1
            if -0.5 < tmp_foreData[i] < 0.5 and abs(tmp_moniData[i]) >= 1:
                M += 1

    # 气温Ps评分统计
    if type == "T":
        for i in range(len(tmp_moniData)):
            # 判断实况缺测
            if np.isnan(tmp_moniData[i]):
                d += 1
                continue

            # 判断趋势预报是否正确
            if tmp_moniData[i] >= 0 and tmp_foreData[i] >= 0 or (tmp_moniData[i] < 0 and tmp_foreData[i] < 0):
                N0 += 1

            # 判断一级异常
            if (1 <= tmp_moniData[i] < 2 and 1 <= tmp_foreData[i] < 2) or \
                    (-2 < tmp_moniData[i] <= -1 and -2 < tmp_foreData[i] <= -1):
                N1 += 1

            # 判断二级异常
            if (tmp_moniData[i] >= 2 and tmp_foreData[i] >= 2) or (
                    tmp_moniData[i] <= -2 and tmp_foreData[i] <= -2):
                N2 += 1

            # 判断异常漏报：没有预报二级异常，实况绝对值>=1
            if -2 < tmp_foreData[i] < 2 and abs(tmp_moniData[i]) >= 3:
                M += 1

    N = len(tmp_moniData) - d
    a = 2.
    b = 2.
    c = 4.
    fm = (N - N0) + a * N0 + b * N1 + c * N2 + M
    if fm == 0:
        Ps = 999999
    else:
        Ps = (a * N0 + b * N1 + c * N2) / fm * 100
        Ps = round(Ps, 1)
    return Ps

# 统计ACC
def cal_acc(moniData, foreData):
    """ 统计空间相关系数（ACC）

        Parameters
        ----------
        moniData : DataArray
            含有站点维的一维DataArray数组， 站点维要与foreData的站点维一致
        foreData : DataArray
            含有站点维的一维DataArray数组，站点维要与moniData的站点维一致

        Returns
        -------
        obj : float
            保留2位小数的相关系数值
    """
    tmp_moniData = np.array(moniData)
    tmp_foreData = np.array(foreData)
    gsm = pd.Series(tmp_moniData)
    gsf = pd.Series(tmp_foreData)
    acc = gsm.corr(gsf)
    if np.isnan(acc):
        return 999.0
    else:
        return round(acc, 2)

# 统计TCC
def cal_tcc(moniData, foreData):
    """ 统计时间空间相关系数（TCC）

        Parameters
        ----------
        moniData : DataArray
            含有时间和站点维的二维DataArray数组， moniData与foreData的维度要保持一致
        foreData : DataArray
            含有时间和站点维的二维DataArray数组，moniData与foreData的维度要保持一致

        Returns
        -------
        obj : DataArray
            含有站点维的一维DataArray数组
    """
    dims = moniData.dims
    sta = moniData[dims[1]]
    tmp_moniData = np.array(moniData)
    tmp_foreData = np.array(foreData)
    r = np.full((tmp_moniData.shape[1]), np.nan)
    p = np.full((tmp_moniData.shape[1]), np.nan)
    for i in range(tmp_moniData.shape[1]):
        if len(np.where(np.isnan(tmp_foreData[:, i]))[0]) == 0 and len(np.where(np.isnan(tmp_moniData[:, i]))[0]) == 0:
            r[i], p[i] = pearsonr(tmp_foreData[:, i], tmp_moniData[:, i])
    data_cor = xr.DataArray(r, coords=[sta], dims=[dims[1]])
    return data_cor

# 相对误差 绝对误差、符号判断检验
def cal_err_symbol(moniData, foreData, type):
    """ 根据type类型做不同的检验统计

        Parameters
        ----------
        moniData : DataArray
            含有时间和站点维的二维DataArray数组， moniData与foreData的维度要保持一致
        foreData : DataArray
            含有时间和站点维的二维DataArray数组，moniData与foreData的维度要保持一致
        type : string
            检验方法 ERR: 绝对误差， RERR: 相对误差， SYMBOL: 符号判定

        Returns
        -------
        obj : DataArray
            含有站点维的一维DataArray数组
    """
    # 绝对误差
    if type == "ERR":
        resultData = foreData - moniData

    # 相对误差
    if type == "RERR":
        resultData = foreData - moniData
        moniData = np.where(moniData == 0, np.nan, moniData)
        resultData = resultData / moniData * 100

    # 符号判定
    if type == "SYMBOL":
        resultData = foreData * moniData
        resultData = xr.where(resultData >= 0, 1, resultData)
        resultData = xr.where(resultData < 0, -1, resultData)
        # 两种特殊情况，符号需设置为-1
        # 统计 监测==0且预测<0 的下标集合
        s1 = set(np.where(moniData == 0)[0]).intersection(set(np.where(foreData < 0)[0]))
        # 统计 监测<0且预测==0 的下标集合
        s2 = set(np.where(moniData < 0)[0]).intersection(set(np.where(foreData == 0)[0]))
        indexs = list(s1.union(s2))
        if len(indexs) > 0:
            resultData[indexs] = -1
    return resultData


# 统计RMSE
def cal_rmse(moniData, foreData):
    """ 统计RMSE

        Parameters
        ----------
        moniData : DataArray
            含有站点维的一维DataArray数组， 站点维要与foreData的站点维一致
        foreData : DataArray
            含有站点维的一维DataArray数组，站点维要与moniData的站点维一致

        Returns
        -------
        obj : float
            保留2位小数的RMSE数值
    """
    tmp_moniData = np.array(moniData)
    tmp_foreData = np.array(foreData)
    a = np.nansum((tmp_foreData - tmp_moniData) ** 2)
    rmse = np.sqrt(a / len(tmp_foreData))
    return round(rmse, 2)


# 同号率
def cal_symbolrate(moniData, foreData):
    """ 同号率检验统计

        Parameters
        ----------
        moniData : DataArray
            含有站点维的一维DataArray数组， moniData与foreData的维度要保持一致
        foreData : DataArray
            含有站点维的一维DataArray数组，moniData与foreData的维度要保持一致
        type : string
            检验方法 ERR: 绝对误差， RERR: 相对误差， SYMBOL: 符号判定

        Returns
        -------
        obj : float
            保留2位小数的同号率数值
    """
    resultData = foreData * moniData
    resultData = xr.where(resultData >0, 1, resultData)
    resultData = xr.where(resultData <= 0, -1, resultData)
    # 统计 监测==0且预测=0 的下标集合
    s1 = set(np.where(moniData == 0)[0]).intersection(set(np.where(foreData == 0)[0]))
    indexs = list(s1)
    if len(indexs) > 0:
        resultData[indexs] = 1
    resultData = xr.where(resultData <= 0, 0, resultData)
    tmp_resultData = np.array(resultData)
    symbolrate = np.nansum(tmp_resultData) / len(tmp_resultData) *100
    return round(symbolrate, 2)


# 统计TRMSE
def cal_trmse(moniData, foreData):
    """ 统计时间空间RMSE

        Parameters
        ----------
        moniData : DataArray
            含有时间和站点维的二维DataArray数组， moniData与foreData的维度要保持一致
        foreData : DataArray
            含有时间和站点维的二维DataArray数组，moniData与foreData的维度要保持一致

        Returns
        -------
        obj : DataArray
            含有站点维的一维DataArray数组
    """
    dims = moniData.dims
    sta = moniData[dims[1]]
    tmp_moniData = np.array(moniData)
    tmp_foreData = np.array(foreData)
    trmse = np.full((tmp_moniData.shape[1]), np.nan)
    for i in range(tmp_moniData.shape[1]):
        if len(np.where(np.isnan(tmp_foreData[:, i]))[0]) == 0 and len(np.where(np.isnan(tmp_moniData[:, i]))[0]) == 0:
            a = np.nansum((tmp_foreData[:, i] - tmp_moniData[:, i]) ** 2)
            tmp_rmse = np.sqrt(a / len(tmp_foreData[:, i]))
            trmse[i] = tmp_rmse
    resTrmse = xr.DataArray(trmse, coords=[sta], dims=[dims[1]])
    return resTrmse

