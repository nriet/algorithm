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
* File:struct_WeatherRadarProduct.h
* Author:Nriet
* time 2023-05-24
*************************************************************************/
#pragma once

#include <string>
#include <iostream>
#include <list>
#include <vector>
#include <struct_WeatherRadar.h>
#include <struct_RadarProduction_Grid.h>

using std::list;
using std::vector;
using namespace std;

#define PREFILLVALUE -32768
//#define LAYERNUM   32		       // 扫描层数-动态    (TASKCONFIG.CutNumber)
//#define BINNUM     3000              // 径向库数-动态    (MOMENTHEADER.Length / MOMENTHEADER.BinLength)
//#define RADIALNUM  1000              // 径向数-动态      (RADIALHEADER.RadialNumber)
//**********************************************************************

#ifdef STRUCT_PACKED
#undef STRUCT_PACKED
#endif

#ifdef __GNUC__
//#define STRUCT_PACKED __attribute__((packed))
#define STRUCT_PACKED
#else
#   pragma pack(push,1)
#   define STRUCT_PACKED
#endif

typedef struct STRUCT_PACKED
{
    int ProductType;                //产品类型见表3-2
    char ProductName[32];           //用户自定义的产品名称
    int ProductGennerationTime;     //产品生成的时间为UTC标准时间计数,1970年1月1日0时为起始计数基准点。
    int ScanStartTime;              //当前任务扫描开始时间，为UTC标准时间计数,1970年1月1日0时为起始计数基准点。
    int DataStartTime;              //产品数据的开始时间。以PPI产品为例，第一层开始的时间为UTC标准时间计数,1970年1月1日0时为起始计数基准点。
    int DataEndTime;                //产品数据结束时间。以PPI产品为例，最后一层结束的时间。时间为UTC标准时间计数,1970年1月1日0时为起始计数基准点。
    int ProjectionType;             //地理信息的投影类型。见表3-3
    int DataType1;                  //产品输入的主数据类型。见表2-6
    int DataType2;                  //产品输入的从数据类型。见表2-6
    char Reserved[64];              //保留字段
}PRODUCTHEADER;

/*表2-6 数据类型定义
Data Type 数据类型	MOMENT 数据类型名称	REMARKS 描述
0	Reserved	数据标志，保留
1	dBT	滤波前反射率（Total Reflectivity）
2	dBZ	滤波后反射率(Reflectivity)
3	V	径向速度(Doppler Velocity)
4	W	谱宽（Spectrum Width）
5	SQI	信号质量指数（Signal Quality Index）
6	CPA	杂波相位一致性（Clutter Phase Alignment）
7	ZDR	差分反射率（Differential Reflectivity）
8	LDR	退偏振比（Liner Differential Ratio）
9	CC	协相关系数（Cross Correlation Coefficient）
10	ΦDP	差分相移（Differential Phase）
11	KDP	差分相移率（Specific Differential Phase）
12	CP	杂波可能性（Clutter Probability）
13	Reserved	数据标志，保留
14	HCL	双偏振相态分类（Hydro Classification）
15	CF	杂波标志（Clutter Flag）
16	SNRH	水平通道信噪比（Horizontal Signal Noise Ratio）
17	SNRV	垂直通道信噪比（Vertical Signal Noise Ratio）
18-31	Reserved	数据标志，保留
32	Zc	订正后反射率（Corrected Reflectivity）
33	Vc	订正后径向速度(Corrected Doppler Velocity)
34	Wc	订正后谱宽（Corrected Spectrum Width）
35	ZDRc	订正后差分反射率（Corrected Differential Reflectivity)
36-70	Reserved	数据标志，保留
71	RR	降水率（Rain Rate）
72	HGT	高度（Height）
73	VIL	垂直积分液态含水量（Vertically Integrated Liquid）
74	SHR	切变（Shear）
75	RAIN	降水量（Rainfall）
76	RMS	均方根（Root Mean Square）
77	CTR	等值线（Contour）
*/

/*表 3-2 产品类型列表
PRODUCT TYPE 产品类型	PRODUCT NAME 产品名称	REMARKS 描述
1	PPI     Plan Position Indicator                 平面位置显示              Radial Format 径向格式
2	RHI     Range Height Indicator                  距离高度显示              Raster Format 栅格格式
3	CAPPI	Const Altitude PPI                      等高面显示
4	MAX     Maximum                                 最大值
5   CR      Composite Reflectivity                  组合反射率              Radial Format 径向格式
6	ET      Echo Tops                               回波顶高                Raster Format 栅格格式
7   EB      Echo Bottom                             回波底高                Raster Format 径向格式
8	VCS     Vertical Cross Section                  垂直剖面                Raster Format 栅格格式
9	LRA     Layer Composite Reflectivity Average    分层组合反射率平均值      Raster Format 栅格格式
10	LRM     Layer Composite Reflectivity Maximum    分层组合反射率最大值      Raster Format 栅格格式
13	SRR     Storm Relative Mean Radial Velocity Region 风暴相对径向速度区域   Radial Format 径向格式
14	SRM     Storm Relative Mean Radial Velocity Map 风暴相对径向速度         Radial Format 径向格式
16  ET      Echo Tops                               回波顶高                Radial Format 径向格式
17  EB      Echo Bottom                             回波底高                Radial Format 径向格式
20	WER     Weak Echo Region                        弱回波区
22	VIL     Vertically Integrated Liquid Water      垂直累计液态水含量       Radial Format 栅格格式
23	VIL     Vertically Integrated Liquid Water      垂直累计液态水含量       Raster Format 栅格格式
24	HSR     Hybrid Scan Reflectivity                混合扫描反射率          Radial Format 径向格式
25	OHP     One Hour Precipitation                  一小时降雨累积
26	THP     Three Hours Precipitation               三小时降雨累积
27	STP     Storm Total Precipitation               风暴总降水累积
28	USP     User Selectable Precipitation           用户可选降雨累积
31	VAD     Velocity Azimuth Display                速度方位显示
32	VWP     Velocity Azimuth Display (VAD) Wind Profile VAD风廓线
34	CS      Shear                                   风切变                 Raster Format 栅格格式
36	SWP     Severe Weather Probability              强天气概率
37	STI     Storm Track Information                 风暴追踪信息
38	HI      Hail Index                              冰雹指数
39	M       Mesocyclone                             中尺度气旋
40	TVS     Tornado Vortex Signature                龙卷涡旋特征
41	SS      Storm Structure                         风暴结构
42  GF      Gusty Front                             阵风锋结构
48	GAGE	Rain Gage                               雨量计
51	HCL     Hydro Class                             水汽分类                Radial Format 径向格式
52	QPE     Quantitative Precipitation Estimation   双偏振定量降水估测       Radial Format 径向格式
*/

