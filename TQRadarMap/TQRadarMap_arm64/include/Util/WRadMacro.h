#pragma once

#define BIT(n) 1<<(n)

// 底层通讯协议

// 天气雷达
// 基本控制指令
#define STATE_ON           1
#define STATE_OFF          0
#define STATE_WAIT         2

#define WRAD_SWITCH_ALL             10000   // 一键开关机
#define WRAD_SWITCH_EMITTER         10001   // 发射机控制
#define WRAD_SWITCH_RECEIVER        10002   // 接收机控制
#define WRAD_SWITCH_AIRCON          10003   // 空调控制
#define WRAD_SWITCH_JOIN_NET        10010   // 加入退出组网控制

#define WRAD_POWER_ALL              10050   // 所有子系统供电
#define WRAD_POWER_EMITTER          10051   // 发射机供电控制
#define WRAD_POWER_SERVO            10052   // 伺服供电控制
#define WRAD_POWER_SYNTHETIC        10053   // 综合供电控制
#define WRAD_POWER_COOLING          10054   // 冷却系统供电控制

#define WRAD_DATA_UPLOAD            10070   // 雷达数据开启上传
#define WRAD_AUTHORITY_SWITCH       10071   // 控制权限交割 0: RCM 1：协同控制

// 雷达标定和测试
#define WRAD_SUN_NORTH              10100   // 太阳法正北
#define WRAD_TEST_DYNAMIC           10101   // 动态测试
#define WRAD_TEST_AUTO              10102   // 自动测试（强度、速度、噪声系数）
#define WRAD_TEST_COHERENCE         10103   // 相干测试
#define WRAD_TEST_FILTER            10104   // 滤波抑制度测试


// 雷达基本设置
#define WRAD_SET_AIRCON_TEMP        11000   // 设置空调温度
#define WRAD_SET_AIRCON_HUMI        11001   // 设置空调湿度
#define WRAD_SET_AIRCON_MODE        11002   // 设置空调工作模式
#define WRAD_SET_AIRCON_OPS         11003   // 设置空调操作模式

// 查询
#define WRAD_QEURY_STATUS           0x0000  // 查询启停状态
#define WRAD_QEURY_POWER_MODE       0x0001  // 查询配电控制模式
#define WRAD_QEURY_POWER_INFO       0x0002  // 查询电源信息
#define WRAD_QEURY_POWER_STATUS     0x0003  // 查询子系统供电状态
#define WRAD_QEURY_AMBIENT_INFO     0x0004  // 查询环境温湿度信息
#define WRAD_QEURY_SYSTEM_BIT       0x0005  // 查询子系统BIT状态
#   define WRAD_SYSTEM_BIT_SERVO        0x0000  // 伺服子系统
#   define WRAD_SYSTEM_BIT_EMITTER      0x0001	// 发射机子系统
#   define WRAD_SYSTEM_BIT_RECEIVER     0x0002	// 接收机子系统
#   define WRAD_SYSTEM_BIT_COOLING      0x0003	// 冷却子系统
#   define WRAD_SYSTEM_BIT_AIRCON       0x0004  // 空调子系统
#   define WRAD_SYSTEM_BIT_ALL          0xFFFF  // 所有子系统
#define WRAD_QEURY_SITE_INFO        0x0006  // 查询站址信息
#define WRAD_QEURY_EMITTER_STATUS   0x0007  // 查询发射机高压状态

// 雷达子系统
#define WRAD_BIT_MASK_SYS_SERVO      0
#define WRAD_BIT_MASK_SYS_EMITTER    1
#define WRAD_BIT_MASK_SYS_RECEIVER   2
#define WRAD_BIT_MASK_SYS_COOLING    3
#define WRAD_BIT_MASK_SYS_AIRCON     4



