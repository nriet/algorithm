# -*- coding:utf-8 -*-
# @Time : 2020/10/15
# @Author : huxin
# @File : ConfigUtils.py

from com.nriet.config.PathConfig import CPCS_ROOT_PATH
from configparser import ConfigParser
import logging

def look_for_single_global_config(key:str,conf_file:str=None,fallback:str=None,current_environment:str=None):
    """
        搜索当前环境下的单个配置信息.配置文件满足ini标准。查询逻辑如下：
        1.如果找不到节名,就抛出NoSectionError;
        2.如果在指定的节中含有配置项，则返回其值;
        3.如果在2中找不到，会尝试在[dafault]节点中查询配置项,有则返回其值;
        4.如果3没找到，如果设计fallback则返回fallback,否则抛出NoOptionError;
    :param key: 传入的key
    :return: 返回value:str。具体规则见上
    """
    config_parser = ConfigParser()

    if not conf_file:
        conf_file = CPCS_ROOT_PATH + "com/nriet/config/GlobalConfig.ini"
    config_parser.read(conf_file)

    if not current_environment:
        current_environment = config_parser.get('default', 'CURRENT_ENVIRONMENT')

    return config_parser.get(current_environment, key,fallback=fallback)

def look_for_gbase_connection_config(conf_file:str=None,current_environment:str=None):
    config_parser = ConfigParser()

    if not conf_file:
        conf_file = CPCS_ROOT_PATH + "com/nriet/config/GlobalConfig.ini"
    config_parser.read(conf_file)

    if not current_environment:
        current_environment = config_parser.get('default', 'CURRENT_ENVIRONMENT')

    host = config_parser.get(current_environment, 'GBASE_HOST')
    port = config_parser.get(current_environment, 'GBASE_PORT')
    user = config_parser.get(current_environment, 'GBASE_USERNAME')
    passwd = config_parser.get(current_environment, 'GBASE_PASSWD')
    database = config_parser.get(current_environment, 'GBASE_DB_NAME')
    autocommit = config_parser.get(current_environment,'GBASE_DB_AUTOCOMMIT')
    return {'host':host,'user':user,'port':port,'passwd':passwd,'database':database,'autocommit':eval(autocommit)}

def look_for_obs_connection_config(conf_file:str=None,current_environment:str=None):
    config_parser = ConfigParser()

    if not conf_file:
        conf_file = CPCS_ROOT_PATH + "com/nriet/config/GlobalConfig.ini"
    config_parser.read(conf_file)

    if not current_environment:
        current_environment = config_parser.get('default', 'CURRENT_ENVIRONMENT')

    obs_ak = config_parser.get(current_environment, 'OBS_AK')
    obs_sk = config_parser.get(current_environment, 'OBS_SK')
    obs_endpoint = config_parser.get(current_environment, 'OBS_ENDPOINT')

    return {'obs_ak':obs_ak,'obs_sk':obs_sk,'obs_endpoint':obs_endpoint}

def look_for_kafka_producer_config(topicKey:str,conf_file:str=None,current_environment:str=None):
    config_parser = ConfigParser()

    if not conf_file:
        conf_file = CPCS_ROOT_PATH + "com/nriet/config/GlobalConfig.ini"
    config_parser.read(conf_file)

    if not current_environment:
        current_environment = config_parser.get('default', 'CURRENT_ENVIRONMENT')

    host = config_parser.get(current_environment, 'KAFKA_HOST')
    port = config_parser.get(current_environment, 'KAFKA_PORT')
    topic = config_parser.get(current_environment, 'KAFKA_'+topicKey)
    return {'host':host,'port':port,'topic':topic}

def look_for_clickhouse_connection_config(conf_file:str=None,current_environment:str=None):
    config_parser = ConfigParser()

    if not conf_file:
        conf_file = CPCS_ROOT_PATH + "com/nriet/config/GlobalConfig.ini"
    config_parser.read(conf_file)

    if not current_environment:
        current_environment = config_parser.get('default', 'CURRENT_ENVIRONMENT')

    host = config_parser.get(current_environment, 'CH_HOST')
    port = config_parser.get(current_environment, 'CH_PORT')
    user = config_parser.get(current_environment, 'CH_USERNAME')
    passwd = config_parser.get(current_environment, 'CH_PASSWD')
    database = config_parser.get(current_environment, 'CH_DB_NAME')
    return {'host':host,'user':user,'port':port,'passwd':passwd,'database':database}


if __name__ == '__main__':
    logging.info(look_for_single_global_config('OBS_BUCKET_NAME'))

