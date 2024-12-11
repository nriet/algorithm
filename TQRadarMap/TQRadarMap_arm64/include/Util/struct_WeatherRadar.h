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
* File:struct_WeatherRadar.h
* Author:Nriet
* time 2023-05-24
*************************************************************************/
#pragma once

#include <vector>

#define PREFILLVALUE -32768
#define PREFILLVALUE_FLOAT -999999.0
#define PREFILLVALUE_INT -2147483648
#define PREFILLVALUE_SHORT -32768
#define PREFILLVALUE_CHAR -128
#define INVALID_BT 0  //Below Threshold
#define INVALID_RF 1  //Range Folding
#define INVALID_UA 2  //Unscanned Area(such as elevtromagnetic blanking area)
#define INVALID_UK 3  //Unknown data
#define INVALID_RSV 4 //Reserved


#ifdef STRUCT_PACKED
    #undef STRUCT_PACKED
#endif

#ifdef __GNUC__
    #define STRUCT_PACKED __attribute__((packed))
#else
    #pragma pack(push,1)
    #define STRUCT_PACKED
#endif

typedef	struct STRUCT_PACKED
{
    int MagicNumber;                 //魔术字，用来指示雷达数据文件 nowtime 0x4D545352 history 0x4D545353 realtimeradial 0x4D545350 monitoring 0x4D545357
    unsigned short MajorVersion;              //主版本号
    unsigned short MinorVersion;              //次版本号
    int GenericType;                 //文件类型，1--基数据文件；2--气象产品文件
    int ProductType;                 //产品类型，文件类型为1时此字段无效（1~100）
    char Reserved[16];               //保留字节
} GENERICHEADER;

typedef struct STRUCT_PACKED
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
    char Reserved[54];               //保留字节
} SITECONFIG;

typedef enum
{
    RTYPE_SA    = 1,
    RTYPE_SB    = 2,
    RTYPE_SC    = 3,
    RTYPE_SAD   = 4,
    RTYPE_CA    = 33,
    RTYPE_CB    = 34,
    RTYPE_CC    = 35,
    RTYPE_CCJ   = 36,
    RTYPE_CD    = 37,
    RTYPE_X     = 101,
    RTYPE_SPA   = 102,              // 恩瑞特S相控阵
} RADAR_TYPE;

typedef struct STRUCT_PACKED
{
    char SiteCode[8];                //站号，如Z9010(ASCII)
    char SiteName[32];               //站点名称，如Beijing_Z9010(ASCII)
    float Latitude;                  //雷达天线所在纬度(度，-90.000000~90.000000)
    float Longitude;                 //雷达天线所在经度(度，-180.000000~180.000000)
    int AntennaHeight;               //天线高度，天线馈源水平时海波高度(米，0~9000)
    int GroundHeight;                //地面高度，雷达塔楼地面海波高度(米，0~9000)
    float Frequency;                 //工作频率(MHz，1.00~999000.00)
    int AntennaType;                 //天线类型，1-波导裂缝天线 2-微带天线
    int TRNumber;                    //收发单元数量 1~4096 高字节（前2）为发单数量，低字节（后2）为收单数量
    int RdaVersion;                  //RDA(雷达数据采集系统)版本号
    short RadarType;                 //雷达类型，7-SPAR 8-SPARD 43-CPAR 44-CPARD 69-XPAR 70-XPARD
    char Reserved[54];               //保留字节
} SITECONFIGPAR;

typedef enum
{
    RTYPE_SPAR    = 7,
    RTYPE_SPARD   = 8,
    RTYPE_CPAR    = 43,
    RTYPE_CPARD   = 44,
    RTYPE_XPAR    = 69,
    RTYPE_XPARD   = 70,
} RADAR_TYPE_PAR_KJC;

