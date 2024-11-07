# @desc: fy数据处理
# @author:qiujj
# @time: 2024\\11\\6
import ast
import os
import sys
import time

import fy4Utils
import xarray as xr
import components
from FY4A import FY4A


def writ_nc(res_data, resVar, out_file_path, latlonType=None):
    # 判断输出目录是否存在，不存在就创建
    str_dir = os.path.dirname(out_file_path)
    # logging.info(out_file_path)
    if not os.path.exists(str_dir):
        os.makedirs(str_dir)
    # 判断输出文件是否存在，存在则删除
    if os.path.exists(out_file_path):
        os.remove(out_file_path)
    # 生成netCDF文件
    data_set = xr.Dataset({resVar: res_data})
    # 设置netcdf的数据属性
    encoding = {resVar: {'dtype': 'float32', '_FillValue': 999999.0}}
    if "time" in res_data.dims:
        encoding["time"] = {'dtype': 'float64'}
    if "ens" in res_data.dims:
        encoding["ens"] = {'dtype': 'float64'}
    if latlonType:
        # logging.info(latlonType)
        encoding["lat"] = {'dtype': latlonType}
        encoding["lon"] = {'dtype': latlonType}
    print("%s is ok" % out_file_path)
    data_set.to_netcdf(out_file_path, encoding=encoding)


# FY4B - _AGRI - -_N_DISK_1050E_L2 - _SST - _MULT_NOM_20240327000000_20240327001459_4000M_V0001.NC
def regular_fy4b_sst_day_data(dataConfig):
    dataInputPath = dataConfig.get("dataInputPath")
    dataOutputPath = dataConfig.get("dataOutputPath")
    var = dataConfig.get("var")
    timeIndex = dataConfig.get("timeIndex")
    # 需要插值的经纬度
    new_lon, new_lat = fy4Utils.gen_lat_lon(0, 360, 90, -90, 0.04)
    arg = components.Arg()
    arg_parsed = arg.arg_parse('-d'.split())  # 代码输入参数
    fy4a = FY4A(arg_parsed)
    ds = fy4a.get_data_from_data_name(dataInputPath, var, new_lon, new_lat, '')
    ori_lat, ori_lon, flag, data = (ds['lat'].values, ds['lon'].values
                                    , ds['flag'].values, ds["SST"].values)
    new_data = fy4a.gen_new_data(data, ori_lat, ori_lon, new_lat, new_lon, flag, "nearest",
                                 '')
    tempArray = xr.DataArray(new_data, coords={"lat": new_lat, "lon": new_lon},
                             dims=["lat", "lon"])
    if os.path.isdir(dataOutputPath):
        file_name = os.path.basename(dataInputPath)
        timeStr = file_name.split("-")[timeIndex]
        year = timeStr[0:4]
        ym = timeStr[0:6]
        ymd = timeStr[0:8]
        dataOutputPath = dataOutputPath.replace("#year#", year).replace("#ym#", ym).replace("#ymd#", ymd)
        dataOutputPath = dataOutputPath + "\\" + file_name
    writ_nc(tempArray, var, dataOutputPath)


if __name__ == '__main__':
    start_time = time.time()
    param_str = sys.argv[1]
    #param_str = '{"dataInputPath": "./db/FY4B-_AGRI--_N_DISK_1050E_L2-_SST-_MULT_NOM_20241106033000_20241106034459_4000M_V0001.NC","dataOutputPath": "./db/1.nc", "var": "SST", "timeIndex": -4}'
    print(f"接收到的参数为{param_str}")
    cmd_params = ast.literal_eval(param_str)
    regular_fy4b_sst_day_data(cmd_params)
    end_time = time.time()
    cost = end_time - start_time
    print("FY4B SST数据规整消耗时间：%s" % cost)
