#include <QCoreApplication>
#include <iostream>
#include <dlfcn.h>
#include <QDir>
#include "cmdline.h"
#include "dirent.h"
#include "IniParser/INIParser.h"
#include "lib_file_io.h"
#include "lib_cappi_mod.h"
#include <QDebug>
#include <QTime>

using namespace std;

// 文件路径的目录部分,最后一个"/\\"之前的部分
string getDirectoryPath(const string &filePath)
{
    size_t found = filePath.find_last_of("/\\");
    if (found != string::npos)
    {
        return filePath.substr(0, found);
    }
    return "";
}

vector<string> stringSplit(const string &str, char delim)
{
    stringstream ss(str);
    string item;
    vector<string> elems;
    while (getline(ss, item, delim))
    {
        if (!item.empty())
        {
            elems.push_back(item);
        }
    }
    return elems;
}

bool DoLoadConfigure_CAPPI(s_Pro_Grid::RadarProduct &m_iCAPPIproduct, int &m_nDebugLevel, int &m_iMaxAlgoWorkerNum)
{
    INIParser parser;
    if (parser.ReadINI("../conf/Algorithms/CappiGridS.ini"))
    {
        m_iCAPPIproduct.MapProjInfo.mapproj = atoi(parser.GetValue("CAPPI", "mapproj").c_str());
        m_iCAPPIproduct.MapProjInfo.ctrlat = atof(parser.GetValue("CAPPI", "ctrlat").c_str());
        m_iCAPPIproduct.MapProjInfo.ctrlon = atof(parser.GetValue("CAPPI", "ctrlon").c_str());
        m_iCAPPIproduct.GridInfo.nrow = atoi(parser.GetValue("CAPPI", "nrow").c_str());
        m_iCAPPIproduct.GridInfo.ncolumn = atoi(parser.GetValue("CAPPI", "ncolumn").c_str());
        //m_iCAPPIproduct.GridInfo.nz = atoi(parser.GetValue("CAPPI", "height0").c_str());
        m_iCAPPIproduct.GridInfo.drow = atoi(parser.GetValue("CAPPI", "drow").c_str());
        m_iCAPPIproduct.GridInfo.dcolumn = atoi(parser.GetValue("CAPPI", "dcolumn").c_str());
        auto height0 = atoi(parser.GetValue("CAPPI", "height0").c_str());
        auto zres0 = atoi(parser.GetValue("CAPPI", "zres0").c_str());
        auto height1 = atoi(parser.GetValue("CAPPI", "height1").c_str());
        auto zres1 = atoi(parser.GetValue("CAPPI", "zres1").c_str());
        auto height2 = atoi(parser.GetValue("CAPPI", "height2").c_str());

        if (zres0 <= 0)
        {
            zres0 = 500;
        }
        if (zres1 <= 0)
        {
            zres1 = 500;
        }

        int nz0 = (height1 - height0) / zres0;
        int nz1 = (height2 - height1) / zres1 + 1;
        m_iCAPPIproduct.GridInfo.z.clear();
        for (int height = height0; height < height1; height += zres0)
        {
            m_iCAPPIproduct.GridInfo.z.push_back(height);
        }
        for (int height = height1; height <= height2; height += zres0)
        {
            m_iCAPPIproduct.GridInfo.z.push_back(height);
        }

        m_iCAPPIproduct.GridInfo.nz = m_iCAPPIproduct.GridInfo.z.size();

        m_nDebugLevel = atoi(parser.GetValue("COMMON", "DebugLevel").c_str());

#ifdef ALGORITHM_DEBUG_CAPPI_GRID_S
        m_iMaxAlgoWorkerNum = 1;
#else
        int number = atoi(parser.GetValue("COMMON", "MaxWorkerThreadNum").c_str());
        m_iMaxAlgoWorkerNum = (number > 1) ? number : 1;
#endif
        return true;
    }
    return false;
}

