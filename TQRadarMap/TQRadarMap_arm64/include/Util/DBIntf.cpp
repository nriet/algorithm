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
* File:DBIntf.cpp
* Author:Nriet
* time 2023-05-24
*************************************************************************/
//#include "Database/dataproviderfactory.h"
#include "DBIntf.h"
#include <string>
#include <iostream>
#include <QDebug>
#include <dlfcn.h>
using namespace std;

initialiseSingleton(CDBIntf);

CDBIntf::CDBIntf()
//: m_DataProvider(nullptr)
{
   // m_DataProvider = DataProviderFactory::createDataProvider();


    void * m_pAlgoHandle=nullptr;
    m_pAlgoHandle = dlopen("../lib/DBCommonInterface.so", RTLD_LAZY);

    if(m_pAlgoHandle)
    {
        pGetAlgoInstance = (CNrietDBCommonInterface *(*)(std::string))dlsym(m_pAlgoHandle, "GetDBAlgoInstance");
    }
    else
    {
        std::cout << "Load library DBCommonInterface.so fail 2"<<std::endl;
    }

}

/**
 * @brief CDBIntf::~CDBIntf
 */
CDBIntf::~CDBIntf()
{
    Shutdown();
    if(m_pDBInterface)
        delete m_pDBInterface;
    m_pDBInterface = nullptr;

}
/**
 * @brief CDBIntf::Initilize
 * @param dbType
 * @param host
 * @param user
 * @param pass
 * @param db
 * @param port
 * @return
 */
bool CDBIntf::Initilize(std::string dbType,std::string host,std::string user,std::string pass,std::string db,int port)
{
    if(pGetAlgoInstance)
    {
        m_pDBInterface = (*pGetAlgoInstance)(dbType);
        if(m_pDBInterface == nullptr)return false;
        bool connectstatue=m_pDBInterface->Initilize(host,user,pass,db,port);
        std::cout << "connectstatue="<<connectstatue<<std::endl;
        std::vector<std::vector<std::string>> selectInfo;

        std::string SQLString="select * from t_user";
        m_pDBInterface->commonSelectWithSQLStr(SQLString,selectInfo);
        std::cout << "DataBase:connectstatue: t_user size="<<selectInfo.size()<<","<<
                 selectInfo.at(0).at(0)<<std::endl;
        return connectstatue;
    }
    else
    {
        std::cout << "Load GetAlgoInstance API fail 1"<<std::endl;
         return false;
    }
}

/**
 * @brief CDBIntf::Shutdown
 */
void CDBIntf::Shutdown(void)
{
    if(m_pDBInterface == nullptr) return;
    m_pDBInterface->Shutdown();

}
/**
 * @brief CDBIntf::Update
 */
void CDBIntf::Update(void)
{
    if(m_pDBInterface == nullptr) return;
    m_pDBInterface->Update();

}

/**
 * @brief CDBIntf::recordLog
 * @param log
 * @return
 */
bool CDBIntf::recordLog(LogInfo &log)
{
    if(m_pDBInterface == nullptr) return 0;
    std::ostringstream sqlstr;
    sqlstr << "call "<< MYSQL_PROC_RECORD_LOG <<"('"
           << string(log.name) << "',"
           << log.type << ","
           << log.level << ",'"
           << string(log.log) << "');";
    bool statue=m_pDBInterface->commonSQL(sqlstr.str());
    return statue;
}

/**
 * @brief CDBIntf::recordProduct
 * @param info
 * @return
 */
bool CDBIntf::recordProduct(ProductInfo & info)
{
    if(m_pDBInterface == nullptr) return 0;
    std::ostringstream sqlstr;
    sqlstr << "call "<< MYSQL_PROC_RECORD_PRODUCT <<"("
           << info.type << ",'"
           << string(info.name) << "','"
           << string(info.producer) << "','"
           << string(info.desc) << "',"
           << info.time << ");";

    bool statue=m_pDBInterface->commonSQL(sqlstr.str());
    return statue;
}
/**
 * @brief CDBIntf::recordHiProductParam
 * @param param
 * @return
 */
