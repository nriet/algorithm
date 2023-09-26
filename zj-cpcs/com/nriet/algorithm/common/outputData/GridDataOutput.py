# -*- coding:utf-8 -*-
# @Time : 2020/10/14
# @Author : huxin
# @File : GridDataOutput.py
"""
此脚本用于写入格点数据到格点空间数据库。
"""

from ctypes import *
import numpy as np
from com.nriet.algorithm.common.outputData.OutputDataComponent import OutputDataComponent
from com.nriet.config.ResponseCodeAndMsgEum import LACK_OF_DATA_TO_INSERT_CODE,LACK_OF_DATA_TO_INSERT_MSG
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.utils.result.ResponseResultUtils import build_response_dict
import copy,logging
from com.nriet.config.ThirdPartyConfig import GRID_DATA_WRITE_SO
from com.nriet.utils.decorator.DIDecorator import DI_decorater
class GridDataOutput(OutputDataComponent):

    def __init__(self, sub_local_params, algorithm_input_data):
        """
        :param sub_local_params:流程参数，算法运算返回结果
        :param algorithm_input_data:流程数据,待录入数据是DataArray形式：
                至多（time,ensNo,validTime,level,lat,lon）顺序一致的6维；
                里边包含至多1个待录入要素；
                更多细节详见《气象局空间库服务接口文档20200831》：https://docs.qq.com/doc/DU0RhUEtRTWtzWU1n 的4.1章节
        """
        # 待录入数据的数据编码、表名称
        self.data_code = sub_local_params.get('data_code')
        self.table_name = None
        '''待录入数据的时间尺度
        监测数据：
            timeType：可填FIVE PEN TEN MON SEA YER HH。缺省为DAY。
            validTimeType: json中不要有这个字段参数
        预测数据:
            timeType：起报时间的时间尺度。可填FIVE PEN TEN MON SEA YER HH。缺省为DAY。
            validTimeType: 预报时效的时间尺度。可填FIVE PEN TEN MON SEA YER HH。缺省为DAY。
        '''
        self.timeType = str.upper(sub_local_params.get('timeType','DAY'))
        self.validTimeType = str.upper(sub_local_params.get('validTimeType','DAY'))

        # 待录入数据
        if isinstance(algorithm_input_data[0]["outputData"],list):
            self.input_data = algorithm_input_data[0]["outputData"]
        else:
            self.input_data = [algorithm_input_data[0]["outputData"]]

        self.output_data = None

        '''
        单个要素条数计算公式：
            监测数据：factor_norm_num = 时间*高度（深度）,高度（深度）维没有时，值取1
            预测数据：factor_norm_num = 起报时间*样本*预报时效*高度（深度）,同理如若入库数据没有指定维度，那么该维度值取1
        数据总条数计算公式：
            norm_num = sum(factor_norm_num)
        '''
        self.norm_num = int(sub_local_params.get('norm_num')) # 定时任务触发时，该类数据理论上应该录入总条数
        self.norm_actual_num = 0 # 定时任务触发时，实际到达数据总条数。因为可能数据只到了一部分。这个是空间库接口返回的结果之和计算得来。
        self.actual_num = 0  # 定时任务触发时，真实入库总条数
        self.reportingTime = sub_local_params.get('reportingTime')
        self.timeRanges = sub_local_params.get('timeRanges')

    @DI_decorater("GridDataProduct")
    def execute(self):

        class InsertTrackLogEntity(object):
            def __init__(self, norm_num):
                self.track_log_dict = {}
                self.norm_num = norm_num

            def __str__(self):
                arrive_num, insert_num = self.get_arrive_and_insert_num()
                should_insert_num_str = "\t\t\t\tIt should insert num is: %s ," % self.norm_num
                arrive_num_str = "total arrive num is: %s ," % arrive_num
                insert_num_str = "total insert num is: %s .\n" % insert_num
                total_information_str = ''.join([should_insert_num_str,arrive_num_str,insert_num_str])
                special_information_str = "\t\t\t\tEach insert information: %s" % self.track_log_dict.__str__()
                return total_information_str+special_information_str

            def get_arrive_and_insert_num(self):
                norm_and_actual_list = np.array(list(self.track_log_dict.values()))
                arrive_num = sum(norm_and_actual_list[:,0])
                insert_num = sum(norm_and_actual_list[:,1])
                return arrive_num, insert_num

            def add_track(self,factor_name,factor_norm_num,factor_actual_num):
                self.track_log_dict[factor_name] = [factor_norm_num,factor_actual_num]

        insert_track_log_entity = InsertTrackLogEntity(self.norm_num)

        if not self.input_data:
            logging.info("             Nothing to insert into Grid dataBase!!")
            raise AlgorithmException(response_code=LACK_OF_DATA_TO_INSERT_CODE,response_msg=LACK_OF_DATA_TO_INSERT_MSG)

        for grid_data_to_write in self.input_data:

            # 0.time维转int数值类型
            time_values = list(grid_data_to_write["time"])
            grid_data_to_write["time"] = [int(time) for time in time_values]

            # logging.info(grid_data_to_write)
            # 1.加载格点写入接口
            library_instance = cdll.LoadLibrary
            grid_data_write_fuc = library_instance(GRID_DATA_WRITE_SO)


            # 2.入参准备
            data_type = 10
            data_type = (c_int)(data_type)
            data_code = self.data_code.encode()

            # 2.1 重组table_name,把要素名称插入到data_code的倒数第二段
            data_code_segments = self.data_code.split("_")
            factor_segment = str(copy.deepcopy(grid_data_to_write.name)).upper()
            data_code_segments.insert(-1,factor_segment)
            self.table_name = "_".join(data_code_segments)
            table_name = self.table_name.encode()

            grid_data_bytes, grid_data_element_name, grid_data_size, number_of_ens_no, number_of_lat, number_of_level, number_of_lon, number_of_pre_time, number_of_time = \
                self.build_gird_data_to_write_params(grid_data_to_write)

            # 3.输入数据的时间尺度（或起报时间的时间尺度）、输入数据的预报时效的时间尺度
            timeType = self.timeType.encode()
            validTimeType = self.validTimeType.encode()

            # 4.调用写入方法写入数据
            logging.info("             call InsertNcDataToPG to insert grid data!")
            # logging.info(data_code)
            # logging.info(table_name)
            # logging.info(data_type)
            # logging.info(number_of_time)
            # logging.info(number_of_pre_time)
            # logging.info(number_of_ens_no)
            # logging.info(number_of_level)
            # logging.info(number_of_lat)
            # logging.info(number_of_lon)
            # logging.info(timeType)
            # logging.info(validTimeType)
            grid_data_write_fuc.InsertNcDataToPG.restype = c_char_p
            insert_result = grid_data_write_fuc.InsertNcDataToPG(grid_data_bytes, grid_data_size, grid_data_element_name, data_code, table_name,
                                                 data_type, number_of_time, number_of_pre_time, number_of_ens_no,
                                                 number_of_level, number_of_lat, number_of_lon,timeType,validTimeType)
            insert_result = eval(insert_result)
            #5 记录录入情况
            insert_track_log_entity.add_track(copy.deepcopy(grid_data_to_write.name),insert_result.get('normNum', 0), insert_result.get('actualNum', 0))

        # 6 打印记录情况，并记录到DI字段内去
        # insert_track_log_entity.add_track('tmp','5124','5124') #测试用
        self.factor_info = insert_track_log_entity.track_log_dict
        logging.info(insert_track_log_entity)
        arrive_num, insert_num = insert_track_log_entity.get_arrive_and_insert_num()
        # arrive_num, insert_num = 5124,5124 #测试用
        self.norm_actual_num = arrive_num
        self.actual_num = insert_num

        return build_response_dict()

    def build_gird_data_to_write_params(self, grid_data_to_write):
        '''
        构造格点写入接口入参
        :param grid_data_to_write: 待写入格点数据，为DataArray对象
        :return:
            grid_data_bytes : （DataSet对象 or nc文件对象）转换后的二进制流，bytes类型
            grid_data_element_name : 待录入格点数据的要素名称
            grid_data_size : 待录入格点数据的字节长度值
            number_of_ens_no : 待录入数格点数据的样本个数维度值，无为0
            number_of_lat : 待录入数格点数据的纬度维度值
            number_of_level : 待录入数格点数据的level维度值，无为0
            number_of_lon : 待录入数格点数据的经度维度值
            number_of_pre_time ： 待录入格点数据的预报时效维度值，无为0
            number_of_time：待录入格点数据的起报时段（或者时间）维度值
        '''

        shape_dict = copy.deepcopy(grid_data_to_write.sizes.mapping)
        # logging.info(shape_dict)
        number_of_time = (c_int)(shape_dict.get('time', 0))
        number_of_pre_time = (c_int)(shape_dict.get('validTime', 0))
        number_of_ens_no = (c_int)(shape_dict.get('ensNo', 0))
        number_of_level = (c_int)(shape_dict.get('level', 0))
        number_of_lat = (c_int)(shape_dict.get('lat', 0))
        number_of_lon = (c_int)(shape_dict.get('lon', 0))

        grid_data_element_name = copy.deepcopy(grid_data_to_write.name).encode()
        # grid_data_element_name = "precip".encode()
        logging.info(grid_data_element_name)
        data_bytes = grid_data_to_write.to_dataset().to_netcdf(format="NETCDF3_CLASSIC")
        size = len(data_bytes)
        grid_data_bytes = (c_byte * size)(*data_bytes)
        grid_data_size = (c_int)(size)
        return grid_data_bytes, grid_data_element_name, grid_data_size, number_of_ens_no, number_of_lat, number_of_level, number_of_lon, number_of_pre_time, number_of_time

