#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/03/14
# @Author : xulh
# @File : MySQLHandler.py

import pymysql
import re
import logging
from com.nriet.config.MySQLConfig import config


class MysqldbHelper(object):  # 继承object类所有方法
    '''
        构造方法：
        config = {
            'host': '127.0.0.1',
            'port': 3306,
            'user': 'root',
            'passwd': 'root',
            'charset':'utf8',
            'cursorclass':pymysql.cursors.DictCursor
            }
        conn = pymysql.connect(**config)
        conn.autocommit(1)
        cursor = conn.cursor()
        '''

    def __init__(self, config):
        self.host = config.get('host')
        self.username = config.get('user')
        self.password = config.get('passwd')
        self.port = config.get('port')
        self.con = None
        self.cur = None

        try:
            self.con = pymysql.connect(**config)
            self.con.autocommit(1)
            # 所有的查询，都在连接 con 的一个模块 cursor 上面运行的
            self.cur = self.con.cursor()
        except:
            logging.info("DataBase connect error,please check the db config.")

    # 关闭数据库连接
    def close(self):
        if not self.con:
            self.con.close()
        else:
            logging.info("DataBase doesn't connect,close connectiong error;please check the db config.")

    # 创建数据库
    def createDataBase(self, DB_NAME):
        # 创建数据库
        self.cur.execute(
            'CREATE DATABASE IF NOT EXISTS %s DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci' % DB_NAME)
        self.con.select_db(DB_NAME)
        logging.info('creatDatabase:' + DB_NAME)

    # 选择数据库
    def selectDataBase(self, DB_NAME):
        self.con.select_db(DB_NAME)

    # 获取数据库版本号
    def getVersion(self):
        self.cur.execute("SELECT VERSION()")
        return self.getOneData()

    # 获取上个查询的结果
    def getOneData(self):
        # 取得上个查询的结果，是单个结果
        data = self.cur.fetchone()
        return data

    # 创建数据库表
    def creatTable(self, tablename, attrdict, constraint):
        """创建数据库表

            args：
                tablename  ：表名字
                attrdict   ：属性键值对,{'book_name':'varchar(200) NOT NULL'...}
                constraint ：主外键约束,PRIMARY KEY(`id`)
        """
        if self.isExistTable(tablename):
            logging.info("%s is exit" % tablename)
            return
        sql = ''
        sql_mid = '`id` bigint(11) NOT NULL AUTO_INCREMENT,'
        for attr, value in attrdict.items():
            sql_mid = sql_mid + '`' + attr + '`' + ' ' + value + ','
        sql = sql + 'CREATE TABLE IF NOT EXISTS %s (' % tablename
        sql = sql + sql_mid
        sql = sql + constraint
        sql = sql + ') ENGINE=InnoDB DEFAULT CHARSET=utf8'
        logging.info('creatTable:' + sql)
        self.executeCommit(sql)

    def executeSql(self, sql=''):
        """执行sql语句，针对读操作返回结果集

            args：
                sql  ：sql语句
        """
        try:
            self.cur.execute(sql)
            records = self.cur.fetchall()
            return records
        except pymysql.Error as e:
            error = 'MySQL execute failed! ERROR (%s): %s' % (e.args[0], e.args[1])
            logging.info(error)

    def executeCommit(self, sql=''):
        """执行数据库sql语句，针对更新,删除,事务等操作失败时回滚

        """
        try:
            self.cur.execute(sql)
            self.con.commit()
        except pymysql.Error as e:
            self.con.rollback()
            error = 'MySQL execute failed! ERROR (%s): %s' % (e.args[0], e.args[1])
            logging.info("error:", error)
            return error

    def insert(self, tablename, params):
        """创建数据库表

            args：
                tablename  ：表名字
                key        ：属性键
                value      ：属性值
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
        sql = 'insert into %s' % tablename
        sql = sql + attrs_sql + values_sql
        logging.info('_insert:' + sql)
        result = self.executeCommit(sql)
        if result:
            return False
        else:
            return True

    def select(self, tablename, cond_dict='', order='', fields='*'):
        """查询数据

            args：
                tablename  ：表名字
                cond_dict  ：查询条件
                order      ：排序条件

            example：
                logging.info mydb.select(table)
                logging.info mydb.select(table, fields=["name"])
                logging.info mydb.select(table, fields=["name", "age"])
                logging.info mydb.select(table, fields=["age", "name"])
        """
        consql = ' '
        if cond_dict != '':
            for k, v in cond_dict.items():
                consql = consql + '`' + k + '`' + '=' + '"' + v + '"' + ' and'
        consql = consql + ' 1=1 '
        if fields == "*":
            sql = 'select * from %s where ' % tablename
        else:
            if isinstance(fields, list):
                fields = ",".join(fields)
                sql = 'select %s from %s where ' % (fields, tablename)
            else:
                logging.info("fields input error, please input list fields.")
        sql = sql + consql + order
        logging.info('select:' + sql)
        return self.executeSql(sql)

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
        try:
            logging.info(sql)
            for i in range(0, len(values), 20000):
                self.cur.executemany(sql, values[i:i + 20000])
                self.con.commit()
        except pymysql.Error as e:
            self.con.rollback()
            error = 'insertMany executemany failed! ERROR (%s): %s' % (e.args[0], e.args[1])
            logging.info(error)

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
        sql = "DELETE FROM %s where%s" % (tablename, consql)
        logging.info(sql)
        return self.executeCommit(sql)

    def update(self, tablename, attrs_dict, cond_dict):
        """更新数据

            args：
                tablename  ：表名字
                attrs_dict  ：更新属性键值对字典
                cond_dict  ：更新条件字典

            example：
                params = {"name" : "caixinglong", "age" : "38"}
                cond_dict = {"name" : "liuqiao", "age" : "18"}
                mydb.update(table, params, cond_dict)

        """
        attrs_list = []
        consql = ' '
        for tmpkey, tmpvalue in attrs_dict.items():
            attrs_list.append("`" + tmpkey + "`" + "=" + "\'" + tmpvalue + "\'")
        attrs_sql = ",".join(attrs_list)
        logging.info("attrs_sql:", attrs_sql)
        if cond_dict != '':
            for k, v in cond_dict.items():
                if isinstance(v, str):
                    v = "\'" + v + "\'"
                consql = consql + "`" + tablename + "`." + "`" + k + "`" + '=' + v + ' and '
        consql = consql + ' 1=1 '
        sql = "UPDATE %s SET %s where%s" % (tablename, attrs_sql, consql)
        logging.info(sql)
        return self.executeCommit(sql)

    def dropTable(self, tablename):
        """删除数据库表

            args：
                tablename  ：表名字
        """
        sql = "DROP TABLE  %s" % tablename
        self.executeCommit(sql)

    def deleteTable(self, tablename):
        """清空数据库表

            args：
                tablename  ：表名字
        """
        sql = "DELETE FROM %s" % tablename
        logging.info("sql=", sql)
        self.executeCommit(sql)

    def isExistTable(self, tablename):
        """判断数据表是否存在

            args：
                tablename  ：表名字

            Return:
                存在返回True，不存在返回False
        """
        sql = "select * from %s" % tablename
        result = self.executeCommit(sql)
        if result is None:
            return True
        else:
            if re.search("doesn't exist", result):
                return False
            else:
                return True


if __name__ == '__main__':

    # 初始化打开数据库连接
    mydb = MysqldbHelper(config)
    # 打印数据库版本
    logging.info(mydb.getVersion())
    logging.info(mydb.isExistTable("T_AUTO_PRODUCT"))
    logging.info(mydb.select("T_AUTO_PRODUCT", fields=["*"]))