bool CDBIntf::recordHiProductParam(HiParam& param)
{
    if(m_pDBInterface == nullptr) return false;
    std::ostringstream sqlstr;
    sqlstr << "insert  into "<< MYSQL_PRODUCT_HIPARAM
           << " (time,hail_id,sort,lon,lat,azimuth,hail_range,possibility_of_hail,possibility_of_severe_hail,size_of_hail) values ('"
           << string(param.time).substr(0,19) << "',"
           << param.hail_id << ","
           << param.sort << ","
           << param.lon << ","
           << param.lat << ","
           << param.azimuth << ","
           << param.hail_range << ","
           << param.possibility_of_hail << ","
           << param.possibility_of_severe_hail << ","
           << param.size_of_hail << ");";

    std::string sqlStr = sqlstr.str();
    std::cout<<sqlStr<<std::endl;
    bool statue=m_pDBInterface->commonSQL(sqlStr);
    return statue;
}
/**
 * @brief CDBIntf::recordStiProductParam
 * @param param
 * @return
 */
bool CDBIntf::recordStiProductParam(StiParam& param)
{
    if(m_pDBInterface == nullptr) return false;
    std::ostringstream sqlstr;
    sqlstr << "insert into "<< MYSQL_PRODUCT_STIPARAM
           <<" (time,storm_id,sort,lon,lat,lon_forecast_one,lat_forecast_one,lon_forecast_two,lat_forecast_two,lon_forecast_three,lat_forecast_three,lon_forecast_n,lat_forecast_n,azimuth,storm_range,speed,direction,top_height,bottom_height,height_of_maximum_reflectivity,height,vil,maximum_reflectivity) values ('"
           << string(param.time).substr(0,19) << "',"
           << param.storm_id << ","
           << param.sort << ","
           << param.lon << ","
           << param.lat << ","
           << param.lon_forecast_one << ","
           << param.lat_forecast_one << ","
           << param.lon_forecast_two << ","
           << param.lat_forecast_two << ","
           << param.lon_forecast_three << ","
           << param.lat_forecast_three << ","
           << param.lon_forecast_n << ","
           << param.lat_forecast_n << ","
           << param.azimuth << ","
           << param.storm_range << ","
           << param.speed << ","
           << param.direction << ","
           << param.top_height << ","
           << param.bottom_height << ","
           << param.height_of_maximum_reflectivity << ","
           << param.height << ","
           << param.vil << ","
           << param.maximum_reflectivity << ");";

    std::string sqlStr = sqlstr.str();
    std::cout<<sqlStr<<std::endl;
    bool statue=m_pDBInterface->commonSQL(sqlStr);
    return statue;
}

/*
 * bool CDBIntf::recordStiProductParamN(StiParam& param)
{
    if(m_pDBInterface == nullptr) return false;
    std::ostringstream sqlstr;
    sqlstr << "insert into "<< MYSQL_PRODUCT_STIPARAM
           <<" (time,storm_id,sort,lon,lat,lon_forecast_one,lat_forecast_one,lon_forecast_two,lat_forecast_two,lon_forecast_three,lat_forecast_three,lon_forecast_n,lat_forecast_n,azimuth,storm_range,speed,direction,top_height,bottom_height,height_of_maximum_reflectivity,height,vil,maximum_reflectivity) values ('"
           << string(param.time).substr(0,19) << "',"
           << param.storm_id << ","
           << param.sort << ","
           << param.lon << ","
           << param.lat << ","
           << param.lon_forecast_one << ","
           << param.lat_forecast_one << ","
           << param.lon_forecast_two << ","
           << param.lat_forecast_two << ","
           << param.lon_forecast_three << ","
           << param.lat_forecast_three << ","
           << param.lon_forecast_n << ","
           << param.lat_forecast_n << ","
           << param.azimuth << ","
           << param.storm_range << ","
           << param.speed << ","
           << param.direction << ","
           << param.top_height << ","
           << param.bottom_height << ","
           << param.height_of_maximum_reflectivity << ","
           << param.height << ","
           << param.vil << ","
           << param.maximum_reflectivity << ");";

    std::string sqlStr = sqlstr.str();
    std::cout<<sqlStr<<std::endl;
    bool statue=m_pDBInterface->commonSQL(sqlStr);
    return statue;
}
*/
/**
 * @brief CDBIntf::recordmProductParam
 * @param param
 * @return
 */
