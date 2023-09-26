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




docker run --restart=always --name='SEDES2' -d nriet/algorithm:sedes-data-2023-08 tail -f main.py