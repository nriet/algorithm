#ifndef LIB_FILE_IO_H
#define LIB_FILE_IO_H

#include "NrietFile.h"
#include "struct_WeatherRadar.h"
#include "struct_WeatherRadarProduct.h"
#include <struct_RadarProduction_Grid.h>
#include <struct_RadarProduction_Latlon.h>
#include "stable.h"
#include "struct_VTBnew.h"
#include <string>
#include "string.h"
#include <iostream>
#include <fstream>
#include "time.h"
#include <zlib.h>
#include <bzlib.h>
#include <QString>
#include <QStringList>
#include "Archive.h"
#include "dual_784.h"
#include "newdual_784.h"
#include "doppler_784.h"
#include "new_doppler.h"
#include <QDebug>

#include <fcntl.h>   // for O_WRONLY
#include <unistd.h>  // for dup and dup2
#include <cstdio>    // for fileno, stdout, stderr

using namespace std;

class CNrietFileIO : public CNrietFile
{
public:
    CNrietFileIO();
    ~CNrietFileIO();

    int LoadDataFromFile(void *in_str, int standard);

    void *PutHeadPoint();
    void *PutDataPoint();
    void *PutRadarRawData();

    void *GetFileName(void *ProPoint, int standard);
    int SetDebugLevel(int temp);
    int FreeData(void);

    void GetFileNameList(void *ProPoint, void *str_out);
    int GetDrawData(void *data, void *outdata, void *mapinfo, void *gridinfo, void *invalid);
    int LoadDataAndSaveFile(void *temp, void *in_str, int standard);

    int LoadCSA(void *, void *);

    void getSITECODE(string SITECODE);
    void gettime_opticalFlow(string Time_opticalFlow);
private:
    // 720A
    RadarHeader720A *m_RadarHeader720A = nullptr;
    NewRadarHeader_New_DP *m_radarHeaderNewDP = nullptr;
    // 784
    NewRadarHeader_DUAL *m_NewRadarHeader_DUAL = nullptr;
    NewRadarHeader_NEWDUAL *m_NewRadarHeader_NEWDUAL = nullptr;

    RadarDataHead *m_RadarDataHead = nullptr;      // 雷达数据头
    NewLineDataBlock *m_pLineData = nullptr;      // 径向数据指针

    COMMONBLOCK *m_RadarHead = nullptr;     //  标准格式雷达数据头
    WRADRAWDATA *m_RadarData = nullptr;

    RadarDataHead_SBADN_PHASEDARRAY *m_RadarDataHead_SBand = nullptr;     // S波段相控阵雷达数据头

    s_Pro_Grid::RadarProduct m_SA_Data;

    int m_FlagofDataLoaded = -1;               // 加载标志
    int m_nLayerNum = 0;                    // 扫描层数
    int m_nRadialNum = 0;                   // 每层径向数，原始数据各层不同，均一化后间隔为0.25整数倍
    int m_nRadialNumSum = 0;                // 总有效径向数
    vector<bool> m_validLayer;              // 判断层数据是否有效（仅用于附件S相控阵）
    int m_nValidLayerNum = 0;               // 有效层数
    int m_nValidRadialNumSum = 0;           // 有效径向数

    int m_DebugLevel = 2;

//    bool ZlibFlag = false;
    string m_SITECODE;
    string m_time_opticalFlow;
    QString m_radarFileName;
    string m_fileTime;

    int IsInternalVTB(char *fileName);//VTB2.1
    bool IsZlibFile(char *filename);
    bool IsBZ2File(char *filename);
    bool IsFakeFile(char *filename);
    bool IsZlibRawData(char *fileName);//VTB2.1
    bool LoadInternalVTB(char *fileName);
    bool LoadInternalVTB_SBand_PhasedArray(char *fileName);
    bool LoadJDRadar(char *fileName);
    // 720A
    bool LoadJD720ARadar(char *fileName);
    void Get_nNumSum_720A();
    void convertSiChuangHeaderToNewVTB();
    void Get_nNumSum_720ADP();
    void convert720ADPHeaderToVTB();
    // 784
    int if784DP(QString RadarName);
    int if784Dual(QString RadarName);
    int if784NewDual(QString RadarName);
    bool LoadJD784DualRadar(char *fileName);
    bool LoadJD784NewDualRadar(char *fileName);
    bool LoadJD784DPRadar(char *fileName);
    bool LoadJD720ADPRadar(char *fileName);
    void Get_nNumSum_784_Dual();
    void Get_nNumSum_784_NewDual();
    void convert784dualHeaderToVTB();
    void convert784newdualHeaderToVTB();
    void convert784DPHeaderToVTB();