bool CDBIntf::recordmProductParam(MParam& param)
{
    if(m_pDBInterface == nullptr) return false;
    std::ostringstream sqlstr;
    sqlstr << "insert into "<< MYSQL_PRODUCT_MPARAM
           <<" (time,feature_id,storm_id,sort,lon,lat,feature_type,m_range,elevation,height) values ('"
           << string(param.time).substr(0,19) << "',"
           << param.feature_id << ","
           << param.storm_id << ","
           << param.sort << ","
           << param.lon << ","
           << param.lat << ","
           << param.feature_type << ","
           << param.m_range << ","
           << param.elevation << ","
           << param.height << ");";

    std::string sqlStr = sqlstr.str();
    std::cout<<sqlStr<<std::endl;
    bool statue=m_pDBInterface->commonSQL(sqlStr);
    return statue;
}

/**
 * @brief CDBIntf::recordProductLatlon
 * @param param
 * @return
 */
bool CDBIntf::recordProductLatlon(ProdLatlon& param)
{
    if(m_pDBInterface == nullptr) return false;
    std::ostringstream sqlstr;
    sqlstr << "insert into "<< MYSQL_PRODUCT_LATLON
           <<" (stationId,time,productCode,datatime,millisecond,des) values ('"
           << param.stationId << "',"
           << param.dateStr << ",'"
           << param.productCode << "',"
           << param.datetimeStr << ","
           << param.milliSecond << ",'"
           << param.des << "');";

    std::string sqlStr = sqlstr.str();
    std::cout<<sqlStr<<std::endl;
    bool statue=m_pDBInterface->commonSQL(sqlStr);
    return statue;
}

/**
 * @brief CDBIntf::recordProductPathInfo
 * @param param
 * @return
 */
bool CDBIntf::recordProductPathInfo(ProdPathInfo& param)
{
    if(m_pDBInterface == nullptr) return false;
    tm pro_tm;
    time_t t = time(NULL);
    localtime_r(&t,&pro_tm);
    char yyyymmddhhmmss[21] = {0};
    sprintf(&yyyymmddhhmmss[0],"%4.4d",pro_tm.tm_year +1900);
    sprintf(&yyyymmddhhmmss[4],"%c",'-');
    sprintf(&yyyymmddhhmmss[5],"%2.2d",pro_tm.tm_mon + 1);
    sprintf(&yyyymmddhhmmss[7],"%c",'-');
    sprintf(&yyyymmddhhmmss[8],"%2.2d",pro_tm.tm_mday);
    sprintf(&yyyymmddhhmmss[10],"%c",' ');
    sprintf(&yyyymmddhhmmss[11],"%2.2d",pro_tm.tm_hour);
    sprintf(&yyyymmddhhmmss[13],"%c",':');
    sprintf(&yyyymmddhhmmss[14],"%2.2d",pro_tm.tm_min);
    sprintf(&yyyymmddhhmmss[16],"%c",':');
    sprintf(&yyyymmddhhmmss[17],"%2.2d",pro_tm.tm_sec);

    std::ostringstream sqlstr;
    sqlstr << "insert into "<< MYSQL_PRODUCT_PATH
           <<" (id,station_id,datetime,product_code,elev,path,product_type,length,creat_tmsp) values ('"
           << param.code << "','"
           << param.stationId << "','"
           << string(param.datetime).substr(0,19) << "','"
           << param.productCode << "','"
           << param.elevIndex << "','"
           << param.pathStr << "','"
           << param.productType << "','"
           << param.fileSize << "','"
           <<yyyymmddhhmmss<<"');";

    std::string sqlStr = sqlstr.str();
    qDebug()<<QString::fromStdString(sqlStr);
    bool statue=m_pDBInterface->commonSQL(sqlStr);
    return statue;
}

