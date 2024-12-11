#pragma once
#include <string>
#include "Singleton.h"
#include "struct_ProductParamDef.h"
//#include "Database/dataprovider.h"
//#include "Database/common.h"
//#include "Database/DBMacro.h"
//#include "Database/dalexcept.h"
//#include <iosfwd>
#include <sstream>



//#include "DBConf.h"
#include <QDebug>
#include <time.h>

#include "NrietDBCommonInterface.h"


#define MYSQL_PROC_RECORD_LOG  "recordlog"
#define MYSQL_PROC_RECORD_PRODUCT   "recordproduct"
#define MYSQL_PRODUCT_HIPARAM    "xkz_tqld_hi"
#define MYSQL_PRODUCT_STIPARAM   "xkz_tqld_sti"
#define MYSQL_PRODUCT_MPARAM     "xkz_tqld_m"
#define MYSQL_PRODUCT_TVSPARAM   "xkz_tqld_tvs"
#define MYSQL_PRODUCT_LATLON     "t_latlon"
#define MYSQL_PRODUCT_PATH     "t_product_path"

//typedef struct
//{
//    int type;
//    char name[256];  //
//    char producer[256];
//    char desc[500];
//    int time;
//}ProductInfo;

//typedef struct
//{
//    char name[256];  //
//    int type;
//    int level;
//    char log[500];
//}LogInfo;

class CDBIntf : public Singleton<CDBIntf>
{
public:
    CDBIntf();
    ~CDBIntf();

    bool Initilize(std::string DBType,std::string host,std::string user,std::string pass,std::string db,int port);
    void Shutdown(void);
    void Update(void);

    bool recordLog(LogInfo&);
    bool recordProduct(ProductInfo&);
    bool recordProductLatlon(ProdLatlon&);
    bool recordHiProductParam(HiParam&);
    bool recordStiProductParam(StiParam&);
    bool recordmProductParam(MParam&);
    bool recordProductPathInfo(ProdPathInfo&);
    bool recordRecPPIPathInfo(ProdPathInfo&);

private:
    //DataProvider *m_DataProvider;
    CNrietDBCommonInterface * (*pGetAlgoInstance)(std::string);
    CNrietDBCommonInterface *m_pDBInterface=nullptr;
};

#define DBOperator CDBIntf::getSingleton()
