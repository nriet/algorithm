# -*- coding: utf-8 -*-

'''
此类用于动态导入模块、动态导入类、动态实例化、动态执行对应方法
'''
import importlib


def import_module(abs_module_path):
    """
     动态导入模块
    :param abs_module_path: 模块绝对路径
    :return: 返回所需导入的模块
    """
    return importlib.import_module(abs_module_path)


def import_module_attr(abs_module_path, attr_name):
    """
    动态导入模块的属性，包括不限于:类、方法、自定义属性等
    :param abs_module_path: 模块绝对路径
    :param attr_name: 属性名称
    :return: 返回所需属性
    """
    if not abs_module_path or not attr_name:
        return -1
    model = importlib.import_module(abs_module_path)
    return model.getattr(attr_name)


def create_class_instance(abs_module_path, class_name, **kwargs):
    """
    动态导入模块，并实现类的实例化
    :param abs_module_path: 模块绝对路径
    :param class_name: 类名称
    :param kwargs: 实例化对象所需之形参，字典方式
    :return: 返回所需实例化对象
    """
    if not abs_module_path or not class_name:
        return -1
    model = importlib.import_module(abs_module_path)
    cls = getattr(model, class_name)
    return cls(**kwargs)


def has_attr_by_modname(mode, attr_name):
    '''
    根据属性名称判断mode是否包含该属性
    :param mode: 模块
    :param attr_name: 属性名称
    :return:
    '''
    if hasattr(mode, attr_name):
        return True
    else:
        return False


def get_attr(mode, attr_name):
    '''
    根据属性名称获取m属性
    :param mode:
    :param attr_name:
    :return:
    '''
    return getattr(mode, attr_name)