bool CDBIntf::recordRecPPIPathInfo(ProdPathInfo &param)
{
    if(m_pDBInterface == nullptr) return false;
    tm pro_tm;
    time_t t = time(NULL);
    localtime_r(&t,&pro_tm);
    char yyyymmddhhmmss[21] = {0};
    sprintf(&yyyymmddhhmmss[0],"%4.4d",pro_tm.tm_year + 1900);
    sprintf(&yyyymmddhhmmss[4],"%c",'-');
    sprintf(&yyyymmddhhmmss[5],"%2.2d",pro_tm.tm_mon + 1);
    sprintf(&yyyymmddhhmmss[7],"%c",'-');
    sprintf(&yyyymmddhhmmss[8],"%2.2d",pro_tm.tm_mday);
    sprintf(&yyyymmddhhmmss[10],"%c",' ');
    sprintf(&yyyymmddhhmmss[11],"%2.2d",pro_tm.tm_hour);
    sprintf(&yyyymmddhhmmss[13],"%c",':');
    sprintf(&yyyymmddhhmmss[14],"%2.2d",pro_tm.tm_min);
    sprintf(&yyyymmddhhmmss[16],"%c",':');
    sprintf(&yyyymmddhhmmss[17],"%2.2d",pro_tm.tm_sec);

    std::ostringstream sqlstr;
    sqlstr << "insert into "<< MYSQL_PRODUCT_PATH
           <<" (id,station_id,datetime,product_code,elev,path,product_type,length,is_rec,creat_tmsp) values ('"
           << param.code << "','"
           << param.stationId << "','"
           << string(param.datetime).substr(0,19) << "','"
           << param.productCode << "','"
           << param.elevIndex << "','"
           << param.pathStr << "','"
           << param.productType << "','"
           << param.fileSize << "','"
           << '1' << "','"
           << yyyymmddhhmmss << "');";

    std::string sqlStr = sqlstr.str();
    bool statue = m_pDBInterface->commonSQL(sqlStr);
    return statue;
}

//bool CDBIntf::recordProductPathInfonew(ProdPathInfo& param)
//{
//    if(m_pDBInterface == nullptr) return false;
//    tm pro_tm;
//    time_t t = time(NULL);
//    localtime_r(&t,&pro_tm);
//    char yyyymmddhhmmss[21] = {0};
//    sprintf(&yyyymmddhhmmss[0],"%4.4d",pro_tm.tm_year +1900);
//    sprintf(&yyyymmddhhmmss[4],"%c",'-');
//    sprintf(&yyyymmddhhmmss[5],"%2.2d",pro_tm.tm_mon + 1);
//    sprintf(&yyyymmddhhmmss[7],"%c",'-');
//    sprintf(&yyyymmddhhmmss[8],"%2.2d",pro_tm.tm_mday);
//    sprintf(&yyyymmddhhmmss[10],"%c",' ');
//    sprintf(&yyyymmddhhmmss[11],"%2.2d",pro_tm.tm_hour);
//    sprintf(&yyyymmddhhmmss[13],"%c",':');
//    sprintf(&yyyymmddhhmmss[14],"%2.2d",pro_tm.tm_min);
//    sprintf(&yyyymmddhhmmss[16],"%c",':');
//    sprintf(&yyyymmddhhmmss[17],"%2.2d",pro_tm.tm_sec);

//    std::ostringstream sqlstr;
//    sqlstr << "insert into "<< MYSQL_PRODUCT_PATH
//           <<" (id,station_id,datetime,product_code,elev,path,product_type,length,creat_tmsp) values ('"
//           << param.code << "','"
//           << param.stationId << "','"
//           << string(param.datetime).substr(0,19) << "','"
//           << param.productCode << "','"
//           << param.elevIndex << "','"
//           << param.pathStr << "','"
//           << param.productType << "','"
//           << param.fileSize << "','"
//           <<yyyymmddhhmmss<<"');";

//    std::string sqlStr = sqlstr.str();
//    qDebug()<<QString::fromStdString(sqlStr);
//    bool statue=m_pDBInterface->commonSQL(sqlStr);
//    return statue;
//}
