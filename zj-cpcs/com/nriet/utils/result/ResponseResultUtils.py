'''
构造执行结果对象字典
'''

from com.nriet.config.ResponseCodeAndMsgEum import CIPAS_SUCCESS_CODE,SUCCESS_CODE,SUCCESS_MSG

def build_response_dict(response_dict=None, response_code=None, response_msg=None, serial_no=None,from_tianqin=0):
    '''
    构造执行结果对象字典
    :param response_dict: 原有结果
    :param response_code: 响应码
    :param response_msg: 响应消息
    :param serial_no: 序列号
    :param from_tianqin: 任务调用是否来源于产品加工流水线系统（定时+历史回溯+页面触发），默认不是。
    :return: dict
    '''
    if int(from_tianqin) == 1:
        response_dict = build_response_dict_from_tianqin(response_dict, response_code, response_msg,serial_no)
    else:
        response_dict=build_response_dict_from_cipas(response_dict, response_code, response_msg,serial_no)

    return response_dict


def build_response_dict_from_cipas(response_dict=None, response_code=None, response_msg=None,serial_no=None):
    if not response_dict:
        response_dict = {'response_code': CIPAS_SUCCESS_CODE}
    if serial_no:
        response_dict['serial_no'] = serial_no

    if response_code:
        response_dict['response_code'] = response_code
    if response_msg:
        response_dict['response_msg'] = response_msg
    return response_dict


def build_response_dict_from_tianqin(response_dict=None, response_code=None, response_msg=None, serial_no=None):
    if not response_dict:
        response_dict = {'monitor': {'returnCode': SUCCESS_CODE}}

    if serial_no:
        response_dict['serial_no'] = serial_no

    if response_code:
        response_dict['monitor']['returnCode'] = response_code

    if response_msg:
        response_dict['monitor']['returnMessage'] = response_msg

    return response_dict

def judge_response_result(response_dict=None):
    """
    验证响应结果是否成功
    :param response_dict:传入的响应结果
    :return: 响应结果正确True 错误False
    """
    judge = True
    if response_dict is None:
        judge = False
    else:
        if response_dict.get('response_code'):
            judge = response_dict.get('response_code') == CIPAS_SUCCESS_CODE
        elif response_dict['monitor'].get('returnCode'):
            judge= response_dict['monitor'].get('returnCode') == SUCCESS_CODE
    return judge

def response_result_convert(response_dict,convert_switch:int=0):
    """
    响应结果格式转换
    :param response_dict:待转换的响应消息字典
    :param convert_switch:是否使用天擎结构返回结构
    :return:
    """
    if int(convert_switch) ==0:
        return response_dict

    response_code = response_dict.pop('response_code')
    response_msg = response_dict.pop('response_msg',None)
    if response_code == CIPAS_SUCCESS_CODE:
        response_code = SUCCESS_CODE
        response_msg = SUCCESS_MSG
    monitor = {'returnCode':response_code,'returnMessage':response_msg}
    response_dict['monitor']=monitor
    return  response_dict


