/**********************************************************************
* Copyright 2023-xxxx Nriet Co., Ltd.
* All right reserved. See COPYRIGHT for detailed Information
*
* Alternatively, you may use this file under the terms of the NRT license
* as follows:
**
* "Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions are
* met:
*   * Redistributions of source code must retain the above copyright
*     notice, this list of conditions and the following disclaimer.
*   * Redistributions in binary form must reproduce the above copyright
*     notice, this list of conditions and the following disclaimer in
*     the documentation and/or other materials provided with the
*     distribution.
*   * Neither the name of The NRT Company Ltd nor the names of its
*     contributors may be used to endorse or promote products derived
*     from this software without specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
* "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
* LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
* A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
* OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
* SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
* LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
* DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
* THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
* (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
* OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
*
* File:ProductParamSaveDB.cpp
* Author:Nriet
* time 2023-05-24
*************************************************************************/
#include "ProductParamSaveDB.h"
#include "struct_WeatherRadarProduct.h"
#include "DBIntf.h"
#include "NDebug.h"
#include "IniParser/INIParser.h"

/**
 * @brief CProductParamSaveDB::CProductParamSaveDB
 * @param com
 */
CProductParamSaveDB::CProductParamSaveDB(Ice::CommunicatorPtr& com)
{
    m_bDone = false;
    m_pCommunicator = com;
    m_pLogger = com->getLogger();
    m_nDebugLevel = 0;
    m_pTopicMgr = CIceUtilSton.getTopicManager();
    m_strName = "productParamSaveQueue";
}

/**
 * @brief CProductParamSaveDB::~CProductParamSaveDB
 */
CProductParamSaveDB::~CProductParamSaveDB()
{

}

/**
 * @brief CProductParamSaveDB::doLoadConfiguration
 */
void CProductParamSaveDB::doLoadConfiguration()
{
    INIParser parser;
    if(parser.ReadINI("../conf/Services/productFactory.ini"))
    {
        stiMaxValThreshold = atoi(parser.GetValue("Common", "MaxValThreshold").c_str());
        stiVilThreshold = atoi(parser.GetValue("Common", "StiVilThreshold").c_str());
    }
    else
    {
        NRIET_DEBUG_ERROR(m_nDebugLevel, m_pLogger, "ProductParamSaveDB Load configuration fail");
    }
}

/**
 * @brief CProductParamSaveDB::run
 */
void CProductParamSaveDB::run()
{
//    m_pLogger->trace(m_strName,"run");
    NRIET_DEBUG_INFO(m_nDebugLevel,m_pLogger,m_strName,"run");

    IceUtil::Monitor<IceUtil::Mutex>::Lock lock(m_Monitor);
    while(!m_bDone)
    {
        if(false == lock.acquired())
            lock.acquire();

        if((m_qProdInfoSaveDB.size() == 0) && (m_qProdLatlonSaveDB.size() ==0) && (m_qPreSavedProductPath.size() == 0) && (m_qPreSavedRecPPIPath.size() == 0))
            m_Monitor.wait();

        if(m_bDone) break;

        if(m_qProdInfoSaveDB.size() > 0){
            auto task = m_qProdInfoSaveDB.front();
            m_qProdInfoSaveDB.pop();
            lock.release();
            OnSaveProductParamTask(task);
        }
        else if(m_qProdLatlonSaveDB.size() > 0){
            auto task = m_qProdLatlonSaveDB.front();
            m_qProdLatlonSaveDB.pop();
            lock.release();
            OnSaveProductLatlonTask(task);
        }
        else if(m_qPreSavedRecPPIPath.size() > 0){
            auto task = m_qPreSavedRecPPIPath.front();
            m_qPreSavedRecPPIPath.pop();
            lock.release();
            OnSaveRecPPIInfoSavePath(task);
        }
        else if(m_qPreSavedProductPath.size() > 0){
            auto task = m_qPreSavedProductPath.front();
            m_qPreSavedProductPath.pop();
            lock.release();
            OnSaveProductInfoSavePath(task);
        }
    }
//    this->m_pLogger->trace(m_strName, "exit");
    NRIET_DEBUG_INFO(m_nDebugLevel,m_pLogger,m_strName,"exit");

}

/**
 * @brief CProductParamSaveDB::OnSaveProductLatlonTask
 * @param task
 */
void CProductParamSaveDB::OnSaveProductLatlonTask(ProductLatLonSaveTask& task)
{
    ProdLatlon latlonparamDB;
    latlonparamDB.stationId = get<0>(task);
    latlonparamDB.datetimeStr = get<1>(task);
    latlonparamDB.dateStr = atoi(get<1>(task).substr(0,8).c_str());
    latlonparamDB.productCode = get<2>(task);
    latlonparamDB.des = get<3>(task);

    qint64 temptime = QDateTime::fromString(QString::fromStdString(get<1>(task)),"yyyyMMddhhmmss").toMSecsSinceEpoch();
    latlonparamDB.milliSecond = temptime;
    if(DBOperator.recordProductLatlon(latlonparamDB))
        NRIET_DEBUG_INFO(m_nDebugLevel, m_pLogger, m_strName, "Record latlon Product Params done");
    else
        NRIET_DEBUG_ERROR(m_nDebugLevel, m_pLogger, "Record latlon Product Params fail");
}

