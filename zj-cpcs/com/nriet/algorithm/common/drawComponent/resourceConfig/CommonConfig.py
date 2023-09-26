from com.nriet.config import PathConfig
common_params_dict = {

    'logo_elements': {
        'NCC': {
            'file_path':PathConfig.CPCS_ROOT_PATH+ 'com/nriet/algorithm/common/drawComponent/logoFiles/NCC-BIG.png',
            'logo_location': (80, 90),
        },

        'BCC': {
            'file_path':PathConfig.CPCS_ROOT_PATH+ 'com/nriet/algorithm/common/drawComponent/logoFiles/BCC-BIG.png',
            'logo_location': (80 + 220 + 10, 90),
        },
    },
    # 'big_logo_elements': {
    #     'NCC': {
    #         'file_path':PathConfig.CPCS_ROOT_PATH+ 'com/nriet/algorithm/common/drawComponent/logoFiles/NCC-BIG.png',
    #         'logo_location': (80, 60),
    #     },
    #
    #     'BCC': {
    #         'file_path':PathConfig.CPCS_ROOT_PATH+ 'com/nriet/algorithm/common/drawComponent/logoFiles/BCC-BIG.png',
    #         'logo_location': (80 + 220 + 10, 60),
    #     },
    # },

    "title_elements": {
        "font_file_path": PathConfig.CPCS_ROOT_PATH+"com/nriet/algorithm/common/drawComponent/fontFiles/MSYH.TTC"
        # 微软雅黑
        , "font_main_size": 60  # 主标题20px
        , "font_sub_size": 45  # 副标题15px
        , "top_padding": 100  # 上边距40px
        , "title_padding": 20  # 标题间隔5px
    },

    # 全球图例
    "label_bar": {
        "lbAutoManage": False,
        "lbOrientation":"Horizontal",
        "lbLabelAlignment": "ExternalEdges",
        "lbPerimOn": False,
        "lbPerimColor": "black",
        "lbPerimThicknessF": 2,
        "lbLabelFontHeightF" : 0.005 ,           # label font height
        "nglDraw"            :False,
        "lbMonoFillPattern": True,
        "lbLabelFontColor": "black",
        "vpWidthF": 0.685,
        "vpHeightF": 0.11,
        # "pmLabelBarWidthF": 0.485,
        # 图例位置
        "labelbar_location": {
            "amParallelPosF": 0,
            "amOrthogonalPosF": 0.65
        },
    },
    "label_bar_marker": {
        "lbAutoManage": False,
        "lbOrientation":"Horizontal",
        "lbLabelAlignment": "BoxCenters",
        "lbPerimOn": False,
        "lbPerimColor": "black",
        "lbPerimThicknessF": 2,
        "lbLabelFontHeightF" : 0.005 ,           # label font height
        "nglDraw"            :False,
        "lbMonoFillPattern": True,
        "lbLabelFontColor": "black",
        "vpWidthF": 0.685,
        "vpHeightF": 0.11,
        # "pmLabelBarWidthF": 0.485,
        # 图例位置
        "labelbar_location": {
            "amParallelPosF": 0,
            "amOrthogonalPosF": 0.65
        },
    }
}
