#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time : 2020/02/17
# @Author : Eldan
# @File : StationToNc.py
import numpy as np
from scipy.interpolate import Rbf, griddata
import xarray as xr
import logging
from metpy.interpolate import remove_nan_observations,interpolate_to_grid
from com.nriet.algorithm.business.BusComponent import BusComponent
from com.nriet.utils.decorator.TimerDecorator import timer_with_param

from com.nriet.utils.exception.workFlow.AlgorithmException import AlgorithmException
"""
站点插值到格点
metpy cressman:
@see https://unidata.github.io/MetPy/latest/examples/gridding/Point_Interpolation.html?highlight=cressman
IDW:
@see com.nriet.utils.IDW.interpolation()
"""


class StationToNc(BusComponent):
    def __init__(self, sub_local_params, algorithm_input_data):
        """
                :param sub_local_params:流程参数，算法运算返回结果
                :param algorithm_input_data:流程数据
                """
        if isinstance(algorithm_input_data[0], list):
            algorithm_input_data = algorithm_input_data[0]
        # 插值方法
        self.interpolationMethod = sub_local_params["interpolationMethod"]
        # 需要插值到的纬度起止点及个数
        self.lats = sub_local_params["lats"]
        # 需要插值到的经度起止点及个数
        self.lons = sub_local_params.get("lons")
        # 站点数据
        if isinstance(algorithm_input_data[0]["outputData"], list):
            self.inputData = algorithm_input_data[0]["outputData"][0]
        else:
            self.inputData = algorithm_input_data[0]["outputData"]
        # 站点信息
        self.inputData2 = algorithm_input_data[1]["outputData"]
        self.output_data = None

    @timer_with_param('StationToNc')
    def execute(self):
        out_data = {}
        if np.isnan(np.nanmean(self.inputData.values)):
            raise AlgorithmException(response_code='9801', response_msg='All Missing Values')
        if self.interpolationMethod == 'idw':
            out_data["outputData"] = self.interp_idw()
        elif self.interpolationMethod == 'cressman':
            out_data["outputData"] = self.interp_cressman()
        elif self.interpolationMethod == 'nearest':
            out_data["outputData"] = self.interp_nearest()
        elif self.interpolationMethod == 'linear':
            out_data["outputData"] = self.interp_linear()
        elif self.interpolationMethod == 'cubic':
            out_data["outputData"] = self.interp_cubic()
        elif self.interpolationMethod == 'ref':
            out_data["outputData"] = self.interp_ref()
        self.output_data = out_data

    def interp_cressman(self):
        inputData = self.inputData
        inputData2 = self.inputData2
        lats = self.lats
        lons = self.lons
        zlat = inputData2.sel(space="lat").values
        zlon = inputData2.sel(space="lon").values
        glon = np.linspace(lons[0], lons[1], lons[2])
        glat = np.linspace(lats[0], lats[1], lats[2])
        olon, olat = np.meshgrid(glon, glat)
        boundary_coords = {"west": lons[0], "south": lats[0], "east": lons[1], "north": lats[1]}
        # ols = np.asarray([olon.flatten(), olat.flatten()]).swapaxes(1, 0)
        dims = self.inputData.dims
        if len(dims) == 1:
            zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, inputData)
            if lons[0] >=0:
                zlon1 = np.where(zlon1 < 0, zlon1+360, zlon1)
            gx, gy, grid1 = interpolate_to_grid(zlon1, zlat1, tmpdata.values, interp_type='cressman', minimum_neighbors=2, hres=2,
                                              search_radius=7,boundary_coords = boundary_coords)
            glat = gy[:, 0]
            glon = gx[0]
            # grid1 = inverse_distance_to_grid(zlon1, zlat1, tmpdata, olon, olat, 2.5)
            # logging.info(grid1.shape)
            interp_grid_data = xr.DataArray(grid1, coords=[glat, glon], dims=['lat', 'lon'])
        else:
            times = inputData["time"]
            expand_dim_name = "time"
            interp_data = []
            for tt in times:
                tmpdata = inputData.sel(time=tt)
                zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, tmpdata)
                zlon1 = np.where(zlon1 < 0, zlon1 + 360, zlon1)
                gx, gy, interpData = interpolate_to_grid(zlon1, zlat1, tmpdata.values, interp_type='cressman', minimum_neighbors=2,
                                                    hres=1,
                                                    search_radius=7, boundary_coords=boundary_coords)
                glat = gy[:, 0]
                glon = gx[0]
                interpData = xr.DataArray(interpData, coords=[glat, glon], dims=['lat', 'lon'])
                interpData = interpData.expand_dims(expand_dim_name)
                interpData[expand_dim_name] = [tt.values]
                interp_data.append(interpData)
            interp_grid_data = xr.concat(interp_data, dim=expand_dim_name)
        return interp_grid_data      
        
    def interp_nearest(self):
        inputData = self.inputData
        inputData2 = self.inputData2
        lats = self.lats
        lons = self.lons
        zlat = inputData2.sel(space="lat").values
        zlon = inputData2.sel(space="lon").values
        glon = np.linspace(lons[0], lons[1], lons[2])
        glat = np.linspace(lats[0], lats[1], lats[2])
        olon, olat = np.meshgrid(glon, glat)
        boundary_coords = {"west": lons[0], "south": lats[0], "east": lons[1], "north": lats[1]}
        # ols = np.asarray([olon.flatten(), olat.flatten()]).swapaxes(1, 0)
        dims = self.inputData.dims
        if len(dims) == 1:
            zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, inputData)
            grid1  = griddata((zlon1,zlat1), tmpdata.values, (olon, olat),method='nearest')
            grid1  = grid1.reshape((lats[2],lons[2]))
            interp_grid_data = xr.DataArray(grid1, coords=[glat, glon], dims=['lat', 'lon'])
        else:
            times = inputData["time"]
            expand_dim_name = "time"
            interp_data = []
            for tt in times:
                tmpdata = inputData.sel(time=tt)
                if (len(tmpdata) == 0):
                    interpData = np.full([lats[2], lons[2]], np.nan)
                else:
                    zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, tmpdata)
                    interpData = griddata((zlon1,zlat1), tmpdata.values, (olon, olat),method='nearest')
                    interpData = interpData.reshape((lats[2], lons[2]))
                interpData = xr.DataArray(interpData, coords=[glat, glon], dims=['lat', 'lon'])
                interpData = interpData.expand_dims(expand_dim_name)
                interpData[expand_dim_name] = [tt.values]
                interp_data.append(interpData)
            interp_grid_data = xr.concat(interp_data, dim=expand_dim_name)
        return interp_grid_data
                
    def interp_ref(self):
        inputData = self.inputData
        inputData2 = self.inputData2
        lats = self.lats
        lons = self.lons
        zlat = inputData2.sel(space="lat").values
        zlon = inputData2.sel(space="lon").values
        glon = np.linspace(lons[0], lons[1], lons[2])
        glat = np.linspace(lats[0], lats[1], lats[2])
        olon, olat = np.meshgrid(glon, glat)
        boundary_coords = {"west": lons[0], "south": lats[0], "east": lons[1], "north": lats[1]}
        # ols = np.asarray([olon.flatten(), olat.flatten()]).swapaxes(1, 0)
        dims = self.inputData.dims
        if len(dims) == 1:
            zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, inputData)
            rf = Rbf(zlon1, zlat1, tmpdata.values,kind = "thin_plate",smooth=0.2)
            grid1 = rf(olon, olat)
            grid1  = grid1.reshape((lats[2],lons[2]))
            interp_grid_data = xr.DataArray(grid1, coords=[glat, glon], dims=['lat', 'lon'])
        else:
            times = inputData["time"]
            expand_dim_name = "time"
            interp_data = []
            for tt in times:
                tmpdata = inputData.sel(time=tt)
                if (len(tmpdata) == 0):
                    interpData = np.full([lats[2], lons[2]], np.nan)
                else:
                    zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, tmpdata)
                    rf = Rbf(zlon1, zlat1, tmpdata.values ,epsilon = 2)
                    interpData = rf(olon, olat)
                    interpData = interpData.reshape((lats[2], lons[2]))
                interpData = xr.DataArray(interpData, coords=[glat, glon], dims=['lat', 'lon'])
                interpData = interpData.expand_dims(expand_dim_name)
                interpData[expand_dim_name] = [tt.values]
                interp_data.append(interpData)
            interp_grid_data = xr.concat(interp_data, dim=expand_dim_name)
        return interp_grid_data
        
    def interp_linear(self):
        inputData = self.inputData
        inputData2 = self.inputData2
        lats = self.lats
        lons = self.lons
        zlat = inputData2.sel(space="lat").values
        zlon = inputData2.sel(space="lon").values
        glon = np.linspace(lons[0], lons[1], lons[2])
        glat = np.linspace(lats[0], lats[1], lats[2])
        olon, olat = np.meshgrid(glon, glat)
        boundary_coords = {"west": lons[0], "south": lats[0], "east": lons[1], "north": lats[1]}
        # ols = np.asarray([olon.flatten(), olat.flatten()]).swapaxes(1, 0)
        dims = self.inputData.dims
        if len(dims) == 1:
            zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, inputData)
            grid1  = griddata((zlon1,zlat1), tmpdata.values, (olon, olat),method='linear')
            grid1  = grid1.reshape((lats[2],lons[2]))
            interp_grid_data = xr.DataArray(grid1, coords=[glat, glon], dims=['lat', 'lon'])
        else:
            times = inputData["time"]
            expand_dim_name = "time"
            interp_data = []
            for tt in times:
                tmpdata = inputData.sel(time=tt)
                if (len(tmpdata) == 0):
                    interpData = np.full([lats[2], lons[2]], np.nan)
                else:
                    zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, tmpdata)
                    interpData = griddata((zlon1,zlat1), tmpdata.values, (olon, olat),method='linear')
                    interpData = interpData.reshape((lats[2], lons[2]))
                interpData = xr.DataArray(interpData, coords=[glat, glon], dims=['lat', 'lon'])
                interpData = interpData.expand_dims(expand_dim_name)
                interpData[expand_dim_name] = [tt.values]
                interp_data.append(interpData)
            interp_grid_data = xr.concat(interp_data, dim=expand_dim_name)
        return interp_grid_data
        
    def interp_cubic(self):
        inputData = self.inputData
        inputData2 = self.inputData2
        lats = self.lats
        lons = self.lons
        zlat = inputData2.sel(space="lat").values
        zlon = inputData2.sel(space="lon").values
        glon = np.linspace(lons[0], lons[1], lons[2])
        glat = np.linspace(lats[0], lats[1], lats[2])
        olon, olat = np.meshgrid(glon, glat)
        boundary_coords = {"west": lons[0], "south": lats[0], "east": lons[1], "north": lats[1]}
        # ols = np.asarray([olon.flatten(), olat.flatten()]).swapaxes(1, 0)
        dims = self.inputData.dims
        if len(dims) == 1:
            zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, inputData)
            grid1  = griddata((zlon1,zlat1), tmpdata.values, (olon, olat),method='cubic')
            grid1  = grid1.reshape((lats[2],lons[2]))
            interp_grid_data = xr.DataArray(grid1, coords=[glat, glon], dims=['lat', 'lon'])
        else:
            times = inputData["time"]
            expand_dim_name = "time"
            interp_data = []
            for tt in times:
                tmpdata = inputData.sel(time=tt)
                if (len(tmpdata) == 0):
                    interpData = np.full([lats[2], lons[2]], np.nan)
                else:
                    zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, tmpdata)
                    interpData = griddata((zlon1,zlat1), tmpdata.values, (olon, olat),method='cubic')
                    interpData = interpData.reshape((lats[2], lons[2]))
                interpData = xr.DataArray(interpData, coords=[glat, glon], dims=['lat', 'lon'])
                interpData = interpData.expand_dims(expand_dim_name)
                interpData[expand_dim_name] = [tt.values]
                interp_data.append(interpData)
            interp_grid_data = xr.concat(interp_data, dim=expand_dim_name)
        return interp_grid_data

    def interp_idw(self):
        inputData = self.inputData
        inputData2 = self.inputData2
        lats = self.lats
        lons = self.lons
        zlat = inputData2.sel(space="lat")
        zlon = inputData2.sel(space="lon")
        glon = np.linspace(lons[0], lons[1], lons[2])
        glat = np.linspace(lats[0], lats[1], lats[2])
        olon, olat = np.meshgrid(glon, glat)
        olon, olat = olon.flatten(), olat.flatten()
        # ols = np.asarray([olon.flatten(), olat.flatten()]).swapaxes(1, 0)
        dims = self.inputData.dims
        if len(dims) == 1:
            zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, inputData)
            grid1  = simple_idw(zlon1.values,zlat1.values, tmpdata.values, olon, olat)
            logging.info(grid1.shape)
            grid1  = grid1.reshape((lats[2],lons[2]))
            interp_grid_data = xr.DataArray(grid1, coords=[glat, glon], dims=['lat', 'lon'])
        else:
            times = inputData["time"]
            expand_dim_name = "time"
            interp_data = []
            for tt in times:
                tmpdata = inputData.sel(time=tt)
                if (len(tmpdata) == 0):
                    interpData = np.full([lats[2], lons[2]], np.nan)
                else:
                    zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, tmpdata)
                    if len(tmpdata.values) == 0:
                        interpData = np.full([lats[2], lons[2]], np.nan)
                    else:
                        interpData = simple_idw(zlon1.values, zlat1.values, tmpdata.values, olon, olat)
                        interpData = interpData.reshape((lats[2], lons[2]))
                interpData = xr.DataArray(interpData, coords=[glat, glon], dims=['lat', 'lon'])
                interpData = interpData.expand_dims(expand_dim_name)
                interpData[expand_dim_name] = [tt.values]
                interp_data.append(interpData)
            interp_grid_data = xr.concat(interp_data, dim=expand_dim_name)
        return interp_grid_data

def simple_idw(x,y,z,xi,yi):
    dist = distance_matrix(x,y,xi,yi)
    weights = 1.0 / dist**20
    weights /= weights.sum(axis=0)
    zi = np.dot(weights.T, z)
    return zi

def distance_matrix(x0,y0,x1,y1):
    obs = np.vstack((x0,y0)).T
    interp = np.vstack((x1,y1)).T
    d0 = np.subtract.outer(obs[:,0],interp[:,0])
    d1 = np.subtract.outer(obs[:,1], interp[:,1])
    return np.hypot(d0,d1)