/**
 * @brief CProductParamSaveDB::OnSaveProductParamTask 接收产品参数
 * @param task
 */
void CProductParamSaveDB::OnSaveProductParamTask(ProductDBSaveTask& task)
{
    int prodType = get<4>(task);
    switch (prodType) {
    case PTYPE_HI:
        parse_HiParams(task);
        break;
    case PTYPE_STI:
        parse_StiParams(task);
        break;
    case PTYPE_TVS:
        parse_TvsParams(task);
        break;
    case PTYPE_M:
        parse_MParams(task);
        break;
    }
}

/**
 * @brief CProductParamSaveDB::OnSaveProductInfoSavePath
 * @param savetask
 * @param standard
 */
void CProductParamSaveDB::OnSaveProductInfoSavePath(ProdPathSaveTask& savetask, int standard)
{
    ProdPathInfo pathInfo;
    string productpath = get<2>(savetask);
    QString productPath = QString::fromStdString(productpath.substr(productpath.find_last_of('/')+1,productpath.size()-productpath.find_last_of('/')));
    QString rootpath = QString::fromStdString(productpath.substr(0,productpath.find_last_of('/')));
    QString filetype=QString::fromStdString(productpath.substr(productpath.find_last_of('.')));
    if (filetype==".Z")
    {
        standard = 1;
    }

    if (standard == 0)
    {
        //if(!productPath.contains("QC"))
        //{
            if(productPath.contains("latlon"))
            {
                auto strlist = productPath.split("_");
                pathInfo.pathStr = productPath.toStdString();
                pathInfo.stationId = rootpath.split("/").at(0).toStdString();
                std::string datetimeStr= strlist.at(3).split(".").at(0).toStdString();
                datetimeStr.insert(4,"-");
                datetimeStr.insert(7,"-");
                datetimeStr.insert(10," ");
                datetimeStr.insert(13,":");
                datetimeStr.insert(16,":");
                strcpy(pathInfo.datetime,datetimeStr.c_str());

                pathInfo.milliSecond = QDateTime::fromString(strlist.at(3).split(".").at(0),"yyyyMMddhhmmss").toMSecsSinceEpoch();
                pathInfo.productCode = strlist.at(2).toStdString();
                pathInfo.productType = get<0>(savetask);
                pathInfo.fileSize = get<1>(savetask)/1000;
                pathInfo.elevIndex = "NUL";
                QString tempcode = QString::number(pathInfo.milliSecond) + "-NUL-" + strlist.at(2);
                pathInfo.code = tempcode.toStdString();
                if(DBOperator.recordProductPathInfo(pathInfo))
                    NRIET_DEBUG_INFO(m_nDebugLevel, m_pLogger, m_strName, "Record  Product Path Params done :" + productPath.toStdString());
                else
                    NRIET_DEBUG_ERROR(m_nDebugLevel, m_pLogger, "Record Product Path fail :" + productPath.toStdString());
            }
            else
            {
                auto strlist = productPath.split("_");
                pathInfo.pathStr = productPath.toStdString();
                pathInfo.stationId = strlist.at(3).toStdString();

                //            pathInfo.datetimeStr = strlist.at(4).toStdString();
                std::string datetimeStr= strlist.at(4).toStdString();
                datetimeStr.insert(4,"-");
                datetimeStr.insert(7,"-");
                datetimeStr.insert(10," ");
                datetimeStr.insert(13,":");
                datetimeStr.insert(16,":");
                strcpy(pathInfo.datetime,datetimeStr.c_str());



                //            pathInfo.milliSecond = QDateTime::fromString(QString::fromStdString(strlist.at(0).toStdString().substr(12)),"yyyyMMddhhmmss").toMSecsSinceEpoch();
                pathInfo.milliSecond = QDateTime::fromString(strlist.at(4),"yyyyMMddhhmmss").toMSecsSinceEpoch();
                pathInfo.productCode = strlist.at(8).toStdString();
                pathInfo.productType = get<0>(savetask);
                pathInfo.fileSize = get<1>(savetask)/1000;
                //            pathInfo.elevIndex=strlist.at(0).split(".")[0].toStdString().substr(7);
                pathInfo.elevIndex = strlist.at(strlist.size()-1).split(".")[0].toStdString();

                //std::cout<<"$$$$$$$$$$$$$$$$$$error_test: "<<pathInfo.productCode<<", length-3="<<std::to_string(pathInfo.productCode.length()-3)<<std::endl;
//                if(pathInfo.productCode.length()>2)
//                {
                    //string ScanTyprstr=pathInfo.productCode.substr(pathInfo.productCode.length()-3);
                if (QString::fromStdString(pathInfo.productCode).contains("RHI"))
                {
//                    pathInfo.stationId =strlist.at(3).split("-").at(0).toStdString()+"-NUL-"+strlist.at(3).split("-").at(2).toStdString();
                    pathInfo.elevIndex="NUL";
                }

//                    pathInfo.stationId = strlist.at(3).toStdString();
//                    pathInfo.stationId =strlist.at(3).split("-").at(0).toStdString()+"-NUL-"+strlist.at(3).split("-").at(2).toStdString();
//                    pathInfo.elevIndex="NUL";
//                }


                QString tempcode = QString::number(pathInfo.milliSecond) + "-" + QString::fromStdString(pathInfo.elevIndex) + "-" + strlist.at(8);
                pathInfo.code = tempcode.toStdString();
                //            pathInfo.code="NUL";

                if(DBOperator.recordProductPathInfo(pathInfo))
                    NRIET_DEBUG_INFO(m_nDebugLevel, m_pLogger, m_strName, "Record  Product Path Params done :" + productPath.toStdString());
                else
                    NRIET_DEBUG_ERROR(m_nDebugLevel, m_pLogger, "Record Product Path fail :" + productPath.toStdString());
            }
        //}
    }
    else if (standard == 1)
    {
        auto strlist = productPath.split("_");
        pathInfo.pathStr = productPath.toStdString();

        pathInfo.stationId=strlist.at(0).toStdString().substr(3,5);

        std::string datetimeStr= strlist.at(0).toStdString().substr(12,14);
        pathInfo.milliSecond = QDateTime::fromString(QString::fromStdString(datetimeStr),"yyyyMMddhhmmss").toMSecsSinceEpoch();

        datetimeStr.insert(4,"-");
        datetimeStr.insert(7,"-");
        datetimeStr.insert(10," ");
        datetimeStr.insert(13,":");
        datetimeStr.insert(16,":");
        strcpy(pathInfo.datetime,datetimeStr.c_str());



        QString tmpname=strlist.at(1).split(".")[0];
        int namesize=tmpname.length();

        int pos = namesize;
        for (auto ichar = namesize-1; ichar >=0; ichar--)
        {
            if ( (tmpname.at(ichar).unicode() >= '0' && tmpname.at(ichar).unicode() <= '9') || tmpname.at(ichar).unicode() == '-' ){
                pos --;
            }
            else {
                break;
            }

        }
        pathInfo.elevIndex=tmpname.toStdString().substr(pos);
        string proname = tmpname.toStdString().substr(0,pos);
        //            string str="PTYPE_"+proname;
        //            KJC::PRODUCT_TYPE myproduct=(PRODUCT_TYPE)(enum.Parse(typeof(KJC::PRODUCT_TYPE),str));

        pathInfo.productCode = proname;
        if (proname == "PPIDBT")
        {
            pathInfo.productType = KJC::PTYPE_PPIDBT;
        }
        else if(proname=="PPIDBZ")
        {
            pathInfo.productType=KJC::PTYPE_PPIDBZ;
        }
        else if(proname=="PPIV")
        {
            pathInfo.productType=KJC::PTYPE_PPIV;
        }
        else if(proname=="PPISW")
        {
            pathInfo.productType=KJC::PTYPE_PPISW;
        }
        else if(proname=="RHIDBT")
        {
            pathInfo.productType=KJC::PTYPE_RHIDBT;
        }
        else if(proname=="RHIDBZ")
        {
            pathInfo.productType=KJC::PTYPE_RHIDBZ;
        }
        else if(proname=="RHIV")
        {
            pathInfo.productType=KJC::PTYPE_RHIV;
        }
        else if(proname=="RHISW")
        {
            pathInfo.productType=KJC::PTYPE_RHISW;
        }
        else if(proname=="CAPPIDBZ")
        {
            pathInfo.productType=KJC::PTYPE_CAPPIDBZ;
        }
        else if(proname=="CAPPIDBT")
        {
            pathInfo.productType=KJC::PTYPE_CAPPIDBT;
        }
        else if(proname=="CAPPIV")
        {
            pathInfo.productType=KJC::PTYPE_CAPPIV;
        }
        else if(proname=="CAPPISW")
        {
            pathInfo.productType=KJC::PTYPE_CAPPISW;
        }
        else if(proname=="CR")
        {
            pathInfo.productType=KJC::PTYPE_CR;
        }
        else if(proname=="ZR")
        {
            pathInfo.productType=KJC::PTYPE_ZR;
        }
        else if(proname=="ET")
        {
            pathInfo.productType=KJC::PTYPE_ET;
        }
        else if(proname=="EB")
        {
            pathInfo.productType=KJC::PTYPE_EB;
        }
        else if(proname=="VIL")
        {
            pathInfo.productType=KJC::PTYPE_VIL;
        }
        else if(proname=="RVD")
        {
            pathInfo.productType=KJC::PTYPE_RVD;
        }
        else if(proname=="ARD")
        {
            pathInfo.productType=KJC::PTYPE_ARD;
        }
        else if(proname=="CS")
        {
            pathInfo.productType=KJC::PTYPE_CS;
        }
        else if(proname=="MAX")
        {
            pathInfo.productType=KJC::PTYPE_MAX;
        }
        else if(proname=="WER")
        {
            pathInfo.productType=KJC::PTYPE_WER;
        }
        else if(proname=="LTA")
        {
            pathInfo.productType=KJC::PTYPE_LTA;
        }
        else if(proname=="SWP")
        {
            pathInfo.productType=KJC::PTYPE_SWP;
        }
        else if(proname=="OHP")
        {
            pathInfo.productType=KJC::PTYPE_OHP;
        }
        else if(proname=="USP")
        {
            pathInfo.productType=KJC::PTYPE_USP;
        }
        else if(proname=="VWP")
        {
            pathInfo.productType=KJC::PTYPE_VWP;
        }
        else if(proname=="VAD")
        {
            pathInfo.productType=KJC::PTYPE_VAD;
        }
        else if(proname=="EDWF")
        {
            pathInfo.productType=KJC::PTYPE_EDWF;
        }
        else if(proname=="SS")
        {
            pathInfo.productType=KJC::PTYPE_SS;
        }
        else if(proname=="GFI")
        {
            pathInfo.productType=KJC::PTYPE_GFI;
        }
        else if(proname=="HI")
        {
            pathInfo.productType=KJC::PTYPE_HI;
        }
        else if(proname=="DBI")
        {
            pathInfo.productType=KJC::PTYPE_DBI;
        }
        else if(proname=="M")
        {
            pathInfo.productType=KJC::PTYPE_M;
        }
        else if(proname=="RS")
        {
            pathInfo.productType=KJC::PTYPE_RS;
        }
        else if(proname=="TVS")
        {
            pathInfo.productType=KJC::PTYPE_TVS;
        }
        else if(proname=="STI")
        {
            pathInfo.productType=KJC::PTYPE_STI;
        }
        else if(proname=="SAT")
        {
            pathInfo.productType=KJC::PTYPE_SAT;
        }
        else if(proname=="ACC")
        {
            pathInfo.productType=KJC::PTYPE_ACC;
        }
        else if(proname=="LGT")
        {
            pathInfo.productType=KJC::PTYPE_LGT;
        }
        else if(proname=="EXP")
        {
            pathInfo.productType=KJC::PTYPE_EXP;
        }
        else if(proname=="EV")
        {
            pathInfo.productType=KJC::PTYPE_EV;
        }
        else if (proname == "EXTRASS")
        {
            pathInfo.productType = KJC::PTYPE_EXTRASS;
        }
        else
        {
            pathInfo.productType = -1;
        }
        //            pathInfo.productType = get<0>(savetask);
        pathInfo.fileSize = get<1>(savetask)/1000;
        //            pathInfo.elevIndex=strlist.at(0).split(".")[0].toStdString().substr(7);
        //            pathInfo.elevIndex = strlist.at(strlist.size()-1).split(".")[0].toStdString();

        //std::cout<<"$$$$$$$$$$$$$$$$$$error_test: "<<pathInfo.productCode<<", length-3="<<std::to_string(pathInfo.productCode.length()-3)<<std::endl;
        if(pathInfo.productCode.length()>2)
        {
            //                string ScanTyprstr=pathInfo.productCode.substr(pathInfo.productCode.length()-3);
            string ScanTyprstr=pathInfo.productCode.substr(0,3);
            if(ScanTyprstr=="RHI")
            {
                pathInfo.stationId=strlist.at(0).toStdString().substr(3,5);
                pathInfo.elevIndex="NUL";
            }
        }

        if(QString::fromStdString(pathInfo.elevIndex).length()==0)
        {
            pathInfo.elevIndex="NUL";
        }

        if (pathInfo.productType == KJC::PTYPE_EXP || pathInfo.productType == KJC::PTYPE_EXTRASS)
        {
            pathInfo.elevIndex = "NUL";
        }

        QString tempcode = QString::number(pathInfo.milliSecond) + "-" + QString::fromStdString(pathInfo.elevIndex) + "-" + QString::fromStdString(proname);
        pathInfo.code = tempcode.toStdString();

        if(DBOperator.recordProductPathInfo(pathInfo))
            NRIET_DEBUG_INFO(m_nDebugLevel, m_pLogger, m_strName, "Record  Product Path Params done :" + productPath.toStdString());
        else
            NRIET_DEBUG_ERROR(m_nDebugLevel, m_pLogger, "Record Product Path fail :" + productPath.toStdString());
    }
}