typedef enum
{
    PTYPE_PPI = 1,
    PTYPE_RHI = 2,
    PTYPE_CAPPI = 3,
    PTYPE_MAX = 4,
    PTYPE_CR = 5,   // Radial Format
    PTYPE_CRH_RADIAL = 15,   // Radial Format
    PTYPE_ET = 6,   // Raster Format
    PTYPE_ET_RADIAL = 16,   // Radial Format
    PTYPE_EB = 7,   // Raster Format
    PTYPE_EB_RADIAL = 17,   // Radial Format
    PTYPE_VCS = 8,
    PTYPE_LRA = 9,
    PTYPE_LRM = 10,
    PTYPE_SRR = 13,
    PTYPE_SRM = 14,
    PTYPE_WER = 20,
    PTYPE_VIL_RADIAL = 22,  // Radial Format
    PTYPE_VIL = 23, // Raster Format
    PTYPE_HSR = 24,
    PTYPE_OHP = 25,
    PTYPE_THP = 26,
    PTYPE_STP = 27,
    PTYPE_USP = 28,
    PTYPE_VAD = 31,
    PTYPE_VWP = 32,
    PTYPE_Shear = 34,
    PTYPE_SWP = 36,
    PTYPE_STI = 37,
    PTYPE_HI = 38,
    PTYPE_M = 39,
    PTYPE_TVS = 40,
    PTYPE_SS = 41,
    PTYPE_GF = 42,
    PTYPE_DB = 43,
    PTYPE_RS = 44,
    PTYPE_GAGE = 48,
    PTYPE_ML = 50,      // melting layer
    PTYPE_HCL = 51,
    PTYPE_PolarQPE = 52,
    PTYPE_QPE = 53,
    PTYPE_PolarOHP = 54,
    PTYPE_PolarSTP = 57,
    PTYPE_UV = 61,      //光流风场
    PTYPE_FLOW = 62,    //光流外推
    PTYPE_QPF = 63,
    PTYPE_2DUV = 64,      //2D光流风场(CR)
    PTYPE_RVD = 101,   //径向散度，采用PPI径向格式，每层仰角单独输出，数据范围(-100~100) * 10e-4 s-1
    PTYPE_ARD = 102,   //方位涡度，采用PPI径向格式，每层仰角单独输出，数据范围(-100~100) * 10e-4 s-1
    PTYPE_CS = 103,    //联合切变，采用PPI径向格式，每层仰角单独输出，数据范围(0~150) * 10e-4 s-1
    PTYPE_HR = 110,    //强降水识别，0：非强降水；1：强降水
    PTYPE_SAT = 208,        // 颠簸
    PTYPE_ACC = 209,        // 积冰
    PTYPE_LGT = 210,        // 雷电
    PTYPE_LTA = 78,
    PTYPE_LTM = 79,
    PTYPE_LTH = 80,
}PRODUCT_TYPE;

namespace KJC
{
    typedef enum
    {
        PTYPE_PPIDBZ = 0,
        PTYPE_PPIDBT = 1,
        PTYPE_PPIV = 2,
        PTYPE_PPISW = 3,
        PTYPE_CAPPIDBZ = 20,   // Radial Format
        PTYPE_CAPPIDBT = 21,   // Radial Format
        PTYPE_CAPPIV = 22,   // Raster Format
        PTYPE_CAPPISW = 23,   // Radial Format
        PTYPE_RHIDBZ = 40,   // Raster Format
        PTYPE_RHIDBT = 41,   // Radial Format
        PTYPE_RHIV = 42,
        PTYPE_RHISW = 43,
        PTYPE_CR = 100,
        PTYPE_ZR = 101,
        PTYPE_ET = 102,
        PTYPE_EB = 103,
        PTYPE_VIL = 104,  // Radial Format
        PTYPE_RVD = 105, // Raster Format
        PTYPE_ARD = 106,
        PTYPE_CS = 107,
        PTYPE_MAX = 108,
        PTYPE_WER = 109,
        PTYPE_LTA = 110,
        PTYPE_SWP = 111,
        PTYPE_OHP = 112,
        PTYPE_USP = 113,
        PTYPE_VWP = 150,
        PTYPE_VAD = 151,
        PTYPE_EDWF = 152,
        PTYPE_SS = 200,
        PTYPE_GFI = 201,
        PTYPE_HI = 202,
        PTYPE_DBI = 203,
        PTYPE_M = 204,
        PTYPE_RS = 205,
        PTYPE_TVS = 206,
        PTYPE_STI = 207,
        PTYPE_SAT = 208,
        PTYPE_ACC = 209,
        PTYPE_LGT = 210,
        PTYPE_EXP = 300,
        PTYPE_EV = 301,
		PTYPE_SRM = 350,
    //    PTYPE_FLOW = 62,    //光流外推
    //    PTYPE_RVD = 101,   //径向散度，采用PPI径向格式，每层仰角单独输出，数据范围(-100~100) * 10e-4 s-1
    //    PTYPE_ARD = 102,   //方位涡度，采用PPI径向格式，每层仰角单独输出，数据范围(-100~100) * 10e-4 s-1
    //    PTYPE_CS = 103,    //联合切变，采用PPI径向格式，每层仰角单独输出，数据范围(0~150) * 10e-4 s-1
    //    PTYPE_HR = 110,    //强降水识别，0：非强降水；1：强降水
    }PRODUCT_TYPE;
}
/*表 3-2 产品类型列表
TYPE 类型	PROJECTION NAME 投影名称	REMARKS 描述
1	MERCATOR	麦卡托投影
2	AZIMUTHAL EQUIDISTANT	等距方位投影
13	LAMBERT AZIMUTHAL EQUAL AREA	兰勃特方位等积投影
*/

///PRODUCTDEPENDENTPARAMETER***********************************************************************
typedef struct STRUCT_PACKED
{
    float Elevation;    //Unit:degree
}PPIPARAMETER;

typedef struct STRUCT_PACKED
{
    float Azimuth;  //Unit:degree
    int Top;        //Unit:m
    int Bottom;     //Unit:m
}RHIPARAMETER;

