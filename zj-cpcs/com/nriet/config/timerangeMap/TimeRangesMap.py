timerange_dict = {
    # default
    "001": {
        "range_concat": "",
        "range_formatter": "",
        "range_type": ""
    },
    # -拼接
    "002": {
        "range_concat": "-",
        "range_formatter": "",
        "range_type": ""
    },
    # -分割,-拼接
    "003": {
        "range_concat": "",
        "range_formatter": "-",
        "range_type": ""
    },
    # /分割
    "004": {
        "range_concat": "",
        "range_formatter": "/",
        "range_type": "pre"
    },
    # 中文
    "006": {
        "range_concat": "",
        "range_formatter": "U",
        "range_type": ""
    },
    # 开始时间为开始日期
    "007": {
        "range_concat": "",
        "range_formatter": "U",
        "range_type": "date"
    },  # /分割
    "008": {
        "range_concat": "-",
        "range_formatter": "/",
        "range_type": ""
    },
    "010": {
        "range_concat": "-",
        "range_formatter": "-",
        "range_type": ""
    },
    "009": {
        "range_concat": "",
        "range_formatter": "/",
        "range_type": ""
    },
    "011": {
        "range_concat": "",
        "range_formatter": "U",
        "range_type": "date_af"
    },
    "012": {
        "range_concat": "",
        "range_formatter": "U",
        "range_type": "split_year"
    },
    "013": {
        "range_concat": "-",
        "range_formatter": "U",
        "range_type": "split_year"
    },
    "014": {
        "range_concat": "-",
        "range_formatter": "U",
        "range_type": ""
    },
    "015": {
        "range_concat": "-",
        "range_formatter": "",
        "range_type": "split_year"
    },  # 月份前后滑动一个月
    "016": {
        "range_concat": "-",
        "range_formatter": "",
        "range_type": "runave_mon"
    },
    "020": {
        "range_concat": "-",
        "range_formatter": "U",
        "range_type": ""
    },
}
time_type_dict = {
    "day": {
        "0": "yyyyMMdd",
        "1": "yyyy-MM-dd",
        "2": "yyyy/MM/dd",
        "3": "yyyy年MM月dd日"
    },
    "five": {
        "0": "yyyyMMHH",
        "1": "yyyy-MM-HH",
        "2": "yyyy/MM/HH",
        "3": "yyyy年MM月HH候"
    },
    "five1": {
        "0": "yyyyHH",
        "1": "yyyy-HH",
        "2": "yyyy/HH",
        "3": "yyyy年HH候"
    },
    "mon": {
        "0": "yyyyMM",
        "1": "yyyy-MM",
        "2": "yyyy/MM",
        "3": "yyyy年MM月"
    },
    "season": {
        "0": "yyyySS",
        "1": "yyyy-SS",
        "2": "yyyy/SS",
        "3": "yyyy年XX"
    },
    "year": {
        "0": "yyyy",
        "3": "yyyy年"
    }
}