int main(int argc, char *argv[])
{
    // read in and out config;
    QCoreApplication a(argc, argv);

    // 开始计时
    QTime time_start_in;
    time_start_in.start();
    qDebug() << "Algo_CAPPI_Grid: Program starts execution" << endl;

    cmdline::parser oParser;
    oParser.add<string>("inputfile", 'i', "input radar base file", true, "");
    oParser.add<string>("outpath", 'o', "output full file path", true);
    oParser.add("help", 0, "print this message");

    bool ok = oParser.parse(argc, argv);
    if (!ok)
    {
        cerr << oParser.usage();
        return -1;
    }

    string sourceFileName, targetFileName;
    sourceFileName = oParser.get<string>("inputfile");
    targetFileName = oParser.get<string>("outpath");
    cout << "sourceFileName:" << sourceFileName << std::endl;
    cout << "targetFileName:" << targetFileName << std::endl;
    string productPath = getDirectoryPath(targetFileName);
    DIR *dir = opendir(productPath.c_str());
    if (dir == nullptr)
    {
        cout << "Product path does not exit, creating " + productPath << std::endl;
        string command = "mkdir -p " + productPath;
        if (-1 == system(command.c_str()))
        {
            cout << "create product path fail!" << std::endl;
            return -1;
        }
    }
    else
    {
        (void)closedir(dir);
    }
    QString radarFileName;
    radarFileName = QString::fromStdString(sourceFileName).split("/").last();
    string extracted = radarFileName.mid(3, 5).toStdString();
    cout << extracted << std::endl;
    /***********************************************************************************/
    // CAPPI_Grid config
    int m_nDebugLevel = 0;
    int m_iMaxAlgoWorkerNum = 0;
    s_Pro_Grid::RadarProduct m_iCAPPIproduct;

    if (!DoLoadConfigure_CAPPI(m_iCAPPIproduct, m_nDebugLevel, m_iMaxAlgoWorkerNum))
    {
        cout << "load CAPPI_Grid.ini failed, exit!" << std::endl;
        return -1;
    }
    cout << "load CAPPI_Grid.ini configures done!!" << std::endl;
    /***********************************************************************************/
    int status = 0;
    // base sourceFileName read radar raw data;
    CNrietFile *m_pFileIO = nullptr;
#ifdef ALGORITHM_DEBUG_FILE_IO
    m_pFileIO = new CNrietFileIO();
#else
    void *m_pIoHandle = nullptr;
    m_pIoHandle = dlopen("../lib/libFileIO.so", RTLD_LAZY);
    if (m_pIoHandle)
    {
        // 使用 dlsym 函数获取 GetFileInstance 函数的指针
        CNrietFileIO * (*pGetFileInstance)(void);
        pGetFileInstance = (CNrietFileIO * (*)(void))dlsym(m_pIoHandle, "GetFileInstance");
        if (pGetFileInstance)
        {
            // 调用函数以获取CNrietFileIO的实例
            m_pFileIO = (*pGetFileInstance)();
        }
        else
        {
            cout << "load GetFileInstance API of FileIO fail!" << std::endl;
            return -1;
        }
    }
    else
    {
        cout << "load library libFileIO.so fail!" << std::endl;
        return -1;
    }
#endif
    cout << "create FileIO instance done!" << std::endl;

    // load radar data
    status = m_pFileIO->LoadDataFromFile((void *)sourceFileName.c_str(), 2);
    if (status)
    {
        cout << "Error: Read file fail, file:" + sourceFileName << std::endl;
        m_pFileIO->FreeData();
        return -1;
    }
    else
    {
        cout << "Read file success, file:" + sourceFileName << std::endl;
    }

    WRADRAWDATA *data = nullptr;

    data = (WRADRAWDATA *)m_pFileIO->PutRadarRawData();
    /***********************************************************************************/
    // load library libCAPPI_Mod.so;
    CNrietAlogrithm *m_pAlgorithm = nullptr;
    void *m_pAlgoHandle = nullptr;
#ifdef ALGORITHM_DEBUG_CAPPI_GRID_S
    m_pAlgorithm = new CAlgoCAPPI();
#else
    m_pAlgoHandle = dlopen("../lib/libCAPPI.so", RTLD_LAZY);
    if (m_pAlgoHandle)
    {
        CNrietAlogrithm * (*pGetAlgoInstance)(void);
        pGetAlgoInstance = (CNrietAlogrithm * (*)(void))dlsym(m_pAlgoHandle, "GetAlgoInstance");
        if (pGetAlgoInstance)
        {
            m_pAlgorithm = (*pGetAlgoInstance)();
        }
        else
        {
            cout << "load pGetInstance API of libCAPPI_Mod.so fail!" << std::endl;
            return -1;
        }
    }
    else
    {
        cout << "load library libCAPPI_Mod.so fail!" << std::endl;
        return -1;
    }
#endif
    cout << "create CAPPI_Grid algorithm instance done!" << std::endl;

    // CAPPI_Grid make product
    {
        m_pAlgorithm->Init();
        m_pAlgorithm->SetDebugLevel(m_nDebugLevel);

        vector<s_Pro_Grid::RadarProduct> m_RadarCAPPIPro_org;
        vector<s_Pro_Grid::RadarProduct> *m_RadarCAPPIPro_out = nullptr;    //产品头，包含雷达数据头及产品生成参数
        m_RadarCAPPIPro_org.resize(8);
        //    m_RadarCAPPIPro_org.resize(1);
        //1-滤波前反射率dBT
        //2-滤波后反射率dBZ
        //3-径向速度V
        //4-谱宽W
        //5-信号质量指数SQI
        //6-杂波相位一致性CPA
        //7-差分反射率ZDR
        //8-退偏振比LDR
        //9-协相关系数CC
        //10-差分相移fDP
        //11-差分相移率KDP
        //12-杂波可能性CP
        //13-Reserved保留
        m_RadarCAPPIPro_org.at(0).ProInfo.ProductionID = 101;
        m_RadarCAPPIPro_org.at(1).ProInfo.ProductionID = 102;
        m_RadarCAPPIPro_org.at(2).ProInfo.ProductionID = 103;
        m_RadarCAPPIPro_org.at(3).ProInfo.ProductionID = 104;
        m_RadarCAPPIPro_org.at(4).ProInfo.ProductionID = 107;
        m_RadarCAPPIPro_org.at(5).ProInfo.ProductionID = 109;
        m_RadarCAPPIPro_org.at(6).ProInfo.ProductionID = 110;
        m_RadarCAPPIPro_org.at(7).ProInfo.ProductionID = 111;

        for (int i_pro = 0 ; i_pro < m_RadarCAPPIPro_org.size(); i_pro++)
        {
            m_RadarCAPPIPro_org.at(i_pro).MapProjInfo.mapproj = m_iCAPPIproduct.MapProjInfo.mapproj;
            m_RadarCAPPIPro_org.at(i_pro).MapProjInfo.ctrlat = m_iCAPPIproduct.MapProjInfo.ctrlat;    // Station lat 31.956
            m_RadarCAPPIPro_org.at(i_pro).MapProjInfo.ctrlon = m_iCAPPIproduct.MapProjInfo.ctrlon;   // Station lon 119.219
            m_RadarCAPPIPro_org.at(i_pro).GridInfo.nrow = m_iCAPPIproduct.GridInfo.nrow;
            m_RadarCAPPIPro_org.at(i_pro).GridInfo.ncolumn = m_iCAPPIproduct.GridInfo.ncolumn;
            m_RadarCAPPIPro_org.at(i_pro).GridInfo.nz = m_iCAPPIproduct.GridInfo.nz;
            m_RadarCAPPIPro_org.at(i_pro).GridInfo.drow = m_iCAPPIproduct.GridInfo.drow;     // unit:1/50000°~~~2 m
            m_RadarCAPPIPro_org.at(i_pro).GridInfo.dcolumn = m_iCAPPIproduct.GridInfo.dcolumn;     // 即 ~100 m 分辨率
            m_RadarCAPPIPro_org.at(i_pro).GridInfo.z = m_iCAPPIproduct.GridInfo.z;

            //        if (m_RadarCAPPIPro_org.at(i_pro).GridInfo.nz <= 12){
            //            for (int iz = 0; iz < m_RadarCAPPIPro_org.at(i_pro).GridInfo.nz; iz++)
            //            {
            //                m_RadarCAPPIPro_org.at(i_pro).GridInfo.z[iz] = 500 * (iz + 1);
            //            }
            //        }
            //        else
            //        {
            //            for (int iz = 0; iz < 12; iz++)
            //            {
            //                m_RadarCAPPIPro_org.at(i_pro).GridInfo.z[iz] = 500 * (iz + 1);
            //            }
            //            for (int iz = 12; iz< m_RadarCAPPIPro_org.at(i_pro).GridInfo.nz; iz++)
            //            {
            //                m_RadarCAPPIPro_org.at(i_pro).GridInfo.z[iz] = 1000 * (iz + 1) - 6000;
            //            }
            //        }
        }

        status = m_pAlgorithm->LoadParameters(&m_RadarCAPPIPro_org);
        if (status)
        {
            cout << "CAlgoCAPPI loadParameters failed." << std::endl;
            return -1;
        }
        status =  m_pAlgorithm->LoadStdData(data);
        if (status)
        {
            cout << "CAlgoCAPPI loadstdData failed." << std::endl;
            return -1;
        }
        status = m_pAlgorithm->MakeProduct();
        if (status)
        {
            cout << "CAlgoCAPPI make product failed." << std::endl;
            return -1;
        }

        m_RadarCAPPIPro_out = static_cast<vector<s_Pro_Grid::RadarProduct>*>(m_pAlgorithm->GetProduct());
        for (unsigned long i_pro = 0; i_pro < m_RadarCAPPIPro_out->size(); i_pro++)
        {
            if (m_RadarCAPPIPro_out->at(i_pro).SiteInfo.size() == 0)
            {
                m_RadarCAPPIPro_out->erase(m_RadarCAPPIPro_out->begin() + i_pro);
                m_RadarCAPPIPro_org.erase(m_RadarCAPPIPro_org.begin() + i_pro);
                i_pro--;
            }
        }

        /***********************************************************************************/
        // write CAPPI_Grid product files by FileIO;
        vector<string> m_FileName;
        m_FileName.reserve(m_RadarCAPPIPro_org.size());
        m_pFileIO->getSITECODE(extracted);

        for (int i_out = 0; i_out < m_RadarCAPPIPro_out->size(); i_out++)
        {
            m_FileName.push_back(static_cast<char *>(m_pFileIO->GetFileName(&m_RadarCAPPIPro_out->at(i_out), 0)));
        }

        if (m_RadarCAPPIPro_out->size() != m_FileName.size())
        {
            m_pAlgorithm->FreeData();
            cout << "product file name mismatch with product, drop all!" << std::endl;
            return -1;
        }
        else
        {
            cout << "Starting product path output." << std::endl;
            for (int ipro = 0; ipro < m_RadarCAPPIPro_out->size(); ipro++)
            {
                QDir dir = QDir(productPath.c_str()).absolutePath();
                string fullPath = QDir(productPath.c_str()).absolutePath().toStdString() + "/" + \
                                  m_FileName.at(ipro) + ".Z";

                string tmpDir = getDirectoryPath(fullPath);
                DIR *m_pDir = opendir(tmpDir.c_str());
                if (m_pDir == nullptr)
                {
//                    cout << "Product path does not exit, creating " + tmpDir << endl;
                    string command = "mkdir -p " + tmpDir;
                    if (-1 == system(command.c_str()))
                    {
                        cout << "create product path fail!" << std::endl;
                        return -1;
                    }
                }
                else
                {
                    (void)closedir(m_pDir);
                }
                cout << fullPath;
                if (ipro != (m_RadarCAPPIPro_out->size() - 1))
                {
                    cout << ",";
                }
                else
                {
                    cout << std::endl;
                }

                char FileDir[1024] = {0};
                strncpy(FileDir, fullPath.c_str(), fullPath.length());
                m_pFileIO->LoadDataAndSaveFile(&m_RadarCAPPIPro_out->at(ipro), FileDir);
            }
            cout << "Ending product path output." << std::endl;
        }

        m_pAlgorithm->FreeData();
    }
    m_pFileIO->FreeData();
    /***********************************************************************************/

    // 程序逻辑执行完毕
    qDebug() << "Algo_CAPPI_Grid: Program execution complete" << endl;

    // 计算程序执行时间
    qDebug() << "Time Cost:";
    qDebug() << time_start_in.elapsed();
    qDebug() << "  ms";
    return 0;
}