typedef struct STRUCT_PACKED
{
    int Layer;
    int Top;
    int Bottom;
    int CAPPIFill;
}CAPPIPARAMETER;

typedef struct STRUCT_PACKED
{
    int Top;
    int Bottom;
}MAXPARAMETER;

typedef struct STRUCT_PACKED
{
    float dBZContour;
}ETPARAMETER;

typedef struct STRUCT_PACKED
{
    float AzimuthofStart;
    int RangeofStart;
    float AzimuthofEnd;
    int RangeofEnd;
    int Top;
    int Bottom;
}VCSPARAMETER;

typedef struct STRUCT_PACKED
{
    int Range;
    float Azimuth;
    int SideLength;
    int Levels;
}WERPARAMETER;

typedef struct STRUCT_PACKED
{
    int Layer;
    short Height[30];
}VADPARAMETER;

typedef struct STRUCT_PACKED
{
    int Layer;
    short Height[30];
}VWPPARAMETER;

typedef struct STRUCT_PACKED
{
    int BaseProduct;
    int CAPPIHeight;
    int CAPPIFill;
    int RainGageAdjustment;
}STPPARAMETER;

typedef struct STRUCT_PACKED
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
}QPEPARAMETER;

typedef struct
{
    int Layer;
    int Top;
    int Bottom;
    int CAPPIFill;
    float THW1;
    float THW2;
    float THW3;
    int MinGridNum;
}SATPARAMETER;

typedef struct
{
    int Layer;
    int Top;
    int Bottom;
    int CAPPIFill;
    int MLH;
    float THDBZ1;
    float THDBZ2;
    float THDBZ3;
    int MinGridNum;
}ACCPARAMETER;

typedef struct
{
    int Height;
    float THDBZ1;
    float THDBZ2;
    float THDBZ3;
    float THDBZ4;
    int MinGridNum;
}LGTPARAMETER;

typedef struct STRUCT_PACKED
{
    int BaseProduct;
    int CAPPIHeight;
    int CAPPIFill;
    int RainGageAdjustment;
    int QPEMethod;
}OHPPARAMETER;

typedef struct STRUCT_PACKED
{
    int MaxRange;
}STIPARAMETER;

typedef struct STRUCT_PACKED
{
    int MaxRange;
}HIPARAMETER;

typedef struct STRUCT_PACKED
{
    int MaxRange;
}MPARAMETER;

typedef struct STRUCT_PACKED
{
    int MaxRange;
}TVSPARAMETER;

typedef struct STRUCT_PACKED
{
    int MaxRange;
}SSPARAMETER;

typedef struct STRUCT_PACKED
{
    int MaxRange;
}DBPARAMETER;

typedef struct STRUCT_PACKED
{
    int MaxRange;
}RSPARAMETER;

typedef struct STRUCT_PACKED
{
    float Elevation;
}HCLPARAMETER;

typedef struct STRUCT_PACKED
{
    float Elevation;
    int MaxHeight;      // 融化层顶最大高度，单位：m
    float MaxElev;
    float MinElev;
    float MaxCC;
    float MinCC;
    float MaxZH;
    float MinZH;
    float MaxZDR;
    float MinZDR;
    int ContHGT;
    float ContPCT;
    float MaxRatio;
}MLPARAMETER;

typedef struct STRUCT_PACKED
{
    float Top1;
    float Top2;
    float Top3;
    float C;
    float L;
}LTPARAMETER;

typedef struct STRUCT_PACKED
{
    union
    {
        char Reserved[64];
        PPIPARAMETER    ppiparameter;
        RHIPARAMETER    rhiparameter;
        CAPPIPARAMETER  cappiparameter;
        MAXPARAMETER    maxparameter;
        ETPARAMETER     etparameter;
        WERPARAMETER    werparameter;
        VADPARAMETER    vadparameter;
        VWPPARAMETER    vwpparameter;
        STPPARAMETER    stpparameter;
        OHPPARAMETER    ohpparameter;
        STIPARAMETER    stiparameter;
        HIPARAMETER     hiparameter;
        MPARAMETER      mparameter;
        TVSPARAMETER    tvsparameter;
        SSPARAMETER     ssparameter;
        DBPARAMETER     dbparameter;
        RSPARAMETER     rsparameter;
        HCLPARAMETER    hclparameter;
        MLPARAMETER     mlparameter;
        QPEPARAMETER    qpeparameter;
        SATPARAMETER    satparameter;
        ACCPARAMETER    accparameter;
        LGTPARAMETER    lgtparameter;
        LTPARAMETER     ltparameter;
    };
}PRODUCTDEPENDENTPARAMETER;

typedef struct STRUCT_PACKED
{
    PRODUCTHEADER productheader;
    PRODUCTDEPENDENTPARAMETER productdependentparameter;
}PRODUCTHEADERBLOCK;
///径向格式********************************************************************
typedef struct STRUCT_PACKED
{
    int DataType;
    int Scale;
    int Offset;
    short BinLength;
    short Flags;
    int Resolution;//m
    int StartRange;//m
    int MaxRange;//m
    int NumOfRadials;
    int MaxValue;
    int RangeOfMaxValue;//m
    float AzOfMaxValue;
    int MinValue;
    int RangeOfMinValue;
    float AzOfMinValue;
    char Reserved[8];
}  RADIALHEADERBLOCK;

typedef struct STRUCT_PACKED
{
    float StartAngle;
    float AnglularWidth;
    int NumOfBins;
    char Reserved[20];
}RADIALDATAHEADERBLOCK;

typedef struct STRUCT_PACKED
{
    vector <char> Data;
}RADIALDATADATABLOCK;

typedef struct STRUCT_PACKED
{
    RADIALDATAHEADERBLOCK RadialDataHead;
    RADIALDATADATABLOCK RadialDataData;
}RADIALDATABLOCK;

typedef struct STRUCT_PACKED
{
    RADIALHEADERBLOCK RadialHeader;
    vector<RADIALDATABLOCK> RadialData;
}RADIALFORMAT;
///栅格格式*******************************************************************
typedef struct STRUCT_PACKED
{
    int DataType;
    int Scale;
    int Offset;
    short BinLength;
    short Flags;
    int RowResolution;
    int ColumnResolution;
    int RowSideLength;
    int ColumnSideLength;
    int MaximumData;
    int RangeOfMaximumValue;
    float AzimuthOfMaximumValue;
    int MinimumData;
    int RangeOfMinimumValue;
    float AzimuthOfMinimumValue;
    char Reserved[8];
}RASTERHEADERBLOCK;

