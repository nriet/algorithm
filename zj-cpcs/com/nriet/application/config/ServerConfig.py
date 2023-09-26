import os, socket

# Debug开关
DEBUG_TUNER = False
# Xsrf保护开关
XSRF_PROECT_TUNER = False
# 默认服务器监听端口
DEFAULT_SERVER_PORT = 8000
# cookie加密密钥
COOKIE_SECRET = 'bZJc2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E='
# 帖子列表单页渲染数目
POST_PER_PAGE = 10
# 工程根目录
CURRENT_PATH = os.path.dirname(__name__)
# 宿主机名称
CURRENT_HOSTNAME = socket.gethostname()
# 宿主机IP
CURRENT_IP = socket.gethostbyname(CURRENT_HOSTNAME)
# 是否缓存高访问频率页面
SAVE_CACHE = True
# session有效期 单位：秒
SESSION_VALIDITY_PERIOD = 86400
# html页面缓存有效期 单位：秒
PAGE_CACHE_VALIDITY_PERIOD = 3600
# 服务器变更自动重载开关
'''
只感知.py文件的改变，模版的改变不会加载，有些特殊的错误，比如import的错误，就会直接让服务下线，到时候还得手动重启。
还有就是调试模式和 HTTPServer 的多进程模式不兼容。
在调试模式下，你必须将 HTTPServer.start 的参数设为不大于 1 的数字。
'''
AUTO_RELOAD = False
# 环境
DEFAULT_ENVIRONMENT = os.environ.get('pod_env','TEST')
# 服务名称
DEFAULT_SERVICE_NAME = 'cipas_cpcs'
# 是否需要在控制台打印日志,默认关，生产环境以减轻负担,调试运行时可以打开。
DEFAULT_CONSOLE_PRINT = True
# 单个服务开启多少个进程(也就是占用多少个逻辑核数)
NUM_PROCESSES = 5
