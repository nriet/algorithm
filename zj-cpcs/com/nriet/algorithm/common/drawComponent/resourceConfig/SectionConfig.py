from com.nriet.config import PathConfig

section_params_dict = {
    'workstation': {
        'wkWidth': 1200
        , 'wkHeight': 1200
        # ,'wkBackgroundOpacityF' : 1.0
    },

    'contour': {
        'cnFillOn': True,

        'cnLevelSelectionMode': 'ExplicitLevels',

        'cnInfoLabelOn': False,
        'cnSmoothingOn': True,
        'cnFillMode': "RasterFill",
        "cnRasterSmoothingOn": True,

        'cnSmoothingDistanceF': 0.002,
        'cnConstFEnableFill': True,
        'cnNoDataLabelOn': False,
        'cnConstFLabelOn': False,
        'cnLinesOn': False,  # 模板中，不开启等值线绘制
        'cnLineThicknessF': 1.0,  # 等值线粗细
        'cnLineLabelsOn': False,  # 是否显示数值
        'cnLineLabelInterval': 1,  # 每条线上都显示数值
        # 'cnLineLabelDensityF': 0.7,  # 数值密
        'cnLabelMasking': False,  # 等值线穿过文字
        "cnLineColors": "black",  # 等值线黑色
        "cnLineLabelFontHeightF": 0.01,  # 等值线标签的字体高度（实际是字体大小），越大整个标签越大，
        "cnMonoLineColor": False,  # 默认是True；如果是True，等值线会取前景色；如果是False，才能按照我们的要求的颜色绘制等值线

        'nglDraw': False,
        'nglFrame': False,
        'nglMaximize': False,

        # 'pmLabelBarWidthF': 0.8,
        # 'pmLabelBarHeightF': 0.08,
        # 'pmLabelBarOrthogonalPosF': 0.047,

        'vpXF': 0.12,
        'vpYF': 0.888172,
        'vpWidthF': 0.852720,
        'vpHeightF': 0.546651,

        'lbLabelBarOn': False,
        # 'lbLabelFontHeightF': 0.012,
        # 'lbLabelFont': 25,
        # "lbLabelPosition": "Bottom",  # 色标置于底部
        # "lbOrientation": "Horizontal",  # 水平显示
        'trYReverse': True,

        'tmXTOn': False,
        'tmYROn': False,

        # 手动设置坐标值和显示值
        "tmXBMode": "Explicit",
        "tmYLMode": "Explicit",
        "nglYAxisType": "LinearAxis",

        # 坐标刻度线位置、字体大小
        "tmXBLabelDeltaF": -0.7  # 如果不设置,刻度线会朝着图形内;越负越不会再图形内
        , "tmYLLabelDeltaF": -0.7  # 同理
        , "tmXBLabelFontHeightF": 0.012  # 坐标显示值得字体大小
        , "tmYLLabelFontHeightF": 0.012  # 同理
        , "tmXBMajorThicknessF": 3
        , "tmYLMajorThicknessF": 3

        # 主坐标轴
        , "tmXBMajorLengthF": 0.009  # 刻度线长度
        , "tmYLMajorLengthF": 0.009  # 同理
        , "tmXBMajorOutwardLengthF": 0.009  # 作用类似于tmXBLabelDeltaF,不设置会向图形内;正数远离图形
        , "tmYLMajorOutwardLengthF": 0.009  # 同理

        , "tmXBMinorOn": True  # 手动打开副坐标
        , "tmXBMinorOutwardLengthF": 0.006  # 副坐标刻度线厚度
        , "tmXBMinorLineColor": "black"  # 副坐标刻度线颜色
        , "tmXBMinorLengthF": 0.006  # 副坐标刻度线长度
        , "tmYLMinorOn": True
        , "tmYLMinorOutwardLengthF": 0.006
        , "tmYLMinorLineColor": "black"
        , "tmYLMinorLengthF": 0.006,

        "tiXAxisFontHeightF": 0.015,
        "tiXAxisOn": False,
        "tiXAxisString": "depth(m)",
        "tiXAxisAngleF": "90",
        "tiXAxisOffsetXF": "-0.5",
        "tiXAxisOffsetYF": "0.35",
        "tiYAxisFontThicknessF": 2,

        # "tmEqualizeXYSizes": True,  # xy坐标轴等间隔值
        # "nglMaximize": False,  # 不占用整个画布大小
    },

    # 数据源和单位
    "datasource_unit": {
        "font_file_path": PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC",
        # 微软雅黑
        "font_note_size": 17,
        "font_datasource_size": 17,
        "font_unit_size": 17,
        "interval": 8,  # 10对应15px 8对应12
        "top_padding": 75,  # 57对应65px  55对应63px
        "right_padding": 45,  # 45对应49px
        "unit_interval": 20,  # 注意这里是空格个数！
    },

    'vector': {
        'pmTickMarkDisplayMode': 'Never'  # 不绘制坐标轴
        , 'tmXTOn': False
        , 'tmYROn': False
        , 'trYReverse': True
        # 手动设置坐标值和显示值
        , "tmXBMode": "Explicit"
        , "tmYLMode": "Explicit"
        , "nglYAxisType": "LinearAxis"
        # 'trYReverse': True,
        # 'trYLog':True,
        # "tmYUseLeft":False,

        # 坐标刻度线位置、字体大小
        , "tmXBLabelDeltaF": -0.7  # 如果不设置,刻度线会朝着图形内;越负越不会再图形内
        , "tmYLLabelDeltaF": -0.7  # 同理
        , "tmXBLabelFontHeightF": 0.012  # 坐标显示值得字体大小
        , "tmYLLabelFontHeightF": 0.012  # 同理
        , "tmXBMajorThicknessF": 3
        , "tmYLMajorThicknessF": 3

        # 主坐标轴
        , "tmXBMajorLengthF": 0.009  # 刻度线长度
        , "tmYLMajorLengthF": 0.009  # 同理
        , "tmXBMajorOutwardLengthF": 0.009  # 作用类似于tmXBLabelDeltaF,不设置会向图形内;正数远离图形
        , "tmYLMajorOutwardLengthF": 0.009  # 同理

        , "tmXBMinorOn": True  # 手动打开副坐标
        , "tmXBMinorOutwardLengthF": 0.006  # 副坐标刻度线厚度
        , "tmXBMinorLineColor": "black"  # 副坐标刻度线颜色
        , "tmXBMinorLengthF": 0.006  # 副坐标刻度线长度
        , "tmYLMinorOn": True
        , "tmYLMinorOutwardLengthF": 0.006
        , "tmYLMinorLineColor": "black"
        , "tmYLMinorLengthF": 0.006

        , "tiYAxisFontHeightF": 0.01
        , "tiYAxisFontThicknessF": 2

        , 'vcFillArrowsOn': False
        , 'vcFillArrowHeadXF': 1.0  # 箭头的箭大小vcRefAnnoOrthogonalPosF
        , 'vcFillArrowHeadYF': 1.0  # 箭头的箭大小
        , 'vcGlyphStyle': "CurlyVector"  # 指定风矢形状
        , "vcLevelSelectionMode": "AutomaticLevels"  # 风矢间隔
        , 'vcLineArrowThicknessF': 2.0  # 调整箭头粗细 :2.3
        , 'vcLineArrowHeadMaxSizeF': 0.01  # 调整箭头大小 :0.005
        , 'vcLineArrowColor': "black"  # 风矢图形颜色
        , "vcMapDirection": False  # 在绘制垂直剖面图时，一定设置为False
        , 'vcMinDistanceF': 0.0  # 相邻风矢的间距
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
        , 'vcRefLengthF': 0.03  # 单位风速的参考长度

        , 'vcNoDataLabelOn': False
        , 'vcVectorDrawOrder': "PostDraw"  # 风矢优先绘制

        , 'vpXF': 0.12
        , 'vpYF': 0.888172
        , 'vpWidthF': 0.852720
        , 'vpHeightF': 0.546651

        , 'nglDraw': False
        , 'nglFrame': False
        , "nglMaximize": False
        , 'nglSpreadColors': True

    },
    'contourLine': {
        'tmXTOn': False
        , 'tmYROn': False
        # 手动设置坐标值和显示值
        , "tmXBMode": "Explicit"
        , "tmYLMode": "Explicit"
        , "nglYAxisType": "LinearAxis"
        # 'trYReverse': True,
        # 'trYLog':True,
        # "tmYUseLeft":False,

        # 坐标刻度线位置、字体大小
        , "tmXBLabelDeltaF": -0.7  # 如果不设置,刻度线会朝着图形内;越负越不会再图形内
        , "tmYLLabelDeltaF": -0.7  # 同理
        , "tmXBLabelFontHeightF": 0.012  # 坐标显示值得字体大小
        , "tmYLLabelFontHeightF": 0.012  # 同理
        , "tmXBMajorThicknessF": 3
        , "tmYLMajorThicknessF": 3

        # 主坐标轴
        , "tmXBMajorLengthF": 0.009  # 刻度线长度
        , "tmYLMajorLengthF": 0.009  # 同理
        , "tmXBMajorOutwardLengthF": 0.009  # 作用类似于tmXBLabelDeltaF,不设置会向图形内;正数远离图形
        , "tmYLMajorOutwardLengthF": 0.009  # 同理

        , "tmXBMinorOn": True  # 手动打开副坐标
        , "tmXBMinorOutwardLengthF": 0.006  # 副坐标刻度线厚度
        , "tmXBMinorLineColor": "black"  # 副坐标刻度线颜色
        , "tmXBMinorLengthF": 0.006  # 副坐标刻度线长度
        , "tmYLMinorOn": True
        , "tmYLMinorOutwardLengthF": 0.006
        , "tmYLMinorLineColor": "black"
        , "tmYLMinorLengthF": 0.006

        , "tiYAxisFontHeightF": 0.01
        , "tiYAxisFontThicknessF": 2,
        'cnFillOn': False,
        'cnLevelSelectionMode': 'ExplicitLevels',
        'cnInfoLabelOn': False,
        'cnSmoothingOn': True,
        "cnRasterSmoothingOn": True,

        'cnSmoothingDistanceF': 0.002,
        'cnConstFEnableFill': True,
        'cnNoDataLabelOn': False,
        'cnConstFLabelOn': False,
        'cnLinesOn': True,  # 模板中，不开启等值线绘制
        'cnLineThicknessF': 2.5,  # 等值线粗细
        'cnLineLabelsOn': True,  # 是否显示数值
        'cnLineLabelInterval': 1,  # 每条线上都显示数值
        'cnLineLabelDensityF': 1,  # 数值密
        'cnLabelMasking': False,  # 等值线穿过文字
        "cnLineColor": "black",  # 等值线黑色
        "cnLineColors": "black",  # 等值线黑色
        "cnLineLabelFontHeightF": 0.008,  # 等值线标签的字体高度（实际是字体大小），越大整个标签越大，
        "cnMonoLineColor": True,  # 默认是True；如果是True，等值线会取前景色；如果是False，才能按照我们的要求的颜色绘制等值线

        'nglDraw': False,
        'nglFrame': False,
        'nglMaximize': False,

        'pmTickMarkDisplayMode': 'Never',  # 不绘制坐标轴

        'vpXF': 0.12,
        'vpYF': 0.888172,
        'vpWidthF': 0.852720,
        'vpHeightF': 0.546651,

        'trYReverse': True
    },
    "title_elements": {
        "font_file_path": PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC"
        # 微软雅黑
        , "font_main_size": 30  # 主标题20px
        , "font_sub_size": 20  # 副标题15px
        , "top_padding": 25  # 上边距40px
        , "title_padding": 8  # 标题间隔5px
    },
    "title_elements_2": {
        "font_file_path": PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC"
        # 微软雅黑
        , "font_main_size": 30  # 主标题20px
        , "font_sub_size": 20  # 副标题15px
        , "top_padding": 45  # 上边距40px
        , "title_padding": 8  # 标题间隔5px
    },
    # 绘制图例
    "label_bar_global": {
        "lbAutoManage": False,
        "lbPerimOn": False,
        "lbLabelAlignment": "InteriorEdges",
        "lbOrientation": "Horizontal",
        "lbMonoFillPattern": True,
        "lbLabelFontColor": "black",
        "lbLabelFontHeightF": "0.012",
        "vpWidthF": 0.785,
        "vpHeightF": 0.06,
        # 图例位置
        "labelbar_location": {
            "amParallelPosF": 0,
            "amOrthogonalPosF": 0.63
        }
    },
    # 点图
    'polyMarker': {
        "gsMarkerIndex": 16  # 标准16
        , "gsMarkerSizeF": 0.009
    },
    'logo_elements': {
        'LOGO':{
            'file_path':PathConfig.CPCS_ROOT_PATH+ 'com/nriet/algorithm/common/drawComponent/logoFiles/logo1200.png',
            'logo_location': (40, 40),
        },
    }

}
