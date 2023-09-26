import math
import re
import logging
from com.nriet.config.timerangeMap.TimeRangesMap import timerange_dict, time_type_dict


def convert_season(season):
    if season == "01":
        season_srt = "春季"
    elif season == "02":
        season_srt = "夏季"
    elif season == "03":
        season_srt = "秋季"
    else:
        season_srt = "冬季"
    return season_srt


def convert_five(five):
    five = (int(five) - 1) * 5 + 1
    if five < 10:
        five = "0" + str(five)
    return str(five)


def convert_five_af(five):
    five = (int(five) - 1) * 5 + 5
    if five < 10:
        five = "0" + str(five)
    return str(five)


def convert_five1(five):
    mon = str(math.ceil(int(five) / 6)).zfill(2)
    day = str(convert_five(int(five) % 6)).zfill(2)
    return mon, day


def convert_five1_af(five):
    mon = str(math.ceil(int(five) / 6)).zfill(2)
    day = str(convert_five_af(int(five) % 6)).zfill(2)
    return mon, day


def convert_season_month(season):
    # season = (int(season) - 1) * 3 + 1
    if season != "04":
        season = int(season) * 3
        if season < 10:
            season = "0" + str(season)
    else:
        season = 12
    return str(season)


def convert_season_month_af(season):
    # season = (int(season) - 1) * 3 + 3
    if season != "04":
        season = int(season) * 3 + 2
        if season < 10:
            season = "0" + str(season)
    else:
        season = "02"
    return str(season)


