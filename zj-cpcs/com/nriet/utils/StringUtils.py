def capitalize_str(old_str):
    if old_str:
        return "%s%s" % (old_str[0].upper(), old_str[1:])
    else:
        return old_str

def judge_str_is_number(x):
    '''
    判断字符串是不是数字，包括正负数，小数
    :param x:
    :return:
    '''
    try:
        x=float(x)
        return isinstance(x,float)
    except ValueError:
        return False
