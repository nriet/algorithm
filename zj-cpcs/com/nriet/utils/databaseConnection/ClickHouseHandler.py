#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time: 2022/12/29
# @Author: Shiys
# @File: ClickHouseHandler.py

import logging
import clickhouse_driver

class ClickHouseHandler:
    def __init__(self, config):
        # 连接属性设置
        self.host = config.get('host')
        self.username = config.get('user')
        self.password = config.get('passwd')
        self.port = config.get('port')
        self.database = config.get('database')
        try:
            self.client = clickhouse_driver.Client(host=self.host, port=self.port, database=self.database, user=self.username, password=self.password)
        except Exception:
            logging.error("ClickHouse DataBase connect error, please check the db config.")

    def execute_sql(self, sql=''):
        res = None
        try:
            res = self.client.execute(sql)
        except Exception as e:
            logging.error("%s %s" % (sql, e))
        return res
    def executeSql(self, sql=''):
        res = None
        try:
            res = self.client.execute(sql,with_column_types=True)
            records = res[0]
            descriptions = res[1]
            # print(records)
            fields = [dp[0] for dp in descriptions]
            if fields and records:
                res = [self._conv_row(r, fields) for r in records]
        except Exception as e:
            logging.error("%s %s" % (sql, e))
        return res

    def disconnect(self):
        self.client.disconnect()

    def _conv_row(self, row, fields):
        if row is None:
            return None
        return dict(zip(fields, row))