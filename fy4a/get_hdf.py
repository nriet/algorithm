# -*- coding: utf-8 -*-
"""
Created on Sat May 19 22:44:15 2018

@author: nriet
"""

import numpy as np
#from mpl_toolkits.basemap import Basemap
#import matplotlib.pyplot as plt
import h5py
import pickle
import time
from netCDF4 import Dataset
#import paramiko
import shutil
import os
from index2data import index2data,cal2data,cal2data_07

###################


def get_hdf(path_in,path_out,file_in):
    
#    time0=time.mktime(time.strptime('%Y%m%d_%H%M%S'))
    
    time_s_c=file_in.split('_')[15]
    time_e_c=file_in.split('_')[16]
    
    time_s=time.mktime(time.strptime(time_s_c,'%Y%m%d%H%M%S'))
    time_e=time.mktime(time.strptime(time_e_c,'%Y%m%d%H%M%S'))
    
    time_str=time_s_c[0:12]
    path_temp=time_s_c[0:8]
    
    
    res_str=file_in.split('_')[-2]
    
    # if res_str=='0500M':
        # res=0.005
        # brands=['02']
        # lc_file='FY4A_China_500m.pkl'
    # elif res_str=='1000M':
        # res=0.01
        # brands=['01','03']
        # lc_file='FY4A_China_1km.pkl'
    # elif res_str=='2000M':
        # res=0.02
        # brands=['04','05','06','07']
        # lc_file='FY4A_China_2km.pkl'
    # elif res_str=='4000M':
        # res=0.04
        # brands=['08','09','10','11','12','13','14']
        # lc_file='FY4A_China_4km.pkl'
    # else:
        # print('reslution error '+file_in)
        # break
    
    #print('res_str:'+res_str)
    if res_str=='4000M':
        res=0.04
        brands=['01','02','03','04','05','06','07','08','09','10','11','12','13','14']
        lc_file='/home/algorithm/fy4a-2.0/FY4A_China_4km.pkl'
    elif res_str=='0500M':
        res=0.005
        brands=['02']
        lc_file='/home/algorithm/fy4a-2.0/FY4A_China_500m.pkl'
    else:
        print('reslution error '+file_in)
    
    #print('lc_file:'+lc_file)
    
    pkl_file=open(lc_file,'rb')
    lc_info=pickle.load(pkl_file)
    pkl_file.close()
    l=np.array(np.round(lc_info['l']),int) #y
    c=np.array(np.round(lc_info['c']),int) #x
    
    nx,ny=np.shape(l)
    
    lon_l=70
    lon_r=140
    lat_u=55
    lat_d=5
    
    lon_out=np.arange(lon_l,lon_r+0.001,res)
    lat_out=np.arange(lat_d,lat_u+0.001,res)
    
    area=file_in.split('_')[9]

    try:
    #if 1:
        now0=time.time()
        f_hdf=h5py.File(path_in+file_in,'r')
        
#        f_hdf.keys()

        s_l=f_hdf.attrs['Begin Line Number'][0]
        e_l=f_hdf.attrs['End Line Number'][0]
        s_c=f_hdf.attrs['Begin Pixel Number'][0]
        e_c=f_hdf.attrs['End Pixel Number'][0]
        
        l[l>e_l]=0
        c[c>e_c]=0
        
        l=l-s_l
        c=c-s_c
        
        for brand in brands:
            #try:
            if 1:

                cal=np.array(f_hdf['CALChannel'+brand],'float64')
                data=np.array(f_hdf['NOMChannel'+brand],'int')
        
                brand_0=index2data(data,l,c)
                
                if brand=='07':
                    brand_out=cal2data_07(brand_0,cal)
                else:
                    brand_out=cal2data(brand_0,cal)
                if brand=='02':
                    brand_out=brand_out*100
                    for i in range(len(brand_out)):
                        for j in range(len(brand_out[0])):
                            if brand_out[i][j]<0.1:
                                brand_out[i][j]=0
                path_out_b=path_out+'B'+brand+'/'+path_temp+'/'
                if os.path.exists(path_out_b)==False:
                    os.makedirs(path_out_b)
                
                file_out=path_out_b+'MOP_CHINA_FY_B'+brand+'_'+time_str+'.nc'
                
                if (int(brand)<=6):
                    
                    varname='albedo'     
                else:
                    varname='tbb'
                
                
                f_out=Dataset(file_out,'w',format='NETCDF3_CLASSIC')
                x_dim=f_out.createDimension(dimname='lon',size=len(lon_out))
                y_dim=f_out.createDimension(dimname='lat',size=len(lat_out))

                lon_out_c = f_out.createVariable(varname="lon", datatype="f4", dimensions=("lon",))
                lat_out_c = f_out.createVariable(varname="lat", datatype="f4", dimensions=("lat",))

                var_out_c= f_out.createVariable(varname=varname, datatype="f4", dimensions=("lat","lon"),fill_value=-1)

                lon_out_c[:]=lon_out
                lat_out_c[:]=lat_out
                
                var_out_c[:]=brand_out
                f_out.close()
                
                    # shutil.copy('tbb.nc',file_out)
        
                    # f=Dataset(file_out,'a')
                    # f.variables['latitude'][:]=lat_out
                    # f.variables['longitude'][:]=lon_out
                    # f.variables['start_time'][:]=time_s
                    # f.variables['end_time'][:]=time_e
                    # f.variables['tbb'][:]=brand_out
                    # f.close()
                print('Done '+brand+' '+time_str)
      #      except:
      #          print('Error '+brand+' '+time_str)
                
        f_hdf.close()
        flag=1
    except Exception as err:
        flag=0
        print(err)
        print('Error:'+time_str)
    return flag
        