def formatter_time(time_value, range_dict, time_type):
    range_formatter = range_dict.get("range_formatter")
    range_type = range_dict.get("range_type")
    time_str = ""
    if range_type == "pre":
        if range_formatter == "-" or range_formatter == "/":
            if time_type == "day":
                time_str = time_value[0:4] + range_formatter + time_value[4:6]
            elif time_type == "five":
                time_str = time_value[0:4] + range_formatter + time_value[4:6]
            else:
                time_str = time_value[0:4]
        elif range_formatter == "U":
            if time_type == "day":
                time_str = time_value[0:4] + "年" + time_value[4:6] + "月"
            elif time_type == "five":
                time_str = time_value[0:4] + "年" + time_value[4:6] + "月"
            else:
                time_str = time_value[0:4] + "年"
        else:
            time_str = time_value
    elif range_type == "date":
        if range_formatter == "-" or range_formatter == "/":
            if time_type == "five":
                time_str = time_value[0:4] + range_formatter + time_value[4:6] + range_formatter + convert_five(
                    time_value[6:8])
            elif time_type == "fiveYear":
                mon, day = convert_five1(time_value[4:6])
                time_str = time_value[0:4] + range_formatter + mon + range_formatter + day
            elif time_type == "season":
                time_str = time_value[0:4] + range_formatter + convert_season_month(time_value[4:6])
            else:
                time_str = time_value[0:4]
        elif range_formatter == "U":
            if time_type == "five":
                time_str = time_value[0:4] + "年" + time_value[4:6] + "月" + convert_five(
                    time_value[6:8]) + "日"
            elif time_type == "fiveYear":
                mon, day = convert_five1(time_value[4:6])
                time_str = time_value[0:4] + "年" + mon + "月" + day + "日"
            elif time_type == "season":
                year = time_value[0:4]
                if time_value[4:6] == "04":
                    year = int(year) - 1
                time_str = str(year) + "年" + convert_season_month(time_value[4:6]) + "月"
        else:
            time_str = time_value
    elif range_type == "date_af":
        if range_formatter == "-" or range_formatter == "/":
            if time_type == "five":
                time_str = time_value[0:4] + range_formatter + time_value[4:6] + range_formatter + convert_five_af(
                    time_value[6:8])
            elif time_type == "fiveYear":
                mon, day = convert_five1_af(time_value[4:6])
                time_str = time_value[0:4] + range_formatter + mon + range_formatter + day
            elif time_type == "season":
                time_str = time_value[0:4] + range_formatter + convert_season_month_af(time_value[4:6])
            else:
                time_str = time_value[0:4]
        elif range_formatter == "U":
            if time_type == "five":
                time_str = time_value[0:4] + "年" + time_value[4:6] + "月" + convert_five_af(
                    time_value[6:8]) + "日"
            elif time_type == "fiveYear":
                mon, day = convert_five1_af(time_value[4:6])
                time_str = time_value[0:4] + "年" + mon + "月" + day + "日"
            elif time_type == "season":
                time_str = time_value[0:4] + "年" + convert_season_month_af(time_value[4:6]) + "月"
        else:
            time_str = time_value
    elif range_type == "split_year":
        if range_formatter == "-" or range_formatter == "/"  or range_formatter == "":
            if time_type == "day":
                time_str = time_value[4:6] + range_formatter + time_value[6:8]
            elif time_type == "five":
                time_str = time_value[4:6] + range_formatter + time_value[6:8]
            elif time_type == "year":
                time_str = time_value[0:4]
            else:
                time_str = time_value[4:6]
        elif range_formatter == "U":
            if time_type == "day":
                time_str = time_value[4:6] + "月" + time_value[6:8] + "日"
            elif time_type == "five":
                time_str = time_value[4:6] + "月" + time_value[6:8] + "候"
            elif time_type == "fiveYear":
                time_str = time_value[4:6] + "候"
            elif time_type == "mon":
                time_str = time_value[4:6] + "月"
            elif time_type == "season":
                time_str = convert_season(time_value[4:6])
            else:
                time_str = time_value[0:4] + "年"
        else:
            time_str = time_value
    elif range_type == "runave_mon":
        if range_formatter == "-" or range_formatter == "/"  or range_formatter == "":
            if time_type == "mon":
                curr_mon = int(time_value[4:6])
                prex_mon,suff_mon = curr_mon -1, curr_mon +1
                if prex_mon == 0:
                    prex_mon = 12
                if suff_mon == 13:
                    suff_mon = 1
                time_str = "{0:02d}".format(prex_mon)+"{0:02d}".format(suff_mon)
            else:
                time_str = time_value
        elif range_formatter == "U":
            time_str = time_value
        else:
            time_str = time_value
    else:
        if range_formatter == "-" or range_formatter == "/":
            if time_type == "day":
                time_str = time_value[0:4] + range_formatter + time_value[4:6] + range_formatter + time_value[6:8]
            elif time_type == "five":
                time_str = time_value[0:4] + range_formatter + time_value[4:6] + range_formatter + time_value[6:8]
            elif time_type == "fiveYear":
                time_str = time_value[0:4] + range_formatter + time_value[4:6]
            elif time_type == "ten":
                time_str = time_value[0:4] + range_formatter + time_value[4:6] + range_formatter + time_value[6:8]
            elif time_type == "mon":
                time_str = time_value[0:4] + range_formatter + time_value[4:6]
            elif time_type == "season":
                time_str = time_value[0:4] + range_formatter + time_value[4:6]
            else:
                time_str = time_value[0:4]
        elif range_formatter == "U":
            if time_type == "day":
                time_str = time_value[0:4] + "年" + time_value[4:6] + "月" + time_value[6:8] + "日"
            elif time_type == "five":
                time_str = time_value[0:4] + "年" + time_value[4:6] + "月" + time_value[6:8] + "候"
            elif time_type == "fiveYear":
                time_str = time_value[0:4] + "年" + time_value[4:6] + "候"
            elif time_type == "ten":
                tens = time_value[6:8]
                ten_str = ""
                if tens == "01":
                    ten_str = "上旬"
                if tens == "02":
                    ten_str = "中旬"
                if tens == "03":
                    ten_str = "下旬"
                time_str = time_value[0:4] + "年" + time_value[4:6] + "月" + ten_str
            elif time_type == "mon":
                time_str = time_value[0:4] + "年" + time_value[4:6] + "月"
            elif time_type == "season":
                time_str = time_value[0:4] + "年" + convert_season(time_value[4:6])
            else:
                time_str = time_value[0:4] + "年"
        else:
            time_str = time_value
    return time_str


def formatter_time_range(time_ranges, range_str):
    time_range = ""
    time_type, range_key, range_method, timeRanges = range_str.split("_")
    range_dict = timerange_dict.get(range_key)

    if range_dict:

        if range_method == "S":
            time_range = formatter_time(str(time_ranges[0]), range_dict, time_type)
        elif range_method == "E":
            time_range = formatter_time(str(time_ranges[1]), range_dict, time_type)
        elif range_method == "SE":
            range_concat = range_dict.get("range_concat")
            start_time = formatter_time(str(time_ranges[0]), range_dict, time_type)
            end_time = formatter_time(str(time_ranges[1]), range_dict, time_type)
            if time_ranges[0] == time_ranges[1] and range_key == "014":
                time_range = start_time
            elif time_ranges[0] == time_ranges[1] and range_key == "020":
                mon_en= ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
                time_range = mon_en[int(start_time[5:7])-1]+" "+start_time[:4]
            elif time_ranges[0] == time_ranges[1] and range_key == "013":
                time_range = start_time
            elif range_key == "016":
                time_range = start_time[0:2] + range_concat + end_time[2:]
            else:
                time_range = start_time + range_concat + end_time
    return time_range


if __name__ == '__main__':
    logging.info(formatter_time_range(["202001", "202001"], "mon_012_S_time"))
