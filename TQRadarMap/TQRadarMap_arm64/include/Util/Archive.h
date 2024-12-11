#ifndef ARCHIVE_H
#define ARCHIVE_H
//#include "struct_stddata.h"
#include <vector>
#include <QVector>

using namespace std;

#pragma pack(1)

//#ifndef UCHAR
//    #define UCHAR unsigned char
//#endif

#ifndef USHORT
    #define USHORT unsigned short
#endif

#ifndef ULONG
    #define ULONG unsigned int
#endif

//--------------------------------------------------------------------------------------------------
#define	NUMBEROFBIN				1000			//每径向距离库数
//--------------------------------------------------------------------------------------------------

//	文件标识
typedef struct tagFILEIDENTIFIERS
{
    char	sFileID[4];			//雷达数据标识(原始数据标识符'RD'为雷达原始数据,'GD'为雷达衍生数据等...)
    float	fVersionNo;			//表示数据格式的版本号
    int	lFileHeaderLength;	//表示文件头的长度
} FILEIDENTIFIERS720A;
//--------------------------------------------------------------------------------------------------

//--------------------------------------------------------------------------------------------------
//	站址情况
typedef struct tagRADARSITE720A
{
    char	sCountry[30];		//国家名
    char	sProvince[20];		//省名
    char	sStation[40];		//站名
    char	sStationNumber[10];	//区站号
    char	sRadarType[20];		//雷达型号
    char	sLongitude[16];		//经度（文本，东经E，西经W）
    char	sLatitude[16];		//纬度（文本，北纬N，南纬S）
    int	lLongitudeValue;	//经度（单位1/1000°，东经正，西经负）
    int	lLatitudeValue;		//纬度（单位1/1000°，北纬正，南纬负）
    int	lHeight;			//海拔高度（mm）
    short	shMaxAngle;			//地物最大遮挡仰角（单位1/100°）
    short	shOptiAngle;		//最佳观测仰角（单位1/100°）
} RADARSITE720A;
//--------------------------------------------------------------------------------------------------

//--------------------------------------------------------------------------------------------------
//	性能参数
typedef struct tagRADARPERFORMANCEPARAM720A
{
    int 	lAntennaG;		//天线增益(0.001dB)
    USHORT 	usBeamH;		//垂直波束宽度(1/100°)
    USHORT	usBeamL;		//水平波束宽度(1/100°)
    unsigned char	ucPolarization;	//极化状态
    //	 0-水平
    //	 1-垂直
    //	 2-双偏振
    // 	 3-圆偏振
    //	 4-其它
    USHORT	usSidelobe;		//第一旁瓣(0.01dB)
    int 	lPower;			//峰值功率(瓦)
    int 	lWavelength;	//波长(微米)
    USHORT	usLogA;			//对数接收机动态范围(0.01dB)
    USHORT	usLineA;		//线性接收机动态范围(0.01dB)
    USHORT	usAGCP;			//AGC延迟量(微秒)
    USHORT	usLogMinPower;	//对数接收机最小可测功率(0.01dBm)
    USHORT	usLineMinPower;	//线性接收机最小可测功率(0.01dBm)
    unsigned char	ucClutterT;		//杂波消除阀值(0.01dB)
    unsigned char	ucVelocityP;	//多普勒处理模式(原：速度处理方式 0-无 1-PPP 2-FFT)
    //	0 ~ PPP处理
    //	1 ~ FFT全程
    //	2 ~ FFT单库
    //  3 ~ 相干脉组解距离模糊
    //  4 ~ 相位编码解距离模糊
    unsigned char	ucFilterP;		//地物杂波消除方式
    //	0-无
    //	1-滤波器1（原：杂波图）
    //	2-滤波器2（原：杂波图加滤波器）
    //	3-滤波器3（原：滤波器）
    //	4-滤波器4（原：谱分析）
    //	5-其它
    unsigned char	ucNoiseT;		//噪声消除阀值(0~255)
    unsigned char	ucSQIT;			//SQI阀值(0.01)
    unsigned char	ucIntensityC;	//RVP强度值估算采用的通道
    //	1-对数通道
    //	2-线形通道
    unsigned char	ucIntensityR;	//强度值估算是否进行了距离订正
    //	0-没有
    //	1-已进行
} RADARPERFORMANCEPARAM720A;

