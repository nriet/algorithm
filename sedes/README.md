# algorithm
基础算法镜像

numpy
netcdf4
cdsapi
xlrd
pandas
torch
xarray
matplotlib
joblib
pytorch_lightning

人工智能
python app/SEDES/main.py 2023-08




下载EC数据
# download ec and ec_climate data
# for year in range(yystart, yylast+1):
#     print(year)
#     download_ec(year, months)
#     download_ec_climate(str(year), months)
#
# # compute anomaly
# Anomaly_process(yystart, yylast, months)





docker run --restart=always --name='SEDES' -d nriet/algorithm:sedes-python3


docker run -u root --name='SEDES' -d \
nriet/algorithm:sedes-python3 \
tail -f /space/cmadaas/dpl/nriet/app/SEDES/main.py



docker run --rm -v /home/test/ec_data:/space/cmadaas/dpl/nriet/app/SEDES/ec_data nriet/algorithm:sedes-python3 