#ifndef LIB_PPIS_H
#define LIB_PPIS_H

#include <struct_WeatherRadar.h>
#include <struct_WeatherRadarProduct.h>
#include "stable.h"
#include <list>
#include <vector>
#include <string>
#include <string.h>
#include <math.h>
#include <fstream>
#include <iostream>
#include "NrietAlgorithm.h"

typedef vector<WRADPRODATA_PARA_IN> WRADPROLIST_IN;
typedef vector<WRADPRODATA> WRADPROLIST_OUT;

class CAlgoPPIS:public CNrietAlogrithm
{
public:
    CAlgoPPIS(){}
    virtual ~CAlgoPPIS() override {}

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

    WRADPROLIST_IN* m_RadarProParameters_org = nullptr;      // 雷达数据头
    WRADRAWDATA* m_RadarData_org = nullptr;      // 雷达数据头
    WRADPROLIST_OUT* m_RadarPro_out = nullptr;    //产品头，包含雷达数据头及产品生成参数

    int m_DebugLevel = 2;    //1:Error message   2:process message   3:debug message
    char time_str[32];

    int m_LayerNum;
    int m_ProNum;

    vector<int> ElRadialNum;                                             //记录每层的径向数
    vector<int> ElRadialIndex;

    void set_time_str();

    int SetProOutHead();
    int GetRadialNumOfEl();
    int GetRadialIndexOfEl();
    int MakePPIPro();

};
extern "C" CNrietAlogrithm * GetAlgoInstance();

#endif // LIB_PPIS_H
