#pragma once

#include <vector>

#ifdef STRUCT_PACKED
#undef STRUCT_PACKED
#endif

#ifdef __GNUC__
#define STRUCT_PACKED __attribute__((packed))
#else
#   pragma pack(push,1)
#   define STRUCT_PACKED
#endif

#define PACKSIZE 30000

typedef	struct STRUCT_PACKED
{
    unsigned short header;                 //报文头 固定值；为：0xFBFB
    unsigned short cmdCode;              //报文标识（+2B：表示大类，+3B：标识子类，无子类为0x00）
    unsigned short serialNum;              //报文序列号 每发一帧，计数加1；0～65535循环（高字节在前）
    unsigned short length;                 //帧长包含除报文头之外的所有的字节数（高字节在前）
    unsigned char sourceCode;             //信息源
    unsigned char destCode;               //信息宿
    unsigned char totalPackNum;           //包总数
    unsigned char currentPackID;           //分包序号
    unsigned short systemCode;           //分系统标识
    unsigned short versionCode;           //程序版本号
}ST_LDB2FILE_PackHead;

typedef	struct STRUCT_PACKED
{
    char TaskUID[40];           //唯一任务标识
    int LongitudeValue;           //天线所在经度的数值，以1/10000度为计数单位，东经（E）为正，西经（W）为负
    int LatitudeValue;           //天线所在纬度的数值，以1/10000度为计数单位，北纬（N）为正，南纬（S）为负
    int Height;           //天线海拔高度
    unsigned char DataType;           //本层观测要素：1=单强度，2=四要素 单PRF，3=四要素 双PRF
    unsigned short MaxV;           //本层的最大可测速度，计数单位：厘米/秒
    char DataForm;           //本层径向中的数据排列方式
    short storeType;           //存储数据类型，从最低位起每一位均与DataForm排列的要素相对应，0：1字节存储，1：2字节存储
    unsigned short StartBin;           //有效数据开始库
    unsigned short RHIA;           //做RHI时的所在方位角，计数单位为1/100度，做PPI和立体扫描时为65535
    short RHIL;           //做RHI时的最低仰角，计数单位为1/100度，做其他扫描时为-32768
    short RHIH;           //做RHI时的最高仰角，计数单位为1/100度，做其他扫描时为-32768
    unsigned short Level_sum;           //扫描总层数
    unsigned char ScanType;           //扫描类型 0：未定义 1：定点 2：PPI 3：VOL 4：扇扫 5：立体扇扫 6：RHI 7：立体RHI
}ST_STATE_DISPLY;

typedef	struct STRUCT_PACKED
{
    unsigned short fs_beta[10];           //发射beta码
}ST_FSBETACODE;

typedef	struct STRUCT_PACKED
{
    unsigned int ScanLayerNumericalOrder;           //扫描层流水号 生命周期内层的流水号
    unsigned char WaveSequenceNum;           //波位序号
    unsigned char BeamSum;           //波束总数
    unsigned char BeamSequenceNum;           //波束序号
//    unsigned char LayerNum;           //层号，从0开始，0xFF标识为中间过渡数据
    unsigned short LayerNum;           //层号，从0开始，0xFF标识为中间过渡数据
    unsigned char ScanNodeIdentifying;           //扫描节点标识
    unsigned short Ku_Number;           //库数
    unsigned short KU_length;           //库长 猜测厘米
    unsigned char DataScaleEstimate;           //数据规模估值
    ST_STATE_DISPLY task_state;
    ST_FSBETACODE  beta_FS;
}ST_LineDataBlockInfo;

typedef	struct STRUCT_PACKED
{
    short Elev;           //计数单位为1/100度
    unsigned short Az;           //计数单位为1/100度
    unsigned char Hh;           //
    unsigned char Min;           //
    unsigned char Ss;           //
    unsigned int Ms;           //
}ST_RadialLDB;

typedef struct
{
    std::vector<short> bindataZ;
    std::vector<short> bindataUnZ;
    std::vector<short> bindataV;
    std::vector<short> bindataW;
    std::vector<short> bindataSNR;
}ST_RadialDatas;

typedef struct
{
    unsigned short tail;//报文尾 固定值；为0xBFBF
}ST_PACKTAIL;

typedef struct
{
    ST_LDB2FILE_PackHead packHead;
    ST_LineDataBlockInfo preLDBHead;
    ST_RadialLDB LDBHead;
    ST_RadialDatas binDatas;
    ST_PACKTAIL packTail;
}ST_RADIAL_PACK_KX;


#ifdef __GNUC__
#else
#   pragma pack(pop)
#endif