typedef struct STRUCT_PACKED
{
    vector <char> Data;
}RASTERDATABLOCK;

typedef struct STRUCT_PACKED
{
    RASTERHEADERBLOCK RasterHeader;
    RASTERDATABLOCK RasterData;
}RASTERFORMAT;
///CAPPI产品格式***************************************************************
//typedef struct STRUCT_PACKED
//{
//    vector <RADIALHEADERBLOCK> RadialHeader;
//    vector <RADIALDATABLOCK> RadialData;
//}CAPPIFORMAT;
typedef struct STRUCT_PACKED
{
    vector <RADIALFORMAT> CappiData;
}CAPPIFORMAT;
///MAX产品格式****************************************************************
typedef struct STRUCT_PACKED
{
    RASTERFORMAT MAXData[3];
}MAXFORMAT;
///WER产品格式****************************************************************
typedef struct STRUCT_PACKED
{
    float ElevationAngle;
    int ScanTime;
    int CenterHeight;
    char Reserved[20];
}WERHEADERBLOCK;

typedef struct STRUCT_PACKED
{
    WERHEADERBLOCK WERHeader;
    RASTERFORMAT RasterData;
}WERDATABLOCK;

typedef struct STRUCT_PACKED
{
    vector<WERDATABLOCK> WERData;
}WERFORMAT;

typedef struct STRUCT_PACKED
{
    float Azimuth;              // °
    int BottomHeight;           // m
    int TopHeight;              // m
    int TopEdge;                // m
    int TopCenter;              // m
    int BottomCenter;           // m
    int BottomEdge;             // m
}MLDATABLOCK;

typedef struct STRUCT_PACKED
{
    int MLDataNumber;
    vector<MLDATABLOCK> MLData;
}MLFORMAT;
///VAD产品****************************************************************
typedef struct STRUCT_PACKED
{
    float Elevation;
    int Height;
    int SlantRange;
    int FitValid;
    float P0;
    float P1;
    float P2;
    float WindDirection;
    float WindSpeed;
    float RMS;
    float NyquistVelocity;
    int NumberDataPoints;
    char Reserved[16];
}VADHEADERBLOCK;

typedef struct STRUCT_PACKED
{
    float AzimuthData;
    float VelocityData;
    float ReflecitivityData;
}VADDATABLOCK;

typedef struct STRUCT_PACKED
{
    VADHEADERBLOCK VADHeader;
    vector <VADDATABLOCK> VADData;
}VADPROBLOCK;

typedef struct STRUCT_PACKED
{
    vector<VADPROBLOCK> VADProblock;
}VADFORMAT;
///VWP产品格式****************************************************************
typedef struct STRUCT_PACKED
{
    float NyquistVelcity;
    int NumberofVolumes;
    float MaximumWindSpeed;
    float MaximumWindDirection;
    float MaximumWindHeight;
    char Reserved[12];
}VWPHEADERBLOCK;

typedef struct STRUCT_PACKED
{
    int VolumeStartTime;
    int Height;
    int FitValid;
    float WindDirection;
    float WindSpeed;
    float RMS;
    char Reserved[8];
}VWPDATABLOCK;

typedef struct STRUCT_PACKED
{
    VWPHEADERBLOCK VWPHeader;
    vector<VWPDATABLOCK> VWPData;
}VWPFORMAT;
///SWP产品格式****************************************************************
typedef struct STRUCT_PACKED
{
    int Range;
    float Azimuth;
    int SWP;
}SWPDATABLOCK;

typedef struct STRUCT_PACKED
{
    int NumberofSWP;
    vector<SWPDATABLOCK> SWPData;
}SWPFORMAT;
///STP产品格式****************************************************************
typedef struct STRUCT_PACKED
{
    float MeanBias;
    float ErrorVariance;
    int ProductAdjusted;
}QPEBIASDATABLOCK;

typedef struct STRUCT_PACKED
{
    float MINTHRFL;//最小反射率门限,dbz
    float MAXTHRFL;//最大反射率门限,dbz
    float REFLECTLT;//反射率测试下限,dbz
    int RNGTLTIN;//内侧检测距离,km
    int RNGTLTOUT;//外侧检测距离,km
    int MAXRNGBI;//双层扫描最大距离.km
    int MINARECHO;//最小降水面积,km^2
    int MINREFLAA;//最小区域平均反射率,dbz
    float MAXARPCT;//最大面积衰减比,%
    int CZM;//降水率累积系数
    float CZP;//降水率乘方系数
    float MINDBZRFL;//最小反射率门限,dbz
    float MAXDBZRFL;//最大反射率门限,dbz
    float MINRNGBI;//双层扫描最小距离,km
    int MAXSPDSTM;//最大风暴速度,m/s
    float THRMXTDIF;//最大扫描间隔,min // OHP
    int MINARTIMC;//最小降水面积,km^2
    float PRMTIMC1;//降水率变化率1,1/h
    float PRMTIMC2;//降水率变化率2,1/h
    int MXRATCHG;//回波区域变化最大比率,km^2/h
    int RNGCUTOFF;//边界效应截止范围,km
    float RNGCOEF1;//边界效应第1系数,dbr
    float RNGCOEF2;//边界效应第2系数
    float RNGCOEF3;//边界效应第3系数
    float MINPRATE;//最小降水率,mm/h
    float MAXPRATE;//最大降水率,mm/h
    int TIMRESTRT;//重启时间,min
    int MAXTIMINT;//最大插值时间,min
    int MINTIMPD;//累积最小时间,min // OHP
    int THOURLI;//小时累积外推极限,mm
    int ENTIMGAG;//雨量计结束时间,min
    int MAXPRDVAL;//体扫累积极限,mm
    int MAXHLYVAL;//小时累积最大值,mm
    int TIMBIEST;//降水调整时间,min
    int THRNSETS;//最小数据对
    float RESETBI;//偏差重置值
    float RESMSQER;//重置方差
    float MAXMSQER;//最大允许方差
    int THRTIMDIF;//雨量计时间差门限,min
    float MXTIMPROP;//最大重置时间,hour
    float SYSNOISE;//系统噪声
    float VARADJFAC;//方差调整因子
    float THGAGDISC;//雨量计摒弃门限
    int MAXGAGACC;//最大雨量计累积值,mm
    float THRRGACUM;//最小累积时间,min
}ADAPTATIONPARAMETERBLOCK;