//	层参数
typedef struct tagLAYERPARAM720A
{
    unsigned char	ucDataType;		//本层观测要素
    //	1-单强度
    //	2-三要素	(单PRF)
    //	3-三要素	(双PRF)
    //	4-双线偏振
    //	5-双线偏振多普勒
    //	6-双波长(不共天线)
    //	7-双波长(共用天线)
    unsigned char	ucAmbiguousP;	//退模糊状态
    //	0-无退模糊
    //	1-软件退模糊
    //	2-双T退模糊
    //	3-批式退模糊
    //	4-双T加软件退模糊
    //	5-批式加软件退模糊
    //	6-双PPI退模糊
    //	9-其它方式
    USHORT	usSpeed;		//天线转速(0.01度/秒)
    USHORT	usPRF1;			//第一次重复频率(0.1Hz)
    USHORT	usPRF2;			//第二次重复频率(0.1Hz)
    USHORT	usPulseWidth;	//脉宽(微秒)
    USHORT	usMaxV;			//最大可测速度(厘米/秒)
    USHORT	usMaxL;			//最大可测距离(10米)
    USHORT	usZBinWidth;	//强度数据库长(1/10米)
    USHORT	usVBinWidth;	//速度数据库长(1/10米)
    USHORT	usWBinWidth;	//谱宽数据库长(1/10米)
    USHORT	usZBinNumber;	//强度数据库数
    USHORT	usVBinNumber;	//速度数据库数
    USHORT	usWBinNumber;	//谱宽数据库数
    USHORT	usRecordNumber;	//扫描径向个数
    short	sSwpAngle;		//仰角
    //	PPI-填写第一层(1/100度)，其余填FFFF
    //	RHI-不填
    //	VOL-填写本层(1/100度)
    char	cDataForm;		//数据排列方式
    //	11-CorZ
    //	12-UnZ
    //	13-V
    //	14-W
    //	21-CorZ+UnZ
    //	22-CorZ+V+W
    //	23-UnZ+V+W
    //	24-CorZ+UnZ+V+W
    //	4X-双偏振要素排列模式
    //	6X-双偏振多普勒要素排列模式
    //	8X-双波长要素排列模式
    ULONG	ulDataBegin;	//本层数据开始位置(字节计数)
} LAYERPARAM720A;
//--------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------
//	库长变化结构
typedef struct tagBINPARAM720A
{
    short	sCode;			//变化结构代码
    short	Begin;			//开始库位置(10米)
    short	End;			  //结束库位置(10米)
    short	BinLength;		//库长(1/10米)
} BINPARAM720A;
//--------------------------------------------------------------------------------------------------

