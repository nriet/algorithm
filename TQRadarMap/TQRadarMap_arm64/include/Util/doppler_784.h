#ifndef DOPPLER_784_H
#define DOPPLER_784_H

//#include "struct_stddata.h"
#include <vector>
#include <QVector>
using namespace std;

#define RAWRECORDLENGTH		998
#define SINGLERAWRECORDLENGTH	992

#pragma pack(1)

typedef struct  _RADARIdDP_
{
    char  RadarDataType[2];
    int  DataVersion;
    unsigned int  FileHeaderLength;
    char  Reserved[6];
} RADARId_DP;

typedef struct _RADARSITEDP_
{
    char  station[40];
    char  stationnumber[5];
    char  radartype[20];
    int  longitudevalue;
    int  lantitudevalue;
    int  height;
    short  Maxangle;
    short  Opangle;
    char  Reserved[3];
} RADARSITE_DP;

typedef struct _RADARPERFORMANCEPARAMDP
{
    unsigned short  BeamH;
    unsigned short  BeamL;
    int  Power;
    int  wavelength;
    unsigned short  sidelobe;
    unsigned short  logA;
    unsigned short  LineA;
    unsigned short  AGCP;
    unsigned short  MinLogPw;
    unsigned short  MinLinePw;
    int  AntennaG;
    short  polarizations;
    short  clutterT;
    unsigned char  VelocityP;
    unsigned char  filderP;
    short  noiseT;
    short  SQIT;
    unsigned char  intensityC;
    unsigned char  intensityR;
    char  Reserved[10];
} RADARPERFORMANCEPARAM_DP;

/*
typedef struct _LAYERPARAM
{
    unsigned char	ambiguousp;
    unsigned short	Arotate;
    unsigned short	Prf1;
    unsigned short	Prf2;
    unsigned short	spulseW;
    unsigned short	MaxV;
    unsigned short	MaxL;
    unsigned short	binWidth;
    unsigned short	binnumber;
    unsigned short	recordnumber;
    short Swangles;
} LAYERPARAM_DP;
*/

typedef struct _LAYERPARAM
{
    unsigned char  ambiguouspV;
    unsigned char  ambiguouspR;
    char DataForm;
    unsigned short	 Arotate;
    unsigned int PluseW;
    unsigned short	 Prf1;
    unsigned short	 Prf2;
    unsigned short	 MaxV;
    unsigned short	 MaxL;
    unsigned short	 RBinWidth;
    unsigned short	 VBinWidth;
    unsigned short	 WBinWidth;
    unsigned short	 PolarBinWidth;
    unsigned short	 RBinnumber;
    unsigned short	 VBinnumber;
    unsigned short	 WBinnumber;
    unsigned short	 PolarBinnumber;
    unsigned short	 recordnumber;
    short	 Swangles;
    unsigned int DBegin;
} LAYERPARAM_DP;

typedef struct _RADAROBSERVATIONPARAMDP_
{
    unsigned char  sType;
    unsigned char  calibration;
    unsigned char  IntensityI;
    unsigned char  VelocityP;
    unsigned short	sYear;
    unsigned char  sMonth;
    unsigned char  sDay;
    unsigned char  sHour;
    unsigned char  sMinute;
    unsigned char  sSecond;
    unsigned char  Timep;
    unsigned short  sIntensityN;
    unsigned short  sVelocityN;
    unsigned short  sBipolarN;
    unsigned char  eDay;
    unsigned char  eHour;
    unsigned char  eMinute;
    unsigned char  eSecond;
    unsigned char  ExportDigit;
    LAYERPARAM_DP LayerParam[32];
    short RHIA;
    short RHIL;
    short RHIH;
} RADAROBSERVATIONPARAM_DP;

typedef struct _NewRadarHeaderDP_
{
    RADARId_DP id;
    RADARSITE_DP SiteInfo;
    RADARPERFORMANCEPARAM_DP PerformanceInfo;
    RADAROBSERVATIONPARAM_DP ObservationInfo;
    char Reserved[557];
} NewRadarHeader_DP;

typedef struct  _RawBinDP_
{
    union
    {
        struct
        {
            unsigned char m_dbz, m_undbz, m_vel, m_sw;
        };
        struct
        {
            unsigned char value[4];
        };
    };
} RawBin_DP;

#define RAWRADARDATALENGTH		998
typedef struct _DataRecordDP_
{
    unsigned short startaz;
    short startel;
    unsigned char hour, minute, second;
    unsigned short millisecond;
    RawBin_DP rawdata[RAWRADARDATALENGTH];
} DataRecord_DP;
#pragma pack()

//class Doppler_784
//{
//public:
//    Doppler_784();
//    int MakePro(string input_str, SWROriginFileHeader &h, HISRADIALDATA *d);
////	int parse(const char*fileName, RadarDataHead &fileHead, QVector<HISRADIALDATA> &dataBuffer);

//private:
//    int load784File(const char *fileName);
//    void convert784HeaderToVTB(SWROriginFileHeader &h);
//    void convert720ABufferToVTB(SWROriginFileHeader &h, HISRADIALDATA *d);
//    void convert784BufferToVTB(SWROriginFileHeader &h, HISRADIALDATA *d);
//    int getLayerInfo(NewRadarHeader_DP radarHeader784DP);
////    int getEEE(const char *fileName);
//private:
////    int m_EEE;
//    int m_LayerNumber;	// 扫描层数
//    int m_ScanType;//扫描任务类型，0-体扫，1-单层PPI，2-单层RHI，3-单层扇扫，4-扇体扫，5-多层RHI，6-手工扫描
//    NewRadarHeader_DP m_radarHeader784DP;
//    vector<vector<DataRecord_DP>> m_784DPDataLst;
//};


#endif // DOPPLER_784_H
