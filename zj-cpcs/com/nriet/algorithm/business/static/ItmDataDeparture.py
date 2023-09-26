#!/usr/bin/env python
# -*- coding:utf-8 -*-

import logging
from xarray import DataArray

from com.nriet.algorithm.business.BusComponent import BusComponent


class ItmDataDeparture(BusComponent):

    def __init__(self, sub_local_params, algorithm_input_data):
        """
        :param sub_local_params:流程参数，算法运算返回结果
        :param algorithm_input_data:流程数据
        """
        # 子流程算法执行产生的数据
        self.flag = True
        if len(algorithm_input_data) == 2:
            #如果传递过来的实况数据是list，则获取list里的xarray对象
            if isinstance(algorithm_input_data[0]["outputData"],list):
                self.ncData = algorithm_input_data[0]["outputData"][0]
            else:
                self.ncData = algorithm_input_data[0]["outputData"]
            # 如果传递过来的气候态数据是list，则获取list里的xarray对象
            if isinstance(algorithm_input_data[1]["outputData"],list):
                self.jpData = algorithm_input_data[1]["outputData"][0]
            else:
                self.jpData = algorithm_input_data[1]["outputData"]
            self.flag = False
        else:
            self.flow_data = algorithm_input_data[0]
            self.ncData = self.flow_data["outputData"][0]
            self.jpData = self.flow_data["outputData"][1]

        self.sub_local_params = sub_local_params
        self.output_data = None

    def execute(self):

        output_data = {}
        if self.flag:
            nc = self.ncData
            jp = self.jpData
            # 排序
            if "lat" in nc.dims:
                nc = nc.sortby("lat")
                jp = jp.sortby("lat")
        else:
            nc = self.ncData
            jp = self.jpData

        # 数据做差
        itm_data = nc - jp.values
        # 作差后的数据属性保持与源数据一致
        itm_data.attrs = nc.attrs
        # if element == "subsst":
        #     self.ncData[element] = nc - jp[:, :, ::-1].values
        # else:
        #     self.ncData[element] = nc[element] - jp[element].values
        output_data["outputData"] = itm_data
        # output_data["ncData"] = self.ncData
        self.output_data = output_data

if __name__ == '__main__':
    algorithm_input_data = []
    input_data = [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]]
    input_data2 = [[2, 3, 4, 5, 6], [6, 7, 8, 9, 10]]
    dims = ["time", "value"]
    input_data = DataArray(input_data, dims=dims)
    input_data2 = DataArray(input_data2, dims=dims)
    out_put_data = {"outputData": input_data}
    out_put_data2 = {"outputData": input_data2}
    algorithm_input_data.append(out_put_data)
    algorithm_input_data.append(out_put_data2)
    sub_local_params = {}
    dd = ItmDataDeparture(sub_local_params,algorithm_input_data)
    dd.execute()
    logging.info(dd.output_data)


