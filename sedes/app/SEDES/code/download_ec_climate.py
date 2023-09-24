import cdsapi

def download_ec_climate(year, imonth):
    # imonth = ['05']
    ipre = ["200", "500", "850"]
    # year = '2023'
    c = cdsapi.Client()
    for month in imonth:
        for pre in ipre:
            try:
                c.retrieve(
                    'seasonal-monthly-pressure-levels',
                    {
                        'format': 'netcdf',
                        'originating_centre': 'ecmwf',
                        'system': '51',
                        'variable': [
                            'geopotential', 'temperature', 'u_component_of_wind',
                            'v_component_of_wind', 'specific_humidity'
                        ],
                        'pressure_level': [
                            pre
                        ],
                        'product_type': 'hindcast_climate_mean',
                        'year': year,
                        'month': month,
                        'leadtime_month': [
                            '1', '2', '3',
                            '4', '5', '6',
                        ],
                    },
                    './ec_data/' + 'EC_' + month + '_' + pre + '_climate.nc')
            except:
                print('no ' + month)
        try:
            c.retrieve(
                'seasonal-monthly-single-levels',
                {
                    'format': 'netcdf',
                    'originating_centre': 'ecmwf',
                    'system': '51',
                    'variable': [
                        '10m_wind_speed', '2m_temperature', 'mean_sea_level_pressure',
                        'surface_solar_radiation_downwards', 'total_precipitation',
                    ],
                    'product_type': 'hindcast_climate_mean',
                    'year': year,
                    'leadtime_month': [
                        '1', '2', '3',
                        '4', '5', '6',
                    ],
                    'month': month,
                },
                './ec_data/' + 'EC_' + month + '_sl_climate.nc')
        except:
            print('no ' + month)
