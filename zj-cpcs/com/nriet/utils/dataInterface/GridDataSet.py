#!/usr/bin/env python
# -*- coding: utf-8 -*- 
from  netCDF4 import Dataset
import numpy as np
import struct
import xarray as xr
import pandas as pd
class GridDataSet():
    nc_obj =None
    xar_obj=None
    all_keys=[]
    byteData=None
    noTime=0
    def __init__(self,byteData):
        self.byteData= byteData

        self.xar_obj=xr.open_dataset(byteData)
        self.noTime=1
        self.nodepth = 1
        self.nolon = 0
        self.nolat = 0
        self.all_keys=[]



    def get_xarray_data(self):
        return self.xar_obj