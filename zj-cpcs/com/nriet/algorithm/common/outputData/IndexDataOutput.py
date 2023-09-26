# -*- coding:utf-8 -*-
# @Time : 2020/10/21
# @Author : huxin
# @File : IndexDataOutput.py
"""
此脚本用于写入指数数据到GBASE数据库。
"""
from com.nriet.algorithm.common.outputData.OutputDataComponent import OutputDataComponent
from com.nriet.utils.databaseConnection.GbaseHandler import GbaseHandler
from com.nriet.utils.config.ConfigUtils import look_for_gbase_connection_config, look_for_single_global_config
from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
from com.nriet.config.ResponseCodeAndMsgEum import DB_CREATE_TEMP_TABLE_ERROR_CODE, DB_CREATE_TEMP_TABLE_ERROR_MSG, \
    DB_MANIPULATE_ERROR_CODE, DATA_OUT_OF_SCALE_CODE,DB_INSERT_TEMP_TABLE_ERROR_CODE,DB_INSERT_TEMP_TABLE_ERROR_MSG,DB_INSERT_PROP_TABLE_ERROR_CODE,DB_INSERT_PROP_TABLE_ERROR_MSG,DB_MANIPULATE_ERROR_MSG
from com.nriet.utils.result.ResponseResultUtils import build_response_dict
from com.nriet.utils.MathUtils import formatting_data
from com.nriet.utils.DateUtils import get_time_list
from GBaseConnector.GBaseError import DatabaseError
from com.nriet.utils.decorator.DIDecorator import DI_decorater
import hashlib
import time,copy
import importlib, sys
import numpy as np
import pandas as pd
import xarray as xr
import logging
importlib.reload(sys)
import traceback
query_product_type_sql_template = "SELECT productType FROM CIPAS_PRODUCT WHERE productId='{productId}' AND  productName= '{productName}';"
create_temp_data_table_template = "CREATE TEMPORARY TABLE %s LIKE %s;"
query_table_columns_template = "select COLUMN_NAME from information_schema.COLUMNS where TABLE_SCHEMA='{schema_name}' and TABLE_NAME='{table_name}';"
insert_many_sql_template ="insert into %s(%s) values(%s)" # 操，这里不能有分号



