## 脚本说明
###### 如果想用更多分辨率的数据，把下面对应分辨率代码放开，注意（4000M里面brands对应的通道也要删掉，不删掉会覆盖前面的数据）
##### get_hdf.py
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
    
    if res_str=='4000M':
        res=0.04
        brands=['01','02','03','04','05','06','07','08','09','10','11','12','13','14']
        lc_file='FY4A_China_4km.pkl'
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
	FY4A_China_1km.pkl
	FY4A_China_2km.pkl
	FY4A_China_4km.pkl
	FY4A_China_500m.pkl

### 第二步，gfortran相关配置
	f2py -m index2data -c index2data.f90
### 第三步测试
	python3 main_decode_python.py /nfs/ANHUI/data/obs/sate/FY4A/2019/10/12/ /nfs/ANHUI/data/obs/sate/FY4A_NRIET/ Z_SATE_C_BAWX_20191012021656_P_FY4A-_AGRI--_N_DISK_1047E_L1-_FDI-_MULT_NOM_20191012020000_20191012021459_4000M_V0001.HDF