void CProductParamSaveDB::OnSaveRecPPIInfoSavePath(ProdPathSaveTask &savetask)
{
    ProdPathInfo pathInfo;
    string productpath  = get<2>(savetask);
    QString productPath = QString::fromStdString(productpath.substr(productpath.find_last_of('/')+1,productpath.size()-productpath.find_last_of('/')));
    QString rootpath    = QString::fromStdString(productpath.substr(0,productpath.find_last_of('/')));
    QString filetype    = QString::fromStdString(productpath.substr(productpath.find_last_of('.')));

//    if (filetype != '.Z') return;

    auto strlist            = productPath.split("_");
    pathInfo.pathStr        = productPath.toStdString();
    pathInfo.stationId      = strlist.at(0).toStdString().substr(3,5);
    std::string datetimeStr = strlist.at(0).toStdString().substr(12,14);
    pathInfo.milliSecond    = QDateTime::fromString(QString::fromStdString(datetimeStr),"yyyyMMddhhmmss").toMSecsSinceEpoch();

    datetimeStr.insert(4, "-");
    datetimeStr.insert(7, "-");
    datetimeStr.insert(10, " ");
    datetimeStr.insert(13, ":");
    datetimeStr.insert(16, ":");
    strcpy(pathInfo.datetime, datetimeStr.c_str());

    QString tmpname = strlist.at(1).split(".")[0];
    int namesize    = tmpname.length();
    int pos         = namesize;

    for (auto ichar = namesize - 1; ichar >= 0; ichar--)
    {
        if ( (tmpname.at(ichar).unicode() >= '0' && tmpname.at(ichar).unicode() <= '9') || tmpname.at(ichar).unicode() == '-' ){
            pos --;
        }
        else {
            break;
        }
    }

    pathInfo.elevIndex  = tmpname.toStdString().substr(pos);
    string proname      = tmpname.toStdString().substr(0,pos);
    pathInfo.productCode= proname;

    if (proname != "PPIDBZ")
        return;

    pathInfo.productType    = KJC::PTYPE_PPIDBZ;
    pathInfo.fileSize       = get<1>(savetask)/1000;

    if(QString::fromStdString(pathInfo.elevIndex).length() == 0)
    {
        pathInfo.elevIndex = "NUL";
    }

    QString tempcode    = QString::number(pathInfo.milliSecond) + "-" + QString::fromStdString(pathInfo.elevIndex) + "-" + QString::fromStdString(proname);
    pathInfo.code       = tempcode.toStdString();

    if(DBOperator.recordRecPPIPathInfo(pathInfo))
        NRIET_DEBUG_INFO(m_nDebugLevel, m_pLogger, m_strName, "Record  Product Path Params done :" + productPath.toStdString());
    else
        NRIET_DEBUG_ERROR(m_nDebugLevel, m_pLogger, "Record Product Path fail :" + productPath.toStdString());
}

