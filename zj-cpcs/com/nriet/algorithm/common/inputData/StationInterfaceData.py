# -*- coding:utf-8 -*-
# @Time : 2020/09/01
# @Author : huxin
# @File : StationInterfaceData.py

import requests
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.algorithm.common.inputData.InputDataComponent import InputDataComponent
from com.nriet.utils.decorator.TimerDecorator import timer_with_param
from urllib.parse import urlencode
from uuid import uuid4
from time import time
import traceback
import pandas as pd
import numpy as np
import xarray as xr
import logging

baseUrl = "http://10.40.17.54/music-ws/api?" \
          "serviceNodeId=NMIC_MUSIC_CMADAAS&" \
          "userId=USR_LIUBEI&" \
          "pwd=Cipas1234!@#$&" \
          "dataFormat=json&" \

class StationInterfaceData(InputDataComponent):


    def __init__(self, sub_local_params, algorithm_input_data):
        """
        :param sub_local_params:流程参数，算法运算返回结果
        :param algorithm_input_data:流程数据
        """
        # 1.CIMISS 数据接口地址
        self.baseUrl = baseUrl
        self.args = sub_local_params.copy()

        # 2.请求随机参数拼接
        self.args['timestamp'] = int(round(time() * 1000))
        self.args['nonce'] = uuid4().__str__()

        # 3.入参预处理(暂无)

        # 4.组装interface_url信息
        self.interface_url = urlencode(self.args)

    @timer_with_param("          get station data by interface") #注解。计算调用站点算法耗时，单位：秒
    def execute(self):
        outputData = {}
        data_list = []

        # 1.调用CIMISS站点数据读取接口获取站点数据
        station_data = self.query_data_by_interface()

        try:
            # 2 CIPAS业务化处理
            # 2.1尝试获取具体的站点数据，并转换为Pandas库中的DataFrame数据结构
            DS = eval(station_data.content)['DS']
            df = pd.DataFrame(DS)

            for column in df.columns.tolist():
                df[column] = pd.to_numeric(df[column])

            # 2.2得到站号，一维数组
            stations = np.array(df['Station_Id_d'])

            # 2.3站点文件，相当于原来的txt
            station_info = np.array(df[['Station_Id_d','Lat','Lon']])

            # 2.4数据文件，相当于原来的nc
            web_data = np.array(df.drop(['Station_Id_d','Lat', 'Lon'], axis=1))

            # 2.5截取站点数据
            station_data = xr.DataArray(web_data.flatten(), coords=[stations], dims=["station"],name='rain')
            station_data = xr.where(station_data >= 999999.0, np.nan, station_data)

            # 2.6 返回站点信息数据
            station_info_data = xr.DataArray(station_info, coords=[stations, ['station', 'lat', 'lon']], dims=['station', 'space'])
            station_info_data = xr.where(station_info_data >= 999999.0, np.nan, station_info_data)


        except Exception :
            logging.error(traceback.format_exc())
            raise AlgorithmException(response_msg=eval(station_data.content)['returnMessage'])

        # 3.数据结果保存至临时队列，交予下游处理
        data_list.append(station_data)
        data_list.append(station_info_data)
        outputData["outputData"] = data_list
        self.output_data = outputData


    def query_data_by_interface(self):
        logging.info("              " + self.baseUrl + self.interface_url)
        logging.info("              " + self.args.__str__())
        data = requests.get(self.baseUrl + self.interface_url)
        return data

if __name__ == '__main__':
    # "interfaceId=getSurfEleByTime&" \
    # "dataCode=SURF_GLB_MUL_DAY&" \
    # "elements=Year,Mon,Day,Station_Id_C,Station_Id_d,Lat,Lon,TEM_Avg,PRE_24h&" \
    # "times=20200902000000&" \
    # "timestamp=%s&" \
    # "nonce=%s"

    sub_local_params={
        'interfaceId':'getSurfEleByTime'
        ,'dataCode':'SURF_GLB_MUL_DAY'
        ,'elements':'Station_Id_d,Lat,Lon,TEM_Avg'
        ,'times':'20200831000000'

    }
    sid = StationInterfaceData(sub_local_params,None)

    try:
        sid.execute()
    except AlgorithmException as e:
        logging.info(e.__str__())
