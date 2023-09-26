from abc import ABCMeta, abstractmethod


class CommonService:

    def __init__(self, input_data, lon=None, lat=None, lon_indexes=None,lat_indexes=None,station_lon=None,station_lat=None,request_dict=None, dims=None,plot=None):
        '''
        Service
        :param input_data:
        :param lon:
        :param lat:
        :param request_dict:
        '''
        self.request_dict = request_dict
        self.input_data = input_data
        self.lon = lon
        self.lat = lat
        self.lon_indexes =lon_indexes
        self.lat_indexes =lat_indexes
        self.dims =dims
        self.plot = plot
        self.station_lon=station_lon
        self.station_lat=station_lat

    def draw(self):
        pass
