#ifndef SHIPRADARSTRUCT_H_
#define SHIPRADARSTRUCT_H_

#include <vector>

#ifdef __GNUC__
#define STRUCT_PACKED __attribute__((packed))
#else
#   pragma pack(push,1)
#   define STRUCT_PACKED
#endif

//new data from 002
#define DATA_LEN	1024		//数据最多1024个

struct RcordHeader
{
    unsigned short  ID;
    unsigned short  buff_len;
    unsigned short  Bak[4];
    RcordHeader() {}
};

struct NetDatagramHeader//8short
{

    char DatagramCounter;	//数据包打包个数	1～255
    char DatagramID	;	//标识（0xff内部报文,其余为外部报文）	0xff
    short PackLen	;	//长度	1～65535
    int PackTime	;	//时间	统一为北京时间，发送节点填写，为此报文的发送时刻（精度：0.1ms）。
    int PackTypeID	;	//报文编号 唯一标识报文类型及数据内容数据格式。（内部数据打包时只允许同id的数据进行打包，具体协议及编号待定）
    char  SendNodeCounter;  //发送节点（模块）编号	0～255
    char  RecvNodeCounter;  //接收节点（模块）编号	0～255
    char  SendSeqID	;	//发送序列号SN	0～255
    char  bak	;	//备用
};

typedef struct
{
    unsigned short PRF1;   //本层第一脉冲重复频率，计数单位为1/10Hz【2】			？
    unsigned short PRF2;   //本层第二脉冲重复频率，计数单位为1/10Hz【2】			？

    unsigned short PluseW;   //本层的脉冲宽度，计数单位为微秒【2】					？按波形
    unsigned short MaxV;   //本层向的最大可测速度，计数单位为厘米/秒【2】			？按重频

    unsigned short MaxL;   //本层向的最大可测距离，以10米为计数单位【2】			作用距离
    unsigned short BinWidth; //本层向数据的库长，以1/10米为计数单位【2】			300/600米？

    unsigned int  CutIndex;		 // 雷达扫描的PPI序号，此序号用于径向传输时的数据匹配，在网络传输出现错误时及时修正【4】

    unsigned short BinNum;     //本层扫描的库数【2】								距离/裤长
    char DataForm;                //本层中的数据排列方式：【1】						24
    //11 单要素排列 ConZ
    //12 单要素排列 UnZ
    //21 按要素排列 ConZ+UnZ
    //22 按要素排列 ConZ+V+W
    //23 按要素排列 UnZ+V+W
    //24 按要素排列 ConZ+UnZ+V+W
    unsigned char ElevIndex;		 // 体扫时，本次扫描位于体扫中的序号（第几组扫描）【1】   XXX雷达：1--5

    unsigned char Filter;								//滤波器代号【1】
    unsigned char Polarizations;    //极化状况【1】										1
    //0=水平
    //1=垂直
    //2=双线偏振
    //3=其他待定
    unsigned short SideLobe;        //第一旁瓣，以0.01dB为计数单位【2】					25dB


    int AntennaG;                //天线法向增益，以0.01dB为计数单位【4】  				41dB
    unsigned short BeamH;        //法线方向上的波束宽度，以1/100度为计数单位【2】		1.8°
    unsigned short BeamL;        //切线方向上的波束宽度，以1/100读为计数单位【2】		1.9°

    int Power;                     //雷达脉冲峰值功率，以瓦为单位【4】					177kw
    int WaveLength;                //波长，以微米为计数单位【4】						9.5cm
    unsigned short LineA;   //接收机动态范围，以0.01dB为计数单位【2】					80dB
    short LineMinPower;     //接收机最小可测功率，计数单位为0.01dBm【2】				-90dBm

    char ClutterP;          //地杂波消除阈值，计数单位为0.2dB【1】						45dB
    char ClutterS;          //海杂波消除阈值，计数单位为0.2dB【1】						35dB
    unsigned char VelocityP;     //速度处理方式【1】									2
    //0=无速度处理
    //1=PPP
    //2=FFT
    unsigned char FilterP;        //地杂波消除方式【1】									1
    //0=无地杂波消除
    //1=地杂波扣除法
    //2=地杂波+滤波器处理
    //3=滤波器处理
    //4=谱分析处理
    //5=其他处理法

    unsigned char FilterS;        //海杂波消除方式【1】									1
    //待定
    unsigned char NoiseT;          //噪声消除阈值（0-255）【1】
    unsigned char IntensityR;      //强度估算是否进行了距离订正【1】					0 1满朝确认
    //0=无
    //1=以进行了距离订正
    unsigned char SType;        //工作方式【1】        对应XXX雷达						2 4 5
    //1= 搜索模式      //1=兼容模式PPI
    //2= 单强度PPI    //2=兼容模式体扫
    //3= 单强度RHI    //3=专用模式PPI
    //4= 强度速度PPI  //4=专用模式体扫
    //5= 体扫

    unsigned short SYear;            //观测记录开始时间的年（2000-）【2】
    unsigned char SMonth;           //观测记录开始时间的月（1-12）【1】
    unsigned char SDay;             //观测记录开始时间的日（1-31）【1】

    unsigned char SHour;            //观测记录开始时间的时（00-23）【1】
    unsigned char SMinute;           //观测记录开始时间的分（00-59）【1】
    unsigned char SSecond;           //观测记录开始时间的秒（00-59）【1】
    unsigned char Calibration;        //标校状态【1】								0
    //0=无标校
    //1=自动标校
    //2=一星期内人工标校
    //3=一月内人工标校
    //4=开机自动标校
    //其他码不用

    unsigned char WeatherMode;	 // 天气状况【1】
    unsigned char Ambiguousp;     //本层退模糊状态【1】								2
    //0=无退模糊状态
    //1=软件退模糊
    //2=双T退模糊
    //3=批式退模糊
    //4=双T+软件退模糊
    //5=批式+软件退模糊
    //6=双PPI退模糊
    //9=其他方式

    unsigned short RHIA;           //做RHI时的所在方位角，计数单位为1/100度，做PPI和立体扫描时为65535【2】

    short RHIL;                  //做RHI时的最低仰角，计数单位为1/100度，做其他扫描时为-32768【2】
    short RHIH;                  //做RHI时的最高仰角，计数单位为1/100度，做其他扫描时为-32768【2】
//above  34 short
    char Reserved[24];                //保留【24】
    char Reserved1[24];             //保留【24】
    char Reserved2[24];             //保留【24】
}RADARDATAHEADER;   /* 雷达数据头【140】 */