    bool LoadPhasedArrayInternalVTB(char *fileName);
    bool LoadStandardVTB(char *fileName);
    bool LoadQCData(char *fileName);
    bool LoadBZ2StandardVTB(char *fileName);
    bool LoadMHVTB(char *fileName);
    bool LoadStandardPARVTB(char *fileName);

//    int LoadZlibInternalVTB(char* fileName);

    int ConvertInternalVTBtoStandardFormat_SBand_PhasedArray();
    int ConvertInternalVTBtoStandardFormat1_0();
    int ConvertStandardFormat1_0toInternalVTB();
    int ConvertFMTtoFakePhasedArray();
    int ConvertRadialHeaderNWCtoRadialHeaderPAR(RADIALHEADER *, RADIALHEADERPAR *);
    int ConvertCommonBLockPARtoCommonBlockNWC(COMMONBLOCKPAR *, COMMONBLOCK *);

    void Get_nNumSum();
    void Get_nNumSum_SBand_PhasedArray();
    void Sort_pLineData();
    void Sort_Data(NewLineDataBlock *DataPoint, int nSortNum);
    void Normalize_Az();
    int GetMaxRadialNum();
    time_t time_convert(int year, int month, int day, int hour, int minute, int second);
    int FreeBlock();

    bool IsRadarRawData(void *data);
    bool SaveRadarRawData(void *data, char *fileName);
    bool SaveZlibRadarRawData(void *data, char *fileName);
    bool SaveZlibRadarQCData(void *temp, char *FileName);
    bool SaveBZ2RadarRawData(void *data, char *fileName);
    bool SaveZlibRadarRawDataBuf(void *source, Bytef *dest, uLongf *destLen);
    char *GetRadarRawFileName(void *data);

    bool IsRadarProData(void *data);
    bool SaveRadarProData(void *data, char *fileName);
    bool GetRadarProDrawData(void *indata, void *outdata, void *mapinfo, void *gridinfo, void *invalid);
    bool SaveZlibRadarProData(void *data, char *fileName);
    bool SaveZlibRadarProDataBuf(void *source, Bytef *dest, uLongf *destLen);
    char *GetRadarProFileName(void *data);
    char *GetRadarQCFileName(void *data);
    char *GetRadarProFileName_JS(void *data);

    bool IsRadarLatlonData(void *data);
    bool SaveRadarLatlonData(void *data, char *fileName);
    bool SaveZlibRadarLatlonData(void *data, char *fileName);
    bool SaveZlibRadarLatlonDataBuf(void *source, Bytef *dest, uLongf *destLen);
    char *GetRadarLatlonFileName(void *data);
    char *GetRadarKJCLatlonFileName(void *data);
    void get_files(const string strDir, const string strFeature, vector<string> &filelist);

    char *GetKJCFileName(void *data);
    bool IsRadarKJCProData(void *temp);
    char *GetRadarKJCProFileName(void *data);
    bool SaveRadarKJCProData(void *data, char *FileName);
    bool SaveZlibRadarKJCProData(void *temp, char *FileName);

    bool IsRadarKJCRawData(void *temp);
    bool SaveZlibRadarKJCRawData(void *temp, char *FileName);
    bool SaveBZ2RadarKJCRawData(void *temp, char *FileName);



    char m_aFileName[256];
};

extern "C" CNrietFile *GetFileInstance();

#endif // LIB_FILE_IO_H
