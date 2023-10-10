import numpy as np
from scipy.interpolate import Rbf, griddata
import xarray as xr
import logging
from metpy.interpolate import remove_nan_observations, interpolate_to_grid

"""
站点插值到格点
metpy cressman:
@see https://unidata.github.io/MetPy/latest/examples/gridding/Point_Interpolation.html?highlight=cressman
IDW:
@see com.nriet.utils.IDW.interpolation()
"""

"""
    inputData：站点数据
    atationLat：站点纬度
    stationLon：站点经度
    gridLat：需要插值到的纬度起止点及格点分辨率
    gridLon：需要插值到的经度起止点及格点分辨率
"""


def interp_ref(inputData, stationLat, stationLon, gridLat, gridLon):
    lats = gridLat
    lons = gridLon
    zlat = stationLat
    zlon = stationLon
    glon = np.arange(lons[0], lons[1], lons[2])
    glat = np.arange(lats[0], lats[1], lats[2])
    olon, olat = np.meshgrid(glon, glat)
    boundary_coords = {"west": lons[0], "south": lats[0], "east": lons[1], "north": lats[1]}
    # ols = np.asarray([olon.flatten(), olat.flatten()]).swapaxes(1, 0)
    dims = inputData.dims
    if len(dims) == 1:
        zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, inputData)
        rf = Rbf(zlon1, zlat1, tmpdata.values, kind="thin_plate", smooth=0.2)
        grid1 = rf(olon, olat)
        grid1 = grid1.reshape((lats[2], lons[2]))
        interp_grid_data = xr.DataArray(grid1, coords=[glat, glon], dims=['lat', 'lon'])
    else:
        times = inputData["time"]
        expand_dim_name = "time"
        interp_data = []
        for tt in times:
            tmpdata = inputData.sel(time=tt)
            if len(tmpdata) == 0:
                interpData = np.full([glat.shape[0], glon.shape[0]], np.nan)
            else:
                zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, tmpdata)
                rf = Rbf(zlon1, zlat1, tmpdata.values, epsilon=2)
                interpData = rf(olon, olat)
                interpData = interpData.reshape((glat.shape[0], glon.shape[0]))
            interpData = xr.DataArray(interpData, coords=[glat, glon], dims=['lat', 'lon'])
            interpData = interpData.expand_dims(expand_dim_name)
            interpData[expand_dim_name] = [tt.values]
            interp_data.append(interpData)
        interp_grid_data = xr.concat(interp_data, dim=expand_dim_name)
    return interp_grid_data


def interp_nearest(inputData, stationLat, stationLon, gridLat, gridLon):
    lats = gridLat
    lons = gridLon
    zlat = stationLat
    zlon = stationLon
    glon = np.arange(lons[0], lons[1], lons[2])
    glat = np.arange(lats[0], lats[1], lats[2])
    olon, olat = np.meshgrid(glon, glat)
    boundary_coords = {"west": lons[0], "south": lats[0], "east": lons[1], "north": lats[1]}
    # ols = np.asarray([olon.flatten(), olat.flatten()]).swapaxes(1, 0)
    dims = inputData.dims
    if len(dims) == 1:
        zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, inputData)
        grid1 = griddata((zlon1,zlat1), tmpdata.values, (olon, olat),method='nearest')
        grid1 = grid1.reshape((glat.shape[0], glon.shape[0]))
        interp_grid_data = xr.DataArray(grid1, coords=[glat, glon], dims=['lat', 'lon'])
    else:
        times = inputData["time"]
        expand_dim_name = "time"
        interp_data = []
        for tt in times:
            tmpdata = inputData.sel(time=tt)
            if len(tmpdata) == 0:
                interpData = np.full([glat.shape[0], glon.shape[0]], np.nan)
            else:
                zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, tmpdata)
                interpData = griddata((zlon1, zlat1), tmpdata.values, (olon, olat), method='nearest')
                interpData = interpData.reshape((glat.shape[0], glon.shape[0]))
            interpData = xr.DataArray(interpData, coords=[glat, glon], dims=['lat', 'lon'])
            interpData = interpData.expand_dims(expand_dim_name)
            interpData[expand_dim_name] = [tt.values]
            interp_data.append(interpData)
        interp_grid_data = xr.concat(interp_data, dim=expand_dim_name)
    return interp_grid_data


def interp_linear(inputData, stationLat, stationLon, gridLat, gridLon):
    lats = gridLat
    lons = gridLon
    zlat = stationLat
    zlon = stationLon
    glon = np.arange(lons[0], lons[1], lons[2])
    glat = np.arange(lats[0], lats[1], lats[2])
    olon, olat = np.meshgrid(glon, glat)
    boundary_coords = {"west": lons[0], "south": lats[0], "east": lons[1], "north": lats[1]}
    # ols = np.asarray([olon.flatten(), olat.flatten()]).swapaxes(1, 0)
    dims = inputData.dims
    if len(dims) == 1:
        zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, inputData)
        grid1  = griddata((zlon1, zlat1), tmpdata.values, (olon, olat),method='linear')
        grid1  = grid1.reshape((glat.shape[0],glon.shape[0]))
        interp_grid_data = xr.DataArray(grid1, coords=[glat, glon], dims=['lat', 'lon'])
    else:
        times = inputData["time"]
        expand_dim_name = "time"
        interp_data = []
        for tt in times:
            tmpdata = inputData.sel(time=tt)
            if len(tmpdata) == 0:
                interpData = np.full([glat.shape[0], glon.shape[0]], np.nan)
            else:
                zlon1, zlat1, tmpdata = remove_nan_observations(zlon, zlat, tmpdata)
                interpData = griddata((zlon1, zlat1), tmpdata.values, (olon, olat), method='linear')
                interpData = interpData.reshape((glat.shape[0], glon.shape[0]))
            interpData = xr.DataArray(interpData, coords=[glat, glon], dims=['lat', 'lon'])
            interpData = interpData.expand_dims(expand_dim_name)
            interpData[expand_dim_name] = [tt.values]
            interp_data.append(interpData)
        interp_grid_data = xr.concat(interp_data, dim=expand_dim_name)
    return interp_grid_data