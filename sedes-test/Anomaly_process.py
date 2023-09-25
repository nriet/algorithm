import numpy as np
import xarray as xr

def Anomaly_process(yystart, yylast, month):
    model = ['EC']
    filedir = "./ec_data/"

    # 年份
    # yystart = 2023
    # yylast = 2023
    year = np.arange(yystart, yylast + 1, 1)

    # 月份
    # month = ["01","02","03","04","05","06","07","08","09","10","11","12"]
    # month = ['05']
    level = ["sl", "850", "500", "200"]

    for imodel in model:
        for iyear in year:
            for imonth in month:
                for ilevel in level:
                    if ilevel == 'sl':
                        print(imodel + '_' + str(iyear) + imonth + '_' + ilevel + '.nc')
                        data = xr.open_dataset(
                            filedir + imodel + '_' + str(iyear) + imonth + '_' + ilevel + '.nc')
                        latitude = data['latitude']
                        longitude = data['longitude']
                        time = data['time']
                        number = data['number']
                        msdsrf = data['msdsrf']
                        msl = data['msl']
                        si10 = data['si10']
                        t2m = data['t2m']
                        tprate = data['tprate']

                        data_c = xr.open_dataset(
                            filedir + imodel + '_' + imonth + '_' + ilevel + '_climate.nc'). \
                            interp(latitude=latitude, longitude=longitude, method="linear",
                                   kwargs={"fill_value": "extrapolate"})
                        msdsrf_c = data_c['msdsrf']
                        msl_c = data_c['msl']
                        si10_c = data_c['si10']
                        t2m_c = data_c['t2m']
                        tprate_c = data_c['tprate']
                        for inum in np.arange(number.shape[0]):
                            msdsrf[:, inum, :, :] = msdsrf[:, inum, :, :].values - msdsrf_c[:, :, :].values
                            msl[:, inum, :, :] = msl[:, inum, :, :].values - msl_c[:, :, :].values
                            si10[:, inum, :, :] = si10[:, inum, :, :].values - si10_c[:, :, :].values
                            t2m[:, inum, :, :] = t2m[:, inum, :, :].values - t2m_c[:, :, :].values
                            tprate[:, inum, :, :] = (tprate[:, inum, :, :].values - tprate_c[:, :,
                                                                                    :].values) / tprate_c[:,
                                                                                                 :,
                                                                                                 :].values * 100.
                        tprate = np.where(tprate < -100., -100., tprate)

                        f_out = xr.Dataset({'msdsrf': (('time', 'number', 'latitude', 'longitude'), np.asarray(msdsrf)),
                                            'msl': (('time', 'number', 'latitude', 'longitude'), np.asarray(msl)),
                                            'si10': (('time', 'number', 'latitude', 'longitude'), np.asarray(si10)),
                                            't2m': (('time', 'number', 'latitude', 'longitude'), np.asarray(t2m)),
                                            'tprate': (('time', 'number', 'latitude', 'longitude'), tprate)},
                                           coords={'time': ('time', np.asarray(time)),
                                                   'number': ('number', np.asarray(number)),
                                                   'latitude': ('latitude', np.asarray(latitude)),
                                                   'longitude': ('longitude', np.asarray(longitude))})
                        f_out.to_netcdf(filedir + imodel + '_' + str(
                            iyear) + imonth + '_' + ilevel + '_anom.nc')
                    else:
                        print(imodel + '_' + str(iyear) + imonth + '_' + ilevel + '.nc')
                        data = xr.open_dataset(
                            filedir + imodel + '_' + str(iyear) + imonth + '_' + ilevel + '.nc')
                        latitude = data['latitude']
                        longitude = data['longitude']
                        time = data['time']
                        number = data['number']
                        t = data['t']
                        u = data['u']
                        v = data['v']
                        z = data['z']
                        q = data['q']
                        data_c = xr.open_dataset(
                            filedir + imodel + '_' + imonth + '_' + ilevel + '_climate.nc'). \
                            interp(latitude=latitude, longitude=longitude, method="linear",
                                   kwargs={"fill_value": "extrapolate"})
                        t_c = data_c['t']
                        u_c = data_c['u']
                        v_c = data_c['v']
                        z_c = data_c['z']
                        q_c = data_c['q']
                        for inum in np.arange(number.shape[0]):
                            t[:, inum, :, :] = t[:, inum, :, :].values - t_c[:, :, :].values
                            u[:, inum, :, :] = u[:, inum, :, :].values - u_c[:, :, :].values
                            v[:, inum, :, :] = v[:, inum, :, :].values - v_c[:, :, :].values
                            z[:, inum, :, :] = z[:, inum, :, :].values - z_c[:, :, :].values
                            q[:, inum, :, :] = q[:, inum, :, :].values - q_c[:, :, :].values
                        f_out = xr.Dataset({'t': (('time', 'number', 'latitude', 'longitude'), np.asarray(t)),
                                            'u': (('time', 'number', 'latitude', 'longitude'), np.asarray(u)),
                                            'v': (('time', 'number', 'latitude', 'longitude'), np.asarray(v)),
                                            'z': (('time', 'number', 'latitude', 'longitude'), np.asarray(z)),
                                            'q': (('time', 'number', 'latitude', 'longitude'), np.asarray(q))},
                                           coords={'time': ('time', np.asarray(time)),
                                                   'number': ('number', np.asarray(number)),
                                                   'latitude': ('latitude', np.asarray(latitude)),
                                                   'longitude': ('longitude', np.asarray(longitude))})
                        f_out.to_netcdf(filedir + imodel + '_' + str(
                            iyear) + imonth + '_' + ilevel + '_anom.nc')
