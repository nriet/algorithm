import numpy as np


def formatting_data(format, saveType, data):
    '''
    :param format: 填写规则：integer类型，数值就表示需要保留的小数位数；填写示例：2，表示保留两位小数
    :param saveType: 填写规则：“round”表示四舍五入，“floor”表示向下舍入；填写示例：round，表示四舍五入
    :param data: data
    :return:
    '''
    if saveType == "round":
        data = np.around(data, decimals=int(format))
    elif saveType == "floor":
        format_str = "1".ljust(int(format) + 1, "0")
        data = np.floor(data*int(format_str), decimals=int(format))/int(format_str)
    return data


if __name__ == '__main__':
    list = [1.867, -1.864]
    formatting_data("2", "floor", np.asarray(list))