//--------------------------------------------------------------------------------------------------
//	观测参数
typedef struct tagRADAROBSERVATIONPARAM720A
{
    unsigned char		ucType;			//扫描方式
    //	1-RHI
    //	10-PPI
    //	1XX-XX层的VOL
    //	200-单库FFT扫描
    USHORT		usSYear;		//观测开始时间的年(2000-)
    unsigned char		ucSMonth;		//观测开始时间的月(1-12)
    unsigned char		ucSDay;			//观测开始时间的日(1-31)
    unsigned char		ucSHour;		//观测开始时间的时(0-23)
    unsigned char		ucSMinute;		//观测开始时间的分(0-59)
    unsigned char		ucSSecond;		//观测开始时间的秒(0-59)
    unsigned char		ucTimeP;		//时间来源
    //	0-计算机时钟(1天内未对时)
    //  1-计算机时钟(1天内已对时)
    //	2-GPS
    //	3-其它
    ULONG		ulSMillisecond;	//观测开始时间的秒的小数位(微秒)
    unsigned char		ucCalibration;	//标校状态
    //  0-无
    //	1-自动
    // 	2-1星期内人工
    //  3-1月内人工
    //	其它码不用
    unsigned char		ucIntensityI;	//强度积分次数
    unsigned char		ucVelocityP;	//速度处理样本
    USHORT		usZStartBin;	//强度有效数据开始库数
    USHORT		usVStartBin;	//速度有效数据开始库数
    USHORT		usWStartBin;	//谱宽有效数据开始库数
    LAYERPARAM720A	LayerInfo[32];	//层参数数据结构
    USHORT		usRHIA;			//RHI所在的方位角(0.01度为单位)
    //PPI和VOL时为FFFF
    //单库FFT时为通道数(128或256)
    short 		sRHIL;			//RHI所在的最低仰角(0.01度为单位)
    //PPI和VOL和单库FFT时为FFFF
    //单库FFT时为方位(0.01度为单位)
    short 		sRHIH;			//RHI所在的最高仰角(0.01度为单位)
    //PPI和VOL和单库FFT时为FFFF
    //单库FFT时为仰角(0.01度为单位)
    USHORT		usEYear;		//观测结束时间的年(2000-)
    unsigned char		ucEMonth;		//观测结束时间的月(1-12)
    unsigned char		ucEDay;			//观测结束时间的日(1-31)
    unsigned char		ucEHour;		//观测结束时间的时(0-23)
    unsigned char		ucEMinute;		//观测结束时间的分(0-59)
    unsigned char		ucESecond;		//观测结束时间的秒(0-59)
    unsigned char		ucETenth;		//观测结束时间的1/100秒(0-99)
    USHORT		usZBinByte;		//强度数据库长变化情况
    //	无则填写0
    //	有则填写占用字节数
    BINPARAM720A 	BinRange1[5];	//5个8字节(强度无变化填入空字节)
    USHORT		usVBinByte;		//速度数据库长变化情况
    //	无则填写0
    //	有则填写占用字节数
    BINPARAM720A BinRange2[5];	//5个8字节(速度无变化填入空字节)
    USHORT		usWBinByte;		//谱宽数据库长变化情况
    //	无则填写0
    //	有则填写占用字节数
    BINPARAM720A BinRange3[5];	//5个8字节(谱宽无变化填入空字节)
} RADAROBSERVATIONPARAM720A;
//--------------------------------------------------------------------------------------------------

