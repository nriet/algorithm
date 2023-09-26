#!/usr/bin/env python
# -*- coding:utf-8 -*-

import redis
from redis.exceptions import WatchError
import logging,traceback
logger = logging.getLogger(__name__)
logger.root.setLevel(level=logging.INFO)

def get_redis_client(host:str,port:str,db:int=0):
    redis_client = redis.StrictRedis(host=host, port=port,  db=db)

    return redis_client

def transaction_set_order(redis_client,key=None,value=None):

    logging.info("必要参数校验")
    if (key is None) or (value is None):
        logging.error("key或者value不合法!")
        return False

    with redis_client.pipeline() as pipe:
        try:
            logging.info("监听开启")
            pipe.watch(key)
            logging.info("事务开启")
            pipe.multi()
            logging.info("命令入队")
            pipe.set(key, value)
            logging.info("事务提交")
            pipe.execute()

        except WatchError:
            logging.warning("事务提交失败，原因是该key在事务提交前被修改了")
            return False

    return True



if __name__ == '__main__':
    redis_client = get_redis_client('10.40.24.52','6379')
    transaction_set_order(redis_client,'10.40.24.52_CPCS_RESTRAT','1')

    # 推送方


    # 订阅方
    # pubsub = redis_client.pubsub()
    # pubsub.subscribe("39.106.78.27_CPCS_RESTRAT")
    # while True:
    #     print("time~~~")
    #     msg = pubsub.parse_response()
    #     print(msg)