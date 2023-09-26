# -*- coding:utf-8 -*-
# @Time : 2021/12/07
# @Author : huxin
# @File : IndexDataOutput.py
"""
此脚本用于写入森林火险数据到GBASE数据库。
"""

from com.nriet.utils.databaseConnection.GbaseHandler import GbaseHandler
from com.nriet.utils.config.ConfigUtils import look_for_gbase_connection_config, look_for_single_global_config
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import DB_CREATE_TEMP_TABLE_ERROR_CODE, DB_CREATE_TEMP_TABLE_ERROR_MSG, \
    DB_MANIPULATE_ERROR_CODE, DATA_OUT_OF_SCALE_CODE, DB_INSERT_TEMP_TABLE_ERROR_CODE, DB_INSERT_TEMP_TABLE_ERROR_MSG, \
    DB_INSERT_PROP_TABLE_ERROR_CODE, DB_INSERT_PROP_TABLE_ERROR_MSG, DB_MANIPULATE_ERROR_MSG
from com.nriet.utils.result.ResponseResultUtils import build_response_dict

from GBaseConnector.GBaseError import DatabaseError

import hashlib
import time
import importlib, sys
import numpy as np
import logging

importlib.reload(sys)
import traceback

create_temp_data_table_template = "CREATE TEMPORARY TABLE %s LIKE %s;"
query_table_columns_template = "select COLUMN_NAME from information_schema.COLUMNS where TABLE_SCHEMA='{schema_name}' and TABLE_NAME='{table_name}';"
insert_many_sql_template = "insert into %s(%s) values(%s)"  # 操，这里不能有分号




def slhx_data_insert_or_update(insert_or_update_data_array, product_type='SLHX_MOP', save_type='DAY'):
    '''
    本方法用于森林火险数据入库GBASE，目前支持多条数据同时新增或更新
    Args:
        insert_or_update_data_array: 待写入数据。必传，维度np.array对象，维度有且只有两个维度
        product_type: 产品类型。默认为SLHX_MOP
        saveType: 保存表之时间尺度类型。默认为DAY。参考已有指数表表名即可。

    Returns:
        CIPAS通用返回结构。
    '''

    # 0. 创建Gbase连接
    result_dict = build_response_dict()
    gbase_handler = GbaseHandler(look_for_gbase_connection_config())

    try:
        # 1. 创建临时表source_table（复制数据存储表target_table的表结构）
        target_table = "_".join(("CIPAS_PRODUCT", product_type, save_type.upper()))
        source_table = '_'.join((target_table, str(int(round(time.time() * 1000)))))
        create_temp_table_result = gbase_handler.execute_write_sql(
            create_temp_data_table_template % (source_table, target_table))

        # 1.1 确定待插入数据input_data,插入到临时表会有到那些列template_columns_to_insert（主要变数在数据值列数是动态变化的）
        schema_name = look_for_single_global_config(key="GBASE_DB_NAME")
        template_columns_to_insert = gbase_handler.execute_read_sql(
            query_table_columns_template.format(schema_name=schema_name,
                                                table_name=target_table))  # 因为目标表和临时表表结构一致，直接获取全部目标表表字段，再做修改即可
        template_columns_to_insert = np.array(template_columns_to_insert).flatten().tolist()

        # 1.2 准备待插入的数据
        # 1.2.1常量数据准备
        d_iymdhm = time.strftime("%Y-%m-%d %H:%M:%S")
        d_dymdhm = time.strftime("%Y-%m-%d %H:%M:%S")

        # 1.2.2 监测/预测数据预处理,转入库格式
        if product_type =='SLHX_MOP':
            insert_or_update_data_array =build_mop_table_value_list(d_dymdhm, d_iymdhm, insert_or_update_data_array, save_type)
        elif product_type == 'SLHX_PREP':
            insert_or_update_data_array = build_prep_table_value_list(d_dymdhm, d_iymdhm, insert_or_update_data_array, save_type)
        elif product_type == 'SLHX_PTEP':
            pass


        # 1.3 写入到临时表
        insert_many_sql = insert_many_sql_template % (
        source_table, ",".join(template_columns_to_insert), ",".join(['%s'] * len(template_columns_to_insert)))
        write_many_result = gbase_handler.execute_write_many_sql(insert_many_sql_template=insert_many_sql,
                                                                 write_many_sql_params=insert_or_update_data_array)
        # 2 写入目标表 target_table
        # 2.1 临时表数据写入成功之后，直接使用 merge语法，实现有则改，无则增
        if write_many_result:
            '''
                考虑以下情况:
                    1.不同数据表的表结构
                    2.不同数据表的分区字段加密规则转换方式 √
                    3.通用的数据处理逻辑 √
            '''

            # 2.1.1 准备update_data_list以及insert_data_list
            distribute_key = "D_DATAROW_ID"

            sql_aa = "delete from {target_table} where exists (select 1 from {source_table} where {target_table}.{distribute_key}={source_table}.{distribute_key});".format(
                source_table=source_table, target_table=target_table, distribute_key=distribute_key)
            sql_bb = "insert into {target_table} select * from {source_table};".format(
                source_table=source_table, target_table=target_table)
            gbase_handler.execute_write_sql(sql_aa)
            gbase_handler.execute_write_sql(sql_bb)



        # 2.2 临时表数据写入失败,向上抛出algorithmException,交由subflowhandler处理
        else:
            raise AlgorithmException(response_code=DB_INSERT_TEMP_TABLE_ERROR_CODE,
                                     response_msg=DB_INSERT_TEMP_TABLE_ERROR_CODE % source_table)

        # 3.都冇得问题，提交事务
        gbase_handler.commit()
    except ( Exception):
        # 此次转换异常，回滚事务；向上抛出algorithmException,交由subflowhandler处理
        gbase_handler.rollback()
        logging.error("insert slhx data into gbase ,failed!")
        logging.error(traceback.format_exc())
        raise AlgorithmException(response_code=DB_MANIPULATE_ERROR_CODE, response_msg=DB_MANIPULATE_ERROR_MSG)
    finally:
        gbase_handler.close()
        del gbase_handler

    logging.info("insert slhx data into gbase ,success!")
    return result_dict

