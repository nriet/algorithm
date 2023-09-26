import sys, os

print("Server root path is : %s" % os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from tornado import options, httpserver, ioloop
from com.nriet.application.config import ApplicationUrls, ServerConfig, ApplicationConfig, LogConfig
from com.nriet.application.application.CpcsApplication import CpcsApplication
import logging
import time
import requests
import socket
import threading

# 命令行参数定义
options.define('port', type=int, default=ServerConfig.DEFAULT_SERVER_PORT)  # 端口号
options.define('environment', type=str, default=ServerConfig.DEFAULT_ENVIRONMENT)  # 环境
options.define('serviceName', type=str, default=ServerConfig.DEFAULT_SERVICE_NAME)  # 服务名称
options.define('consolePrint', type=bool, default=ServerConfig.DEFAULT_CONSOLE_PRINT)  # 日志是否输出控制台
options.define('ip', type=str, default=ServerConfig.CURRENT_IP)  # ip
options.define('num_processes', type=int, default=ServerConfig.NUM_PROCESSES)  # 多进程个数

# CURRENT_IP = socket.gethostbyname(socket.gethostname())

# # nacos服务
# def service_register():
#     url = "http://10.40.24.33:8848/nacos/v1/ns/instance?namespaceId=2b7049d1-5478-449b-814d-e42c26b8355d&serviceName=cipas-cpcs&ip={ip}&port={port}".format(ip=CURRENT_IP,port=options.options.port)
#     res = requests.post(url)
#     logging.info("向nacos注册中心，发起服务注册请求，注册响应状态： {}".format(res.status_code))
#
#
# # 服务检测
# def service_beat():
#     while True:
#         url = "http://10.40.24.33:8848/nacos/v1/ns/instance/beat?namespaceId=2b7049d1-5478-449b-814d-e42c26b8355d&serviceName=cipas-cpcs&ip={ip}&port={port}".format(ip=CURRENT_IP,port=options.options.port)
#         res = requests.put(url)
#         logging.info("已注册服务，执行心跳服务，续期服务响应状态： {}".format(res.status_code))
#         time.sleep(3)


if __name__ == '__main__':
    loop = ioloop.IOLoop.current()
    options.parse_command_line()
    app = CpcsApplication(
        ApplicationUrls.urls,
        **ApplicationConfig.app_settings
    )
    # 日志配置，必须要在Application之后启动才行
    LogConfig.load_log_config(console_print=options.options.consolePrint)

    #注册nacos服务
    # service_register()
    #异步发送心跳，发送频率为3秒
    # threading.Timer(1,service_beat).start()
    server = httpserver.HTTPServer(app)
    logging.info('启动端口: %s' % options.options.port)
    server.listen(options.options.port) # 在Linux系统bind方法不起作用，需要使用listen;在macOS系统listen方法不起作用，需要使用bind。
    # server.start(num_processes=options.options.num_processes)
    server.start()
    logging.info('服务器已启动。')
    loop.start()