typedef struct LinDataBlock_tag
{
    unsigned short CutIndex;			 /* 雷达扫描的PPI序号，此序号用于径向传输时的数据匹配，在网络传输出现错误时及时修正【4】*/
    unsigned char beiyong1;			//beiyong
    unsigned char lastRadial;		/* 是否是本次扫描的最后一个径向：1，是。【1】*/
    short Elev;						/*仰角，计数单位1/100度【2】*/
    unsigned short Az;				/*方位，计数单位1/100度【2】*/
    char Longtitude[16];			/*经度，以字符串记录【16】*/
    char Latitude[16];				/*纬度，以字符串记录【16】*/
    float Vs;						/*纵摇，计数单位【4】*/
    float Hs;						/*横摇，计数单位【4】*/
    unsigned short Course;			/*航向，计数单位【2】*/
    unsigned short Nv;				/*舰速，计数单位【2】*/
    unsigned char CorZ[DATA_LEN];	/*经过地物杂波消除的dBZ值=（CorZ-64）/2【1024】*/
    unsigned char UnZ[DATA_LEN];	/*不经过地物杂波消除的dBZ值=（UnZ-64）/2【1024】*/
    char          V[DATA_LEN];				/*速度值，计数单位为最大可测速度的1/127【1024】*/
    /*   正值表示远离雷达的速度，负值表示朝向雷达的速度*/
    /*         无回波时计-128*/
    unsigned char W[DATA_LEN];  /*谱宽值，计数单位为最大可测速度的1/512【1024】*/
    /*     无回波时计零*/
}LinDataBlock;   /* 径向数据【4149】 */

typedef struct ShipRadarLayer_tag
{
    RADARDATAHEADER layerHeader;
    std::vector<LinDataBlock> layerData;
}ShipRadarLayer;

typedef struct ShipRadarVol_tag
{
    unsigned short layerNum;//有多少层
    std::vector<unsigned short> radialNumList;//每一层的径向数队列
    std::vector<ShipRadarLayer> volData;//每层对应的径向队列
}ShipRadarVol;

#ifdef __GNUC__
#else
#   pragma pack(pop)
#endif
#endif /*SHIPRADARSTRUCT_H_*/
