import json
import logging
params_standard = {
    'region_type': 'global',  # 地域类型： wholeChina:中国(含南海); global:全球任意经纬度; hemisphere:南/北半球
    'output_img_path': '/home/nriet/PycharmProjects/test-master/main/test/global_/',
    'output_img_name': 'global_test',
    'output_img_type': 'png',
    'output_img_max_width': 930,
    'output_img_dpi': 92,
    'main_title': '全球海表温度平均场',
    'sub_titles': [
        '2019年11月24日'
    ],
    'x_values': [0, 60, 120, 180, 240, 300, 360],  # x轴实际值
    'y_values': [-90, -60, -30, 0, 30, 60, 90],  # y轴实际值
    'x_labels': ['0', '60E', '120E', '180', '120W', '60W', '0'],  # x轴显示值
    'y_labels': ['90S', '60S', '30S', '0', '30N', '60N', '90N'],  # y轴显示值
    # 'x_values': [0, 15, 30, 45, 60, 75, 90],  # x轴实际值
    # 'y_values': [0, 15, 30, 45, 60, 75, 90],  # y轴实际值
    # 'x_labels': ['0', '15E', '30E', '45E', '60E', '75E', '90E'],  # x轴显示值
    # 'y_labels': ['0', '15N', '30N', '45N', '60N', '75N', '90N'],  # y轴显示值
    # 'x_values': [0, 60, 50, 60],  # x轴实际值
    # 'y_values': [-90, -60, -30, 0, 30, 60, 90],  # y轴实际值
    # 'x_labels': ['30E', '40E', '50E', '60E'],  # x轴显示值
    # 'y_labels': ['90S', '60S', '30S', '0', '30N', '60N', '90N'],  # y轴显示值
    'layers': [
        {
            'unit': '单位: °C',
            'data_source': '数据: N0AA_OISSTv2_Highers_DAY',
            'regions':"0,360,-90,90", #startLon,endLon,startLat,endLat
            'layer_type': 'contourMap',  # 绘图类型： contourMap:色斑; contour:等值线;vector:风场
            'intervals': [
                0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30
            ],
            'colors': [
                [0., 0.3, 0.6],
                [0., 0.4, 0.8],
                [0.1, 0.5, 0.9],
                [0.3, 0.7, 1.],
                [0.6, 0.8, 1.],
                [0.7, 0.9, 1.],
                [1., 1., 0.7],
                [1., 0.9, 0.5],
                [1., 0.8, 0.2],
                [1., 0.4, 0.],
                [0.9, 0., 0],
                [0.7, 0., 0.]
            ]
        }
    ]
}

request_json = json.dumps(params_standard)
logging.info(request_json)