typedef struct STRUCT_PACKED
{
    char TaskName[32];               //任务名称，如VCP21
    char TaskDescription[128];       //任务描述
    int PolarizationType;            //极化方式，1-水平极化，2-垂直极化，3-水平/垂直同时，4-水平/垂直交替
    int ScanType;                    //扫描任务类型，0-体扫，1-单层PPI，2-单层RHI，3-单层扇扫，4-扇体扫，5-多层RHI，6-手工扫描
    int PulseWidth;                  //脉冲宽度(纳秒，1~10000)
    int ScanStartTime;               //扫描开始时间(秒，0~)UTC标准时间计数，1970.1.1日0时为起始计数基准点
    int CutNumber;                   //扫描层数(1~256)
    float HorizontalNoise;           //水平通道噪声(dBm，-100.00~0.00)
    float VerticalNoise;             //垂直通道噪声(dBm，-100.00~0.00)
    float HorizontalCalibration;     //水平通道标定值(dB，0.00~200.00)
    float VerticalCalibration;       //垂直通道标定值(dB，0.00~200.00)
    float HorizontalNoiseTemperature;//水平通道噪声温度(K，0.00~800.00)
    float VerticalNoiseTemperature;  //垂直通道噪声温度(K，0.00~800.00)
    float ZDRCalibration;            //ZDR标定偏差(dB，-10.00~10.00)
    float PHIDPCalibration;          //差分相移标定偏差(度，-180.00~180.00)
    float LDRCalibration;            //系统LDR标定偏差(dB，-60~0)
    float ZDRCalibrationInside;
    float PHIDPCalibrationInside;
    int BlindBinNum;
    float LGTZDRA;
    float LGTZDRB;
    float LGTAZ;                     //第一根避雷针方位角
    int BinDilution;                 //库抽稀
    int AzDilution;                  //方位角抽稀
    char Reserved[8];               //保留字节
} TASKCONFIG;

typedef struct STRUCT_PACKED
{
    char TaskName[32];               //任务名称，如VCP21
    char TaskDescription[128];       //任务描述
    int PolarizationType;            //极化方式，1-水平极化，2-垂直极化，3-水平/垂直同时，4-水平/垂直交替
    int ScanType;                    //扫描任务类型，0-体扫，1-单层PPI，2-单层RHI，3-单层扇扫，4-扇体扫，5-多层RHI，6-手工扫描
    int ScanBeamNumber;              //发射波束数目 1~256 扫描配置中的发射波束数量
    int CutNumber;                   //接收仰角数目 1~256
    int RayOrder;                    //0~1 0-按径向采集时间排序  1-按先方位后俯仰方式排序
    long long ScanStartTime;         //扫描开始时间(秒，0~)UTC标准时间计数，1970.1.1日0时为起始计数基准点
    int BinDilution;                 //库抽稀
    int AzDilution;                  //方位角抽稀
    char Reserved[60];               //保留字节
} TASKCONFIGPAR;

typedef struct STRUCT_PACKED
{
    int SubPulseStrategy;         //
    int SubPulseModulation;
    float SubPulseFrequency;
    float SubPulseBandWidth;
    int SubPulseWidth;
    float HorizontalNoise;
    float VerticalNoise;
    float HorizontalCalibration;
    float VerticalCalibration;
    float HorizontalNoiseTemperature;
    float VerticalNoiseTemperature;
    float ZDRCalibration;
    float PHIDPCalibration;
    float LDRCalibration;
    short PulsePoints;
    char Reserved[70];
} SUBPULSECONFIGPAR;

typedef struct STRUCT_PACKED
{
    int BeamIndex;                 //扫描波束编号 1~32 按扫描波束依次编号
    int BeamType;                 //扫描波束类型 1~3 1-宽波束 2-窄波束 3-异频多波束（新增）
    int SubPluseNumber;            //子脉冲数量 1~4  主工作脉冲和补盲子脉冲数量总和
    float TxBeamDirection;         //发射波束中心指向  -2.00~90.00 （Degree）发射波束中心的俯仰角指向
    float TxBeamWidth_H;           //发射波束水平宽度（Degree）
    float TxBeamWidth_V;           //发射波束垂直宽度（Degree）
    float TxBeamGain;              //发射波束增益（dB）
    char Reserved[100];            //保留字段
    SUBPULSECONFIGPAR SubPulseConfig[10]; //子脉冲参数块
} BEAMCONFIGPAR;

