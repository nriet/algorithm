## 脚本说明
###### 如果想用更多分辨率的数据，把下面对应分辨率代码放开，注意（4000M里面brands对应的通道也要删掉，不删掉会覆盖前面的数据）
##### get_hdf.py
    # if res_str=='0500M':
        # res=0.005
        # brands=['02']
        # lc_file='500m.pkl'
    # elif res_str=='1000M':
        # res=0.01
        # brands=['01','03']
        # lc_file='1km.pkl'
    # elif res_str=='2000M':
        # res=0.02
        # brands=['04','05','06','07']
        # lc_file='2km.pkl'
    # elif res_str=='4000M':
        # res=0.04
        # brands=['08','09','10','11','12','13','14']
        # lc_file='4km.pkl'
    # else:
        # print('reslution error '+file_in)
        # break
    
    if res_str=='4000M':
        res=0.04
        brands=['01','02','03','04','05','06','07','08','09','10','11','12','13','14']
        lc_file='4km.pkl'
    else:
        print('reslution error '+file_in)
        break



## 算法配置文件
##### fy4a.ini

    run_command=python3 main_decode_python.py
    run_args={run_input}
    run_inputType=0
    run_input=
    run_outputType=0
    run_output=
    run_language=python






## 第一次需要先执行
### 第一步，生成经纬度信息文件
	python3 a0_ll2lc_fy4a.py
	#会生成一下四个文件，文件比较大会处理一段时间
	1km.pkl
	2km.pkl
	4km.pkl
	500m.pkl

### 第二步，gfortran相关配置
	f2py -m index2data -c index2data.f90
### 第三步测试
	python main_decode_python.py /data/fy4b/ /data/fy4b/nc/ FY4B-_AGRI--_N_DISK_1050E_L1-_FDI-_MULT_NOM_20240405054500_20240405055959_4000M_V0001.hdf
    python main_decode_python.py /data/fy4b/ /data/fy4b/nc/ FY4B-_AGRI--_N_DISK_1050E_L1-_FDI-_MULT_NOM_20240405054500_20240405055959_2000M_V0001.hdf
    python main_decode_python.py /data/fy4b/ /data/fy4b/nc/ FY4B-_AGRI--_N_DISK_1050E_L1-_FDI-_MULT_NOM_20240405054500_20240405055959_1000M_V0001.hdf
    python main_decode_python.py /data/fy4b/ /data/fy4b/nc/ FY4B-_AGRI--_N_DISK_1050E_L1-_FDI-_MULT_NOM_20240405054500_20240405055959_0500M_V0001.hdf
