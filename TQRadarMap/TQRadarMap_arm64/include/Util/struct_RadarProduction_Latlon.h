#ifndef STRUCT_LATLON_H
#define STRUCT_LATLON_H

#include <string>
#include <iostream>
#include <list>
#include <vector>

using std::list;
using std::vector;
using namespace std;

typedef struct tagRadar_domain_struction //此部分仅需要填写ProductionID,其他由算法输出
{
    float slat, wlon;  // 0.01 deg 西南角经纬度
    float nlat, elon;  // 0.01 deg 东北角经纬度
    float clat, clon;  // 0.01 deg  中心经纬度
    int   rows, cols;  // 行列数
    float dlat, dlon;  // minimize = 0.01 deg 经纬度单位间隔
}LATLON_DOMAIN;

typedef struct tagLatLonGridDataFileHeaderStruct
{
    char  dataname[128];  // CREF_FZ 文件信息
    char  varname[32];    // CREF 变量名称
    char  units[16];      // dBZ 变量单位，默认dbz
    unsigned short label; // 'L'>>8|'L'
    short unitlen ;       // 2=short
    LATLON_DOMAIN  domain; // 经纬度信息
    unsigned short nodata;
    unsigned short offset;
//    float nodata;         // -32 for radar
    int  levelbytes;	  // data bytes of per-level
    short levelnum;       // level numbers of data 文件内一共的层数
    short amp;            // amplify factor = 10; 放大系数，dbz乘上放大系数后存储
    short compmode;       // 0 = LatLon grid; 1=sparse LatLon grid
    unsigned short dates;  // UTC dates 日期
    int   seconds;         // UTC seconds 秒
    short min_value;       // used in compress mode
    short max_value;       // used in compress mode

    // modified by liubojun, 扩展针对多层数据的支持
    short enablemultiLevel;	  // 是否存储多层，0表示只有一层，1表示多层
    short height;   //  or  forecast_time;
    //当数据为CAPPI多高度层数据时，为对应层的高度数值(m)；
    //当数据为光流外推数据时，为起报时间开始，到该预报时次的分钟数间隔(min);
    int index_nextbytes;	  // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
//    short offset;
    unsigned short azimuth;         // 当数据为扇面插值结果时，表示扇面的方位角（单位：0.1°）
    unsigned char cleanCache;       // 0=不需要前端清缓存, 1=需要前端清缓存
    char reserved;
//    short reserved;
//    short reserved[2];
} LLDF_HEADER;

typedef struct tagLatLonDatStruct
{
    LLDF_HEADER header;
    vector<char> data;
}LLDF_DATA_BLOCK;

typedef struct tagLatLonStruct
{
    vector<LLDF_DATA_BLOCK> data;
}LLDF_FORMAT;

typedef struct tagSparseHeader         // Sparse头信息
{
    short y;
    short x;
    short n;
}SPARSEHEADER;

typedef struct tagSparseInfo
{
    SPARSEHEADER sparseHeader;
    vector<unsigned char> data;
}SPARSEINFO;

typedef struct tagSparseLatLonDatStruct
{
    LLDF_HEADER header;
    vector<SPARSEINFO> sparseUnion;
}SPARSE_LLDF_DATA_BLOCK;

typedef struct tagSparseLatLonStruct
{
    vector<SPARSE_LLDF_DATA_BLOCK> data;
}SPARSE_LLDF_FORMAT;

#endif //STRUCT_LATLON_H
