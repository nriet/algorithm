#pragma once
#include <string>
#include "Singleton.h"
#include "Database/dataprovider.h"
#include "Database/common.h"
#include "Database/DBMacro.h"
#include "Database/dalexcept.h"

#define MYSQL_PROC_RECORD_LOG  "recordlog"
#define MYSQL_PROC_RECORD_PRODUCT   "recordproduct"

typedef struct
{
    int type;
    char name[256];  //
    char producer[256];
    char desc[500];
    int time;
}ProductInfo;

typedef struct
{
    char name[256];  //
    int type;
    int level;
    char log[500];
}LogInfo;

class CDBUtil : public Singleton<CDBUtil>
{
public:
    CDBUtil();
    ~CDBUtil();

    bool Initilize(std::string host,std::string user,std::string pass,std::string db,int port);
    void Shutdown(void);
    void Update(void);

    bool recordLog(LogInfo&);
    bool recordProduct(ProductInfo&);
private:
    DataProvider *m_DataProvider;
};

#define DBInstance CDBUtil::getSingleton()