//--------------------------------------------------------------------------------------------------
//极坐标产品观测参数的结构（294个字节）
typedef struct tagPOLARPRODUCTOBSERVATIONPARAM
{
    unsigned char ucNStep;                   //体扫描层数  0XX=XX扫描层数
    unsigned short usSYear;                  //体扫记录开始时间的年(2000-)
    unsigned char ucSMonth;                  //体扫记录开始时间的月(1-12)
    unsigned char ucSDay;                    //体扫记录开始时间的日(1-31)
    unsigned char ucSHour;                   //体扫记录开始时间的时(00-23)
    unsigned char ucSMinute;                 //体扫记录开始时间的分(00-59)
    unsigned char ucSSecond;                 //体扫记录开始时间的秒(00-59)
    unsigned char ucTimeP;                   //时间来源  0-计算机时钟,但一天内未进行对时
    //          1-计算机时钟,一天内已进行对时  2-GPS   3-其他
    unsigned int ulSMillisecond;        //秒的小数位(计数单位微秒)
    unsigned char ucCalibrtion;              //标校状态   0-无   1-自动标校   2-一星期内人工标校  3-一月内人工标校  其他码不用
    unsigned char ucIntensityI;              //强度积分次数(32-128)
    unsigned char ucVelocityP;               //速度处理样本(31-255)(样本数减1)
    unsigned char ucDataType;                //体扫观测要素 1=单强度  2=三要素 单PRF  3=三要素 双PRF  4=双线偏振  5=双线偏振多普勒  6=双波长(不用天线)  7=双波长(公用天线)
    unsigned char ucAmbiguousP;              //体扫退速度模糊状态  0-无退模糊       1-软件退模糊       2-双T退模糊
    //                     3-批式退模糊     4-双T+软件退模糊    5-批式+软件退模糊
    //                     6-双PPI退模糊                9-其他方式
    unsigned short usMaxV;                   //最大可测速度，计数单位厘米/秒
    unsigned short usMaxL;                   //最大可测距离，计数单位10米
    unsigned short usZBinWidth;              //本高度层强度数据库长，以1/10米为计数单位
    unsigned short usVBinWidth;              //本高度层速度数据库长，以1/10米为计数单位
    unsigned short usWBinWidth;              //本高度层谱宽数据库长，以1/10米为计数单位

    unsigned short usZBinNumber;             //本高度层强度数据径向的库数
    unsigned short usVBinNumber;             //本高度层速度数据径向的库数
    unsigned short usWBinNumber;             //本高度层谱宽数据径向的库数

    unsigned short usZStartBin;              //强度有效数据开始库数
    unsigned short usVStartBin;              //速度有效数据开始库数
    unsigned short usWStartBin;              //谱宽有效数据开始库数
    unsigned short usRecordNumber;           //本高度层的径向个数
    char DataForm;                           //本高度层径向数据排列方式
    //11＝单要素CorZ
    //12＝单要素UnZ
    //13＝单要素V
    //14＝单要素W
    //21＝CorZ+UnZ
    //22＝CorZ+V+W
    //23＝UnZ+V+W
    //24＝CorZ+UnZ+V+W
    //4X双偏振按要素
    //6X-双偏振多谱勒按要素
    //8X-双波长按要素
    unsigned short usHeight;                 //本高度层海拔高度值,单位1/10米(根据实际需要，改为米)
    unsigned short usEYear;                  //体扫记录结束时间的年(2000-)
    unsigned char ucEMonth;                  //体扫记录结束时间的月(1-12)
    unsigned char ucEDay;                    //体扫记录结束时间的日(1-31)
    unsigned char ucEHour;                   //体扫记录结束时间的时(00-23)
    unsigned char ucEMinute;                 //体扫记录结束时间的分(00-59)
    unsigned char ucESecond;                 //体扫记录结束时间的秒(00-59)
    unsigned char ucETenth;                  //体扫记录结束时间的1/100秒(00-99)
    unsigned short usZBinByte;               //原始强度数据中库长无变化填0
    //原始强度数据中库长有变化填占用字节数
    BINPARAM720A BinRange1[5];                   //5个8字节(强度库长无变化为空字节)
    unsigned short usVBinByte;               //原始速度数据中库长无变化填0
    BINPARAM720A BinRange2[5];                   //5个8字节(速度库长无变化为空字节)
    unsigned short usWBinByte;               //原始谱宽数据中库长无变化填0
    //原始谱宽数据中库长有变化填占用字节数
    BINPARAM720A BinRange3[5];                   //5个8字节(谱宽库长无变化为空字节)
    unsigned char ucProductCode;             //自定义  101=雨强  102=累积雨量
    // 121=ZC 122=垂直液态含水量 123=回波顶高 124=回波底高 125=最大回波强度 126=分层组合反射率
    char DAmp;                               //自定义 数值放大倍数
    short VdlMax;                            //解模糊后的最大可测速度
    short int usIdenDangeNumber;             //危险天气的的个数
    char Spare[111 - 2];                     //备用115个字节
} POLARPRODUCTOBSERVATIONPARAM;
//--------------------------------------------------------------------------------------------------

