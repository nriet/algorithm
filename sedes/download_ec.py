import cdsapi
import os

def download_ec(iyear, imonth):
    # iyear = 2023
    # imonth=["01",'02','03','04','05','06','07','08','09','10','11','12']
    # imonth = ['05']
    filedir = "./ec_data/"
    if not os.path.exists(filedir):
        os.makedirs(filedir)
    ipre = ["200", "500", "850"]
    c = cdsapi.Client()
    for year in range(iyear, iyear+1):
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
                                'v_component_of_wind', 'specific_humidity',
                            ],
                            'pressure_level': [
                                pre
                            ],
                            'product_type': 'monthly_mean',
                            'year': str(year),
                            'month': month,
                            'leadtime_month': [
                                '1', '2', '3',
                                '4', '5', '6',
                            ],
                            "grid": "1/1",
                            "area": "89.5/0.5/-89.5/359.5",
                        },
                        './ec_data/' + 'EC_' + str(year) + month + '_' + pre + '.nc')
                except:
                    print('no ' + str(year) + month)
            c.retrieve(
                'seasonal-monthly-single-levels',
                {
                    'format': 'netcdf',
                    'originating_centre': 'ecmwf',
                    'variable': [
                        '10m_wind_speed', '2m_temperature', 'mean_sea_level_pressure',
                        'surface_solar_radiation_downwards', 'total_precipitation',
                    ],
                    'system': '51',
                    'product_type': 'monthly_mean',
                    'year': str(year),
                    'month': month,
                    'leadtime_month': [
                        '1', '2', '3',
                        '4', '5', '6',
                    ],
                },
                './ec_data/' + 'EC_' + str(year) + month + '_sl.nc')
