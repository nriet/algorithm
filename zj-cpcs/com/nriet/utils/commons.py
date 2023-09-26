from metpy.interpolate import remove_nan_observations, remove_repeat_coordinates, inverse_distance_to_grid, \
    inverse_distance_to_points
from pandas import np
import logging

def cressman(dataFinal, xg, yg):
    # d0 = 6.
    # scan = [d0, d0 / 2., d0 / 4., d0 / 8., d0 / 16., d0 / 32., d0 / 64., d0 / 128., d0 / 256., d0 / 512.]
    # scan = [d0, d0 / 2., d0 / 4., d0 / 8., d0 / 16.]
    x1, y1 = np.meshgrid(xg, yg)
    # logging.info xg,yg
    # logging.info dataFinal.shape[0]
    # logging.info dataFinal
    x = dataFinal.loc[:, 'lon']  # lon
    y = dataFinal.loc[:, 'lat']  # lat
    z = dataFinal.loc[:, 0]
    x, y, z = remove_nan_observations(x, y, z)
    x, y, z = remove_repeat_coordinates(x, y, z)
    z = inverse_distance_to_grid(x, y, z, x1, y1, 0.7, min_neighbors=1, kind='cressman')
    z = np.ma.masked_where(np.isnan(z), z)
    # gridvar = interp.cressman_multipass(z, x1, y1, x, y, scan)
    # logging.info z

    # exit()
    return z


def cressman_reverse(dataFinal, points_array):
    # d0 = 6.
    # scan = [d0, d0 / 2., d0 / 4., d0 / 8., d0 / 16., d0 / 32., d0 / 64., d0 / 128., d0 / 256., d0 / 512.]
    # scan = [d0, d0 / 2., d0 / 4., d0 / 8., d0 / 16.]
    x1 = points_array.loc[:'lon']
    y1 = points_array.loc[:'lat']
    # logging.info xg,yg
    # logging.info dataFinal.shape[0]
    # logging.info dataFinal
    x = dataFinal.loc[:, 'lon']  # lon
    y = dataFinal.loc[:, 'lat']  # lat
    z = dataFinal.loc[:, 0]
    x, y, z = remove_nan_observations(x, y, z)
    x, y, z = remove_repeat_coordinates(x, y, z)
    z = inverse_distance_to_points([x, y], z, [x1, y1], 0.7, min_neighbors=1, kind='cressman')
    z = np.ma.masked_where(np.isnan(z), z)
    # gridvar = interp.cressman_multipass(z, x1, y1, x, y, scan)
    # logging.info z

    # exit()
    return z
