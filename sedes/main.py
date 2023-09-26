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


if len(sys.argv) != 2:
    print("Usage: python main.py argument, please input YYYY-MM")
else:
    argument = sys.argv[1]
    del sys.argv[1]
    print("Argument passed: ", argument)

    yystart = int(argument[0:4])
    yylast = int(argument[0:4])
    months = [argument[5:7]]
    day = 1

    # download ec and ec_climate data
    for year in range(yystart, yylast + 1):
        download_ec(year, months)
        download_ec_climate(str(year), months)

    # compute anomaly
    Anomaly_process(yystart, yylast, months)

    # opreation
    for year in range(yystart, yylast + 1):
        for month in months:
            process_time = str(year) + str(month)
            process_time_start = str(year) + '-' + month
            # 计算当前月份的后5个月份(如2023-04，process_time_end2023-10）
            process_time_end = get_recent_month(datetime.date(year, int(month), day), 5)
            operation(process_time, process_time_start, process_time_end)
