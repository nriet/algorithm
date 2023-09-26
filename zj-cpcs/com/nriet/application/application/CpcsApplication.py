from tornado.web import Application
"""
此脚本为Cpcs服务实例类
"""
from com.nriet.utils.RedisUtils import get_redis_client
from com.nriet.utils.config.ConfigUtils import look_for_single_global_config
import socket,logging
import os
class CpcsApplication(Application):
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        logging.info("初始化服务redis状态")
        # redis_client = get_redis_client(look_for_single_global_config('REDIS_IP'), look_for_single_global_config('REDIS_PORT'))
        # CURRENT_IP = socket.gethostbyname(socket.gethostname())
        # redis_client.set( CURRENT_IP+'_CPCS_RESTRAT', '0')
        # logging.info("初始化服务redis状态完成")

        file_name = look_for_single_global_config('IS_HEALTHY_TXT')
        logging.info("初始化服务健康信息is_healthy=yes至%s" % file_name)
        if os.path.exists(file_name):
            with open(file_name,mode='w',encoding='utf-8') as file:
                file.write('is_healthy=yes')