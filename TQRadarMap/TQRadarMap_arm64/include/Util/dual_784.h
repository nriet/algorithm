#ifndef DUAL_784_H
#define DUAL_784_H

//#include "struct_stddata.h"
#include <vector>
#include <QVector>

using namespace std;

#pragma pack(1)

#define NEWRADARHEADERLENGTH	1024
struct LAYERPARAM_DUAL
{
    unsigned char  ambiguousp;
    unsigned short	 Arotate;
    unsigned short	 Prf1;
    unsigned short	 Prf2;
    unsigned short	 spulseW;
    unsigned short	 MaxV;
    unsigned short	 MaxL;
    unsigned short	 binWidth;
    unsigned short	 binnumber;
    unsigned short	 recordnumber;
    short	 Swangles;
};

struct RADARSITE_DUAL
{
    char   country[30];
    char   province[20];
    char   station[40];
    char   stationnumber[10];
    char   radartype[20];
    char   longitude[16];
    char   latitude[16];
    int  longitudevalue;
    int  lantitudevalue;
    int  height;
    short   Maxangle;
    short   Opangle;
    short   MangFreq;
};


struct RADARPERFORMANCEPARAM_DUAL
{
    int	 AntennaG;
    unsigned short  BeamH;
    unsigned short  BeamL;
    unsigned char  polarizations;
    char   sidelobe;
    int  Power;
    int  wavelength;
    unsigned short  logA;
    unsigned short  LineA;
    unsigned short  AGCP;
    unsigned char 	 clutterT;
    unsigned char 	 VelocityP;
    unsigned char 	 filderP;
    unsigned char	 noiseT;
    unsigned char 	 SQIT;
    unsigned char 	 intensityC;
    unsigned char	intensityR;
};

struct RADAROBSERVATIONPARAM_DUAL
{
    unsigned char 	 stype;
    unsigned short 	 syear;
    unsigned char 	 smonth;
    unsigned char 	 sday;
    unsigned char 	 shour;
    unsigned char 	 sminute;
    unsigned char 	 ssecond;
    unsigned char 	 Timep;
    unsigned int smillisecond;
    unsigned char 	 calibration;
    unsigned char 	 intensityI;
    unsigned char 	 VelocityP;
    struct LAYERPARAM_DUAL LayerParam[30];
    unsigned short	 RHIA;
    short	 RHIL;
    short	 RHIH;
    unsigned short 	 Eyear;
    unsigned char 	 Emonth;
    unsigned char 	 Eday;
    unsigned char 	 Ehour;
    unsigned char 	 Eminute;
    unsigned char 	 Esecond;
    unsigned char 	 Etenth;
};

struct NewRadarHeader_DUAL // header
{
    struct RADARSITE_DUAL  SiteInfo;
    struct RADARPERFORMANCEPARAM_DUAL  PerformanceInfo;
    struct RADAROBSERVATIONPARAM_DUAL  ObservationInfo;
    char datasign[30];

    int dataStyle;
    char Reserved[129];
};

#define RAWITEM  8
#define RAWRECORDLENGTH	1000

#define   DBZ_INDEX           0
#define   DBT_INDEX           1
#define   VEL_INDEX           2
#define   W_INDEX             3
#define   ZDR_INDEX           4
#define   KDP_INDEX           5
#define   PDP_INDEX           6
#define   RHV_INDEX           7
struct RVP7Data_DUAL
{
    unsigned short startaz, startel, endaz, endel;
    unsigned short rawdata[RAWITEM][RAWRECORDLENGTH];
};

struct RawBin
{
    char m_dbz/*强度*/, m_vel/*速度*/, m_undbz/*未定正强度*/, m_sw/*谱宽*/;
};

#define RAWRECORDLENGTH1		998

struct RVP7Record  			//	雷达数据格式I-V-W记录定义
{
    unsigned short startaz, startel, endaz, endel;
    RawBin  RawData[RAWRECORDLENGTH1];
};

#pragma pack()

//class DUAL_784
//{
//public:
//    DUAL_784();
////    int parse(const char *fileName, RadarDataHead &fileHead, QVector<HISRADIALDATA> &dataBuffer);
//    int MakePro(string input_str, SWROriginFileHeader &h, HISRADIALDATA *d);
////    int MakePro(string input_str, SWROriginFileHeader &h, QVector<HISRADIALDATA> &dataBuffer);

//private:
//    void readheader(SWROriginFileHeader &h);
//    int load784DualFile(const char *fileName);
//    int load784SingleFile(const char *fileName);
//    void convert784HeaderToVTB(SWROriginFileHeader &h);
////    void convert784BufferToVTB(SWROriginFileHeader &h, QVector<HISRADIALDATA> &dataBuffer);
//    void convert784BufferToVTB(SWROriginFileHeader &h, HISRADIALDATA *d);
////    void convert784SingleBufferToVTB(RadarDataHead fileHead, QVector<HISRADIALDATA> &dataBuffer);
//    void convert784SingleBufferToVTB(SWROriginFileHeader &h, HISRADIALDATA *d);
//    int getLayerInfo(NewRadarHeader_DUAL radarHeader784DUAL);
////    int getBB(const char *fileName);
//    unsigned char getPolarizations(const char *fileName);

//private:
////    int m_BB;
//    int m_LayerNumber;	// 扫描层数
//    int m_ScanType;//扫描任务类型，0-体扫，1-单层PPI，2-单层RHI，3-单层扇扫，4-扇体扫，5-多层RHI，6-手工扫描
//    NewRadarHeader_DUAL m_radarHeader784DUAL;
//    vector<vector<RVP7Data_DUAL> > m_784DUALDataLst;
//    vector<vector<RVP7Record> > m_784SingleDataLst;
//};

#endif // DUAL_784_H
