from com.nriet.config import PathConfig
satellite_params_dict = {
    'map': {

        'mpEllipticalBoundary': True  # 控制图形呈圆形
        , 'mpFillOn': True
        ,'mpProjection' : "Orthographic"
        ,'mpCenterLatF' : 30.
        ,'mpCenterLonF' : 160.
        # ,'mpCenterRotF' :60
        # ,'mpCenterRotF' : 60.
        ,'mpLabelsOn'   : False
        ,'mpPerimLineColor'    :'red'

        , 'mpGeophysicalLineColor': 'black'
        , 'mpGeophysicalLineDashPattern': 0
        , 'mpGeophysicalLineThicknessF': 3
        ,'mpPerimLineDashPattern'    :3
        , 'mpNationalLineColor': 'black'  # 添加国界线颜色
        , 'mpNationalLineThicknessF': 3  # 国界线粗细
        , 'mpOutlineBoundarySets': 'National'  # 添加国界线
        , 'mpOutlineOn': True  # 陆地边界线开关
        # , 'mpProjection': "Satellite"  #
        , 'mpUSStateLineColor': 'transparent'
        , 'mpGridLatSpacingF': 10.
        , 'mpGridAndLimbOn': False
        , "mpInlandWaterFillColor": (151.0/255, 219.0/255, 242.0/255)
        , "mpOceanFillColor": (151.0/255, 219.0/255, 242.0/255)
        , "mpLandFillColor": 'grey'

        , 'nglDraw': False
        , 'nglFrame': False
        , 'nglMaximize': False  # 必须添加！！ 不然vP相关的动不了

        , 'vpXF': 0.12  # 到左边缘距离
        , 'vpYF': 0.875  # 到顶边缘距离
        , 'vpWidthF': 0.77  # 矩形边框宽度
        , 'vpHeightF': 0.77  # 矩形边框高度

    },

    'contour': {
        'cnConstFLabelOn': False
        , 'cnFillOn': True  # 填充颜色
        , 'cnInfoLabelOn': False  # 不显示等值线
        , 'cnLevelSelectionMode': 'ExplicitLevels'  # 使用自己给定的色阶和等值线属性来绘图
        , 'cnLineColor': 'black'  # 等值线颜色
        , 'cnLineLabelsOn': False  # 不显示等值线的值
        , 'cnNoDataLabelOn': False
        # , 'cnFillMode': "RasterFill"
        , 'lbLabelBarOn': True  # 显示色标
        , 'lbLabelFontHeightF': 0.009  # 色标字体--15号大小
        , 'lbLabelPosition': "Bottom"  # 色标置于底部
        , 'lbOrientation': "Horizontal"  # 水平显示
        , 'cnLinesOn': False  # 等值线数据是否显示
        , 'cnLineThicknessF': 2.5  # 等值线粗细
        , 'cnLineLabelInterval': 1  # 每条线上都显示数值
        , 'cnLineLabelDensityF': 0.7  # 数值密度

        , 'cnLineLabelFontHeightF': 0.009  # 数值字体大小
        , 'cnLabelMasking': True  # 等值线不穿过文字
        , 'cnSmoothingOn': True
        , 'cnSmoothingDistanceF': 0.001

        , 'pmLabelBarWidthF': 0.45  # 色标变窄
        , 'pmLabelBarHeightF': 0.06  # 色标变细
        , 'pmLabelBarOrthogonalPosF': 0.02  # 色标向下
        , 'pmTickMarkDisplayMode': "Never"  # 不显示坐标轴

        , 'nglDraw': False
        , 'nglFrame': False
        , 'nglMaximize': False  # 必须添加！！ 不然vP相关的动不了

    },

    "contourLine": {
        'cnFillOn': False  # 等值线之间不填充颜色
        , "cnLevelSelectionMode": "ExplicitLevels"
        , 'cnInfoLabelOn': False
        , 'cnLinesOn': True  # 模板中，开启等值线绘制
        , 'cnLineThicknessF': 1.0  # 等值线粗细
        , 'cnLineLabelsOn': True  # 是否显示数值
        , 'cnLineLabelInterval': 1  # 每条等值线显示多少个标签
        , 'cnLineLabelDensityF': 0.7  # 数值密
        , 'cnLabelMasking': False  # 等值线穿过文字
        , "cnLineColor": "black"  # 等值线黑色
        , "cnLineLabelFontHeightF": 0.01  # 等值线标签的字体高度（实际是字体大小），越大整个标签越大，
        , "cnMonoLineColor": True  # 默认是True；如果是True，等值线会取前景色；如果是False，才能按照我们的要求的颜色绘制等值线
        , "cnInfoLabelOn": False  # 不画等值线信息标签,就是右下角默认的文本说明
        , "nglDraw": False  # plot之后不绘制，只能通过手动调用的方式实现最终绘制
        , "nglFrame": False  # 不翻页
        , "nglMaximize": False  #

        , "tiMainOn": False  # 不显示主标题

        , 'vpXF': 0.12  # 到左边缘距离
        , 'vpYF': 0.875  # 到顶边缘距离
        , 'vpWidthF': 0.77  # 矩形边框宽度
        , 'vpHeightF': 0.77  # 矩形边框高度
    },

    'vector': {
        'pmTickMarkDisplayMode': 'Never'  # 不绘制坐标轴

        , 'vcFillArrowsOn': False
        , 'vcFillArrowHeadXF': 0.1  #
        , 'vcFillArrowHeadYF': 0.1  #
        , 'vcGlyphStyle': "CurlyVector"  # 弯曲的形状
        , "vcLevelSelectionMode": "AutomaticLevels"  # 风矢间隔
        , 'vcLineArrowThicknessF': 2.0  # 调整箭头粗细 :2.3
        , 'vcLineArrowHeadMaxSizeF': 0.01  # 调整箭头大小 :0.005
        , 'vcLineArrowColor': "black"  # 风矢图形颜色
        # , "vcMapDirection": False  # 在绘制垂直剖面图时，一定设置为False
        , 'vcMinDistanceF': 0.017  # 相邻风矢的间距
        , 'vcMinMagnitudeF': 0.0  # 最小风速
        , 'vcMonoLineArrowColor': True

        , 'vcRefAnnoArrowSpaceF': 1.0
        , 'vcRefAnnoBackgroundColor': 'white'
        , 'vcRefAnnoFontHeightF': 0.008
        , 'vcRefAnnoOn': True  # 绘制参考箭头，默认值为True
        , 'vcRefAnnoOrthogonalPosF': -0.090  # 垂直位置
        , 'vcRefAnnoParallelPosF': 0.999  # 水平位置
        , 'vcRefAnnoPerimOn': True  # 不绘制参考箭头的边框
        , 'vcRefAnnoSide': 'Top'
        , 'vcRefAnnoString1On': True  # 注释箭头上可绘制
        , 'vcRefAnnoString2On': True  # 注释箭头下可绘制
        , 'vcRefLengthF': 0.04  # 单位风速的参考长度

        , 'vcNoDataLabelOn': False # 无数据不显示文字
        , 'vcVectorDrawOrder': "PostDraw"  # 风矢优先绘制
        , 'vcWindBarbLineThicknessF':1.2 # 如果是风杆类型，线的宽度
        , 'vcWindBarbTickSpacingF':0.2 # 风杆类型时，每一根风羽箭头上的羽毛间距
        , 'vcWindBarbCalmCircleSizeF':-1 # 风杆类型时，圆形图大小 -1为黑点
        , 'vcWindBarbScaleFactorF': 3 # 风系数  国际标准和国内标准的转换 默认1
        , 'nglDraw': False
        , 'nglFrame': False
        , "nglMaximize": False
        , 'nglSpreadColors': True

        , "vpXF": 0.083
        , "vpYF": 0.892473
        , "vpWidthF": 0.866  # Change the aspect ratio, but
    },

    # 流线配置
    'streamLine': {
        'pmTickMarkDisplayMode': 'Never'  # 不绘制坐标轴
        , 'stArrowStride': '1'
        , 'stLineThicknessF': '1.5'
        , 'stLineStartStride': '1'
        # , 'stArrowLengthF': 0.008
        , 'nglDraw': False
        , 'nglFrame': False
        , "nglMaximize": False
        , 'nglSpreadColors': True
        , 'stStreamlineDrawOrder': "PostDraw"  # 风矢优先绘制

        , "vpXF": 0.083
        , "vpYF": 0.892473
        , "vpWidthF": 0.866  # Change the aspect ratio, but
    },

    # 数据源和单位
    # "datasource_unit": {
    #     "font_file_path":  PathConfig.CPCS_ROOT_PATH+"com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC",  # 微软雅黑
    #     "font_note_size": 14,
    #     "font_datasource_size": 13,
    #     "font_unit_size": 12,
    #     "interval": 6.5,  # 10对应15px 8对应12
    #     "top_padding": 55,  # 57对应65px  55对应63px
    #     "right_padding": 45,  # 45对应49px
    #     "unit_interval": 20,  # 注意这里是空格个数！
    # },
    "datasource_unit": {
         "font_file_path": PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC",
         # 微软雅黑
         "font_note_size": 35,
         "font_datasource_size": 35,
         "font_unit_size": 35,
         "interval": 6.5,  # 10对应15px 8对应12
         "top_padding": 100,  # 57对应65px  55对应63px
         "right_padding": 140,  # 45对应49px
         "unit_interval": 20,  # 注意这里是空格个数！
     },
    # 点图
    'polyMarker': {
        "gsMarkerIndex": 16 # 标准16
        , "gsMarkerSizeF": 0.004
    }
}
