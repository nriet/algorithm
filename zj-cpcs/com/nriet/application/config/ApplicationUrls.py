# coding=utf-8
import os
from com.nriet.application.handler.CpcsHandler import CpcsHandler
from com.nriet.application.handler.CorrelationHandler import CorrelationHandler
from com.nriet.application.handler.DrawFrontHandler import DrawFrontHandler
from com.nriet.application.handler.DrawRegionsHandler import DrawRegionsHandler
from com.nriet.application.handler.IndexRetryHandler import IndexRetryHandler
from com.nriet.application.handler.GridDataRetryHandler import GridDataRetryHandler
from com.nriet.application.handler.HealthDetectHandler import HealthDetectHandler
from com.nriet.application.handler.ChangeHealthyHandler import ChangeHealthyHandler
from com.nriet.application.handler.TimeOutTestHandler import TimeOutTestHandler

# 路由配置

root_path = os.path.abspath(os.path.join(os.getcwd(), "../"))
urls = [
    (r'/HealthDetectService', HealthDetectHandler),  # 心跳检测服务

    (r'/ChangeHealthyService', ChangeHealthyHandler),  # 心跳检测服务

    (r'/TimeoutService', TimeOutTestHandler),  # 超时连接测试接口

    (r'/GeneralService', CpcsHandler),  # 通用流程服务

    (r'/CorrelationService', CorrelationHandler),   # 相关分析服务

    (r'/DrawFrontService', DrawFrontHandler),   # 通用绘图服务

    (r'/DrawPublishService', DrawFrontHandler),   # 通用绘图服务(对外)

    (r'/DrawRegionsService', DrawRegionsHandler),   # 区域绘制服务

    (r'/IndexRetryService', IndexRetryHandler),     # 指数补录服务

    (r'/GridDataRetryService', GridDataRetryHandler),  # 格点补录服务

]

