# -*- coding: utf-8 -*-
import json
import logging
params_standard = {
    'region_type': 'wholeChina',  # 地域类型： wholeChina:中国(含南海); global:全球任意经纬度; hemisphere:南/北半球
    'output_img_path': '/home/nriet/PycharmProjects/test-master/main/test/wholeChina/',
    'output_img_name': 'wholeChina_test',
    'output_img_type': 'png',
    'output_img_max_width': 930,
    'output_img_dpi': 92,
    'main_title': '累计降雨量原始场',
    'sub_titles': [
        '起报: 20191119 预报: 20191121-20191125',
        '模式: DERF2.0 样本数: 4'
    ],

    'layers': [
        {
            'unit': '单位(mm)',
            'layer_type': 'contourMap',  # 绘图类型： contourMap:色斑; contour:等值线;vector:风场
            'intervals': [10., 30., 50., 100.],
            'legend_labels': [
                '<10',
                '10~F34~*~F~30',
                '30~F34~*~F~50',
                '50~F34~*~F~100',
                '>100'
            ],
            'colors': [
                [1., 1., 1.],
                [0.7, 1., 1.],
                [0.5, 0.8, 1.],
                [0.3, 0.7, 1.],
                [0.2, 0.3, 1.]
            ],
        },
    ]
}

request_json = json.dumps(params_standard)
logging.info(request_json)
