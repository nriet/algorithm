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
* File:struct_RadarProduction_Recognition.h
* Author:Nriet
* time 2023-05-24
*************************************************************************/
#ifndef STRUCT_RADARPRODUCTION_RECOGNITION_H
#define STRUCT_RADARPRODUCTION_RECOGNITION_H

#include <string>
#include <iostream>
#include <list>
#include <vector>
#include <struct_RadarProduction_Grid.h>

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

310 = ET                 // 回波顶高
311 = EB                 // 回波底高
312 = CR                 // 组合反射率
313 = VIL                // 累计液态水

600 = MESH
601 = RAIN              //Precipitation
602 = SS                 //Storm
603 = MESO               //Meso
604 = TVS                //Tornado vortex signature
605 = HAIL               //Hail Storm
606 = WIND               //Wind Hazard

*/

namespace  s_Pro_Rec{

    typedef struct
    {
        float MaxLongitude;     //max ref location
        float MaxLatitude;
        float MaxHeight;
        int MaxTime;
        float Top;
        float Bottom;
        float Size;
        float MaxRef;
        float Mass;
        float VIL;
        int   Tref;
        int   Tarea;
    }STORMPARAMETERS;

    typedef struct
    {
        float SRTavg;
        float mavg;
        float SRTmax;
        float HFC;
        float DAA;
        float DMA;
        float DAR;
        float FRadius;
        float FMaxV;
        float FMinV;
        int   Num;
        int   Vortex;
    }MESOPARAMETERS;

    typedef struct
    {

    }TVSPARAMETERS;

    typedef struct
    {

    }HAILPARAMETERS;

    typedef struct
    {

    }RAINPARAMETERS;

    typedef struct
    {
        int Time;
        float Latitude;
        float Longitude;
        float Height;
        float Data;
    }CENTREINFO;

    typedef struct
    {
        float Latitude;
        float Longitude;
    }OUTLINEPOINT;

    typedef struct
    {
        float CtrLat;
        float CtrLon;
        float LongAxis;
        float ShortAxis;
        float DipAngle;
    }ELLIPSEINFO;

    typedef struct
    {
        CENTREINFO Centre;
        vector<OUTLINEPOINT> Outline;
        ELLIPSEINFO Ellipse;
    }SHAPEINFO;

    typedef struct
    {
        int RecTime;
        SHAPEINFO ShapeParas;
        union
        {
            char Reserved[128];
            STORMPARAMETERS StormInfo;
            MESOPARAMETERS MesoInfo;
            TVSPARAMETERS TVSInfo;
            HAILPARAMETERS HailInfo;
            RAINPARAMETERS RainInfo;
        };
    }RecParas;

    typedef vector <RecParas> RecParasSeq;

    typedef struct
    {
        int ProductID;
        int StormID;
        int StormStartTime;    //数据开始时间戳
        int StormEndTime;      //数据结束时间戳  //当尚未结束时，赋缺测
        float StormSpeed;       // 风暴单体的速度m/s
        float StormDirection;   // 风暴单体的方向，度
        vector <RecParas> PastInfo;
        vector <RecParas> ForecastInfo;
    }RecBlock;
    typedef vector <RecBlock> RecBlockSeq;

    typedef struct
    {
        s_Pro_Grid::RadarProductParameters ProInfo;
        s_Pro_Grid::RadarProductDataParameters ProDataInfo;
        vector <s_Pro_Rec::RecBlock> RecList;
    }RecognitionProduct;

}

#endif // STRUCT_RADARPRODUCTION_RECOGNITION_H
