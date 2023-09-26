#!/usr/bin/env python
# -*- coding: utf-8 -*-
from netCDF4 import Dataset
import numpy as np


class GridDataSet:
    nc_obj = None
    all_keys = []
    byteData = None

    def __init__(self, byteData):
        self.byteData = byteData
        self.nc_obj = Dataset('inmemory.nc', memory=self.byteData)
        for i in self.nc_obj.variables.keys():
            self.all_keys.append(i)
        self.time = np.asarray(self.nc_obj.variables[self.all_keys[0]][:])
        self.lat = np.asarray(self.nc_obj.variables[self.all_keys[1]][:])
        self.lon = np.asarray(self.nc_obj.variables[self.all_keys[2]][:])
        self.data = np.asarray(self.nc_obj.variables[self.all_keys[3]][:])

    def get_lat(self):
        return self.lat

    def get_lon(self):
        return self.lon

    def get_data(self):
        return self.data

    def get_time(self):
        return self.time

    def get_ncData(self):
        return self.nc_obj
