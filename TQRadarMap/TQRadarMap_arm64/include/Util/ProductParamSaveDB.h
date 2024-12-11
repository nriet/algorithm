#ifndef CPRODUCTPARAMSAVEDB_H
#define CPRODUCTPARAMSAVEDB_H
#include <queue>
#include <Ice/Ice.h>
#include <IceUtil/Monitor.h>
#include <IceUtil/Mutex.h>
#include <IceStorm/IceStorm.h>
#include <NTaskQueueBase.h>
#include "CIceUtil.h"
#include "ProductTask.h"
#include "struct_ProductParamDef.h"
#include "Mercator.h"
#include <QDateTime>
#include <QString>
class CProductParamSaveDB : public CTaskQueueBase
{
public:
    CProductParamSaveDB(Ice::CommunicatorPtr&);
    virtual ~CProductParamSaveDB() override;
    virtual void run() override;
    void destroy();
    void addProductParamInfoSaveQueue(ProductDBSaveTask&);
    void addProdLatlonSaveQueue(ProductLatLonSaveTask&);
    void addProdPathInfoSaveQueue(ProdPathSaveTask&);
    void addRecPPIPathInfoSaveQueue(ProdPathSaveTask&);
private:
    IceUtil::Monitor<IceUtil::Mutex> m_Monitor;
    bool m_bDone;
    std::string m_strName;
    int m_nDebugLevel = 0;
    std::queue<ProductDBSaveTask> m_qProdInfoSaveDB;
    std::queue<ProductLatLonSaveTask> m_qProdLatlonSaveDB;
    std::queue<ProdPathSaveTask> m_qPreSavedProductPath;
    std::queue<ProdPathSaveTask> m_qPreSavedRecPPIPath;
    int stiMaxValThreshold;
    int stiVilThreshold;
private:
   void OnSaveProductParamTask(ProductDBSaveTask&);
   void OnSaveProductLatlonTask(ProductLatLonSaveTask&);
   void OnSaveProductInfoSavePath(ProdPathSaveTask&, int standard = 0);
   void OnSaveRecPPIInfoSavePath(ProdPathSaveTask&);
   void parse_HiParams(ProductDBSaveTask& task);
   void parse_StiParams(ProductDBSaveTask& task);
   void parse_MParams(ProductDBSaveTask& task);
   void parse_TvsParams(ProductDBSaveTask& task);
   void longLatOffset(float startlon, float startlat, float az, float dst,float& lon,float& lat);
   void doLoadConfiguration();
   time_t time_convert(int year, int month, int day, int hour,int minute, int second);
};

typedef IceUtil::Handle<CProductParamSaveDB> CProdcutParamSaveTaskQueuePtr;

#endif // CPRODUCTPARAMSAVEDB_H
