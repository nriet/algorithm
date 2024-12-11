#include <QCoreApplication>
#include <iostream>
#include <dlfcn.h>
#include <QDir>
#include "cmdline.h"
#include "dirent.h"
#include "IniParser/INIParser.h"
#include "lib_file_io.h"
#include "lib_ppis.h"
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

bool DoLoadConfigure_PPIS(int &m_nDebugLevel)
{
    INIParser INIparser;
    if (INIparser.ReadINI("../conf/Algorithms/PPIS.ini"))
    {
        m_nDebugLevel = atoi(INIparser.GetValue("COMMON", "DebugLevel").c_str());
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
    qDebug() << "Algo_PPIS: Program starts execution" << endl;

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
    /***********************************************************************************/
    // PPIS config
    int m_nDebugLevel = 0;
    if (!DoLoadConfigure_PPIS(m_nDebugLevel))
    {
        cout << "load PPIS.ini failed, exit!" << std::endl;
        return -1;
    }
    cout << "load PPIS.ini configures done!!" << std::endl;
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
    // load library libPPIS.so;
    CNrietAlogrithm *m_pCAlgoPPIS = nullptr;
#ifdef ALGORITHM_DEBUG_PPI_S
    m_pCAlgoPPIS = new CAlgoPPIS();
#else
    void *m_pPPISHandle = nullptr;
    m_pPPISHandle = dlopen("../lib/libPPIS.so", RTLD_LAZY);
    if (m_pPPISHandle)
    {
        CNrietAlogrithm * (*pGetPPISInstance)(void);
        pGetPPISInstance = (CNrietAlogrithm * (*)(void))dlsym(m_pPPISHandle, "GetAlgoInstance");
        if (pGetPPISInstance)
        {
            m_pCAlgoPPIS = (*pGetPPISInstance)();
        }
        else
        {
            cout << "load pGetInstance API of libPPIS.so fail!" << std::endl;
            return -1;
        }
    }
    else
    {
        cout << "load library libPPIS.so fail!" << std::endl;
        return -1;
    }
#endif
    cout << "create PPIS algorithm instance done!" << std::endl;

    // PPIS make product
    {
        m_pCAlgoPPIS->Init();
        m_pCAlgoPPIS->SetDebugLevel(m_nDebugLevel);

        vector<WRADPRODATA> *m_RadarPro_out = nullptr;
        vector<WRADPRODATA_PARA_IN> m_paras_in;
        vector<RADIALFORMAT> m_paras_in_productdata;
        WRADPRODATA_PARA_IN m_paras_in_temp;
        RADIALFORMAT m_paras_in_productdata_temp;

        auto i_radial = 0;
        for (auto i_cut = 0; i_cut < data->commonBlock.cutconfig.size(); i_cut++)
        {
            for (i_radial; i_radial < data->radials.size(); i_radial++)
            {
                if (data->radials.at(i_radial).radialheader.ElevationNumber == (i_cut + 1))
                {
                    for (int i_var = 0; i_var < data->radials.at(i_radial).momentblock.size(); i_var++)
                    {
                        m_paras_in_temp.commonBlock = data->commonBlock;
                        m_paras_in_temp.commonBlockPAR = data->commonBlockPAR;
                        m_paras_in_temp.commonBlock.genericheader.GenericType = 2;
                        m_paras_in_temp.productheader.productheader.ProductType = PTYPE_PPI;

                        m_paras_in_temp.productheader.productdependentparameter.ppiparameter.Elevation \
                            = data->commonBlock.cutconfig.at(i_cut).Elevation;
                        //m_paras_in_temp.productheader.productheader.DataType1 \
                        //  = data.radials.front().momentblock.at(i_var).momentheader.DataType;
                        //modified by xfwu 20210604:
                        m_paras_in_temp.productheader.productheader.DataType1 \
                            = data->radials.at(i_radial).momentblock.at(i_var).momentheader.DataType;

                        //m_paras_in_productdata_temp.RadialHeader.DataType \
                        //  = data.radials.front().momentblock.at(i_var).momentheader.DataType;
                        //modified by xfwu 20210604
                        m_paras_in_productdata_temp.RadialHeader.DataType \
                            = data->radials.at(i_radial).momentblock.at(i_var).momentheader.DataType;

                        if (m_paras_in_productdata_temp.RadialHeader.DataType == 3 \
                                || m_paras_in_productdata_temp.RadialHeader.DataType == 4)
                        {
                            m_paras_in_productdata_temp.RadialHeader.Resolution \
                                = data->commonBlock.cutconfig.at(i_cut).DopplerResolution;
                        }
                        else
                        {
                            m_paras_in_productdata_temp.RadialHeader.Resolution \
                                = data->commonBlock.cutconfig.at(i_cut).LogResolution;
                        }
                        m_paras_in_productdata_temp.RadialData.resize(1);
                        m_paras_in_productdata_temp.RadialData.at(0).RadialDataHead.AnglularWidth \
                                                              = data->commonBlock.cutconfig.at(i_cut).AngularResolution;

                        m_paras_in.push_back(m_paras_in_temp);
                        m_paras_in_productdata.push_back(m_paras_in_productdata_temp);
                        //m_paras_in.back().productdatapoint = &m_paras_in_productdata.back();
                    }
                    break;  //get info from first radial of each cut
                }
            }
        }
        for (int i = 0; i < m_paras_in.size(); i++)
        {
            m_paras_in.at(i).productdatapoint = &m_paras_in_productdata.at(i);
        }

        status = m_pCAlgoPPIS->LoadParameters(&m_paras_in);
        if (status)
        {
            cout << "CAlgoPPI loadParameters failed." << std::endl;
            return -1;
        }
        status =  m_pCAlgoPPIS->LoadStdData(data);
        if (status)
        {
            cout << "CAlgoPPI loadstdData failed." << std::endl;
            return -1;
        }
        status = m_pCAlgoPPIS->MakeProduct();
        if (status)
        {
            cout << "CAlgoPPI make product failed." << std::endl;
            return -1;
        }
        m_RadarPro_out = (vector<WRADPRODATA> *)m_pCAlgoPPIS->GetProduct();
        for (unsigned long i_pro = 0; i_pro < m_RadarPro_out->size(); i_pro++)
        {
            if (m_RadarPro_out->at(i_pro).dataBlock.size() == 0)
            {
                m_RadarPro_out->erase(m_RadarPro_out->begin() + i_pro);
                m_paras_in.erase(m_paras_in.begin() + i_pro);
                i_pro--;
            }
        }

        /***********************************************************************************/
        // write ppis product files by FileIO;
        vector<string> m_FileName;
        m_FileName.reserve(m_paras_in.size());
        m_pFileIO->getSITECODE(extracted);

        for (int i_out = 0; i_out < m_RadarPro_out->size(); i_out++)
        {
            m_FileName.push_back(static_cast<char *>(m_pFileIO->GetFileName(&m_RadarPro_out->at(i_out), 0)));
        }

        if (m_RadarPro_out->size() != m_FileName.size())
        {
            m_pCAlgoPPIS->FreeData();
            cout << "product file name mismatch with product, drop all!" << std::endl;
            return -1;
        }
        else
        {
            cout << "Starting product path output." << std::endl;
            for (int ipro = 0; ipro < m_RadarPro_out->size(); ipro++)
            {
                QDir dir = QDir(productPath.c_str()).absolutePath();
                string fullPath = QDir(productPath.c_str()).absolutePath().toStdString() + "/" + \
                                  m_FileName.at(ipro) + ".Z";

                string tmpDir = getDirectoryPath(fullPath);
                DIR *m_pDir = opendir(tmpDir.c_str());
                if (m_pDir == nullptr)
                {
//                    cout << "Product path does not exit, creating " + tmpDir << std::endl;
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
                if (ipro != (m_RadarPro_out->size() - 1))
                {
                    cout << ",";
                }
                else
                {
                    cout << std::endl;
                }

                char FileDir[1024] = {0};
                strncpy(FileDir, fullPath.c_str(), fullPath.length());
                m_pFileIO->LoadDataAndSaveFile(&m_RadarPro_out->at(ipro), FileDir);
            }
            cout << "Ending product path output." << std::endl;
        }

        m_pCAlgoPPIS->FreeData();
    }
    m_pFileIO->FreeData();
    /***********************************************************************************/

    // 程序逻辑执行完毕
    qDebug() << "Algo_PPIS: Program execution complete" << endl;

    // 计算程序执行时间
    qDebug() << "Time Cost:";
    qDebug() << time_start_in.elapsed();
    qDebug() << "  ms";
    return 0;
}
