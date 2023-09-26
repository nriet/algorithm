#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/08/21
# @Author : JiangP
# @File : Correlation.py

import xarray as xr
import logging
import os
from com.nriet.algorithm.business.BusComponent import BusComponent
from com.nriet.config.ResponseCodeAndMsgEum import FILE_NOT_FOUND_ERROR_CODE
from com.nriet.utils.exception.workFlow.WorkFlowException import WorkFlowException
import traceback
class BcccsmConvert(BusComponent):
    def __init__(self, sub_local_params, algorithm_iuput_data):
    # def __init__(self,):
        # self.flow_data = algorithm_iuput_data
        self.flow_data = []
        self.inputPaths = sub_local_params.get("dataInputPaths")
        self.elements = sub_local_params.get("elements")
        self.vardicts = dict(sub_local_params.get("vars"))  # 原始数据变量与规整后的数据字典对应
        if self.elements in self.vardicts.keys():
            self.outVar = self.vardicts[self.elements]
        else:
            logging.error(traceback.format_exc())
            raise WorkFlowException(response_code=FILE_NOT_FOUND_ERROR_CODE, response_msg="%s 要素未配置 !!" % self.elements)
        self.fn = ["","p01","p02","p03"]
        self.name = ["01", "02", "03", "04"]
        self.outPath = sub_local_params.get("outPath")
        self.level = [100,200,500,700,850,925,1000]
        # self.level = [100,200]
        timeRange = sub_local_params.get("timeRanges")
        self.startTime = str(timeRange[0])
        self.oringinalePath = self.inputPaths  + self.startTime + ""
        # logging.info(self.flow_data)
        # self.inputData = self.flow_data
        # self.formulaCoefficient = sub_local_params.get("formulaCoefficient")
        # self.reportingTime = sub_local_params.get("reportingTime")
        # self.forecastPeriod = sub_local_params.get("forecastPeriod")
        # self.timeType = sub_local_params.get("timeType")
        self.output_data = None

    def writedata(self,outPath,var,data):
        if os.path.exists(outPath):
            os.remove(outPath)
        path = '/'.join(outPath.split('/')[:-1])
        if not os.path.exists(path):
            os.makedirs(path)
        encoding = {var: {'dtype': 'float32', '_FillValue': 999999.},
                    'time': {'dtype': 'int32'}}
        data = xr.Dataset({var: data})
        #nc数据有问题，生成的数据就有问题，还得删掉，不然下面算集合平均的时候会报错
        try:
            data.to_netcdf(outPath, encoding=encoding)
        except TypeError:
            logging.info("%s TypeError!" % outPath)
            logging.info(data.time.values)
            os.remove(outPath)
        except OverflowError:
            logging.info("%s OverflowError!" % outPath)
            logging.info(data.time.values)
            os.remove(outPath)
        # logging.info("%s is OK!"%outPath)
        return 0

    def _calmn(self,dataPath,var):
        tmp_path = "/".join(dataPath.split("/")[:-1])
        all_path = [tmp_path + "/" + self.startTime + "_" + name + ".nc" for name in self.name]
        result_data_list = []
        real_path = [path for path in all_path if os.path.exists(path)]
        if len(real_path) == len(all_path):
            for i,path in enumerate(all_path):
                # print(path)
                ds = xr.open_dataset(path)
                data = ds[var]
                # 扩展样本维
                year_data = data.expand_dims('mn')
                year_data['mn'] = [i]
                result_data_list.append(year_data)
            # 将年份维合并
            result_data = xr.concat(result_data_list, dim='mn')
            # 对年份维求平均
            res_data = result_data.mean(dim='mn', keep_attrs=True)
            self.writedata(tmp_path+"/"+self.startTime + "_mn.nc",var,res_data)
            return True
        else:
            # logging.info("[%s]样本不全，不能计算集合平均"%var)
            return False

    def execute(self):
        res_dict = {}
        res_dict["file_num"] = 0
        flag = True
        for inp,p in enumerate(self.fn):
            path = self.oringinalePath + "/daily_bcccsm_" + self.startTime + "00" + p + "_" +self.elements +".nc"
            try:
                tmp = xr.open_dataset(path)[self.elements][:]
            except IOError:
                res_dict["response_msg"] = 'File: %s cannot be found'%path
                res_dict["file_num"] = 0
                logging.error(res_dict)
                flag = False
                continue
            if len(tmp.shape) == 3:
                ds = xr.DataArray(tmp, coords=[tmp['time'], tmp['latitude'], tmp['longitude']],
                                  dims=['time', 'lat', 'lon'])
                if self.outVar == "prate":
                    ds *= 86400*1000  #单位转换，不知道对不对
                    ds.attrs['units'] = "mm/day"
                    # logging.info(ds.max(),ds.min())
                outPath = self.outPath + self.outVar + "/day/" + self.startTime[:4] + "/" \
                          + self.startTime[4:6] + "/" + self.startTime + "_" + self.name[inp] + ".nc"
                self.writedata(outPath, self.outVar, ds)
                res_dict["file_num"] += 1
                if inp == 3:
                    flag = self._calmn(outPath,self.outVar)
                    if flag:
                        res_dict["file_num"] += 1
            else:
                ds = xr.DataArray(tmp, coords=[tmp['time'], tmp['level'], tmp['latitude'], tmp['longitude']],
                                  dims=['time', 'level', 'lat', 'lon'])
                levels = list(ds.level.values)
                for l in self.level:
                    outPath = self.outPath+self.outVar+str(l)+"/day/"+self.startTime[:4]+"/"\
                              +self.startTime[4:6]+"/"+self.startTime+"_"+self.name[inp]+".nc"
                    data = ds[:,levels.index(l),...]
                    self.writedata(outPath,self.outVar+str(l),data)
                    res_dict["file_num"] += 1
                    if inp == 3:
                        flag = self._calmn(outPath, self.outVar + str(l))
                        if flag:
                            res_dict["file_num"] += 1
        if flag:
            res_dict["response_code"] = "0000"
        else:
            res_dict["response_code"] = "-9999"
            res_dict["response_msg"] = "[%s]要素[%s]日期的源文件全部缺失"%(self.elements,self.startTime)
            # logging.error("%s 数据异常!" % (self.elements))
        return res_dict
        # else:

if __name__ == "__main__":
    sub_local_params = {
        "dataInputPaths":"/nfsshare1/cdbdata/ftpdata/BCCCSM_S2S/",
        "elements": "V",
        "vars": {
            "TREFHT": "tmp",
            "PRECT": "prate",
        },
        "outPath":"/nfsshare1/cdbdata/data/BCC_CPSv3/",
        "timeRanges":[20220501,20220501]
    }
    algorithm_iuput_data = []
    tmp = BcccsmConvert(sub_local_params,algorithm_iuput_data)
    tmp.execute()