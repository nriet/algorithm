import xarray as xr
from com.nriet.algorithm.common.drawComponent.drawService.WholeChinaService import WholeChinaService
import pandas as pd
import numpy as np
import logging
#获取任意最后一天的站点数据
marker_nc = xr.open_dataset('/nfsshare/cdbdata/data/STATION/aqi/day/2020.nc')
#logging.info(marker_nc)

#获取站点的经纬度信息
station_info_data = pd.read_csv("/nfsshare/cdbdata/data/STATION/jdqh_station/airQuality/CH_airquality_stations.txt", header=None, encoding='utf-8', sep=" ")
lats = np.array(station_info_data.loc[:,1])
lons = np.array(station_info_data.loc[:,2])


#构造入参


request_dict = {
							"region_type":"wholeChina",
							"output_img_path":"/usr/local/src/huxin/CPCS/com/nriet/algorithm/common/drawComponent/test/wholeChina/",
							"output_img_name":"Poly_Marker_Test",
							"output_img_type":"png",
							"output_img_max_width":"930",
							"main_title":"PM2.5原始场",
                            "sub_titles":["超级","变变变"],
							"layers":[
								{
									"unit":"单位：ug/m³",
									"draw_regions":"60,150,0,60",
									"legend_labels":['<-30','-35~F34~*~F~-24','-24~F34~*~F~-18','-18~F34~*~F~-12','-12~F34~*~F~-8',
                                                     '-8~F34~*~F~-4','-4~F34~*~F~0','0~F34~*~F~4','4~F34~*~F~8',
                                                     '8~F34~*~F~12', '12~F34~*~F~18', '18~F34~*~F~24', '24~F34~*~F~30','>30'],
									"data_source":"CIMISS",
									"layer_type":"polyMarker",
                                    "intervals":[-30.0, -24.0, -18.0, -12.0, -8.0, -4.0, 0.0, 4.0, 8.0, 12.0, 18.0, 24.0, 30.0],
                                    "colors":[[0.027450980392156862, 0.2784313725490196, 0.5411764705882353], [0.12941176470588237, 0.42745098039215684, 0.6823529411764706], [0.27058823529411763, 0.5843137254901961, 0.7843137254901961], [0.37254901960784315, 0.6745098039215687, 0.8196078431372549], [0.4980392156862745, 0.7607843137254902, 0.8588235294117647], [0.6470588235294118, 0.8509803921568627, 0.8980392156862745], [0.7764705882352941, 0.9176470588235294, 0.9568627450980393], [1.0, 0.9921568627450981, 0.7568627450980392], [1.0, 0.9333333333333333, 0.5529411764705883], [0.984313725490196, 0.8588235294117647, 0.3843137254901961], [0.9490196078431372, 0.7725490196078432, 0.2627450980392157], [0.9215686274509803, 0.5882352941176471, 0.14901960784313725], [0.8745098039215686, 0.4235294117647059, 0.058823529411764705], [0.803921568627451, 0.3058823529411765, 0.011764705882352941]],
                                    "marker_size": 0.005,
								}
							]
						}



# request_dict = china_params_dict.get('polyMarker')
# 清楚无用的nan值

input_data =np.array(marker_nc['aqi'][200,:]) #随便取一天的
# logging.info(marker_nc['aqi'][2,:])
# bbb =marker_nc['aqi'][2,:]
# bbb.assign_attrs(lons=lons,lats=lats)
# logging.info(bbb)

data_dict = {
    "data": input_data,
    "lons": lons,
    "lats": lats
}
input_data = pd.DataFrame(data_dict)
input_data = input_data.dropna(axis=0,how='any') #删除表中含有任何NaN的行
data = np.ma.array(input_data.iloc[:,0])
lons = np.ma.array(input_data.iloc[:,1])
lats = np.ma.array(input_data.iloc[:,2])


input_data = [data]

wholeChinaService = WholeChinaService(input_data=input_data,lon=lons,lat=lats,request_dict=request_dict)
wholeChinaService.draw()