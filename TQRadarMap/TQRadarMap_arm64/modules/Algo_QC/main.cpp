#include <QCoreApplication>
#include <iostream>
#include <dlfcn.h>
#include <QDir>
#include "cmdline.h"
#include "dirent.h"
#include "IniParser/INIParser.h"
#include "lib_file_io.h"
#include "lib_qc.h"
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

bool DoLoadConfigure_QC(vector<QCParams> &param)
{
    INIParser INIparser;
    if (INIparser.ReadINI("../conf/Algorithms/QC.ini"))
    {
        QCParams tmp;
        // QCFLAG
        memcpy(&tmp.FuncName[0], INIparser.GetValue("QCFLAG", "FuncName").c_str(), sizeof(tmp.FuncName));
        tmp.Scope = atoi(INIparser.GetValue("QCFLAG", "Scope").c_str());
        tmp.Method = atoi(INIparser.GetValue("QCFLAG", "Method").c_str());
        auto typeStr = INIparser.GetValue("QCFLAG", "Type");
        auto sites = stringSplit(typeStr, '&');
        for (auto iter : sites)
        {
            tmp.Type.push_back(atoi(iter.c_str()));
        }
        typeStr = INIparser.GetValue("QCFLAG", "Except");
        sites = stringSplit(typeStr, '&');
        for (auto iter : sites)
        {
            tmp.Except.push_back(atoi(iter.c_str()));
        }
        param.push_back(tmp);
        // CalculateKDP
        tmp.Type.clear();
        tmp.Except.clear();
        memcpy(&tmp.FuncName[0], INIparser.GetValue("CalculateKDP", "FuncName").c_str(), sizeof(tmp.FuncName));
        tmp.Scope = atoi(INIparser.GetValue("CalculateKDP", "Scope").c_str());
        tmp.Method = atoi(INIparser.GetValue("CalculateKDP", "Method").c_str());
        typeStr = INIparser.GetValue("CalculateKDP", "Type");
        sites = stringSplit(typeStr, '&');
        for (auto iter : sites)
        {
            tmp.Type.push_back(atoi(iter.c_str()));
        }
        typeStr = INIparser.GetValue("CalculateKDP", "Except");
        sites = stringSplit(typeStr, '&');
        for (auto iter : sites)
        {
            tmp.Except.push_back(atoi(iter.c_str()));
        }
        param.push_back(tmp);
        // Zdr_PHDP_Correct
        tmp.Type.clear();
        tmp.Except.clear();
        memcpy(&tmp.FuncName[0], INIparser.GetValue("Zdr_PHDP_Correct", "FuncName").c_str(), sizeof(tmp.FuncName));
        tmp.Scope = atoi(INIparser.GetValue("Zdr_PHDP_Correct", "Scope").c_str());
        tmp.Method = atoi(INIparser.GetValue("Zdr_PHDP_Correct", "Method").c_str());
        typeStr = INIparser.GetValue("Zdr_PHDP_Correct", "Type");
        sites = stringSplit(typeStr, '&');
        for (auto iter : sites)
        {
            tmp.Type.push_back(atoi(iter.c_str()));
        }
        typeStr = INIparser.GetValue("Zdr_PHDP_Correct", "Except");
        sites = stringSplit(typeStr, '&');
        for (auto iter : sites)
        {
            tmp.Except.push_back(atoi(iter.c_str()));
        }
        param.push_back(tmp);
        // UnflodVel
        tmp.Type.clear();
        tmp.Except.clear();
        memcpy(&tmp.FuncName[0], INIparser.GetValue("UnflodVel", "FuncName").c_str(), sizeof(tmp.FuncName));
        tmp.Scope = atoi(INIparser.GetValue("UnflodVel", "Scope").c_str());
        tmp.Method = atoi(INIparser.GetValue("UnflodVel", "Method").c_str());
        typeStr = INIparser.GetValue("UnflodVel", "Type");
        sites = stringSplit(typeStr, '&');
        for (auto iter : sites)
        {
            tmp.Type.push_back(atoi(iter.c_str()));
        }
        typeStr = INIparser.GetValue("UnflodVel", "Except");
        sites = stringSplit(typeStr, '&');
        for (auto iter : sites)
        {
            tmp.Except.push_back(atoi(iter.c_str()));
        }
        param.push_back(tmp);
        // AttenuationCorrection
        tmp.Type.clear();
        tmp.Except.clear();
        memcpy(&tmp.FuncName[0], INIparser.GetValue("AttenuationCorrection", "FuncName").c_str(), sizeof(tmp.FuncName));
        tmp.Scope = atoi(INIparser.GetValue("AttenuationCorrection", "Scope").c_str());
        tmp.Method = atoi(INIparser.GetValue("AttenuationCorrection", "Method").c_str());
        typeStr = INIparser.GetValue("AttenuationCorrection", "Type");
        sites = stringSplit(typeStr, '&');
        for (auto iter : sites)
        {
            tmp.Type.push_back(atoi(iter.c_str()));
        }
        typeStr = INIparser.GetValue("AttenuationCorrection", "Except");
        sites = stringSplit(typeStr, '&');
        for (auto iter : sites)
        {
            tmp.Except.push_back(atoi(iter.c_str()));
        }
        param.push_back(tmp);
        return true;
    }
    return false;
}

