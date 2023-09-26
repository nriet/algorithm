from com.nriet.config import PathConfig

north_params_dict = {
    # 纯地图
    "map": {
        'mpProjection': 'LambertConformal'
        , 'mpGridAndLimbOn': False
        , 'mpLambertMeridianF': 105.0
        , 'mpLimitMode': 'Corners '
        , 'mpLambertParallel1F': 25
        , 'mpLambertParallel2F': 47
        , 'mpPerimOn': True

        , 'mpPerimDrawOrder': 'PostDraw'
        , 'mpPerimLineThicknessF': 5
        , 'mpGridLineDashPattern': 5
        , 'mpGridLineThicknessF': 0.5
        , 'mpLeftCornerLatF': 35.2578
        , 'mpRightCornerLatF': 50.6752
        , 'mpLeftCornerLonF': 78
        , 'mpRightCornerLonF': 148
        , 'mpFillOn': True

        , 'mpLandFillColor': 'transparent'
        , 'mpInlandWaterFillColor': 'transparent'
        , 'mpOceanFillColor': 'transparent'
        , 'mpOutlineBoundarySets': 'NoBoundaries'

        , 'pmTickMarkDisplayMode': 'Always'

        , 'tmXBOn': False
        , 'tmXTOn': False
        , 'tmYLOn': False
        , 'tmYROn': False

        , 'vpXF': 0.
        , 'vpYF': 1.
        , 'vpWidthF': 1.
        , 'vpHeightF': 0.5

        , "nglDraw": False  # plot之后不绘制，只能通过手动调用的方式实现最终绘制
        , "nglFrame": False  # 不翻页
        , "nglMaximize": False  #
    },

    # 地图+色斑
    'contourMap': {
        'cnLevelSelectionMode': 'ExplicitLevels',
        'cnInfoLabelOn': False
        , 'cnFillOn': True
        , 'cnFillMode': 'AreaFill'
        , 'cnFillDrawOrder': 'PreDraw'
        , 'cnLinesOn': False
        , 'cnLevelSpacingF': 2.
        , 'cnLineLabelsOn': False
        , "cnSmoothingOn": True  # 是否平滑
        , "cnSmoothingDistanceF": 0.001
        # 新绘图修改
        , "cnSmoothingTensionF": -0.001
        # 结束
        # ,"cnConstFEnableFill":True
        # ,"cnNoDataLabelOn":False
        # ,"cnConstFLabelOn":False

        , 'nglMaximize': False
        , 'nglDraw': False  # 关掉ngl绘图
        , 'nglFrame': False  # 关掉ngl绘图框架

        , 'lbLabelBarOn': False

        , 'mpProjection': 'LambertConformal'
        , 'mpGridAndLimbOn': False
        , 'mpLambertMeridianF': 105.0
        , 'mpLimitMode': 'Corners '
        , 'mpLambertParallel1F': 25
        , 'mpLambertParallel2F': 47
        , 'mpPerimOn': True
        # , 'mpPerimLineColor' : 'black'
        , 'mpPerimDrawOrder': 'PostDraw'
        , 'mpPerimLineThicknessF': 5
        , 'mpGridLineDashPattern': 5
        , 'mpGridLineThicknessF': 0.5
        , 'mpLeftCornerLatF': 30
        , 'mpRightCornerLatF': 53
        , 'mpLeftCornerLonF': 70
        , 'mpRightCornerLonF': 145
        , 'mpFillOn': True
        # 新绘图修改
        , 'mpDataSetName': '/nfsshare/cdbdata/algorithm/conductor/WMFS/EXTPRE/ysq/basedata/Earth..4'
        , 'mpDataBaseVersion': 'MediumRes'
        , 'mpAreaMaskingOn': True
        , 'mpMaskAreaSpecifiers': 'China'
        , 'mpMaskOutlineSpecifiers': 'China'
        , 'mpLandFillColor': 'white'
        , 'mpInlandWaterFillColor': 'white'
        , 'mpOceanFillColor': (151.0 / 255, 219.0 / 255, 242.0 / 255)
        , 'mpOutlineBoundarySets': 'NoBoundaries'
        , 'mpNationalLineColor': 'white'
        , 'mpGeophysicalLineColor': 'white'
        , 'mpNationalLineThicknessF': 0.0
        , 'mpFillPatternBackground': 255
        , 'pmTickMarkDisplayMode': 'Always'
        # 结束

        , 'tmXBOn': False
        , 'tmXTOn': False
        , 'tmYLOn': False
        , 'tmYROn': False

        , 'vpXF': 0.
        , 'vpYF': 1.0375
        , 'vpWidthF': 1.
        , 'vpHeightF': 0.5
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
        , "cnLineLabelFontHeightF": 0.008  # 等值线标签的字体高度（实际是字体大小），越大整个标签越大，
        , "cnMonoLineColor": True  # 默认是True；如果是True，等值线会取前景色；如果是False，才能按照我们的要求的颜色绘制等值线
        , "cnInfoLabelOn": False  # 不画等值线信息标签,就是右下角默认的文本说明
        , "cnLineDrawOrder": "PreDraw"
        , "cnLabelDrawOrder": "PreDraw"
        , "nglDraw": False  # plot之后不绘制，只能通过手动调用的方式实现最终绘制
        , "nglFrame": False  # 不翻页
        , "nglMaximize": False  #

        , "tiMainOn": False  # 不显示主标题
    },
    'vector': {
        'pmTickMarkDisplayMode': 'Never'  # 不绘制坐标轴

        , 'vcFillArrowsOn': False
        , 'vcFillArrowHeadXF': 0.1  # 箭头的箭大小vcRefAnnoOrthogonalPosF
        , 'vcFillArrowHeadYF': 0.1  # 箭头的箭大小
        , 'vcGlyphStyle': "CurlyVector"  # 指定风矢形状
        , "vcLevelSelectionMode": "AutomaticLevels"  # 风矢间隔
        , 'vcLineArrowThicknessF': 4  # 调整箭头粗细 :2.3
        , 'vcLineArrowHeadMaxSizeF': 0.005  # 调整箭头大小 :0.005
        , 'vcLineArrowColor': "black"  # 风矢图形颜色
        # , "vcMapDirection": True  # 在绘制垂直剖面图时，一定设置为False
        , 'vcMinDistanceF': 0.017  # 相邻风矢的间距
        , 'vcMinMagnitudeF': 0.0  # 最小风速
        , 'vcMonoLineArrowColor': True

        , 'vcRefAnnoArrowSpaceF': 1.0
        , 'vcRefAnnoBackgroundColor': 'white'
        , 'vcRefAnnoFontHeightF': 0.008
        , 'vcRefAnnoOn': True  # 绘制参考箭头，默认值为True
        , 'vcRefAnnoOrthogonalPosF': -0.680  # 垂直位置
        , 'vcRefAnnoParallelPosF': 0.063  # 水平位置
        , 'vcRefAnnoPerimOn': True  # 不绘制参考箭头的边框
        , 'vcRefAnnoPerimThicknessF': 10.0  # 参考矩形的边框

        , 'vcRefAnnoSide': 'Top'
        , 'vcRefAnnoString1On': True  # 注释箭头上可绘制
        , 'vcRefAnnoString2On': True  # 注释箭头下可绘制
        , 'vcRefLengthF': 0.03  # 单位风速的参考长度

        , 'vcNoDataLabelOn': False
        , 'vcVectorDrawOrder': "PreDraw"  # 风矢优先绘制
        # , "vcRefAnnoString2": "0.0"
        , 'nglDraw': False
        , 'nglFrame': False
        , "nglMaximize": False
        , 'nglSpreadColors': True

    },
    # 新绘图修改
    "title_elements": {
        "font_file_path": PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC"
        # 微软雅黑
        , "font_main_size": 75  # 主标题20px
        , "font_sub_size": 55  # 副标题15px
        , "top_padding": 120  # 上边距40px
        , "title_padding": 30  # 标题间隔5px
    },
    # 结束
    # 检验标题大小
    "title_jy_elements": {
        "font_file_path": PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC"
        # 微软雅黑
        , "font_main_size": 50  # 主标题20px
        , "font_sub_size": 43  # 副标题15px
        , "top_padding": 120  # 上边距40px
        , "title_padding": 30  # 标题间隔5px
    },

    # 点图
    'polyMarker': {
        "gsMarkerIndex": 16
        , "gsMarkerSizeF": 0.009
    },

    # 线或者框
    'polyline': {
        "rectangle": {
            "gsLineThicknessF": 5.0,
            "gsLineColor": "red",
            "gsLineDashPattern": 1
        },
        "shp": {
            "gsLineThicknessF": 1.0,
            "gsLineColor": "black",
            "gsLineDashPattern": 0
        },
        "shp_temp": {
            "gsLineThicknessF": 1.0,
            "gsLineColor": "black",
            "gsLineDashPattern": 0
        }

    },

    # 主体地理线
    'geo': {
        # file_names = ["HYDL.shp", "BOUL_S.shp", "HAX.shp", "nh/HFCP.shp",
        #               "BOUL_S2.shp", "BOUL_GY.shp", "BOUL_GW.shp"]

        # china_polygon
        # 新绘图修改
        # "china_polygon": {
        # "file_name": "china_mask3.shp",
        # "type": "polygon",
        # "gsColors": ['white'],  # 就是把第一个segments颜色设置为white
        # },
        # 结束

        # river
        # 新绘图修改
        "river": {
            "file_name": "HYDL.shp",
            "type": "polyline",
            "gsLineThicknessF": 6.0,
            "gsLineColor": (14.0 / 255, 190.0 / 255, 254.0 / 255),
            "gsLineDashPattern": 0
        },
        "lake": {
            "file_name": "HYDA.shp",
            "type": "polygon",
            "gsFillColor": (14.0 / 255, 190.0 / 255, 254.0 / 255),
            "gsLineThicknessF": 2.0,
            "gsLineColor": (14.0 / 255, 190.0 / 255, 254.0 / 255)
        },
        # province
        "province": {
            "file_name": "BOUL_S.shp",
            "type": "polyline",
            "gsLineThicknessF": 2.0,
            "gsLineColor": "black",
            "gsLineDashPattern": 0
        },
        # coastline
        "coastline": {
            "file_name": "HAX.shp",
            "type": "polyline",
            "gsLineThicknessF": 5.0,
            "gsLineColor": (100.0 / 255, 105.0 / 255, 91.0 / 255),
            "gsLineDashPattern": 0
        },
        # south_sea
        "south_sea": {
            "file_name": "nh/HFCP.shp",
            "type": "polyline",
            "gsLineThicknessF": 5.0,
            "gsLineColor": (0.0, 0.0, 153.0 / 255),
            "gsLineDashPattern": 0
        },
        # HongKong
        "HongKong": {
            "file_name": "BOUL_S2.shp",
            "type": "polyline",
            "gsLineThicknessF": 5.0,
            "gsLineColor": "black",
            "gsLineDashPattern": 2
        },
        # Established_boundaries
        "established_boundaries": {
            "file_name": "BOUL_GY.shp",
            "type": "polyline",
            "gsLineThicknessF": 10.0,
            "gsLineColor": "black",
            "gsLineDashPattern": 0
        },
        # Unestablished boundaries
        "unestablished_boundaries": {
            "file_name": "BOUL_GW.shp",
            "type": "polyline",
            "gsLineThicknessF": 10.0,
            "gsLineColor": "black",
            "gsLineDashPattern": 1
        },
        # 结束

    },
    # 中国图例
    "label_bar": {
        "lbAutoManage": False,
        "lbLabelAlignment": "BoxCenters",
        "lbTitleString": "fads",
        "lbTitleFontHeightF": 0.035,
        "lbTitleFontColor": "white",
        "lbPerimOn": True,
        "lbPerimColor": "black",
        "lbPerimThicknessF": 10,
        "lbJustification": "CenterLeft",
        # 新绘图修改
        "lbPerimFill": "0",
        "lbPerimFillColor": "white",

        "lbBoxLinesOn": True,  # 添加labelbar外框线
        "lbBoxLineThicknessF": 2,  # labelbar外框线粗细
        "lbBoxLineColor": "black",
        # 结束

        "lbBoxMajorExtentF": 0.8,
        "lbMonoFillPattern": True,
        "lbLabelJust": "CenterLeft",
        "lbLabelFontColor": "black",
        "vpWidthF": 0.11,
        # 图例位置
        "labelbar_location": {
            "amJust": "BottomLeft",
            "amParallelPosF": -0.489247,
            "amOrthogonalPosF": 0.4856322
        },
    },
    # 中国检验图例
    "label_bar_test": {
        "lbAutoManage": True,
        "lbLabelAlignment": "BoxCenters",
        "lbTitleString": "fads",
        "lbTitleFontHeightF": 0.035,
        "lbTitleFontColor": "white",
        "lbPerimOn": False,
        "lbJustification": "CenterLeft",
        # 新绘图修改
        "lbPerimFill": "0",
        "lbPerimFillColor": "white",

        "lbBoxLinesOn": True,  # 添加labelbar外框线
        "lbBoxLineThicknessF": 2,  # labelbar外框线粗细
        "lbBoxLineColor": "black",
        # 结束

        "lbBoxMajorExtentF": 0.8,
        "lbMonoFillPattern": True,
        "lbLabelJust": "CenterLeft",
        "lbLabelFontColor": "white",
        "vpWidthF": 0.05,
        # 图例位置
        "labelbar_location": {
            "amJust": "BottomLeft",
            "amParallelPosF": -0.469247,
            "amOrthogonalPosF": 0.4056322
        },
    },
    # 比例尺
    "scale": {
        "font_file_path": PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC",
        # 微软雅黑
        "scala_figure": "比例尺 1:20 000 000",
        # 新绘图修改
        "location": (665, 2017),  # 比例尺在图片中的绝对位置
        # 结束
        # "txFontHeightF": 0.012097,
        # "txFontColor": "black",
        "tx_font_size": 15
    },
    # 检验数据
    "numbers": {
        "font_file_path": PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC",
        "tx_font_size": 35
    },

    # 数据源
    "datasource": {
        "font_file_path": PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC",
        # 微软雅黑
        "font_datasource_size": 40,
        "interval": 10,  # 10对应15px 8对应12
        "top_padding": 45,  # 57对应65px  55对应63px
        "right_padding": 10,  # 45对应49px
    },

    # 南海相关
    "south_sea": {
        # 纯地图
        "map": {
            'nglMaximize': False
            , 'nglDraw': False  # 关掉ngl绘图
            , 'nglFrame': False  # 关掉ngl绘图框架

            , 'lbLabelBarOn': False

            , 'mpProjection': 'LambertConformal'
            , 'mpGridAndLimbOn': False
            , 'mpLambertMeridianF': 105.0
            , 'mpLimitMode': 'Corners '
            , 'mpLambertParallel1F': 25
            , 'mpLambertParallel2F': 48
            , 'mpPerimOn': True
            , 'mpPerimLineThicknessF': 3
            , 'mpGridLineDashPattern': 5
            , 'mpGridLineThicknessF': 0.5
            , "mpLeftCornerLatF": 2.8
            , "mpRightCornerLatF": 23.3
            , "mpLeftCornerLonF": 106.7
            , "mpRightCornerLonF": 126.6
            , 'mpFillOn': True

            , 'mpLandFillColor': 'transparent'
            , 'mpInlandWaterFillColor': 'transparent'
            , 'mpOceanFillColor': 'transparent'
            , 'mpOutlineBoundarySets': 'NoBoundaries'

            , 'pmTickMarkDisplayMode': 'Always'

            , 'tmXBOn': False
            , 'tmXTOn': False
            , 'tmYLOn': False
            , 'tmYROn': False

            , 'vpXF': 0.
            , 'vpYF': 1.
            , "vpWidthF": 0.18
            , "vpHeightF": 0.18
        },

        # 地图+色斑
        'contourMap': {
            'cnLevelSelectionMode': 'ExplicitLevels'
            , 'cnInfoLabelOn': False
            , 'cnFillOn': True
            , 'cnFillDrawOrder': 'PreDraw'
            , 'cnLinesOn': False
            , 'cnLevelSpacingF': 20.0
            , 'cnLineLabelsOn': False
            , "cnSmoothingOn": True  # 是否平滑
            , "cnSmoothingDistanceF": 0.01
            , "cnSmoothingTensionF": 0.01
            , 'nglMaximize': False
            , 'nglDraw': False  # 关掉ngl绘图
            , 'nglFrame': False  # 关掉ngl绘图框架

            , 'lbLabelBarOn': False

            , 'mpProjection': 'LambertConformal'
            , 'mpGridAndLimbOn': False
            , 'mpLambertMeridianF': 105.0
            , 'mpLimitMode': 'Corners '
            , 'mpLambertParallel1F': 25
            , 'mpLambertParallel2F': 48
            , 'mpPerimOn': True
            # 新绘图修改
            , 'mpPerimLineThicknessF': 10
            , 'mpPerimLineColor': 'black'
            , 'mpGridLineDashPattern': 5
            , 'mpGridLineThicknessF': 0.5
            , "mpLeftCornerLatF": 2.8
            , "mpRightCornerLatF": 23.3
            , "mpLeftCornerLonF": 106.7
            , "mpRightCornerLonF": 126.6
            , 'mpFillOn': True
            , 'mpDataSetName': '/nfsshare/cdbdata/algorithm/conductor/WMFS/EXTPRE/ysq/basedata/Earth..4'
            , 'mpDataBaseVersion': 'MediumRes'
            , 'mpAreaMaskingOn': True
            , 'mpMaskAreaSpecifiers': ['China']
            , 'mpMaskOutlineSpecifiers': ['China']
            , 'mpLandFillColor': 'white'
            , 'mpInlandWaterFillColor': 'white'
            , 'mpOceanFillColor': (151.0 / 255, 219.0 / 255, 242.0 / 255)
            , 'mpOutlineBoundarySets': 'NoBoundaries'
            , 'mpNationalLineColor': 'white'
            , 'mpGeophysicalLineColor': 'white'
            , 'mpNationalLineThicknessF': 0.0
            # 结束

            , 'pmTickMarkDisplayMode': 'Always'

            , 'tmXBOn': False
            , 'tmXTOn': False
            , 'tmYLOn': False
            , 'tmYROn': False

            , 'vpXF': 0.
            , 'vpYF': 1.
            , "vpWidthF": 0.18
            , "vpHeightF": 0.18
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
            , "cnLineLabelFontHeightF": 0.008  # 等值线标签的字体高度（实际是字体大小），越大整个标签越大，
            , "cnMonoLineColor": True  # 默认是True；如果是True，等值线会取前景色；如果是False，才能按照我们的要求的颜色绘制等值线
            , "cnInfoLabelOn": False  # 不画等值线信息标签,就是右下角默认的文本说明
            , "nglDraw": False  # plot之后不绘制，只能通过手动调用的方式实现最终绘制
            , "cnLineDrawOrder": "PreDraw"
            , "nglFrame": False  # 不翻页
            , "nglMaximize": False  #

            , "tiMainOn": False  # 不显示主标题
        },

        'vector': {
            'pmTickMarkDisplayMode': 'Never'  # 不绘制坐标轴

            , 'vcFillArrowsOn': False
            , 'vcFillArrowHeadXF': 0.1  # 箭头的箭大小vcRefAnnoOrthogonalPosF
            , 'vcFillArrowHeadYF': 0.1  # 箭头的箭大小
            , 'vcGlyphStyle': "CurlyVector"  # 指定风矢形状
            , "vcLevelSelectionMode": "AutomaticLevels"  # 风矢间隔
            , 'vcLineArrowThicknessF': 3  # 调整箭头粗细 :2.3
            , 'vcLineArrowHeadMaxSizeF': 0.005  # 调整箭头大小 :0.005
            , 'vcLineArrowColor': "black"  # 风矢图形颜色
            # , "vcMapDirection": True  # 在绘制垂直剖面图时，一定设置为False
            , 'vcMinDistanceF': 0.017  # 相邻风矢的间距
            , 'vcMinMagnitudeF': 0.0  # 最小风速
            , 'vcMonoLineArrowColor': True
            , "vcRefAnnoOn": False
            , 'vcRefLengthF': 0.05  # 单位风速的参考长度

            , 'vcNoDataLabelOn': False
            , 'vcVectorDrawOrder': "PreDraw"  # 风矢优先绘制

            , 'nglDraw': False
            , 'nglFrame': False
            , "nglMaximize": False
            , 'nglSpreadColors': True

            # , 'vcRefMagnitudeF': 0.2

        },

        # 点图
        'polyMarker': {
            "gsMarkerIndex": 16
            , "gsMarkerSizeF": 0.003
        },

        # 地理线
        'geo': {

            # file_names = ["nh/BOUL_G.shp", "BOUL_S.shp", "nh/BOUL_S2.shp", "nh/HAX.shp",
            #               "nh/HFCP.shp"]  # nh/BOUL_JDX.shp 九段线已经在已定国界中包含

            # china_polygon
            # 新绘图修改
            # "china_polygon": {
            # "file_name": "china_mask3.shp",
            # "type": "polygon",
            # "gsColors": ['white'],  # 就是把第一个segments颜色设置为white
            # },

            # 国界
            "BOUL_G": {
                "file_name": "nh/BOUL_G.shp",
                "type": "polyline",
                "gsLineThicknessF": 5.0,
                "gsLineColor": "black",
                "gsLineDashPattern": 0
            },

            # 省界
            "BOUL_S": {
                "file_name": "BOUL_S.shp",
                "type": "polyline",
                "gsLineThicknessF": 3.0,
                "gsLineColor": "black",
                "gsLineDashPattern": 0
            },

            # 香港特别行政区边界
            "BOUL_S2": {
                "file_name": "nh/BOUL_S2.shp",
                "type": "polyline",
                "gsLineThicknessF": 4.0,
                "gsLineColor": "black",
                "gsLineDashPattern": 2
            },

            # 海岸线
            "HAX": {
                "file_name": "nh/HAX.shp",
                "type": "polyline",
                "gsLineThicknessF": 4.0,
                "gsLineColor": (100.0 / 255, 105.0 / 255, 91.0 / 255),
                "gsLineDashPattern": 0
            },

            # 南海诸岛
            "HFCP": {
                "file_name": "nh/HFCP.shp",
                "type": "polyline",
                "gsLineThicknessF": 4.0,
                "gsLineColor": (0.0 / 255, 0.0 / 255, 153.0 / 255),
                "gsLineDashPattern": 0
            },
            # 南海九段线
            "JDX": {
                "file_name": "nh/BOUL_JDX.shp",
                "type": "polyline",
                "gsLineThicknessF": 5.0,
                "gsLineColor": 'black',
                "gsLineDashPattern": 0
            }

            # 省会点位（非必须）
        },
        # 比例尺
        'scale': {
            "scala_figure": "1:40 000 000"
            , "location": "118x3"
            , "txFontHeightF": 0.009
            , "txFontColor": "black"
        },
        # 小地图位置
        'location': {
            "amParallelPosF": 0.489247
            , "amOrthogonalPosF": 0.4856322
            , "amJust": "BottomRight"
        }
    },

    "legend_unit": {
        "font_file_path": PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC"
        # 微软雅黑
        , "lb_legend_font_size": 45  # 图例中文标题15px
        , "lb_unit_font_size": 35  # 图例中文单位12px
        , "interval": 5  # 标题和单位间隔
        , "inner_top_padding": 5  # 标题距图例边框补上距离
        , "outer_left_padding": 20  # 图例边框距图片左部距离
        , "outer_buttom_padding": 10  # 图例边框距图片底部距离
    },
    'logo_elements': {
        # 新绘图修改
        'LOGO': {
            'file_path': PathConfig.CPCS_ROOT_PATH + 'com/nriet/algorithm/common/drawComponent/logoFiles/logo.png',
            'logo_location': (40, 40),
        },
        # 结束

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
    # 结束

}
