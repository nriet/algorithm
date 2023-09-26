#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/03/17
# @Author : xulh
# @File : OperatorUtils.py

import operator
import logging

def get_operator_fn(op):
    return {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '%': operator.mod,
        '^': operator.xor,
        "<": operator.lt,
        "<=": operator.le,
        "=": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        ">=": operator.ge,
    }[op]


def eval_binary_expr(op1, oper, op2):
    op1, op2 = op1, op2
    return get_operator_fn(oper)(op1, op2)


if __name__ == '__main__':
    logging.info(eval_binary_expr("6", "<=", 8))
    logging.info(eval_binary_expr("6", "+", "8"))

