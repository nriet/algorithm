# # -*- coding: utf-8 -*-
# """
# #
# # Authors: limanman
# # OsChina: http://my.oschina.net/pydevops/
# # Purpose:
# #
# """
# # 数据库配置文件
# import sqlconf
# import MySQLdb
# from DBUtils.PooledDB import PooledDB
# # 为返回字典格式推荐将连接池的cursorclass设置为它
# from MySQLdb.cursors import DictCursor
#
#
# class Mysql(object):
#     """
#     Attributes:
#        None
#     """
#     __mysql_pool = None
#
#     def __init__(self):
#         # 获取连接对象
#         self._mysql_conn = Mysql.__get_connection()
#         # 创建游标对象
#         self._mysql_cursor = self._mysql_conn.cursor()
#
#     @staticmethod
#     def __get_connection():
#         """Get mysql connection from connection pool.
#
#         Args:
#             None
#         Returns:
#             connection
#         """
#         # 根据配置文件创建连接池
#         if not Mysql.__mysql_pool:
#             Mysql.__mysql_pool = PooledDB(
#                 creator=MySQLdb,
#                 use_unicode=False,
#                 cursorclass=DictCursor,
#                 db=sqlconf.MysqlConfig['db'],
#                 host=sqlconf.MysqlConfig['host'],
#                 port=sqlconf.MysqlConfig['port'],
#                 user=sqlconf.MysqlConfig['user'],
#                 passwd=sqlconf.MysqlConfig['passwd'],
#                 charset=sqlconf.MysqlConfig['charset'],
#                 mincached=sqlconf.MysqlConfig['mincached'],
#                 maxcached=sqlconf.MysqlConfig['maxcached'],
#                 maxconnections=sqlconf.MysqlConfig['maxconnections'])
#         # 返回连接池中连接对象
#         return Mysql.__mysql_pool.connection()
#
#     def get_all(self, sql_command, cmd_param=None):
#         """"Get all sql command execute result.
#
#         Args:
#             sql_command: sql command
#             cmd_param  : sql command paramaters
#         Returns:
#             tuple
#         """
#         if cmd_param:
#             count = self._mysql_cursor.execute(sql_command, cmd_param)
#         else:
#             count = self._mysql_cursor.execute(sql_command)
#
#         if count:
#             sql_result = self._mysql_cursor.fetchall()
#         else:
#             sql_result = None
#
#         return sql_result
#
#     def get_one(self, sql_command, cmd_param=None):
#         """"Get one sql command execute result.
#
#         Args:
#             sql_command: sql command
#             cmd_param  : sql command paramaters
#         Returns:
#             dict
#         """
#         if cmd_param:
#             count = self._mysql_cursor.execute(sql_command, cmd_param)
#         else:
#             count = self._mysql_cursor.execute(sql_command)
#
#         if count:
#             sql_result = self._mysql_cursor.fetchoneDict()
#         else:
#             sql_result = None
#
#         return sql_result
#
#     # 删查改 (略)
#
#     def sta_commit(self):
#         # 不对修改立即提交.
#         self._mysql_conn.autocommit(0)
#



#     def con_release(self, is_commit=False):
#         # 释放连接提交回滚?
#         # if is_is_commit:
#         # self._mysql_conn.commit()
#         # else:
#         # self._mysql_conn.rollback()
#
#         # 释放刚获取的连接
#         self._mysql_cursor.close()
#         self._mysql_conn.close()
