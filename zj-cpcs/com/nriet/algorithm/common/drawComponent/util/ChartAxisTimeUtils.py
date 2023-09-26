# -*- coding: utf-8 -*-

import datetime
import logging
from dateutil import rrule


def get_individual_years_indexes(x_values):

    x_valus_years = [str(x_value)[:4] for x_value in x_values]
    x_individual_years = set([int(x_value_year) for x_value_year in x_valus_years])
    x_individual_years = [str(x_individual_year) for x_individual_year in x_individual_years]
    individual_years_indexes = []
    for individual_year in x_individual_years:
        individual_years_index = x_valus_years.index(individual_year)
        if individual_years_index != -1:
            individual_years_indexes.append(individual_years_index)
    return individual_years_indexes

def get_each_month(start, end, regex='%Y%m'):
    start = datetime.datetime.strptime(start, regex)
    end = datetime.datetime.strptime(end, regex)
    start = datetime.datetime(year=start.year, month=start.month, day=1)
    end = datetime.datetime(year=end.year, month=end.month, day=1)

    month_count = rrule.rrule(rrule.MONTHLY, dtstart=start, until=end).count()  # 计算总月份数
    if end < start:
        logging.info("Parameter Error: Pls input right date range,start_month can't latter than end_month")
        return []
    else:
        list_month = []
        year = int(str(start)[:7].split('-')[0])  # 截取起始年份
        for m in range(month_count):  # 利用range函数填充结果列表
            month = int(str(start)[:7].split('-')[1])  # 截取起始月份，写在for循环里，作为每次迭代的累加基数
            month = month + m
            if month > 12:
                if month % 12 > 0:
                    month = month % 12  # 计算结果大于12，取余数
                    if month == 1:
                        year += 1  # 只需在1月份的时候对年份加1，注意year的初始化在for循环外
                else:
                    month = 12
            if len(str(month)) == 1:
                list_month.append(int(str(year) + '0' + str(month)))
            else:
                list_month.append(int(str(year) + str(month)))
        return list_month

def get_each_day(begin_date,end_date,regex='%Y%m%d'):
    date_list = []
    begin_date = datetime.datetime.strptime(begin_date, regex)
    end_date = datetime.datetime.strptime(end_date, regex)
    while begin_date <= end_date:
        date_int = int(begin_date.strftime(regex))
        date_list.append(date_int)
        begin_date += datetime.timedelta(days=1)
    return date_list

def get_mons_list(start_mon,end_mon):
    years = range(int(start_mon[:4]),int(end_mon[:4])+1)
    mon = ["01","02","03","04","05","06","07","08","09","10","11","12"]
    list1 = []
    for year in years:
        for m in mon:
            list1.append(str(year)+m)
    return list1[list1.index(start_mon):list1.index(end_mon)+1]

def get_seasons_list(start_season,end_season):
    years = range(int(start_season[:4]),int(end_season[:4])+1)
    mon = ["04","01","02","03"]
    list1 = []
    for year in years:
        for m in mon:
            list1.append(str(year)+m)
    return list1[list1.index(start_season):list1.index(end_season)+1]

def get_five_list(start_five,end_five):
    mons = get_mons_list(start_five[:6],end_five[:6])
    fives = ["01","02","03","04","05","06"]
    list2 = []
    for mon in mons:
        for f in fives:
            list2.append(mon+f)
    return list2[list2.index(start_five):list2.index(end_five)+1]

def get_ten_list(start_ten,end_ten):
    mons = get_mons_list(start_ten[:6],end_ten[:6])
    tens = ["01","02","03"]
    list2 = []
    for mon in mons:
        for f in tens:
            list2.append(mon+f)
    return list2[list2.index(start_ten):list2.index(end_ten)+1]

def get_month_abbr(month,regex='%m'): #YYYYMM
    mon = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    mon_abbr = ["01/", "02/", "03/", "04/", "05/", "06/", "07/", "08/", "09/", "10/", "11/", "12/"]
    return mon_abbr[mon.index(month[-2:])]

def get_day_month(day): #YYYYMMDD
    day_str = str(day)
    return get_month_abbr(day_str[4:6]) + day_str[-2:]

def get_day_month_year(day): #YYYYMMDD
    day_str = str(day)
    return get_day_month(day_str) + "\n" + day_str[:4] #MM/DD\nYYYY


def get_month_year(day):
    day_str = str(day)
    return  get_month_abbr(day_str)[:2] +"\n" + day_str[:4]
