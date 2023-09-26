import logging
from tornado import options
from logging.handlers import TimedRotatingFileHandler
import socket,os
from datetime import date
import threading
class ContextFilter(logging.Filter):

    def filter(self,record):
        thread_local = threading.current_thread()
        request_id = thread_local.request_id if hasattr(thread_local, 'request_id') else '--'
        record.request_id = request_id
        return True


def load_log_config(console_print=False):
    LOG_LEVEL=logging.INFO
    LOG_WARNING_LEVEL=logging.WARNING
    # LOG_FORMAT_TEMPLATE = "[{serviceName}-{environment}:{ip}:{port}][%(thread)d] [%(threadName)s] %(asctime)s.%(msecs)03d %(levelname).4s %(message)s"  # 服务器日志标准格式
    LOG_FORMAT_TEMPLATE = "[%(request_id)s][{serviceName}-{environment}:{ip}:{port}][MainThread] %(asctime)s.%(msecs)03d %(levelname).4s %(pathname)s%(lineno)d %(message)s"  # 服务器日志标准格式
    LOG_DATE_FORMAT="%Y-%m-%d %H:%M:%S"
    LOG_FILE_NAME='%s.%s.log'
    LOG_WARNING_FILE_NAME='%s.%s.warning.log'
    LOG_FILE_PATH="/tmp/logs/{environment}/{serviceName}/"
    # LOG_WHEN='H'
    # LOG_SUFFIX="%H"
    # LOG_EXTMATCH=r"^\d{2}(\.\w+)?$"

    logger = logging.getLogger(__name__)
    logger.setLevel(level=LOG_LEVEL)
    log_format = LOG_FORMAT_TEMPLATE.format(**options.options.as_dict())
    formatter = logging.Formatter(fmt=log_format, datefmt=LOG_DATE_FORMAT)

    LOG_FILE_PATH = LOG_FILE_PATH.format(**options.options.as_dict())
    if not os.path.exists(LOG_FILE_PATH):
        os.makedirs(LOG_FILE_PATH)

    LOG_FILE_NAME = LOG_FILE_NAME % (socket.gethostbyname(socket.gethostname()),date.today().strftime('%Y-%m-%d'))
    LOG_FILE_NAME=LOG_FILE_PATH+LOG_FILE_NAME

    LOG_WARNING_FILE_NAME = LOG_WARNING_FILE_NAME % (socket.gethostbyname(socket.gethostname()),date.today().strftime('%Y-%m-%d'))
    LOG_WARNING_FILE_NAME = LOG_FILE_PATH+LOG_WARNING_FILE_NAME



    handler = TimedRotatingFileHandler(filename=LOG_FILE_NAME,encoding='utf-8')
    # handler.suffix = LOG_SUFFIX
    # handler.extMatch = LOG_EXTMATCH
    handler.setFormatter(formatter)
    # handler.setLevel(LOG_LEVEL)

    warning_handler = TimedRotatingFileHandler(filename=LOG_WARNING_FILE_NAME,encoding='utf-8')
    # warning_handler.suffix = LOG_SUFFIX
    # warning_handler.extMatch = LOG_EXTMATCH
    warning_handler.setFormatter(formatter)
    warning_handler.setLevel(LOG_WARNING_LEVEL)

    if not console_print:
        logging.getLogger().handlers.pop(0)

    context_filter = ContextFilter()
    handler.addFilter(context_filter)

    logging.getLogger().addHandler(handler)
    logging.getLogger().addHandler(warning_handler)