class IndexDataOutput(OutputDataComponent):

    def __init__(self, sub_local_params, algorithm_input_data):
        """
        :param sub_local_params:流程参数
        :param algorithm_input_data:流程数据
        """

        # 指数产品类参数
        self.productId = sub_local_params.get("productId")
        self.productName = sub_local_params.get("productName")
        self.productType = sub_local_params.get("productType")
        self.busType = sub_local_params.get("busType")

        # 指数产品数据检索类参数
        self.elements = sub_local_params.get("elements")
        if not self.elements:
            self.elements='999999'

        self.dataSource = sub_local_params.get("dataSource",'999999')
        self.areaCode = sub_local_params.get("areaCode",'999999')
        self.level = sub_local_params.get("level",'999999')
        self.time_ranges = sub_local_params.get("timeRanges")
        self.forecastTime = sub_local_params.get("reportingTime")
        self.method = sub_local_params.get("method")

        # 补充DI中的timeRanges字段
        self.timeRanges = [self.forecastTime,self.forecastTime] if self.forecastTime  else sub_local_params.get("timeRanges")


        self.forecastPeriod = sub_local_params.get("forecastPeriod")

        self.data_type = sub_local_params.get("data_type")
        self.product_normal_num = sub_local_params.get("product_normal_num",1) # 默认为1

        # 待录入数据
        if len(algorithm_input_data) > 1:  # 多个数据合并成1个
            self.convert_data(algorithm_input_data)
        else:
            self.input_data = algorithm_input_data[0]["outputData"]
        # 处理待录入数据第一维不是"time"时，需要对数据进行转置
        if self.input_data.dims[0] !="time":
            self.input_data = self.input_data.T

        # 其他参数
        self.timeType = sub_local_params.get("timeType") # 原始数据的时间尺度
        self.DBtimeType = sub_local_params.get("DBtimeType")  # 强制控制存于那张指数表
        self.indexTimeType = sub_local_params.get("indexTimeType")  # 强制申明指数是什么尺度的指数
        self.productTitle = sub_local_params.get("indexTitle")
        self.format = sub_local_params.get("format")
        self.saveType = sub_local_params.get("saveType")
        # 监测指数和检验指数入库 time_ranges为空的特殊处理
        if self.productType == "INDEX_MOP":
            if not self.time_ranges:
                data_time_list = list(self.input_data.time.values)
                self.time_ranges = [data_time_list[0], data_time_list[-1]]
        # 预测指数入库 time_ranges为空的特殊处理
        elif self.productType == "INDEX_PREP":
            if not self.forecastPeriod:
                data_time_list = list(self.input_data.time.values)
                self.forecastPeriod = [data_time_list[0], data_time_list[-1]]
        # 检验指数入库 更新self.forecastPeriod值
        elif self.productType == "INDEX_PTEP":
            data_time_list = list(self.input_data.time.values)
            self.forecastPeriod = data_time_list

        # 结果数据
        self.output_data = None

    @DI_decorater("IndexProduct")
    def execute(self):
        # 0.创建Gbase连接
        result_dict = build_response_dict()
        gbase_handler = GbaseHandler(look_for_gbase_connection_config())

        try:
            # # 1.查询有无此类产品(依据是：是否返回productType(产品类型))
            # query_product_type_sql = query_product_type_sql_template.format(productId=self.productId, productName=self.productName)
            # query_product_type = gbase_handler.execute_read_sql(query_product_type_sql)
            #
            # if len(query_product_type) == 0:
            #     # 1.1 没有productType(新建此条产品)
            #     params = {"productId": self.productId, "productName": self.productName, "productType": self.productType,"productTitle":self.productTitle}
            #     if self.busType:
            #         params.update({"busType": self.busType})
            #     product_insert_sql = self.build_common_insert_sql(table_name="CIPAS_PRODUCT", params=params)
            #     product_insert_result = gbase_handler.execute_write_sql(sql_str=product_insert_sql)
            #     if product_insert_result:
            #         logging.info("Product insert success!")
            #     else:
            #         raise AlgorithmException(response_code=DB_INSERT_PROP_TABLE_ERROR_CODE,
            #                                  response_msg=DB_INSERT_PROP_TABLE_ERROR_MSG % "CIPAS_PRODUCT")

            # 1.2 有productType，创建临时表（连接一断，临时表随即删除；处于不同连接时临时表不共享）
            query_product_type = self.productType

            time_type = self.timeType
            db_time_type = self.DBtimeType

            # 1.2.1 确定存储类型(用于确定数据到底该存到哪张表)
            save_type =  db_time_type if db_time_type else time_type

            # 1.2.2 创建临时表source_table（复制数据存储表target_table的表结构）
            # target_table = "_".join(("CIPAS_PRODUCT",query_product_type,str(save_type).upper()))
            target_table = "_".join(("SEVP_CIPAS_GLB",query_product_type,str(save_type).upper(),"TAB"))
            source_table = '_'.join((target_table, str(int(round(time.time() * 1000)))))
            create_temp_table_result = gbase_handler.execute_write_sql(
                create_temp_data_table_template % (source_table, target_table))

            # if not create_temp_table_result: #创建失败则抛出异常  此处返回0，故注释掉这段代码
            #     raise AlgorithmException(response_code=DB_CREATE_TEMP_TABLE_ERROR_CODE,
            #                              response_msg=DB_CREATE_TEMP_TABLE_ERROR_MSG % source_table)


            # 2 将待插入数据保存至临时表内
            # 2.1 确定待插入数据input_data维度，得到data_columns, data_rows（可能是只有1列数据，也有可能会是多列数据）这里只做一列存储！！！
            input_data = self.input_data.values
            data_columns, data_rows,input_data = self.convert_input_data_shape(input_data,self.saveType,self.format)

            # 2.2 确定待插入数据input_data,插入到临时表会有到那些列template_columns_to_insert（主要变数在数据值列数是动态变化的）
            schema_name = look_for_single_global_config(key="GBASE_DB_NAME")
            template_columns_to_insert = gbase_handler.execute_read_sql(
                query_table_columns_template.format(schema_name=schema_name, table_name=target_table)) #因为目标表和临时表表结构一致，直接获取全部目标表表字段，再做修改即可
            template_columns_to_insert = np.array(template_columns_to_insert).flatten().tolist()
            # 剔除 D_UPDATE_TIME 列
            if "D_UPDATE_TIME" in template_columns_to_insert:
                template_columns_to_insert.remove("D_UPDATE_TIME")


            # 2.3 准备待插入的数据（初始化table_value_list，最终得到table_value_ndarray）
            table_value_list = []

            # 2.3.1 根据监测/检验场景还是预测场景 分别确定table_value_list
            # 准备待插入的基础数据（productId,d_iymdhm,d_dymdhm,elements,dataSource,areaCode,level;对于每次任务，这些值都是一样的）
            product_id = self.productId
            d_iymdhm = time.strftime("%Y-%m-%d %H:%M:%S")
            d_dymdhm = time.strftime("%Y-%m-%d %H:%M:%S")
            elements = self.elements
            dataSource = self.dataSource
            areaCode = self.areaCode
            level = self.level
            method = self.method
            index_time_type = self.indexTimeType
            # 2.3.1.1 如果是预测数据
            if query_product_type =='INDEX_PREP':
                table_value_list =  self.build_prep_table_value_list(areaCode, d_dymdhm, d_iymdhm, dataSource, data_rows, db_time_type,
                                                 elements, level, product_id, table_value_list, time_type,index_time_type)

            # 2.3.1.2 如果是监测数据/检验数据
            elif query_product_type == 'INDEX_MOP':
                table_value_list = self.build_mop_table_value_list(areaCode, d_dymdhm, d_iymdhm, dataSource, data_rows,
                                                                   elements, level, product_id, table_value_list, time_type)
            elif query_product_type == 'INDEX_PTEP':
                table_value_list = self.build_ptep_table_value_list(areaCode, d_dymdhm, d_iymdhm, dataSource, method,data_rows,
                                                                   elements, level, product_id, table_value_list, time_type)


            # 2.3.2 得到落表数据：table_value_ndarray
            table_value_ndarray = np.array(table_value_list).T
            table_value_ndarray = np.c_[table_value_ndarray,input_data]
            logging.info(table_value_ndarray.shape)
            table_value_ndarray= table_value_ndarray.tolist()


            # 2.4 写入到临时表
            insert_many_sql = insert_many_sql_template % (source_table,",".join(template_columns_to_insert),",".join(['%s']*len(template_columns_to_insert)))
            write_many_result = gbase_handler.execute_write_many_sql(insert_many_sql_template=insert_many_sql,write_many_sql_params=table_value_ndarray)

            # 2.5 记录入库详情
            # 有效视为1，包含999999视为0
            def judge_data_status(d_value):
                return 0 if str(d_value).__contains__('999999') or str(d_value).__contains__('nan') else 1
            # 按业务时次分组，统计status数量，构造details用于返回
            table_value_nd = np.array(table_value_ndarray)
            table_value_df = pd.DataFrame(table_value_nd,columns=template_columns_to_insert)
            table_value_df['D_STATUS'] = table_value_df.apply(lambda x: judge_data_status(x['D_VALUE']), axis=1)
            status_df = table_value_df.groupby(["D_DATETIME", 'D_STATUS']).count().reset_index().loc[:,
                        ["D_DATETIME", "D_STATUS", "D_DATAROW_ID"]]
            status = status_df.to_dict(orient='split')['data']
            details = {}
            for one_index, one_value in enumerate(status):
                if one_value[0] not in details.keys():
                    details[one_value[0]] = [0, 0, 0]
                if one_value[1] == 0:
                    details[one_value[0]][1] = one_value[2]
                elif one_value[1] == 1:
                    details[one_value[0]][0] = one_value[2]
            logging.info("The detail is : %s " % details.__str__())
            result_dict['details']=details

            # 3 写入目标表 target_table
            # 3.1 临时表数据写入成功之后，直接使用 merge语法，实现有则改，无则增
            if write_many_result:
                '''
                    考虑以下情况:
                        1.不同数据表的表结构
                        2.不同数据表的分区字段加密规则转换方式 √
                        3.通用的数据处理逻辑 √
                '''

                # 3.1.1 准备update_data_list以及insert_data_list
                distribute_key = "D_DATAROW_ID"

                sql_aa = "delete from {target_table} where exists (select 1 from {source_table} where {target_table}.{distribute_key}={source_table}.{distribute_key});".format(
                    source_table=source_table, target_table=target_table, distribute_key=distribute_key)
                sql_bb = "insert into {target_table} select * from {source_table};".format(
                    source_table=source_table, target_table=target_table)
                gbase_handler.execute_write_sql(sql_aa, True)
                gbase_handler.execute_write_sql(sql_bb, True)



            # 3.2 临时表数据写入失败,向上抛出algorithmException,交由subflowhandler处理
            else:
                raise AlgorithmException(response_code=DB_INSERT_TEMP_TABLE_ERROR_CODE,
                                         response_msg=DB_INSERT_TEMP_TABLE_ERROR_CODE % source_table)
            # 4.都冇得问题，提交事务
            gbase_handler.commit()
        except (DatabaseError,Exception):
            # 此次转换异常，回滚事务；向上抛出algorithmException,交由subflowhandler处理
            gbase_handler.rollback()
            logging.error("insert index data into gbase ,failed!")
            logging.error(traceback.format_exc())
            raise AlgorithmException(response_code=DB_MANIPULATE_ERROR_CODE, response_msg=DB_MANIPULATE_ERROR_MSG)
        finally:
            gbase_handler.close()


        logging.info("insert index data into gbase ,success!")
        return result_dict

    def build_prep_table_value_list(self, areaCode, d_dymdhm, d_iymdhm, dataSource, data_rows, db_time_type, elements,
                                    level, product_id, table_value_list, time_type,index_time_type):
        # data_size, date_time_list = self.check_size(data_rows, self.forecastPeriod, time_type)

        # 优先级 index_time_type > db_time_type > time_type
        check_type = time_type
        if db_time_type is not None:
            check_type = db_time_type
        if index_time_type is not None:
            check_type = index_time_type

        data_size, date_time_list = self.check_size(data_rows, self.forecastPeriod, check_type)
        self.product_actual_num = data_size  # 补充DI中实入条数
        date_time_list = [int(d_data_time) for d_data_time in date_time_list]

        date_time_forecast_list = copy.deepcopy(date_time_list)
        date_time_list = [int(self.forecastTime)] * data_size
        d_datarow_id_list = [hashlib.md5("".join(
            [product_id, str(self.forecastTime), str(d_data_time_forecast), elements, dataSource, areaCode,
             level]).encode(
            encoding='UTF-8')).hexdigest() for d_data_time_forecast in date_time_forecast_list]
        table_value_list.append(d_datarow_id_list)
        table_value_list.append([product_id] * data_size)
        table_value_list.append([d_iymdhm] * data_size)
        table_value_list.append([d_dymdhm] * data_size)
        table_value_list.append(date_time_list)
        table_value_list.append(date_time_forecast_list)
        table_value_list.append([elements] * data_size)
        table_value_list.append([dataSource] * data_size)
        table_value_list.append([areaCode] * data_size)
        table_value_list.append([level] * data_size)
        # 预测数据经常是DBTimeType和timeType同时存在
        v04001_list = []
        v04002_list = []
        v04003_list = []
        v04001_forecast_list = []
        v04002_forecast_list = []
        v04003_forecast_list = []


        if time_type.upper() in ['DAY', 'FIVE', 'TEN']:
            for d_data_time in date_time_list:
                v04001_list.append(d_data_time // 10000)  # 年
                v04002_list.append(int(str(d_data_time)[4:6]))  # 月
                v04003_list.append(d_data_time % 100)  # 日/候/旬
            table_value_list.append(v04001_list)
            table_value_list.append(v04002_list)
            table_value_list.append(v04003_list)

        elif time_type.upper() in ['MON', 'SEASON']:
            for d_data_time in date_time_list:
                v04001_list.append(d_data_time // 100)  # 年
                v04002_list.append(d_data_time % 100)  # 月、季
            table_value_list.append(v04001_list)
            table_value_list.append(v04002_list)

        elif time_type.upper() == 'YEAR':
            for d_data_time in date_time_list:
                v04001_list.append(d_data_time)  # 年
            table_value_list.append(v04001_list)
        else:
            pass  # 其他尺度暂不考虑

        if len(str(date_time_forecast_list[0]))==8:
            for date_time_forecast in date_time_forecast_list:
                v04001_forecast_list.append(date_time_forecast // 10000)  # 年
                v04002_forecast_list.append(int(str(date_time_forecast)[4:6]))  # 月
                v04003_forecast_list.append(date_time_forecast % 100)  # 日/候/旬
        elif len(str(date_time_forecast_list[0]))==6:
            for date_time_forecast in date_time_forecast_list:
                v04001_forecast_list.append(date_time_forecast // 100)  # 年
                v04002_forecast_list.append(date_time_forecast % 100)  # 月/季
                v04003_forecast_list.append(999999)  # 日/候/旬
        elif len(str(date_time_forecast_list[0]))==4:
            for date_time_forecast in date_time_forecast_list:
                v04001_forecast_list.append(date_time_forecast)  # 年
                v04002_forecast_list.append(999999)  # 月/季
                v04003_forecast_list.append(999999)  # 日/候/旬
        table_value_list.append(v04001_forecast_list)
        table_value_list.append(v04002_forecast_list)
        table_value_list.append(v04003_forecast_list)


        return table_value_list

    def build_mop_table_value_list(self, areaCode, d_dymdhm, d_iymdhm, dataSource, data_rows, elements, level,
                                   product_id, table_value_list, time_type):
        data_size, date_time_list = self.check_size(data_rows, self.time_ranges, time_type)
        self.product_actual_num =1  # 补充DI中实入条数
        date_time_list = [int(d_data_time) for d_data_time in date_time_list]
        # 特殊字段处理
        if level == 0:
            level="0000"

        d_datarow_id_list = [
            hashlib.md5("".join([product_id, str(d_data_time), elements, dataSource, areaCode, level]).encode(
                encoding='UTF-8')).hexdigest() for d_data_time in date_time_list]
        table_value_list.append(d_datarow_id_list)
        table_value_list.append([product_id] * data_size)
        table_value_list.append([d_iymdhm] * data_size)
        table_value_list.append([d_dymdhm] * data_size)
        table_value_list.append(date_time_list)
        table_value_list.append([elements] * data_size)
        table_value_list.append([dataSource] * data_size)
        table_value_list.append([areaCode] * data_size)
        table_value_list.append([level] * data_size)
        # 一般监测数据是没有DBTimeType的，只有timeType
        v04001_list = []
        v04002_list = []
        v04003_list = []
        if time_type.upper() in ['DAY', 'FIVE', 'TEN']:
            for d_data_time in date_time_list:
                v04001_list.append(d_data_time // 10000)  # 年
                v04002_list.append(int(str(d_data_time)[4:6]))  # 月
                v04003_list.append(d_data_time % 100)  # 日/候/旬
            table_value_list.append(v04001_list)
            table_value_list.append(v04002_list)
            table_value_list.append(v04003_list)

        elif time_type.upper() in ['MON', 'SEASON', 'FIVEYEAR']:
            for d_data_time in date_time_list:
                v04001_list.append(d_data_time // 100)  # 年
                v04002_list.append(d_data_time % 100)  # 月、季
            table_value_list.append(v04001_list)
            table_value_list.append(v04002_list)

        elif time_type.upper() == 'YEAR':
            for d_data_time in date_time_list:
                v04001_list.append(d_data_time)  # 年
            table_value_list.append(v04001_list)
        else:
            pass  # 其他尺度暂不考虑

        return table_value_list


    def build_ptep_table_value_list(self, areaCode, d_dymdhm, d_iymdhm, dataSource, method,data_rows, elements, level,
                                   product_id, table_value_list, time_type):
        data_size, fore_time_list = self.check_size_ptep(data_rows, self.forecastPeriod)
        fore_time_list = [str(fore_time) for fore_time in fore_time_list]
        self.product_actual_num =1  # 补充DI中实入条数
        date_time_list = [int(self.forecastTime)]*data_size
        # 特殊字段处理
        if level == 0:
            level="0000"

        d_datarow_id_list = [
            hashlib.md5("".join([product_id, str(self.forecastTime),str(fore_time), elements, dataSource,method, areaCode, level]).encode(
                encoding='UTF-8')).hexdigest() for fore_time in fore_time_list]
        table_value_list.append(d_datarow_id_list)
        table_value_list.append([product_id] * data_size)
        table_value_list.append([d_iymdhm] * data_size)
        table_value_list.append([d_dymdhm] * data_size)
        table_value_list.append(date_time_list)
        table_value_list.append(fore_time_list)
        table_value_list.append([elements] * data_size)
        table_value_list.append([dataSource] * data_size)
        table_value_list.append([method] * data_size)
        table_value_list.append([areaCode] * data_size)
        table_value_list.append([level] * data_size)
        # 一般监测数据是没有DBTimeType的，只有timeType
        v04001_list = []
        v04002_list = []
        v04003_list = []
        if time_type.upper() in ['DAY', 'FIVE', 'TEN']:
            for d_data_time in date_time_list:
                v04001_list.append(d_data_time // 10000)  # 年
                v04002_list.append(int(str(d_data_time)[4:6]))  # 月
                v04003_list.append(d_data_time % 100)  # 日/候/旬
            table_value_list.append(v04001_list)
            table_value_list.append(v04002_list)
            table_value_list.append(v04003_list)

        elif time_type.upper() in ['MON', 'SEASON', 'FIVEYEAR']:
            for d_data_time in date_time_list:
                v04001_list.append(d_data_time // 100)  # 年
                v04002_list.append(d_data_time % 100)  # 月、季
            table_value_list.append(v04001_list)
            table_value_list.append(v04002_list)

        elif time_type.upper() == 'YEAR':
            for d_data_time in date_time_list:
                v04001_list.append(d_data_time)  # 年
            table_value_list.append(v04001_list)
        else:
            pass  # 其他尺度暂不考虑

        return table_value_list

    def convert_input_data_shape(self, raw_input_data,save_type:str=None,format=None):
        """
        确定待插入数据input_data维度，将多维转换为一维
        :param input_data: 待插入数据,ndarray格式
        :param save_type: 数据处理方式
        :param format: 数据处理格式
        :return:
            data_columns：列，即数据列数
            data_rows：行，即数据条数
            converted_input_data:转换后的数据，1维 ndarray格式
        """
        input_data = raw_input_data
        if save_type:
            input_data = formatting_data(format=format,saveType=save_type,data=raw_input_data)
        input_data_shape = input_data.shape
        if len(input_data_shape) == 1:
            converted_input_data = input_data
        elif len(input_data_shape) == 2:
            #将多列合并成1列
            converted_input_data =[]
            for row in range(input_data_shape[0]):
                row_datas =input_data[row, :].tolist()
                converted_input_data.append( ",".join([str(row_data) for row_data in row_datas]))

        else:  # 三维及以上暂不考虑
            pass
        return  1, input_data_shape[0], np.array(converted_input_data)

    def check_size(self, data_rows, time_value_list, time_type):
        """
        用于检验输入数据与传入的时间值列表长度是否一致，如果不一致抛出异常；如果一致则返回真实输入时间列表,及其长度
        :param data_rows: 输入数据行数
        :param time_value_list: 时间值列表
        :param time_type:时间尺度
        :return: 返回真实输入时间列表,及其长度
        """
        date_time_list = get_time_list(time_value_list, time_type)
        data_size = len(date_time_list)
        # 数据条数一定是要与data_size匹配！
        if data_rows != data_size:
            # 找出缺的是哪一天！
            self.ret_list = list(set(self.input_data._indexes['time'].tolist())^set(date_time_list))
            self.bussiness_state="4" # DI字段，4表示缺测
            raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE,
                                     response_msg="The count of index data: [%s] can not match time size [%s]，lack_list is %s" % (
                                         str(data_rows), str(data_size),str(self.ret_list)))

        return data_size, date_time_list

    def check_size_ptep(self, data_rows, time_value_list):
        """
        用于检验输入数据与传入的时间值列表长度是否一致，如果不一致抛出异常；如果一致则返回真实输入时间列表,及其长度
        :param data_rows: 输入数据行数
        :param time_value_list: 时间值列表
        :param time_type:时间尺度
        :return: 返回真实输入时间列表,及其长度
        """
        data_size = len(time_value_list)
        # 数据条数一定是要与data_size匹配！
        if data_rows != data_size:
            # 找出缺的是哪一天！

            raise AlgorithmException(response_code=DATA_OUT_OF_SCALE_CODE,
                                     response_msg="The count of index data: [%s] can not match time size [%s]" % (
                                         str(data_rows), str(data_size)))

        return data_size, time_value_list


    def build_common_insert_sql(self, table_name: str, params: dict):
        """
        创建数据写入SQL,通用类型
        :param table_name: 待插入数据表名称
        :param params: 插入数据key:value
                key: 表字段
                value:数据值
        :return: 数据写入SQL；str
        """
        key = []
        value = []
        for tmpkey, tmpvalue in params.items():
            key.append(tmpkey)
            if isinstance(tmpvalue, str):
                value.append("\'" + tmpvalue + "\'")
            else:
                value.append(tmpvalue)
        attrs_sql = '(' + ','.join(key) + ')'
        values_sql = ' values(' + ','.join(value) + ')'
        sql = 'INSERT INTO %s' % table_name
        sql = sql + attrs_sql + values_sql
        return sql

    def build_create_or_update_sql(self, target_table: str, source_table: str, distribute_key: str,
                                   update_data_list: list, insert_data_list: list):
        """
        构造一条SQL，满足数据表中有数据时，完成更新操作；数据没有时，完成新增操作
        基于Gbase的merge语句实现
        :param target_table:目标表
        :param source_table:源表
        :param distribute_key:分区字段（类似于唯一索引绑定的字段，这个只能是在建表时创建）
        :param update_data_list:遭遇更新时，待更新数据字段的集合
        :param insert_data_list:遭遇新增时，待新增数据字段的集合
        :return: create_or_update_sql
        """
        # 0.前段SQL
        create_or_update_sql_prefix = "merge into {target_table} using {source_table}" \
                                      " on {target_table}.{distribute_key} = {source_table}.{distribute_key} " \
                                      "when matched then update set ".format(target_table=target_table,
                                                                             source_table=source_table,
                                                                             distribute_key=distribute_key)

        # 1.中段SQL
        update_sql_list = []
        for update_key in update_data_list:
            update_sql_list.append(
                "{target_table}.{update_key}={source_table}.{update_key}".format(target_table=target_table,
                                                                                 source_table=source_table,
                                                                                 update_key=update_key))
        create_or_update_sql_for_update = ",".join(update_sql_list)

        # 2.后段SQL
        insert_sql_list_1 = []
        insert_sql_list_2 = []
        for insert_key in insert_data_list:
            insert_sql_list_1.append(
                "{target_table}.{insert_key}".format(target_table=target_table, insert_key=insert_key))
            insert_sql_list_2.append(
                "{source_table}.{insert_key}".format(source_table=source_table, insert_key=insert_key))
        insert_sql_1 = ",".join(insert_sql_list_1)
        insert_sql_2 = ",".join(insert_sql_list_2)
        create_or_update_sql_for_insert = " when not matched then insert({insert_sql_1}) values({insert_sql_2});".format(
            insert_sql_1=insert_sql_1, insert_sql_2=insert_sql_2)

        # 3.合并前中后三段sql，返回之
        return "".join([create_or_update_sql_prefix, create_or_update_sql_for_update, create_or_update_sql_for_insert])

    # 多数据源合并
    def convert_data(self, algorithm_input_data):
        flow_data = []

        for aid_index, aid in enumerate(algorithm_input_data):
            if isinstance(aid["outputData"], list):
                for a in aid["outputData"]:
                    flow_data.append(a.values)
                    time_data = a.time
            else:
                if len(aid["outputData"].shape) == 2:
                    for xi in range(aid["outputData"].shape[1]):
                        flow_data.append(aid["outputData"][:, xi])
                else:
                    flow_data.append(aid["outputData"].values)
                time_data = aid["outputData"].time
        flow_data = np.asarray(flow_data)
        data_list = []
        for time_index, time in enumerate(time_data):
            data_list.append(flow_data[:, time_index])
        flow_data = xr.DataArray(data_list, dims=["time", "value"])
        flow_data["time"] = time_data
        self.input_data = flow_data