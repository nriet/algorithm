1.调用'/home/zhfx/TQRadarMap/dist/bin'文件夹中的可执行程序 'Algo_QC'
Algo_QC：雷达解析、质控
调用：'./Algo_QC -i /home/zhfx/data_tmp/radar/s_radar/Z_RADR_I_Z9070_20241125163334_O_DOR_SC_CAP_FMT.bin.bz2 -o /home/zhfx/data_tmp/product/ -s Z9070'
-i：雷达数据文件路径
-o：中间雷达文件生成路径（即经过雷达解析和质控后的雷达数据）（路径后面最后一个'/'不可以省略）
最后生成的文件路径为：'/home/zhfx/product/QC/Z9070/20241125/KLGZ9070SC0020241125182454_QC.VOL.Z'，product后面的文件夹由算法自动生成
-s：该雷达文件的站点，即Z9070

2.调用'/home/zhfx/TQRadarMap/dist/bin'文件夹中的可执行程序 'Algo_PPIS/Algo_CAPPI_Grid'
下面以Algo_CAPPI_Grid举例：
调用：'./Algo_PPIS -i /home/zhfx/data_tmp/product/QC/Z9070/20241125/KLGZ9070SC0020241125163334_QC.VOL.Z -o /home/zhfx/data_tmp/product/'
-i：Algo_QC生成的中间雷达文件路径（从Algo_QC输出到终端上的日志获取）
日志：
sourceSiteCode:Z9070
load QC.ini configures done!!
create FileIO instance done!
file ID or file header length check fail
file ID check fail
Load Standard VTB successfully.
Read file success, file:/home/zhfx/data_tmp/radar/s_radar/Z_RADR_I_Z9599_20241125182454_O_DOR_SA_CAP_FMT.bin.bz2
create QC algorithm instance done!
i_dAz:1
Starting product path output.
/home/zhfx/product/QC/Z9070/20241125/KLGZ9070SC0020241125182454_QC.VOL.Z
Ending product path output.
Algo_QC: Program execution complete

Time Cost:
1155
  ms

-o：产品生成的路径（路径后面最后一个'/'不可以省略）
最后生成的文件路径为：'/home/zhfx/product/RADA/RADA_PUP/Z9070/20241125/2024112518/RCAPPI/KLGZ9070SC0020241125183032_RCAPPI.Z'，product后面的文件夹由算法自动生成
日志：
...
-- 12/10/2024 19:27:12  Algo_CAPPI::Time of Z9599 VCAPPI is 1732559094.
-- 12/10/2024 19:27:12  Algo_CAPPI::Time of Z9599 WCAPPI is 1732559094.
Starting product path output.
/home/zhfx/product/RADA/RADA_PUP/Z9070/20241125/2024112518/RCAPPI/KLGZ9070SC0020241125183032_RCAPPI.Z,/home/zhfx/product/RADA/RADA_PUP/Z9070/20241125/2024112518/VCAPPI/KLGZ9070SC0020241125183032_VCAPPI.Z,/home/zhfx/product/RADA/RADA_PUP/Z9070/20241125/2024112518/WCAPPI/KLGZ9070SC0020241125183032_WCAPPI.Z
Ending product path output.
Algo_CAPPI_Grid: Program execution complete

Time Cost:
2848
  ms
docker commit openeuler registry.cn-hangzhou.aliyuncs.com/nriet/algorithm:tqradarmap_openeuler_24.03_linux_arm64

openeuler_24.03_linux_arm64
