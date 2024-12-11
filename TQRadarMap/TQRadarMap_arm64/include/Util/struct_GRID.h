#ifndef STRUCT_VTB_H
#define STRUCT_VTB_H

//#pragma once

//#pragma pack(1)

//#include "struct_VTB.h"

#define MAXGRIDLAYER 32
#define MAXRADAR 32

/* 产品ID，
基于极坐标数据产品序列   VTB->GRID
101 = ZCAPPI     // 经过地物杂波消除的dBZ值= CorZ/100
102 = TCAPPI     // 不经过地物杂波消除的dBZ值= UnZ/100
103 = VCAPPI     // 速度值= V/100
				 //正值表示远离雷达的速度，负值表示朝向雷达的速度
104 = WCAPPI     // 谱宽值= W/100
105 = ZDRCAPPI   // 反射率差值= ZDR/100，单位db
106 = PHDPCAPPI  // 差分传播相移= PHDP/100+180，单位度
107 = KDPCAPPI	 // 差分传播相移常数= KDP/100，单位度/公里
108 = ROHVCAPPI	 // 相关系数值= ROHV/100
109 = LDRCAPPI

基于格点数据产品序列   GRID->GRID
201 = ZCAPPIMOSAIC       // 经过地物杂波消除的dBZ值= CorZ/100
202 = TCAPPIMOSAIC       // 不经过地物杂波消除的dBZ值= UnZ/100
203 = VCAPPIMOSAIC       // 速度值= V/100                 //一般没有这个产品
						 //正值表示远离雷达的速度，负值表示朝向雷达的速度
204 = WCAPPIMOSAIC       // 谱宽值= W/100
205 = ZDRCAPPIMOSAIC     // 反射率差值= ZDR/100，单位db
206 = PHDPCAPPIMOSAI     // 差分传播相移= PHDP/100+180，单位度   //一般没有这个产品
207 = KDPCAPPIMOSAIC     // 差分传播相移常数= KDP/100，单位度/公里
208 = ROHVCAPPIMOSAIC    // 相关系数值= ROHV/100
209 = LDRCAPPIMOSAIC

210 = ET                 // 回波顶高
211 = EB                 // 回波底高
212 = CR                 // 组合反射率
213 = VIL                // 累计液态水
*/

typedef struct tagRadarProductParameters
{
	unsigned short ProductionID;
	char ProductionName[10]; //产品名称ZCAPPI，与产品ID对应
	char ProductMethod[10]; //产品实现方法，区分不同算法，例如单偏振QPE,双偏振QPE
	short DAmp;//数值放大倍数
	char DByte;//数据文件中一个数据(一个格点)，占用字节数, 百位数表示是否有符号 	0xx:表示无符号位；1xx : 表示有符号位
	short DZero;//无数据的代码
	unsigned short Year;//数据产品生成时间的年(2000～)
	unsigned char Month;//数据产品据生成时间的月(1～12)
	unsigned char Day;//数据产品据生成时间的日(1～31)
	unsigned char Hour;//数据产品生成时间的时(00～23
	unsigned char Minute;//数据产品生成时间的分(00～59)
	unsigned char Second;//数据产品生成时间的分(00～59)
}RadarProductParameters;

typedef struct tagMapProjectionParameters
{
	unsigned char mapproj; // 1=Lambert; 2=lat-lon
	short ctrlon; //unit:0.01°   -180°~180°东经为正
	short ctrlat; //unit:0.01°   -90°~90°北纬为正
	//if ctrlon & ctrlat = -32768, use radar location as ctrlon &ctrlat
	short trulat1; // used by Lambert projection
	short trulat2;
	short trulon;
}MapProjectionParameters;

typedef struct tagGridParameters
{
	unsigned short nx;
	unsigned short ny;
    unsigned char nz;
	unsigned short dx; //unit:m(Lambert) 1/50000°(lat-lon）等经纬网格
	unsigned short dy; //unit:m(Lambert) 1/50000°(lat-lon）等经纬网格
	unsigned short z[MAXGRIDLAYER];  //unit:m
}GridParameters;

typedef struct tagAlgorithmParameters
{
	short Para0;
	short Para1;
	short Para2;
	short Para3;
	short Para4;
	short Para5;
	short Para6;
	short Para7;
	short Para8;
	short Para9;
}AlgorithmParameters;

typedef struct tagRadarProductHead
{
	char StationNumber[10];
    //RadarDataHead RadarInfo[MAXRADAR];
    RadarProductParameters ProInfo;
	MapProjectionParameters MapProjInfo;
	GridParameters GridInfo;
	AlgorithmParameters AlgorithmInfo;
}RadarProductHead;

/*
typedef struct tagRADARBASEPRODUCTPARAM
{
	unsigned short Production;//产品名称1＝CAPPI
	short HeightAngle;//RHI时为方位角, 单位1/10度； PPI时为仰角值，单位1/10度； CAPPI时为高度值，单位为米；
	short Range;//有效探测距离(单位为公里)
	short Resoluton;//网格距(单位为米)
	short XLength;//水平格点数
	short YLength;//垂直格点数
	short XRadar;//雷达位置X（X-左上角为零）
	short YRadar;//雷达位置Y（Y-左上角为零）
	short DAmp;//数值放大倍数
	char DByte;//数据文件中一个数据(一个格点)，占用字节数, 百位数表示是否有符号 	0xx:表示无符号位；1xx : 表示有符号位
	short DZero;//无数据的代码
	char DataType;//资料类型 1＝强度值(dBZ)	2＝径向速度值(米／秒) 3＝速度谱宽(米／秒)
	char StationID;//台站代码
	unsigned short Year;//数据产品生成时间的年(2000～)
	unsigned char Month;//数据产品据生成时间的月(1～12)
	unsigned char Day;//数据产品据生成时间的日(1～31)
	unsigned char Hour;//数据产品生成时间的时(00～23
	unsigned char Minute;//数据产品生成时间的分(00～59)
	//char Spare[726];//备用726个字节
	short ZLength;//高度格点数
	short Resoluton_Z;//高度分辨率//km
	char Spare[722];//备用726个字节
}RADARBASEPRODUCTPARAM;
*/

#endif //STRUCT_VTB_H