///QPE产品格式***************************************************************
typedef struct STRUCT_PACKED
{
    RADIALFORMAT QPEData;
    QPEBIASDATABLOCK QPEBiasData;
    ADAPTATIONPARAMETERBLOCK AdaptationParameter;
}QPEFORMAT;
///THP/USP产品格式***************************************************************
typedef struct STRUCT_PACKED
{
    int ScanTime;//sec
    float MeanBias;//
    float ErrorVariance;
    int ProductAdjusted;
}HOURBIASBOLCK;

typedef struct STRUCT_PACKED
{
    int ContinueHours;//h
    vector <HOURBIASBOLCK> HourBiasBlock;
}THPBIASDATABLOCK;

typedef struct STRUCT_PACKED
{
    RADIALFORMAT THPData;
    THPBIASDATABLOCK THPBiasData;
}THPFORMAT;
///STORM_SCIT*****************************************************************************************************************************
typedef struct STRUCT_PACKED
{
    int NumOfStorm;
    int NumOfContinuousStorms;
    int NumOfComponents;
    float AverageSpeedOfStorms;//平均风暴速度，m/s
    float AverageDirectionOfStorm;//平均风暴方向，度
}STIHEADERBLOCK;

typedef struct STRUCT_PACKED
{
    float Azimuth;//风暴单体到雷达的方位，度
    int Range;//风暴单体到雷达的距离，米
    float Speed;//风暴单体的速度m/s
    float Direction;//风暴单体的方向，度
    int ForecastError;//预报错误，米
    int MeanForecastError;//平均预报错误、米
}STORMMOTIONBLOCK;

typedef struct STRUCT_PACKED
{
    float AzimithOfPosition;//风暴单体到雷达方位。度
    int RangeOfPosition;//方位单体到雷达的距离，米
    int VolumeTimeOfPosition;//径向数据采集时间
}STORMPOSITION;

typedef struct STRUCT_PACKED
{
    int NumOfPositions;//位置个数
    vector <STORMPOSITION> stormposition;
}STORMFORECASTBLOCK;

typedef struct STRUCT_PACKED
{
    int NumOfPositions;//位置个数
    vector <STORMPOSITION> stormposition;
}STORMHISTORYBLOCK;

typedef struct STRUCT_PACKED
{
    vector <STORMMOTIONBLOCK> stormmotionblock;
    vector <STORMFORECASTBLOCK> stormforecastblock;
    vector <STORMHISTORYBLOCK> stormhistoryblock;
}STORMTRACKINGINFOBLOCKS;

typedef struct STRUCT_PACKED
{
    int StormID;
    int StormType;//0——旧生，1——新生
    int NumOfVolumes;//体扫个数
    float Azimuth;//方位，度
    int Range;//距离，米
    int Height;//风暴高度，米
    float MaxRef;//
    int HeightOfMaxRef;//
    float VIL;//
    int NumOfComponents;
    int IndexToFirstComponent;
    int TopHeight;//米
    int IndexToTop;//风暴顶的风暴编号
    int BottomHeight;//米
    int IndexToBottom;//风暴底编号
}STORMATTRIBUTESBLOCK;

typedef struct STRUCT_PACKED
{
    double Mass;//风暴的质量
    double Xpos;//质心X坐标/km
    double Ypos;//质心Y坐标/km
    float speedOfX;//X speed
    float speedOfY;//Y speed mod by ht
}STORMOTHERATTRIBUTESBLOCK;

typedef struct STRUCT_PACKED
{
    int Height;//高度，米
    float MaxRef;//反射率因子
    int IndexToNextCompornt;//下一个风暴构成编号
}COMPONENTTABLEBLOCK;


typedef struct STRUCT_PACKED
{
    vector<STORMOTHERATTRIBUTESBLOCK> stormotherattributesblock;
    vector<STORMATTRIBUTESBLOCK> stormattributesblock;
    vector<COMPONENTTABLEBLOCK> compoenttableblock;
}STORMATTRIBUTESTABLEBLOCKS;

typedef struct STRUCT_PACKED
{
    int DEFDIREC;//默认风向，度
    float DEFSPEED;//默认风速，m/s
    int MAXVTIME;//最大体扫时间,minute
    int NPASTVOL;//历史体扫数
    float CORSPEED;//相关速度,m/s
    float SPEEDMIN;//最小速度,m/s
    int ALLOWERR;//允许误差,km
    int FRCINTVL;//预报间隔,minute
    int NUMFRCST;//预报个数
    int ERRINTVL;//误差间隔
}STORMTRACKINGADAPTATIONDATA;

typedef struct STRUCT_PACKED
{
    STIHEADERBLOCK stiheaderblock;
    STORMTRACKINGINFOBLOCKS stormtrackinginfoblock;
    STORMATTRIBUTESTABLEBLOCKS stormattributestableblocks;
    STORMTRACKINGADAPTATIONDATA stormtrackingadaptationdata;
}STIFORMAT;
///HI*****************************************************************************************************************************
typedef struct STRUCT_PACKED
{
    int HailID;
    float Azimuth;
    int Range;
    int PossibilityOfHail;
    int PossibilityOfSevereHail;
    float SizeOfHail;
    int RCMcode;
}HAILTABLE;

typedef struct STRUCT_PACKED
{
    float HT0MSL;//零度层高度 km 默认3.2
    float HT20MSL;//-20度层高度 km 默认6.1
    float HKECOF1;//动能系数 默认0.0005/0.084/10.0
    float HKECOF2;//动能系数 默认0.0005/0.084/10.0
    float HKECOF3;//动能系数 默认0.0005/0.084/10.0
    float POSHCOF;//强冰雹概率系数 默认29
    int   POSHOFS;//强冰雹概率偏置量 默认50
    float HSCOF;//冰雹尺寸系数 默认0.1
    float HSEXP;//冰雹尺寸指数 默认0.5
    int   LLHKEREF;//反射率下限 默认40
    int   ULHKEREF;//反射率上限 默认50
    int   RCMPRBL;//RCM冰雹概率门限 默认30
    float WTCOF;//报警门限系数 默认57.50
    int   MXHLRNG;//冰雹计算最大范围 km 默认230
    float POHHDTH1;//冰雹概率高度差 km 默认1.62/1.88/2.12/2.38/2.62
                                         //2.92/3.30/3.75/4.00/5.00

    float POHHDTH2;
    float POHHDTH3;
    float POHHDTH4;
    float POHHDTH5;
    float POHHDTH6;
    float POHHDTH7;
    float POHHDTH8;
    float POHHDTH9;
    float POHHDTH10;
    int   MRPOHTH;//最小反射率门限 默认45
    int   RCMPSTV;//RCM强冰雹概率门限 默认50
}ADAPTATIONDATA;