def build_mop_table_value_list(d_dymdhm, d_iymdhm, insert_or_update_data_array, save_type):
    data_size = insert_or_update_data_array.shape[0]
    begin_value_list = []
    medium_value_list = []
    v04001_list = []
    v04002_list = []
    v04003_list = []

    d_datarow_id_list = [hashlib.md5(''.join([str(insert_or_update_data_array[row_index, 0]), str(insert_or_update_data_array[row_index, 1]),
                                              str(insert_or_update_data_array[row_index, 2])]).encode(
        encoding='UTF-8')).hexdigest() for row_index in range(data_size)]
    begin_value_list.append(d_datarow_id_list)
    begin_value_list.append([d_iymdhm] * data_size)
    begin_value_list.append([d_dymdhm] * data_size)

    if save_type.upper() in ['DAY', 'FIVE', 'TEN']:
        for row_index in range(data_size):
            d_data_time = int(insert_or_update_data_array[row_index, 1])
            v04001_list.append(d_data_time // 10000)  # 年
            v04002_list.append(int(str(d_data_time)[4:6]))  # 月
            v04003_list.append(d_data_time % 100)  # 日/候/旬
        medium_value_list.append(v04001_list)
        medium_value_list.append(v04002_list)
        medium_value_list.append(v04003_list)

    elif save_type.upper() in ['MON', 'SEASON', 'FIVEYEAR']:
        for row_index in range(data_size):
            d_data_time = int(insert_or_update_data_array[row_index, 1])
            v04001_list.append(d_data_time // 100)  # 年
            v04002_list.append(d_data_time % 100)  # 月、季
        medium_value_list.append(v04001_list)
        medium_value_list.append(v04002_list)

    elif save_type.upper() == 'YEAR':
        for row_index in range(data_size):
            d_data_time = int(insert_or_update_data_array[row_index, 1])
            v04001_list.append(d_data_time)  # 年
        medium_value_list.append(v04001_list)
    else:
        pass  # 其他尺度暂不考虑
    begin_value_list = np.array(begin_value_list).T
    medium_value_list = np.array(medium_value_list).T

    insert_or_update_data_array = np.c_[begin_value_list, insert_or_update_data_array[:, :3], medium_value_list, insert_or_update_data_array[:, 3:]]
    logging.info(insert_or_update_data_array.shape)
    insert_or_update_data_array = insert_or_update_data_array.tolist()
    return insert_or_update_data_array


def build_prep_table_value_list(d_dymdhm, d_iymdhm, insert_or_update_data_array, save_type):
    data_size = insert_or_update_data_array.shape[0]
    begin_value_list = []
    medium_value_list = []
    v04001_list = []
    v04002_list = []
    v04003_list = []
    v04001_forecast_list = []
    v04002_forecast_list = []
    v04003_forecast_list = []

    d_datarow_id_list = [hashlib.md5(''.join([str(insert_or_update_data_array[row_index, 0]), str(insert_or_update_data_array[row_index, 1]),
                                              str(insert_or_update_data_array[row_index, 2]),str(insert_or_update_data_array[row_index, 3])]).encode(
        encoding='UTF-8')).hexdigest() for row_index in range(data_size)]
    begin_value_list.append(d_datarow_id_list)
    begin_value_list.append([d_iymdhm] * data_size)
    begin_value_list.append([d_dymdhm] * data_size)

    if save_type.upper() in ['DAY', 'FIVE', 'TEN']:
        for row_index in range(data_size):
            d_data_time = int(insert_or_update_data_array[row_index, 1])
            v04001_list.append(d_data_time // 10000)  # 年
            v04002_list.append(int(str(d_data_time)[4:6]))  # 月
            v04003_list.append(d_data_time % 100)  # 日/候/旬
        medium_value_list.append(v04001_list)
        medium_value_list.append(v04002_list)
        medium_value_list.append(v04003_list)

    elif save_type.upper() in ['MON', 'SEASON', 'FIVEYEAR']:
        for row_index in range(data_size):
            d_data_time = int(insert_or_update_data_array[row_index, 1])
            v04001_list.append(d_data_time // 100)  # 年
            v04002_list.append(d_data_time % 100)  # 月、季
        medium_value_list.append(v04001_list)
        medium_value_list.append(v04002_list)

    elif save_type.upper() == 'YEAR':
        for row_index in range(data_size):
            d_data_time = int(insert_or_update_data_array[row_index, 1])
            v04001_list.append(d_data_time)  # 年
        medium_value_list.append(v04001_list)
    else:
        pass  # 其他尺度暂不考虑

    if len(str(insert_or_update_data_array[0,2])) == 8:
        for row_index in range(data_size):
            date_time_forecast = int(insert_or_update_data_array[row_index,2])
            v04001_forecast_list.append(date_time_forecast // 10000)  # 年
            v04002_forecast_list.append(int(str(date_time_forecast)[4:6]))  # 月
            v04003_forecast_list.append(date_time_forecast % 100)  # 日/候/旬
    elif len(str(insert_or_update_data_array[0,2])) == 6:
        for row_index in range(data_size):
            date_time_forecast = int(insert_or_update_data_array[row_index, 2])
            v04001_forecast_list.append(date_time_forecast // 100)  # 年
            v04002_forecast_list.append(date_time_forecast % 100)  # 月/季
            v04003_forecast_list.append(999999)  # 日/候/旬
    elif len(str(insert_or_update_data_array[0,2])) == 4:
        for row_index in range(data_size):
            date_time_forecast = int(insert_or_update_data_array[row_index, 2])
            v04001_forecast_list.append(date_time_forecast)  # 年
            v04002_forecast_list.append(999999)  # 月/季
            v04003_forecast_list.append(999999)  # 日/候/旬
    medium_value_list.append(v04001_forecast_list)
    medium_value_list.append(v04002_forecast_list)
    medium_value_list.append(v04003_forecast_list)


    begin_value_list = np.array(begin_value_list).T
    medium_value_list = np.array(medium_value_list).T

    insert_or_update_data_array = np.c_[begin_value_list, insert_or_update_data_array[:, :4], medium_value_list, insert_or_update_data_array[:, 4:]]
    logging.info(insert_or_update_data_array.shape)
    insert_or_update_data_array = insert_or_update_data_array.tolist()
    return insert_or_update_data_array

if __name__ == '__main__':

    PREP_insert_or_update_data_array = np.array([['v10000', '20211201', '20211220', 'CFSV2', '0', '11.2', '25', '44', '2.5'],
                                            ['v10000', '20211201', '20211221', 'CFSV2', '0', '11.2', '25', '44', '2.5'],
                                            ['v10000', '20211201', '20211222', 'CFSV2', '0', '11.2', '25', '44', '2.5'],
                                            ['v10000', '20211201', '20211223', 'CFSV2', '0', '11.2', '25', '44', '2.5'],
                                            ['v10000', '20211201', '20211224', 'DERF2.0', '0', '11.2', '25', '44', '2.5']
                                            ])
    result_dict = slhx_data_insert_or_update(PREP_insert_or_update_data_array,product_type='SLHX_PREP',save_type='DAY')

    mop_insert_or_update_data_array = np.array([['v10000', '20211201',  'CFSV2', '0', '11.2', '25', '44', '2.5'],
                                            ['v10000', '20211202', 'CFSV2', '0', '11.2', '25', '44', '2.5'],
                                            ['v10000', '20211203', 'CFSV2', '0', '11.2', '25', '44', '2.5'],
                                            ['v10000', '20211204', 'CFSV2', '0', '11.2', '25', '44', '2.5'],
                                            ['v10000', '20211205', 'DERF2.0', '0', '11.2', '25', '44', '2.5']
                                            ])
    result_dict = slhx_data_insert_or_update(mop_insert_or_update_data_array,product_type='SLHX_MOP',save_type='DAY')


    logging.info(result_dict)