typedef struct STRUCT_PACKED
{
    int ProcessMode;                 //处理模式，1-PPP，2-FFT
    int WaveForm;                    //波形类别，0-CS连续监测
    //        1-CD连续多普勒
    //        2-CDX多普勒扩展
    //        3-RxTest
    //        4-BATCH批模式
    //        5-Dual PRF双PRF
    //        6-Staggered PRF 参差PRF
    float PRF1;                      //脉冲重复频率1(Hz，1~3000)
    float PRF2;                      //脉冲重复频率2(Hz，1~3000)
    int DealiasingMode;              //速度退模糊方法, 1-单PRF,2-双PRF3:2模式，3-双PRF4:3模式，4-双PRF5:4模式
    float Azimuth;                   //RHI模式的方位角(度，0.00~360.00)
    float Elevation;                 //PPI模式的俯仰角(度，-2.00~90.00)
    float StartAngle;                //起始角度，PPI扇扫的起始方位角，或RHI模式的高限仰角(度，-10.00~360.00)
    float EndAngle;                  //结束角度，PPI扇扫的结束方位角，或RHI模式的低限仰角(度，-10.00~360.00)
    float AngularResolution;         //角度分辨率，径向数据的角度分辨率，仅用于PPI扫描模式(度，0.00~2.00)
    float ScanSpeed;                 //扫描速度，PPI扫描的方位转速，或RHI扫描的俯仰转速(度，0.00~36.00)
    int LogResolution;               //强度数据距离分辨率(m,1~5000)
    int DopplerResolution;            //多普勒距离分辨率(m,1~5000)
    int MaximumRange1;               //PRF1的最大可探测距离(m, 1~500000)
    int MaximumRange2;               //PRF2的最大可探测距离(m, 1~500000)
    int StartRange;                  //数据探测起始距离(m, 1~500000)
    int Sample1;                     //PRF1的采样个数(2~512)
    int Sample2;                     //PRF2的采样个数(2~512)
    int PhaseMode;                   //相位编码模式，1-固定相位，2-随机相位，3-SZ编码
    float AtmosphericLoss;           //大气衰减(dB/km,0.000000~10.000000)
    float NyquistSpeed;              //最大不模糊速度(m/s，0~100)
    long long MomentsMask;                //数据类型掩码，0-不允许获取数据，1-允许获取数据
    long long MomentsSizeMask;            //数据大小掩码，0-1个字节，1-2个字节
    int MiscFilterMask;              //滤波设置掩码，0-未应用，1-应用
    float SQIThreshold;              //SQI门限(dB，0.00~1.00)
    float SIGThreshold;              //SIG门限(dB，0.00~20.00)
    float CSRThreshold;              //CSR门限(dB，0.00~100.00)
    float LOGThreshold;              //LOG门限(dB，0.00~20.00)
    float CPAThreshold;              //CPA门限(0.00~100.00)
    float PMIThreshold;              //PMI门限(0.00~1.00)
    float DPLOGThreshold;            //DPLOG门限(0.00~1.00)
    char ThresholdsReserved[4];      //阈值门限保留字段
    int dBTMask;                     //dBT质控掩码，0-未应用，1-应用
    int dBZMask;                     //dBZ质控掩码，0-未应用，1-应用
    int VelocityMask;                //速度质控掩码，0-未应用，1-应用
    int SpectrumWidthMask;           //谱宽质控掩码，0-未应用，1-应用
    int DPMask;                      //偏振量质控掩码，0-未应用，1-应用
    char MaskReserved[12];           //质控掩码保留字节
    int ScanSync;                    //扫描同步标志
    int Direction;                   //天线运行方向，1-顺时针，2-逆时针
    short GroundClutterClassifierType;//地物杂波图类型，1-所有数据不滤波，2-全程滤波，3-使用实时动态滤波图，4-使用静态滤波图
    short GroundClutterFilterType;   //底物滤波类型，0-不滤波，1-频域自适应滤波，2-固定宽带频域滤波，3-可变宽带频域滤波器，4-可变最小方差频域滤波器，5-IIR时域滤波
    short GroundClutterFilterNotchWidth;//地物滤波宽度(0.1m/s，0.1~10.0)
    short GroundClutterFilterWindow; //滤波窗口类型，0-矩形窗，1-汉明窗，2-blackman窗，3-自适应窗口，4-无
    char Reserved[72];              //保留字段
} CUTCONFIG;