typedef struct STRUCT_PACKED
{
    int NumberOfHail;
    vector <HAILTABLE> HailTables;
    ADAPTATIONDATA AdaptationData;
}HIFORMAT;

///MESO*****************************************************************************************************************************
typedef struct STRUCT_PACKED
{
    int NumberOfStorms;
    int NumberOfMeso;
    int NumberOfFeatures;
}MESOGEADERBLOCK;

typedef struct STRUCT_PACKED
{
    int FeatureID;
    int StormID;
    float Azimuth;
    int Range;
    float Elevation;
    float AverageShear;
    int Height;
    int AzimuthalDiameter;
    int RadialDiameter;
    float AverageRotationalSpeed;
    float MaxRotationalSpeed;
    int Top;
    int Base;
    float BaseAzimuth;
    int BaseRange;
    float BaseElevation;
    float MaxTangentialShear;
}MESOTABLE;

typedef struct STRUCT_PACKED
{
    int FeatureID;
    int StormID;
    int FeatureType;
    float Azimuth;
    int Range;
    float Elevation;
    int Height;
    int AzimuthalDiameter;
    int RadialDiameter;
    float AverageShear;
    float MaximumShear;
    float AverageRotationalSpeed;
    float MaximumRotationalSpeed;
    int Top;
    int Base;
    float BaseAzimuth;
    int BaseRange;
    float BaseElevation;
}MESOFEATURETABLE;

typedef struct STRUCT_PACKED
{
    int NPVTHR;//特征向量个数门限
    float FHTHR;//特征高度
    float HMTHR;//高角动量门限
    float LMTHR;//低角动量门限
    float HSTHR;//高切变门限
    float LSTHR;//低切变门限
    float MRTHR;//直径比率上限
    float FMRTHR;//远比率上限
    float NRTHR;//近比率下限
    float FNRTHR;//远比率下限
    float RNGTHR;//距离门限
    float DISTHR;//最大径向差
    float AZTHR;//最大方位差

}MESOADAPTATIONDATA;

typedef struct STRUCT_PACKED
{
    int NPVTHR;//特征向量个数门限
    float FHTHR;//特征高度
    float HMTHR;//高角动量门限
    float LMTHR;//低角动量门限
    float HSTHR;//高切变门限
    float LSTHR;//低切变门限
    float MRTHR;//直径比率上限
    float FMRTHR;//远比率上限
    float NRTHR;//近比率下限
    float FNRTHR;//远比率下限
    float RNGTHR;//距离门限
    float DISTHR;//最大径向差
    float AZTHR;//最大方位差
    float MAXVIN;   //模式矢量最大入流速度
    float MINVOUT;  //模式矢量最小出流速度
    float MINVR;    //模式矢量旋转速度阈值
    float CORED;    //核区直径
    int NDCOUNT;    //无效值数量
    float NDRATIO;  //无效值占比
    int DROPCOUNT;  //速度值减小的点数
    float DROPVALUE;//速度值减小的阈值
    float DROPRATIO;//速度值减小点占比
}MESOPARAMS;

typedef struct STRUCT_PACKED
{
    MESOGEADERBLOCK mesoheaderblock;
    vector <MESOTABLE> mesotables;
    vector <MESOFEATURETABLE> mesofeaturetables;
    MESOADAPTATIONDATA mesoadaptationdata;
}MFORMAT;

///TVS*****************************************************************************************************************************
typedef struct STRUCT_PACKED
{
    int NumberOfTVS;
    int NumberOfETVS;
}TVSHEADERBLOCK;

typedef struct STRUCT_PACKED
{
    int StormID;
    int Type;                           // 1-TVS; 2-ETVS
    float Azimuth;                      // degree: 0-360
    int Range;                          // meter: 0-500000
    float Elevation;                    // degree: 0.00-20.00
    float LowLevelDeltaVelocity;        // m/s
    float AverageDeltaVelocity;         // m/s
    float MaximumDeltaVelocity;         // m/s
    int HeightOfMaximumDeltaVelocity;   // meter: 0-21000
    int Depth;                          // 深度, m
    int Base;                           // 回波底, m
    int Top;                            // 回波顶, m
    float MaximumShear;                 // 最大切变
    int HeightOfMaximumShear;           // 最大切变高度
}TVSTABLE;

typedef struct STRUCT_PACKED
{
    int MINREFL;                        // 最小反射率门限，dBZ，0
    int MINPVDV;                        // 相邻距离库速度差最小值，m/s，11
    int MAXPVRNG;                       // 模式向量允许的最大距离，km，100
    float MAXPVHT;                      // 模式向量允许的最大高度，km，10.0
    int MAXNUMPV;                       // 最大的模式向量个数，，2500
    int TH2DDV1;                        // 差分速度门限1，m/s，11
    int TH2DDV2;                        // 差分速度门限2，m/s，15
    int TH2DDV3;                        // 差分速度门限3，m/s，20
    int TH2DDV4;                        // 差分速度门限4，m/s，25
    int TH2DDV5;                        // 差分速度门限5，m/s，30
    int TH2DDV6;                        // 差分速度门限6，m/s，35
    int MIN1DP2D;                       // 识别二维特征要求的最小模式向量个数，，3
    float MAXPVRD;                      // 二维向量最大径向距离，km，0.5
    float MAXPVAD;                      // 二维向量最大方位角度，degree，1.5
    float MAX2DAR;                      // 二维特征最大比率，km/km，4.0
    float THCR1;                        // 搜索径向距离1，km，2.5
    float THCR2;                        // 搜索径向距离1，km，4.0
    int THCRR;                          // 搜索的径向距离门限，km，80
    int MAXNUM2D;                       // 二维特征最大个数，，600
    int MIN2DP3D;                       // 识别三维特征需要最少的二维特征数量，，3
    float MINTVSD;                      // 识别三维特征要求的最小深度，km，1.5
    int MINLLDV;                        // 识别三维特征要求的最小低层速度差，m/s，25
    int MINMTDV;                        // TVS要求的速度差最小值，m/s，36
    int MAXNUM3D;                       // 最大三维特征个数，，35
    int MAXNUMTV;                       // 最大TVS个数，，15
    int MAXNUMET;                       // 最大ETVS个数，，0
    float MINTVSBH;                     // TVS最小底高度，km，0.6
    float MINTVSBE;                     // 最小TVS仰角，degree，1.0
    float MINADVHT;                     // 最小平均速度差的高度，km，3.0
    float MAXTSTMD;                     // 最大风暴关联距离，km，20.0
}TVSADAPTATIONDATA;