/**
 * @brief CProductParamSaveDB::parse_HiParams
 * @param task
 */
void CProductParamSaveDB::parse_HiParams(ProductDBSaveTask& task)
{
    int HiCount;
    auto data = get<0>(task);
    string path= get<1>(task);
    string prodTime = QString::fromStdString(path).split("_")[4].toStdString();
    float lon = get<2>(task);
    float lat = get<3>(task);

    size_t offset = 0;
    HAILTABLE hiProd;
    HiParam hiParamDB;
    memcpy(&HiCount,&data.at(offset),sizeof (int));
    offset += sizeof (int);
    size_t elemSize = sizeof(HAILTABLE);
    for(int i = 0 ; i < HiCount ; i++){
        memcpy(&hiProd,&data.at(offset),elemSize);
        hiParamDB.hail_id = hiProd.HailID;
        memcpy(hiParamDB.time,prodTime.c_str(),prodTime.length());
        hiParamDB.sort = i;
        hiParamDB.azimuth = hiProd.Azimuth;
        hiParamDB.hail_range = hiProd.Range;
        longLatOffset(lon,lat,hiParamDB.azimuth,hiParamDB.hail_range,hiParamDB.lon,hiParamDB.lat);
        hiParamDB.size_of_hail = hiProd.SizeOfHail;
        hiParamDB.possibility_of_hail = hiProd.PossibilityOfHail;
        hiParamDB.possibility_of_severe_hail = hiProd.PossibilityOfSevereHail;

        offset += elemSize;
        if(DBOperator.recordHiProductParam(hiParamDB))
            NRIET_DEBUG_INFO(m_nDebugLevel, m_pLogger, m_strName, "Record Hi Product Params done:" + to_string(hiParamDB.hail_id));
        else
            NRIET_DEBUG_ERROR(m_nDebugLevel, m_pLogger, "Record Hi Product Params fail:" + to_string(hiParamDB.hail_id));
    }
}

