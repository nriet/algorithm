import numpy as np



def numpy_nan_equal(numpy_values_a,numpy_values_b):
    """
    此方法用于比较两个numpy数组是否相等，包括数值存在NaN的情况在内也能比较。
    :param numpy_values_a: 传入的numpy数组A
    :param numpy_values_b: 传入的numpy数组B
    :return: 返回比较结果
    """
    try:
        np.testing.assert_equal(numpy_values_a,numpy_values_b)
    except AssertionError:
        return False
    return True