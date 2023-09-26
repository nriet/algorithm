import json
import logging
params_standard = {
    'region_type': 'section',  # 地域类型： wholeChina:中国(含南海); global:全球任意经纬度; hemisphere:南/北半球;section:剖面图
    'output_img_path': '/home/nriet/PycharmProjects/test-master/main/test/section/',
    'output_img_name': 'section_vector_test',
    'output_img_type': 'png',
    'output_img_max_width': 930,
    'output_img_dpi': 92,
    'main_title': '赤道地区(5S-5N)海表温度平均场演变',
    'sub_titles': [
        '2017年12月-2019年11月'
    ],

    'x_values': [60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0],
    'x_labels': ['60E', '80E', '100E', '120E', '140E', '160E', '180', '160W', '140W', '120W', '100W', '80W', '60W'],
    'y_values': [100.0, 150.0, 200.0, 250.0, 300.0, 400, 500, 700, 850, 1000],
    'y_labels': ['100', '150', '200', '250', '300', '400', '500', '700', '850', '1000'],

    'layers': [

        {
            'unit': '单位: °C',
            'data_source': '数据: N0AA_OISSTv2_MON',
            'regions': '0.5,359.5,5,366',
            'layer_type': 'contour',  # 绘图类型： contour:此处为等值线;vector:风场
            "intervals": [-5, -4, -3, -2, -1, -0.5, 0, 0.5, 1, 2, 3, 4, 5],
            'colors': [
                [0., 0.3, 0.6],
                [0., 0.4, 0.8],
                [0.1, 0.5, 0.9],
                [0.3, 0.7, 1.],
                [0.6, 0.8, 1.],
                [0.7, 0.9, 1.],
                [0.8, 1.0, 1.0],
                [0.9, 0.9, 1.],
                [1., 0.9, 1.],
                [1., 1., 0.7],
                [1., 0.9, 0.5],
                [1., 0.8, 0.2],
            ]
        },

        {
            'draw_regions': '0.5,359.5,5,366',
            'vector_unit': '0.02Pa/s',
            'vector_scale': '10',
            'layer_type': 'vector',  # 绘图类型： contourMap:色斑; contour:等值线;vector:风场
        },

    ]
}

# request_json = json.dumps(params_standard)
request_json = params_standard
logging.info(request_json)