/**
 * @brief CProductParamSaveDB::parse_StiParams
 * @param task
 */
void CProductParamSaveDB::parse_StiParams(ProductDBSaveTask& task)
{
    auto data = get<0>(task);
    string path= get<1>(task);
    string prodTime = QString::fromStdString(path).split("_")[4].toStdString();
    float lon = get<2>(task);
    float lat = get<3>(task);

    size_t offset = 0;
    STIHEADERBLOCK stiHeadBlock;
    vector<StiParam> stiParamDB;
    memcpy(&stiHeadBlock,&data.at(offset),sizeof (STIHEADERBLOCK));
    offset += sizeof (STIHEADERBLOCK);
    STORMMOTIONBLOCK CurrentStormInfo;
    int StormCount = stiHeadBlock.NumOfStorm;
    stiParamDB.resize(StormCount);
    if(StormCount <= 0)
        return;
    size_t SizeOfCurrentStormInfo = sizeof (STORMMOTIONBLOCK);
    size_t SizeOfHistoryBlock, SizeOfForcastBlock;
    SizeOfHistoryBlock = SizeOfForcastBlock = sizeof (STORMPOSITION);
    size_t forcastStormOffset = 0;
    size_t historyStormOffset = 0;
    for(int i = 0 ; i < StormCount ; i++){
        memcpy(&CurrentStormInfo,&data.at(offset + SizeOfCurrentStormInfo * i),SizeOfCurrentStormInfo);
        stiParamDB[i].sort = i;
        stiParamDB[i].azimuth = CurrentStormInfo.Azimuth;
        stiParamDB[i].speed  = CurrentStormInfo.Speed;
        stiParamDB[i].direction  = CurrentStormInfo.Direction;
        stiParamDB[i].storm_range = CurrentStormInfo.Range;
        memcpy(stiParamDB[i].time,prodTime.c_str(),prodTime.length());
        longLatOffset(lon,lat,CurrentStormInfo.Azimuth,CurrentStormInfo.Range,stiParamDB[i].lon,stiParamDB[i].lat);
    }
    offset += SizeOfCurrentStormInfo * StormCount;

    //read  forcast storm info
    for(int i = 0 ; i < StormCount ; i++){
        int forcastStormCount;
        memcpy(&forcastStormCount,&data.at(offset + forcastStormOffset),sizeof (int));
        forcastStormOffset += sizeof (int);
        if(forcastStormCount <= 0)
            continue;
        vector<STORMPOSITION> forcastStormPositionlist;
        forcastStormPositionlist.resize(forcastStormCount);
        memcpy(&forcastStormPositionlist.front(),&data.at(offset + forcastStormOffset),SizeOfForcastBlock * forcastStormCount);
        forcastStormOffset += SizeOfForcastBlock * forcastStormCount;
        longLatOffset(lon,lat,forcastStormPositionlist[0].AzimithOfPosition,forcastStormPositionlist[0].RangeOfPosition,stiParamDB[i].lon_forecast_one,stiParamDB[i].lat_forecast_one);
        longLatOffset(lon,lat,forcastStormPositionlist[1].AzimithOfPosition,forcastStormPositionlist[1].RangeOfPosition,stiParamDB[i].lon_forecast_two,stiParamDB[i].lat_forecast_two);
        longLatOffset(lon,lat,forcastStormPositionlist[2].AzimithOfPosition,forcastStormPositionlist[2].RangeOfPosition,stiParamDB[i].lon_forecast_three,stiParamDB[i].lat_forecast_three);
        longLatOffset(lon,lat,forcastStormPositionlist[forcastStormCount-1].AzimithOfPosition,forcastStormPositionlist[forcastStormCount-1].RangeOfPosition,stiParamDB[i].lon_forecast_n,stiParamDB[i].lat_forecast_n);
    }
    offset += forcastStormOffset;
    //read  history storm info
    for (int i = 0 ; i < StormCount ; i++) {
        int historyStormCount;
        memcpy(&historyStormCount,&data.at(offset + historyStormOffset),sizeof (int));
        historyStormOffset += sizeof (int);
        historyStormOffset += SizeOfHistoryBlock * historyStormCount;
    }
    offset += historyStormOffset;

    //    size_t SizeOfStormOtherAttr = sizeof (STORMOTHERATTRIBUTESBLOCK);
    //    size_t StormOtherAttrOffset = StormCount * SizeOfStormOtherAttr;
    //    offset += StormOtherAttrOffset;

    size_t SizeOfStormAttribute = sizeof (STORMATTRIBUTESBLOCK);
    size_t StormAttributeOffset = 0;
    STORMATTRIBUTESBLOCK StormAttribute;
    for (int i = 0 ; i < StormCount ; i++) {
        memcpy(&StormAttribute,&data.at(offset + SizeOfStormAttribute * i),SizeOfStormAttribute);
        StormAttributeOffset += SizeOfStormAttribute;

        stiParamDB[i].storm_id = StormAttribute.StormID;
        stiParamDB[i].vil = StormAttribute.VIL;
        stiParamDB[i].height = StormAttribute.Height;
        stiParamDB[i].top_height = StormAttribute.TopHeight;
        stiParamDB[i].bottom_height = StormAttribute.BottomHeight;
        stiParamDB[i].height_of_maximum_reflectivity = StormAttribute.HeightOfMaxRef;
        stiParamDB[i].maximum_reflectivity = StormAttribute.MaxRef;
    }
    offset += StormAttributeOffset;
    int componentSize = sizeof(COMPONENTTABLEBLOCK);
    offset += componentSize * StormCount;
    int stormTrackAdaptionSize = sizeof(STORMTRACKINGADAPTATIONDATA);
    offset += componentSize * StormCount;
    for (int i = 0 ; i < StormCount ; i++) {
        if(stiParamDB[i].maximum_reflectivity >= stiMaxValThreshold && stiParamDB[i].vil >= stiVilThreshold){
            if(DBOperator.recordStiProductParam(stiParamDB[i]))
                NRIET_DEBUG_INFO(m_nDebugLevel, m_pLogger, m_strName, "Record storm sti Product Params done strom_id:" + to_string(stiParamDB[i].storm_id));
            else
                NRIET_DEBUG_ERROR(m_nDebugLevel, m_pLogger, "Record storm sti Product Params fail strom_id:" + to_string(stiParamDB[i].storm_id));
        }
    }
}

