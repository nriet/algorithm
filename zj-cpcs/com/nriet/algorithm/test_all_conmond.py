#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/03/16

import os
import sys
import pandas as pd
import threading,logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))))
p = r'python /usr/local/src/JiangP/com/nriet/algorithm/business/MonthlyForecastDataTcc.py '
p = r'python /usr/local/src/JiangP/com/nriet/core/MainEntrance.py '

class MyThreading(threading.Thread):
    def __init__(self,func,*args,**kwargs):
        super(MyThreading,self).__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self,*args,**kwargs):
        self.func(*self.args,**self.kwargs)

def read_conmond(path=r'/usr/local/src/JiangP/sea_commands.txt'):
    tmp = pd.read_csv(path,header=None,sep=' ')
    tm = []
    for i in range(tmp.shape[0]):
        tm.append(tmp.loc[i,:])
    return tm

def my_fun(comand):
    # logging.info('[' + comand + ' begin]')
    ret = os.system(comand)
    if ret == 0:
        logging.error('[' + comand + ' success]')
    else:
        logging.info('[' + comand + ' fail]')
    # logging.info('[' + comand + ' end]')
if __name__ == "__main__":
    # tmps = read_conmond()
    # tmps = read_conmond(r'/usr/local/src/JiangP/sea_commands_fore.txt')
    tmps = read_conmond(r'/usr/local/src/JiangP/test_DQHL.txt')
    # logging.basicConfig(filemode = 'w',filename='/usr/local/src/JiangP/info.log',level=logging.INFO,
    #                     format='%(asctime)s - %(name)s -%(levelname)s - %(message)s')
    for tmp in tmps:
        if "".join(tmp.values).__contains__("mon"):
            for year in range(1961,2021):
                tmp_comand = p + "".join((tmp.values)) + ""
                os.system(tmp_comand.replace("#SE", str(year)+"01").replace("#EE", str(year)+"12"))
        if "".join(tmp.values).__contains__("day"):
            for year in range(1961,2021):
                tmp_comand = p + "".join((tmp.values)) + ""
                os.system(tmp_comand.replace("#SE", str(year)+"0101").replace("#EE", str(year)+"1231"))
        if "".join(tmp.values).__contains__("year"):
            tmp_comand = p + "".join((tmp.values)) + ""
            os.system(tmp_comand.replace("#SE", "1951").replace("#EE", "2020"))
        if "".join(tmp.values).__contains__("FIVE"):
            for year in range(1961, 2021):
                tmp_comand = p + "".join((tmp.values)) + ""
                os.system(tmp_comand.replace("#SE", str(year) + "0101").replace("#EE", str(year) + "1231"))







    # tmpconmond = '{"ltm_mode":"","monitor_mode":"CRA1P00_surface","forecast_mode":"BCC_CSM1.1m","monitor_elements":"precip","forecast_elements":"prate","timeType":"mon","leadingTime":["#LM"], "yearTimeRange":["#MM1","#MM2"],"level":"","areaCode":"第三极地区","regions":"0,150,0,90","draw_regions":"65,105,25,50","yearRange":[1991,2020],"areaName":"THIRDAREA"}'
    # tmpconmond = '{"ltm_mode":"","monitor_mode":"CPC","forecast_mode":"BCC_CSM1.1m","monitor_elements":"precip","forecast_elements":"prate","timeType":"mon","leadingTime":["#LM"], "yearTimeRange":["#MM1","#MM2"],"level":"","areaCode":"第三极地区","regions":"0,150,0,90","draw_regions":"65,105,25,50","yearRange":[1991,2020],"areaName":"THIRDAREA"}'
    # logging.basicConfig(filemode = 'w',filename='/usr/local/src/jiangP/info_monitor.log',level=logging.INFO,format='%(asctime)s - %(name)s -%(levelname)s - %(message)s')
    # tmpconmond = '{"ltm_mode":"","monitor_mode":"CRA1P00_surface","forecast_mode":"BCC_CSM1.1m","monitor_elements":"air_2m","forecast_elements":"tmp","timeType":"mon","leadingTime":["#LM"], "yearTimeRange":["#MM1","#MM2"],"level":"","areaCode":"第三极地区","regions":"0,150,0,90","draw_regions":"65,105,25,50","yearRange":[1991,2020],"areaName":"THIRDAREA"}'
    #
    # mon = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    # mon3 = ["12", "01", "02", "03", "04", "05", "06", "07", "08", "09"]  # 对应秋季
    # mon2 = ["09", "10", "11", "12", "01", "02", "03", "04", "05", "06"]  # 对应夏季
    # mon1 = ["06", "07", "08", "09", "10", "11", "12", "01", "02", "03", ]  # 对应春季
    # mon4 = ["03", "04", "05", "06", "07", "08", "09", "10", "11", "12", ]  # 对应冬季
    # mons = [mon1, mon2, mon3, mon4]
    # # season1 = [["12", "02"], ["03", "05"], ["06", "08"], ["09", "11"]]
    # season = [["03", "05"], ["06", "08"], ["09", "11"], ["12", "02"]]
    # for mo in mon:
    #     for s in mon:
    #         command = tmpconmond.replace("#LM", s).replace("#MM1", mo).replace("#MM2", mo)
    #         tmp_comand = p + " '" + command + "'"
    #         # print(tmp_comand)
    #         os.system(tmp_comand)
    # for index, m in enumerate(season):
    #     mon = mons[index]
    #     for s in mon:
    #         command = tmpconmond.replace("#LM", s).replace("#MM1", m[0]).replace("#MM2", m[1])
    #         tmp_comand = p + " '" + command + "'"
    #         # print(tmp_comand)
    #         os.system(tmp_comand)
    #         # exit()
    #         # logging.info('[' + comand + ' end]')
    #         '''并行'''
        #     t = MyThreading(my_fun,tmp_comand)
        #     t.start()
        #
        # t.join()

# timeList = get_time_list([20201101, 20201124],"day")
    # for command in tmps:
    #     logging.info('[' + command + ' begin]')
    #     for t in timeList:
    #         time.sleep(0.1)
    #         st = time_increase(strToDate(t, "%Y%m%d"),1)
    #         et = time_increase(strToDate(t, "%Y%m%d"),44)
    #         # tmp_comand = p+ " \""+"".join((command.values))+"\""
    #         tmp_comand = p+ " "+"".join((command.values))+""
    #         comand = tmp_comand.replace("#YYYYMMDD#",str(t)).replace("#SS#",st).replace("#EE#",et)
    #         '''串行'''
    #         logging.info(comand)
    #         os.system(comand)
    #     logging.info('[' + command + ' end]')
    #     '''并行'''
    #     # t = MyThreading(my_fun,comand)
    #     # t.start()