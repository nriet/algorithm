#ifndef NRIET_DBCOMMOMINTERFACE_H
#define NRIET_DBCOMMOMINTERFACE_H

#include <string>
#include <vector>
using namespace  std;

class CNrietDBCommonInterface
{
public:
    virtual ~CNrietDBCommonInterface() = default;
    virtual bool Initilize(std::string host,std::string user,std::string pass,std::string db,int port)=0;
    virtual bool UnInitilize()=0;
    virtual void Shutdown(void) =0;
    virtual void Update(void) =0;

    //example:
    //    std::string tablename="t_dslog";
    //    std::vector<std::string> tableValues;
    //    tableValues.push_back("VTB20210430201003.010.zip");
    //    tableValues.push_back("2023-12-28 11:18:36");
    //    tableValues.push_back("2022-09-28 11:18:36");
    //    bool test4= myDB->commonInsert(tablename,tableValues);
    virtual bool commonInsert(std::string ,std::vector<std::string> ) =0;

    virtual bool commonInsertWithSQLStr(std::string sqlStr) =0;

    //example:
    //    std::string tablename="t_dslog";
    //    std::string SelectCondition="datafilename='VTB20210430201111.010.zip'";
    //    std::vector<std::vector<std::string>> selectInfo;
    //    bool test2= myDB->commonSelectRow(tablename,SelectCondition,selectInfo);
    virtual bool commonSelectRow(std::string ,std::string ,std::vector<std::vector<string>> &) =0;

    //example:
    //std::vector<std::vector<std::string>> selectInfo;
    //std::string SQLString="select min(datetime) as datetime from t_product_path";
    //bool test6=myDB->commonSelectWithSQLStr(SQLString,selectInfo);
    virtual bool commonSelectWithSQLStr(std::string ,std::vector<std::vector<string>> &) =0;

    //example:
    //    std::string tablename="t_dslog";
    //    std::string deleteCondition="datafilename='VTB20210430201111.010.zip'";
    //    bool test3=myDB->commonDeleteRow(tablename,deleteCondition);
    virtual bool commonDeleteRow(std::string ,std::string ) =0;
    virtual bool commonDeleteWithSQLStr(std::string sqlStr) =0;

    //example:
    //    bool test5=myDB->commonCall("recordlog","'WRadDataMgt.cpp:run',4,4,'2222'");
    virtual bool commonCall(std::string ,std::string ) =0;

    virtual bool commonSQL(std::string sqlStr) =0;
};

#endif // NRIET_DBCOMMOMINTERFACE_H
