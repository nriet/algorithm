import logging
import numpy as np
from com.nriet.algorithm.common.drawComponent.drawService.SequenceService import SequenceService
# figure = plt.figure(figsize=(7,10))
#
# subplot = figure.add_subplot()
# colors = layer.get('colors')
# linewidths = layer.get('linewidths')
# linestyles = layer.get('linestyles')
# legends = layer.get('legends')
# markers = layer.get('markers')
# legends_location = layer.get('legends_location')
# layer_main_title = layer.get('layer_main_title')
# layer_y_left_title = layer.get('layer_y_left_title')
# layer_x_buttom_title = layer.get('layer_x_buttom_title')
time=[1,2,3,4,5,6,7,8,9,10]
payment=[11,22,33,44,55,66,77,88,99,110]
payment1=[221,331,441,551,66,77,88,991,1101,121]

input_data = np.array([time,payment,payment1]).T
input_data = np.expand_dims(input_data,axis=0)


logging.info(input_data)
request_dict = {
    'output_img_type':'png',
    'output_img_path':'/usr/local/src/huxin/CPCS/com/nriet/algorithm/common/drawComponent/test/sequence/',
    'output_img_name':'土豆',
    'output_img_dpi':'200',
    'legends_location':2,
    'main_title': '我是大表哥',
    'sub_titles': ['我是小表哥'],
    'y_left_title':'我是左表哥',
    'x_buttom_title':'我是下表哥',
    'layers':[
        {
            'layer_type':'plot',
            'colors':['red'],
            'linewidths':[2],
            'labels':['西红柿'],
            'markers':['*'],
        },
        {
            'layer_type': 'bar',
            'data_rows':[2],
            'colors': ['orange'],
            'linewidths': [2],
            'labels': ['猫猫大侠'],
        }
    ]
}

sequence_service = SequenceService(input_data,request_dict=request_dict)
sequence_service.draw()



