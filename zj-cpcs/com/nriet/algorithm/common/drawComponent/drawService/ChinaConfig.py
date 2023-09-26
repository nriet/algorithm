from com.nriet.config import PathConfig

china_params_dict = {

    # 底板
    'contourMap': {
        'cnLevelSelectionMode': 'ExplicitLevels',
        'cnInfoLabelOn': False
        , 'cnFillOn': True
        , 'cnFillDrawOrder': 'PreDraw'
        , 'cnLinesOn': False
        , 'cnLevelSpacingF': 2.
        , 'cnLineLabelsOn': False
        , "cnSmoothingOn": True  # 是否平滑
        , "cnSmoothingDistanceF": 0.001
        # , "cnSmoothingTensionF": 0.005
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
        , 'mpLambertParallel2F': 48
        , 'mpPerimOn': True
        # , 'mpPerimLineColor' : 'black'
        , 'mpPerimDrawOrder': 'PostDraw'
        , 'mpPerimLineThicknessF': 5
        , 'mpGridLineDashPattern': 5
        , 'mpGridLineThicknessF': 0.5
        , 'mpLeftCornerLatF': 13.2578
        , 'mpRightCornerLatF': 50.6752
        , 'mpLeftCornerLonF': 78.9951
        , 'mpRightCornerLonF': 148.8066
        , 'mpFillOn': True
        # , 'mpDataSetName': '/nfsshare/cdbdata/algorithm/conductor/WMFS/EXTPRE/ysq/basedata/Earth..4'
        # , 'mpDataBaseVersion': 'MediumRes'
        # , 'mpAreaMaskingOn': True
        # , 'mpMaskAreaSpecifiers': 'China'
        # , 'mpMaskOutlineSpecifiers': 'China'
        , 'mpLandFillColor': 'transparent'
        , 'mpInlandWaterFillColor': 'transparent'
        , 'mpOceanFillColor': 'transparent'
        , 'mpOutlineBoundarySets': 'NoBoundaries'
        # , 'mpNationalLineColor': 'white'
        # , 'mpGeophysicalLineColor': 'white'
        # , 'mpNationalLineThicknessF': 0.0
        # , 'mpFillPatternBackground':255
        , 'pmTickMarkDisplayMode': 'Always'

        , 'tmXBOn': False
        , 'tmXTOn': False
        , 'tmYLOn': False
        , 'tmYROn': False

        , 'vpXF': 0.
        , 'vpYF': 1.
        , 'vpWidthF': 1.
        , 'vpHeightF': 1.
    },
    'vector': {
        'pmTickMarkDisplayMode': 'Never'  # 不绘制坐标轴

        , 'vcFillArrowsOn': False
        , 'vcFillArrowHeadXF': 0.1  # 箭头的箭大小vcRefAnnoOrthogonalPosF
        , 'vcFillArrowHeadYF': 0.1  # 箭头的箭大小
        , 'vcGlyphStyle': "CurlyVector"  # 指定风矢形状
        , "vcLevelSelectionMode": "AutomaticLevels"  # 风矢间隔
        , 'vcLineArrowThicknessF': 1.3  # 调整箭头粗细 :2.3
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
        , 'vcRefAnnoPerimThicknessF': 2.0  # 参考矩形的边框

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
    # 主体地理线
    'geo': {
        # file_names = ["HYDL.shp", "BOUL_S.shp", "HAX.shp", "nh/HFCP.shp",
        #               "BOUL_S2.shp", "BOUL_GY.shp", "BOUL_GW.shp"]

        # china_polygon
        "china_polygon": {
            "file_name": "china_mask3.shp",
            "type": "polygon",
            "gsColors": ['white'],  # 就是把第一个segments颜色设置为white
        },

        # river
        "river": {
            "file_name": "HYDL.shp",
            "type": "polyline",
            "gsLineThicknessF": 1.0,
            "gsLineColor": "blue",
            "gsLineDashPattern": 0
        },
        # province
        "province": {
            "file_name": "BOUL_S.shp",
            "type": "polyline",
            "gsLineThicknessF": 1.0,
            "gsLineColor": "black",
            "gsLineDashPattern": 0
        },
        # coastline
        "coastline": {
            "file_name": "HAX.shp",
            "type": "polyline",
            "gsLineThicknessF": 1.0,
            "gsLineColor": (0.0, 0.0, 153.0 / 255),
            "gsLineDashPattern": 0
        },
        # south_sea
        "south_sea": {
            "file_name": "nh/HFCP.shp",
            "type": "polyline",
            "gsLineThicknessF": 1.0,
            "gsLineColor": (0.0, 0.0, 153.0 / 255),
            "gsLineDashPattern": 0
        },
        # HongKong
        "HongKong": {
            "file_name": "BOUL_S2.shp",
            "type": "polyline",
            "gsLineThicknessF": 2.0,
            "gsLineColor": "black",
            "gsLineDashPattern": 2
        },
        # Established_boundaries
        "established_boundaries": {
            "file_name": "BOUL_GY.shp",
            "type": "polyline",
            "gsLineThicknessF": 2.0,
            "gsLineColor": "black",
            "gsLineDashPattern": 0
        },
        # Unestablished boundaries
        "unestablished_boundaries": {
            "file_name": "BOUL_GW.shp",
            "type": "polyline",
            "gsLineThicknessF": 2.0,
            "gsLineColor": "black",
            "gsLineDashPattern": 1
        },

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
        "lbPerimThicknessF": 2,
        "lbJustification": "CenterLeft",

        "lbBoxLinesOn": True,  # 添加labelbar外框线
        "lbBoxLineThicknessF": 0.2,  # labelbar外框线粗细

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

    # 比例尺
    "scale": {
        "font_file_path": PathConfig.CPCS_ROOT_PATH+"com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC",
        # 微软雅黑
        "scala_figure": "比例尺 1:20 000 000",
        "location": (221, 670),  # 比例尺在图片中的绝对位置
        # "txFontHeightF": 0.012097,
        # "txFontColor": "black",
        "tx_font_size": 15
    },

    # 数据源
    "datasource": {
        "font_file_path": PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC",
        # 微软雅黑
        "font_datasource_size": 13,
        "interval": 6.5,  # 10对应15px 8对应12
        "top_padding": 18,  # 57对应65px  55对应63px
        "right_padding": 5,  # 45对应49px
    },


    # 南海相关
    "south_sea": {
        # 底板
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
            , 'mpPerimLineThicknessF': 3
            # , 'mpPerimLineColor': 'black'
            , 'mpGridLineDashPattern': 5
            , 'mpGridLineThicknessF': 0.5
            , "mpLeftCornerLatF": 2.8
            , "mpRightCornerLatF": 23.3
            , "mpLeftCornerLonF": 106.7
            , "mpRightCornerLonF": 126.6
            , 'mpFillOn': True
            # , 'mpDataSetName': '/nfsshare/cdbdata/algorithm/conductor/WMFS/EXTPRE/ysq/basedata/Earth..4'
            # , 'mpDataBaseVersion': 'MediumRes'
            # , 'mpAreaMaskingOn': True
            # , 'mpMaskAreaSpecifiers': ['China']
            # , 'mpMaskOutlineSpecifiers': ['China']
            , 'mpLandFillColor': 'transparent'
            , 'mpInlandWaterFillColor': 'transparent'
            , 'mpOceanFillColor': 'transparent'
            , 'mpOutlineBoundarySets': 'NoBoundaries'
            # , 'mpNationalLineColor': 'white'
            # , 'mpGeophysicalLineColor': 'white'
            # , 'mpNationalLineThicknessF': 0.0

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

        'vector': {
            'pmTickMarkDisplayMode': 'Never'  # 不绘制坐标轴

            , 'vcFillArrowsOn': False
            , 'vcFillArrowHeadXF': 0.1  # 箭头的箭大小vcRefAnnoOrthogonalPosF
            , 'vcFillArrowHeadYF': 0.1  # 箭头的箭大小
            , 'vcGlyphStyle': "CurlyVector"  # 指定风矢形状
            , "vcLevelSelectionMode": "AutomaticLevels"  # 风矢间隔
            , 'vcLineArrowThicknessF': 1.3  # 调整箭头粗细 :2.3
            , 'vcLineArrowHeadMaxSizeF': 0.005  # 调整箭头大小 :0.005
            , 'vcLineArrowColor': "black"  # 风矢图形颜色
            # , "vcMapDirection": True  # 在绘制垂直剖面图时，一定设置为False
            , 'vcMinDistanceF': 0.017  # 相邻风矢的间距
            , 'vcMinMagnitudeF': 0.0  # 最小风速
            , 'vcMonoLineArrowColor': True
            , "vcRefAnnoOn": False
            , 'vcRefLengthF': 0.03  # 单位风速的参考长度

            , 'vcNoDataLabelOn': False
            , 'vcVectorDrawOrder': "PreDraw"  # 风矢优先绘制

            , 'nglDraw': False
            , 'nglFrame': False
            , "nglMaximize": False
            , 'nglSpreadColors': True

            # , 'vcRefMagnitudeF': 0.2

        },

        # 地理线
        'geo': {

            # file_names = ["nh/BOUL_G.shp", "BOUL_S.shp", "nh/BOUL_S2.shp", "nh/HAX.shp",
            #               "nh/HFCP.shp"]  # nh/BOUL_JDX.shp 九段线已经在已定国界中包含

            # china_polygon
            "china_polygon": {
                "file_name": "china_mask3.shp",
                "type": "polygon",
                "gsColors": ['white'],  # 就是把第一个segments颜色设置为white
            },

            # 国界
            "BOUL_G": {
                "file_name": "nh/BOUL_G.shp",
                "type": "polyline",
                "gsLineThicknessF": 1.0,
                "gsLineColor": "black",
                "gsLineDashPattern": 0
            },

            # 省界
            "BOUL_S": {
                "file_name": "BOUL_S.shp",
                "type": "polyline",
                "gsLineThicknessF": 1.0,
                "gsLineColor": "black",
                "gsLineDashPattern": 0
            },

            # 香港特别行政区边界
            "BOUL_S2": {
                "file_name": "nh/BOUL_S2.shp",
                "type": "polyline",
                "gsLineThicknessF": 1.0,
                "gsLineColor": "black",
                "gsLineDashPattern": 2
            },

            # 海岸线
            "HAX": {
                "file_name": "nh/HAX.shp",
                "type": "polyline",
                "gsLineThicknessF": 1.0,
                "gsLineColor": "blue",
                "gsLineDashPattern": 0
            },

            # 南海诸岛
            "HFCP": {
                "file_name": "nh/HFCP.shp",
                "type": "polyline",
                "gsLineThicknessF": 1.0,
                "gsLineColor": (0.0 / 255, 0.0 / 255, 153.0 / 255),
                "gsLineDashPattern": 0
            },
            # 南海九段线
            "JDX": {
                "file_name": "nh/BOUL_JDX.shp",
                "type": "polyline",
                "gsLineThicknessF": 2.0,
                "gsLineColor": 'black',
                "gsLineDashPattern": 0
            }

            # 省会点位（非必须）
        },
        # 比例尺
        'scale': {
            "scala_figure": "1:40 000 000"
            , "location": "118x3"
            , "txFontHeightF": 0.008
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
        "font_file_path": PathConfig.CPCS_ROOT_PATH+"com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC"
        # 微软雅黑
        , "lb_legend_font_size": 15  # 图例中文标题15px
        , "lb_unit_font_size": 12  # 图例中文单位12px
        , "interval": 1  # 标题和单位间隔
        , "inner_top_padding": 5  # 标题距图例边框补上距离
        , "outer_left_padding": 7  # 图例边框距图片左部距离
        , "outer_buttom_padding": 7  # 图例边框距图片底部距离
    }

}
