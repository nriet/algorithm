
import logging
import math
import arrow
from com.nriet.utils.matchUtils import match_interval
import calendar



class Time():
    default_regex_list = ['YYYY', 'YYYYMM', 'YYYYMMDD', 'YYYYSS', 'YYYYMMXX', 'YYYYMMHH', 'YYYYHH', 'YYYYWW']
    # time_type_list = ['year', 'mon', 'day', 'season', 'ten', 'five', 'fiveYear', 'week']
    time_type_list = ['YEAR', 'MON', 'DAY', 'SEASON', 'TEN', 'FIVE', 'FIVEYEAR', 'WEEK']

    DAY_TO_LIST = ['YEAR', 'MON', 'SEASON', 'TEN', 'FIVE', 'FIVEYEAR', 'DAY', 'WEEK']
    FIVE_TO_LIST = ['YEAR', 'MON', 'SEASON', 'FIVE']
    TEN_TO_LIST = ['YEAR', 'MON', 'SEASON', 'TEN']
    MON_TO_LIST = ['YEAR', 'SEASON', 'MON']
    FIVEYEAR_TO_LIST = ['YEAR', 'FIVEYEAR']
    SEASON_TO_LIST = ['YEAR', 'SEASON']
    YEAR_TO_LIST = ['YEAR','DAY']
    WEEK_TO_LIST = ['WEEK', 'DAY']


    time_type_mapping = {
        "MON": "months",
        "DAY": "days",
        "YEAR": "years",
    }


    def __init__(self, value, time_type):
        self.value = value
        self.time_type = time_type
        self.regex = Time.default_regex_list[Time.time_type_list.index(time_type)]
        if Time.time_type_list.index(time_type) <= 2:
            self.obj = arrow.get(self.value, self.regex)


    def convert(self, time_type, regex=None):
        if not regex:
            regex = ''
        # 1.先转换类型
        time_type = time_type.upper()

        if time_type != self.time_type:
            # 判断支不支持转
            if not time_type in getattr(self.__class__, self.time_type + '_TO_LIST'):
                logging.info('%s cannot be transfored as  %s type!' % (self.time_type, time_type))
                return self

            # 更新正则表达
            self.regex = Time.default_regex_list[Time.time_type_list.index(time_type)]

        # 2.适配具体类型转化
        func = getattr(self.__class__, self.time_type + '_convert')
        func(self,time_type)

        # 更新time_type
        self.time_type = time_type

        # 3.再看正则表达
        if regex != self.regex and len(regex) == len(self.regex):  # 传进来的regex要和当前的time_tpye对应的默认正则位数要匹配！
            regex_dict = {}
            # 根据obj.time_type 获取不同的正则字典
            if Time.time_type_list.index(time_type) <= 2:
                if time_type == 'YEAR':
                    regex_dict['year'] = int(regex)
                elif time_type == 'MON':
                    year = regex[:4]
                    mon = regex[-2:]
                    if year.isdigit():
                        regex_dict['year'] = int(year)
                    if mon.isdigit():
                        regex_dict['month'] = int(mon)
                else:
                    year = regex[:4]
                    mon = regex[4:6]
                    day = regex[-2:]
                    if year.isdigit():
                        regex_dict['year'] = int(year)
                    if mon.isdigit():
                        regex_dict['month'] = int(mon)
                    if day.isdigit():
                        regex_dict['day'] = int(day)
                self.obj = self.obj.replace(**regex_dict)
                self.value = self.obj.format(self.regex)
            else:
                for index, reg in enumerate(regex):
                    if reg.isdigit():
                        self.value = replace_char(self.value, reg, index)
                        self.obj = self.value
        return self

    def DAY_convert(self, time_type):
        if Time.time_type_list.index(time_type) <= 2:  # 如果转成的类型为年 月 日，则在arrow对象中流转即可
            self.value = self.obj.format(self.regex)
            self.obj = arrow.get(self.value, self.regex)
        else:  # 如果不是
            # 假设是季
            if time_type == 'SEASON':
                current_month = self.obj.month
                if current_month < 3:
                    self.value = str(self.obj.datetime.year) + "04"
                if 3 <= current_month < 6:
                    self.value = str(self.obj.datetime.year) + "01"
                if 6 <= current_month< 9:
                    self.value = str(self.obj.datetime.year) + "02"
                if 9 <= current_month < 12:
                    self.value = str(self.obj.datetime.year) + "03"
                if current_month == 12:
                    self.value = str(self.obj.datetime.year + 1) + "04"
                # season = match_interval(current_month,[1,4,7,10,12],["01",'02','03','04'])
                # self.value = str(self.obj.datetime.year) + season
                self.obj = self.value
            # 假设是旬
            elif time_type == 'TEN':
                current_day = self.obj.day
                ten = match_interval(current_day,[1,11,21,32],['01','02','03'])
                self.value = self.obj.format("YYYYMM") + ten
                self.obj = self.value
            # 假设是中国侯
            elif time_type == 'FIVE':
                current_day = self.obj.day
                five = match_interval(current_day,[1,6,11,16,21,26,32],['01','02','03','04','05','06'])
                self.value = self.obj.format("YYYYMM") + five
                self.obj = self.value
            # 假设是国际侯
            elif time_type == 'FIVEYEAR':
                current_day = int(self.obj.format('DDD'))  # 获取当前日 1 2 3 ... 366
                # 如果是闰年,0301之后的 对应的日数要减去1
                if judge_leap_year(self.obj.year):
                    if current_day >= 240525:
                        current_day -= 1
                fiveYear = math.ceil(current_day / 5)

                self.value = str(self.obj.year) + str(fiveYear) if fiveYear >= 10 else str(self.obj.year) + '0' + str(fiveYear)
                self.obj = self.value
        # 假设是中国周,注意：周一为本周的起始日，周日为本周的结束日
            elif time_type == 'WEEK':
                current_day = int(self.obj.format('DDD'))  # 获取当前日 1 2 3 ... 366
                # 获取第二周的具体日期和末周的具体日期
                weekday_of_first_day = self.obj.replace(month=1, day=1).isocalendar()[2]
                weekday_of_last_day = self.obj.replace(month=12, day=31).isocalendar()[2]

                if weekday_of_first_day !=0:  # 如果不是0
                    second_week_date = int(self.obj.replace(month=1, day=1).shift(days=8 - weekday_of_first_day).format('DDD'))
                else:
                    second_week_date = int(self.obj.replace(month=1, day=1).shift(days=1).format('DDD'))

                if weekday_of_last_day == 0:
                    last_week_date = int(self.obj.replace(month=12, day=31).format('DDD'))
                else:
                    last_week_date = int(self.obj.replace(month=12, day=31).shift(days=-weekday_of_last_day).format('DDD'))

                week = '01'
                year = self.obj.year
                if current_day < second_week_date:
                    pass
                elif current_day >= second_week_date and current_day <= last_week_date:
                    week = math.ceil((current_day - second_week_date) / 7) + 1
                else:
                    year = str(self.obj.year + 1)

                week_str = '0'+str(week) if int(week) <10 else str(week)
                self.value = str(year) + week_str
                self.obj = self.value


    def MON_convert(self, time_type):
        if Time.time_type_list.index(time_type) <= 2:  # 如果转成的类型为年 月 日，则在arrow对象中流转即可
            self.value = self.obj.format(self.regex)
            self.obj = arrow.get(self.value, self.regex)
        elif time_type == 'SEASON':
            month = self.obj.month
            year = str(self.obj.year)
            season = match_interval(month,[1,4,7,10,12],["01",'02','03','04'])
            self.value = year + season
            self.obj = self.value


    def YEAR_convert(self, time_type):
        if Time.time_type_list.index(time_type) <= 2:  # 如果转成的类型为年 月 日，则在arrow对象中流转即可
            self.value = self.obj.format(self.regex)
            self.obj = arrow.get(self.value, self.regex)



    def SEASON_convert(self, time_type):
        if Time.time_type_list.index(time_type) <= 2:  # 如果转成的类型为年 月 日，则在arrow对象中流转即可
            date_str = self.value[:len(self.regex)]
            self.value = date_str
            self.obj = arrow.get(date_str, self.regex)


    def TEN_convert(self, time_type):
        # ['year','mon','season','ten']
        if Time.time_type_list.index(time_type) <= 2:  # 如果转成的类型为年 月 日，则在arrow对象中流转即可
            date_str = self.value[:len(self.regex)]
            self.value = date_str
            self.obj = arrow.get(date_str, self.regex)

        elif time_type =='SEASON':
            month = int(self.value[4:6])
            season = match_interval(month,[1,4,7,10,12],["01",'02','03','04'])
            self.value = self.value[:4] + season
            self.obj = self.value


    def FIVE_convert(self, time_type):
        # five_to_list = ['year','mon','season','five']
        if Time.time_type_list.index(time_type) <= 2:  # 如果转成的类型为年 月 日，则在arrow对象中流转即可
            date_str = self.value[:len(self.regex)]
            self.value = date_str
            self.obj = arrow.get(date_str, self.regex)
        elif time_type == 'SEASON':
            month = int(self.value[4:6])
            season = match_interval(month,[1,4,7,10,12],["01",'02','03','04'])
            self.value = self.value[:4] + season
            self.obj = self.value


    def FIVEYEAR_convert(self, time_type):
        if Time.time_type_list.index(time_type) <= 2:  # 如果转成的类型为年 月 日，则在arrow对象中流转即可
            date_str = self.value[:len(self.regex)]
            self.value = date_str
            self.obj = arrow.get(date_str, self.regex)


    def WEEK_convert(self, time_type):
        if Time.time_type_list.index(time_type) <= 2:  # 如果转成的类型为年 月 日，则在arrow对象中流转即可
            date_str = self.value[:len(self.regex)]
            self.value = date_str
            self.obj = arrow.get(date_str, self.regex)


    def calculate(self, timedelta=0):
        '''
        目前只支持加减
        '''

        time_type = self.time_type

        if Time.time_type_list.index(time_type) <= 2:  # 如果转成的类型为年 月 日，则在arrow对象中流转即可
            mapping = Time.time_type_mapping[time_type]
            self.obj = self.obj.shift(**{mapping: int(timedelta)})
            self.value = self.obj.format(self.regex)
        else:  # 更改最后两位即可
            if time_type == 'SEASON':
                year = int(self.value[:4])
                season = int(self.value[-2:]) + int(timedelta)
                if season % 4 == 0:
                    year += (season // 4) - 1
                    season =4
                else:
                    year += season // 4
                    season = season % 4
                self.value = "".join([str(year),"0",str(season)])
                self.obj =self.value
            elif time_type == 'TEN':
                year = int(self.value[:4])
                month = int(self.value[4:6])
                ten =int(self.value[-2:]) + int(timedelta)
                if ten % 3 ==0:
                    month += (ten // 3) - 1
                    ten = 3
                else:
                    month += ten // 3
                    ten = ten % 3


                if month %12 ==0:
                    year += (month //12) -1
                    month = 12
                else:
                    year += (month //12)
                    month = month %12

                month_str = str(month) if month >=10 else '0'+ str(month)
                ten_str = '0'+str(ten)
                self.value = ''.join([str(year),month_str,ten_str])
                self.obj = self.value
            elif time_type == 'FIVE':
                year = int(self.value[:4])
                month = int(self.value[4:6])
                five =int(self.value[-2:]) + int(timedelta)
                if five % 6 ==0:
                    month += (five // 6) - 1
                    five = 6
                else:
                    month += five // 6
                    five = five % 6


                if month %12 ==0:
                    year += (month //12) -1
                    month = 12
                else:
                    year += (month //12)
                    month = month %12

                month_str = str(month) if  int(month) >=10 else '0'+ str(month)
                five_str = '0'+str(five)
                self.value = ''.join([str(year),month_str,five_str])
                self.obj = self.value
            elif time_type == 'FIVEYEAR':
                year = int(self.value[:4])
                fiveYear = int(self.value[-2:]) + int(timedelta)
                if fiveYear % 73 == 0:
                    year += (fiveYear // 73) - 1
                    fiveYear = 73
                else:
                    year += fiveYear // 73
                    fiveYear = fiveYear % 73
                five_year_str = str(fiveYear) if int(fiveYear) >=10 else '0'+ str(fiveYear)
                self.value = "".join([str(year),five_year_str])
                self.obj =self.value
            elif time_type =='WEEK':
                timedelta = int(timedelta)
                current_year = self.value[:4]


                current_week = int(self.value[-2:])
                # 给定年份的中国周最大到多少
                current_week_counts = self.calculate_week_count(current_year)
                logging.info("The max number of week of %s is: %s" % (current_year,str(current_week_counts)))
                week_result = current_week + timedelta
                year = current_year
                if timedelta <0:
                    if week_result <=0:
                        # 给定年份的去年，中国周最大到多少
                        pre_year = str(int(current_year) - 1)
                        pre_week_counts = self.calculate_week_count(pre_year)
                        logging.info("The max number of week of %s is：%s" % (pre_year, str(current_week_counts)))
                        week_result += pre_week_counts-1
                        year = pre_year
                else:
                    if week_result-current_week_counts > 0:
                        # 给定年份的去年，中国周最大到多少,默认不能超过明年的周数！！
                        next_year = str(int(current_year) + 1)
                        # next_week_counts = self.calculate_week_count(next_year)
                        week_result -= current_week_counts-1
                        year = next_year


                week_result_str = '0'+ str(week_result) if week_result<10 else str(week_result)
                self.value = "".join([str(year),week_result_str])
                self.obj =self.value



        return self

    def calculate_week_count(self, current_year):
        first_day_of_year = arrow.get(current_year, 'YYYY')
        weekday_of_first_day = first_day_of_year.isocalendar()[2]
        if weekday_of_first_day != 0:
            second_week_date = first_day_of_year.shift(days=1-weekday_of_first_day)
        else:
            second_week_date = first_day_of_year.shift(days=1)
        first_week_date = second_week_date.shift(days=-7)
        last_day_of_year = first_day_of_year.replace(month=12, day=31)
        weekday_of_last_day = last_day_of_year.isocalendar()[2]
        if weekday_of_last_day == 0:  # 如果不是0 ,也就是星期日
            last_week_date = last_day_of_year
        else:
            last_week_date = last_day_of_year.shift(days=-weekday_of_last_day)

        days = (last_week_date - first_week_date).days+1

        return int(days / 7)

    def get_start(self):
        time_type = self.time_type
        if Time.time_type_list.index(time_type) <= 2:
            return self.obj.format("YYYYMMDD")
        elif time_type == 'SEASON':
            season_list = ['01','02','03','04']
            mon_first_list = ['0301','0601','0901','1201']
            if self.value[-2:] == "04":
               tt =  str(int(self.value[:4])-1) + mon_first_list[season_list.index(self.value[-2:])]
            else:
                tt = self.value[:4] + mon_first_list[season_list.index(self.value[-2:])]
            return tt
        elif time_type == 'TEN':
            ten_list = ['01','02','03']
            ten_first_list = ['01','11','21']
            return self.value[:6] + ten_first_list[ten_list.index(self.value[-2:])]
        elif time_type == 'FIVE':
            five_list = ['01','02','03','04','05','06']
            five_first_list = ['01','06','11','16','21','26']
            return self.value[:6] + five_first_list[five_list.index(self.value[-2:])]
        elif time_type == 'FIVEYEAR':
            current_year = self.value[:4]
            current_five_year = self.value[-2:]
            if judge_leap_year(current_year) and current_five_year >=13:
                current_day = str((int(current_five_year) - 1) * 5 + 2)
            else:
                current_day = str((int(current_five_year) - 1) * 5 + 1)
            return arrow.get(current_year+current_day,'YYYYDDD').format('YYYYMMDD')
        elif time_type == 'WEEK':
            current_year = self.value[:4]
            current_week = int(self.value[-2:])
            first_day_of_year = arrow.get(current_year,'YYYY')

            weekday_of_first_day = first_day_of_year.isocalendar()[2]
            if weekday_of_first_day !=0:  # 如果不是0 ,也就是星期日
                second_week_date =first_day_of_year.shift(days=8 - weekday_of_first_day)

            else:
                second_week_date = first_day_of_year.shift(days=1)

            if current_week <2:
                return second_week_date.shift(days=-7).format("YYYYMMDD")
            else:
                return second_week_date.shift(days=(current_week-2)*7).format("YYYYMMDD")

    def get_end(self):
        time_type = self.time_type
        if time_type == 'YEAR':
            return self.obj.ceil('year').format("YYYYMMDD")
        elif time_type == 'MON':
            return self.obj.ceil('month').format("YYYYMMDD")
        elif time_type == 'DAY':
            return self.value
        elif time_type == 'SEASON':
            season_list = ['01', '02', '03', '04']
            mon_first_list = [5, 8, 11, 2]
            return self.value[:4] +"{0:02d}".format(calendar.monthrange(int( self.value[:4]), mon_first_list[season_list.index(self.value[-2:])])[1])
        elif time_type == 'TEN':
            ten_list = ['01','02','03']
            ten_end_list = ['10','20',arrow.get(self.value[:6],"YYYYMM").ceil('month').format("DD")]
            return self.value[:6] + ten_end_list[ten_list.index(self.value[-2:])]
        elif time_type == 'FIVE':
            five_list = ['01','02','03','04','05','06']
            five_end_list = ['05','10','15','20','25',arrow.get(self.value[:6],"YYYYMM").ceil('month').format("DD")]
            return self.value[:6] + five_end_list[five_list.index(self.value[-2:])]
        elif time_type == 'FIVEYEAR':
            current_year = self.value[:4]
            current_five_year = self.value[-2:]
            if judge_leap_year(current_year) and current_five_year >=13:
                current_day = str((int(current_five_year) - 1) * 5 + 6)
            else:
                current_day = str((int(current_five_year) - 1) * 5 + 5)
            return arrow.get(current_year+current_day,'YYYYDDD').format('YYYYMMDD')
        elif time_type == 'WEEK':
            current_year = self.value[:4]
            current_week = int(self.value[-2:])
            first_day_of_year = arrow.get(current_year,'YYYY')

            weekday_of_first_day = first_day_of_year.isocalendar()[2]
            if weekday_of_first_day!=0:  # 如果不是0 ,也就是星期日
                second_week_date = first_day_of_year.shift(days=8 - weekday_of_first_day)

            else:
                second_week_date = first_day_of_year.shift(days=1)

            if current_week <2:
                return second_week_date.shift(days=-1).format("YYYYMMDD")
            else:
                return second_week_date.shift(days=((current_week-1)*7)-1).format("YYYYMMDD")

    def get_time(self):
        return self.value

    def get_ymd(self):
        time_type = self.time_type
        if Time.time_type_list.index(time_type) <= 2:
            self.value = self.obj.format("YYYYMMDD")
        elif time_type == 'SEASON':
            season_list = ['01','02','03','04']
            mon_first_list = ['0301','0601','0901','1201']
            if self.value[-2:] == "04":
               tt =  str(int(self.value[:4])-1) + mon_first_list[season_list.index(self.value[-2:])]
            else:
                tt = self.value[:4] + mon_first_list[season_list.index(self.value[-2:])]
            self.value = tt

        elif time_type == 'TEN':
            ten_list = ['01','02','03']
            ten_first_list = ['01','11','21']
            self.value =  self.value[:6] + ten_first_list[ten_list.index(self.value[-2:])]
        elif time_type == 'FIVE':
            five_list = ['01','02','03','04','05','06']
            five_first_list = ['01','06','11','16','21','26']
            self.value = self.value[:6] + five_first_list[five_list.index(self.value[-2:])]
        elif time_type == 'FIVEYEAR':
            current_year = self.value[:4]
            current_five_year = self.value[-2:]
            if judge_leap_year(current_year) and current_five_year >=13:
                current_day = str((int(current_five_year) - 1) * 5 + 2)
            else:
                current_day = str((int(current_five_year) - 1) * 5 + 1)
            self.value = arrow.get(current_year+current_day,'YYYYDDD').format('YYYYMMDD')
        elif time_type == 'WEEK':
            current_year = self.value[:4]
            current_week = int(self.value[-2:])
            first_day_of_year = arrow.get(current_year,'YYYY')

            weekday_of_first_day = first_day_of_year.isocalendar()[2]
            if weekday_of_first_day !=0:  # 如果不是0 ,也就是星期日
                second_week_date =first_day_of_year.shift(days=8 - weekday_of_first_day)

            else:
                second_week_date = first_day_of_year.shift(days=1)

            if current_week <2:
                self.value = second_week_date.shift(days=-7).format("YYYYMMDD")
            else:
                self.value = second_week_date.shift(days=(current_week-2)*7).format("YYYYMMDD")
        self.time_type = "DAY"
        self.regex = "YYYYMMDD"
        self.obj = arrow.get(self.value, self.regex)
        return self

def replace_char(string, char, index):
    string = list(string)
    string[index] = char
    return ''.join(string)


def judge_leap_year(current_year):
    '''
    判断是不是闰年
    :param current_year: 给定年份 ，int类型
    :return:
    '''
    if (current_year % 100 != 0 and current_year % 4 == 0) and (current_year % 100 == 0 and current_year % 400 == 0):
        return True
    else:
        return False
