#ifndef LIB_CAPPI_MOD_H
#define LIB_CAPPI_MOD_H

#include <stable.h>
#include <struct_WeatherRadar.h>
#include <struct_RadarProduction_Grid.h>
#include "string.h"
#include <iostream>
#include <omp.h>
#include "time.h"
#include "NrietAlgorithm.h"

typedef struct{
    int DataType;                   // var的数据类型
    int Range;                      // 量程，取各层最大量程，单位：米
    int BinWidth;                   // 量程最大处的库长，单位：米
    int BinNum;                     // 量程最大处的库数
    float RadarWestLongitude;       // 雷达西边界，以北纬60°为例，东西方向约55000 m
    float RadarEastLongitude;       // 雷达东边界
    float RadarSouthLatitude;       // 雷达南边界，南北方向约110000.0 m
    float RadarNorthLatitude;       // 雷达北边界
    int varCutNum;                  // 有效仰角层数
    vector<int> varElCutIndex;      // 仰角记录
    vector<int> varMomentIndex;     // var在该仰角层的MomentIndex
    vector<int> varBinNum;          //
    vector<int> varBinWidth;        //
    vector<int> varElRadialNum;     // 记录每层的径向数
    vector<int> varElRadialIndex;   // 每层仰角的起始径向数
}VARCAPPIINFO;

using namespace std;

typedef vector<s_Pro_Grid::RadarProduct> RadarProductList;

class CAlgoCAPPI:public CNrietAlogrithm
{
public:
    CAlgoCAPPI(){}
    virtual ~CAlgoCAPPI() override {}

    virtual int Init() override;
    virtual int LoadParameters(void *) override;
    virtual int LoadStdCommonBlock(void *) override;
    virtual int LoadStdRadailBlock(void *) override;
    virtual int LoadStdData(void *) override;
    virtual int MakeProduct() override;
    virtual void* GetProduct(void) override;
    virtual int FreeData() override;
    virtual int Uninit() override;
    virtual int SetDebugLevel(int) override;


private:
    COMMONBLOCK* m_RadarHead_org = nullptr;
    WRADRAWDATA* m_RadarData_org = nullptr;

    RadarProductList* m_RadarProParameters_org = nullptr;   // in   输入算法参数头指针
    RadarProductList* m_RadarPro = nullptr;       // out  输出产品头指针，包含雷达数据头及产品生成参数

    //short* m_RadarProData = nullptr;                  // out  输出格点数据指针
    vector<short> m_RadarProData;
    float* m_GridLat = nullptr;                      // 中间变量 格点纬度
    float* m_GridLon = nullptr;                      // 中间变量 格点经度
    float* m_GridHeight = nullptr;                   // 中间变量 格点高度

    float m_RadarWestLongitude = 0;                //雷达西边界
    float m_RadarEastLongitude = 0;                //雷达东边界
    float m_RadarSouthLatitude = 0;                //雷达南边界
    float m_RadarNorthLatitude = 0;                //雷达北边界

//	int m_nRadarNum = 1;                        //雷达数
//	bool m_bDataIsLoaded = FALSE;               // 加载标志
    int m_LayerNum = 0;                    // 扫描层数

    typedef struct
    {
        short cut_index;
        short moment_index;
    }VarIndex;

    vector<vector<VarIndex>> m_moment_index;
    //int m_nRadialNum[MAXLAYER] = { 0 };           // 每层径向数
    int m_nRadialNumSum = 0;                      // 总有效径向数
    unsigned short m_binNumber = 0;
    unsigned short m_binWidth = 0;              //米

    int m_DebugLevel = 2;
    //1:Error message   2:process message   3:debug message
    char time_str[32];
    void set_time_str();

    int InitProHead();
    int GetRadarPara();
    int InitGridPara();
    int InitProGrid();
    int CalcCAPPI();
    int CalcOneGrid(int iGrid);
    int CalcOneGrid_NEW(int iGrid);
    int CalcGridtoRadarLoc(float* i_GridtoRadarElev, float* i_GridtoRadarAz, float* i_GridtoRadarDis, int iGrid);
    int CalcGridtoRadarLoc_NEW(float* i_GridtoRadarElev, float* i_GridtoRadarAz, float* i_GridtoRadarDis, int iGrid, int iPro);
//    int FindGridtoRadarIndex(float i_GridtoRadarElev, float i_GridtoRadarAz, int* i_RecordLowLeftIndex, int* i_RecordLowRightIndex, int* i_RecordHighLeftIndex, int* i_RecordHighRightIndex);
    int FindGridtoRadarIndex(double i_GridtoRadarElev, double i_GridtoRadarAz, int i_pro, int* i_RecordLowLeftIndex, int* i_RecordLowRightIndex,\
                             int* i_RecordHighLeftIndex, int* i_RecordHighRightIndex, int* i_moment_index_low, int* i_moment_index_high);
    int FindGridtoRadarIndex_NEW(double i_GridtoRadarElev, double i_GridtoRadarAz, int i_Pro, int* i_RecordLowLeftIndex, int* i_RecordLowRightIndex, \
                                 int* i_RecordHighLeftIndex, int* i_RecordHighRightIndex, int* i_moment_index_low, int* i_moment_index_high);
    void Calclonlat(float radarLon, float radarLat, int radarHeight, float elev, float az, float dst, float& tagLon, float& tagLat);
    int FreeBlock();

    vector<int> ElRadialNum;                                             //记录每层的径向数
    vector<int> ElRadialIndex;
    int GetRadialNumOfEl();
    int GetRadialIndexOfEl();

    ///Var Info
    vector<VARCAPPIINFO> m_VarInfo;
    void GetVarInfo();
    time_t time_convert(int year, int month, int day, int hour,int minute, int second);


};
extern "C" CNrietAlogrithm * GetAlgoInstance();
#endif // LIB_CAPPI_MOD_H
