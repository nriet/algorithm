# -*- coding:utf-8 -*-
# @Time : 2020/10/21
# @Author : huxin
# @File : GbaseHandler.py

from GBaseConnector import connect, GBaseError
from GBaseConnector.GBaseError import DatabaseError
import logging

class GbaseHandler:
    """
        构造方法：
        config = {'host':'10.20.64.30',
                    'user':'NCC_CIPAS_QH',
                    'passwd':'Cipas1234!@#$',
                    'port':5258,
                  'db':'cipas'
                  }
        try:
            # 1.创建连接
            conn = connect()
            conn.connect(**config)

            # 2.创建游标
            cur = conn.cursor()
            # cur.execute("CREATE TABLE IF NOT EXISTS test_cipas(id INT, name VARCHAR(20))")

        except GBaseError.DatabaseError as err:
            logging.info(err)
        finally:
            conn.close()
    """

    def __init__(self, config):
        #连接属性设置
        self.host = config.get('host')
        self.username = config.get('user')
        self.password = config.get('passwd')
        self.port = config.get('port')
        self.db = config.get('db')
        self.charset = config.get('charset','utf8') #只能支持utf8/gbk,默认为utf8
        self.use_unicode = config.get('use_unicode',True) #是否使用 unicode 字符,默认True
        self.connect_timeout = config.get('connect_timeout',30) #连接超时时间。创建连接时的超时时间。默认30s
        self.autocommit = config.get('autocommit',False) #是否使用自动提交模式,默认False,开启手动提交

        #实例化连接对象、游标对象
        self.con = None
        self.cur = None

        try:
            self.con = connect()
            self.con.connect(**config)
            # 所有的查询，都在连接 con 的一个模块 cursor 上面运行的
            self.cur = self.con.cursor()
        except GBaseError.DatabaseError as err: #遇到异常，脚本不处理，调用者处理。
            raise err

    def close(self):
        """
        关闭Gbase数据库连接
        :return: 无返回
        """
        if self.con:
            self.con.close()
        else:
            logging.info("DataBase doesn't connect,close connectiong error;please check the db config.")

    def commit(self):
        """
        提交连接中的事务
        :return: 无返回
        """
        if self.con:
            self.con.commit()
        else:
            logging.info("DataBase doesn't connect,close connectiong error;please check the db config.")


    def rollback(self):
        """
        回滚
        :return: 无返回
        """
        if self.con:
            self.con.rollback()
        else:
            logging.info("DataBase doesn't connect,close connectiong error;please check the db config.")

    def select_data_base(self, db_name:str):
        """
        :param db_name: 待切换的数据库名称
        :return: 无返回
        """
        self.con.set_database(db_name)

    def get_one_data(self):
        """
        在执行 SQL 查询语句后，获取一行结果集
        :return: 包含一行结果集的元组 tuple
        """
        data = self.cur.fetchone()
        return data

    def get_many_data(self,fetch_size:int=None):
        """
        在执行 SQL 查询语句后，获取多行结果集。
        :param fetch_size: 想要获取指定条数的数据，不填则默认返回全部条数
        :return: 包含多行结果集的列表，元素类型为元组 list[tuple]
        """
        if fetch_size:
            data = self.cur.fetchmany(fetch_size)
        else:
            data = self.cur.fetchall()
        return data

    def next_set(self,skip_counts:int):
        """
        在执行多条 SQL 查询语句，且只需要多个查询结果中的一个时，可
        通过该方法跳过其他结果集，从而简化结果集获取过程。
        :param skip_counts:跳过结果集的数量
        :return 返回跳过skip_counts的结果集结果
        """
        self.cur.nextset(skip_counts)
        return self.cur.fetchall()

    def execute_read_sql(self, sql_str:str):
        """
        执行sql语句，针对读操作返回结果集
        :param sql_str:读SQL
        :return 返回读取之结果 list[tuple] 或者list
        """
        try:
            self.cur.execute(sql_str)
            records = self.cur.fetchall()
            return records
        except DatabaseError as e:
            error = 'Gbase execute read sql failed! ERROR (%s): %s' % (e.errno,e.msg)
            logging.info(error)
            raise e

    def execute_write_sql(self,sql_str:str,multi_stmt = False):
        """
        执行DML语句
        :param sql_str:写SQL
        :param multi_stmt:是否是多條语句，默认False
        :return:影响的行数，int类型

        """
        try:
            self.cur.execute(sql_str,multi_stmt = multi_stmt)
            return self.cur.rowcount
        except DatabaseError as e:
            self.con.rollback()
            error = 'Gbase execute read sql failed! ERROR (%s): %s' % (e.errno,e.msg)
            logging.info(error)
            raise e

    def execute_write_many_sql(self,insert_many_sql_template:str,write_many_sql_params:list):
        """
        批量执行多条 SQL 语句，并针对 insert 语句进行优化执行。
        :param insert_many_sql_template: SQL 语句模板
        :param write_many_sql_params:批量SQL的参数
        :return:返回最后一个SQL影响的行数

        例：
        operation = "INSERT INTO test VALUES(%s,%s)"
        cur.executemany(operation, [(1,'a'),(2,'b')])

        """
        try:
            self.cur.executemany(insert_many_sql_template,write_many_sql_params)

            return self.cur.rowcount
        except DatabaseError as e:
            self.con.rollback()
            error = 'Gbase execute read sql failed! ERROR (%s): %s' % (e.errno, e.msg)
            logging.info(error)
            raise e


    def delete(self, tablename, cond_dict):
        """删除数据

            args：
                tablename  ：表名字
                cond_dict  ：删除条件字典

            example：
                params = {"name" : "caixinglong", "age" : "38"}
                mydb.delete(table, params)

        """
        consql = ' '
        if cond_dict != '':
            for k, v in cond_dict.items():
                if isinstance(v, str):
                    v = "\'" + v + "\'"
                consql = consql + tablename + "." + k + '=' + v + ' and '
        consql = consql + ' 1=1 '
        sql_str = "DELETE FROM %s where%s" % (tablename, consql)
        logging.info(sql_str)
        return self.cur.execute(sql_str,multi_stmt = False)

    def insertMany(self, table, attrs, values):
        """插入多条数据

            args：
                tablename  ：表名字
                attrs        ：属性键
                values      ：属性值

            example：
                table='test_mysqldb'
                key = ["id" ,"name", "age"]
                value = [[101, "liuqiao", "25"], [102,"liuqiao1", "26"], [103 ,"liuqiao2", "27"], [104 ,"liuqiao3", "28"]]
                mydb.insertMany(table, key, value)
        """
        values_sql = ['%s' for v in attrs]
        attrs_sql = '(' + ','.join(attrs) + ')'
        values_sql = ' values(' + ','.join(values_sql) + ')'
        sql = 'insert into %s' % table
        sql = sql + attrs_sql + values_sql
        logging.info('insertMany:' + sql)
        return self.execute_write_many_sql(sql, values)

    def executeSql(self, sql_str:str):
        """
        执行sql语句，针对读操作返回结果集
        :param sql_str:读SQL
        :return 返回读取之结果 list[tuple] 或者list
        """
        try:
            # XX = sql_str[0,sql_str.index("FROM")]
            # print(XX)
            # exit()
            self.cur.execute(sql_str)
            descriptions = self.cur.description
            fields = []
            if descriptions:
                fields = [str(dp[0], encoding='utf-8') for dp in descriptions]
            # logging.info(fields)
            records = self.cur.fetchall()
            if fields and records:
                records = [self._conv_row(r, fields) for r in records]
            return records
        except DatabaseError as e:
            error = 'Gbase execute read sql failed! ERROR (%s): %s' % (e.errno,e.msg)
            logging.info(error)
            raise e


    def _conv_row(self, row, fields):
        if row is None:
            return None
        return dict(zip(fields, row))








