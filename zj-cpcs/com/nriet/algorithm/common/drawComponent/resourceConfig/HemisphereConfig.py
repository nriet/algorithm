from com.nriet.config import PathConfig
hemisphere_params_dict = {
    'map': {
        'pmTickMarkDisplayMode': "Never"  # 不显示坐标轴
        , 'mpCenterLatF': 90.
        , 'mpCenterLonF': 90.
        , 'mpEllipticalBoundary': True  # 控制图形呈圆形
        , 'mpFillOn': True
        , 'mpFillColors': ("background", "transparent", "transparent", "transparent")
        , 'mpGeophysicalLineColor': 'black'
        , 'mpGeophysicalLineDashPattern': 0
        , 'mpPerimOn': False
        , 'mpGeophysicalLineThicknessF': 4
        , 'mpGridLineDashPattern': 2
        , 'mpLimitMode': "LatLon"  # 控制球形显示的，不能动
        , 'mpMaxLatF': 90.
        , 'mpMaxLonF': 357.5
        , 'mpMinLatF': -0.1
        , 'mpMinLonF': 0
        , 'mpNationalLineColor': 'black'  # 添加国界线颜色
        , 'mpNationalLineThicknessF': 3  # 添加国界线粗细
        , 'mpOutlineBoundarySets': 'Geophysical'  # 添加海陆分界线，若显示国界线，则设置为National，默认值Geophysical
        , 'mpOutlineOn': True  # 陆地边界线开关
        , 'mpProjection': "Stereographic"  # 控制投影为球形
        , 'mpUSStateLineColor': 'transparent'

        , 'mpGridLatSpacingF': 10.

        , 'nglDraw': False
        , 'nglFrame': False
        , 'nglMaximize': False  # 必须添加！！ 不然vP相关的动不了

        , 'vpXF': 0.12  # 到左边缘距离
        , 'vpYF': 0.875  # 到顶边缘距离
        , 'vpWidthF': 0.76  # 矩形边框宽度
        , 'vpHeightF': 0.76  # 矩形边框高度

    },
    'contourMap': {

        'cnConstFLabelOn': False
        , 'cnFillOn': True  # 填充总开关
        , 'cnLinesOn': False
        , 'cnInfoLabelOn': False  # 不显示等值线
        , 'cnLevelSelectionMode': 'ExplicitLevels'  # 使用自己给定的色阶和等值线属性来绘图
        , 'cnLineColor': 'black'  # 等值线颜色
        , 'cnLineLabelsOn': False  # 不显示等值线的值
        , 'cnLineLabelInterval': 1
        , 'cnNoDataLabelOn': False
        # , 'cnFillMode':  "RasterFill"
        , 'lbLabelBarOn': False  # 显示色标
        , 'lbLabelFontHeightF': 0.009  # 色标字体--15号大小
        , 'lbLabelPosition': "Bottom"  # 色标置于底部
        , 'lbOrientation': "Horizontal"  # 水平显示

        , 'mpCenterLatF': 90.
        , 'mpCenterLonF': 90.
        , 'mpEllipticalBoundary': True  # 控制图形呈圆形
        , 'mpFillOn': True
        , 'mpFillColors': ("background", "transparent", "transparent", "transparent")
        , 'mpGeophysicalLineColor': 'black'  # 添加海陆分界线颜色
        , 'mpGeophysicalLineDashPattern': 0
        , 'mpGeophysicalLineThicknessF': 4  # 添加海陆分界线颜色
        , 'mpGridLineDashPattern': 2
        , 'mpLimitMode': "LatLon"  # 控制球形显示的，不能动
        , 'mpMaxLatF': 90.
        , 'mpMaxLonF': 357.5
        , 'mpMinLatF': -0.1
        , 'mpMinLonF': 0
        , 'mpNationalLineColor': 'black'  # 添加国界线颜色
        , 'mpNationalLineThicknessF': 4  # 添加国界线粗细
        , 'mpOutlineBoundarySets': 'Geophysical'  # 添加海陆分界线
        , 'mpOutlineOn': True  # 陆地边界线开关
        , 'mpProjection': "Stereographic"  # 控制投影为球形
        , 'mpUSStateLineColor': 'transparent'
        
        , 'mpGridLatSpacingF': 10.

        , 'nglDraw': False
        , 'nglFrame': False
        , 'nglMaximize': False  # 必须添加！！ 不然vP相关的动不了

        , 'pmLabelBarWidthF': 0.45  # 色标变窄
        , 'pmLabelBarHeightF': 0.06  # 色标变细
        , 'pmLabelBarOrthogonalPosF': 0.02  # 色标向下
        , 'pmTickMarkDisplayMode': "Never"  # 不显示坐标轴

        , 'vpXF': 0.12  # 到左边缘距离
        , 'vpYF': 0.875  # 到顶边缘距离
        , 'vpWidthF': 0.76  # 矩形边框宽度
        , 'vpHeightF': 0.76  # 矩形边框高度

    },

    'contour': {

        'cnConstFLabelOn': False
        , 'cnFillOn': False  # 等值线之间不填充颜色
        , 'cnInfoLabelOn': False
        , 'cnLinesOn': True  # 等值线数据是否显示
        , 'cnLineThicknessF': 2.5  # 等值线粗细
        , 'cnLineLabelsOn': True  # 是否显示数值
        , 'cnLineLabelInterval': 1  # 每条线上都显示数值
        , 'cnLineLabelDensityF': 0.7  # 数值密度

        , 'cnLineLabelFontHeightF': 0.009  # 数值字体大小
        , 'cnLevelSelectionMode': "ExplicitLevels"
        , 'cnLabelMasking': True  # 等值线不穿过文字
        , 'cnNoDataLabelOn': False
        , 'cnSmoothingOn': True
        , 'cnSmoothingDistanceF': 0.001

        , 'nglDraw': False
        , 'nglFrame': False
        , 'nglMaximize': False  # 必须添加！！ 不然vP相关的动不了

        # 'black': {
        #     'cnConstFLabelOn': False
        #     , 'cnFillOn': False  # 等值线之间不填充颜色
        #     , 'cnInfoLabelOn': False
        #     , 'cnLinesOn': True  # 等值线数据是否显示
        #     , 'cnLineThicknessF': 2.5  # 等值线粗细
        #     , 'cnLineLabelsOn': True  # 是否显示数值
        #     , 'cnLineLabelInterval': 1  # 每条线上都显示数值
        #     , 'cnLineLabelDensityF': 0.7  # 数值密度
        #     , 'cnLineLabelFontColors': ("black", "black")
        #     , 'cnLineLabelFontHeightF': 0.009  # 数值字体大小
        #     , 'cnLevelSelectionMode': "ExplicitLevels"
        #     , 'cnLabelMasking': True  # 等值线不穿过文字
        #     , 'cnNoDataLabelOn': False
        #     , 'cnSmoothingOn': True
        #     , 'cnSmoothingDistanceF': 0.001
        #
        #     , 'nglDraw': False
        #     , 'nglFrame': False
        #     , 'nglMaximize': False  # 必须添加！！ 不然vP相关的动不了
        # },
        # 'red': {
        #     'cnConstFLabelOn': False
        #     , 'cnFillOn': False  # 等值线之间不填充颜色
        #     , 'cnInfoLabelOn': False
        #
        #     , 'cnLineDashPatterns': (0, 0)
        #     , 'cnLinesOn': True  # 等值线数据是否显示
        #     , 'cnLineThicknessF': 4.5  # 等值线粗细
        #     , 'cnLineLabelsOn': True  # 是否显示数值
        #     , 'cnLineLabelBackgroundColor': "white"  # Label的背景色
        #     , 'cnLineLabelInterval': 1  # 每条线上都显示数值
        #     , 'cnLineLabelDensityF': 0.7  # 数值密度
        #     , 'cnLineLabelFontColors': ("red", "red")  # Label数值字体颜色
        #     , 'cnLineLabelFontHeightF': 0.012  # Label数值字体大小
        #     , 'cnLevelSelectionMode': "ExplicitLevels"
        #     , 'cnLabelMasking': True  # 等值线不穿过文字
        #
        #     # , 'cnMonoLineColor': False
        #     # , 'cnMonoLineDashPattern': False
        #     # , 'cnMonoLineLabelFontColor': False
        #
        #     , 'cnNoDataLabelOn': False
        #     , 'cnSmoothingOn': True
        #     , 'cnSmoothingDistanceF': 0.001
        #
        #     , 'nglDraw': False
        #     , 'nglFrame': False
        #     , 'nglMaximize': False  # 必须添加！！ 不然vP相关的动不了
        # },

    },
    'vector': {
        'pmTickMarkDisplayMode': 'Never'  # 不绘制坐标轴

        , 'vcGlyphStyle': "CurlyVector"  # 指定风矢形状
        , 'vcFillArrowHeadXF': 0.3  # 箭头的箭大小vcRefAnnoOrthogonalPosF
        , 'vcFillArrowHeadYF': 0.1  # 箭头的箭大小
        , 'vcFillArrowHeadMinFracXF': 0.5
        , 'vcFillArrowHeadMinFracYF': 0.5
        , 'vcFillArrowHeadInteriorXF': 0.2
        , 'vcFillArrowHeadEdgeThicknessF': 0.4
        , 'vcFillArrowWidthF': 0.03
        , 'vcFillArrowEdgeColor': 'white'
        , 'vcFillArrowFillColor': 'black'
        , "vcLevelSelectionMode": "AutomaticLevels"  # 风矢间隔
        , 'vcLineArrowThicknessF': 3.0  # 调整箭头粗细 :2.3
        , 'vcLineArrowHeadMaxSizeF': 0.006  # 调整箭头大小 :0.005
        , 'vcLineArrowHeadMinSizeF': 0.003
        , 'vcLineArrowColor': "black"  # 风矢图形颜色
        # , "vcMapDirection": True  # 在绘制垂直剖面图时，一定设置为False
        , 'vcMinDistanceF': 0.017  # 相邻风矢的间距
        , 'vcMinMagnitudeF': 0.0  # 最小风速
        , 'vcMonoLineArrowColor': True

        , 'vcRefAnnoArrowSpaceF': 1.0
        , 'vcRefAnnoBackgroundColor': 'white'
        , 'vcRefAnnoFontHeightF': 0.012
        , 'vcRefAnnoOn': True  # 绘制参考箭头，默认值为True
        , 'vcRefAnnoOrthogonalPosF': -0.050  # 垂直位置
        , 'vcRefAnnoParallelPosF': 0.999  # 水平位置
        , 'vcRefAnnoPerimOn': False  # 不绘制参考箭头的边框
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
        , 'stLineStartStride': 5  # 每5个格点才能启动一条流线
        , 'stArrowStride': 5  # 每5个格点绘制一个箭头
        , 'stLineThicknessF': 5.0  # 流线粗细
        , 'stArrowLengthF': 0.003  # 箭头大小
        , 'stStreamlineDrawOrder': "PostDraw"  # 风矢优先绘制

        , 'nglDraw': False
        , 'nglFrame': False
        , "nglMaximize": False
        , 'nglSpreadColors': True
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
    # 主体地理线
    'geo': {
        # coastline
        "coastline": {
            "file_name": "HAX.shp",
            "type": "polyline",
            "gsLineThicknessF": 3.0,
            "gsLineColor": (0.0, 0.0, 153.0 / 255),
            "gsLineDashPattern": 0
        },
        # river
        "river": {
            "file_name": "HYDL.shp",
            "type": "polyline",
            "gsLineThicknessF": 4.0,
            "gsLineColor": "blue",
            "gsLineDashPattern": 0
        },
        # Established_boundaries
        "established_boundaries": {
            "file_name": "BOUL_GY.shp",
            "type": "polyline",
            "gsLineThicknessF": 3.0,
            "gsLineColor": "black",
            "gsLineDashPattern": 0
        },
        # Unestablished boundaries
        "unestablished_boundaries": {
            "file_name": "BOUL_GW.shp",
            "type": "polyline",
            "gsLineThicknessF": 3.0,
            "gsLineColor": "black",
            "gsLineDashPattern": 1
        },
    },
    # 绘制图例
    "label_bar_global": {
        "lbAutoManage": False,
        "lbPerimOn": False,
        "lbLabelAlignment": "InteriorEdges",
        "lbOrientation":"Horizontal",
        "lbMonoFillPattern": True,
        "lbLabelFontColor": "black",
        "lbLabelFontHeightF": "0.012",
        "vpWidthF": 0.785,
        "vpHeightF": 0.06,
        # 图例位置
        "labelbar_location": {
            "amParallelPosF": 0,
            "amOrthogonalPosF": 0.58
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
