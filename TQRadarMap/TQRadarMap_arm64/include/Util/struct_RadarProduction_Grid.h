/**********************************************************************
* Copyright 2023-xxxx Nriet Co., Ltd.
* All right reserved. See COPYRIGHT for detailed Information
*
* Alternatively, you may use this file under the terms of the NRT license
* as follows:
**
* "Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions are
* met:
*   * Redistributions of source code must retain the above copyright
*     notice, this list of conditions and the following disclaimer.
*   * Redistributions in binary form must reproduce the above copyright
*     notice, this list of conditions and the following disclaimer in
*     the documentation and/or other materials provided with the
*     distribution.
*   * Neither the name of The NRT Company Ltd nor the names of its
*     contributors may be used to endorse or promote products derived
*     from this software without specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
* "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
* LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
* A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
* OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
* SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
* LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
* DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
* THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
* (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
* OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
*
* File:struct_RadarProduction_Grid.h
* Author:Nriet
* time 2023-05-24
*************************************************************************/
#ifndef STRUCT_PRO_H
#define STRUCT_PRO_H

#include <string>
#include <iostream>
#include <list>
#include <vector>

using std::list;
using std::vector;
using namespace std;

#define PREFILLVALUE -32768

/* 产品ID，
基于极坐标数据产品序列   VTB->GRID
101 = dBTCAPPI  // 不经过地物杂波消除的dBT值= UnZ/100
102 = dBZCAPPI    // 经过地物杂波消除的dBZ值= CorZ/100
103 = VCAPPI    // 速度值= V/100
                // 正值表示远离雷达的速度，负值表示朝向雷达的速度
104 = WCAPPI    // 谱宽值= W/100
107 = ZDR       // 反射率差值= ZDR/100，单位db
110 = PHDP;     // 差分传播相移= PHDP-(-18000)/100，单位度
111 = KDP;      // 差分传播相移常数= KDP/100，单位度/公里
109 = ROHV;     // 相关系数值= ROHV/100
108 = LDR;      // 退偏振比= LDR/100
122 = dBZFCST   // 反射率外推预报

基于格点数据产品序列   GRID->GRID  拼图
201 = dBTCAPPIMOSAIC  // 不经过地物杂波消除的dBT值= UnZ/100
202 = dBZCAPPIMOSAIC    // 经过地物杂波消除的dBZ值= CorZ/100
203 = VCAPPIMOSAIC    // 速度值= V/100
                // 正值表示远离雷达的速度，负值表示朝向雷达的速度
204 = WCAPPIMOSAIC    // 谱宽值= W/100
207 = ZDRMOSAIC       // 反射率差值= ZDR/100，单位db
210 = PHDPMOSAIC;     // 差分传播相移= PHDP-(-18000)/100，单位度
211 = KDPMOSAIC;      // 差分传播相移常数= KDP/100，单位度/公里
209 = ROHVMOSAIC;     // 相关系数值= ROHV/100
208 = LDRMOSAIC;      // 退偏振比= LDR/100

241 = dBTELEVMOSAIC     // 不经过地物杂波消除的dBT值= UnZ/100
242 = dBZELEVMOSAIC     // 经过地物杂波消除的dBZ值= CorZ/100
243 = VELEVMOSAIC       // 速度值= V/100
244 = WELEVMOSAIC       // 谱宽值= W/100
247 = ZDRELEVMOSAIC     // 反射率差值= ZDR/100，单位db
248 = LDRELEVMOSAIC;    // 退偏振比= LDR/100
249 = ROHVELEVMOSAIC;   // 相关系数值= ROHV/100
250 = PHDPELEVMOSAIC;   // 差分传播相移= PHDP-(-18000)/100，单位度
251 = KDPELEVMOSAIC;    // 差分传播相移常数= KDP/100，单位度/公里

264 = ELCR = PTYPE_MAX + 260

219 = WINDRETRIEVAL(OPTICALFLOW)
220 = WINDRETRIEVAL(DDA)
221 = vor
222 = div
229 = WINDMOSAIC
230 = vor
231 = div


ET    PTYPE_ET+300             // 回波顶高
EB    PTYPE_EB+300             // 回波底高
CR    PTYPE_MAX+300            // 组合反射率
VIL   PTYPE_VIL+300            // 累计液态水
QPE   PTYPE_QPE+300

600 = MESH
601 = RAIN              //Precipitation
602 = SS                 //Storm
603 = MESO               //Meso
604 = TVS                //Tornado vortex signature
605 = HAIL               //Hail Storm
606 = WIND               //Wind Hazard
*/
namespace  s_Pro_Grid{

typedef struct tagRadarProductParameters //此部分仅需要填写ProductionID,其他由算法输出
{
    int MagicNumber;                 //魔术字，用来指示雷达数据文件  Current:0x45673210  History:0x45673211
    unsigned short ProductionID;
    char ProductionName[32];//产品名称ZCAPPI，与产品ID对应
    char ProductMethod[32]; //产品实现方法，区分不同算法，例如单偏振QPE,双偏振QPE
    int ProductionTime;   //产品生成时间戳
    int DataStartTime;    //数据开始时间戳
    int DataEndTime;      //数据结束时间戳
    int DataFormat;       //产品格式   1=径向格式  2=栅格格式  101=多层径向格式  102=多层栅格格式   201=特定格式   202=文本格式
}RadarProductParameters;

typedef struct tagSiteInfo
{
    char SiteCode[8];                //站号，如Z9010(ASCII)
    char SiteName[32];               //站点名称，如Beijing(ASCII)
    float Latitude;                  //雷达天线所在纬度(度，-90.000000~90.000000)
    float Longitude;                 //雷达天线所在经度(度，-180.000000~180.000000)
    int AntennaHeight;               //天线高度，天线馈源水平时海波高度(米，0~9000)
    int GroundHeight;                //地面高度，雷达塔楼地面海波高度(米，0~9000)
    float Frequency;                 //工作频率(MHz，1.00~999000.00)
    float BeamWidthHori;             //水平波束宽度(度，0.10~2.00)
    float BeamWidthVert;             //垂直波束宽度(度，0.10~2.00)
    int RdaVersion;                  //RDA(雷达数据采集系统)版本号
    short RadarType;                 //雷达类型，1-SA, 2-SB, 3-SC, 4-SAD, 33-CA, 34-CB, 35-CC, 36-CCJ, 37-CD
}SiteInfo;

typedef struct tagRadarProductDataParameters //此部分由算法输出
{
    char VarName[32];
	int DScale;         //数值放大的倍数
    int DOffset;        //数据编码的偏移
    int DZero;          //无数据的代码
    int BinLength;      //每个数据所占用的字节数
        //数据值 = (存储值-Offset)/Scale
}RadarProductDataParameters;

typedef struct tagMapProjectionParameters  //此部分所有内容均应填写
{
    unsigned char mapproj; //仅当栅格格式时有效 1=Mercator lat-lon; 2=Azimuthal equidistant，等距方位投影；3=Lambert;
    float ctrlon; //unit:°   -180°~180°东经为正
    float ctrlat; //unit:°   -90°~90°北纬为正
	//if ctrlon & ctrlat = -32768, use radar location as ctrlon &ctrlat
    float trulat1; // Only used by Lambert projection(mapproj==1)
    float trulat2; // Only used by Lambert projection(mapproj==1)
    float trulon;  // Only used by Lambert projection(mapproj==1)
}MapProjectionParameters;

typedef struct tagGridParameters  //此部分所有内容均应填写
{
    unsigned short nrow;      //横轴、X轴（笛卡尔坐标）、径向（极坐标）
    unsigned short ncolumn;   //纵轴、Y轴（笛卡尔坐标）、切向（极坐标）
    unsigned short drow;
        //unit:m(笛卡尔坐标系下Azimuthal equidistant、Lambert、极坐标系) 1/50000°(笛卡尔坐标系下Mercator/lat-lon等经纬网格）
    unsigned short dcolumn;
        //unit:m(笛卡尔坐标系下Azimuthal equidistant、Lambert) 1/50000°(笛卡尔坐标系下Mercator/lat-lon等经纬网格、极坐标系）
    unsigned short nz;
    vector<unsigned short> z;  //unit:m
        //注：RHI二维格点数据时，高度方向使用row维，nz should be equal to 1.
        //注：RHI径向数据使用极坐标格式，仰角方向使用row维，nz should be equal to 1.
}GridParameters;

typedef struct tagCAPPIPARAMETER
{
    int QCMask;
}CAPPIPARAMETER;

typedef struct tagCRPARAMETER
{

}CRPARAMETER;

typedef struct tagETPARAMETER
{
    float dBZContour;
}ETPARAMETER;

typedef struct tagEBPARAMETER
{
    float dBZContour;
}EBPARAMETER;

typedef struct tagQPEPARAMETER
{
    int QPEMethod;//0:Auto; 1:DBZToR 2:DBZxZDRToR 3:KDPToR 4:KDPxZDRToR
    float DBZToR_a;
    float DBZToR_b;
    float DBZxZDRToR_a;
    float DBZxZDRToR_b;
    float DBZxZDRToR_c;
    float KDPToR_a;
    float KDPToR_b;
    float KDPxZDRToR_a;
    float KDPxZDRToR_b;
    float KDPxZDRToR_c;
    int TimeGap;  //Minutes
}QPEPARAMETER;

typedef struct tagQPFPARAMETER
{
    int QPFMethod;//0:CAPPI 1 = CR
    int Bottom;//m
    int Top;//m
    int Layer;
    int drow;//1/50000度
    int dcolumn;
    int FCSTINTERVAL;//min
    int FCSTTIME;//min
    int Mask;
    int Step;
    float DBZToR_a;
    float DBZToR_b;
}QPFPARAMETER;

typedef struct tagOHPPARAMETER
{
    int QPEMethod;//0:Auto; 1:DBZToR 2:DBZxZDRToR 3:KDPToR 4:KDPxZDRToR
    float DBZToR_a;
    float DBZToR_b;
    float DBZxZDRToR_a;
    float DBZxZDRToR_b;
    float DBZxZDRToR_c;
    float KDPToR_a;
    float KDPToR_b;
    float KDPxZDRToR_a;
    float KDPxZDRToR_b;
    float KDPxZDRToR_c;
    float TimeGap;  //Minutes
}OHPPARAMETER;

typedef struct tagDDAPARAMETER
{

}DDAPARAMETER;

typedef struct tagHCLPARAMETER
{

}HCLPARAMETER;

typedef struct tagDependentParameters
{
    union
    {
        char Reserved[64];
        CAPPIPARAMETER  cappiparameter;
        CRPARAMETER    crparameter;
        ETPARAMETER     etparameter;
        EBPARAMETER     ebparameter;
        DDAPARAMETER    ddaparameter;
        OHPPARAMETER    ohpparameter;
        HCLPARAMETER    hclparameter;
        QPEPARAMETER    qpeparameter;
        QPFPARAMETER    qpfparameter;
    };
}DependentParameters;


typedef struct tagDataBlock
{
    RadarProductDataParameters ProDataInfo;
    vector<char> ProductData; //unsigned short
}DataBlock;

typedef struct tagRadarProduct
{
    //RadarDataHead RadarInfo[MAXRADAR];
    s_Pro_Grid::RadarProductParameters ProInfo;
	vector<s_Pro_Grid::SiteInfo> SiteInfo;
    s_Pro_Grid::MapProjectionParameters MapProjInfo;
    s_Pro_Grid::GridParameters GridInfo;
    //AlgorithmParameters AlgorithmInfo;
    s_Pro_Grid::DependentParameters ParametersInfo;

    vector<s_Pro_Grid::DataBlock> DataBlock;
}RadarProduct;

}

#endif //STRUCT_PRO_H