/**
 * @brief CProductParamSaveDB::parse_MParams
 * @param task
 */
void CProductParamSaveDB::parse_MParams(ProductDBSaveTask& task)
{
    auto data = get<0>(task);
    float lon = get<2>(task);
    float lat = get<3>(task);
    string path= get<1>(task);
    string prodTime = QString::fromStdString(path).split("_")[4].toStdString();
    size_t offset = 0;
    MESOGEADERBLOCK MProd;
    vector<MParam> mParamDB;
    memcpy(&MProd,&data.at(offset),sizeof (MESOGEADERBLOCK));
    if(MProd.NumberOfMeso <= 0)
        return;
    offset += sizeof (MESOGEADERBLOCK);
    size_t mesoSize = sizeof(MESOTABLE);
    MESOTABLE SingelMeso;
    mParamDB.resize(MProd.NumberOfMeso);
    for(int i = 0 ; i < MProd.NumberOfMeso ; i++){
        memcpy(&SingelMeso,&data.at(offset),mesoSize);
        mParamDB[i].feature_id = SingelMeso.FeatureID;
        mParamDB[i].storm_id = SingelMeso.StormID;
        memcpy(mParamDB[i].time,prodTime.c_str(),prodTime.length());
        mParamDB[i].sort = i;
        mParamDB[i].azimuth = SingelMeso.Azimuth;
        mParamDB[i].m_range = SingelMeso.Range;
        mParamDB[i].height = SingelMeso.Height;
        longLatOffset(lon,lat,mParamDB[i].azimuth,mParamDB[i].m_range,mParamDB[i].lon,mParamDB[i].lat);
        offset += mesoSize;
    }

    MESOFEATURETABLE MesoFeature;
    size_t mesoFeatureSize = sizeof(MESOFEATURETABLE);
    for(int i = 0 ; i < MProd.NumberOfMeso ; i++){
        memcpy(&MesoFeature,&data.at(offset),mesoFeatureSize);
        mParamDB[i].feature_type = MesoFeature.FeatureType;
        offset += mesoFeatureSize;
    }

    for(int i = 0 ; i < MProd.NumberOfMeso ; i++)
    {
        if(DBOperator.recordmProductParam(mParamDB[i]))
            NRIET_DEBUG_INFO(m_nDebugLevel, m_pLogger, m_strName, "Record M Product Params done feature_id:" + to_string(mParamDB[i].feature_id));
        else
            NRIET_DEBUG_ERROR(m_nDebugLevel, m_pLogger, "Record M Product Params fail feature_id:" + to_string(mParamDB[i].feature_id));
    }
}

