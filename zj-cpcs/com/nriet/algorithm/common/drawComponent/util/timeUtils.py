import time
import logging

# 时间戳，到毫秒
def stamp_ms(c_time=None):
    if c_time is None:
        c_time = time.time()
    curr_t = int(c_time * 1000)
    return curr_t


# 格式化成2017-08-18
def fmt_date(c_time):
    return fmt_d(c_time, "%Y-%m-%d")


# 格式化成22:18:45
def fmt_time(c_time):
    return fmt_d(c_time, "%H:%M:%S")


# 格式化成2017-08-18 22:18:45
def fmt_datetime(c_time):
    return fmt_d(c_time, "%Y-%m-%d %H:%M:%S")


# 格式化成“fmt_str”指定格式
def fmt_d(c_time, fmt_str=None):
    if c_time is None:
        c_time = time.time()
    if fmt_str is None:
        fmt_str = "%Y-%m-%d %H:%M:%S"
    return time.strftime(fmt_str, time.localtime(c_time))


# 将字符串格式的时间转换成时间戳（单位毫秒）
def stamp_time(time_str, fmt_str=None):
    if time_str is None or len(time_str) == 0:
        return None
    if fmt_str is None:
        fmt_str = "%Y-%m-%d %H:%M:%S"
    try:
        timeArray = time.strptime(time_str, fmt_str)
        timeStamp = int(time.mktime(timeArray)) * 1000
        return timeStamp
    except Exception as e:
        logging.info(e)
    return None


a = '12345_6'
# logging.info(int(a.split("_")))
