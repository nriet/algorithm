#ifndef STRUCT_STRATEGYDEF_H
#define STRUCT_STRATEGYDEF_H
#include <string>
#include <vector>
using namespace  std;

typedef  struct{
    int id;                 // 数据库中主键值
    char name[50];          // 模式名称
    int priority;           // 模式优先级
    int trig;               // 模式触发等级
    int sync;               // 是否同步扫描
    int status;             // 模式有效状态
    char description[4000]; // 模式描述信息
    int insertTime;
    char insertMan[50];
    int lastUpdateTime;
    char lastUpdateMan[50];
} pattern;

typedef  struct{
    int id;
    int patternId;		// 模式索引
    char equipType[256];	// 设备类型名称
    char equipMark[256];	// 设备型号名称
    int distanceId;		// 距离索引
    int scanId;			// 扫描模式索引
    int status;
    char description[400];
    int serialNo;
    short repeatTimes;
    int insertTime;
    char insertMan[50];
    int lastUpdateTime;
    char lastUpdateMan[50];
} pattern_st;

typedef  struct{
    int id;
    int patternStId;
    int paramId;
    double paramValue;
    int status;
    char description[400];
    int serialNo;
    int insertTime;
    char insertMan[50];
    int lastUpdateTime;
    char lastUpdateMan[50];
} pattern_st_param;

typedef  struct{
    int id;
    char code[50];
    char alias[50];
    int status;
    char desc[400];
    int insertTime;
    char insertMan[50];
    int lastUpdateTime;
    char lastUpdateMan[50];
} tag_distance;

typedef  struct{
    int id;
    char code[50];
    char alias[50];
    int status;
    char desc[400];
    int insertTime;
    char insertMan[50];
    int lastUpdateTime;
    char lastUpdateMan[50];
} tag_scan_mode;

typedef  struct{
    int id;
    char code[50];
    char alias[50];
    int status;
    char desc[400];
    int insertTime;
    char insertMan[50];
    int lastUpdateTime;
    char lastUpdateMan[50];
} tag_scan_param;

typedef  struct{
    int id;
    char name[256];
    int status;
    char desc[400];
    int insertTime;
    char insertMan[50];
    int lastUpdateTime;
    char lastUpdateMan[50];
} tag_trig_cond;

typedef  struct{
    int code;
    char name[256];
} tag_param;

typedef enum {
   SA_X_NoReflect = 0,
   X_SA_Reflect = 1,
   X_Rain = 2,
   X_Storm = 4
}ST_PRODUCT_ID;

typedef  enum{
   IDEL_MODE,
   GUARD_MODE,
   RAIN_MODE,
   STORM_MODE
}ST_SYS_WORK_MODE;

typedef  enum
{
    QUERY_TAG,
    QUERY_STRATEGY,
}ST_QUERY_T;

typedef  enum
{
    REQUEST_ST_UPDATE,
    REQUEST_ST_ADD,
    REQUEST_ST_DELETE,
}ST_REQUEST_T;
//
typedef enum
{
    PARAM_ELE_BEGIN = 1,
    PARAM_ELE_MID = 2,
    PARAM_ELE_END = 3,
    PARAM_AZI_BEGIN = 4,
    PARAM_AZI_MID = 5,
    PARAM_AZI_END = 6,
    PARAM_DSP_BINWIDTH = 7,
    PARAM_DSP_PRF = 8,
    PARAM_DSP_PRFRATIO = 9,
    PARAM_DSP_PROCESSMODE = 10,
    PARAM_DSP_PULSE = 11,
    PARAM_SERVO_SPEED = 12,
    PARAM_DSP_THR_NOISE_H = 13,
    PARAM_DSP_THR_NOISE_V = 14,
    PARAM_DSP_THR_SQI = 15,
    PARAM_DSP_THR_SCR = 16,
    PARAM_DSP_DZ_M = 17,    // dead zone mode
}PARAM_TYPE;

typedef enum
{
    PRF_4000_30 = 0,
    PRF_2000_60 = 1,
    PRF_1100_120 = 2,
    PRF_400_240 = 3,
}PARAM_TBL_PRF;

typedef enum
{
    PRF_RATIO_1_1 = 0,
    PRF_RATIO_3_2 = 1,
    PRF_RATIO_4_3 = 2,
    PRF_RATIO_5_4 = 3,
}PARAM_TBL_PRF_RATIO ;

typedef enum
{
    BINWIDTH_30 = 0,
    BINWIDTH_60 = 1,
    BINWIDTH_120 = 2,
}PARAM_TBL_BINWIDTH;

typedef enum
{
    PROCESS_MODE_PPP = 0,
    PROCESS_MODE_FFT = 1,
    PROCESS_MODE_DPRF = 2,
    PROCESS_MODE_D = 3,
    PROCESS_MODE_DD = 4,
}PARAM_TBL_PROCESS_MODE;

typedef enum
{
    PULSE_16 = 0,
    PULSE_32 = 1,
    PULSE_64 = 2,
    PULSE_128 = 3,
    PULSE_256 = 4,
}PARAM_TBL_PULSE ;

typedef enum
{
    SCAN_PPI = 1,
    SCAN_RHI = 2,
    SCAN_VCP = 3,
    SCAN_SECTOR = 4,
}SCAN_TYPE;

typedef enum
{
    ST_NONE_TASK,
    ST_RHI_WORKING,
    ST_PPI_WORKING,
    ST_VTB_WORKING,
    ST_WORK_FAILED,
    ST_FINISH,
}SCAN_TASK_STATE;

typedef enum
{
    NEAREST = 1,  // nearest radar
    INRANGE = 2,  // radar in range
    OUTRANGE = 3, // radar out of range
    ALLRANGE = 4,
}DISTANCE_TAG;

typedef enum
{
    TRIG_COND_NO_REFLECT = 0,
    TRIG_COND_REFLECT = 1,
    TRIG_COND_RAIN = 2,
    TRIG_COND_VIL_OVER = 3,
    TRIG_COND_REF_OVER = 4,
    TRIG_COND_MESO_MAX = 5
}TRIG_CONDITION_TAG;

#define STATUS_ACTIVE   1
#define STATUS_INACTIVE 0

// strategy params == CUT configure
typedef struct
{
    int id;
    int status;
    PARAM_TYPE code;
    double value;
    int serialNo;
    string desc;
}strategy_params;

// strategy == TASK configure
typedef  struct{
    int id;
    string equipType;
    string equipMark;
    DISTANCE_TAG distanceCond;   // distance to target
    SCAN_TYPE scanType;     // PPI or RHI
    int status;              // active status 0: deactive 1: active
    string desc;
    int serialNo;
    short repeatTimes;        // repeat count
    std::vector<strategy_params> paramList;
} model_strategy;

typedef struct
{
    int id;
    string alias;
    int priority;
    int trig;
    int sync;
    int status;
    string desc;

    std::vector<model_strategy> strategyList;
} wrad_scan_model;

typedef std::vector<wrad_scan_model> wrad_scan_modelSeq;

#endif // STRUCT_STRATEGYDEF_H
