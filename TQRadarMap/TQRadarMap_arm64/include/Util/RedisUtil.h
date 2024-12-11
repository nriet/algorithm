#pragma once

#include <memory>
#include <mutex>
#include <queue>
#include <sstream>
#include <map>
#include "HiRedis/hiredis.h"
#include "equipmentInfo.h"
#include "Singleton.h"

#define DEFAULT_REDIS_EXPIRE_DURATION   30  // 1min

class CRedisUtil:public Singleton<CRedisUtil>
{
public:
    CRedisUtil();
    ~CRedisUtil();
    bool Initilize(std::string&,std::string&,int&, int&);
    void Shutdown(void);

    std::vector<std::string>stringSplit(const std::string&, const char);
    std::string retrieveDevIdByToken(std::string &);
    bool retrieveRadarByToken(std::string &, WeatherRadar&);
    std::string retrieveRadarTokenById(std::string&);
    bool retrieveRadarTokenMap(std::map<std::string, std::string>&);
    bool saveKeyValue(std::string&, std::string&);
    bool saveKeyValueWithExpire(std::string&, std::string&, int);
    bool removeKeyValue(std::string& key);
    bool refreshKey(std::string& key);
    bool isExistKey(std::string& key);
    //
    bool Del(std::string& key);
    // HASH
    bool HExist(std::string&, std::string&);
    bool HDel(std::string&, std::string&);
    bool HSet(std::string&, std::string&, std::string&);
    bool HGet(std::string&, std::string&, std::string&);
    bool HKeys(std::string&, std::vector<std::string>&);
    bool HIncrby(std::string&, std::string&, std::string&);

private:
    std::queue<redisContext *> m_client;
    bool getStringValue(redisReply*, std::string&);
    bool executeCmd(const std::string& cmd, std::string& response);
    bool executeCmd(const std::string& cmd, std::vector<std::string>& response);
    bool executeCmd(char* cmd, std::string& response);

    redisContext *createContext();
    void releaseContext(redisContext* ctx, bool active);
    bool checkStatus(redisContext* ctx);
    std::string _password;
    std::string _ip;
    int _port;
    int _timeout;
    time_t m_beginInvalidTime;
    static const int m_maxReconnectInterval = 3;

    std::mutex _mutex;
};

#define RedisUtilSTon CRedisUtil::getSingleton()