typedef struct STRUCT_PACKED
{
    short CutIndex;              // 扫描层索引 1~256 基数据仰角编号
    short TxBeamIndex;           //发射波束索引 1~256 对应的发射波束索引
    float RxBeamElevation;       //接受波束指向 -2.00~90.00 PPI模式的俯仰角
    float TxBeamGain;            //发射波束增益 在本接收方向上，发射波束的增益
    float RxBeamWidth_H;         //接收波束水平宽度
    float RxBeamWidth_V;         //接收波束垂直宽度
    float RxBeamGain;           //接收波束增益
    int ProcessMode;            //处理模式  1~2 1-PPP 2-FFT
    int WaveForm;               //波形类别 0~6 0-CS连续监测 1-CD连续多普勒 2-CDX多普勒扩展 3-Tx Test 4-BATCH批模式  5-Dual PRF 6-Staggered PRT 参差PRT
    float N1PRF1;               //第一组脉冲重复频率1 1~10000Hz 对于Batch、双PRF和参差PRT模式，表示高PRF值，对其他单PRF模式，表示唯一的PRF值
    float N1PRF2;               //第一组脉冲重复频率2 1~10000Hz 对于Batch、双PRF和参差PRT模式，表示低PRF值，对其他单PRF模式，无效
    float N2PRF1;               //第二组脉冲重复频率1 1~10000Hz 对于Batch、双PRF和参差PRT模式，表示高PRF值，对其他单PRF模式，表示唯一的PRF值
    float N2PRF2;              //第二组脉冲重复频率2 1~10000Hz 对于Batch、双PRF和参差PRT模式，表示低PRF值，对其他单PRF模式，无效
    int DealiasingMode;        //速度退模糊方法 1~4 1-单PRF 2-双PRF3:2模式 3-双PRF4:3模式 4-双PRF5:4模式
    float Azimuth;             //方位角 0.00~360.00（degree）
    float StartAngle;          //起始角度 -10.00~360.00（degree）
    float EndAngle;            //结束角度 -10.00~360.00（degree）
    float AngularResolution;    //角度分辨率 0.00~2.00 径向数据的角度分辨率，仅用于PPI扫描模式
    float ScanSpeed;            //扫描速度 0.00~100.00 PPI扫描的方位转速，或者RHI扫描的俯仰转速
    float LogResolution;        //强度分辨率 1~5000（meter）强度数据的距离分辨率，支持浮点分辨率
    float DopplerResolution;    //多普勒分辨率 1~5000（meter）多普勒数据的距离分辨率，支持浮点分辨率
    int MaximumRange1;          //最大距离1 1~500000（m）对应脉冲重复频率1的最大可探测距离
    int MaximumRange2;           //最大距离2  1~500000（m）对应脉冲重复频率2的最大可探测距离
    int StartRange;             //起始距离 1~500000（m）数据探测起始距离
    int Sample1;                //采用个数1 2~512 对应于脉冲重复频率1的采样个数
    int Sample2;                //采样个数2 2~512 对应于脉冲重复频率2的采样个数
    int PhaseMode;              //相位编码模式 1~3 1-固定相位 2-随机相位 3-SZ编码
    float AtmosphericLoss;      //大气衰减  0.000000~10.000000 （db/Km）双程大气衰减值，精度为小数点后保留6位
    float NyquistSpeed;         //最大不模糊速度 0~100 理论最大不模糊速度
    long long MomentsMask;           //数据类型掩码 0~0xFFFFFFFFFFFFFFFF 以掩码的形式表示当前允许获取的数据类型，其中0-不允许获取数据 1-允许获取数据
    long long MomentsSizeMask;       //数据大小掩码 0~0xFFFFFFFFFFFFFFFF 以掩码的形式表示每种数据类型字节数，其中0-1个字节 1-2个字节
    int MiscFilterMask;         //滤波设置掩码 0-未应用 1-应用
    float SQIThreshold;
    float SIGThreshold;
    float CSRThreshold;
    float LOGThreshold;
    float CPAThreshold;
    float PMIThreshold;
    float DPLOGThreshold;
    char ThresholdsReserved[4];  //门限保留字段
    int dBTMask;                 //dBT数据使用的质控门限掩码，其中0-未应用 1-应用
    int dBZMask;                //dBZ数据使用的质控门限掩码，其中0-未应用 1-应用
    int VelocityMask;            //速度数据使用的质控门限掩码，其中0-未应用 1-应用
    int SpectrumWidthMask;       //谱宽数据使用的质控门限掩码，其中0-未应用 1-应用
    int DPMask;                  //偏振量数据使用的质控门限掩码，其中0-未应用 1-应用
    char MaskReserved[12];       //保留，用于标识质控方法
    char Reserved[4];
    int Direction;               //天线运行方向 1~2 仅对PPI模式有效 1-顺时针 2-逆时针
    short GroundClutterClassifierType;  //地物杂波图类型 1~4 1-所有数据不滤波 2-全程滤波 3-使用实时动态滤波图 4-使用静态滤波图
    short GroundClutterFilterType;      //地物滤波类型  0~5  0-不滤波 1-频域自适应滤波 2-固定宽带频域滤波器 3-可变宽带频域滤波器 4-可变最小方差频域滤波器 5-IIR时域滤波器
    short GroundClutterFilterNotchWidth;//地物滤波宽度
    short GroundClutterFilterWindow;   // 地物滤波窗口类型 0~4 0-矩阵窗 1-汉明窗 2-blackman窗 3-自适应窗口 4-无
    char Reserved2[44];           //保留字段
} CUTCONFIGPAR;

