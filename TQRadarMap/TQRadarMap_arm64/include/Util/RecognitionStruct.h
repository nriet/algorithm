#ifndef RECOGNITIONSTRUCT_H
#define RECOGNITIONSTRUCT_H

#include <vector>
#include <string>
#include <iostream>
#include <list>
#include <string.h>

using std::list;
using std::vector;
using namespace std;

#define MAXLAYERNUM 100

///Storm recognition
typedef struct {
    double rsbeg;                                                     //开始距离 公里
    double rsend;                                                     //结束距离 公里
    double az;                                                        //方位角 度
    double mwl;                                                       //质量权重长度 kg/km**2
    double mwls;                                                      //质量权重面积 kg/km
    double maxIrain;
    double avgIrain;
    double maxref;                                                    //最大反射率 dbZ
    int    Tref;                                                      //反射率域值 dbZ
}STORM_SEGMENT;

typedef struct {
    double MaxRef;                                                    //最大反射率因子
    double Height;                                                    //高度
    double El;                                                        //仰角
    double Xpos;                                                      //X坐标
    double Ypos;                                                      //Y坐标
    double Range;                                                     //距离
    double Az;                                                        //方位
    double Azbeg;                                                     //开始方位
    double Azend;                                                     //结束方位
    int    nSegNum;                                                   //段的个数
    double rcbeg;                                                     //开始距离
    double rcend;                                                     //结束距离
    double Mass;                                                      //质量
    int Tref;                                                         //反射率域值
    double Area;                                                      //面积
//    STORM_SEGMENT Segment[1440];                                      //风暴段结构，每层最多1440个
}STORM_COMPONENT;

typedef struct
{
    int ID;
    int ScanTime;
    double Xpos;                                                      //X坐标/km
    double Ypos;                                                      //Y坐标/km
    double Base;                                                      //风暴底高度/km
    double Top;                                                       //风暴顶高度/km
    double Range;                                                     //风暴中心距离/km
    double Az;                                                        //风暴中心方位
    double VIL;                                                       //VIL值
    double MaxRef;                                                    //最大反射率因子
    double H_MaxRef;                                                  //最大反射率因子所在的高度/km
    int    nCompNum;                                                  //包含的二维风暴个数
    double Mass;                                                      //风暴的质量
    double Height;                                                    //风暴的高度/km
    double Depth;                                                     //风暴深度/km
    double Volume;                                                    //风暴的体积/km
    double Radius;                                                    //风暴的半径/km
    STORM_COMPONENT Component[MAXLAYERNUM];                           //二维风暴的结构,最多32个,因为最多32层
}STORM_CELL;

typedef  struct
{
    vector<STORM_CELL> SingleStormList;
}STORMCELL_LIST;

//定义风暴track信息的结构体*****************************
typedef struct
{
    int  ID;
    double Base;                                                      //风暴底高度
    double Top;                                                       //风暴顶高度
    double MaxRef;                                                    //最大反射率因子
    double H_MaxRef;                                                  //最大反射率因子所在的高度
    int    nCompNum;                                                  //包含的二维风暴个数
    double Mass;                                                      //风暴的质量
    double Height;                                                    //风暴的高度
    double Depth;                                                     //风暴深度
    double Volume;                                                    //风暴的体积
    double Radius;                                                    //风暴的半径

    double timegap;
    double X_last;
    double Y_last;
    double X_now;
    double Y_now;
    double X_delta;
    double Y_delta;
    double VIL_last;
    double VIL_now;
    double Range_last;
    double Range_now;
    double Az_last;
    double Az_now;
    double speed;
}STORM_TRACK;

typedef struct
{
    int time;//外推时间，秒
    double X;
    double Y;
    double VIL;
    double Az;//相对雷达站方位
    double Range;
}POSITION;

//定义风暴forecast信息的结构体*****************************
typedef struct
{
    int ID;
    int Continue; //0-旧生，1-新生
    int NumOfVolumes;//体扫个数
    double Speed;
    double Xpos;                                                      //当前X坐标
    double Ypos;                                                      //当前Y坐标
    double VIL;
    double Az;
    double Dir;
    double Range;

    double Base;                                                      //风暴底高度
    double Top;                                                       //风暴顶高度
    double MaxRef;                                                    //最大反射率因子
    double H_MaxRef;                                                  //最大反射率因子所在的高度
    int    nCompNum;                                                  //包含的二维风暴个数
    double Mass;                                                      //风暴的质量
    double Height;                                                    //风暴的高度
    double Depth;                                                     //风暴深度
    double Volume;                                                    //风暴的体积
    double Radius;                                                    //风暴的半径


    POSITION FPos[5];
    POSITION HPos;
}STORM_FORECAST;

///MARC recognition
typedef struct {
    double rsbeg;                                                     //开始距离 公里
    double rsend;                                                     //结束距离 公里
    double az;                                                        //方位角 度
    double mwl;                                                       //质量权重长度 kg/km**2
    double mwls;                                                      //质量权重面积 kg/km
    double maxIrain;
    double avgIrain;
    double minRVD;                                                    //最大RVD
    int    TRVD;                                                      //RVD域值
}MARC_SEGMENT;

typedef struct {
    double MinRVD;                                                    //最小径向散度
    double Height;                                                    //高度
    double El;                                                        //仰角
    double Xpos;                                                      //X坐标
    double Ypos;                                                      //Y坐标
    double Range;                                                     //距离
    double Az;                                                        //方位
    double Azbeg;                                                     //开始方位
    double Azend;                                                     //结束方位
    int    nSegNum;                                                   //段的个数
    double rcbeg;                                                     //开始距离
    double rcend;                                                     //结束距离
    double Mass;                                                      //质量
    int TRVDref;                                                      //径向散度阈值
    double Area;                                                      //面积
}MARC_COMPONENT;

typedef struct
{
    int ID;
    int ScanTime;
    double Xpos;                                                      //X坐标/km
    double Ypos;                                                      //Y坐标/km
    double Base;                                                      //MARC特征底高度/km
    double Top;                                                       //MARC特征顶高度/km
    double Range;                                                     //MARC特征中心距离/km
    double Az;                                                        //MARC特征中心方位
    double VIL;                                                       //VIL值
    double MinRVD;                                                    //最小RVD值
    double H_MinRVD;                                                  //最小RVD所在的高度/km
    int    nCompNum;                                                  //包含的二维MARC分量个数
    double Mass;                                                      //MARC特征的质量
    double Height;                                                    //MARC特征的高度/km
    double Depth;                                                     //MARC特征深度/km
    double Volume;                                                    //MARC特征的体积/km
    double Radius;                                                    //MARC特征的半径/km
    MARC_COMPONENT Component[MAXLAYERNUM];                            //二维MARC分量的结构
}MARC_CELL;

#endif // RECOGNITIONSTRUCT_H
