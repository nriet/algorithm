from com.nriet.config import PathConfig

global_params_dict = {
    # 纯地图
    "map": {
        "mpGridAndLimbOn": False
        , "mpGridLineColor": 'black'
        , "mpGridLineDashPattern": 2
        , "mpGridLineThicknessF": 1

        , "mpFillOn": True  # 填色地图
        , "mpLandFillColor": [1, 1, 1]
        , "mpGeophysicalLineColor": 'black'  # 海陆分界线颜色
        , "mpGeophysicalLineThicknessF": 3  # 海陆分界线粗细
        , "mpShapeMode": "FreeAspect"
        , "mpInlandWaterFillColor": 'white'
        , "mpOceanFillColor": 'white'

        , "nglDraw": False  # plot之后不绘制，只能通过手动调用的方式实现最终绘制
        , "nglFrame": False  # 不翻页
        , "nglMaximize": False  #

        , 'pmTickMarkDisplayMode': 'Never'
        , "vpXF": 0.083
        , "vpYF": 0.892473
        , "vpWidthF": 0.866  # Change the aspect ratio, but
    },

    "contourLine": {
        'cnFillOn': False  # 等值线之间不填充颜色
        , "cnLevelSelectionMode": "ExplicitLevels"
        # , 'cnInfoLabelOn': False
        , 'cnLinesOn': True  # 模板中，开启等值线绘制
        , 'cnLineThicknessF': 4.0  # 等值线粗细
        , 'cnLineLabelsOn': True  # 是否显示数值
        , 'cnLineLabelInterval': 1  # 间隔几条等值线标注
        , 'cnLineLabelDensityF': 0.75  # 数值密
        , 'cnLabelMasking': True  # 等值线穿过文字
        , "cnLineColor": "black"  # 等值线黑色
        , "cnLineLabelFontHeightF": 0.008  # 等值线标签的字体高度（实际是字体大小），越大整个标签越大，
        , "cnLineLabelBackgroundColor": -1  # 等值线标签背景颜色；如果是-1，背景为透明，默认值是0，背景为白色
        , "cnMonoLineColor": True  # 默认是True；如果是True，等值线会取前景色；如果是False，才能按照我们的要求的颜色绘制等值线
        , "cnInfoLabelOn": False  # 不画等值线信息标签,就是右下角默认的文本说明
        , "nglDraw": False  # plot之后不绘制，只能通过手动调用的方式实现最终绘制
        , "nglFrame": False  # 不翻页
        , "nglMaximize": False  #

        , "tiMainOn": False  # 不显示主标题

        , "vpXF": 0.083
        , "vpYF": 0.892473
        , "vpWidthF": 0.866  # # Change the aspect ratio, but
    },

    "contourMap": {
        "cnConstFLabelOn": False
        , "cnFillOn": True
        , "cnInfoLabelOn": False  # 不画等值线信息标签
        , "cnLevelSelectionMode": "ExplicitLevels"
        , "cnLinesOn": False  # 去除等值线
        , "cnLineLabelsOn": False  # 不显示数值
        , "cnNoDataLabelOn": False
        , "cnSmoothingOn": False  # 是否平滑
        , "cnSmoothingDistanceF": 0.1
        , "cnFillDrawOrder": "PreDraw"

        , "lbLabelBarOn": False  # 显示色标
        # , "lbLabelFontHeightF": 0.009  # 色标字体--15号大小
        # , "lbLabelPosition": "Bottom"  # 色标置于底部
        # , "lbOrientation": "Horizontal"  # 水平显示

        , "mpGridAndLimbOn": False  # 绘制格点线
        , "mpGridLineColor": 'black'
        , "mpGridLineDashPattern": 2
        , "mpGridLineThicknessF": 1

        # , "mpFillOn": True  # 填色地图
        , "mpLandFillColor": 'white'
        , "mpGeophysicalLineColor": 'black'  # 海陆分界线颜色
        , "mpGeophysicalLineThicknessF": 4  # 海陆分界线粗细
        , "mpShapeMode": "FreeAspect"
        , "mpInlandWaterFillColor": 'white'
        , "mpOceanFillColor": 'white'

        , "nglDraw": False  # plot之后不绘制，只能通过手动调用的方式实现最终绘制
        , "nglFrame": False  # 不翻页
        , "nglMaximize": False  #

        # , "pmLabelBarWidthF": 0.485  # 色标变窄
        # , "pmLabelBarHeightF": 0.11  # 色标变细     实际宽度 200 *0.11 = 22px
        # , "pmLabelBarOrthogonalPosF": 0.068  # 色标向下 实际宽度 250 *0.08 = 20px
        , 'pmTickMarkDisplayMode': 'Never'

        , "tiMainOn": False  # 不显示主标题

        , "vpXF": 0.083
        , "vpYF": 0.892473
        , "vpWidthF": 0.866  # Change the aspect ratio, but

    },

    'vector': {
        'pmTickMarkDisplayMode': 'Never'  # 不绘制坐标轴

        , 'vcGlyphStyle': "CurlyVector"  # 指定风矢形状
        , 'vcFillArrowHeadXF': 0.3  # 箭头x分量长度
        , 'vcFillArrowHeadYF': 0.1  # 箭头y分量长度
        , 'vcFillArrowHeadMinFracXF': 0.5
        , 'vcFillArrowHeadMinFracYF': 0.5
        , 'vcFillArrowHeadInteriorXF': 0.2  # 0.25
        , 'vcFillArrowHeadEdgeThicknessF': 0.4
        , 'vcFillArrowWidthF': 0.03
        , 'vcFillArrowEdgeColor': 'white'
        , 'vcFillArrowFillColor': 'black'
        , "vcLevelSelectionMode": "AutomaticLevels"  # 风矢间隔
        , 'vcLineArrowThicknessF': 3.0  # 调整箭头粗细 :2.3
        , 'vcLineArrowHeadMaxSizeF': 0.006  # 调整箭头大小 :0.005, 0.008
        , 'vcLineArrowHeadMinSizeF': 0.003
        , 'vcLineArrowColor': "black"  # 风矢图形颜色
        # , "vcMapDirection": False  # 在绘制垂直剖面图时，一定设置为False
        , 'vcMinDistanceF': 0.02  # 相邻风矢的间距
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
        , 'vcRefLengthF': 0.035  # 单位风速的参考长度,0.04

        , 'vcNoDataLabelOn': False
        , 'vcVectorDrawOrder': "PostDraw"  # 风矢优先绘制

        , 'nglDraw': False
        , 'nglFrame': False
        , "nglMaximize": False
        , 'nglSpreadColors': True

        , "vpXF": 0.083
        , "vpYF": 0.892473
        , "vpWidthF": 0.866  # Change the aspect ratio, but
    },
    # 流线
    'streamLine': {
        'pmTickMarkDisplayMode': 'Never'  # 不绘制坐标轴
        , 'stLineStartStride': 5  # 每5个格点才能启动一条流线
        , 'stArrowStride': 5  # 每5个格点绘制一个箭头
        , 'stLineThicknessF': 4.0  # 流线粗细
        , 'stArrowLengthF': 0.003  # 箭头大小
        , 'stStreamlineDrawOrder': "PostDraw"  # 风矢优先绘制

        , 'nglDraw': False
        , 'nglFrame': False
        , "nglMaximize": False
        , 'nglSpreadColors': True
    },
    # 点图
    'polyMarker': {
        "gsMarkerIndex": 16  # 标准16
        , "gsMarkerSizeF": 0.015
    },
    # 点线图（台风轨迹）
    'polyMarkerLine': {
        "gsMarkerIndex": 16  # 标准16
        , "gsMarkerSizeF": 0.006
        , "gsLineThicknessF": 5.0
        , "gsLineDashPattern": 0
        , "gsLineColor": "black"
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

        # river
        "river": {
            "file_name": "HYDL.shp",
            "type": "polyline",
            "gsLineThicknessF": 4.0,
            "gsLineColor": "blue",
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
        # HongKong
        "HongKong": {
            "file_name": "BOUL_S2.shp",
            "type": "polyline",
            "gsLineThicknessF": 5.0,
            "gsLineColor": "black",
            "gsLineDashPattern": 2
        },

        # coastline
        "coastline": {
            "file_name": "HAX.shp",
            "type": "polyline",
            "gsLineThicknessF": 2.0,
            "gsLineColor": (0.0, 0.0, 153.0 / 255),
            "gsLineDashPattern": 0
        },

        # Established_boundaries
        "established_boundaries": {
            "file_name": "BOUL_GY.shp",
            "type": "polyline",
            "gsLineThicknessF": 5.0,
            "gsLineColor": "black",
            "gsLineDashPattern": 0
        },
        # Unestablished boundaries
        "unestablished_boundaries": {
            "file_name": "BOUL_GW.shp",
            "type": "polyline",
            "gsLineThicknessF": 5.0,
            "gsLineColor": "black",
            "gsLineDashPattern": 1
        },
    },
    # 坐标轴设置
    "tickmack": {
        # 坐标轴总开关
        "tmXTOn": False
        , "tmYROn": False

        # 手动设置坐标值和显示值
        , "tmXBMode": "Explicit"
        , "tmYLMode": "Explicit"

        # 坐标刻度线位置、字体大小
        , "tmXBLabelDeltaF": -0.7  # 如果不设置,刻度线会朝着图形内;越负越不会再图形内
        , "tmYLLabelDeltaF": -0.7  # 同理
        , "tmXBLabelFontHeightF": 0.015  # 坐标显示值得字体大小
        , "tmYLLabelFontHeightF": 0.015  # 同理
        , "tmXBMajorThicknessF": 4  # 主刻度线X粗细
        , "tmYLMajorThicknessF": 4  # 主刻度线Y粗细

        , "tmXBMinorThicknessF": 2  # 边框粗细
        , "tmYLMinorThicknessF": 2  # 边框粗细

        # 主坐标轴
        , "tmXBMajorLengthF": 0.009  # 刻度线长度
        , "tmYLMajorLengthF": 0.009  # 同理
        , "tmXBMajorOutwardLengthF": 0.009  # 作用类似于tmXBLabelDeltaF,不设置会向图形内;正数远离图形
        , "tmYLMajorOutwardLengthF": 0.009  # 同理

        , "tmBorderThicknessF": 5.0  # 边框粗细

        # 副坐标轴
        , "tmXBMinorOn": True  # 手动打开副坐标
        , "tmXBMinorOutwardLengthF": 0.006  # 副坐标刻度线厚度
        , "tmXBMinorLineColor": "black"  # 副坐标刻度线颜色
        , "tmXBMinorLengthF": 0.006  # 副坐标刻度线长度
        , "tmYLMinorOn": True
        , "tmYLMinorOutwardLengthF": 0.006
        , "tmYLMinorLineColor": "black"
        , "tmYLMinorLengthF": 0.006

        # 其他
        , "tmEqualizeXYSizes": True  # xy坐标轴等间隔值
        # , "tmXTIrregularPoints": [30.0]  # xy坐标轴等间隔值
        # , "tmXUseBottom": False  # xy坐标轴等间隔值
        # , "tmXMajorGrid": True  # 坐标轴刻度延生 从底到顶连成一根线

        , "nglMaximize": False  # 不占用整个画布大小

    },

    # 数据源和单位
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
    # 绘制图例
    "label_bar_global": {
        "lbBoxLinesOn": True,
        "lbBoxLineThicknessF ": 4.0,
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
            "amOrthogonalPosF": 0.69
        }
    },
    "title_elements": {
        "font_file_path": PathConfig.CPCS_ROOT_PATH + "com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC"
        # 微软雅黑
        , "font_main_size": 60  # 主标题20px
        , "font_sub_size": 45  # 副标题15px
        , "top_padding": 60  # 上边距40px
        , "title_padding": 10  # 标题间隔5px
    },
}