/**
 * @brief CProductParamSaveDB::parse_TvsParams
 * @param task
 */
void CProductParamSaveDB::parse_TvsParams(ProductDBSaveTask& task)
{

}

/**
 * @brief CProductParamSaveDB::addProductParamInfoSaveQueue
 * @param task
 */
void CProductParamSaveDB::addProductParamInfoSaveQueue(ProductDBSaveTask& task)
{
    IceUtil::Monitor<IceUtil::Mutex>::Lock lock(m_Monitor);

    if(!m_bDone)
    {
        if(m_qProdInfoSaveDB.size() == 0)
            m_Monitor.notify();

        m_qProdInfoSaveDB.push(task);
    }
}

/**
 * @brief CProductParamSaveDB::addProdLatlonSaveQueue
 * @param task
 */
void CProductParamSaveDB::addProdLatlonSaveQueue(ProductLatLonSaveTask& task)
{
    IceUtil::Monitor<IceUtil::Mutex>::Lock lock(m_Monitor);

    if(!m_bDone)
    {
        if(m_qProdLatlonSaveDB.size() == 0)
            m_Monitor.notify();

        m_qProdLatlonSaveDB.push(task);
    }
}

/**
 * @brief CProductParamSaveDB::addProdPathInfoSaveQueue
 * @param productpath
 */
void CProductParamSaveDB::addProdPathInfoSaveQueue(ProdPathSaveTask& productpath)
{
    IceUtil::Monitor<IceUtil::Mutex>::Lock lock(m_Monitor);

    if(!m_bDone)
    {
        if(m_qPreSavedProductPath.size() == 0)
            m_Monitor.notify();

        m_qPreSavedProductPath.push(productpath);
    }
}

void CProductParamSaveDB::addRecPPIPathInfoSaveQueue(ProdPathSaveTask &productpath)
{
    IceUtil::Monitor<IceUtil::Mutex>::Lock lock(m_Monitor);

    if(!m_bDone)
    {
        if(m_qPreSavedRecPPIPath.size() == 0)
            m_Monitor.notify();

        m_qPreSavedRecPPIPath.push(productpath);
    }
}

/**
 * @brief CProductParamSaveDB::destroy
 */
void CProductParamSaveDB::destroy()
{
    IceUtil::Monitor<IceUtil::Mutex>::Lock lock(m_Monitor);
    m_bDone = true;
    m_Monitor.notify();
}


/**
 * 根据中心经纬度求，方位角，距离求另一个经纬度
 *
 * @param startlon 经度
 * @param startlat 纬度
 * @param az       方位角（要换算弧度）
 * @param dst      移动距离 m
 * @return
 */
