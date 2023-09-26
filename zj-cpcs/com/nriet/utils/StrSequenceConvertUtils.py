def str_to_sequence(str):
    '''

    :param str: 原数组
    :return:
   　１．如果能被，分割， 如：
        1.1 ’1,2,3,4,‘ -->
    　
    '''
    try:
        return eval(str)
    except:
        return str