//--------------------------------------------------------------------------------------------------
//极坐标产品其他参数的结构
typedef struct tagPOLARPRODUCTOTHERINFORMATION
{
    char StationID[2];                       //台站代号
    char Vppitype[10];                       // VOL_PM1  降水模式1
    // VOL_PM2  降水模式2
    // VOL_GM   警戒模式
    // VOL_UPM1 降水模式1(解距离模糊)
    // VOL_UPM2 降水模式2(解距离模糊)
    // VOL_UM   用户自定义体扫
    // PPI      平扫
    // RHI      高扫
    // FFT      FFT
    char Spare[524 - 10];                    //备用字节524-10个
} POLARPRODUCTOTHERINFORMATION;
//--------------------------------------------------------------------------------------------------

//	原始数据块结构
typedef struct tagRADARDATABLOCK
{
    short	sElevation;				//仰角(1/100度)
    USHORT	usAzimuth;				//方位(1/100度)
    unsigned char	ucHour;					//时
    unsigned char	ucMinute;				//分
    unsigned char	ucSecond;				//秒
    ULONG	ulMillisecond;			//秒的小数(0.1毫秒)
    unsigned char	ucCorZ[NUMBEROFBIN];	//经过地物杂波消除的dBZ值=(CorZ-64)/2
    unsigned char	ucUnZ[NUMBEROFBIN];		//未经过地物杂波消除的dBZ值=UnZ/2
    //720A: 未经过地物杂波消除的dBZ值=(UnZ-64)/2
    char	cV[NUMBEROFBIN];		//速度值(单位为最大可测速度的1/127)
    //	正值表明远离雷达站
    //	负值表明朝向雷达站
    unsigned char	ucW[NUMBEROFBIN];		//谱宽值(单位为最大可测速度的1/512)
//    short	ucCorZ[NUMBEROFBIN];	//经过地物杂波消除的dBZ值=(CorZ-64)/2
//    short	ucUnZ[NUMBEROFBIN];		//未经过地物杂波消除的dBZ值=UnZ/2
//    //720A: 未经过地物杂波消除的dBZ值=(UnZ-64)/2
//    short	cV[NUMBEROFBIN];		//速度值(单位为最大可测速度的1/127)
//    //	正值表明远离雷达站
//    //	负值表明朝向雷达站
//    short	ucW[NUMBEROFBIN];		//谱宽值(单位为最大可测速度的1/512)
} RADARDATABLOCK;

typedef struct _RadarHeader720A_
{
    FILEIDENTIFIERS720A FileIds;
    RADARSITE720A SiteInfo;
    RADARPERFORMANCEPARAM720A PerformanceInfo;
    RADAROBSERVATIONPARAM720A ObservationInfo;
    //POLARPRODUCTOBSERVATIONPARAM PolarObservationInfo;
    //POLARPRODUCTOTHERINFORMATION PolarOtherInfo;
    char Spare[562];
} RadarHeader720A;

#pragma pack()


//class ARCHIVE
//{
//public:
//    ARCHIVE();
//    int MakePro(string input_str, SWROriginFileHeader &h, HISRADIALDATA *d);

//private:
//    void readheader(SWROriginFileHeader &h);
//    int loadSiChuangFile(const char *fileName);
//    void convertSiChuangHeaderToVTB(SWROriginFileHeader &h);
//    void convertSiChuangBufferToVTB(SWROriginFileHeader &h, HISRADIALDATA *d);
//    int getLayerInfo(RadarHeader720A radarHeader720A);
//    //int getBB(const char *fileName);

//private:
//    //int m_BB;
//    int m_LayerNumber;	// 扫描层数
//    int m_ScanType;//扫描任务类型，0-体扫，1-单层PPI，2-RHI
//    RadarHeader720A m_radarHeader720A;
//    vector<vector<RADARDATABLOCK> > m_720ADataLst;
//};

#endif // ARCHIVE_H
