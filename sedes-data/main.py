import os
import sys
import datetime
import calendar
from download_ec import download_ec
from download_ec_climate import download_ec_climate
from Anomaly_process import Anomaly_process
from operation import operation


def get_recent_month(dt, months):
    # 这里的months 参数传入的是正数表示往后 ，负数表示往前
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return str(dt.replace(year=year, month=month, day=day))[:7]


def strToDate(date, formatter):
    return datetime.datetime.strptime(date, formatter)


def dateToStr(date, formatter):
    return date.strftime(formatter)


def month_list(time_ranges):
    start_time = time_ranges[1:7]
    end_time = time_ranges[8:14]
    time_list = []

    t1 = strToDate(str(start_time), "%Y%m")
    t2 = strToDate(str(end_time), "%Y%m")
    m_year = t2.year - t1.year

    m_start = t1.month
    m_end = m_year * 12 + t2.month

    for y in range(m_year + 1):
        for m in range(1, 13):
            time_list.append(dateToStr(t1.replace(year=t1.year + y, month=m), "%Y%m"))
    time_list = time_list[m_start - 1:m_end]
    return time_list


if len(sys.argv) != 2:
    print("Usage: python main.py argument, please input YYYY-MM")
else:
    argument = sys.argv[1]
    month_list = month_list(argument)
    del sys.argv[1]
    print("Argument passed: ", argument)

    for date in month_list:
        year = date[0:4]
        month = date[4:6]
        monthList = [date[4:6]]
        day = 1

        # download ec and ec_climate data
        download_ec(int(year), monthList)
        download_ec_climate(year, monthList)

        # compute anomaly
        Anomaly_process(int(year), int(year), monthList)

        # opreation
        process_time = year + month
        process_time_start = year + '-' + month
        # 计算当前月份的后5个月份(如2023-05，process_time_end2023-10）
        process_time_end = get_recent_month(datetime.date(int(year), int(month), day), 5)
        operation(process_time, process_time_start, process_time_end)