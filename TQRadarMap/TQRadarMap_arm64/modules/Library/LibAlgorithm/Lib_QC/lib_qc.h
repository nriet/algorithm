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
* File:lib_qc.h
* Author:Nriet
* time 2023-05-24
*************************************************************************/
#ifndef LIB_QC_H
#define LIB_QC_H

#include <struct_WeatherRadar.h>
#include <struct_WeatherRadarProduct.h>
#include <stable.h>
#include "string.h"
#include <iostream>
#include <math.h>
#include <time.h>
#include <fstream>
#include "omp.h"
#include "NrietAlgorithm.h"

#define TWOPI   (2*PI)
#define NOMASK  0
#define MASK    1

#pragma once
typedef struct
{
    char FuncName[32];              // 功能名
    int Scope;                      // 作用域（-1：始终起作用；0：始终不起作用；1：选择性起作用）
    int Method;
    std::vector<int> Type;
    std::vector<int> Except;
} QCParams;

typedef struct
{
    double mod;
    int x_connectivity;
    int y_connectivity;
    int no_of_edges;
} params_t;

//PIXELM information
struct PIXELM
{
    int increment;                  // No. of 2*pi to add to the pixel to unwrap it
    int number_of_pixels_in_group;  // No. of pixel in the pixel group
    double value;                   // value of the pixel
    double reliability;             //
    unsigned char input_mask;       // MASK: pixel is masked. NOMASK: pixel is not masked
    unsigned char extended_mask;    // MASK: pixel is masked. NOMASK: pixel is not masked
    int group;                      // group No.
    int new_group;
    struct PIXELM *head;            // pointer to the first pixel in the group in the linked list
    struct PIXELM *last;            // pointer to the last pixel in the group
    struct PIXELM *next;            // pointer to the next pixel in the group
};

typedef struct PIXELM PIXELM;

#define swap_edge(x,y) {EDGE t; t=x; x=y; y=t;}
#define order_QC(x,y) if(x.reliab > y.reliab) swap_edge(x,y)
#define o2(x,y) order_QC(x,y)
#define o3(x,y,z) o2(x,y) o2(x,z) o2(y,z)

typedef enum {yes, no} yes_no;

struct EDGE
{
    double reliab;                  // reliability of the edge and it depends on the two pixels
    PIXELM *pointer_1;              // pointer to the first pixel
    PIXELM *pointer_2;              // pointer to the second pixel
    int increment;                  // No. of 2*pi to add to one of the pixels to unwrap it with respect to the second
};

typedef struct EDGE EDGE;

using namespace std;

typedef struct
{
    vector <short> momentline;
} MOMENTLINE;

typedef struct
{
    vector <MOMENTLINE> radialline;
} RADIALLINE;

typedef struct
{
    vector <RADIALLINE> datablock;
} DATABLOCK;
//float临时数据
typedef struct
{
    vector <float> flinedata;
} FRADIALLINE;

typedef struct
{
    vector <FRADIALLINE> datablock;
} FDATABLOCK;

typedef vector<WRADPRODATA> WRADPROLIST;

#ifdef __GNUC__
#else
    #pragma pack(pop)
#endif

class CAlgoQC: public CNrietAlogrithm
{
public:
    CAlgoQC() {}
    virtual ~CAlgoQC() override {}

    virtual int Init() override;
    virtual int LoadParameters(void *) override;
    virtual int LoadStdCommonBlock(void *) override;
    virtual int LoadStdRadailBlock(void *) override;
    virtual int LoadStdData(void *) override;
    virtual int MakeProduct() override;
    virtual void *GetProduct(void) override;
    virtual int FreeData() override;
    virtual int Uninit() override;
    virtual int SetDebugLevel(int) override;

private:

    WRADRAWDATA *m_radardata_org = nullptr;
    WRADRAWDATA *m_radardata_out = nullptr;

    bool m_single_radial_mode = false;
//    WRADRAWDATA* m_radarqcdata_out;
    vector<short> QCflag{1, 1};
    QCParams m_params_calculateKDP = {"", -1, 0, {}, {4}};
    QCParams m_params_Zdr_PHDP_Correct = {"", 1, 0, {75}, {}};
    QCParams m_params_UnflodVel = {"", -1, 1, {}, {}};
    QCParams m_params_AttenuationCorrection = {"", 0, 0, {}, {}};
    vector<WRADRAWDATA> *m_radardata_out_list = nullptr;
    int DeleteInvalidData();
    int Sort_RadialData();
    void Sort_Data_Iter(int i_start, int i_end);
    int Normalize_Az();
    int Normalize_RHI();
    int GetMaxRadialNum();
    void CalcRadial(RADIAL *front, RADIAL *back, RADIAL *target);
    int m_DebugLevel = 3;
    //1:Error message   2:process message   3:debug message
    char time_str[32];
    void set_time_str();
    int FreeBlock();

    int Normalize_Az(WRADRAWDATA *m_radardata_in, WRADRAWDATA *m_radardata_out);
    void Sort_Data_Iter(int i_start, int i_end, WRADRAWDATA *m_radardata_out);

    MOMENTLINE tempmoment;
    RADIALLINE tempradial;
    DATABLOCK tempdata;
    vector <short> Tempmomentline;
    FRADIALLINE Ftempradial;
    FDATABLOCK Ftempdata;
    vector <float> FTempline;
    int m_LayerNum;
    vector<int> ElRadialNum;
    vector<int> ElRadialIndex;
    int nRadialNum;
    float m_AnglarResolution;