typedef struct
{
    GENERICHEADER genericheader;     //通用头
    SITECONFIG siteconfig;           //站点配置
    TASKCONFIG taskconfig;           //任务配置
    std::vector<CUTCONFIG> cutconfig;     //扫描配置
} COMMONBLOCK;

typedef struct
{
    GENERICHEADER genericheader;     //通用头
    SITECONFIGPAR siteconfig;           //站点配置
    TASKCONFIGPAR taskconfig;           //任务配置
    std::vector<BEAMCONFIGPAR> beamconfig;     //扫描配置
    std::vector<CUTCONFIGPAR> cutconfig;     //扫描配置
} COMMONBLOCKPAR;

typedef struct STRUCT_PACKED
{
    int RadialState;                 //径向数据状态
    //0-仰角开始
    //1-中间数据
    //2-仰角结束
    //3-体扫开始
    //4-体扫结束
    //5-RHI开始
    //6-RHI结束
    int SpotBlank;                   //消隐标志，0-正常，1-消隐
    int SequenceNumber;              //序号，每个体扫径向从1计数(1~65536)
    int RadialNumber;                //径向数，每个扫描从1计数(1~1000)??
    int ElevationNumber;             //仰角编号(1~50)
    float Azimuth;                   //方位角(度，0.00~360.00)
    float Elevation;                 //仰角(度，-2.00~90.00)
    int Seconds;                     //秒
    int Microseconds;                //微秒
    int LengthOfData;                //数据长度，仅本径向数据块所占用长度
    int MomentNumber;                //数据类别数量(1~64)
    char Reserved0[2];
    short HorizontalEstimatedNoise;   //径向的水平通道估计噪声 0~20000（db）编码为实际噪声的-100倍
    short VerticalEstimatedNoise;    //径向的垂直通道估计噪声 0~20000（db）编码为实际噪声的-100倍
    char Reserved[14];               //保留字段
} RADIALHEADER;

