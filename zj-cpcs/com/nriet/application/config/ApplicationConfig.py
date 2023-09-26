# coding=utf-8
from com.nriet.application.config import ServerConfig
import os


current_path = os.path.dirname(__file__)
root_path = os.path.abspath(os.path.join(os.getcwd(), "../"))
static_path = os.path.join(root_path, "statics")
app_settings = {  # 服务器设置
    'static_path': static_path,# 静态文件地址
    'cookie_secret': ServerConfig.COOKIE_SECRET,
    'xsrf_cookies': ServerConfig.XSRF_PROECT_TUNER,
    'debug': ServerConfig.DEBUG_TUNER,
    'autoreload': ServerConfig.AUTO_RELOAD,
    'xheaders': True
}

mysql_options = {  # mysql数据库设置
    'host': '60.205.1.25',
    'port': 3306,
    'db': 'tornadoweb_db',
    'user': 'root',
    'password': 'nriet123'
}
#  redis设置
redis_options = {
    'address': ('60.205.1.25', 6379),
    'minsize': 8,  # 连接池最小数量
    'maxsize': 16  # 连接池最大数量
}

#  补算接口
retry_interface = 'http://10.20.64.78:8080/cipas/v1/api/makeupData'
