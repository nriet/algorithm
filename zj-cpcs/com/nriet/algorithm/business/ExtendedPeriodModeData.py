#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/02/17
# @Author : Eldan
# @File : ExtendedPeriodModeData.py
import os,time,calendar
import numpy as np
import xarray as xr
from com.nriet.algorithm.business.BusComponent import BusComponent
from com.nriet.utils import fileUtils, DateUtils
from com.nriet.utils.DerfDataUtils import DerfDataUtils
from com.nriet.utils.NcepCfsDataUtils import NcepCfsDataUtils
from com.nriet.utils.EcDataUtils import EcDataUtils
from com.nriet.utils.EcWeekDataUtils import EcWeekDataUtils
from com.nriet.utils.BccCsmDataUtils import BccCsmDataUtils
from com.nriet.utils.ModesDataUtils import ModesDataUtils
from com.nriet.utils.CmmeDataUtils import CmmeDataUtils
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import PARAMETER_VALUE_ERROR_CODE
from com.nriet.utils.decorator.TimerDecorator import timer_with_param
import logging
class ExtendedPeriodModeData(BusComponent):
    def __init__(self, sub_local_params, algorithm_input_data):
        """
        :param sub_local_params:流程参数，算法运算返回结果
        :param algorithm_input_data:流程数据
        """
        # 模式名称
        self.patternDataName = sub_local_params.get("patternDataName")
        # 数据路径
        self.dataInputPaths = sub_local_params.get("dataInputPaths")
        self.ltmDataInputPaths = sub_local_params.get("ltmDataInputPaths")
        # 经纬度范围
        self.regions = sub_local_params.get("regions")
        # 起报时间
        self.reportingTime = sub_local_params.get("reportingTime")
        # 预报起止时间
        self.forecastPeriod = sub_local_params.get("forecastPeriod")
        # 用于区分取多样本或集合平均数据
        self.dataSet = sub_local_params.get("dataSet")
        # 数据要素
        self.elements = sub_local_params.get("elements")
        # 单位转换
        self.unitConvert = sub_local_params.get("unitConvert")
        # 是否补全数据
        self.whetherMakeup = sub_local_params.get("whetherMakeup")
        self.levels = sub_local_params.get("levels")
        # 站号
        if self.patternDataName == "CPSV3DZ":
            self.station_list = algorithm_input_data[0]["outputData"].sel(space="station").values
        self.stacticType = sub_local_params.get("stacticType")
        if self.stacticType and self.stacticType == "DT":
            self.forecastPeriod[0] = int(DateUtils.getForwradTime(str(self.forecastPeriod[0]),"day",-1))
        self.output_data = None

    #@timer_with_param("          get Extended Period Mode Data")
    def execute(self):
        main_start_time = time.time()
         # 解析预报的起止时间
        foreStartTime1, foreEndTime1 = [forecastPeriod for forecastPeriod in self.forecastPeriod]
        if foreStartTime1 > foreEndTime1:
            error_str = "forecastStartTime[%s] cannot be greater than forecastEndTime[%s]!" % (foreStartTime1,foreEndTime1)
            raise AlgorithmException(response_code=PARAMETER_VALUE_ERROR_CODE, response_msg=error_str)
        out_data = {}
        if len(self.elements.split(",")) == 1:
            logging.info("ExtendedPeriodModeData processing get_single_element_data ")
            res_data = self.get_single_element_data()
        else:
            logging.info("ExtendedPeriodModeData processing __get_single_element_data ")
            res_data = self.__get_multiple_element_data()

        out_data["outputData"] = res_data
        # print(res_data)
        self.output_data = out_data
        # return  self
        main_stop_time = time.time()
        cost = main_stop_time - main_start_time
        logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))


    def get_single_element_data(self):
        data_list = []
        # 默认不补全数据 设置False
        whetherMakeup = "False"
        if self.whetherMakeup: whetherMakeup = self.whetherMakeup
        # 解析经纬度范围
        if self.regions:
            start_lon, end_lon, start_lat, end_lat = [float(value) for value in self.regions.split(',')]
        # 解析预报的起止时间
        foreStartTime, foreEndTime = [str(forecastPeriod) for forecastPeriod in self.forecastPeriod]
        tt1 = DateUtils.getTimeStamp()
        # 获取Derf数据
        if self.patternDataName in ["DERF2","BCC-S2S","BCCCSM12","CPSV3"]:
            if self.dataInputPaths:
                dataInputPaths_tmp = self.dataInputPaths + "#YYYY#/#MM#/#YYYYMMDD#_#HH#.nc"
                if self.dataSet == "mn" and self.patternDataName in ["CPSV3"]:
                    dataInputPaths_tmp = self.dataInputPaths + "#YYYY#/#MM#/#YYYYMMDD#_mn.nc"
                    modeData = DerfDataUtils.get_derf_mn_mean_data(dataInputPaths_tmp, self.reportingTime, foreStartTime,
                                                                foreEndTime, self.elements, start_lat, end_lat,
                                                                start_lon,
                                                                end_lon, whetherMakeup)
                else:
                    modeData = DerfDataUtils.get_derf_mean_data(dataInputPaths_tmp, self.reportingTime, foreStartTime,
                                                                foreEndTime, self.elements, start_lat, end_lat, start_lon,
                                                                end_lon, whetherMakeup)
            if self.ltmDataInputPaths:
                ltmDataInputPaths_tmp = self.ltmDataInputPaths + "#MMDD#_#HH#.nc"
                if self.dataSet == "mn" and self.patternDataName in ["CPSV3"]:
                    ltmDataInputPaths_tmp = self.ltmDataInputPaths + "#MMDD#_mn.nc"
                    modeLtmData = DerfDataUtils.get_derf_mn_ltm_data(ltmDataInputPaths_tmp, self.reportingTime,
                                                                  foreStartTime,
                                                                  foreEndTime, self.elements, start_lat, end_lat,
                                                                  start_lon,
                                                                  end_lon, whetherMakeup)
                else:
                    modeLtmData = DerfDataUtils.get_derf_ltm_data(ltmDataInputPaths_tmp, self.reportingTime, foreStartTime,
                                                                  foreEndTime, self.elements, start_lat, end_lat, start_lon,
                                                                  end_lon, whetherMakeup)
        # 获取EC数据
        if self.patternDataName == "ECMWF":
            if self.dataInputPaths:
                dataInputPaths_tmp = self.dataInputPaths + "#YYYY#/#MM#/#DD#/#YYYYMMDD#_#MMDD#.nc"
                modeData = EcDataUtils.get_ec_mean_data(dataInputPaths_tmp, self.reportingTime, foreStartTime,
                                                        foreEndTime, self.elements, start_lat, end_lat, start_lon,
                                                        end_lon, whetherMakeup)
            if self.ltmDataInputPaths:
                # raise AlgorithmException(response_msg="No Data : ECMWF No Data Found",response_code='9804')
                ltmDataInputPaths_tmp = self.ltmDataInputPaths + "#YYYY#/#MM#/#DD#/#YYYYMMDD#_#MMDD#.nc"
                # print(ltmDataInputPaths_tmp)
                modeLtmData = EcDataUtils.get_ec_ltm_data(ltmDataInputPaths_tmp, self.reportingTime, foreStartTime,
                                                          foreEndTime, self.elements, start_lat, end_lat, start_lon,
                                                          end_lon, whetherMakeup)
        # 获取NCEP_CFS数据
        if self.patternDataName == "CFSV2":
            if self.dataInputPaths:
                dataInputPaths_tmp = self.dataInputPaths + "#YYYY#/#MM#/#YYYYMMDD#_#HH#_#NM#.nc"
                if self.dataSet == "mn":
                    dataInputPaths_tmp = self.dataInputPaths + "#YYYY#/#MM#/#YYYYMMDD#_MN.nc"
                    modeData = NcepCfsDataUtils.get_cfs_mn_mean_data(dataInputPaths_tmp, self.reportingTime, foreStartTime,
                                                                  foreEndTime, self.elements, start_lat, end_lat,
                                                                  start_lon, end_lon, whetherMakeup)
                else:
                    modeData = NcepCfsDataUtils.get_cfs_mean_data(dataInputPaths_tmp, self.reportingTime, foreStartTime,
                                                              foreEndTime, self.elements, start_lat, end_lat, start_lon,
                                                              end_lon, whetherMakeup)
            if self.ltmDataInputPaths:
                ltmDataInputPaths_tmp = self.ltmDataInputPaths + "#MMDD#_#HH#_#NM#.nc"
                modeLtmData = NcepCfsDataUtils.get_cfs_ltm_data(ltmDataInputPaths_tmp, self.reportingTime,
                                                                foreStartTime, foreEndTime, self.elements, start_lat,
                                                                end_lat, start_lon, end_lon, whetherMakeup)

        # 获取BCCCSM11数据
        if self.patternDataName == "BCC_CSM11M":
            if self.dataInputPaths:
                dataInputPaths_tmp = self.dataInputPaths + "#YYYYMM#01.atm."+self.elements+".#YYYYMM#-#FEYM#_sfc_member.nc"
                if self.dataSet == "mn":
                    dataInputPaths_tmp = self.dataInputPaths + "MODESv2_ncc_csm11_#YYYYMM#_monthly_em.nc"
                    modeData = BccCsmDataUtils.get_bcccsm_mn_mean_data(dataInputPaths_tmp, self.reportingTime,
                                                                     foreStartTime,
                                                                     foreEndTime, self.elements, start_lat,
                                                                     end_lat,
                                                                     start_lon, end_lon, whetherMakeup)
                else:
                    modeData = BccCsmDataUtils.get_bcccsm_ens_mean_data(dataInputPaths_tmp, self.reportingTime,
                                                                  foreStartTime,
                                                                  foreEndTime, self.elements, start_lat,
                                                                  end_lat, start_lon,
                                                                  end_lon, whetherMakeup)
            if self.ltmDataInputPaths:
                ltmDataInputPaths_tmp = self.ltmDataInputPaths + "MODESv2_ncc_csm11_#MM#_monthly_ltm.nc"
                modeLtmData = BccCsmDataUtils.get_bcccsm_mn_ltm_data(ltmDataInputPaths_tmp, self.reportingTime,
                                                                foreStartTime, foreEndTime, self.elements,
                                                                start_lat,
                                                                end_lat, start_lon, end_lon, whetherMakeup)
        # 获取MODES数据
        if self.patternDataName in ["CPSV3MON","CFS2", "JMA2", "ECMWF5", "UKMO5", "NCCCSM","NCCCSM3", "MODESCFS","MODESEC", "JMA3", "EC5", "NCC"]:
            mode_str = ""
            if self.patternDataName == "CFS2" or self.patternDataName == "MODESCFS":
                mode_str = "ncep_cfs2"
            if self.patternDataName == "JMA2":
                mode_str = "jma_cps3"
            if self.patternDataName == "JMA3":
                mode_str = "jma_cps3"
            if self.patternDataName == "CPSV3MON":
                mode_str = "jma_cps3"
            if self.patternDataName == "ECMWF5" or self.patternDataName == "MODESEC" or self.patternDataName == "EC5":
                mode_str = "ecmwf_system5"
            if self.patternDataName == "UKMO5":
                mode_str = "ukmo_glosea5"
            if self.patternDataName == "NCCCSM" or self.patternDataName == "NCC":
                mode_str = "ncc_csm11"
            if self.dataInputPaths:
                # UKMO5模式实时路径特殊处理
                if self.patternDataName == "UKMO5" and self.dataInputPaths.endswith("UKMO_GLOSEA5/"):
                    dataInputPaths_tmp = self.dataInputPaths + "#YYYYMM#/MODESv2_" + mode_str + "_#YYYYMM#_monthly_em.nc"
                else:
                    dataInputPaths_tmp = self.dataInputPaths + "MODESv2_" + mode_str + "_#YYYYMM#_monthly_em.nc"
                if self.patternDataName == "NCCCSM3":
                    dataInputPaths_tmp = self.dataInputPaths + "#YYYY_MM#.nc"
                modeData = ModesDataUtils.get_modes_mean_data(dataInputPaths_tmp, self.reportingTime,
                                                              foreStartTime,
                                                              foreEndTime, self.elements, start_lat, end_lat,
                                                              start_lon,
                                                              end_lon, self.patternDataName, whetherMakeup)
            if self.ltmDataInputPaths:
                # UKMO5模式常年值路径特殊处理
                if self.patternDataName == "UKMO5" and self.ltmDataInputPaths.endswith("UKMO_GLOSEA5/"):
                    ltmDataInputPaths_tmp = self.ltmDataInputPaths + "#YYYYMM#/ltm/MODESv2_" + mode_str + "_#MM#_monthly_ltm.nc"
                else:
                    ltmDataInputPaths_tmp = self.ltmDataInputPaths + "MODESv2_" + mode_str + "_#MM#_monthly_ltm.nc"
                if self.patternDataName == "NCCCSM3":
                    ltmDataInputPaths_tmp = self.ltmDataInputPaths + "#MM#.nc"
                    print(ltmDataInputPaths_tmp)
                modeLtmData = ModesDataUtils.get_modes_ltm_data(ltmDataInputPaths_tmp, self.reportingTime,
                                                                foreStartTime,
                                                                foreEndTime, self.elements, start_lat, end_lat,
                                                                start_lon,
                                                                end_lon, self.patternDataName, whetherMakeup)
        # 获取BCC_CSM1.1m数据
        if self.patternDataName in ["BCCCSM11M","BCCCSM"]:
            if self.dataInputPaths:
                dataInputPaths_tmp = self.dataInputPaths +"#YYYY_MM#.nc"
                modeData = ModesDataUtils.get_bcccms11m_mean_data(dataInputPaths_tmp, self.reportingTime,
                                                              foreStartTime,
                                                              foreEndTime, self.elements, start_lat, end_lat,
                                                              start_lon,
                                                              end_lon, self.patternDataName, whetherMakeup)
            if self.ltmDataInputPaths:
                ltmDataInputPaths_tmp = self.ltmDataInputPaths +"mon_1991-2010.nc"
                modeLtmData = ModesDataUtils.get_bcccms11m_ltm_data(ltmDataInputPaths_tmp, self.reportingTime,
                                                                foreStartTime,
                                                                foreEndTime, self.elements, start_lat, end_lat,
                                                                start_lon,
                                                                end_lon, self.patternDataName, whetherMakeup)

        # 获取EC逐周数据
        if self.patternDataName == "ECWEEK":
            if self.dataInputPaths:
                dataInputPaths_tmp = self.dataInputPaths + "#YYYY#/#MM#/#YYYYMMDD#_#MMDD#.nc"
                modeData = EcWeekDataUtils.get_ecweek_mean_data(dataInputPaths_tmp, self.reportingTime, foreStartTime,
                                                        foreEndTime, self.elements, start_lat, end_lat,
                                                        start_lon,
                                                        end_lon, whetherMakeup)
            if self.ltmDataInputPaths:
                # raise AlgorithmException(response_msg="No Data : ECMWF No Data Found",response_code='9804')
                ltmDataInputPaths_tmp = self.ltmDataInputPaths + "#YYYY#/#MM#/#YYYYMMDD#_#MMDD#.nc"
                # print(ltmDataInputPaths_tmp)
                modeLtmData = EcWeekDataUtils.get_ecweek_mean_data(ltmDataInputPaths_tmp, self.reportingTime,
                                                          foreStartTime,
                                                          foreEndTime, self.elements, start_lat, end_lat,
                                                          start_lon,
                                                          end_lon, whetherMakeup)
        if self.patternDataName in ["FGOALSF", "FGOALSS2", "PCCSM4","CMMEV2"]:
            if self.dataInputPaths:
                if self.patternDataName == "FGOALSF":
                    dataInputPaths_tmp = self.dataInputPaths + self.elements+".anom.mon.fcst.6m.from.#YYYYMM#20.FGOALS-f.nc"
                if self.patternDataName == "FGOALSS2":
                    dataInputPaths_tmp = self.dataInputPaths + self.elements +".anom.mon.fcst.6m.#YYYYMM#20.FGOALS-s2.nc"
                if self.patternDataName == "PCCSM4":
                    dataInputPaths_tmp = self.dataInputPaths + self.elements +".anom.mon.fcst.6m.#YYYYMM#20.PCCSM4.nc"
                if self.patternDataName == "CMMEV2":
                    if  self.elements == "PREC_PERC":
                        dataInputPaths_tmp = self.dataInputPaths + self.elements +".anom.sea.CMME.#YYYYMM#.nc"
                    else:
                        dataInputPaths_tmp = self.dataInputPaths + self.elements +".anom.6m.CMME.#YYYYMM#.1x1.ens.nc"
                modeData = CmmeDataUtils.get_cmme_mean_data(dataInputPaths_tmp, self.reportingTime,
                                                              foreStartTime,
                                                              foreEndTime, self.elements, start_lat, end_lat,
                                                              start_lon,
                                                              end_lon, self.patternDataName,self.levels, whetherMakeup)
            if self.ltmDataInputPaths:
                if self.patternDataName == "FGOALSF":
                    ltmDataInputPaths_tmp = self.ltmDataInputPaths + self.elements+"-V1.1-#MM#20_clim.s2s_m.nc"
                if self.patternDataName == "FGOALSS2":
                    ltmDataInputPaths_tmp = self.ltmDataInputPaths + self.elements +".clim.mon.#MM#.FGOALS-s2.nc"
                if self.patternDataName == "PCCSM4":
                    ltmDataInputPaths_tmp = self.ltmDataInputPaths + self.elements +".clim.mon.#MM#20.PCCSM4.int.1x1.nc"
                if self.patternDataName == "CMMEV2":
                    ltmDataInputPaths_tmp = self.ltmDataInputPaths + self.elements +".clm.CMME.#MM#.1x1.nc"
                modeLtmData = CmmeDataUtils.get_cmme_ltm_data(ltmDataInputPaths_tmp, self.reportingTime,
                                                              foreStartTime,
                                                              foreEndTime, self.elements, start_lat, end_lat,
                                                              start_lon,
                                                              end_lon, self.patternDataName,self.levels, whetherMakeup)
        # 获取CPSV3订正数据
        if self.patternDataName in ["CPSV3DZ"]:
            if self.dataInputPaths:
                dataInputPaths_tmp = self.dataInputPaths + "#YYYY#/#MM#/#YYYYMMDD#_#HH#.nc"
                if self.dataSet == "mn" and self.patternDataName in ["CPSV3DZ"]:
                    dataInputPaths_tmp = self.dataInputPaths + "#YYYY#/#MM#/#YYYYMMDD#_mn.nc"
                    modeData = DerfDataUtils.get_cpsv3_dz_mn_mean_data(dataInputPaths_tmp, self.reportingTime,
                                                                   foreStartTime,
                                                                   foreEndTime, self.elements,
                                                                   self.station_list, whetherMakeup)
                else:
                    modeData = DerfDataUtils.get_cpsv3_dz_mean_data(dataInputPaths_tmp, self.reportingTime,
                                                                foreStartTime,
                                                                foreEndTime, self.elements,
                                                                self.station_list, whetherMakeup)
        tt2 = DateUtils.getTimeStamp()
        # logging.info("获取模式【%s】数据，耗时: %s ms" % (self.patternDataName,str(tt2 - tt1)))
        # 样本处理
        # CFSV2
        if self.patternDataName == "CFSV2":
            if self.dataSet == "mn":
                if self.ltmDataInputPaths:
                    modeLtmData = modeLtmData.mean(dim="ens")
        # DERF2
        if self.patternDataName in ["DERF2","BCC-S2S","BCCCSM12"]:
            if self.dataSet == "mn":
                if self.dataInputPaths:
                    modeData = modeData.mean(dim="ens")
                if self.ltmDataInputPaths:
                    modeLtmData = modeLtmData.mean(dim="ens")
        # ECMWF
        if self.patternDataName == "ECMWF":
            if self.dataSet == "mn":
                if self.dataInputPaths:
                    modeData = modeData.isel(ens=[0]).mean(dim="ens")
                if self.ltmDataInputPaths:
                    modeLtmData = modeLtmData.isel(ens=[0]).mean(dim="ens")
            else:
                if self.dataInputPaths:
                    modeData = modeData.isel(ens=range(1, 51))
                if self.ltmDataInputPaths:
                    modeLtmData = modeLtmData.isel(ens=range(1, 51))
        tt3 = DateUtils.getTimeStamp()
        # logging.info("获取模式【%s】样本平均，耗时: %s ms" % (self.patternDataName, str(tt3 - tt2)))
        # 数据单位处理
        if self.unitConvert:
            if self.unitConvert != "null":
                convert_type, convert_value = self.unitConvert.split("_")
                # CMME-V2 实况场不做数据单位处理
                if self.dataInputPaths and self.patternDataName != "CMMEV2":
                    modeData = fileUtils.convert_data(modeData, convert_type, convert_value)
                # CMME-V2 降水实况场数据单位处理
                if self.dataInputPaths and self.patternDataName == "CMMEV2" and self.elements in ["PREC"]:
                    modeData = fileUtils.convert_data(modeData, convert_type, convert_value)
                if self.ltmDataInputPaths:
                    modeLtmData = fileUtils.convert_data(modeLtmData, convert_type, convert_value)
        # BCC_CSM1.1m模式降水数据单位特殊处理  mm/day -> mm/mon
        # print("单位处理前：", np.nanmin(modeData), np.nanmax(modeData))
        if self.patternDataName == "BCC_CSM11M" and self.elements in ["precsfc","PREC"]:
            if self.dataInputPaths:
                mean_time_list = list(modeData.time.values)
                mean_data_list = []
                for i,tt in enumerate(mean_time_list):
                    mondays = calendar.monthrange(int(tt[0:4]),int(tt[4:]))[1]
                    mean_data_list.append(fileUtils.convert_data(modeData.isel(time=range(i,i+1)), "multiply", mondays))
                modeData = xr.concat(mean_data_list,dim="time")

            if self.ltmDataInputPaths:
                ltm_time_list = list(modeLtmData.time.values)
                ltm_data_list = []
                for i,tt in enumerate(ltm_time_list):
                    mondays = calendar.monthrange(int(tt[0:4]),int(tt[4:]))[1]
                    ltm_data_list.append(fileUtils.convert_data(modeLtmData.isel(time=range(i,i+1)), "multiply", mondays))
                modeLtmData = xr.concat(ltm_data_list,dim="time")
        # print("单位处理后：", np.nanmin(modeData),np.nanmax(modeData))
        tt4 = DateUtils.getTimeStamp()
        # logging.info("模式【%s】单位转换，耗时: %s ms" % (self.patternDataName, str(tt4 - tt3)))
        # 变温数据
        if self.stacticType and self.stacticType == "DT":
            if self.dataInputPaths:
                meanForeData_prex = modeData[:, :-1]
                meanForeData_suff = modeData[:, 1:]
                meanForeData_prex.time.values = meanForeData_suff.time.values
                modeData = meanForeData_suff - meanForeData_prex
        if self.dataInputPaths:
            data_list.append(modeData)
        if self.ltmDataInputPaths:
            data_list.append(modeLtmData)
        return data_list

    def __get_multiple_element_data(self):
        data_list = []
        # 默认不补全数据 设置False
        whetherMakeup = "False"
        if self.whetherMakeup: whetherMakeup = self.whetherMakeup
        # 解析经纬度范围
        start_lon, end_lon, start_lat, end_lat = [float(region) for region in self.regions.split(",")]
        # 解析预报的起止时间
        foreStartTime, foreEndTime = [str(forecastPeriod) for forecastPeriod in self.forecastPeriod]
        # 循环要素获取数据
        element_list = self.elements.split(",")
        levels = []
        mode_data_list = []
        mode_ltm_data_list = []
        dim = "level"
        for element in element_list:
            levels.append(float(element[1:]))
            # 获取Derf数据
            if self.patternDataName == "DERF2":
                if self.dataInputPaths:
                    dataInputPaths_tmp = self.dataInputPaths.replace(element_list[0],element) + "#YYYY#/#MM#/#YYYYMMDD#_#HH#.nc"
                    # 判断文件时存在时，调用获取数据
                    cmd = "ls "+self.dataInputPaths.replace(element_list[0],element) + self.reportingTime[0:4] + "/" + self.reportingTime[4:6]+"/" + self.reportingTime + "_*.nc"
                    if os.system(cmd) == 0:
                        modeData = DerfDataUtils.get_derf_mean_data(dataInputPaths_tmp, self.reportingTime, foreStartTime,
                                                                foreEndTime, element, start_lat, end_lat, start_lon,
                                                                end_lon, whetherMakeup)
                        # 数组扩维
                        modeData = modeData.expand_dims(dim, axis=2)
                        modeData[dim] = [float(element[1:])]
                        mode_data_list.append(modeData)
                if self.ltmDataInputPaths:
                    ltmDataInputPaths_tmp = self.ltmDataInputPaths.replace(element_list[0],element) + "#MMDD#_#HH#.nc"
                    modeLtmData = DerfDataUtils.get_derf_ltm_data(ltmDataInputPaths_tmp, self.reportingTime, foreStartTime,
                                                                  foreEndTime, element, start_lat, end_lat, start_lon,
                                                                  end_lon, whetherMakeup)
                    # 数组扩维
                    modeLtmData = modeLtmData.expand_dims(dim, axis=2)
                    modeLtmData[dim] = [float(element[1:])]
                    mode_ltm_data_list.append(modeLtmData)

        # 合并level维
        if self.dataInputPaths:
            mode_data = xr.concat(mode_data_list, dim=dim)
        if self.ltmDataInputPaths:
            mode_ltm_data = xr.concat(mode_data_list, dim=dim)

        # 对样本维求平均
        if self.dataSet == "mn":
            if self.dataInputPaths:
                mode_data = mode_data.mean(dim="ens")
            if self.ltmDataInputPaths:
                mode_ltm_data = mode_ltm_data.mean(dim="ens")
        # 数据单位处理
        if self.unitConvert:
            if self.unitConvert != "null":
                convert_type, convert_value = self.unitConvert.split("_")
                if self.dataInputPaths:
                    mode_data = fileUtils.convert_data(mode_data, convert_type, convert_value)
                if self.ltmDataInputPaths:
                    mode_ltm_data = fileUtils.convert_data(mode_ltm_data, convert_type, convert_value)
        # 结果合并
        if self.dataInputPaths:
            data_list.append(mode_data)
        if self.ltmDataInputPaths:
            data_list.append(mode_ltm_data)
        return data_list