typedef struct STRUCT_PACKED
{
    int RadialState;                 //径向数据状态
    //0-仰角开始
    //1-中间数据
    //2-仰角结束
    //3-体扫开始
    //4-体扫结束
    //5-RHI开始
    //6-RHI结束
    int SpotBlank;                   //消隐标志，0-正常，1-消隐
    int SequenceNumber;              //序号，每个体扫径向从1计数(1~65536)
    int RadialNumber;                //径向数，每个扫描从1计数(1~1000)??
    int ElevationNumber;             //仰角编号(1~50)
    float Azimuth;                   //方位角(度，0.00~360.00)
    float Elevation;                 //仰角(度，-2.00~90.00)
    long long Seconds;                     //秒
    int Microseconds;                //微秒
    int LengthOfData;                //数据长度，仅本径向数据块所占用长度
    int MomentNumber;                //数据类别数量(1~64)
    short ScanBeamIndex;             //波束编号 1~32
    short HorizontalEstimatedNoise;   //径向的水平通道估计噪声 0~20000（db）编码为实际噪声的-100倍
    short VerticalEstimatedNoise;    //径向的垂直通道估计噪声 0~20000（db）编码为实际噪声的-100倍
    unsigned int PRFFlag;            //重频标志   11-N1 PRF #1 、12-N1 PRF #2、 21-N2 PRF #1 、22-N2 PRF #2
    char Reserved[70];               //保留字段
} RADIALHEADERPAR;

typedef struct STRUCT_PACKED
{
    int DataType;                    //数据类型(1~64)
    //0-Reserved保留
    //1-滤波前反射率dBT
    //2-滤波后反射率dBZ
    //3-径向速度V
    //4-谱宽W
    //5-信号质量指数SQI
    //6-杂波相位一致性CPA
    //7-差分反射率ZDR
    //8-退偏振比LDR
    //9-协相关系数CC
    //10-差分相移fDP
    //11-差分相移率KDP
    //12-杂波可能性CP
    //13-Reserved保留
    //14-双偏振相态分类HCL
    //15-杂波标志CP
    //16-水平通道信噪比SNRH
    //17-垂直通道信噪比SNRV
    //18~31-Reserved保留
    //32-订正后反射率Zc
    //33-订正后径向速度Vc
    //34-订正后谱宽Wc
    //35-订正后差分反射率ZDRc
    int Scale;                       //比例,数据编码的比例(0~32768)？？
    int Offset;                      //偏移，数据编码的偏移(0~32768)？？
    short BinLength;                 //库字节长度(1~2)
    short Flags;                     //数据标志位，暂不使用
    int Length;                      //距离库数据的长度，不包括当前的径向数具头大小
    char Reserved[12];               //保留字段
    //径向数据值 = (存储值-Offset)/Scale
} MOMENTHEADER;


typedef struct
{
    std::vector<char> linedata;
} MOMENTDATA;

typedef struct
{
    MOMENTHEADER momentheader;
    std::vector<char> momentdata;
} MOMENTBLOCK;

typedef struct
{
    RADIALHEADERPAR radialheader;
    std::vector<MOMENTBLOCK> momentblock;
} RADIAL;

typedef struct
{
    RADIALHEADER radialheader;
    std::vector<MOMENTBLOCK> momentblock;
} RADIAL_NWC;

typedef struct
{
    std::vector<RADIAL> radial;
} RADIALBLOCK;

typedef struct
{
    COMMONBLOCK commonBlock;
    COMMONBLOCKPAR commonBlockPAR;
    std::vector<RADIAL> radials;
} WRADRAWDATA;


#ifdef __GNUC__
#else
    #pragma pack(pop)
#endif