typedef struct STRUCT_PACKED
{
    TVSHEADERBLOCK tvsheaderblock;      // 头模块
    vector <TVSTABLE> tvstables;        // TVS表#1～#N
    TVSADAPTATIONDATA tvsadaptationdata;// 适配数据
}TVSFORMAT;
///storm****************************************************************************************************************
typedef struct STRUCT_PACKED
{
    int NumberOfStorms; //风暴个数
}SSHEADERBLOCK;

typedef struct STRUCT_PACKED
{
    int StormID;
    float Azimuth;//方位角°
    int Range;//距离，m
    int Base;//回波底m
    int Top;//回波顶m
    float VIL;//kg/m**2
    float MaxRef; //dBZ
    int HeightOfMaxRef;//m
}SSTABLE;

typedef struct STRUCT_PACKED
{
    int StormID;
    int NumberOfVolumes;//历史体扫个数
    int VolumeTime;//UCTfrom1970,秒
    int Height;
    int Base;
    int Top;
    int VIL;
    int MaxRef;
    int HeightOfMaxRef;
    int PossibilityOfHail;
    int PossibilityOfSevereHail;
}CELLTRENDDATA;

typedef struct STRUCT_PACKED
{
    int REFLECTH1;//反射率因子门限
    int REFLECTH2;
    int REFLECTH3;
    int REFLECTH4;
    int REFLECTH5;
    int REFLECTH6;
    int REFLECTH7;
    int NREFLEVL;//反射率因子阈值数量
    int NUMAVGBN;//平均库数
    int SEGRNGMX;//段搜索距离km
    float MCOEFCTR;//系数因子
    float MULTFCTR;//倍数因子
    float MWGTFCTR;//权重因子
    float SEGLENTH1;//段长阈值
    float SEGLENTH2;
    float SEGLENTH3;
    float SEGLENTH4;
    float SEGLENTH5;
    float SEGLENTH6;
    float SEGLENTH7;
    int DRREFDFF;//丢弃反射率因子差
    int NDROPBIN;//丢弃库数
    int NUMSEGMX;//仰角段数
    int RADSEGMX;//径向段数
}SEGMENTADAPTATIONDATA;

typedef struct STRUCT_PACKED
{
    float CMPARETH1;//风暴组1面积
    float CMPARETH2;
    float CMPARETH3;
    float CMPARETH4;
    float CMPARETH5;
    float CMPARETH6;
    float CMPARETH7;
    float RADIUSTH1;//搜索半径1
    float RADIUSTH2;
    float RADIUSTH3;
    int STMVILMX;//风暴单体VIL最大值
    int MXDETSTM;//最大单体个数
    int OVLAPADJ;//邻近重叠距离
    float AZMDLTHR;//方位角差门限
    float DEPTHDEL;//删除深度km
    float HORIZDEL;//删除距离km
    float ELVMERGE;//合并仰角du
    float HGTMERGE;//合并高度km
    float HRZMERGE;//合并距离km
    int NBRSEGMN;//最少段数
    int NUMCMPMX;//最多组数
    int MXPOTCMP;//最多可能组数
    int NUMSTMMX;//最多单体数
}CENTROIDSADAPTATIONDATA;

typedef struct STRUCT_PACKED
{
    SSHEADERBLOCK ssheaderblock;
    vector <SSTABLE> sstable;
    vector <CELLTRENDDATA> celltrenddata;
    SEGMENTADAPTATIONDATA segmentadaptationdata;
    CENTROIDSADAPTATIONDATA centroidsadaptationdata;
    STORMTRACKINGADAPTATIONDATA stormtrackingadaptationdata;
}SSFORMAT;

///Gust Front产品***********************************************************
typedef struct STRUCT_PACKED
{
    int longitude;          // 经度，单位:0.01°
    int latitude;           // 纬度，单位:0.01°
}POINTINFO;

typedef struct STRUCT_PACKED
{
    int PointsCount;        // 点集中包含的点数
    std::vector<POINTINFO>  singleGF;
}GFTABLE;

typedef struct STRUCT_PACKED
{
    int NumberOfGustFronts; // 阵风锋个数
    std::vector<GFTABLE>  GFTables;
}GFFORMAT;

///MARC特征**********************************************************
typedef struct STRUCT_PACKED
{
    int RVDLECTH1;      // 径向散度门限
    int RVDLECTH2;
    int RVDLECTH3;
    int RVDLECTH4;
    int RVDLECTH5;
    int RVDLECTH6;
    int RVDLECTH7;
    int NRVDLEVL;       // 径向散度阈值数量
    int NUMAVGBN;       // 平均库数
    int SEGRNGMX;       // 段搜索距离km
    float MCOEFCTR;     // 系数因子
    float MULTFCTR;     // 倍数因子
    float MWGTFCTR;     // 权重因子
    float SEGLENTH1;    // 段长阈值
    float SEGLENTH2;
    float SEGLENTH3;
    float SEGLENTH4;
    float SEGLENTH5;
    float SEGLENTH6;
    float SEGLENTH7;
    int DRRVDDFF;       // 丢弃径向散度差
    int NDROPBIN;       // 丢弃库数
    int NUMSEGMX;       // 仰角段数
    int RADSEGMX;       // 径向段数
}MARCSEGMENTADAPTATIONDATA;