void CProductParamSaveDB::longLatOffset(float startlon, float startlat, float az, float dst,float& deslon,float& deslat) {

    double arc = 6371.393 * 1000;
    double q = dst / arc;
    az = DEG_TO_RAD(az);
    startlon = DEG_TO_RAD(startlon);
    startlat = DEG_TO_RAD(startlat);
    double lat = asin(sin(startlat) * cos(q) + cos(startlat) * sin(q) * cos(az));
    double lon = startlon + atan2(sin(az) * sin(q) * cos(startlat), cos(q) - sin(startlat) * sin(lat));
    lon = RAD_TO_DEG(lon);
    lat = RAD_TO_DEG(lat);
    deslon = lon;
    deslat = lat;
}

/**
 * @brief CProductParamSaveDB::time_convert 时间转换
 * @param year
 * @param month
 * @param day
 * @param hour
 * @param minute
 * @param second
 * @return
 */
time_t CProductParamSaveDB::time_convert(int year, int month, int day, int hour,int minute, int second)
{
    time_t now = time(nullptr);
    auto temp = localtime(&now);
    auto offset = temp->tm_gmtoff;
    tm info;
    info.tm_year = year - 1900;
    info.tm_mon = month - 1;
    info.tm_mday = day;
    info.tm_hour = hour;
    info.tm_min = minute;
    info.tm_sec = second;
    info.tm_isdst = 0;
    time_t TimeStamp = mktime(&info);
    TimeStamp = TimeStamp + offset - 28800;
    return TimeStamp;
}


//time_t CProductParamSaveDB::time_convertCP(int year, int month, int day)
//{
//    time_t now = time(nullptr);
//    auto temp = localtime(&now);
//    auto offset = temp->tm_gmtoff;
//    tm info;
//    info.tm_year = year - 1900;
//    info.tm_mon = month - 1;
//    info.tm_mday = day;
//    info.tm_hour = hour;
//    info.tm_min = minute;
//    info.tm_sec = second;
//    info.tm_isdst = 0;
//    time_t TimeStamp = mktime(&info);
//    TimeStamp = TimeStamp + offset - 28800;
//    return TimeStamp;
//}

//time_t CProductParamSaveDB::longLatOffsetCP(int year, int month, int day, int hour,int minute)
//{
//    time_t now = time(nullptr);
//    auto temp = localtime(&now);
//    auto offset = temp->tm_gmtoff;
//    tm info;
//    info.tm_year = year - 1900;
//    info.tm_mon = month - 1;
//    info.tm_mday = day;
//    info.tm_hour = hour;
//    info.tm_min = minute;
//    info.tm_sec = second;
//    info.tm_isdst = 0;
//    time_t TimeStamp = mktime(&info);
//    TimeStamp = TimeStamp + offset - 28800;
//    return TimeStamp;
//}

//void CProductParamSaveDB::parse_MParamsCP(ProductDBSaveTask& task)
//{
//    auto data = get<0>(task);
//    float lon = get<2>(task);
//    float lat = get<3>(task);
//    string path= get<1>(task);
//    string prodTime = QString::fromStdString(path).split("_")[4].toStdString();
//    size_t offset = 0;
//    MESOGEADERBLOCK MProd;
//    vector<MParam> mParamDB;
//    memcpy(&MProd,&data.at(offset),sizeof (MESOGEADERBLOCK));
//    if(MProd.NumberOfMeso <= 0)
//        return;
//    offset += sizeof (MESOGEADERBLOCK);
//    size_t mesoSize = sizeof(MESOTABLE);
//    MESOTABLE SingelMeso;
//    mParamDB.resize(MProd.NumberOfMeso);
//    for(int i = 0 ; i < MProd.NumberOfMeso ; i++){
//        memcpy(&SingelMeso,&data.at(offset),mesoSize);
//        mParamDB[i].feature_id = SingelMeso.FeatureID;
//        mParamDB[i].storm_id = SingelMeso.StormID;
//        memcpy(mParamDB[i].time,prodTime.c_str(),prodTime.length());
//        mParamDB[i].sort = i;
//        mParamDB[i].azimuth = SingelMeso.Azimuth;
//        mParamDB[i].m_range = SingelMeso.Range;
//        mParamDB[i].height = SingelMeso.Height;
//        longLatOffset(lon,lat,mParamDB[i].azimuth,mParamDB[i].m_range,mParamDB[i].lon,mParamDB[i].lat);
//        offset += mesoSize;
//    }

//    MESOFEATURETABLE MesoFeature;
//    size_t mesoFeatureSize = sizeof(MESOFEATURETABLE);
//    for(int i = 0 ; i < MProd.NumberOfMeso ; i++){
//        memcpy(&MesoFeature,&data.at(offset),mesoFeatureSize);
//        mParamDB[i].feature_type = MesoFeature.FeatureType;
//        offset += mesoFeatureSize;
//    }

//    for(int i = 0 ; i < MProd.NumberOfMeso ; i++)
//    {
//        if(DBOperator.recordmProductParam(mParamDB[i]))
//            NRIET_DEBUG_INFO(m_nDebugLevel, m_pLogger, m_strName, "Record M Product Params done feature_id:" + to_string(mParamDB[i].feature_id));
//        else
//            NRIET_DEBUG_ERROR(m_nDebugLevel, m_pLogger, "Record M Product Params fail feature_id:" + to_string(mParamDB[i].feature_id));
//    }
//}
