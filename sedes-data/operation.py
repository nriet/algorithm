import sys
import matplotlib as mpl
from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os
import joblib
import numpy as np
import torch
from torch.utils.data import DataLoader
import pytorch_lightning as pl
from pytorch_lightning.loggers import TensorBoardLogger
from pytorch_lightning.callbacks import ModelCheckpoint, EarlyStopping
from model.PrecModel import PrecModel
import xarray as xr
import argparse
import pandas as pd
import shutil
from StationToNc import interp_nearest

def acc(forecast, obs):
    acc = np.sum(forecast * obs)
    acc /= np.sqrt(np.sum((forecast ** 2))) * np.sqrt(np.sum((obs ** 2)))
    return acc

# 清空文件夹文件
def clear_folder_shutil(path):
    shutil.rmtree(path)
    os.mkdir(path)

def operation(process_time, process_time_start, process_time_end):
    '''
    model data reprocess
    '''
    print("model data reprocess")
    # process_time = '202305'
    time = pd.date_range(process_time_start, process_time_end, freq='MS')
    time = time.strftime('%Y%m').tolist()
    print(time)
    # ec和ec_climate数据路径（修改）
    data_path = './ec_data/'
    feature_list = ['u_200', 'v_200', 'z_200', 'q_200', \
                    'u_500', 'v_500', 'z_500', 'q_500', \
                    'u_850', 'v_850', 'z_850', 'q_850', 'msl']
    model_list = ['EC_51']
    lt_list = ['0', '1', '2', '3', '4', '5']
    level = ['200', '500', '850', 'sl']
    latitude = np.arange(-89.5, 90.5, 1)
    longitude = np.arange(0.5, 360.5, 1)

    for ilevel in level:
        if ilevel == 'sl':
            data = xr.open_dataset(data_path + 'EC_' + process_time + '_' + ilevel + '_anom.nc'). \
                interp(latitude=latitude, longitude=longitude, method="linear", kwargs={"fill_value": "extrapolate"})
            data_std = xr.open_dataset('./data/EC_' + ilevel + '_stdev.nc')
            msdsrf = np.asarray(data['msdsrf'][:, :, :, :] / data_std['msdsrf']).mean(1)
            msl = np.asarray(data['msl'][:, :, :, :] / data_std['msl']).mean(1)
            si10 = np.asarray(data['si10'][:, :, :, :] / data_std['si10']).mean(1)
            t2m = np.asarray(data['t2m'][:, :, :, :] / data_std['t2m']).mean(1)
            tprate = np.asarray(data['tprate'][:, :, :, :] / data_std['tprate']).mean(1)

        elif ilevel == '200':
            data = xr.open_dataset(data_path + 'EC_' + process_time + '_' + ilevel + '_anom.nc'). \
                interp(latitude=latitude, longitude=longitude, method="linear", kwargs={"fill_value": "extrapolate"})
            data_std = xr.open_dataset('./data/EC_' + ilevel + '_stdev.nc')
            q_200 = np.asarray(data['q'][:, :, :, :] / data_std['q']).mean(1)
            u_200 = np.asarray(data['u'][:, :, :, :] / data_std['u']).mean(1)
            v_200 = np.asarray(data['v'][:, :, :, :] / data_std['v']).mean(1)
            z_200 = np.asarray(data['z'][:, :, :, :] / data_std['z']).mean(1)
        elif ilevel == '500':
            data = xr.open_dataset(data_path + 'EC_' + process_time + '_' + ilevel + '_anom.nc'). \
                interp(latitude=latitude, longitude=longitude, method="linear", kwargs={"fill_value": "extrapolate"})
            data_std = xr.open_dataset('./data/EC_' + ilevel + '_stdev.nc')
            q_500 = np.asarray(data['q'][:, :, :, :] / data_std['q']).mean(1)
            u_500 = np.asarray(data['u'][:, :, :, :] / data_std['u']).mean(1)
            v_500 = np.asarray(data['v'][:, :, :, :] / data_std['v']).mean(1)
            z_500 = np.asarray(data['z'][:, :, :, :] / data_std['z']).mean(1)
        elif ilevel == '850':
            data = xr.open_dataset(data_path + 'EC_' + process_time + '_' + ilevel + '_anom.nc'). \
                interp(latitude=latitude, longitude=longitude, method="linear", kwargs={"fill_value": "extrapolate"})
            data_std = xr.open_dataset('./data/EC_' + ilevel + '_stdev.nc')
            q_850 = np.asarray(data['q'][:, :, :, :] / data_std['q']).mean(1)
            u_850 = np.asarray(data['u'][:, :, :, :] / data_std['u']).mean(1)
            v_850 = np.asarray(data['v'][:, :, :, :] / data_std['v']).mean(1)
            z_850 = np.asarray(data['z'][:, :, :, :] / data_std['z']).mean(1)

    print("model data output")
    f_out = xr.Dataset({'msdsrf': (('lt', 'latitude', 'longitude'), msdsrf),
                        'msl': (('lt', 'latitude', 'longitude'), msl),
                        'si10': (('lt', 'latitude', 'longitude'), si10),
                        't2m': (('lt', 'latitude', 'longitude'), t2m),
                        'tprate': (('lt', 'latitude', 'longitude'), tprate),
                        'q_200': (('lt', 'latitude', 'longitude'), q_200),
                        'u_200': (('lt', 'latitude', 'longitude'), u_200),
                        'v_200': (('lt', 'latitude', 'longitude'), v_200),
                        'z_200': (('lt', 'latitude', 'longitude'), z_200),
                        'q_500': (('lt', 'latitude', 'longitude'), q_500),
                        'u_500': (('lt', 'latitude', 'longitude'), u_500),
                        'v_500': (('lt', 'latitude', 'longitude'), v_500),
                        'z_500': (('lt', 'latitude', 'longitude'), z_500),
                        'q_850': (('lt', 'latitude', 'longitude'), q_850),
                        'u_850': (('lt', 'latitude', 'longitude'), u_850),
                        'v_850': (('lt', 'latitude', 'longitude'), v_850),
                        'z_850': (('lt', 'latitude', 'longitude'), z_850),
                        },
                       coords={'latitude': ('latitude', latitude),
                               'longitude': ('longitude', longitude)})
    filedir = "./model_data/"
    if not os.path.exists(filedir):
        os.makedirs(filedir)
    f_out.to_netcdf('./model_data/' + process_time + '.nc')

    '''
    data in to AI model 
    '''
    print('data in to AI model')
    input_shape = [13, 80, 120]

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--epochs', type=int, default=300,
        help='max training epochs')

    parser = PrecModel.add_model_args(parser)
    args = parser.parse_args()

    data_fraction = xr.open_dataset('./data/1991-2020_EOF.nc')
    fraction = np.asarray(data_fraction['eof_temp'].pcvar).astype(np.float32)
    fraction = torch.as_tensor(fraction)
    args.fraction = fraction
    eof = np.asarray(data_fraction['eof_temp'].values).astype(np.float32)
    eof = torch.as_tensor(eof)
    args.eof = eof
    args.num_outputs = 50
    args.input_channels = len(feature_list)

    input_shape = torch.as_tensor(input_shape)
    args.input_shape = input_shape

    model_temp = PrecModel(args)
    model_temp = model_temp.load_from_checkpoint(checkpoint_path='./model/temp_trans.ckpt', map_location='cpu')
    model_temp.eval()

    model_precip = PrecModel(args)
    model_precip = model_precip.load_from_checkpoint(checkpoint_path='./model/precip_trans.ckpt', map_location='cpu')
    model_precip.eval()

    data = xr.open_dataset('./model_data/' + process_time + '.nc')

    pc_t2m, pc_precip = [], []
    sample = []
    for var in feature_list:
        sample.append(data[var].values[:, 90:170:1, 60:180:1])

    month = torch.from_numpy(np.array(int(process_time[-2:]) - 1))[np.newaxis, ...]
    sample = np.asarray(sample)
    sample = sample.astype(np.float32)[np.newaxis, ...]
    sample = torch.from_numpy(sample)

    with torch.no_grad():
        for ilt in range(sample.shape[2]):
            pc_t2m.append(np.asarray(model_temp(sample[:, :, ilt, :, :], month))[0, :])
            pc_precip.append(np.asarray(model_precip(sample[:, :, ilt, :, :], month))[0, :] * 100.)

    pc_t2m = np.asarray(pc_t2m).reshape(6, 50)
    pc_precip = np.asarray(pc_precip).reshape(6, 50)

    data = xr.open_dataset('./data/1991-2020_EOF.nc')
    eof_t2m = data_fraction['eof_temp'].values
    eof_precip = data_fraction['eof_precip'].values

    t2m, precip = [], []
    for ilt in range(6):
        for ieof in range(50):
            t2m.append(eof_t2m[ieof, :] * pc_t2m[ilt, ieof])
            precip.append(eof_precip[ieof, :] * pc_precip[ilt, ieof])

    t2m = np.asarray(t2m).reshape(6, 50, 66).sum(1)
    precip = np.asarray(precip).reshape(6, 50, 66).sum(1)

    '''
    output results
    '''
    print('output results')
    output_dir = './results/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    station_dir = './data/station.txt'
    station_info = np.loadtxt(station_dir, dtype="str", encoding='UTF-8')
    station_info = np.delete(station_info, [1, 2], 1)
    lon = xr.DataArray(station_info[:, 1], dims='station').astype(np.float32)
    lat = xr.DataArray(station_info[:, 2], dims='station').astype(np.float32)

    station_t2m = xr.Dataset({'t2m': (('time', 'station'), t2m[1:, :])},
                             coords={'time': ('time', time[1:]),
                                     'station': ('station', np.arange(66)),
                                     'lat': lat,
                                     'lon': lon})
    station_prate = xr.Dataset({'prate': (('time', 'station'), precip[1:, :])},
                               coords={'time': ('time', time[1:]),
                                       'station': ('station', np.arange(66)),
                                       'lat': lat,
                                       'lon': lon})
    output_dir_station_t2m = output_dir + "t2m/station/mon/"
    if not os.path.exists(output_dir_station_t2m):
        os.makedirs(output_dir_station_t2m)
    output_dir_station_prate = output_dir + "prate/station/mon/"
    if not os.path.exists(output_dir_station_prate):
        os.makedirs(output_dir_station_prate)
    station_t2m.to_netcdf(output_dir_station_t2m + process_time[0:4] + "_" + process_time[4:6] + '.nc')
    station_prate.to_netcdf(output_dir_station_prate + process_time[0:4] + "_" + process_time[4:6] + '.nc')

    # 将站点数据插值到格点
    output_dir_grid_t2m = output_dir + "t2m/grid/mon/"
    if not os.path.exists(output_dir_grid_t2m):
        os.makedirs(output_dir_grid_t2m)
    output_dir_grid_prate = output_dir + "prate/grid/mon/"
    if not os.path.exists(output_dir_grid_prate):
        os.makedirs(output_dir_grid_prate)
    gridLat = [27, 31.4, 0.01]
    gridLon = [117.8, 123, 0.01]
    interp_grid_data_t2m = interp_nearest(station_t2m["t2m"], lat.values, lon.values, gridLat, gridLon)
    interp_grid_data_prate = interp_nearest(station_prate["prate"], lat.values, lon.values, gridLat, gridLon)
    grid_t2m = xr.Dataset({'t2m': (('time', 'lat', 'lon'), interp_grid_data_t2m.values)},
                          coords={'time': (interp_grid_data_t2m["time"]),
                                  'lat': (interp_grid_data_t2m["lat"]),
                                  'lon': (interp_grid_data_t2m["lon"])})
    grid_prate = xr.Dataset({'prate': (('time', 'lat', 'lon'), interp_grid_data_prate.values)},
                            coords={'time': (interp_grid_data_prate["time"]),
                                    'lat': (interp_grid_data_prate["lat"]),
                                    'lon': (interp_grid_data_prate["lon"])})
    grid_t2m.to_netcdf(output_dir_grid_t2m + process_time[0:4] + "_" + process_time[4:6] + '.nc')
    grid_prate.to_netcdf(output_dir_grid_prate + process_time[0:4] + "_" + process_time[4:6] + '.nc')

    # 删除中间文件
    if os.path.exists("./ec_data"):
        clear_folder_shutil("./ec_data")
    if os.path.exists("./model_data"):
        clear_folder_shutil("./model_data")

