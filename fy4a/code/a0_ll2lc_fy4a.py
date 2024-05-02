# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 11:52:48 2017

@author: nriet
"""

import numpy as np
import pickle
#import matplotlib.pyplot as plt
#from mpl_toolkits.basemap import Basemap
#import struct
#from netCDF4 import Dataset

pi=3.1415926535897

#######################
# China
lon_l=70
lon_r=140
lat_u=55
lat_d=5

res_s=[0.005,0.01,0.02,0.04]
filenames=['FY4A_China_500m.pkl','FY4A_China_1km.pkl','FY4A_China_2km.pkl','FY4A_China_4km.pkl']

for i in np.arange(0,4):
    res=res_s[i]
    filesave=filenames[i]
    
    if i==0:
    ##  500m
        CFAC=81865099
        LFAC=81865099
        COFF=10991.5
        LOFF=10991.5
    elif i==1:
    ##  1km
        CFAC=40932549
        LFAC=40932549
        COFF=5495.5
        LOFF=5495.5
    elif i==2:
    ##  2km
        CFAC=20466274
        LFAC=20466274
        COFF=2747.5
        LOFF=2747.5
    elif i==3:
        ##  4km
        CFAC=10233137
        LFAC=10233137
        COFF=1373.5
        LOFF=1373.5


    sub_lon=104.7/180.0*pi

    lon_out=np.arange(lon_l,lon_r+0.001,res)
    lat_out=np.arange(lat_d,lat_u+0.001,res)


    lon_out,lat_out=np.meshgrid(lon_out,lat_out)
    lon_out=lon_out/180.0*pi
    lat_out=lat_out/180.0*pi

    eb=6356.7523
    ea=6378.137
    h=42164

    #c_lat=np.arctan(0.993243*np.tan(lat_out))
    c_lat=np.arctan((eb/ea)**2*np.tan(lat_out))

    #rl=6356.5838/np.sqrt(1-0.00675701*np.cos(c_lat)**2)

    rl=eb/(np.sqrt(1-(ea**2-eb**2)/ea**2*np.cos(c_lat)**2))

    r1=h-rl*np.cos(c_lat)*np.cos(lon_out-sub_lon)
    r2=-rl*np.cos(c_lat)*np.sin(lon_out-sub_lon)
    r3=rl*np.sin(c_lat)
    rn=np.sqrt(r1**2+r2**2+r3**2)

    rn_max=np.sqrt(h**2-ea**2)

    cc=rn>rn_max

    x=np.arctan(-r2/r1)/pi*180
    y=np.arcsin(-r3/rn)/pi*180

    c=COFF+np.round(x*2**-16*CFAC)
    l=LOFF+np.round(y*2**-16*CFAC)

    c[np.isinf(c)]=np.nan
    l[np.isinf(l)]=np.nan

    c[cc]=np.nan
    l[cc]=np.nan
    lc_info={'l':l,'c':c}
    output=open(filesave,'wb')
    pickle.dump(lc_info,output)
    output.close()