typedef struct STRUCT_PACKED
{
    float CMPARETH1;    // 面积1
    float CMPARETH2;
    float CMPARETH3;
    float CMPARETH4;
    float CMPARETH5;
    float CMPARETH6;
    float CMPARETH7;
    float RADIUSTH1;    // 搜索半径1
    float RADIUSTH2;
    float RADIUSTH3;
    int STMVILMX;       // VIL最大值
    int MXDETSTM;       // 最大单体个数
    int OVLAPADJ;       // 邻近重叠距离
    float AZMDLTHR;     // 方位角差门限
    float DEPTHDEL;     // 删除深度km
    float MINRVDDEL;    // 删除最小径向散度
    float SSDISDEL;     // 删除远离风暴距离km
    float HORIZDEL;     // 删除距离km
    float ELVMERGE;     // 合并仰角du
    float HGTMERGE;     // 合并高度km
    float HRZMERGE;     // 合并距离km
    int NBRSEGMN;       // 最少段数
    int NUMCMPMX;       // 最多组数
    int MXPOTCMP;       // 最多可能组数
    int NUMSTMMX;       // 最多单体数
    int BASEHEIGHT;     // 质心底高阈值
    int TOPHEIGHT;      // 质心顶高阈值
}MARCCENTROIDSADAPTATIONDATA;

///Downburst 产品****************************************************
typedef struct STRUCT_PACKED
{
    int NumberOfStorms;     // 风暴个数
    int NumberOfDownbursts; // 下击暴流个数
}DBHEADERBLOCK;

typedef struct STRUCT_PACKED
{
    int DownburstID;        // 下击暴流ID
    int StormID;            // 距离最近的风暴ID
    float Azimuth;          // 方位角，度
    int Range;              // 距离，m
    float Elevation;        // 仰角，度
    int Height;             // 高度，m
    int AzimuthalDiameter;  // 方位直径，m
    int RadialDiameter;     // 径向直径，m
    int Top;                // 回波顶高，m
    int Base;               // 回波底高，m
    float VIL;              // kg/m**2
    float AverageMARC;      // 平均中层径向辐合
    float IntegrationMARC;  // 中层径向辐合垂直积分
    float MaxMARC;          // 中层径向辐合最大值
    int HeightOfMaxMARC;    // 中层径向辐合最大值高度，m
    float MaxVelocity;      // 地面最大风速估计
}DBTABLE;

typedef struct STRUCT_PACKED
{
    DBHEADERBLOCK dbheaderblock;
    vector <DBTABLE> dbtable;
    MARCSEGMENTADAPTATIONDATA marcsegmentadaptation;
    MARCCENTROIDSADAPTATIONDATA marccentroidsadaptation;
    SEGMENTADAPTATIONDATA stormsegmentadaptation;
    CENTROIDSADAPTATIONDATA stormacentroidsadaptation;
}DBFORMAT;

///Rainstorm产品格式*************************************************
typedef struct STRUCT_PACKED
{
    int NumberOfRainstorms;     //暴雨个数
    int Confidence;             //置信度: %
}RSHEADERBLOCK;

typedef struct STRUCT_PACKED
{
    int RainstormID;
    float Azimuth;      //方位角: °
    int Range;          //距离: m
    float Area;         //强降水面积: km^2
    float MaxPrecip;    //最大降水量: mm
}RSTABLE;

typedef struct STRUCT_PACKED
{
    RSHEADERBLOCK rsheaderblock;
    vector<RSTABLE> rstable;
    RADIALFORMAT QPEData;
    QPEBIASDATABLOCK QPEBiasData;
    ADAPTATIONPARAMETERBLOCK AdaptationParameter;
}RSFORMAT;

///FHC产品***********************************************************
typedef enum
{
    FHC_RA = 0,      //2 小雨/中雨
    FHC_HR = 1,      //3 大雨
    FHC_RH = 2,     //12 雨夹雹
    FHC_BD = 3,      //4 大滴
    FHC_BS = 4,      //1 生物回波
    FHC_GCAP = 5,    //0 地物/超折射
    FHC_DS = 6,      //6 干雪
    FHC_WS = 7,      //7 湿雪
    FHC_CR = 8,      //8 冰晶
    FHC_GR = 9,      //9 散
}FHC_TYPE;//zhangguifu

typedef enum
{
    FHC_GCAP_ZQ = 5,  // 地物
    FHC_RA_ZQ = 0,    // 小雨
    FHC_HR_ZQ = 1,    // 大雨
    FHC_BD_ZQ = 3,    // 大雨滴
    FHC_SW_ZQ = 10,    // 过冷水
    FHC_DS_ZQ = 6,    // 干雪
    FHC_WS_ZQ = 7,    // 湿雪
    FHC_CR_ZQ = 8,    // 冰晶
    FHC_SH_ZQ = 2,   // 小冰雹
    FHC_LH_ZQ = 2,   // 大冰雹
    FHC_RH_ZQ = 2,  // 雨夹雹
}FHC_TYPE_ZQ;//zhaoqin

typedef struct STRUCT_PACKED
{
    vector <RADIALFORMAT> HclData;
}HCLFORMAT;
///alert******************************************************************************************************************
typedef struct
{
    float ILTLAT;
    float ILTLON;
    float IRBLAT;
    float IRBLON;
    float OLTLAT;
    float OLTLON;
    float ORBLAT;
    float ORBLON;
    float DBZ1;
    float RATE1;
    float RATEX1;
    float DBZ2;
    float RATE2;
    float RATEX2;
    float DBZ3;
    float RATE3;
    float RATEX3;
    float DBZ4;
    float RATE4;
    float RATEX4;
    int RowResolution;
    int ColumnResolution;
}ALERTPARAMETERS;

///common******************************************************************************************************************
typedef struct STRUCT_PACKED
{
    COMMONBLOCK commonBlock;
    COMMONBLOCKPAR commonBlockPAR;
    PRODUCTHEADERBLOCK productheader;
    void* productdatapoint;
}WRADPRODATA_PARA_IN;

typedef struct STRUCT_PACKED
{
    COMMONBLOCK commonBlock;
    COMMONBLOCKPAR commonBlockPAR;
    PRODUCTHEADERBLOCK productheader;
    vector<char> dataBlock;
}WRADPRODATA;
///flow**********************************
typedef struct STRUCT_PACKED
{
    float heightlevel;
    float time_total;
    float time_dt;
    s_Pro_Grid::RadarProduct m_iCAPPIproduct;
}flow_ini;

typedef struct
{
    vector<WRADPRODATA> m_RadarPro_exp_out;
    s_Pro_Grid::RadarProduct m_RadarPro_out_uv;
}m_RadarPro_struct;

#ifdef __GNUC__
#else
#   pragma pack(pop)
#endif