std::vector<std::string> splitPath(const std::string &path)
{
    std::vector<std::string> parts;
    std::istringstream stream(path);
    std::string item;

    while (std::getline(stream, item, '/'))
    {
        if (!item.empty())
        {
            parts.push_back(item);
        }
    }

    return parts;
}

int main(int argc, char *argv[])
{
    // read in and out config;
    QCoreApplication a(argc, argv);

    // 开始计时
    QTime time_start_in;
    time_start_in.start();
    qDebug() << "Algo_QC: Program starts execution" << endl;

    cmdline::parser oParser;
    oParser.add<string>("inputfile", 'i', "input radar base file", true, "");
    oParser.add<string>("sitecode", 's', "input site code", true, "");
    oParser.add<string>("outpath", 'o', "output full file path", true);
    oParser.add("help", 0, "print this message");

    bool ok = oParser.parse(argc, argv);
    if (!ok)
    {
        cerr << oParser.usage();
        return -1;
    }

    string sourceFileName, targetFileName, sourceSiteCode;
    sourceFileName = oParser.get<string>("inputfile");
    targetFileName = oParser.get<string>("outpath");
    sourceSiteCode = oParser.get<string>("sitecode");
    cout << "sourceFileName:" << sourceFileName << std::endl;
    cout << "targetFileName:" << targetFileName << std::endl;
    cout << "sourceSiteCode:" << sourceSiteCode << std::endl;
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
    string scanType;
    if (radarFileName.contains("vtb") || radarFileName.contains("VTB") || radarFileName.contains("FMT") || radarFileName.endsWith("V") || radarFileName.endsWith("v") || radarFileName.contains("vol") || radarFileName.contains("VOL"))
    {
        scanType = "VOL";
    }
    else if (radarFileName.contains("PTB") || radarFileName.contains("ptb") || radarFileName.endsWith("P") || radarFileName.endsWith("p") || radarFileName.contains("PPI") || radarFileName.contains("ppi"))
    {
        scanType = "PPI";
    }
    else if (radarFileName.contains("RTB") || radarFileName.contains("rtb") || radarFileName.endsWith("R") || radarFileName.endsWith("r") || radarFileName.contains("RHI") || radarFileName.contains("rhi"))
    {
        scanType = "RHI";
    }
    else
    {
        cout << "this radar file is not vol/ppi/rhi." << std::endl;
    }

    /***********************************************************************************/
    // QC config
    vector<QCParams> params_qc;
    if (!DoLoadConfigure_QC(params_qc))
    {
        cout << "load QC.ini failed, exit!" << std::endl;
        return -1;
    }
    for (int i = 0; i < params_qc.size(); i++)
    {
        if (strcmp(params_qc.at(i).FuncName, "QCFLAG") == 0)
        {
            params_qc.at(i).Type.resize(2);
            params_qc.at(i).Type.at(0) = 0;         // UNQC
            params_qc.at(i).Type.at(1) = 1;         // QC
        }
    }
    cout << "load QC.ini configures done!!" << std::endl;
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
    status = m_pFileIO->LoadDataFromFile((void *)sourceFileName.c_str(), 0);
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
    // load library libQC.so;
    CNrietAlogrithm *m_pCAlgoQC = nullptr;
    void *m_pAlgoHandle = nullptr;
#ifdef ALGORITHM_DEBUG_QC
    m_pCAlgoQC = new CAlgoQC();
#else
//    void *m_pAlgoHandle = nullptr;
    m_pAlgoHandle = dlopen("../lib/libQC.so", RTLD_LAZY);
    if (m_pAlgoHandle)
    {
        CNrietAlogrithm * (*pGetQCInstance)(void);
        pGetQCInstance = (CNrietAlogrithm * (*)(void))dlsym(m_pAlgoHandle, "GetAlgoInstance");
        if (pGetQCInstance)
        {
            m_pCAlgoQC = (*pGetQCInstance)();
        }
        else
        {
            cout << "load GetAlgoInstance API of QC fail!" << std::endl;
            return -1;
        }
    }
    else
    {
        cout << "load library libQC.so fail!" << std::endl;
        return -1;
    }
#endif
    cout << "create QC algorithm instance done!" << std::endl;

    //QC
    m_pCAlgoQC->Init();
    m_pCAlgoQC->LoadParameters((void *)&params_qc);
    // 设置掩码为1
    m_pCAlgoQC->LoadStdData(data);
    m_pCAlgoQC->MakeProduct();
    vector<WRADRAWDATA> *data_qc = (vector<WRADRAWDATA> *)m_pCAlgoQC->GetProduct();

    // save QC File start

    for (unsigned long i_pro = 0; i_pro < data_qc->size(); i_pro++)
    {
        if (data_qc->at(i_pro).radials.size() == 0)
        {
            data_qc->erase(data_qc->begin() + i_pro);
            i_pro--;
        }
    }

    /***********************************************************************************/
    // write QC files by FileIO;
    vector<string> m_FileName;
    m_FileName.reserve(data_qc->size());
    m_pFileIO->getSITECODE(sourceSiteCode);
//    if (!radarFileName.contains("FMT"))
//    {
//        std::string SITECODE = splitPath(sourceFileName).at(splitPath(sourceFileName).size() - 3);
//        if (SITECODE.size() < 5)
//        {
//            SITECODE.insert(0, 5 - SITECODE.size(), '0');
//        }
//        m_pFileIO->getSITECODE(SITECODE);
//    }

    for (int i_out = 0; i_out < data_qc->size(); i_out++)
    {
        m_FileName.push_back(static_cast<char *>(m_pFileIO->GetFileName(&data_qc->at(i_out), 2)));
    }

    if (data_qc->size() != m_FileName.size())
    {
        m_pCAlgoQC->FreeData();
        cout << "product file name mismatch with product, drop all!" << std::endl;
        return -1;
    }
    else
    {
        cout << "Starting product path output." << std::endl;
        for (int ipro = 0; ipro < data_qc->size(); ipro++)
        {
            QDir dir = QDir(productPath.c_str()).absolutePath();
            string fullPath = QDir(productPath.c_str()).absolutePath().toStdString() + "/" + \
                              m_FileName.at(ipro) + "." + scanType + ".Z";
            string tmpDir = getDirectoryPath(fullPath);
            DIR *m_pDir = opendir(tmpDir.c_str());
            if (m_pDir == nullptr)
            {
//                cout << "Product path does not exit, creating " + tmpDir << std::endl;
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
            if (ipro != (data_qc->size() - 1))
            {
                cout << ",";
            }
            else
            {
                cout << std::endl;
            }

            char FileDir[1024] = {0};
            strncpy(FileDir, fullPath.c_str(), fullPath.length());
            m_pFileIO->LoadDataAndSaveFile(&data_qc->at(ipro), FileDir, 2);
        }
        cout << "Ending product path output." << std::endl;
    }

    // save QC file end
    m_pCAlgoQC->FreeData();
    m_pFileIO->FreeData();
    /***********************************************************************************/

    // 程序逻辑执行完毕
    qDebug() << "Algo_QC: Program execution complete" << endl;

    // 计算程序执行时间
    qDebug() << "Time Cost:";
    qDebug() << time_start_in.elapsed();
    qDebug() << "  ms";
    return 0;
}
