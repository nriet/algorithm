#ifndef NEW_DOPPLER_H
#define NEW_DOPPLER_H

#include <vector>
#include <QVector>
using namespace std;

//#define RAWRECORDLENGTH		998
//#define SINGLERAWRECORDLENGTH	992

#pragma pack(1)

typedef struct  _RADARIdNEWDP_
{
    char  RadarDataType[2];
    int  DataVersion;
    unsigned int  FileHeaderLength;
    char  Reserved[6];
} RADARId_NEW_DP;

typedef struct _RADARSITENEWDP_
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
} RADARSITE_NEW_DP;

typedef struct _RADARPERFORMANCEPARAMNEWDP
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
} RADARPERFORMANCEPARAM_NEW_DP;

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

typedef struct _LAYERPARAMNEWDP
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
} LAYERPARAM_NEW_DP;

typedef struct _RADAROBSERVATIONPARAMNEWDP_
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
    LAYERPARAM_NEW_DP LayerParam[32];
//    short RHIA;
//    short RHIL;
//    short RHIH;
} RADAROBSERVATIONPARAM_NEW_DP;

typedef struct _NewRadarHeaderNewDP_
{
    RADARId_NEW_DP id;
    RADARSITE_NEW_DP SiteInfo;
    RADARPERFORMANCEPARAM_NEW_DP PerformanceInfo;
    RADAROBSERVATIONPARAM_NEW_DP ObservationInfo;
    char Reserved[563];
} NewRadarHeader_New_DP;

#define BINNUMBER_NEWDP  4
#define DATANUMBER_NEWDP	1000

struct _DataRecordNEWDP_
{
    unsigned short startaz;
    short startel;
    unsigned char hour, minute, second;
    unsigned short millisecond;
    unsigned char range[DATANUMBER_NEWDP][BINNUMBER_NEWDP];
};

#pragma pack()

//class NEW_DOPPLER
//{
//public:
//    NEW_DOPPLER();
//    int MakePro(string input_str, SWROriginFileHeader &h, HISRADIALDATA *d);

//private:
////    void readheader(SWROriginFileHeader &h);
//    int loadNewDopplerFile(const char *fileName);
//    void convertNewDopplerHeaderToVTB(SWROriginFileHeader &h);
//    void convertNewDopplerBufferToVTB(SWROriginFileHeader &h, HISRADIALDATA *d);
//    int getLayerInfo(NewRadarHeader_New_DP radarHeaderNewDP);
////    int getBB(const char *fileName);

//private:
////    int m_BB;
//    int m_LayerNumber;	// 扫描层数
//    int m_ScanType;//扫描任务类型，0-体扫，1-单层PPI，2-单层RHI，3-单层扇扫，4-扇体扫，5-多层RHI，6-手工扫描
//    NewRadarHeader_New_DP m_radarHeaderNewDP;
//    vector<vector<_DataRecordNEWDP_>> m_NewDopplerDataLst;
//};

#endif // NEW_DOPPLER_H