    vector<short> indexUnZH, indexV, indexW, indexZH, indexZDR, indexPHDP, indexKDP, indexSNR, indexROHV;
    vector<short> nBinNumZ, nBinNumV;
    vector<float> nBinWidthZ, nBinWidthV;

    int nBinNum;
    float nBinWidth;
    int nVBinNum;
    float nVBinWidth;
    int UnZHindex = -1, Vindex = -1, ZHindex = -1, ZDRindex = -1;
    int PHDPindex = -1, KDPindex = -1, Windex = -1, SNRindex = -1;
    int ROHVindex = -1;
//    int CalradialNum = 0;



    int GetRadialNumOfEl();
    int GetRadialIndexOfEl();
    int GetRadarParameters();
    unsigned short GetPointData(WRADRAWDATA *data, int radialNo, int momentNo, int binNo);
    void QuickSort(short *array, int L, int R);
    int WriteLayerData(int ilayer, int imoment);

    int PolarQC();
    int Zdr_PHDP_Correct();
    int CalculateKDP();                                            // 计算KDP
    int LGT_Correct();                                             //避雷针影响订正
    int AttenuationCorrection();                                   //衰减订正
    int SmoothData(int dot);                                       // 平滑资料
    int SmoothData_Dot;                                            // 中值平滑点数
    int SmoothDataPPI(int dot);                                    // 平滑PPI资料
    int SmoothDataRHI(int dot);                                    // 平滑RHI资料
    int RadialSmooth(int dot);                                     // 径向平滑
    int RadialSmooth_Dot;                                          // 径向平滑点数
    int RadialSmoothRHI(int dot);
    int RadialSmoothPPI(int dot);
    int VOutlierFiltering();
    int OutlierFiltering();
    int FillingGap();
    int UnfoldVel_shearb1s_old();                                               // 退速度模糊
    int UnfoldVel_shearb1s();
    int UnfoldVel_shearb1s_Core();
    int search_1st_beam(float &mean);
    int shearb1s_initial(int j, float *ref);
    int across_unfold(int i, int j);
    float rfold(float datav, float ref, float scale);
    int unfold1(int round_num, int jzero);
    int shearb1s(int round_num, bool flag, int iRial, float *ref);
    int chgbeam(int j, float *ref);
    bool FunctionValid(QCParams &);

    // 相位展开相关
    int m_XNum;             // m_XNum = AzNum
    int m_YNum;             // m_YNum = BinNum
    int m_XConnect = 1;     // X方向是否首尾连续
    int m_YConnect = 0;     // Y方向是否首尾连续
    double m_unamValue  = 0.7 * PI; // 不模糊阈值
    double m_scale;         // 径向速度->[-pi, pi]时的缩放比例
    double *m_VPPI = NULL;
    double *m_unwarpV = NULL;   // 相位展开结果
    unsigned char *m_inputMask = NULL;

    int UnflodVel_phase_unwrapping();
    unsigned short code(double value, int offset, int scale);
    double decode(unsigned short temp, int offset, int scale);
    //int unwrapping();       // 相位展开
    void unwrap2D(double *wrapped_image, double *unwrappedImage, unsigned char *input_mask,
                  int image_width, int image_height,
                  int wrap_around_x, int wrap_around_y);
    void extend_mask(unsigned char *input_mask, unsigned char *extended_mask,
                     int image_width, int image_height, params_t *params);
    void initialisePIXELs(double *wrapped_image, unsigned char *input_mask, unsigned char *extended_mask, PIXELM *pixel, int image_width, int image_height);
    void calculate_reliability(double *wrappedImage, PIXELM *pixel, int image_width, int image_height, params_t *params);
    double wrap(double pixel_value);
    int find_wrap(double pixelL_value, double pixelR_value);
    yes_no find_pivot(EDGE *left, EDGE *right, double *pivot_ptr);
    EDGE *partition(EDGE *left, EDGE *right, double pivot);
    void horizontalEDGEs(PIXELM *pixel, EDGE *edge, int image_width, int image_height, params_t *params);
    void verticalEDGEs(PIXELM *pixel, EDGE *edge, int image_width, int image_height, params_t *params);
    void quicker_sort(EDGE *left, EDGE *right);
    void gatherPIXELs(EDGE *edge, params_t *params);
    void unwrapImage(PIXELM *pixel, int image_width, int image_height);
    void maskImage(PIXELM *pixel, unsigned char *input_mask, int image_width, int image_height);
    void returnImage(PIXELM *pixel, double *unwrapped_image, int image_width, int image_height);

    //退速度模糊参量*********************************
    int NUM_CLUSTERS = 100;      //初始径向最多100根
    int NUM_PASSES = 5;     //最大退模糊回合数
    int KNUM = 2 ;       //10
    int KNREF_TIMES = 4;    //4
    float VELNY_SCALE1 = 0.4;    //用于判断径向速度的正负性，选取小速度求平均
    float VELNY_SCALE2 = 0.5;   //0.75//用于判断库速度是否模糊
    float KTOL = 10;
    float m_velny;       //最大不模糊速度
    int m_jzero = -1;    //初始径向
    float m_velny_scale; //VELNY_SCALE阈值
    int m_max_gate_dist1;//遍历孤立风暴的最大库数
    int m_max_beam_dist1;//最大方位径向单位
    int m_max_gate_dist;
    int m_max_beam_dist;
    vector<int> LineMark;
    vector<vector<int>> m_dataMarkArrayMM;
    float threshold1;//求径向平均速度的阈值
    float threshold2;//判断库是否模糊的阈值

};
extern "C" CNrietAlogrithm *GetAlgoInstance();
#endif // LIB_QC_H
