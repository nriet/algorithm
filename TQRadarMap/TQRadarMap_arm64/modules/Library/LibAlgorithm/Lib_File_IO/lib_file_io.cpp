#include "lib_file_io.h"
#include "cstring"
#include "dirent.h"
#include "sys/stat.h"

CNrietFile *GetFileInstance()
{
    return (new CNrietFileIO());
}

CNrietFileIO::CNrietFileIO()
{
    // 将m_aFileName数组中的所有元素初始化为0
    memset(&m_aFileName[0], 0x00, sizeof(m_aFileName) / sizeof(m_aFileName[0]));
}

CNrietFileIO::~CNrietFileIO()
{
    if (!m_RadarDataHead_SBand)
    {
        delete m_RadarDataHead_SBand;
        m_RadarDataHead_SBand = nullptr;
    }
    delete m_RadarDataHead;
    delete [] m_pLineData;
    //delete m_RadarHead;
    delete m_RadarData;
    m_RadarDataHead = nullptr;      // 雷达数据头
    m_pLineData = nullptr;      // 径向数据指针

    //m_RadarHead = nullptr;     //  标准格式雷达数据头
    m_RadarData = nullptr;
}

int CNrietFileIO::SetDebugLevel(int temp)
{
    m_DebugLevel = temp;
    return 0;
}

int CNrietFileIO::LoadDataFromFile(void *in_str, int standard = 0)
{
    char *fileName = (char *)in_str;
    m_radarFileName = QString::fromStdString(fileName).split("/").last();

    int status = -1;

    if (standard == 2)
    {
        if (LoadQCData(fileName))
        {
            m_fileTime = m_radarFileName.mid(12, 14).toStdString();
            status = 0;
            cout << "Load data_QC successfully." << endl;
        }
    }
    else
    {
        if (IsFakeFile(fileName))
        {
            if (LoadBZ2StandardVTB(fileName))
            {
                status = ConvertFMTtoFakePhasedArray();
                cout << "Load FMT VTB successfully." << endl;
            }
        }
        else
        {
            if (LoadJDRadar(fileName))
            {
                status = ConvertInternalVTBtoStandardFormat1_0();
                cout << "Load JD Radar successfully." << endl;
            }
            else if (LoadInternalVTB_SBand_PhasedArray(fileName))
            {
                status = ConvertInternalVTBtoStandardFormat_SBand_PhasedArray();
                cout << "Load Internal SBand PhasedArray VTB successfully." << endl;
            }
            else if (LoadInternalVTB(fileName))
            {
                status = ConvertInternalVTBtoStandardFormat1_0();
                cout << "Load Internal VTB successfully." << endl;
            }
            else if (LoadPhasedArrayInternalVTB(fileName))
            {
                status = ConvertInternalVTBtoStandardFormat1_0();
                cout << "Load Internal VTB successfully." << endl;
            }
            else if (LoadMHVTB(fileName))
            {
                status = ConvertInternalVTBtoStandardFormat1_0();
                cout << "Load MinHang VTB successfully." << endl;
            }
            else if (LoadBZ2StandardVTB(fileName))
            {
                status = 0;
                cout << "Load Standard VTB successfully." << endl;
            }
            else if (LoadStandardVTB(fileName))
            {
                status = 0;
                cout << "Load Standard VTB successfully." << endl;
            }
            else if (LoadStandardPARVTB(fileName))
            {
                status = 0;
                cout << "Load PAR VTB successfully. " << endl;
            }
        }
    }

    if (status)
    {
        FreeData();
        cout << "Not supported radar format" << endl;
        return  status;
    }

    FreeBlock();

    return status;
}

int CNrietFileIO::GetDrawData(void *data, void *outdata, void *mapinfo, void *gridinfo, void *invalid)
{
    bool iFlag = false;

    if (!iFlag && IsRadarRawData(data))
    {
        cout << "Not supported format" << endl;
        return -1;
    }
    else if (!iFlag && IsRadarProData(data))
    {
        iFlag = GetRadarProDrawData(data, outdata, mapinfo, gridinfo, invalid);
    }
    else if (!iFlag && IsRadarLatlonData(data))
    {
        cout << "Not supported format" << endl;
        return -1;
    }
    else
    {
        cout << "Not supported format" << endl;
    }

    return iFlag;
}

int CNrietFileIO::LoadDataAndSaveFile(void *data, void *in_str, int standard = 0)
{
    char *FileName = (char *)in_str;
    bool iFlag = false;

    if (standard == 2)
    {
        // QC
        iFlag = SaveZlibRadarQCData(data, FileName);
//        cout << "Save QC file success." << endl;
    }
    else
    {
        if (IsZlibFile(FileName))
        {
            if (!iFlag && IsRadarRawData(data))
            {
                iFlag = SaveZlibRadarRawData(data, FileName);
            }
            else if (!iFlag && IsRadarProData(data))
            {
                iFlag = SaveZlibRadarProData(data, FileName);
            }
            else if (!iFlag && IsRadarLatlonData(data))
            {
                iFlag = SaveZlibRadarLatlonData(data, FileName);
            }
            else if (!iFlag && IsRadarKJCRawData(data))
            {
                iFlag = SaveZlibRadarKJCRawData(data, FileName);
            }
            else if (!iFlag && IsRadarKJCProData(data))
            {
                iFlag = SaveZlibRadarKJCProData(data, FileName);
            }
            else
            {
                cout << "Not supported format" << endl;
            }
        }
        else if (IsBZ2File(FileName))
        {
            if (!iFlag && IsRadarRawData(data))
            {
                iFlag = SaveBZ2RadarRawData(data, FileName);
            }
            if (!iFlag && IsRadarKJCRawData(data))
            {
                iFlag = SaveBZ2RadarKJCRawData(data, FileName);
            }
        }
        else
        {
            if (!iFlag && IsRadarRawData(data))
            {
                iFlag = SaveRadarRawData(data, FileName);
            }
            else if (!iFlag && IsRadarProData(data))
            {
                iFlag = SaveRadarProData(data, FileName);
            }
            else if (!iFlag && IsRadarLatlonData(data))
            {
                iFlag = SaveRadarLatlonData(data, FileName);
            }
            else if (!iFlag && IsRadarKJCProData(data))
            {
                iFlag = SaveRadarKJCProData(data, FileName);
            }
            else
            {
                cout << "Not supported format" << endl;
            }
        }
    }
    return iFlag;
}

bool CNrietFileIO::LoadInternalVTB(char *fileName)
{
    gzFile l_File;
    int gz_status = 0;
    l_File = gzopen(fileName, "rb");
    if (l_File == nullptr)
    {
        cout << "Source file open error." << endl;
        return false;
    }

    m_RadarDataHead = new RadarDataHead();

    gz_status = gzread(l_File, m_RadarDataHead, sizeof(RadarDataHead));
    if (gz_status != sizeof(RadarDataHead))
    {
        if (m_RadarDataHead)
        {
            delete m_RadarDataHead;
            m_RadarDataHead = nullptr;
        }
        gzclose(l_File);
        return false;
    }
    if ((m_RadarDataHead->FileID[0] != 'R') || (m_RadarDataHead->FileID[1] != 'D'))
    {
        if (m_RadarDataHead)
        {
            delete m_RadarDataHead;
            m_RadarDataHead = nullptr;
        }
        gzclose(l_File);
        return false;
    }

    Get_nNumSum();

    m_pLineData = new NewLineDataBlock[m_nRadialNumSum];

    int i_Radial = 0;
    char tempparam;
    for (int i = 0; i < m_nLayerNum; i++)
    {
        tempparam = m_RadarDataHead->ObservationInfo.LayerInfo[i].DataForm;

        for (int j = 0; j < m_RadarDataHead->ObservationInfo.LayerInfo[i].RecordNumber; j++)
        {
            gz_status = gzread(l_File, &m_pLineData[i_Radial].LineDataInfo, sizeof(LINEDATAINFO));
            if (gz_status != sizeof(LINEDATAINFO))
            {
                delete m_RadarDataHead;
                m_RadarDataHead = nullptr;
                delete[] m_pLineData;
                m_pLineData = nullptr;
                gzclose(l_File);
                return false;
            }

            if (tempparam == 11 || tempparam == 21 || tempparam == 22 || tempparam == 24 || tempparam == 26 || tempparam == 60 || tempparam == 61 || tempparam == 62 || tempparam == 65 || tempparam == 91) //!-------填补ConZ值
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].CorZ, INTERNALMAXBINDOTS * sizeof(short));
                    if (gz_status != INTERNALMAXBINDOTS * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 12 || tempparam == 21 || tempparam == 23 || tempparam == 24 || tempparam == 26 || tempparam == 60 || tempparam == 65) //!-------填补UnZ值
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].UnZ, INTERNALMAXBINDOTS * sizeof(short));
                    if (gz_status != INTERNALMAXBINDOTS * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 13 || tempparam == 22 || tempparam == 23 || tempparam == 24 || tempparam == 26 || tempparam == 25 || tempparam == 60 || tempparam == 61 || tempparam == 62 || tempparam == 65 || tempparam == 91) //!-----填补V值
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].VbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].V, INTERNALMAXBINDOTS * sizeof(short));
                    if (gz_status != INTERNALMAXBINDOTS * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 14 || tempparam == 22 || tempparam == 23 || tempparam == 24 || tempparam == 26 || tempparam == 25 || tempparam == 60 || tempparam == 61 || tempparam == 62 || tempparam == 65 || tempparam == 91) //!-----填补W值
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].WbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].W, INTERNALMAXBINDOTS * sizeof(short));
                    if (gz_status != INTERNALMAXBINDOTS * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 60 || tempparam == 61 || tempparam == 62 || tempparam == 65 || tempparam == 91)  //ZDR
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].ZDR, INTERNALMAXBINDOTS * sizeof(short));
                    if (gz_status != INTERNALMAXBINDOTS * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 61 || tempparam == 62 || tempparam == 65) //PHDP
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].PHDP, INTERNALMAXBINDOTS * sizeof(short));
                    if (gz_status != INTERNALMAXBINDOTS * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 61 || tempparam == 62 || tempparam == 65) //KDP
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].KDP, INTERNALMAXBINDOTS * sizeof(short));
                    if (gz_status != INTERNALMAXBINDOTS * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 61 || tempparam == 62 || tempparam == 65 || tempparam == 91) //ROHV
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].ROHV, INTERNALMAXBINDOTS * sizeof(short));
                    if (gz_status != INTERNALMAXBINDOTS * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 91) //仅对91——SNRH
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].SNRH, INTERNALMAXBINDOTS * sizeof(short));
                    if (gz_status != INTERNALMAXBINDOTS * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 91) //仅对91——PHDP
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].PHDP, INTERNALMAXBINDOTS * sizeof(short));
                    if (gz_status != INTERNALMAXBINDOTS * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 61 || tempparam == 65 || tempparam == 91) //LDRH
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].LDR, INTERNALMAXBINDOTS * sizeof(short));
                    if (gz_status != INTERNALMAXBINDOTS * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 91) //仅对91——UnZ
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].UnZ, INTERNALMAXBINDOTS * sizeof(short));
                    if (gz_status != INTERNALMAXBINDOTS * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            i_Radial++;
        }
    }

    gzclose(l_File);
    m_RadarDataHead->OtherInfo.RadarType = 101;

    return true;
}

bool CNrietFileIO::LoadJDRadar(char *fileName)
{
    // get Radar name
    std::string filePath(fileName);
    size_t lastSlashPos = filePath.rfind('/');
    string radarname = filePath.substr(lastSlashPos + 1);
    QString RadarName = QString::fromStdString(radarname);
    if (RadarName.startsWith("PTB", Qt::CaseInsensitive) || RadarName.startsWith("ptb", Qt::CaseInsensitive) || RadarName.startsWith("vtb", Qt::CaseInsensitive) || RadarName.startsWith("VTB", Qt::CaseInsensitive) || RadarName.startsWith("RTB", Qt::CaseInsensitive) || RadarName.startsWith("rtb", Qt::CaseInsensitive) || RadarName.startsWith("VOL", Qt::CaseInsensitive) || RadarName.startsWith("vol", Qt::CaseInsensitive))
    {
        // 720A
        m_fileTime = m_radarFileName.mid(3, 14).toStdString();
        // Load Radar Data
        if (LoadJD720ARadar(fileName))
        {
            cout << "Load 720A Radar success." << endl;
            return true;
        }
    }
    else if (RadarName.startsWith("KL", Qt::CaseInsensitive) || RadarName.startsWith("HL", Qt::CaseInsensitive) || RadarName.startsWith("kl", Qt::CaseInsensitive)  || RadarName.startsWith("hl", Qt::CaseInsensitive) || RadarName.endsWith("P", Qt::CaseInsensitive) || RadarName.endsWith("V", Qt::CaseInsensitive) || RadarName.endsWith("p", Qt::CaseInsensitive) || RadarName.endsWith("v", Qt::CaseInsensitive) || RadarName.endsWith("r", Qt::CaseInsensitive) || RadarName.endsWith("r", Qt::CaseInsensitive))
    {
        // 784
        // select
        if (0 == if784Dual(RadarName))
        {
            cout << "parse 784Dual file." << endl;
            m_fileTime = m_radarFileName.mid(0, 13).toStdString();
            // 找到最后一个数字的位置，假设我们要在数字序列的末尾添加 '0'
            size_t lastNumPos = m_fileTime.find_last_of("0123456789");
            // 插入 '0' 字符
            m_fileTime.insert(lastNumPos + 1, "0");

            if (LoadJD784DualRadar(fileName))
            {
                cout << "Load 784Dual Radar success." << endl;
                return true;
            }
        }
        else if (0 == if784DP(RadarName))
        {
            if (RadarName.contains("720A"))
            {
                cout << "parse 720ADP file." << endl;
                m_fileTime = m_radarFileName.mid(10, 14).toStdString();
                if (LoadJD720ADPRadar(fileName))
                {
                    cout << "Load 720ADP Radar success." << endl;
                    return true;
                }
            }
            else
            {
                cout << "parse 784DP file." << endl;
                m_fileTime = m_radarFileName.mid(10, 14).toStdString();
                if (LoadJD784DPRadar(fileName))
                {
                    cout << "Load 784DP Radar success." << endl;
                    return true;
                }
            }
        }
        else if (0 == if784NewDual(RadarName) || RadarName.startsWith("HLGK002LLX", Qt::CaseInsensitive) || RadarName.contains('('))
        {
            m_fileTime = m_radarFileName.mid(10, 14).toStdString();
            if (RadarName.startsWith("HLGK002LLX", Qt::CaseInsensitive))
            {
                m_fileTime = m_radarFileName.mid(11, 14).toStdString();
            }
            cout << "parse 784newdual file." << endl;
            if (LoadJD784NewDualRadar(fileName))
            {
                cout << "Load 784NewDual Radar success." << endl;
                return true;
            }
        }
        else
        {
            cout << "parse not 784 file." << endl;
            return false;
        }
    }
    return false;
}

int CNrietFileIO::if784NewDual(QString RadarName)
{
    if ((!RadarName.startsWith("HL")) && (!RadarName.startsWith("hl")))
    {
        return -1;
    }
    if (RadarName.endsWith(".Z") || RadarName.endsWith(".z") || RadarName.endsWith(".BZ2") || RadarName.endsWith(".bz2"))
    {
        QStringList filenames = RadarName.split(".");
        if (3 != filenames.size())
        {
            qDebug() << "not 784DP file,CParse784::if784NewDual fileName error.";
            return -1;
        }
        QString str1 = filenames.at(0);
        if (27 != str1.length())
        {
            qDebug() << "not 784DP file,CParse784::if784NewDual str1 length error.";
            return -1;
        }
        QString str2 = filenames.at(1);
        if (3 != str2.length())
        {
            qDebug() << "not 784DP file,CParse784::if784NewDual str2 length error.";
            return -1;
        }
//		if (0 != str2.compare("PPI") && 0 != str2.compare("RHI") && 0 != str2.compare("VOL") && 0 != str2.compare("FPI"))
        if (0 != str2.compare("PPI") && 0 != str2.compare("RHI") && 0 != str2.compare("VOL") && 0 != str2.compare("ppi") && 0 != str2.compare("rhi") && 0 != str2.compare("vol"))
        {
            qDebug() << "not 784DP file,CParse784::if784DP laststr error.";
            return -1;
        }
    }
    else
    {
        QStringList filenames = RadarName.split(".");
        if (2 != filenames.size())
        {
            qDebug() << "not 784DP file,CParse784::if784NewDual fileName error.";
            return -1;
        }
        QString str1 = filenames.at(0);
        if (27 != str1.length())
        {
            qDebug() << "not 784DP file,CParse784::if784NewDual str1 length error.";
            return -1;
        }
        QString str2 = filenames.at(1);
        if (3 != str2.length())
        {
            qDebug() << "not 784DP file,CParse784::if784NewDual str2 length error.";
            return -1;
        }
//    if (0 != str2.compare("PPI") && 0 != str2.compare("RHI") && 0 != str2.compare("VOL") && 0 != str2.compare("FPI"))
        if (0 != str2.compare("PPI") && 0 != str2.compare("RHI") && 0 != str2.compare("VOL") && 0 != str2.compare("ppi") && 0 != str2.compare("rhi") && 0 != str2.compare("vol"))
        {
            qDebug() << "not 784NewDual file,CParse784::if784NewDual laststr error.";
            return -1;
        }
    }
    return 0;
}

int CNrietFileIO::if784Dual(QString RadarName)
{
    QStringList filenames = RadarName.split(".");
    if (2 != filenames.size())
    {
        qDebug() << "not 784Dual file,CParse784::if784Dual fileName error.";
        return -1;
    }
    QString str1 = filenames.at(0);
//    if (15 != str1.length() && 13 != str1.length())
    if (13 != str1.length())
    {
        qDebug() << "not 784Dual file,CParse784::if784Dual str1 length error.";
        return -1;
    }
    QString str2 = filenames.at(1);
    if (3 != str2.length())
    {
        qDebug() << "not 784Dual file,CParse784::if784Dual str2 length error.";
        return -1;
    }
    QString laststr = str2.mid(2, 1);
    if (0 != laststr.compare("P", Qt::CaseInsensitive) && 0 != laststr.compare("R", Qt::CaseInsensitive) && 0 != laststr.compare("V", Qt::CaseInsensitive) && 0 != laststr.compare("p", Qt::CaseInsensitive) && 0 != laststr.compare("r", Qt::CaseInsensitive) && 0 != laststr.compare("v", Qt::CaseInsensitive))
    {
        qDebug() << "not 784Dual file,CParse784::if784Dual laststr error.";
        return -1;
    }
    return 0;
}

int CNrietFileIO::if784DP(QString RadarName)
{
    if (RadarName.startsWith("HL") || RadarName.startsWith("hl"))
    {
        return -1;
    }
    if (RadarName.endsWith(".Z"))
    {
        QStringList filenames = RadarName.split(".");
        if (3 != filenames.size())
        {
            qDebug() << "not 784DP file,CParse784::if784DP fileName error.";
            return -1;
        }
        QString str1 = filenames.at(0);
        if (27 != str1.length())
        {
            qDebug() << "not 784DP file,CParse784::if784DP str1 length error.";
            return -1;
        }
        QString str2 = filenames.at(1);
        if (3 != str2.length())
        {
            qDebug() << "not 784DP file,CParse784::if784DP str2 length error.";
            return -1;
        }
//		if (0 != str2.compare("PPI") && 0 != str2.compare("RHI") && 0 != str2.compare("VOL") && 0 != str2.compare("FPI"))
        if (0 != str2.compare("PPI") && 0 != str2.compare("RHI") && 0 != str2.compare("VOL") && 0 != str2.compare("ppi") && 0 != str2.compare("rhi") && 0 != str2.compare("vol"))
        {
            qDebug() << "not 784DP file,CParse784::if784DP laststr error.";
            return -1;
        }
    }
    else
    {
        QStringList filenames = RadarName.split(".");
        if (2 != filenames.size())
        {
            qDebug() << "not 784DP file,CParse784::if784DP fileName error.";
            return -1;
        }
        QString str1 = filenames.at(0);
        if (27 != str1.length())
        {
            qDebug() << "not 784DP file,CParse784::if784DP str1 length error.";
            return -1;
        }
        QString str2 = filenames.at(1);
        if (3 != str2.length())
        {
            qDebug() << "not 784DP file,CParse784::if784DP str2 length error.";
            return -1;
        }
//        if (0 != str2.compare("PPI") && 0 != str2.compare("RHI") && 0 != str2.compare("VOL") && 0 != str2.compare("FPI"))
        if (0 != str2.compare("PPI") && 0 != str2.compare("RHI") && 0 != str2.compare("VOL") && 0 != str2.compare("VTB") && 0 != str2.compare("ppi") && 0 != str2.compare("rhi") && 0 != str2.compare("vol") && 0 != str2.compare("vtb"))
        {
            qDebug() << "not 784DP file,CParse784::if784DP laststr error.";
            return -1;
        }
    }
    return 0;
}

bool CNrietFileIO::LoadJD720ADPRadar(char *fileName)
{
    // header
    // Load
    FILE *file = NULL;
    file = fopen(fileName, "rb");
    if (file == NULL)
    {
        qDebug() << "load720ADPFile open 720ADP radar file error.";
        return false;
    }

    m_radarHeaderNewDP = new NewRadarHeader_New_DP();
    fread(m_radarHeaderNewDP, sizeof(NewRadarHeader_New_DP), 1, file);
    // get m_nRadialNumSum and m_nLayerNum
    Get_nNumSum_720ADP();
    if (m_nLayerNum > 32)
    {
        qDebug() << "load720ADPFile m_LayerNumber > 32.";
        fclose(file);
        return false;
    }
    // convert
    convert720ADPHeaderToVTB();


    // radial
    m_pLineData = new NewLineDataBlock[m_nRadialNumSum];
    vector<_DataRecordNEWDP_> pLineData_temp;
    pLineData_temp.resize(m_nRadialNumSum);

    int i_Radial = 0;
    for (int i = 0; i < m_nLayerNum; i++)
    {
        for (int j = 0; j < m_RadarDataHead->ObservationInfo.LayerInfo[i].RecordNumber; j++)
        {
            // radial header
            fread(&pLineData_temp.at(i_Radial), sizeof(_DataRecordNEWDP_), 1, file);
            m_pLineData[i_Radial].LineDataInfo.Elev = pLineData_temp.at(i_Radial).startel;
            m_pLineData[i_Radial].LineDataInfo.Az = pLineData_temp.at(i_Radial).startaz;
            m_pLineData[i_Radial].LineDataInfo.Hh = 0;
            m_pLineData[i_Radial].LineDataInfo.Mm = 0;
            m_pLineData[i_Radial].LineDataInfo.Ss = 0;
            m_pLineData[i_Radial].LineDataInfo.Min = 0;

            // data
            short data_temp_i_ConZ;
            short data_temp_i_UnZ;
            short data_temp_i_V;
            short data_temp_i_W;
            for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
            {
                if (ibin < DATANUMBER_NEWDP)
                {
                    // 填补ConZ值
                    if (*(unsigned char *)&pLineData_temp[i_Radial].range[ibin][0] == 0)
                    {
                        data_temp_i_ConZ = PREFILLVALUE_VTB;
                    }
                    else
                    {
                        data_temp_i_ConZ = 1.0 * ((*(unsigned char *)&pLineData_temp[i_Radial].range[ibin][0] - 64.0) / 2) * 100 + 0;
                    }
                    // 填补UnZ值
                    if (*(unsigned char *)&pLineData_temp[i_Radial].range[ibin][1] == 0)
                    {
                        data_temp_i_UnZ = PREFILLVALUE_VTB;
                    }
                    else
                    {
                        data_temp_i_UnZ = 1.0 * ((*(unsigned char *)&pLineData_temp[i_Radial].range[ibin][1] - 64.0) / 2) * 100 + 0;
                    }
                    // 填补V值
                    if (*(char *)&pLineData_temp[i_Radial].range[ibin][2] == 0)
                    {
                        data_temp_i_V = PREFILLVALUE_VTB;
                    }
                    else
                    {
                        data_temp_i_V = 1.0 * (*(char *)&pLineData_temp[i_Radial].range[ibin][2] - 128.0) * m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxV / 127;
                    }
                    // 填补W值
                    if (*(unsigned char *)&pLineData_temp[i_Radial].range[ibin][3] == 0)
                    {
                        data_temp_i_W = PREFILLVALUE_VTB;
                    }
                    else
                    {
                        data_temp_i_W = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].range[ibin][3]) * m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxV / 256;
                    }
                }
                else
                {
                    data_temp_i_ConZ = PREFILLVALUE_VTB;
                    data_temp_i_UnZ = PREFILLVALUE_VTB;
                    data_temp_i_V = PREFILLVALUE_VTB;
                    data_temp_i_W = PREFILLVALUE_VTB;
                }
                m_pLineData[i_Radial].CorZ[ibin] = data_temp_i_ConZ;
                m_pLineData[i_Radial].UnZ[ibin] = data_temp_i_UnZ;
                m_pLineData[i_Radial].V[ibin] = data_temp_i_V;
                m_pLineData[i_Radial].W[ibin] = data_temp_i_W;
            }
            i_Radial++;
        }
    }

    fclose(file);
    m_RadarDataHead->OtherInfo.RadarType = 720;
    return true;
}

bool CNrietFileIO::LoadJD784DPRadar(char *fileName)
{
    // header
    // Load
    FILE *file = NULL;
    file = fopen(fileName, "rb");
    if (file == NULL)
    {
        qDebug() << "loadSiChuangFile open sichuang radar file error.";
        return false;
    }

    m_NewRadarHeader_NEWDUAL = new NewRadarHeader_NEWDUAL();
    fread(m_NewRadarHeader_NEWDUAL, sizeof(NewRadarHeader_NEWDUAL), 1, file);
    // get m_nRadialNumSum and m_nLayerNum
    Get_nNumSum_784_NewDual();
    if (m_nLayerNum > 32)
    {
        qDebug() << "load784File m_LayerNumber > 32.";
        fclose(file);
        return false;
    }
    // convert
    convert784DPHeaderToVTB();


    // radial
    m_pLineData = new NewLineDataBlock[m_nRadialNumSum];
    vector<DataRecord_DP> pLineData_temp;
    pLineData_temp.resize(m_nRadialNumSum);

    int i_Radial = 0;
    for (int i = 0; i < m_nLayerNum; i++)
    {
        for (int j = 0; j < m_RadarDataHead->ObservationInfo.LayerInfo[i].RecordNumber; j++)
        {
            // radial header
            fread(&pLineData_temp.at(i_Radial), sizeof(DataRecord_DP), 1, file);
            m_pLineData[i_Radial].LineDataInfo.Elev = pLineData_temp.at(i_Radial).startel;
            m_pLineData[i_Radial].LineDataInfo.Az = pLineData_temp.at(i_Radial).startaz;
            m_pLineData[i_Radial].LineDataInfo.Hh = 0;
            m_pLineData[i_Radial].LineDataInfo.Mm = 0;
            m_pLineData[i_Radial].LineDataInfo.Ss = 0;
            m_pLineData[i_Radial].LineDataInfo.Min = 0;

            // data
            short data_temp_i_ConZ;
            short data_temp_i_UnZ;
            short data_temp_i_V;
            short data_temp_i_W;
            for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
            {
                if (ibin < RAWRADARDATALENGTH)
                {
                    // 填补ConZ值
                    if (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_dbz == 0)
                    {
                        data_temp_i_ConZ = PREFILLVALUE_VTB;
                    }
                    else
                    {
                        data_temp_i_ConZ = 1.0 * ((*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_dbz - 64.0) / 2) * 100 + 0;
                    }
                    // 填补UnZ值
                    if (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_undbz == 0)
                    {
                        data_temp_i_UnZ = PREFILLVALUE_VTB;
                    }
                    else
                    {
                        data_temp_i_UnZ = 1.0 * ((*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_undbz - 64.0) / 2) * 100 + 0;
                    }
                    // 填补V值
                    if (*(char *)&pLineData_temp[i_Radial].rawdata[ibin].m_vel == 0)
                    {
                        data_temp_i_V = PREFILLVALUE_VTB;
                    }
                    else
                    {
                        data_temp_i_V = 1.0 * (*(char *)&pLineData_temp[i_Radial].rawdata[ibin].m_vel - 128.0) * m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxV / 127;
                    }
                    // 填补W值
                    if (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_sw == 0)
                    {
                        data_temp_i_W = PREFILLVALUE_VTB;
                    }
                    else
                    {
                        data_temp_i_W = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_sw) * m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxV / 256;
                    }
                }
                else
                {
                    data_temp_i_ConZ = PREFILLVALUE_VTB;
                    data_temp_i_UnZ = PREFILLVALUE_VTB;
                    data_temp_i_V = PREFILLVALUE_VTB;
                    data_temp_i_W = PREFILLVALUE_VTB;
                }
                m_pLineData[i_Radial].CorZ[ibin] = data_temp_i_ConZ;
                m_pLineData[i_Radial].UnZ[ibin] = data_temp_i_UnZ;
                m_pLineData[i_Radial].V[ibin] = data_temp_i_V;
                m_pLineData[i_Radial].W[ibin] = data_temp_i_W;
            }
            i_Radial++;
        }
    }

    fclose(file);
    m_RadarDataHead->OtherInfo.RadarType = 717;
    return true;
}

bool CNrietFileIO::LoadJD784NewDualRadar(char *fileName)
{
    // get Radar name
    std::string filePath(fileName);
    size_t lastSlashPos = filePath.rfind('/');
    string radarname = filePath.substr(lastSlashPos + 1);
    QString RadarName = QString::fromStdString(radarname);
    if (RadarName.endsWith(".Z") || RadarName.endsWith(".z"))
    {
        // header
        // Load
        gzFile l_File;
        int gz_status = 0;
        l_File = gzopen(fileName, "rb");
        if (l_File == nullptr)
        {
            cout << "CParseNewDual784::load784File open 784 radar file error." << endl;
            return false;
        }

        m_NewRadarHeader_NEWDUAL = new NewRadarHeader_NEWDUAL();
        gz_status = gzread(l_File, m_NewRadarHeader_NEWDUAL, sizeof(NewRadarHeader_NEWDUAL));
        // get m_nRadialNumSum and m_nLayerNum
        Get_nNumSum_784_NewDual();
        if (m_nLayerNum > 32)
        {
            qDebug() << "load784File m_LayerNumber > 32.";
            gzclose(l_File);
            return false;
        }
        // convert
        convert784newdualHeaderToVTB();


        // radial
        m_pLineData = new NewLineDataBlock[m_nRadialNumSum];
        vector<DataRecord_Dual> pLineData_temp;
        pLineData_temp.resize(m_nRadialNumSum);
        int i_Radial = 0;

        for (int i = 0; i < m_nLayerNum; i++)
        {
            for (int j = 0; j < m_RadarDataHead->ObservationInfo.LayerInfo[i].RecordNumber; j++)
            {
                // radial header
                gz_status = gzread(l_File, &pLineData_temp.at(i_Radial), sizeof(DataRecord_Dual));
                m_pLineData[i_Radial].LineDataInfo.Elev = pLineData_temp.at(i_Radial).startel;
                m_pLineData[i_Radial].LineDataInfo.Az = pLineData_temp.at(i_Radial).startaz;
                m_pLineData[i_Radial].LineDataInfo.Hh = pLineData_temp.at(i_Radial).hour;
                m_pLineData[i_Radial].LineDataInfo.Mm = pLineData_temp.at(i_Radial).minute;
                m_pLineData[i_Radial].LineDataInfo.Ss = pLineData_temp.at(i_Radial).second;
                m_pLineData[i_Radial].LineDataInfo.Min = pLineData_temp.at(i_Radial).millisecond;

                // data
                short data_temp_i_ConZ;
                short data_temp_i_UnZ;
                short data_temp_i_V;
                short data_temp_i_W;
                for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
                {
                    if (ibin < 1000)
                    {
                        // 填补ConZ值
                        if (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_dbz == 0 || *(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_dbz == 65535)
                        {
                            data_temp_i_ConZ = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_ConZ = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_dbz - 32768) + 0;
                        }
                        // 填补UnZ值
                        if (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_undbz == 0 || *(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_undbz == 65535)
                        {
                            data_temp_i_UnZ = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_UnZ = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_undbz - 32768) + 0;
                        }
                        // 填补V值
                        if (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_vel == 0 || *(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_vel == 65535)
                        {
                            data_temp_i_V = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_V = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_vel - 32768) * m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxV;
                        }
                        // 填补W值
                        if (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_sw == 0 || *(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_sw == 65535)
                        {
                            data_temp_i_W = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_W = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_sw);
                        }
                    }
                    else
                    {
                        data_temp_i_ConZ = PREFILLVALUE_VTB;
                        data_temp_i_UnZ = PREFILLVALUE_VTB;
                        data_temp_i_V = PREFILLVALUE_VTB;
                        data_temp_i_W = PREFILLVALUE_VTB;
                    }
                    m_pLineData[i_Radial].CorZ[ibin] = data_temp_i_ConZ;
                    m_pLineData[i_Radial].UnZ[ibin] = data_temp_i_UnZ;
                    m_pLineData[i_Radial].V[ibin] = data_temp_i_V;
                    m_pLineData[i_Radial].W[ibin] = data_temp_i_W;
                }
                i_Radial++;
            }
        }
        gzclose(l_File);
        m_RadarDataHead->OtherInfo.RadarType = 784;
        return true;
    }
    else if (RadarName.endsWith(".BZ2") || RadarName.endsWith(".bz2"))
    {
        // header
        // Load
        int bzstatus;
        FILE *fp = fopen(fileName, "rb");
        if (fp == nullptr)
        {
            cout << "CParseNewDual784::load784File open 784 radar file error." << endl;
            return false;
        }
        BZFILE *bzFp = BZ2_bzReadOpen(&bzstatus, fp, 4, 0, nullptr, 0);
        if (bzstatus < BZ_OK)
        {
            BZ2_bzReadClose(&bzstatus, bzFp);
            fclose(fp);
            cout << "CParseNewDual784::load784File open 784 radar file error." << endl;
            return false;
        }

        m_NewRadarHeader_NEWDUAL = new NewRadarHeader_NEWDUAL();

        // 打开/dev/null用于屏蔽输出
        int fd = open("/dev/null", O_WRONLY);
        if (fd == -1)
        {
            std::cerr << "Failed to open /dev/null" << std::endl;
            return -1;
        }

        // 保存当前的标准输出和标准错误
        int saved_stdout = dup(fileno(stdout));
        int saved_stderr = dup(fileno(stderr));

        // 将标准输出和标准错误重定向到/dev/null
        dup2(fd, fileno(stdout));
        dup2(fd, fileno(stderr));
        BZ2_bzRead(&bzstatus, bzFp, m_NewRadarHeader_NEWDUAL, sizeof(NewRadarHeader_NEWDUAL));
        // 关闭/dev/null并恢复原来的标准输出和标准错误
        dup2(saved_stdout, fileno(stdout));
        dup2(saved_stderr, fileno(stderr));

        // get m_nRadialNumSum and m_nLayerNum
        Get_nNumSum_784_NewDual();
        if (m_nLayerNum > 32)
        {
            qDebug() << "load784File m_LayerNumber > 32.";
            BZ2_bzReadClose(&bzstatus, bzFp);
            fclose(fp);
            return false;
        }
        // convert
        convert784newdualHeaderToVTB();


        // radial
        m_pLineData = new NewLineDataBlock[m_nRadialNumSum];
        vector<DataRecord_Dual> pLineData_temp;
        pLineData_temp.resize(m_nRadialNumSum);
        int i_Radial = 0;

        for (int i = 0; i < m_nLayerNum; i++)
        {
            for (int j = 0; j < m_RadarDataHead->ObservationInfo.LayerInfo[i].RecordNumber; j++)
            {
                dup2(fd, fileno(stdout));
                dup2(fd, fileno(stderr));
                BZ2_bzRead(&bzstatus, bzFp, &pLineData_temp.at(i_Radial), sizeof(DataRecord_Dual));
                dup2(saved_stdout, fileno(stdout));
                dup2(saved_stderr, fileno(stderr));
//                gz_status = gzread(l_File, &pLineData_temp.at(i_Radial), sizeof(DataRecord_Dual));
                m_pLineData[i_Radial].LineDataInfo.Elev = pLineData_temp.at(i_Radial).startel;
                m_pLineData[i_Radial].LineDataInfo.Az = pLineData_temp.at(i_Radial).startaz;
                m_pLineData[i_Radial].LineDataInfo.Hh = pLineData_temp.at(i_Radial).hour;
                m_pLineData[i_Radial].LineDataInfo.Mm = pLineData_temp.at(i_Radial).minute;
                m_pLineData[i_Radial].LineDataInfo.Ss = pLineData_temp.at(i_Radial).second;
                m_pLineData[i_Radial].LineDataInfo.Min = pLineData_temp.at(i_Radial).millisecond;

                // data
                short data_temp_i_ConZ;
                short data_temp_i_UnZ;
                short data_temp_i_V;
                short data_temp_i_W;
                for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
                {
                    if (ibin < 1000)
                    {
                        // 填补ConZ值
                        if (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_dbz == 0 || *(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_dbz == 65535)
                        {
                            data_temp_i_ConZ = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_ConZ = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_dbz - 32768) + 0;
                        }
                        // 填补UnZ值
                        if (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_undbz == 0 || *(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_undbz == 65535)
                        {
                            data_temp_i_UnZ = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_UnZ = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_undbz - 32768) + 0;
                        }
                        // 填补V值
                        if (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_vel == 0 || *(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_vel == 65535)
                        {
                            data_temp_i_V = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_V = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_vel - 32768) * m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxV;
                        }
                        // 填补W值
                        if (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_sw == 0 || *(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_sw == 65535)
                        {
                            data_temp_i_W = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_W = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_sw);
                        }
                    }
                    else
                    {
                        data_temp_i_ConZ = PREFILLVALUE_VTB;
                        data_temp_i_UnZ = PREFILLVALUE_VTB;
                        data_temp_i_V = PREFILLVALUE_VTB;
                        data_temp_i_W = PREFILLVALUE_VTB;
                    }
                    m_pLineData[i_Radial].CorZ[ibin] = data_temp_i_ConZ;
                    m_pLineData[i_Radial].UnZ[ibin] = data_temp_i_UnZ;
                    m_pLineData[i_Radial].V[ibin] = data_temp_i_V;
                    m_pLineData[i_Radial].W[ibin] = data_temp_i_W;
                }
                i_Radial++;
            }
        }
        BZ2_bzReadClose(&bzstatus, bzFp);
        fclose(fp);
        close(fd);
        m_RadarDataHead->OtherInfo.RadarType = 784;
        return true;
    }
    else
    {
        // header
        // Load
        FILE *file = NULL;
        file = fopen(fileName, "rb");
        if (file == NULL)
        {
            qDebug() << "CParseNewDual784::load784File open 784 radar file error.";
            //fclose(file);
            return false;
        }

        m_NewRadarHeader_NEWDUAL = new NewRadarHeader_NEWDUAL();
        fread(m_NewRadarHeader_NEWDUAL, sizeof(NewRadarHeader_NEWDUAL), 1, file);
        // get m_nRadialNumSum and m_nLayerNum
        Get_nNumSum_784_NewDual();
        if (m_nLayerNum > 32)
        {
            qDebug() << "load784File m_LayerNumber > 32.";
            fclose(file);
            return false;
        }
        // convert
        convert784newdualHeaderToVTB();


        // radial
        m_pLineData = new NewLineDataBlock[m_nRadialNumSum];
        vector<DataRecord_Dual> pLineData_temp;
        pLineData_temp.resize(m_nRadialNumSum);
        int i_Radial = 0;

        for (int i = 0; i < m_nLayerNum; i++)
        {
            for (int j = 0; j < m_RadarDataHead->ObservationInfo.LayerInfo[i].RecordNumber; j++)
            {
                // radial header
                fread(&pLineData_temp.at(i_Radial), sizeof(DataRecord_Dual), 1, file);
                m_pLineData[i_Radial].LineDataInfo.Elev = pLineData_temp.at(i_Radial).startel;
                m_pLineData[i_Radial].LineDataInfo.Az = pLineData_temp.at(i_Radial).startaz;
                m_pLineData[i_Radial].LineDataInfo.Hh = pLineData_temp.at(i_Radial).hour;
                m_pLineData[i_Radial].LineDataInfo.Mm = pLineData_temp.at(i_Radial).minute;
                m_pLineData[i_Radial].LineDataInfo.Ss = pLineData_temp.at(i_Radial).second;
                m_pLineData[i_Radial].LineDataInfo.Min = pLineData_temp.at(i_Radial).millisecond;

                // data
                short data_temp_i_ConZ;
                short data_temp_i_UnZ;
                short data_temp_i_V;
                short data_temp_i_W;
                for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
                {
                    if (ibin < 1000)
                    {
                        // 填补ConZ值
                        if (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_dbz == 0 || *(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_dbz == 65535)
                        {
                            data_temp_i_ConZ = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_ConZ = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_dbz - 32768) + 0;
                        }
                        // 填补UnZ值
                        if (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_undbz == 0 || *(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_undbz == 65535)
                        {
                            data_temp_i_UnZ = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_UnZ = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_undbz - 32768) + 0;
                        }
                        // 填补V值
                        if (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_vel == 0 || *(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_vel == 65535)
                        {
                            data_temp_i_V = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_V = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_vel - 32768) * m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxV;
                        }
                        // 填补W值
                        if (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_sw == 0 || *(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_sw == 65535)
                        {
                            data_temp_i_W = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_W = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[ibin].m_sw);
                        }
                    }
                    else
                    {
                        data_temp_i_ConZ = PREFILLVALUE_VTB;
                        data_temp_i_UnZ = PREFILLVALUE_VTB;
                        data_temp_i_V = PREFILLVALUE_VTB;
                        data_temp_i_W = PREFILLVALUE_VTB;
                    }
                    m_pLineData[i_Radial].CorZ[ibin] = data_temp_i_ConZ;
                    m_pLineData[i_Radial].UnZ[ibin] = data_temp_i_UnZ;
                    m_pLineData[i_Radial].V[ibin] = data_temp_i_V;
                    m_pLineData[i_Radial].W[ibin] = data_temp_i_W;
                }
                i_Radial++;
            }
        }

        fclose(file);
        m_RadarDataHead->OtherInfo.RadarType = 784;
        return true;
    }
}

bool CNrietFileIO::LoadJD784DualRadar(char *fileName)
{
    // header
    // Load
    FILE *file = NULL;
    file = fopen(fileName, "rb");
    if (file == NULL)
    {
        qDebug() << "CParseDual784::load784File open 784 radar file error.";
        //fclose(file);
        return false;
    }

    m_NewRadarHeader_DUAL = new NewRadarHeader_DUAL();
    fread(m_NewRadarHeader_DUAL, sizeof(NewRadarHeader_DUAL), 1, file);
    // get m_nRadialNumSum and m_nLayerNum
    Get_nNumSum_784_Dual();
    if (m_nLayerNum > 30)
    {
        qDebug() << "load784File m_LayerNumber > 30.";
        fclose(file);
        return false;
    }
    // convert
    convert784dualHeaderToVTB();

    // radial
    m_pLineData = new NewLineDataBlock[m_nRadialNumSum];
    int i_Radial = 0;
    //极化状况
    unsigned char polarizations = 0;
    polarizations = m_NewRadarHeader_DUAL->PerformanceInfo.polarizations;
    cout << "784_Dual::polarizations = " << polarizations << endl;

    if (0 == polarizations)//水平偏振
    {
        vector<RVP7Record> pLineData_temp;
        pLineData_temp.resize(m_nRadialNumSum);
        for (int i = 0; i < m_nLayerNum; i++)
        {
            for (int j = 0; j < m_NewRadarHeader_DUAL->ObservationInfo.LayerParam[i].recordnumber; j++)
            {
                // radial header
                fread(&pLineData_temp.at(i_Radial), sizeof(RVP7Record), 1, file);
                m_pLineData[i_Radial].LineDataInfo.Elev = pLineData_temp.at(i_Radial).startel * 360.0 / 65536.0 * 100;
                m_pLineData[i_Radial].LineDataInfo.Az = pLineData_temp.at(i_Radial).startaz * 360.0 / 65536.0 * 100;
                m_pLineData[i_Radial].LineDataInfo.Hh = 0;
                m_pLineData[i_Radial].LineDataInfo.Mm = 0;
                m_pLineData[i_Radial].LineDataInfo.Ss = 0;
                m_pLineData[i_Radial].LineDataInfo.Min = 0;

                // data
                short data_temp_i_ConZ;
                short data_temp_i_UnZ;
                short data_temp_i_V;
                short data_temp_i_W;
                for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
                {
                    if (ibin < RAWRECORDLENGTH1)
                    {
                        // 填补ConZ值
                        if (*(unsigned char *)&pLineData_temp[i_Radial].RawData[ibin].m_dbz == 0)
                        {
                            data_temp_i_ConZ = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_ConZ = 1.0 * ((*(unsigned char *)&pLineData_temp[i_Radial].RawData[ibin].m_dbz - 64.0) / 2) * 100 + 0;
                        }
                        // 填补UnZ值
                        if (*(unsigned char *)&pLineData_temp[i_Radial].RawData[ibin].m_undbz == 0)
                        {
                            data_temp_i_UnZ = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_UnZ = 1.0 * ((*(unsigned char *)&pLineData_temp[i_Radial].RawData[ibin].m_undbz - 64.0) / 2) * 100 + 0;
                        }
                        // 填补V值
                        if (*(char *)&pLineData_temp[i_Radial].RawData[ibin].m_vel == 0)
                        {
                            data_temp_i_V = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_V = 1.0 * (*(char *)&pLineData_temp[i_Radial].RawData[ibin].m_vel - 128) * m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxV / 127.5;
                        }
                        // 填补W值
                        if (*(unsigned char *)&pLineData_temp[i_Radial].RawData[ibin].m_sw == 0)
                        {
                            data_temp_i_W = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_W = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].RawData[ibin].m_sw) * m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxV / 256;
                        }
                    }
                    else
                    {
                        data_temp_i_ConZ = PREFILLVALUE_VTB;
                        data_temp_i_UnZ = PREFILLVALUE_VTB;
                        data_temp_i_V = PREFILLVALUE_VTB;
                        data_temp_i_W = PREFILLVALUE_VTB;
                    }
                    m_pLineData[i_Radial].CorZ[ibin] = data_temp_i_ConZ;
                    m_pLineData[i_Radial].UnZ[ibin] = data_temp_i_UnZ;
                    m_pLineData[i_Radial].V[ibin] = data_temp_i_V;
                    m_pLineData[i_Radial].W[ibin] = data_temp_i_W;
                }
                i_Radial++;
            }
        }
    }
    else if (2 == polarizations)//双偏振
    {
        vector<RVP7Data_DUAL> pLineData_temp;
        pLineData_temp.resize(m_nRadialNumSum);
        for (int i = 0; i < m_nLayerNum; i++)
        {
            for (int j = 0; j < m_NewRadarHeader_DUAL->ObservationInfo.LayerParam[i].recordnumber; j++)
            {
                // radial header
                fread(&pLineData_temp.at(i_Radial), sizeof(RVP7Data_DUAL), 1, file);
                m_pLineData[i_Radial].LineDataInfo.Elev = pLineData_temp.at(i_Radial).startel * 360.0 / 65536.0 * 100;
                m_pLineData[i_Radial].LineDataInfo.Az = pLineData_temp.at(i_Radial).startaz * 360.0 / 65536.0 * 100;
                m_pLineData[i_Radial].LineDataInfo.Hh = 0;
                m_pLineData[i_Radial].LineDataInfo.Mm = 0;
                m_pLineData[i_Radial].LineDataInfo.Ss = 0;
                m_pLineData[i_Radial].LineDataInfo.Min = 0;

                // data
                short data_temp_i_ConZ;
                short data_temp_i_UnZ;
                short data_temp_i_V;
                short data_temp_i_W;
                for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
                {
                    if (ibin < RAWRECORDLENGTH)
                    {
                        // 填补ConZ值
                        if (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[0][ibin] == 0 || 65535 == *(unsigned char *)&pLineData_temp[i_Radial].rawdata[0][ibin])
                        {
                            data_temp_i_ConZ = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_ConZ = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[0][ibin] - 32768) + 0;
                        }
                        // 填补UnZ值
                        if (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[1][ibin] == 0 || 65535 == *(unsigned char *)&pLineData_temp[i_Radial].rawdata[1][ibin])
                        {
                            data_temp_i_UnZ = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_UnZ = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[1][ibin] - 32768) + 0;
                        }
                        // 填补V值
                        if (*(char *)&pLineData_temp[i_Radial].rawdata[2][ibin] == 0 || 65535 == *(unsigned char *)&pLineData_temp[i_Radial].rawdata[2][ibin])
                        {
                            data_temp_i_V = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_V = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[2][ibin] - 32768) + 0;
                        }
                        // 填补W值
                        if (*(char *)&pLineData_temp[i_Radial].rawdata[3][ibin] == 0 || 65535 == *(unsigned char *)&pLineData_temp[i_Radial].rawdata[3][ibin])
                        {
                            data_temp_i_W = PREFILLVALUE_VTB;
                        }
                        else
                        {
                            data_temp_i_W = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].rawdata[3][ibin] - 32768) + 0;
                        }
                    }
                    else
                    {
                        data_temp_i_ConZ = PREFILLVALUE_VTB;
                        data_temp_i_UnZ = PREFILLVALUE_VTB;
                        data_temp_i_V = PREFILLVALUE_VTB;
                        data_temp_i_W = PREFILLVALUE_VTB;
                    }
                    m_pLineData[i_Radial].CorZ[ibin] = data_temp_i_ConZ;
                    m_pLineData[i_Radial].UnZ[ibin] = data_temp_i_UnZ;
                    m_pLineData[i_Radial].V[ibin] = data_temp_i_V;
                    m_pLineData[i_Radial].W[ibin] = data_temp_i_W;
                }
                i_Radial++;
            }
        }
    }
    else
    {
        cout << "wrong polarizations." << endl;
        return false;
    }

    fclose(file);
    QString radarTypeQString = QString::fromLatin1(m_NewRadarHeader_DUAL->SiteInfo.radartype);
    if (radarTypeQString.contains("721"))
    {
        m_RadarDataHead->OtherInfo.RadarType = 721;
    }
    else
    {
        m_RadarDataHead->OtherInfo.RadarType = 717;
    }
    return true;
}

bool CNrietFileIO::LoadJD720ARadar(char *fileName)
{
    // header
    // Load
    FILE *file = NULL;
    file = fopen(fileName, "rb");
    if (file == NULL)
    {
        qDebug() << "loadSiChuangFile open sichuang radar file error.";
        return false;
    }

    m_RadarHeader720A = new RadarHeader720A();
    fread(m_RadarHeader720A, sizeof(RadarHeader720A), 1, file);
    // get m_nRadialNumSum and m_nLayerNum
    Get_nNumSum_720A();
    if (m_nLayerNum > 32)
    {
        qDebug() << "loadSiChuangFile m_LayerNumber > 32.";
        fclose(file);
        return false;
    }
    // convert
    convertSiChuangHeaderToNewVTB();


    // radial
    m_pLineData = new NewLineDataBlock[m_nRadialNumSum];
    vector<RADARDATABLOCK> pLineData_temp;
    pLineData_temp.resize(m_nRadialNumSum);

    int i_Radial = 0;
//    char tempparam;

    for (int i = 0; i < m_nLayerNum; i++)
    {
//        tempparam = m_RadarDataHead->ObservationInfo.LayerInfo[i].DataForm;
        for (int j = 0; j < m_RadarDataHead->ObservationInfo.LayerInfo[i].RecordNumber; j++)
        {
            // radial header
            fread(&pLineData_temp.at(i_Radial), sizeof(RADARDATABLOCK), 1, file);
            m_pLineData[i_Radial].LineDataInfo.Elev = pLineData_temp.at(i_Radial).sElevation;
            m_pLineData[i_Radial].LineDataInfo.Az = pLineData_temp.at(i_Radial).usAzimuth;
            m_pLineData[i_Radial].LineDataInfo.Hh = pLineData_temp.at(i_Radial).ucHour;
            m_pLineData[i_Radial].LineDataInfo.Mm = pLineData_temp.at(i_Radial).ucMinute;
            m_pLineData[i_Radial].LineDataInfo.Ss = pLineData_temp.at(i_Radial).ucSecond;
            m_pLineData[i_Radial].LineDataInfo.Min = pLineData_temp.at(i_Radial).ulMillisecond;

            // data
            short data_temp_i_ConZ;
            short data_temp_i_UnZ;
            short data_temp_i_V;
            short data_temp_i_W;
            for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
            {
                if (ibin < NUMBEROFBIN)
                {
                    // 填补ConZ值
                    if (*(unsigned char *)&pLineData_temp[i_Radial].ucCorZ[ibin] == 0)
                    {
                        data_temp_i_ConZ = PREFILLVALUE_VTB;
                    }
                    else
                    {
                        data_temp_i_ConZ = 1.0 * ((*(unsigned char *)&pLineData_temp[i_Radial].ucCorZ[ibin] - 64.0) / 2) * 100 + 0;
                    }
                    // 填补UnZ值
                    if (*(unsigned char *)&pLineData_temp[i_Radial].ucUnZ[ibin] == 0)
                    {
                        data_temp_i_UnZ = PREFILLVALUE_VTB;
                    }
                    else
                    {
                        data_temp_i_UnZ = 1.0 * ((*(unsigned char *)&pLineData_temp[i_Radial].ucUnZ[ibin] - 64.0) / 2) * 100 + 0;
                    }
                    // 填补V值
                    if (*(char *)&pLineData_temp[i_Radial].cV[ibin] == -128)
                    {
                        data_temp_i_V = PREFILLVALUE_VTB;
                    }
                    else
                    {
                        data_temp_i_V = 1.0 * (*(char *)&pLineData_temp[i_Radial].cV[ibin] - 128.0) * m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxV / 127;
                    }
                    // 填补W值
                    if (*(unsigned char *)&pLineData_temp[i_Radial].ucW[ibin] == 0)
                    {
                        data_temp_i_W = PREFILLVALUE_VTB;
                    }
                    else
                    {
                        data_temp_i_W = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].ucW[ibin]) * m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxV / 512;
                    }
                }
                else
                {
                    data_temp_i_ConZ = PREFILLVALUE_VTB;
                    data_temp_i_UnZ = PREFILLVALUE_VTB;
                    data_temp_i_V = PREFILLVALUE_VTB;
                    data_temp_i_W = PREFILLVALUE_VTB;
                }
                m_pLineData[i_Radial].CorZ[ibin] = data_temp_i_ConZ;
                m_pLineData[i_Radial].UnZ[ibin] = data_temp_i_UnZ;
                m_pLineData[i_Radial].V[ibin] = data_temp_i_V;
                m_pLineData[i_Radial].W[ibin] = data_temp_i_W;
            }
            i_Radial++;
        }
    }

    fclose(file);
    m_RadarDataHead->OtherInfo.RadarType = 720;
    return true;
}

void CNrietFileIO::convert720ADPHeaderToVTB()
{
    // KLG048720A20240531195059007.VOL
    unsigned short end_year = static_cast<unsigned short>(QString::fromStdString(m_fileTime).mid(0, 4).toUInt());
    // 提取月份并转换为unsigned char
    unsigned char end_month = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(4, 2).toUInt());
    // 提取日期并转换为unsigned char
    unsigned char end_day = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(6, 2).toUInt());
    // 提取小时并转换为unsigned char
    unsigned char end_hour = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(8, 2).toUInt());
    // 提取分钟并转换为unsigned char
    unsigned char end_minute = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(10, 2).toUInt());
    // 提取秒数并转换为unsigned char
    unsigned char end_second = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(12, 2).toUInt());
    //构造VTB文件头
    m_RadarDataHead = new RadarDataHead();
    memset(m_RadarDataHead, 0, sizeof(RadarDataHead));
    strcpy(m_RadarDataHead->FileID, "RD");
    m_RadarDataHead->VersionNo = -2.5f;
    m_RadarDataHead->FileHeaderLength = sizeof(RadarDataHead);

    // radarsite
    strcpy(m_RadarDataHead->SiteInfo.Country, "中国");
    strcpy(m_RadarDataHead->SiteInfo.Province, "unknown");
    strcpy(m_RadarDataHead->SiteInfo.Station, m_radarHeaderNewDP->SiteInfo.station);
    strcpy(m_RadarDataHead->SiteInfo.StationNumber, m_radarHeaderNewDP->SiteInfo.stationnumber);
    strcpy(m_RadarDataHead->SiteInfo.RadarType, m_radarHeaderNewDP->SiteInfo.radartype);
//    qDebug() << "StationNumber = " << m_RadarDataHead->SiteInfo.StationNumber;
//    qDebug() << "RadarType = " << m_RadarDataHead->SiteInfo.RadarType;
//    strcpy(m_RadarDataHead->SiteInfo.Longitude, m_NewRadarHeader_NEWDUAL->SiteInfo.longitude);
//    strcpy(m_RadarDataHead->SiteInfo.Latitude, m_NewRadarHeader_NEWDUAL->SiteInfo.latitude);
    m_RadarDataHead->SiteInfo.LatitudeValue = m_radarHeaderNewDP->SiteInfo.lantitudevalue / 10.0;
    m_RadarDataHead->SiteInfo.LongitudeValue = m_radarHeaderNewDP->SiteInfo.longitudevalue / 10.0;
    m_RadarDataHead->SiteInfo.Height = m_radarHeaderNewDP->SiteInfo.height;
    m_RadarDataHead->SiteInfo.MaxAngle = m_radarHeaderNewDP->SiteInfo.Maxangle;
    m_RadarDataHead->SiteInfo.OptiAngle = m_radarHeaderNewDP->SiteInfo.Opangle;
//    qDebug() << "lantitudevalue = " << m_RadarDataHead->SiteInfo.LatitudeValue;
//    qDebug() << "longitudevalue = " << m_RadarDataHead->SiteInfo.LongitudeValue;
//    qDebug() << "height = " << m_RadarDataHead->SiteInfo.Height;

    // ObservationInfo
    m_RadarDataHead->ObservationInfo.SType = m_radarHeaderNewDP->ObservationInfo.sType;
//    qDebug() << "SType = " << m_RadarDataHead->ObservationInfo.SType;
    m_RadarDataHead->ObservationInfo.SYear = m_radarHeaderNewDP->ObservationInfo.sYear;
    m_RadarDataHead->ObservationInfo.SMonth = m_radarHeaderNewDP->ObservationInfo.sMonth;
    m_RadarDataHead->ObservationInfo.SDay = m_radarHeaderNewDP->ObservationInfo.sDay;
    m_RadarDataHead->ObservationInfo.SHour = m_radarHeaderNewDP->ObservationInfo.sHour;
    m_RadarDataHead->ObservationInfo.SMinute = m_radarHeaderNewDP->ObservationInfo.sMinute;
    m_RadarDataHead->ObservationInfo.SSecond = m_radarHeaderNewDP->ObservationInfo.sSecond;
    m_RadarDataHead->ObservationInfo.TimeP = m_radarHeaderNewDP->ObservationInfo.Timep;
//    m_RadarDataHead->ObservationInfo.SMillisecond = m_NewRadarHeader_NEWDUAL->ObservationInfo.smillisecond;
    m_RadarDataHead->ObservationInfo.Calibration = m_radarHeaderNewDP->ObservationInfo.calibration;
    m_RadarDataHead->ObservationInfo.IntensityI = m_radarHeaderNewDP->ObservationInfo.IntensityI;
    m_RadarDataHead->ObservationInfo.VelocityP = m_radarHeaderNewDP->ObservationInfo.VelocityP;

//    int recordnumber = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[0].recordnumber;
    for (int i = 0; i < m_nLayerNum; i++)
    {
        m_RadarDataHead->ObservationInfo.LayerInfo[i].Ambiguousp = m_radarHeaderNewDP->ObservationInfo.LayerParam[i].ambiguouspR;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DBegin = m_radarHeaderNewDP->ObservationInfo.LayerParam[i].DBegin;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DataForm = 24;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DataType = 8;

        short MaxL = 150;
        short binwidth = m_radarHeaderNewDP->ObservationInfo.LayerParam[i].RBinWidth * 0.1;
//        qDebug() << "binwidth =" << m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].RBinWidth;
        short binnum = MaxL * 1000 / binwidth;// m_radarHeader784DP.ObservationInfo.LayerParam[i].RBinnumber;//334;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxL = MaxL * 100;// m_radarHeader784DP.ObservationInfo.LayerParam[i].MaxL;
//        qDebug() << "MaxL = " << m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxL;

        m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxV = m_radarHeaderNewDP->ObservationInfo.LayerParam[i].MaxV;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].PRF1 = m_radarHeaderNewDP->ObservationInfo.LayerParam[i].Prf1;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].PRF2 = m_radarHeaderNewDP->ObservationInfo.LayerParam[i].Prf2;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].PluseW = m_radarHeaderNewDP->ObservationInfo.LayerParam[i].PluseW;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].RecordNumber = m_radarHeaderNewDP->ObservationInfo.LayerParam[i].recordnumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DPbinNumber = m_radarHeaderNewDP->ObservationInfo.LayerParam[i].Arotate;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].SwpAngles = m_radarHeaderNewDP->ObservationInfo.LayerParam[i].Swangles;
//        qDebug() << "SwpAngles = " << m_RadarDataHead->ObservationInfo.LayerInfo[i].SwpAngles;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].VbinNumber = binnum;//m_radarHeader784DP.ObservationInfo.LayerParam[i].VBinnumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].VBinWidth = m_radarHeaderNewDP->ObservationInfo.LayerParam[i].VBinWidth;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].WbinNumber = binnum;//m_radarHeader784DP.ObservationInfo.LayerParam[i].WBinnumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].WBinWidth = m_radarHeaderNewDP->ObservationInfo.LayerParam[i].WBinWidth;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber = binnum;// m_radarHeader784DP.ObservationInfo.LayerParam[i].RBinnumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].ZBinWidth = m_radarHeaderNewDP->ObservationInfo.LayerParam[i].RBinWidth;
    }

    m_RadarDataHead->ObservationInfo.EYear = end_year;
    m_RadarDataHead->ObservationInfo.EMonth = end_month;
    m_RadarDataHead->ObservationInfo.EDay = end_day;
    m_RadarDataHead->ObservationInfo.EHour = end_hour;
    m_RadarDataHead->ObservationInfo.EMinute = end_minute;
    m_RadarDataHead->ObservationInfo.ESecond = end_second;
    //m_RadarDataHead->ObservationInfo.ETenth = m_radarHeader784DP.ObservationInfo.Etenth;
    m_RadarDataHead->ObservationInfo.ZBinByte = 0;
    m_RadarDataHead->ObservationInfo.ZStartBin = 0;
    m_RadarDataHead->ObservationInfo.VBinByte = 0;
    m_RadarDataHead->ObservationInfo.VStartBin = 0;
    m_RadarDataHead->ObservationInfo.WBinByte = 0;
    m_RadarDataHead->ObservationInfo.WStartBin = 0;

    // PerformanceInfo
    m_RadarDataHead->PerformanceInfo.AntennaG = m_radarHeaderNewDP->PerformanceInfo.AntennaG;
    m_RadarDataHead->PerformanceInfo.VerBeamW = m_radarHeaderNewDP->PerformanceInfo.BeamH;
    m_RadarDataHead->PerformanceInfo.HorBeamW = m_radarHeaderNewDP->PerformanceInfo.BeamL;
    m_RadarDataHead->PerformanceInfo.Polarizations = m_radarHeaderNewDP->PerformanceInfo.polarizations;
    m_RadarDataHead->PerformanceInfo.SideLobe = m_radarHeaderNewDP->PerformanceInfo.sidelobe;
    m_RadarDataHead->PerformanceInfo.Power = m_radarHeaderNewDP->PerformanceInfo.Power;
    m_RadarDataHead->PerformanceInfo.WaveLength = m_radarHeaderNewDP->PerformanceInfo.wavelength;
    m_RadarDataHead->PerformanceInfo.LogA = m_radarHeaderNewDP->PerformanceInfo.logA;
    m_RadarDataHead->PerformanceInfo.LineA = m_radarHeaderNewDP->PerformanceInfo.LineA;
    m_RadarDataHead->PerformanceInfo.AGCP = m_radarHeaderNewDP->PerformanceInfo.AGCP;
    m_RadarDataHead->PerformanceInfo.LogMinPower = 0;
    m_RadarDataHead->PerformanceInfo.LineMinPower = 0;
    m_RadarDataHead->PerformanceInfo.ClutterT = m_radarHeaderNewDP->PerformanceInfo.clutterT;
    m_RadarDataHead->PerformanceInfo.VelocityP = m_radarHeaderNewDP->PerformanceInfo.VelocityP;
    m_RadarDataHead->PerformanceInfo.FilterP = m_radarHeaderNewDP->PerformanceInfo.filderP;
    m_RadarDataHead->PerformanceInfo.NoiseT = m_radarHeaderNewDP->PerformanceInfo.noiseT;
    m_RadarDataHead->PerformanceInfo.SQIT = m_radarHeaderNewDP->PerformanceInfo.SQIT;
    m_RadarDataHead->PerformanceInfo.IntensityC = m_radarHeaderNewDP->PerformanceInfo.intensityC;
    m_RadarDataHead->PerformanceInfo.IntensityR = m_radarHeaderNewDP->PerformanceInfo.intensityR;

//    // test station info
//    qDebug() << "LatitudeValue = " << m_RadarDataHead->SiteInfo.LatitudeValue << endl;
//    qDebug() << "LongitudeValue = " << m_RadarDataHead->SiteInfo.LongitudeValue << endl;
//    qDebug() << "Height = " << m_RadarDataHead->SiteInfo.Height << endl;
//    qDebug() << "sStationNumber = " << m_RadarDataHead->SiteInfo.StationNumber << endl;
//    qDebug() << "sRadarType = " << m_RadarDataHead->SiteInfo.RadarType << endl;
//    for (int i = 0; i < m_nLayerNum; i++)
//    {
//        qDebug() << "MaxL =" << m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxL;
//    }
}

void CNrietFileIO::convert784DPHeaderToVTB()
{
    //KLG298717020240528074544000.PPI
    unsigned short end_year = static_cast<unsigned short>(QString::fromStdString(m_fileTime).mid(0, 4).toUInt());
    // 提取月份并转换为unsigned char
    unsigned char end_month = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(4, 2).toUInt());
    // 提取日期并转换为unsigned char
    unsigned char end_day = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(6, 2).toUInt());
    // 提取小时并转换为unsigned char
    unsigned char end_hour = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(8, 2).toUInt());
    // 提取分钟并转换为unsigned char
    unsigned char end_minute = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(10, 2).toUInt());
    // 提取秒数并转换为unsigned char
    unsigned char end_second = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(12, 2).toUInt());
    //构造VTB文件头
    m_RadarDataHead = new RadarDataHead();
    memset(m_RadarDataHead, 0, sizeof(RadarDataHead));
    strcpy(m_RadarDataHead->FileID, "RD");
    m_RadarDataHead->VersionNo = -2.5f;
    m_RadarDataHead->FileHeaderLength = sizeof(RadarDataHead);

    // radarsite
    strcpy(m_RadarDataHead->SiteInfo.Country, "中国");
    strcpy(m_RadarDataHead->SiteInfo.Province, "unknown");
    strcpy(m_RadarDataHead->SiteInfo.Station, m_NewRadarHeader_NEWDUAL->SiteInfo.station);
    strcpy(m_RadarDataHead->SiteInfo.StationNumber, m_NewRadarHeader_NEWDUAL->SiteInfo.stationnumber);
    strcpy(m_RadarDataHead->SiteInfo.RadarType, m_NewRadarHeader_NEWDUAL->SiteInfo.radartype);
//    qDebug() << "StationNumber = " << m_RadarDataHead->SiteInfo.StationNumber;
//    qDebug() << "RadarType = " << m_RadarDataHead->SiteInfo.RadarType;
//    strcpy(m_RadarDataHead->SiteInfo.Longitude, m_NewRadarHeader_NEWDUAL->SiteInfo.longitude);
//    strcpy(m_RadarDataHead->SiteInfo.Latitude, m_NewRadarHeader_NEWDUAL->SiteInfo.latitude);
    m_RadarDataHead->SiteInfo.LatitudeValue = m_NewRadarHeader_NEWDUAL->SiteInfo.lantitudevalue / 10.0;
    m_RadarDataHead->SiteInfo.LongitudeValue = m_NewRadarHeader_NEWDUAL->SiteInfo.longitudevalue / 10.0;
    m_RadarDataHead->SiteInfo.Height = m_NewRadarHeader_NEWDUAL->SiteInfo.height;
    m_RadarDataHead->SiteInfo.MaxAngle = m_NewRadarHeader_NEWDUAL->SiteInfo.Maxangle;
    m_RadarDataHead->SiteInfo.OptiAngle = m_NewRadarHeader_NEWDUAL->SiteInfo.Opangle;
//    qDebug() << "lantitudevalue = " << m_RadarDataHead->SiteInfo.LatitudeValue;
//    qDebug() << "longitudevalue = " << m_RadarDataHead->SiteInfo.LongitudeValue;
//    qDebug() << "height = " << m_RadarDataHead->SiteInfo.Height;

    // ObservationInfo
    m_RadarDataHead->ObservationInfo.SType = m_NewRadarHeader_NEWDUAL->ObservationInfo.sType;
//    qDebug() << "SType = " << m_RadarDataHead->ObservationInfo.SType;
    m_RadarDataHead->ObservationInfo.SYear = m_NewRadarHeader_NEWDUAL->ObservationInfo.sYear;
    m_RadarDataHead->ObservationInfo.SMonth = m_NewRadarHeader_NEWDUAL->ObservationInfo.sMonth;
    m_RadarDataHead->ObservationInfo.SDay = m_NewRadarHeader_NEWDUAL->ObservationInfo.sDay;
    m_RadarDataHead->ObservationInfo.SHour = m_NewRadarHeader_NEWDUAL->ObservationInfo.sHour;
    m_RadarDataHead->ObservationInfo.SMinute = m_NewRadarHeader_NEWDUAL->ObservationInfo.sMinute;
    m_RadarDataHead->ObservationInfo.SSecond = m_NewRadarHeader_NEWDUAL->ObservationInfo.sSecond;
    m_RadarDataHead->ObservationInfo.TimeP = m_NewRadarHeader_NEWDUAL->ObservationInfo.Timep;
//    m_RadarDataHead->ObservationInfo.SMillisecond = m_NewRadarHeader_NEWDUAL->ObservationInfo.smillisecond;
    m_RadarDataHead->ObservationInfo.Calibration = m_NewRadarHeader_NEWDUAL->ObservationInfo.calibration;
    m_RadarDataHead->ObservationInfo.IntensityI = m_NewRadarHeader_NEWDUAL->ObservationInfo.IntensityI;
    m_RadarDataHead->ObservationInfo.VelocityP = m_NewRadarHeader_NEWDUAL->ObservationInfo.VelocityP;

//    int recordnumber = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[0].recordnumber;
    for (int i = 0; i < m_nLayerNum; i++)
    {
        m_RadarDataHead->ObservationInfo.LayerInfo[i].Ambiguousp = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].ambiguouspR;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DBegin = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].DBegin;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DataForm = 24;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DataType = 8;

        short MaxL = 150;
        short binwidth = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].RBinWidth * 0.1;
//        qDebug() << "binwidth =" << m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].RBinWidth;
        short binnum = MaxL * 1000 / binwidth;// m_radarHeader784DP.ObservationInfo.LayerParam[i].RBinnumber;//334;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxL = MaxL * 100;// m_radarHeader784DP.ObservationInfo.LayerParam[i].MaxL;
//        qDebug() << "MaxL = " << m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxL;

        m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxV = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].MaxV;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].PRF1 = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].Prf1;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].PRF2 = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].Prf2;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].PluseW = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].PluseW;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].RecordNumber = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].recordnumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DPbinNumber = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].Arotate;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].SwpAngles = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].Swangles;
//        qDebug() << "SwpAngles = " << m_RadarDataHead->ObservationInfo.LayerInfo[i].SwpAngles;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].VbinNumber = binnum;//m_radarHeader784DP.ObservationInfo.LayerParam[i].VBinnumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].VBinWidth = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].VBinWidth;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].WbinNumber = binnum;//m_radarHeader784DP.ObservationInfo.LayerParam[i].WBinnumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].WBinWidth = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].WBinWidth;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber = binnum;// m_radarHeader784DP.ObservationInfo.LayerParam[i].RBinnumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].ZBinWidth = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].RBinWidth;
    }

    m_RadarDataHead->ObservationInfo.RHIA = m_NewRadarHeader_NEWDUAL->ObservationInfo.RHIA;
    m_RadarDataHead->ObservationInfo.RHIL = m_NewRadarHeader_NEWDUAL->ObservationInfo.RHIL;
    m_RadarDataHead->ObservationInfo.RHIH = m_NewRadarHeader_NEWDUAL->ObservationInfo.RHIH;
//    qDebug() << "RHIA = " << m_RadarDataHead->ObservationInfo.RHIA;
//    qDebug() << "RHIL = " << m_RadarDataHead->ObservationInfo.RHIL;
//    qDebug() << "RHIH = " << m_RadarDataHead->ObservationInfo.RHIH;
    m_RadarDataHead->ObservationInfo.EYear = end_year;
    m_RadarDataHead->ObservationInfo.EMonth = end_month;
    m_RadarDataHead->ObservationInfo.EDay = end_day;
    m_RadarDataHead->ObservationInfo.EHour = end_hour;
    m_RadarDataHead->ObservationInfo.EMinute = end_minute;
    m_RadarDataHead->ObservationInfo.ESecond = end_second;
    //m_RadarDataHead->ObservationInfo.ETenth = m_radarHeader784DP.ObservationInfo.Etenth;
    m_RadarDataHead->ObservationInfo.ZBinByte = 0;
    m_RadarDataHead->ObservationInfo.ZStartBin = 0;
    m_RadarDataHead->ObservationInfo.VBinByte = 0;
    m_RadarDataHead->ObservationInfo.VStartBin = 0;
    m_RadarDataHead->ObservationInfo.WBinByte = 0;
    m_RadarDataHead->ObservationInfo.WStartBin = 0;

    // PerformanceInfo
    m_RadarDataHead->PerformanceInfo.AntennaG = m_NewRadarHeader_NEWDUAL->PerformanceInfo.AntennaG;
    m_RadarDataHead->PerformanceInfo.VerBeamW = m_NewRadarHeader_NEWDUAL->PerformanceInfo.BeamH;
    m_RadarDataHead->PerformanceInfo.HorBeamW = m_NewRadarHeader_NEWDUAL->PerformanceInfo.BeamL;
    m_RadarDataHead->PerformanceInfo.Polarizations = m_NewRadarHeader_NEWDUAL->PerformanceInfo.polarizations;
    m_RadarDataHead->PerformanceInfo.SideLobe = m_NewRadarHeader_NEWDUAL->PerformanceInfo.sidelobe;
    m_RadarDataHead->PerformanceInfo.Power = m_NewRadarHeader_NEWDUAL->PerformanceInfo.Power;
    m_RadarDataHead->PerformanceInfo.WaveLength = m_NewRadarHeader_NEWDUAL->PerformanceInfo.wavelength;
    m_RadarDataHead->PerformanceInfo.LogA = m_NewRadarHeader_NEWDUAL->PerformanceInfo.logA;
    m_RadarDataHead->PerformanceInfo.LineA = m_NewRadarHeader_NEWDUAL->PerformanceInfo.LineA;
    m_RadarDataHead->PerformanceInfo.AGCP = m_NewRadarHeader_NEWDUAL->PerformanceInfo.AGCP;
    m_RadarDataHead->PerformanceInfo.LogMinPower = 0;
    m_RadarDataHead->PerformanceInfo.LineMinPower = 0;
    m_RadarDataHead->PerformanceInfo.ClutterT = m_NewRadarHeader_NEWDUAL->PerformanceInfo.clutterT;
    m_RadarDataHead->PerformanceInfo.VelocityP = m_NewRadarHeader_NEWDUAL->PerformanceInfo.VelocityP;
    m_RadarDataHead->PerformanceInfo.FilterP = m_NewRadarHeader_NEWDUAL->PerformanceInfo.filderP;
    m_RadarDataHead->PerformanceInfo.NoiseT = m_NewRadarHeader_NEWDUAL->PerformanceInfo.noiseT;
    m_RadarDataHead->PerformanceInfo.SQIT = m_NewRadarHeader_NEWDUAL->PerformanceInfo.SQIT;
    m_RadarDataHead->PerformanceInfo.IntensityC = m_NewRadarHeader_NEWDUAL->PerformanceInfo.intensityC;
    m_RadarDataHead->PerformanceInfo.IntensityR = m_NewRadarHeader_NEWDUAL->PerformanceInfo.intensityR;
}

void CNrietFileIO::convert784newdualHeaderToVTB()
{
    // HLG00006SD20240528201006015.PPI
    unsigned short end_year = static_cast<unsigned short>(QString::fromStdString(m_fileTime).mid(0, 4).toUInt());
    // 提取月份并转换为unsigned char
    unsigned char end_month = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(4, 2).toUInt());
    // 提取日期并转换为unsigned char
    unsigned char end_day = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(6, 2).toUInt());
    // 提取小时并转换为unsigned char
    unsigned char end_hour = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(8, 2).toUInt());
    // 提取分钟并转换为unsigned char
    unsigned char end_minute = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(10, 2).toUInt());
    // 提取秒数并转换为unsigned char
    unsigned char end_second = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(12, 2).toUInt());
    //构造VTB文件头
    m_RadarDataHead = new RadarDataHead();
    memset(m_RadarDataHead, 0, sizeof(RadarDataHead));
    strcpy(m_RadarDataHead->FileID, "RD");
    m_RadarDataHead->VersionNo = -2.5f;
    m_RadarDataHead->FileHeaderLength = sizeof(RadarDataHead);

    // radarsite
    strcpy(m_RadarDataHead->SiteInfo.Country, "中国");
    strcpy(m_RadarDataHead->SiteInfo.Province, "unknown");
    strcpy(m_RadarDataHead->SiteInfo.Station, m_NewRadarHeader_NEWDUAL->SiteInfo.station);
    strcpy(m_RadarDataHead->SiteInfo.StationNumber, m_NewRadarHeader_NEWDUAL->SiteInfo.stationnumber);
    strcpy(m_RadarDataHead->SiteInfo.RadarType, m_NewRadarHeader_NEWDUAL->SiteInfo.radartype);
//    strcpy(m_RadarDataHead->SiteInfo.Longitude, m_NewRadarHeader_NEWDUAL->SiteInfo.longitude);
//    strcpy(m_RadarDataHead->SiteInfo.Latitude, m_NewRadarHeader_NEWDUAL->SiteInfo.latitude);
//    qDebug() << "StationNumber = " << m_RadarDataHead->SiteInfo.StationNumber;
//    qDebug() << "RadarType = " << m_RadarDataHead->SiteInfo.RadarType;
    m_RadarDataHead->SiteInfo.LatitudeValue = m_NewRadarHeader_NEWDUAL->SiteInfo.lantitudevalue / 10.0;
    m_RadarDataHead->SiteInfo.LongitudeValue = m_NewRadarHeader_NEWDUAL->SiteInfo.longitudevalue / 10.0;
    m_RadarDataHead->SiteInfo.Height = m_NewRadarHeader_NEWDUAL->SiteInfo.height;
    m_RadarDataHead->SiteInfo.MaxAngle = m_NewRadarHeader_NEWDUAL->SiteInfo.Maxangle;
    m_RadarDataHead->SiteInfo.OptiAngle = m_NewRadarHeader_NEWDUAL->SiteInfo.Opangle;
//    qDebug() << "lantitudevalue = " << m_RadarDataHead->SiteInfo.LatitudeValue;
//    qDebug() << "longitudevalue = " << m_RadarDataHead->SiteInfo.LongitudeValue;
//    qDebug() << "Height = " << m_RadarDataHead->SiteInfo.Height;

    // ObservationInfo
    m_RadarDataHead->ObservationInfo.SType = m_NewRadarHeader_NEWDUAL->ObservationInfo.sType;
//    qDebug() << "SType = " << m_RadarDataHead->ObservationInfo.SType;
    m_RadarDataHead->ObservationInfo.SYear = m_NewRadarHeader_NEWDUAL->ObservationInfo.sYear;
    m_RadarDataHead->ObservationInfo.SMonth = m_NewRadarHeader_NEWDUAL->ObservationInfo.sMonth;
    m_RadarDataHead->ObservationInfo.SDay = m_NewRadarHeader_NEWDUAL->ObservationInfo.sDay;
    m_RadarDataHead->ObservationInfo.SHour = m_NewRadarHeader_NEWDUAL->ObservationInfo.sHour;
    m_RadarDataHead->ObservationInfo.SMinute = m_NewRadarHeader_NEWDUAL->ObservationInfo.sMinute;
    m_RadarDataHead->ObservationInfo.SSecond = m_NewRadarHeader_NEWDUAL->ObservationInfo.sSecond;
    m_RadarDataHead->ObservationInfo.TimeP = m_NewRadarHeader_NEWDUAL->ObservationInfo.Timep;
//    m_RadarDataHead->ObservationInfo.SMillisecond = m_NewRadarHeader_NEWDUAL->ObservationInfo.smillisecond;
    m_RadarDataHead->ObservationInfo.Calibration = m_NewRadarHeader_NEWDUAL->ObservationInfo.calibration;
    m_RadarDataHead->ObservationInfo.IntensityI = m_NewRadarHeader_NEWDUAL->ObservationInfo.IntensityI;
    m_RadarDataHead->ObservationInfo.VelocityP = m_NewRadarHeader_NEWDUAL->ObservationInfo.VelocityP;

//    int recordnumber = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[0].recordnumber;
    for (int i = 0; i < m_nLayerNum; i++)
    {
        m_RadarDataHead->ObservationInfo.LayerInfo[i].Ambiguousp = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].ambiguouspR;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DBegin = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].DBegin;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DataForm = 24;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DataType = 8;

        short binwidth = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].RBinWidth * 0.1;
//        qDebug() << "binwidth =" << m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].RBinWidth;
        short binnum = 1000;// m_radarHeader784DP.ObservationInfo.LayerParam[i].RBinnumber;//334;
        short MaxL = binwidth;// 150;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxL = MaxL * 100;// m_radarHeader784DP.ObservationInfo.LayerParam[i].MaxL;
//        qDebug() << "MaxL = " << m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxL;

        m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxV = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].MaxV;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].PRF1 = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].Prf1;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].PRF2 = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].Prf2;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].PluseW = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].PluseW;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].RecordNumber = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].recordnumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DPbinNumber = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].Arotate;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].SwpAngles = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].Swangles;
//        qDebug() << "SwpAngles = " << m_RadarDataHead->ObservationInfo.LayerInfo[i].SwpAngles;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].VbinNumber = binnum;//m_radarHeader784DP.ObservationInfo.LayerParam[i].VBinnumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].VBinWidth = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].VBinWidth;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].WbinNumber = binnum;//m_radarHeader784DP.ObservationInfo.LayerParam[i].WBinnumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].WBinWidth = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].WBinWidth;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber = binnum;// m_radarHeader784DP.ObservationInfo.LayerParam[i].RBinnumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].ZBinWidth = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].RBinWidth;
    }

    m_RadarDataHead->ObservationInfo.RHIA = m_NewRadarHeader_NEWDUAL->ObservationInfo.RHIA;
    m_RadarDataHead->ObservationInfo.RHIL = m_NewRadarHeader_NEWDUAL->ObservationInfo.RHIL;
    m_RadarDataHead->ObservationInfo.RHIH = m_NewRadarHeader_NEWDUAL->ObservationInfo.RHIH;
//    qDebug() << "RHIA = " << m_RadarDataHead->ObservationInfo.RHIA;
//    qDebug() << "RHIL = " << m_RadarDataHead->ObservationInfo.RHIL;
//    qDebug() << "RHIH = " << m_RadarDataHead->ObservationInfo.RHIH;
    m_RadarDataHead->ObservationInfo.EYear = end_year;
    m_RadarDataHead->ObservationInfo.EMonth = end_month;
    m_RadarDataHead->ObservationInfo.EDay = end_day;
    m_RadarDataHead->ObservationInfo.EHour = end_hour;
    m_RadarDataHead->ObservationInfo.EMinute = end_minute;
    m_RadarDataHead->ObservationInfo.ESecond = end_second;
    //m_RadarDataHead->ObservationInfo.ETenth = m_radarHeader784DP.ObservationInfo.Etenth;
    m_RadarDataHead->ObservationInfo.ZBinByte = 0;
    m_RadarDataHead->ObservationInfo.ZStartBin = 0;
    m_RadarDataHead->ObservationInfo.VBinByte = 0;
    m_RadarDataHead->ObservationInfo.VStartBin = 0;
    m_RadarDataHead->ObservationInfo.WBinByte = 0;
    m_RadarDataHead->ObservationInfo.WStartBin = 0;

    // PerformanceInfo
    m_RadarDataHead->PerformanceInfo.AntennaG = m_NewRadarHeader_NEWDUAL->PerformanceInfo.AntennaG;
    m_RadarDataHead->PerformanceInfo.VerBeamW = m_NewRadarHeader_NEWDUAL->PerformanceInfo.BeamH;
    m_RadarDataHead->PerformanceInfo.HorBeamW = m_NewRadarHeader_NEWDUAL->PerformanceInfo.BeamL;
    m_RadarDataHead->PerformanceInfo.Polarizations = m_NewRadarHeader_NEWDUAL->PerformanceInfo.polarizations;
    m_RadarDataHead->PerformanceInfo.SideLobe = m_NewRadarHeader_NEWDUAL->PerformanceInfo.sidelobe;
    m_RadarDataHead->PerformanceInfo.Power = m_NewRadarHeader_NEWDUAL->PerformanceInfo.Power;
    m_RadarDataHead->PerformanceInfo.WaveLength = m_NewRadarHeader_NEWDUAL->PerformanceInfo.wavelength;
    m_RadarDataHead->PerformanceInfo.LogA = m_NewRadarHeader_NEWDUAL->PerformanceInfo.logA;
    m_RadarDataHead->PerformanceInfo.LineA = m_NewRadarHeader_NEWDUAL->PerformanceInfo.LineA;
    m_RadarDataHead->PerformanceInfo.AGCP = m_NewRadarHeader_NEWDUAL->PerformanceInfo.AGCP;
    m_RadarDataHead->PerformanceInfo.LogMinPower = 0;
    m_RadarDataHead->PerformanceInfo.LineMinPower = 0;
    m_RadarDataHead->PerformanceInfo.ClutterT = m_NewRadarHeader_NEWDUAL->PerformanceInfo.clutterT;
    m_RadarDataHead->PerformanceInfo.VelocityP = m_NewRadarHeader_NEWDUAL->PerformanceInfo.VelocityP;
    m_RadarDataHead->PerformanceInfo.FilterP = m_NewRadarHeader_NEWDUAL->PerformanceInfo.filderP;
    m_RadarDataHead->PerformanceInfo.NoiseT = m_NewRadarHeader_NEWDUAL->PerformanceInfo.noiseT;
    m_RadarDataHead->PerformanceInfo.SQIT = m_NewRadarHeader_NEWDUAL->PerformanceInfo.SQIT;
    m_RadarDataHead->PerformanceInfo.IntensityC = m_NewRadarHeader_NEWDUAL->PerformanceInfo.intensityC;
    m_RadarDataHead->PerformanceInfo.IntensityR = m_NewRadarHeader_NEWDUAL->PerformanceInfo.intensityR;
}

void CNrietFileIO::convert784dualHeaderToVTB()
{
    // 2024052807300.20p
    unsigned short end_year = static_cast<unsigned short>(QString::fromStdString(m_fileTime).mid(0, 4).toUInt());
    // 提取月份并转换为unsigned char
    unsigned char end_month = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(4, 2).toUInt());
    // 提取日期并转换为unsigned char
    unsigned char end_day = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(6, 2).toUInt());
    // 提取小时并转换为unsigned char
    unsigned char end_hour = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(8, 2).toUInt());
    // 提取分钟并转换为unsigned char
    unsigned char end_minute = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(10, 2).toUInt());
    // 提取秒数并转换为unsigned char
    unsigned char end_second = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(12, 2).toUInt());

    //构造VTB文件头
    m_RadarDataHead = new RadarDataHead();
    memset(m_RadarDataHead, 0, sizeof(RadarDataHead));
    strcpy(m_RadarDataHead->FileID, "RD");
    m_RadarDataHead->VersionNo = -2.5f;
    m_RadarDataHead->FileHeaderLength = sizeof(RadarDataHead);

    // SiteInfo
    strcpy(m_RadarDataHead->SiteInfo.Country, m_NewRadarHeader_DUAL->SiteInfo.country);
    strcpy(m_RadarDataHead->SiteInfo.Province, m_NewRadarHeader_DUAL->SiteInfo.province);
    strcpy(m_RadarDataHead->SiteInfo.Station, m_NewRadarHeader_DUAL->SiteInfo.station);
//    qDebug() << "station = " << h.SiteInfo.Station;
    strcpy(m_RadarDataHead->SiteInfo.StationNumber, m_NewRadarHeader_DUAL->SiteInfo.stationnumber);
//    qDebug() << "stationnumber = " << m_RadarDataHead->SiteInfo.StationNumber;
    strcpy(m_RadarDataHead->SiteInfo.RadarType, m_NewRadarHeader_DUAL->SiteInfo.radartype);
//    qDebug() << "radartype = " << m_RadarDataHead->SiteInfo.RadarType;
    strcpy(m_RadarDataHead->SiteInfo.Longitude, m_NewRadarHeader_DUAL->SiteInfo.longitude);
    strcpy(m_RadarDataHead->SiteInfo.Latitude, m_NewRadarHeader_DUAL->SiteInfo.latitude);
    m_RadarDataHead->SiteInfo.LatitudeValue = m_NewRadarHeader_DUAL->SiteInfo.lantitudevalue * 10.0;
    m_RadarDataHead->SiteInfo.LongitudeValue = m_NewRadarHeader_DUAL->SiteInfo.longitudevalue * 10.0;
    m_RadarDataHead->SiteInfo.Height = m_NewRadarHeader_DUAL->SiteInfo.height;
//    qDebug() << "lantitudevalue = " << m_RadarDataHead->SiteInfo.LatitudeValue;
//    qDebug() << "longitudevalue = " << m_RadarDataHead->SiteInfo.LongitudeValue;
//    qDebug() << "Height = " << m_RadarDataHead->SiteInfo.Height;
    m_RadarDataHead->SiteInfo.MaxAngle = m_NewRadarHeader_DUAL->SiteInfo.Maxangle;
    m_RadarDataHead->SiteInfo.OptiAngle = m_NewRadarHeader_DUAL->SiteInfo.Opangle;

    // ObservationInfo
    m_RadarDataHead->ObservationInfo.SType = m_NewRadarHeader_DUAL->ObservationInfo.stype;
//    qDebug() << "SType = " << m_RadarDataHead->ObservationInfo.SType;
    m_RadarDataHead->ObservationInfo.SYear = m_NewRadarHeader_DUAL->ObservationInfo.syear;
    m_RadarDataHead->ObservationInfo.SMonth = m_NewRadarHeader_DUAL->ObservationInfo.smonth;
    m_RadarDataHead->ObservationInfo.SDay = m_NewRadarHeader_DUAL->ObservationInfo.sday;
    m_RadarDataHead->ObservationInfo.SHour = m_NewRadarHeader_DUAL->ObservationInfo.shour;
    m_RadarDataHead->ObservationInfo.SMinute = m_NewRadarHeader_DUAL->ObservationInfo.sminute;
    m_RadarDataHead->ObservationInfo.SSecond = m_NewRadarHeader_DUAL->ObservationInfo.ssecond;
    m_RadarDataHead->ObservationInfo.TimeP = m_NewRadarHeader_DUAL->ObservationInfo.Timep;
    m_RadarDataHead->ObservationInfo.SMillisecond = m_NewRadarHeader_DUAL->ObservationInfo.smillisecond;

//    qDebug() << "SYear = " << h.ObservationInfo.SYear;
//    qDebug() << "SMonth = " << h.ObservationInfo.SMonth;
//    qDebug() << "SDay = " << h.ObservationInfo.SDay;
//    qDebug() << "SHour = " << h.ObservationInfo.SHour;
//    qDebug() << "SMinute = " << h.ObservationInfo.SMinute;
//    qDebug() << "SSecond = " << h.ObservationInfo.SSecond;

    m_RadarDataHead->ObservationInfo.Calibration = m_NewRadarHeader_DUAL->ObservationInfo.calibration;
    m_RadarDataHead->ObservationInfo.IntensityI = m_NewRadarHeader_DUAL->ObservationInfo.intensityI;
    m_RadarDataHead->ObservationInfo.VelocityP = m_NewRadarHeader_DUAL->ObservationInfo.VelocityP;
//    h.ObservationInfo.VelocityP = m_radarHeader784DUAL.ObservationInfo.VelocityP - 1;

    for (int i = 0; i < m_nLayerNum; i++)
    {
        m_RadarDataHead->ObservationInfo.LayerInfo[i].Ambiguousp = m_NewRadarHeader_DUAL->ObservationInfo.LayerParam[i].ambiguousp;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DBegin = 0;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DataForm = 24;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DataType = 8;
        short MaxL = 150;//150km m_radarHeader784DUAL.ObservationInfo.LayerParam[i].MaxL / 100.0 + 0.5;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxL = MaxL * 100;// m_radarHeader784DUAL.ObservationInfo.LayerParam[i].MaxL;
//        qDebug() << "MaxL =" << m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxL;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxV = m_NewRadarHeader_DUAL->ObservationInfo.LayerParam[i].MaxV;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].PRF1 = m_NewRadarHeader_DUAL->ObservationInfo.LayerParam[i].Prf1;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].PRF2 = m_NewRadarHeader_DUAL->ObservationInfo.LayerParam[i].Prf2;
//        qDebug() << h.ObservationInfo.LayerInfo[i].PRF1;
//        qDebug() << h.ObservationInfo.LayerInfo[i].PRF2;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].PluseW = m_NewRadarHeader_DUAL->ObservationInfo.LayerParam[i].spulseW;
//        h.ObservationInfo.LayerInfo[i].PulseW = m_radarHeader784DUAL.ObservationInfo.LayerParam[i].spulseW / 10;
//        qDebug() << h.ObservationInfo.LayerInfo[i].PulseW;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].RecordNumber = m_NewRadarHeader_DUAL->ObservationInfo.LayerParam[i].recordnumber;
//        qDebug() << "RecordNumber = " << m_RadarDataHead->ObservationInfo.LayerInfo[i].RecordNumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DPbinNumber = m_NewRadarHeader_DUAL->ObservationInfo.LayerParam[i].Arotate;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].SwpAngles = m_NewRadarHeader_DUAL->ObservationInfo.LayerParam[i].Swangles;
//        qDebug() << "SwpAngles = " << m_RadarDataHead->ObservationInfo.LayerInfo[i].SwpAngles;

        short binwidth = m_NewRadarHeader_DUAL->ObservationInfo.LayerParam[i].binWidth;
//        qDebug() << "binwidth =" << m_RadarDataHead->ObservationInfo.LayerParam[i].binWidth;
        short binnum = MaxL * 10000 / binwidth;//1000;// m_radarHeader784DUAL.ObservationInfo.LayerParam[i].binnumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].VbinNumber = binnum;// m_radarHeader784DUAL.ObservationInfo.LayerParam[i].binnumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].VBinWidth = binwidth;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].WbinNumber = binnum;//m_radarHeader784DUAL.ObservationInfo.LayerParam[i].binnumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].WBinWidth = binwidth;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber = binnum;//m_radarHeader784DUAL.ObservationInfo.LayerParam[i].binnumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].ZBinWidth = binwidth;
    }

    m_RadarDataHead->ObservationInfo.RHIA = m_NewRadarHeader_DUAL->ObservationInfo.RHIA;
//    qDebug() << "RHIA = " << m_RadarDataHead->ObservationInfo.RHIA;
    m_RadarDataHead->ObservationInfo.RHIL = m_NewRadarHeader_DUAL->ObservationInfo.RHIL;
//    qDebug() << "RHIL = " << m_RadarDataHead->ObservationInfo.RHIL;
    m_RadarDataHead->ObservationInfo.RHIH = m_NewRadarHeader_DUAL->ObservationInfo.RHIH;
//    qDebug() << "RHIH = " << m_RadarDataHead->ObservationInfo.RHIH;
//    m_RadarDataHead->ObservationInfo.EYear = m_NewRadarHeader_DUAL->ObservationInfo.Eyear;
//    m_RadarDataHead->ObservationInfo.EMonth = m_NewRadarHeader_DUAL->ObservationInfo.Emonth;
//    m_RadarDataHead->ObservationInfo.EDay = m_NewRadarHeader_DUAL->ObservationInfo.Eday;
//    m_RadarDataHead->ObservationInfo.EHour = m_NewRadarHeader_DUAL->ObservationInfo.Ehour;
//    m_RadarDataHead->ObservationInfo.EMinute = m_NewRadarHeader_DUAL->ObservationInfo.Eminute;
//    m_RadarDataHead->ObservationInfo.ESecond = m_NewRadarHeader_DUAL->ObservationInfo.Esecond;
    m_RadarDataHead->ObservationInfo.EYear = end_year;
    m_RadarDataHead->ObservationInfo.EMonth = end_month;
    m_RadarDataHead->ObservationInfo.EDay = end_day;
    m_RadarDataHead->ObservationInfo.EHour = end_hour;
    m_RadarDataHead->ObservationInfo.EMinute = end_minute;
    m_RadarDataHead->ObservationInfo.ESecond = end_second;
    m_RadarDataHead->ObservationInfo.ETenth = m_NewRadarHeader_DUAL->ObservationInfo.Etenth;
    m_RadarDataHead->ObservationInfo.ZBinByte = 0;
    m_RadarDataHead->ObservationInfo.ZStartBin = 0;
    m_RadarDataHead->ObservationInfo.VBinByte = 0;
    m_RadarDataHead->ObservationInfo.VStartBin = 0;
    m_RadarDataHead->ObservationInfo.WBinByte = 0;
    m_RadarDataHead->ObservationInfo.WStartBin = 0;

    // PerformanceInfo
    m_RadarDataHead->PerformanceInfo.AntennaG = m_NewRadarHeader_DUAL->PerformanceInfo.AntennaG;
    m_RadarDataHead->PerformanceInfo.VerBeamW = m_NewRadarHeader_DUAL->PerformanceInfo.BeamH;
    m_RadarDataHead->PerformanceInfo.HorBeamW = m_NewRadarHeader_DUAL->PerformanceInfo.BeamL;
//    qDebug() << "PerformanceInfo.BeamH = " << m_radarHeader784DUAL.PerformanceInfo.BeamH;
//    qDebug() << "PerformanceInfo.BeamL = " << m_radarHeader784DUAL.PerformanceInfo.BeamL;
    m_RadarDataHead->PerformanceInfo.Polarizations = m_NewRadarHeader_DUAL->PerformanceInfo.polarizations;
//    qDebug() << "PerformanceInfo.polarizations = " << m_radarHeader784DUAL.PerformanceInfo.polarizations;
    m_RadarDataHead->PerformanceInfo.SideLobe = m_NewRadarHeader_DUAL->PerformanceInfo.sidelobe;
//    h.PerformanceInfo.SideLobe = m_radarHeader784DUAL.PerformanceInfo.sidelobe * 100;
    m_RadarDataHead->PerformanceInfo.Power = m_NewRadarHeader_DUAL->PerformanceInfo.Power;
    m_RadarDataHead->PerformanceInfo.WaveLength = m_NewRadarHeader_DUAL->PerformanceInfo.wavelength;
//    h.PerformanceInfo.WaveLength = m_radarHeader784DUAL.PerformanceInfo.wavelength * 100;
    m_RadarDataHead->PerformanceInfo.LogA = m_NewRadarHeader_DUAL->PerformanceInfo.logA;
    m_RadarDataHead->PerformanceInfo.LineA = m_NewRadarHeader_DUAL->PerformanceInfo.LineA;
    m_RadarDataHead->PerformanceInfo.AGCP = m_NewRadarHeader_DUAL->PerformanceInfo.AGCP;
    m_RadarDataHead->PerformanceInfo.LogMinPower = 0;
    m_RadarDataHead->PerformanceInfo.LineMinPower = 0;
    m_RadarDataHead->PerformanceInfo.ClutterT = m_NewRadarHeader_DUAL->PerformanceInfo.clutterT;
    m_RadarDataHead->PerformanceInfo.VelocityP = m_NewRadarHeader_DUAL->PerformanceInfo.VelocityP;
    m_RadarDataHead->PerformanceInfo.FilterP = m_NewRadarHeader_DUAL->PerformanceInfo.filderP;
    m_RadarDataHead->PerformanceInfo.NoiseT = m_NewRadarHeader_DUAL->PerformanceInfo.noiseT;
    m_RadarDataHead->PerformanceInfo.SQIT = m_NewRadarHeader_DUAL->PerformanceInfo.SQIT;
    m_RadarDataHead->PerformanceInfo.IntensityC = m_NewRadarHeader_DUAL->PerformanceInfo.intensityC;
    m_RadarDataHead->PerformanceInfo.IntensityR = m_NewRadarHeader_DUAL->PerformanceInfo.intensityR;
}

void CNrietFileIO::convertSiChuangHeaderToNewVTB()
{
    // PTB20240528080843.019
    unsigned short end_year = static_cast<unsigned short>(QString::fromStdString(m_fileTime).mid(0, 4).toUInt());
    // 提取月份并转换为unsigned char
    unsigned char end_month = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(4, 2).toUInt());
    // 提取日期并转换为unsigned char
    unsigned char end_day = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(6, 2).toUInt());
    // 提取小时并转换为unsigned char
    unsigned char end_hour = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(8, 2).toUInt());
    // 提取分钟并转换为unsigned char
    unsigned char end_minute = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(10, 2).toUInt());
    // 提取秒数并转换为unsigned char
    unsigned char end_second = static_cast<unsigned char>(QString::fromStdString(m_fileTime).mid(12, 2).toUInt());

    //构造VTB文件头
    m_RadarDataHead = new RadarDataHead();
    memset(m_RadarDataHead, 0, sizeof(RadarDataHead));
    strcpy(m_RadarDataHead->FileID, "RD");
    m_RadarDataHead->VersionNo = -2.5f;
    m_RadarDataHead->FileHeaderLength = sizeof(RadarDataHead);


    // siteinfo
    strcpy(m_RadarDataHead->SiteInfo.Country, m_RadarHeader720A->SiteInfo.sCountry);
    strcpy(m_RadarDataHead->SiteInfo.Province, m_RadarHeader720A->SiteInfo.sProvince);
    strcpy(m_RadarDataHead->SiteInfo.Station, m_RadarHeader720A->SiteInfo.sStation);
    strcpy(m_RadarDataHead->SiteInfo.StationNumber, m_RadarHeader720A->SiteInfo.sStationNumber);
//    qDebug() << "m_RadarHeader720A->SiteInfo.sStation = " << m_RadarHeader720A->SiteInfo.sStation << endl;
//    qDebug() << "m_RadarHeader720A->SiteInfo.sStationNumber = " << m_RadarHeader720A->SiteInfo.sStationNumber << endl;
    strcpy(m_RadarDataHead->SiteInfo.RadarType, m_RadarHeader720A->SiteInfo.sRadarType);
//    qDebug() << "m_RadarHeader720A->SiteInfo.sRadarType = " << m_RadarHeader720A->SiteInfo.sRadarType << endl;
    strcpy(m_RadarDataHead->SiteInfo.Longitude, m_RadarHeader720A->SiteInfo.sLongitude);
    strcpy(m_RadarDataHead->SiteInfo.Latitude, m_RadarHeader720A->SiteInfo.sLatitude);
    if (m_RadarHeader720A->SiteInfo.lLatitudeValue == 307994 && m_RadarHeader720A->SiteInfo.lLongitudeValue == 1118116) // 当阳
    {
        m_RadarDataHead->SiteInfo.LatitudeValue = m_RadarHeader720A->SiteInfo.lLatitudeValue / 10.;
        m_RadarDataHead->SiteInfo.LongitudeValue = m_RadarHeader720A->SiteInfo.lLongitudeValue / 10.;
    }
    else
    {
        m_RadarDataHead->SiteInfo.LatitudeValue = m_RadarHeader720A->SiteInfo.lLatitudeValue;
        m_RadarDataHead->SiteInfo.LongitudeValue = m_RadarHeader720A->SiteInfo.lLongitudeValue;
    }

//    qDebug() << "lantitudevalue = " << m_RadarDataHead->SiteInfo.LatitudeValue;
//    qDebug() << "longitudevalue = " << m_RadarDataHead->SiteInfo.LongitudeValue;

    m_RadarDataHead->SiteInfo.Height = m_RadarHeader720A->SiteInfo.lHeight;
    m_RadarDataHead->SiteInfo.MaxAngle = m_RadarHeader720A->SiteInfo.shMaxAngle;
    m_RadarDataHead->SiteInfo.OptiAngle = m_RadarHeader720A->SiteInfo.shOptiAngle;


    // observationinfo
    m_RadarDataHead->ObservationInfo.SType = m_RadarHeader720A->ObservationInfo.ucType;
//    qDebug() << "SType = " << m_RadarDataHead->ObservationInfo.SType;
    m_RadarDataHead->ObservationInfo.SYear = m_RadarHeader720A->ObservationInfo.usSYear;
    m_RadarDataHead->ObservationInfo.SMonth = m_RadarHeader720A->ObservationInfo.ucSMonth;
    m_RadarDataHead->ObservationInfo.SDay = m_RadarHeader720A->ObservationInfo.ucSDay;
    m_RadarDataHead->ObservationInfo.SHour = m_RadarHeader720A->ObservationInfo.ucSHour;
    m_RadarDataHead->ObservationInfo.SMinute = m_RadarHeader720A->ObservationInfo.ucSMinute;
    m_RadarDataHead->ObservationInfo.SSecond = m_RadarHeader720A->ObservationInfo.ucSSecond;
    m_RadarDataHead->ObservationInfo.TimeP = m_RadarHeader720A->ObservationInfo.ucTimeP;
    m_RadarDataHead->ObservationInfo.SMillisecond = m_RadarHeader720A->ObservationInfo.ulSMillisecond;
    m_RadarDataHead->ObservationInfo.Calibration = m_RadarHeader720A->ObservationInfo.ucCalibration;
    m_RadarDataHead->ObservationInfo.IntensityI = m_RadarHeader720A->ObservationInfo.ucIntensityI;
    m_RadarDataHead->ObservationInfo.VelocityP = m_RadarHeader720A->ObservationInfo.ucVelocityP;
    m_RadarDataHead->ObservationInfo.ZStartBin = m_RadarHeader720A->ObservationInfo.usZStartBin;
    m_RadarDataHead->ObservationInfo.VStartBin = m_RadarHeader720A->ObservationInfo.usVStartBin;
    m_RadarDataHead->ObservationInfo.WStartBin = m_RadarHeader720A->ObservationInfo.usWStartBin;

    for (int i = 0; i < m_nLayerNum; i++)
    {
        m_RadarDataHead->ObservationInfo.LayerInfo[i].Ambiguousp = m_RadarHeader720A->ObservationInfo.LayerInfo[i].ucAmbiguousP;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DBegin = m_RadarHeader720A->ObservationInfo.LayerInfo[i].ulDataBegin;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DataForm = m_RadarHeader720A->ObservationInfo.LayerInfo[i].cDataForm;
//        h.ObservationInfo.LayerInfo[i].DataForm = 24;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DataType = 8;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxL = m_RadarHeader720A->ObservationInfo.LayerInfo[i].usMaxL;
//        qDebug() << "MaxL =" << m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxL;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxV = m_RadarHeader720A->ObservationInfo.LayerInfo[i].usMaxV;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].PRF1 = m_RadarHeader720A->ObservationInfo.LayerInfo[i].usPRF1;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].PRF2 = m_RadarHeader720A->ObservationInfo.LayerInfo[i].usPRF2;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].PluseW = m_RadarHeader720A->ObservationInfo.LayerInfo[i].usPulseWidth;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].RecordNumber = m_RadarHeader720A->ObservationInfo.LayerInfo[i].usRecordNumber;
//        qDebug() << "RecordNumber =" << m_RadarDataHead->ObservationInfo.LayerInfo[i].RecordNumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].DPbinNumber = m_RadarHeader720A->ObservationInfo.LayerInfo[i].usSpeed;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].SwpAngles = m_RadarHeader720A->ObservationInfo.LayerInfo[i].sSwpAngle;
//        qDebug() << "SwpAngles = " << m_RadarDataHead->ObservationInfo.LayerInfo[i].SwpAngles;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].VbinNumber = m_RadarHeader720A->ObservationInfo.LayerInfo[i].usVBinNumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].VBinWidth = m_RadarHeader720A->ObservationInfo.LayerInfo[i].usVBinWidth;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].WbinNumber = m_RadarHeader720A->ObservationInfo.LayerInfo[i].usWBinNumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].WBinWidth = m_RadarHeader720A->ObservationInfo.LayerInfo[i].usWBinWidth;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber = m_RadarHeader720A->ObservationInfo.LayerInfo[i].usZBinNumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i].ZBinWidth = m_RadarHeader720A->ObservationInfo.LayerInfo[i].usZBinWidth;
//        qDebug() << "usZBinNumber =" << m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber;
//        qDebug() << "usZBinWidth =" << m_RadarDataHead->ObservationInfo.LayerInfo[i].ZBinWidth;
    }

    m_RadarDataHead->ObservationInfo.RHIA = m_RadarHeader720A->ObservationInfo.usRHIA;
    m_RadarDataHead->ObservationInfo.RHIL = m_RadarHeader720A->ObservationInfo.sRHIL;
    m_RadarDataHead->ObservationInfo.RHIH = m_RadarHeader720A->ObservationInfo.sRHIH;
//    qDebug() << "RHIA = " << m_RadarDataHead->ObservationInfo.RHIA;
//    qDebug() << "RHIL = " << m_RadarDataHead->ObservationInfo.RHIL;
//    qDebug() << "RHIH = " << m_RadarDataHead->ObservationInfo.RHIH;
//    m_RadarDataHead->ObservationInfo.EYear = m_RadarHeader720A->ObservationInfo.usEYear;
//    m_RadarDataHead->ObservationInfo.EMonth = m_RadarHeader720A->ObservationInfo.ucEMonth;
//    m_RadarDataHead->ObservationInfo.EDay = m_RadarHeader720A->ObservationInfo.ucEDay;
//    m_RadarDataHead->ObservationInfo.EHour = m_RadarHeader720A->ObservationInfo.ucEHour;
//    m_RadarDataHead->ObservationInfo.EMinute = m_RadarHeader720A->ObservationInfo.ucEMinute;
//    m_RadarDataHead->ObservationInfo.ESecond = m_RadarHeader720A->ObservationInfo.ucESecond;
    m_RadarDataHead->ObservationInfo.EYear = end_year;
    m_RadarDataHead->ObservationInfo.EMonth = end_month;
    m_RadarDataHead->ObservationInfo.EDay = end_day;
    m_RadarDataHead->ObservationInfo.EHour = end_hour;
    m_RadarDataHead->ObservationInfo.EMinute = end_minute;
    m_RadarDataHead->ObservationInfo.ESecond = end_second;
    m_RadarDataHead->ObservationInfo.ETenth = m_RadarHeader720A->ObservationInfo.ucETenth;
    m_RadarDataHead->ObservationInfo.ZBinByte = m_RadarHeader720A->ObservationInfo.usZBinByte;
//    h.ObservationInfo.BinRange1 = m_radarHeader720A.ObservationInfo.BinRange1;
    m_RadarDataHead->ObservationInfo.VBinByte = m_RadarHeader720A->ObservationInfo.usVBinByte;
    //fileHead.ObservationInfo.BinRange2 = m_radarHeader720A.ObservationInfo.BinRange2;
    m_RadarDataHead->ObservationInfo.WBinByte = m_RadarHeader720A->ObservationInfo.usWBinByte;
    //fileHead.ObservationInfo.BinRange3 = m_radarHeader720A.ObservationInfo.BinRange3;


    // PerformanceInfo
    m_RadarDataHead->PerformanceInfo.AntennaG = m_RadarHeader720A->PerformanceInfo.lAntennaG;
    m_RadarDataHead->PerformanceInfo.VerBeamW = m_RadarHeader720A->PerformanceInfo.usBeamH;
    m_RadarDataHead->PerformanceInfo.HorBeamW = m_RadarHeader720A->PerformanceInfo.usBeamL;
//    qDebug() << "usBeamL =" << m_radarHeader720A.PerformanceInfo.usBeamL;
    m_RadarDataHead->PerformanceInfo.Polarizations = m_RadarHeader720A->PerformanceInfo.ucPolarization;
    m_RadarDataHead->PerformanceInfo.SideLobe = m_RadarHeader720A->PerformanceInfo.usSidelobe;
    m_RadarDataHead->PerformanceInfo.Power = m_RadarHeader720A->PerformanceInfo.lPower;
    m_RadarDataHead->PerformanceInfo.WaveLength = m_RadarHeader720A->PerformanceInfo.lWavelength;
    m_RadarDataHead->PerformanceInfo.LogA = m_RadarHeader720A->PerformanceInfo.usLogA;
    m_RadarDataHead->PerformanceInfo.LineA = m_RadarHeader720A->PerformanceInfo.usLineA;
    m_RadarDataHead->PerformanceInfo.AGCP = m_RadarHeader720A->PerformanceInfo.usAGCP;
    m_RadarDataHead->PerformanceInfo.LogMinPower = m_RadarHeader720A->PerformanceInfo.usLogMinPower;
    m_RadarDataHead->PerformanceInfo.LineMinPower = m_RadarHeader720A->PerformanceInfo.usLineMinPower;
    m_RadarDataHead->PerformanceInfo.ClutterT = m_RadarHeader720A->PerformanceInfo.ucClutterT;
    m_RadarDataHead->PerformanceInfo.VelocityP = m_RadarHeader720A->PerformanceInfo.ucVelocityP;
    m_RadarDataHead->PerformanceInfo.FilterP = m_RadarHeader720A->PerformanceInfo.ucFilterP;
    m_RadarDataHead->PerformanceInfo.NoiseT = m_RadarHeader720A->PerformanceInfo.ucNoiseT;
    m_RadarDataHead->PerformanceInfo.SQIT = m_RadarHeader720A->PerformanceInfo.ucSQIT;
    m_RadarDataHead->PerformanceInfo.IntensityC = m_RadarHeader720A->PerformanceInfo.ucIntensityC;
    m_RadarDataHead->PerformanceInfo.IntensityR = m_RadarHeader720A->PerformanceInfo.ucIntensityR;


    // test station info
//    qDebug() << "LatitudeValue = " << m_RadarDataHead->SiteInfo.LatitudeValue << endl;
//    qDebug() << "LongitudeValue = " << m_RadarDataHead->SiteInfo.LongitudeValue << endl;
//    qDebug() << "Height = " << m_RadarDataHead->SiteInfo.Height << endl;
//    qDebug() << "sStationNumber = " << m_RadarHeader720A->SiteInfo.sStationNumber << endl;
//    qDebug() << "sRadarType = " << m_RadarHeader720A->SiteInfo.sRadarType << endl;
//    for (int i = 0; i < m_nLayerNum; i++)
//    {
//        qDebug() << "MaxL =" << m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxL;
//    }
}

void CNrietFileIO::Get_nNumSum_784_NewDual()
{
    m_nRadialNumSum = 0;
    m_nLayerNum = m_NewRadarHeader_NEWDUAL->ObservationInfo.sType;
    if (m_nLayerNum > 100)
    {
        m_nLayerNum -= 100;
        for (int i = 0; i < m_nLayerNum; i++)
        {
            m_nRadialNumSum += m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[i].recordnumber;
        }
        //m_nRadialNum = m_RadarDataHead->ObservationInfo.LayerInfo[0].RecordNumber;
    }
    else if (m_nLayerNum == 10 || m_nLayerNum == 1 || m_nLayerNum == 20)
    {
        m_nLayerNum = 1;
        m_nRadialNumSum = m_NewRadarHeader_NEWDUAL->ObservationInfo.LayerParam[0].recordnumber;
    }

    return;
}

void CNrietFileIO::Get_nNumSum_720ADP()
{
    m_nRadialNumSum = 0;
    m_nLayerNum = m_radarHeaderNewDP->ObservationInfo.sType;
    if (m_nLayerNum > 100)
    {
        m_nLayerNum -= 100;
        for (int i = 0; i < m_nLayerNum; i++)
        {
            m_nRadialNumSum += m_radarHeaderNewDP->ObservationInfo.LayerParam[i].recordnumber;
        }
        //m_nRadialNum = m_RadarDataHead->ObservationInfo.LayerInfo[0].RecordNumber;
    }
    else if (m_nLayerNum == 10 || m_nLayerNum == 1 || m_nLayerNum == 20)
    {
        m_nLayerNum = 1;
        m_nRadialNumSum = m_radarHeaderNewDP->ObservationInfo.LayerParam[0].recordnumber;
    }

    return;
}

void CNrietFileIO::Get_nNumSum_784_Dual()
{
    m_nRadialNumSum = 0;
    m_nLayerNum = m_NewRadarHeader_DUAL->ObservationInfo.stype;
//            m_RadarHeader720A->ObservationInfo.ucType;
    if (m_nLayerNum > 100)
    {
        m_nLayerNum -= 100;
        for (int i = 0; i < m_nLayerNum; i++)
        {
            m_nRadialNumSum += m_NewRadarHeader_DUAL->ObservationInfo.LayerParam[i].recordnumber;
        }
        //m_nRadialNum = m_RadarDataHead->ObservationInfo.LayerInfo[0].RecordNumber;
    }
    else if (m_nLayerNum == 10 || m_nLayerNum == 1 || m_nLayerNum == 20)
    {
        m_nLayerNum = 1;
        m_nRadialNumSum = m_NewRadarHeader_DUAL->ObservationInfo.LayerParam[0].recordnumber;
    }

    return;
}

void CNrietFileIO::Get_nNumSum_720A()
{
    m_nRadialNumSum = 0;
    m_nLayerNum = m_RadarHeader720A->ObservationInfo.ucType;
    if (m_nLayerNum > 100)
    {
        m_nLayerNum -= 100;
        for (int i = 0; i < m_nLayerNum; i++)
        {
            m_nRadialNumSum += m_RadarHeader720A->ObservationInfo.LayerInfo[i].usRecordNumber;
        }
        //m_nRadialNum = m_RadarDataHead->ObservationInfo.LayerInfo[0].RecordNumber;
    }
    else if (m_nLayerNum == 10 || m_nLayerNum == 1 || m_nLayerNum == 20)
    {
        m_nLayerNum = 1;
        m_nRadialNumSum = m_RadarHeader720A->ObservationInfo.LayerInfo[0].usRecordNumber;
    }

    return;
}

bool CNrietFileIO::LoadInternalVTB_SBand_PhasedArray(char *fileName)
{
    gzFile l_File;
    int gz_status = 0;
    l_File = gzopen(fileName, "rb");
    if (l_File == nullptr)
    {
        cout << "Source file open error." << endl;
        return false;
    }

    if (m_RadarDataHead_SBand != nullptr)
    {
        delete m_RadarDataHead_SBand;
        m_RadarDataHead_SBand = nullptr;
    }

    m_RadarDataHead_SBand = new RadarDataHead_SBADN_PHASEDARRAY();

    gz_status = gzread(l_File, m_RadarDataHead_SBand, sizeof(RadarDataHead_SBADN_PHASEDARRAY));
    if (gz_status != sizeof(RadarDataHead_SBADN_PHASEDARRAY))
    {
        if (m_RadarDataHead_SBand)
        {
            delete m_RadarDataHead_SBand;
            m_RadarDataHead_SBand = nullptr;
        }
        gzclose(l_File);
        return false;
    }
    if ((m_RadarDataHead_SBand->FileID[0] != 'R') || (m_RadarDataHead_SBand->FileID[1] != 'D') || (m_RadarDataHead_SBand->FileHeaderLength != 36329))
    {
        cout << "file ID or file header length check fail" << endl;
        if (m_RadarDataHead_SBand)
        {
            delete m_RadarDataHead_SBand;
            m_RadarDataHead_SBand = nullptr;
        }
        gzclose(l_File);
        return false;
    }

    m_nRadialNumSum = 0;
    m_nLayerNum = m_RadarDataHead_SBand->ObservationInfo.SType;
    if (m_nLayerNum > 100)
    {
        m_nLayerNum -= 100;
        for (int i = 0; i < m_nLayerNum; i++)
        {
            m_nRadialNumSum += m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i].RecordNumber;
        }
    }

    m_pLineData = new NewLineDataBlock[m_nRadialNumSum];

    int i_Radial = 0;
    for (int i = 0; i < m_nLayerNum; i++)
    {
        int varNum  = (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i].VarNum;
        int zBinNum = m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i].ZbinNumber;
        int vBinNum = m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i].VbinNumber;

        for (int j = 0; j < m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i].RecordNumber; j++)
        {
            gz_status = gzread(l_File, &m_pLineData[i_Radial].LineDataInfo, sizeof(LINEDATAINFO));
            if (gz_status != sizeof(LINEDATAINFO))
            {
                delete m_RadarDataHead_SBand;
                m_RadarDataHead_SBand = nullptr;
                delete[] m_pLineData;
                m_pLineData = nullptr;
                gzclose(l_File);
                return false;
            }

            for (int i_var = 0; i_var < varNum; i_var++)
            {
                int i_type = (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i].VarType[i_var];
                // 1:CorZ 2:V 3:W 4:UnZ 5:ZDR 6:PHDP 7:KDP 8:ROHV 9:LDR 10:SNR
                switch (i_type)
                {
                    case 1:
                        if (m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                        {
                            gz_status = gzread(l_File, &m_pLineData[i_Radial].CorZ, zBinNum * sizeof(short));
                            if (gz_status != zBinNum * sizeof(short))
                            {
                                delete m_RadarDataHead_SBand;
                                m_RadarDataHead_SBand = nullptr;
                                delete[] m_pLineData;
                                m_pLineData = nullptr;
                                gzclose(l_File);
                                return false;
                            }
                        }
                        break;
                    case 2:
                        if (m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i].VbinNumber != 0)
                        {
                            gz_status = gzread(l_File, &m_pLineData[i_Radial].V, vBinNum * sizeof(short));
                            if (gz_status != vBinNum * sizeof(short))
                            {
                                delete m_RadarDataHead_SBand;
                                m_RadarDataHead_SBand = nullptr;
                                delete[] m_pLineData;
                                m_pLineData = nullptr;
                                gzclose(l_File);
                                return false;
                            }
                        }
                        break;
                    case 3:
                        if (m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i].VbinNumber != 0)
                        {
                            gz_status = gzread(l_File, &m_pLineData[i_Radial].W, vBinNum * sizeof(short));
                            if (gz_status != vBinNum * sizeof(short))
                            {
                                delete m_RadarDataHead_SBand;
                                m_RadarDataHead_SBand = nullptr;
                                delete[] m_pLineData;
                                m_pLineData = nullptr;
                                gzclose(l_File);
                                return false;
                            }
                        }
                        break;
                    case 4:
                        if (m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                        {
                            gz_status = gzread(l_File, &m_pLineData[i_Radial].UnZ, zBinNum * sizeof(short));
                            if (gz_status != zBinNum * sizeof(short))
                            {
                                delete m_RadarDataHead_SBand;
                                m_RadarDataHead_SBand = nullptr;
                                delete[] m_pLineData;
                                m_pLineData = nullptr;
                                gzclose(l_File);
                                return false;
                            }
                        }
                        break;
                    case 5:
                        if (m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                        {
                            gz_status = gzread(l_File, &m_pLineData[i_Radial].ZDR, zBinNum * sizeof(short));
                            if (gz_status != zBinNum * sizeof(short))
                            {
                                delete m_RadarDataHead_SBand;
                                m_RadarDataHead_SBand = nullptr;
                                delete[] m_pLineData;
                                m_pLineData = nullptr;
                                gzclose(l_File);
                                return false;
                            }
                        }
                        break;
                    case 6:
                        if (m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                        {
                            gz_status = gzread(l_File, &m_pLineData[i_Radial].PHDP, zBinNum * sizeof(short));
                            if (gz_status != zBinNum * sizeof(short))
                            {
                                delete m_RadarDataHead_SBand;
                                m_RadarDataHead_SBand = nullptr;
                                delete[] m_pLineData;
                                m_pLineData = nullptr;
                                gzclose(l_File);
                                return false;
                            }
                        }
                        break;
                    case 7:
                        if (m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                        {
                            gz_status = gzread(l_File, &m_pLineData[i_Radial].KDP, zBinNum * sizeof(short));
                            if (gz_status != zBinNum * sizeof(short))
                            {
                                delete m_RadarDataHead_SBand;
                                m_RadarDataHead_SBand = nullptr;
                                delete[] m_pLineData;
                                m_pLineData = nullptr;
                                gzclose(l_File);
                                return false;
                            }
                        }
                        break;
                    case 8:
                        if (m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                        {
                            gz_status = gzread(l_File, &m_pLineData[i_Radial].ROHV, zBinNum * sizeof(short));
                            if (gz_status != zBinNum * sizeof(short))
                            {
                                delete m_RadarDataHead_SBand;
                                m_RadarDataHead_SBand = nullptr;
                                delete[] m_pLineData;
                                m_pLineData = nullptr;
                                gzclose(l_File);
                                return false;
                            }
                        }
                        break;
                    case 9:
                        if (m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                        {
                            gz_status = gzread(l_File, &m_pLineData[i_Radial].LDR, zBinNum * sizeof(short));
                            if (gz_status != zBinNum * sizeof(short))
                            {
                                delete m_RadarDataHead_SBand;
                                m_RadarDataHead_SBand = nullptr;
                                delete[] m_pLineData;
                                m_pLineData = nullptr;
                                gzclose(l_File);
                                return false;
                            }
                        }
                        break;
                    case 10:
                        if (m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                        {
                            gz_status = gzread(l_File, &m_pLineData[i_Radial].SNRH, zBinNum * sizeof(short));
                            if (gz_status != zBinNum * sizeof(short))
                            {
                                delete m_RadarDataHead_SBand;
                                m_RadarDataHead_SBand = nullptr;
                                delete[] m_pLineData;
                                m_pLineData = nullptr;
                                gzclose(l_File);
                                return false;
                            }
                        }
                        break;
                    default:
                        break;
                }
            }
            i_Radial++;
        }
    }

    gzclose(l_File);
    return true;
}

bool CNrietFileIO::LoadPhasedArrayInternalVTB(char *fileName)
{
    gzFile l_File;
    int gz_status = 0;
    l_File = gzopen(fileName, "rb");
    if (l_File == nullptr)
    {
        cout << "Source file open error." << endl;
        return false;
    }

    m_RadarDataHead = new RadarDataHead();

    gz_status = gzread(l_File, m_RadarDataHead, sizeof(RadarDataHead));
    if (gz_status != sizeof(RadarDataHead))
    {
        if (m_RadarDataHead)
        {
            delete m_RadarDataHead;
            m_RadarDataHead = nullptr;
        }
        gzclose(l_File);
        return false;
    }
    if ((m_RadarDataHead->FileID[0] != 'R') || (m_RadarDataHead->FileID[1] != 'D'))
    {
        if (m_RadarDataHead)
        {
            delete m_RadarDataHead;
            m_RadarDataHead = nullptr;
        }
        gzclose(l_File);
        return false;
    }

    Get_nNumSum();

    m_pLineData = new NewLineDataBlock[m_nRadialNumSum]();

    int i_Radial = 0;
    char tempparam;
    for (int i = 0; i < m_nLayerNum; i++)
    {
        tempparam = m_RadarDataHead->ObservationInfo.LayerInfo[i].DataForm;

        for (int j = 0; j < m_RadarDataHead->ObservationInfo.LayerInfo[i].RecordNumber; j++)
        {
            gz_status = gzread(l_File, &m_pLineData[i_Radial].LineDataInfo, sizeof(LINEDATAINFO));
            if (gz_status != sizeof(LINEDATAINFO))
            {
                delete m_RadarDataHead;
                m_RadarDataHead = nullptr;
                delete[] m_pLineData;
                m_pLineData = nullptr;
                gzclose(l_File);
                return false;
            }

            if (tempparam == 11 || tempparam == 21 || tempparam == 22 || tempparam == 24 || tempparam == 26 || tempparam == 60 || tempparam == 61 || tempparam == 62 || tempparam == 65 || tempparam == 91) //!-------填补ConZ值
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].CorZ, m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short));
                    if (gz_status != m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 12 || tempparam == 21 || tempparam == 23 || tempparam == 24 || tempparam == 26 || tempparam == 60 || tempparam == 65) //!-------填补UnZ值
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].UnZ, m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short));
                    if (gz_status != m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 13 || tempparam == 22 || tempparam == 23 || tempparam == 24 || tempparam == 26 || tempparam == 25 || tempparam == 60 || tempparam == 61 || tempparam == 62 || tempparam == 65 || tempparam == 91) //!-----填补V值
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].VbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].V, m_RadarDataHead->ObservationInfo.LayerInfo[i].VbinNumber * sizeof(short));
                    if (gz_status != m_RadarDataHead->ObservationInfo.LayerInfo[i].VbinNumber * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 14 || tempparam == 22 || tempparam == 23 || tempparam == 24 || tempparam == 26 || tempparam == 25 || tempparam == 60 || tempparam == 61 || tempparam == 62 || tempparam == 65 || tempparam == 91) //!-----填补W值
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].WbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].W, m_RadarDataHead->ObservationInfo.LayerInfo[i].WbinNumber * sizeof(short));
                    if (gz_status != m_RadarDataHead->ObservationInfo.LayerInfo[i].VbinNumber * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 60 || tempparam == 61 || tempparam == 62 || tempparam == 65 || tempparam == 91)  //ZDR
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].ZDR, m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short));
                    if (gz_status != m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 61 || tempparam == 62 || tempparam == 65) //PHDP
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].PHDP, m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short));
                    if (gz_status != m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 61 || tempparam == 62 || tempparam == 65) //KDP
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].KDP, m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short));
                    if (gz_status != m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 61 || tempparam == 62 || tempparam == 65 || tempparam == 91) //ROHV
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].ROHV, m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short));
                    if (gz_status != m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 91) //仅对91——SNRH
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].SNRH, m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short));
                    if (gz_status != m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 91) //仅对91——PHDP
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].PHDP, m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short));
                    if (gz_status != m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 61 || tempparam == 65 || tempparam == 91) //LDRH
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].LDR, m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short));
                    if (gz_status != m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            if (tempparam == 91) //仅对91——UnZ
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, &m_pLineData[i_Radial].UnZ, m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short));
                    if (gz_status != m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber * sizeof(short))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                }
            }
            i_Radial++;
        }
    }

    gzclose(l_File);
    return true;
}

bool CNrietFileIO::LoadMHVTB(char *fileName)
{
    gzFile l_File;
    int gz_status = 0;
    l_File = gzopen(fileName, "rb");
    if (l_File == nullptr)
    {
        cout << "Source file open error." << endl;
        return false;
    }

    m_RadarDataHead = new RadarDataHead();

    gz_status = gzread(l_File, m_RadarDataHead, sizeof(RadarDataHead));
    if (gz_status != sizeof(RadarDataHead))
    {
        if (m_RadarDataHead)
        {
            delete m_RadarDataHead;
            m_RadarDataHead = nullptr;
        }
        gzclose(l_File);
        return false;
    }
    if ((m_RadarDataHead->FileID[0] != 'R') || (m_RadarDataHead->FileID[1] != 'D'))
    {
        cout << "file ID check fail" << endl;
        if (m_RadarDataHead)
        {
            delete m_RadarDataHead;
            m_RadarDataHead = nullptr;
        }
        gzclose(l_File);
        return false;
    }

    Get_nNumSum();

    m_pLineData = new NewLineDataBlock[m_nRadialNumSum];

    vector<MHCLineDataBlock> pLineData_temp;
    pLineData_temp.resize(m_nRadialNumSum);

    int i_Radial = 0;
    char tempparam;

    for (int i = 0; i < m_nLayerNum; i++)
    {
        tempparam = m_RadarDataHead->ObservationInfo.LayerInfo[i].DataForm;
        for (int j = 0; j < m_RadarDataHead->ObservationInfo.LayerInfo[i].RecordNumber; j++)
        {
            gz_status = gzread(l_File, &m_pLineData[i_Radial].LineDataInfo, sizeof(LINEDATAINFO));
            if (gz_status != sizeof(LINEDATAINFO))
            {
                delete m_RadarDataHead;
                m_RadarDataHead = nullptr;
                delete[] m_pLineData;
                m_pLineData = nullptr;
                gzclose(l_File);
                return false;
            }
            short data_temp_i;
            // Jiangsu X     tempparam == 6X    1:CorZ == Z  2:UnZ == T  3:V   4:W    5:ZDR    6:PHDP    7:KDP    8:LDR    9:ROHV
            if (tempparam == 11 || tempparam == 21 || tempparam == 22 || tempparam == 24 || tempparam == 26 || tempparam == 60 || tempparam == 61 || tempparam == 62 || tempparam == 65 || tempparam == 91) //!-------填补ConZ值
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, pLineData_temp.at(i_Radial).CorZ, MHMAXBINDOTS * sizeof(char));
                    if (gz_status != MHMAXBINDOTS * sizeof(char))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                    for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
                    {
                        if (ibin < MHMAXBINDOTS)
                        {
                            if (*(unsigned char *)&pLineData_temp[i_Radial].CorZ[ibin] == 0 || *(unsigned char *)&pLineData_temp[i_Radial].CorZ[ibin] == 255)
                            {
                                data_temp_i = PREFILLVALUE_VTB;
                            }
                            else
                            {
                                data_temp_i = 1.0 * ((*(unsigned char *)&pLineData_temp[i_Radial].CorZ[ibin] - 64.0) / 2) * 100 + 0;
                            }
                        }
                        else
                        {
                            data_temp_i = PREFILLVALUE_VTB;
                        }
                        m_pLineData[i_Radial].CorZ[ibin] = data_temp_i;
                    }
                }
            }
            if (tempparam == 12 || tempparam == 21 || tempparam == 23 || tempparam == 24 || tempparam == 26 || tempparam == 60 || tempparam == 65) //!-------填补UnZ值
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, pLineData_temp.at(i_Radial).UnZ, MHMAXBINDOTS * sizeof(char));
                    if (gz_status != MHMAXBINDOTS * sizeof(char))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                    for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
                    {
                        if (ibin < MHMAXBINDOTS)
                        {
                            if (*(unsigned char *)&pLineData_temp[i_Radial].UnZ[ibin] == 0 || *(unsigned char *)&pLineData_temp[i_Radial].UnZ[ibin] == 255)
                            {
                                data_temp_i = PREFILLVALUE_VTB;
                            }
                            else
                            {
                                data_temp_i = 1.0 * ((*(unsigned char *)&pLineData_temp[i_Radial].UnZ[ibin] - 64.0) / 2) * 100 + 0;
                            }
                        }
                        else
                        {
                            data_temp_i = PREFILLVALUE_VTB;
                        }
                        m_pLineData[i_Radial].UnZ[ibin] = data_temp_i;
                    }
                }
            }
            if (tempparam == 13 || tempparam == 22 || tempparam == 23 || tempparam == 24 || tempparam == 26 || tempparam == 25 || tempparam == 60 || tempparam == 61 || tempparam == 62 || tempparam == 65 || tempparam == 91) //!-----填补V值
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].VbinNumber != 0)
                {
                    gz_status = gzread(l_File, pLineData_temp.at(i_Radial).V, MHMAXBINDOTS * sizeof(char));
                    if (gz_status != MHMAXBINDOTS * sizeof(char))
                    {
                        delete m_RadarDataHead;
                        delete[] m_pLineData;
                        gzclose(l_File);
                        return false;
                    }
                    for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
                    {
                        if (ibin < MHMAXBINDOTS)
                        {
                            if (*(char *)&pLineData_temp[i_Radial].V[ibin] == -128  || *(char *)&pLineData_temp[i_Radial].V[ibin] == 127)
                            {
                                data_temp_i = PREFILLVALUE_VTB;
                            }
                            else
                            {
                                data_temp_i = 1.0 * (*(char *)&pLineData_temp[i_Radial].V[ibin]) * m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxV / 127;
                            }
                        }
                        else
                        {
                            data_temp_i = PREFILLVALUE_VTB;
                        }
                        m_pLineData[i_Radial].V[ibin] = data_temp_i;
                    }
                }
            }
            if (tempparam == 14 || tempparam == 22 || tempparam == 23 || tempparam == 24 || tempparam == 26 || tempparam == 25 || tempparam == 60 || tempparam == 61 || tempparam == 62 || tempparam == 65 || tempparam == 91) //!-----填补W值
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].WbinNumber != 0)
                {
                    gz_status = gzread(l_File, pLineData_temp.at(i_Radial).W, MHMAXBINDOTS * sizeof(char));
                    if (gz_status != MHMAXBINDOTS * sizeof(char))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                    for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
                    {
                        if (ibin < MHMAXBINDOTS)
                        {
                            if (*(unsigned char *)&pLineData_temp[i_Radial].W[ibin] == 0  || *(unsigned char *)&pLineData_temp[i_Radial].W[ibin] == 255)
                            {
                                data_temp_i = PREFILLVALUE_VTB;
                            }
                            else
                            {
                                data_temp_i = 1.0 * (*(unsigned char *)&pLineData_temp[i_Radial].W[ibin]) * m_RadarDataHead->ObservationInfo.LayerInfo[i].MaxV / 512;
                            }
                        }
                        else
                        {
                            data_temp_i = PREFILLVALUE_VTB;
                        }
                        m_pLineData[i_Radial].W[ibin] = data_temp_i;
                    }
                }
            }

            if (tempparam == 60 || tempparam == 61 || tempparam == 62 || tempparam == 65 || tempparam == 91)  //ZDR
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, pLineData_temp.at(i_Radial).ZDR, MHMAXBINDOTS * sizeof(char));
                    if (gz_status != MHMAXBINDOTS * sizeof(char))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                    for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
                    {
                        if (ibin < MHMAXBINDOTS)
                        {
                            if (*(char *)&pLineData_temp[i_Radial].ZDR[ibin] == -128  || *(char *)&pLineData_temp[i_Radial].ZDR[ibin] == 127)
                            {
                                data_temp_i = PREFILLVALUE_VTB;
                            }
                            else
                            {
                                data_temp_i =  1.0 * (*(char *)&pLineData_temp[i_Radial].ZDR[ibin]) * 15 / 127 * 100;
                            }
                        }
                        else
                        {
                            data_temp_i = PREFILLVALUE_VTB;
                        }
                        m_pLineData[i_Radial].ZDR[ibin] = data_temp_i;
                    }
                }
            }
            if (tempparam == 61 || tempparam == 62 || tempparam == 65) //PHDP
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, pLineData_temp.at(i_Radial).PHDP, MHMAXBINDOTS * sizeof(char));
                    if (gz_status != MHMAXBINDOTS * sizeof(char))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                    for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
                    {
                        if (ibin < MHMAXBINDOTS)
                        {
                            if (*(char *)&pLineData_temp[i_Radial].PHDP[ibin] == -128  || *(char *)&pLineData_temp[i_Radial].PHDP[ibin] == 127)
                            {
                                data_temp_i = PREFILLVALUE_VTB;
                            }
                            else
                            {
                                data_temp_i =  1.0 * (*(char *)&pLineData_temp[i_Radial].PHDP[ibin]) * 180 / 127 * 100;
                            }
                        }
                        else
                        {
                            data_temp_i = PREFILLVALUE_VTB;
                        }
                        m_pLineData[i_Radial].PHDP[ibin] = data_temp_i;
                    }
                }
            }
            if (tempparam == 61 || tempparam == 62) //KDP
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, pLineData_temp.at(i_Radial).KDP, MHMAXBINDOTS * sizeof(char));
                    if (gz_status != MHMAXBINDOTS * sizeof(char))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                    for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
                    {
                        if (ibin < MHMAXBINDOTS)
                        {
                            if (*(char *)&pLineData_temp[i_Radial].KDP[ibin] == -128  || *(char *)&pLineData_temp[i_Radial].KDP[ibin] == 127)
                            {
                                data_temp_i = PREFILLVALUE_VTB;
                            }
                            else
                            {
                                data_temp_i =  1.0 * (*(char *)&pLineData_temp[i_Radial].KDP[ibin]) * 10 / 127 * 100;
                            }
                        }
                        else
                        {
                            data_temp_i = PREFILLVALUE_VTB;
                        }
                        m_pLineData[i_Radial].KDP[ibin] = data_temp_i;
                    }
                }
            }
            if (tempparam == 65) //KDP-->SNRH
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, pLineData_temp.at(i_Radial).SNRH, MHMAXBINDOTS * sizeof(char));
                    if (gz_status != MHMAXBINDOTS * sizeof(char))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                    for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
                    {
                        if (ibin < MHMAXBINDOTS)
                        {
                            if (*(unsigned char *)&pLineData_temp[i_Radial].SNRH[ibin] == 0  || *(unsigned char *)&pLineData_temp[i_Radial].SNRH[ibin] == 255)
                            {
                                data_temp_i = PREFILLVALUE_VTB;
                            }
                            else
                            {
                                data_temp_i =  1.0 * ((*(unsigned char *)&pLineData_temp[i_Radial].SNRH[ibin] - 64.0) / 2) * 100 + 0;
                            }
                        }
                        else
                        {
                            data_temp_i = PREFILLVALUE_VTB;
                        }
                        m_pLineData[i_Radial].SNRH[ibin] = data_temp_i;
                    }
                }
            }
            if (tempparam == 61 || tempparam == 62 || tempparam == 91) //ROHV
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, pLineData_temp.at(i_Radial).ROHV, MHMAXBINDOTS * sizeof(char));
                    if (gz_status != MHMAXBINDOTS * sizeof(char))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                    for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
                    {
                        if (ibin < MHMAXBINDOTS)
                        {
                            if (*(char *)&pLineData_temp[i_Radial].ROHV[ibin] == -128  || *(char *)&pLineData_temp[i_Radial].ROHV[ibin] == 127)
                            {
                                data_temp_i = PREFILLVALUE_VTB;
                            }
                            else
                            {
                                data_temp_i =  1.0 * (*(char *)&pLineData_temp[i_Radial].ROHV[ibin]) * 15 / 127 * 1000;
                            }
                        }
                        else
                        {
                            data_temp_i = PREFILLVALUE_VTB;
                        }
                        m_pLineData[i_Radial].ROHV[ibin] = data_temp_i;
                    }
                }
            }

            if (tempparam == 91) //仅对91——SNRH
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, pLineData_temp.at(i_Radial).SNRH, MHMAXBINDOTS * sizeof(char));
                    if (gz_status != MHMAXBINDOTS * sizeof(char))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                    for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
                    {
                        if (ibin < MHMAXBINDOTS)
                        {
                            if (*(unsigned char *)&pLineData_temp[i_Radial].SNRH[ibin] == 0  || *(unsigned char *)&pLineData_temp[i_Radial].SNRH[ibin] == 255)
                            {
                                data_temp_i = PREFILLVALUE_VTB;
                            }
                            else
                            {
                                data_temp_i = 1.0 * ((*(unsigned char *)&pLineData_temp[i_Radial].SNRH[ibin] - 64.0) / 2) * 100;
                            }
                        }
                        else
                        {
                            data_temp_i = PREFILLVALUE_VTB;
                        }
                        m_pLineData[i_Radial].SNRH[ibin] = data_temp_i;
                    }
                }
            }

            if (tempparam == 91) //仅对91——PHDP
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, pLineData_temp.at(i_Radial).PHDP, MHMAXBINDOTS * sizeof(char));
                    if (gz_status != MHMAXBINDOTS * sizeof(char))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                    for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
                    {
                        if (ibin < MHMAXBINDOTS)
                        {
                            if (*(char *)&pLineData_temp[i_Radial].PHDP[ibin] == -128  || *(char *)&pLineData_temp[i_Radial].PHDP[ibin] == 127)
                            {
                                data_temp_i = PREFILLVALUE_VTB;
                            }
                            else
                            {
                                data_temp_i = 1.0 * (*(char *)&pLineData_temp[i_Radial].PHDP[ibin]) * 180 / 127 * 100;
                            }
                        }
                        else
                        {
                            data_temp_i = PREFILLVALUE_VTB;
                        }
                        m_pLineData[i_Radial].PHDP[ibin] = data_temp_i;
                    }
                }
            }

            if (tempparam == 61 || tempparam == 65 || tempparam == 91) //LDRH
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, pLineData_temp.at(i_Radial).LDR, MHMAXBINDOTS * sizeof(char));
                    if (gz_status != MHMAXBINDOTS * sizeof(char))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                    for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
                    {
                        if (ibin < MHMAXBINDOTS)
                        {
                            if (*(char *)&pLineData_temp[i_Radial].LDR[ibin] == -128  || *(char *)&pLineData_temp[i_Radial].LDR[ibin] == 127)
                            {
                                data_temp_i = PREFILLVALUE_VTB;
                            }
                            else
                            {
                                data_temp_i =  1.0 * (*(char *)&pLineData_temp[i_Radial].LDR[ibin]) * 35 / 127 * 100;
                            }
                        }
                        else
                        {
                            data_temp_i = PREFILLVALUE_VTB;
                        }
                        m_pLineData[i_Radial].LDR[ibin] = data_temp_i;
                    }
                }
            }
            if (tempparam == 65) //ROHV
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, pLineData_temp.at(i_Radial).ROHV, MHMAXBINDOTS * sizeof(char));
                    if (gz_status != MHMAXBINDOTS * sizeof(char))
                    {
                        delete m_RadarDataHead;
                        delete[] m_pLineData;
                        gzclose(l_File);
                        return false;
                    }
                    for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
                    {
                        if (ibin < MHMAXBINDOTS)
                        {
                            if (*(char *)&pLineData_temp[i_Radial].ROHV[ibin] == -128  || *(char *)&pLineData_temp[i_Radial].ROHV[ibin] == 127)
                            {
                                data_temp_i = PREFILLVALUE_VTB;
                            }
                            else
                            {
                                data_temp_i =  1.0 * (*(char *)&pLineData_temp[i_Radial].ROHV[ibin]) * 15 / 127 * 1000;
                            }
                        }
                        else
                        {
                            data_temp_i = PREFILLVALUE_VTB;
                        }
                        m_pLineData[i_Radial].ROHV[ibin] = data_temp_i;
                    }
                }
            }

            if (tempparam == 91) //仅对91——UnZ
            {
                if (m_RadarDataHead->ObservationInfo.LayerInfo[i].ZbinNumber != 0)
                {
                    gz_status = gzread(l_File, pLineData_temp.at(i_Radial).UnZ, MHMAXBINDOTS * sizeof(char));
                    if (gz_status != MHMAXBINDOTS * sizeof(char))
                    {
                        delete m_RadarDataHead;
                        m_RadarDataHead = nullptr;
                        delete[] m_pLineData;
                        m_pLineData = nullptr;
                        gzclose(l_File);
                        return false;
                    }
                    for (int ibin = 0; ibin < MAXBINDOTS; ibin++)
                    {
                        if (ibin < MHMAXBINDOTS)
                        {
                            if (*(unsigned char *)&pLineData_temp[i_Radial].UnZ[ibin] == 0  || *(unsigned char *)&pLineData_temp[i_Radial].UnZ[ibin] == 255)
                            {
                                data_temp_i = PREFILLVALUE_VTB;
                            }
                            else
                            {
                                data_temp_i = 1.0 * ((*(unsigned char *)&pLineData_temp[i_Radial].UnZ[ibin] - 64.0) / 2) * 100;
                            }
                        }
                        else
                        {
                            data_temp_i = PREFILLVALUE_VTB;
                        }
                        m_pLineData[i_Radial].UnZ[ibin] = data_temp_i;
                    }
                }
            }
            i_Radial++;
        }
    }
    gzclose(l_File);
    m_RadarDataHead->OtherInfo.RadarType = 34;

    return true;
}

int CNrietFileIO::ConvertInternalVTBtoStandardFormat_SBand_PhasedArray()
{
    if (!m_RadarData)
    {
        delete m_RadarData;
        m_RadarData = nullptr;
    }
    m_RadarData = new WRADRAWDATA();
    m_RadarHead = &(m_RadarData->commonBlock);

    //----------Common Block----------
    //----Generic Headare----
    m_RadarHead->genericheader.MagicNumber = 0x4D545352;     //固定标志，用来指示雷达数据文件。
    m_RadarHead->genericheader.MajorVersion = 1;             //主版本号
    m_RadarHead->genericheader.MinorVersion = 0;             //次版本号
    m_RadarHead->genericheader.GenericType = 1;              //文件类型，1-基数据文件；2-产品文件
    m_RadarHead->genericheader.ProductType = PREFILLVALUE_INT;   //文件类型为1时不适应
    strncpy(m_RadarHead->genericheader.Reserved, "Reserved", sizeof(m_RadarHead->genericheader.Reserved) - 1); //保留字段

    //----Site Config----
    strncpy(m_RadarHead->siteconfig.SiteCode, m_RadarDataHead_SBand->SiteInfo.StationNumber, sizeof(m_RadarHead->siteconfig.SiteCode) - 1);  //站号具有唯一性，用来区别不同的雷达站
    strncpy(m_RadarHead->siteconfig.SiteName, m_RadarDataHead_SBand->SiteInfo.Station, sizeof(m_RadarHead->siteconfig.SiteName) - 1);        //站点名称，如BeiJing
    m_RadarHead->siteconfig.Latitude = m_RadarDataHead_SBand->SiteInfo.LatitudeValue / 1000.0;  //雷达站天线所在位置纬度，Unit:°
    m_RadarHead->siteconfig.Longitude = m_RadarDataHead_SBand->SiteInfo.LongitudeValue / 1000.0; //雷达站天线所在位置精度，Unit:°
    m_RadarHead->siteconfig.AntennaHeight = m_RadarDataHead_SBand->SiteInfo.Height / 1000.0;    //天线馈源水平时海拔高度，Unit:m
    m_RadarHead->siteconfig.GroundHeight = m_RadarDataHead_SBand->OtherInfo.CenterAltValue / 1000.0; //雷达塔楼地面海拔高度，Unit:m
    //  以下3变量原始数据中为0
    m_RadarHead->siteconfig.Frequency = 299792458.0 / m_RadarDataHead_SBand->PerformanceInfo.WaveLength / 1000.0; //工作频率，Unit:MHz
    m_RadarHead->siteconfig.BeamWidthHori = m_RadarDataHead_SBand->PerformanceInfo.HorBeamW / 100.0;            //水平波束宽度，Unit:°
    m_RadarHead->siteconfig.BeamWidthVert = m_RadarDataHead_SBand->PerformanceInfo.VerBeamW / 100.0;            //垂直波束宽度，Unit:°
    m_RadarHead->siteconfig.RdaVersion = 1;         //RDA版本号
    m_RadarHead->siteconfig.RadarType = RTYPE_SPA;          //雷达类型   1–SA;    2–SB;    3–SC;    4–SAD;    33–CA;    34–CB;    35–CC;    36–CCJ;    37–CD    ;101-X
    strncpy(m_RadarHead->siteconfig.Reserved, "Reserved", sizeof(m_RadarHead->siteconfig.Reserved) - 1); //保留字段
    //----Task Config----
    strncpy(m_RadarHead->taskconfig.TaskName, "VCP", sizeof(m_RadarHead->taskconfig.TaskName) - 1);      //任务名称,如VCP21
    strncpy(m_RadarHead->taskconfig.TaskDescription, "Reserved", sizeof(m_RadarHead->taskconfig.TaskDescription) - 1);  //任务描述
    m_RadarHead->taskconfig.PolarizationType = int(m_RadarDataHead_SBand->PerformanceInfo.Polarizations) + 1;           //极化方式，1-水平极化，2-垂直极化，3-水平/垂直同时，4-水平/垂直交替
    if (m_RadarDataHead_SBand->ObservationInfo.SType == 1)
    {
        m_RadarHead->taskconfig.ScanType = 2;
        m_RadarHead->taskconfig.CutNumber = 1;
    }
    else if (m_RadarDataHead_SBand->ObservationInfo.SType == 10)
    {
        m_RadarHead->taskconfig.ScanType = 1;    //可能为3，当前版本不做判断
        m_RadarHead->taskconfig.CutNumber = 1;
    }
    else if (m_RadarDataHead_SBand->ObservationInfo.SType == 20)
    {
        cout << "Cannot deal with this type" << endl;
        return -1;
    }
    else if (m_RadarDataHead_SBand->ObservationInfo.SType > 100)
    {
        m_RadarHead->taskconfig.ScanType = 0;
        m_RadarHead->taskconfig.CutNumber = m_RadarDataHead_SBand->ObservationInfo.SType - 100;
    }
    m_RadarHead->taskconfig.PulseWidth = int(m_RadarDataHead_SBand->ObservationInfo.LayerInfo[0].PluseW) * 1000;//发射脉冲宽度，Unit:ns 纳秒
    time_t ScanStartTime = time_convert((int)m_RadarDataHead_SBand->ObservationInfo.SYear, (int)m_RadarDataHead_SBand->ObservationInfo.SMonth, (int)m_RadarDataHead_SBand->ObservationInfo.SDay, \
                                        (int)m_RadarDataHead_SBand->ObservationInfo.SHour, (int)m_RadarDataHead_SBand->ObservationInfo.SMinute, (int)m_RadarDataHead_SBand->ObservationInfo.SSecond) \
                           + 28800;
    //cout << ScanStartTime <<endl;//date +%s，从 1970 年 1 月 1 日 00:00:00 UTC 到目前为止的秒数（时间戳）
    m_RadarHead->taskconfig.ScanStartTime = int(ScanStartTime);//扫描开始时间，扫描开始时间为UTC标准时间计数,1970年1月1日0时为起始计数基准点,Unit:s,
    m_RadarHead->taskconfig.HorizontalNoise = PREFILLVALUE_FLOAT;//水平通道的噪声电平,Unit:dBm 分贝毫瓦
    m_RadarHead->taskconfig.VerticalNoise = PREFILLVALUE_FLOAT;//垂直通道的噪声电平,Unit:dBm 分贝毫瓦
    m_RadarHead->taskconfig.HorizontalCalibration = PREFILLVALUE_FLOAT;//水平通道的反射率标定常数,Unit:dB
    m_RadarHead->taskconfig.VerticalCalibration = PREFILLVALUE_FLOAT;//垂直通道的反射率标定常数,Unit:dB
    m_RadarHead->taskconfig.HorizontalNoiseTemperature = PREFILLVALUE_FLOAT;//水平通道噪声温度，Unit:K 开氏温度
    m_RadarHead->taskconfig.VerticalNoiseTemperature = PREFILLVALUE_FLOAT;//垂直通道噪声温度，Unit:K 开氏温度
    m_RadarHead->taskconfig.ZDRCalibration = PREFILLVALUE_FLOAT;//ZDR标定偏差,Unit:dB
    m_RadarHead->taskconfig.PHIDPCalibration = PREFILLVALUE_FLOAT;//差分相移标定偏差，Unit:°
    m_RadarHead->taskconfig.LDRCalibration = PREFILLVALUE_FLOAT;//系统LDR标定偏差,Unit:dB
    strncpy(m_RadarHead->taskconfig.Reserved, "Reserved", sizeof(m_RadarHead->taskconfig.Reserved) - 1); //保留字段
    //----Cut Congig----
    m_RadarHead->cutconfig.resize(m_RadarHead->taskconfig.CutNumber);
    for (int i_cut = 0; i_cut < m_RadarHead->taskconfig.CutNumber; i_cut++)
    {
        m_RadarHead->cutconfig[i_cut].ProcessMode = 3;  //处理模式,1-PPP,2-FFT
        m_RadarHead->cutconfig[i_cut].WaveForm = PREFILLVALUE_INT;
        //波形类别，0 – CS连续监测，1 – CD连续多普勒，2 – CDX多普勒扩展，3 – Rx Test，4 – BATCH批模式，5 – Dual PRF双PRF，6 - Staggered PRT 参差PRT
        m_RadarHead->cutconfig[i_cut].PRF1 = m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].PRF1 / 10; //脉冲重复频率1，对于Batch、双PRF和参差PRT模式，表示高PRF值。对于其它单PRF模式，表示唯一的PRF值。Unit:Hz
        m_RadarHead->cutconfig[i_cut].PRF2 = m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].PRF2 / 10; //脉冲重复频率2，对Batch、双PRF和参差PRT模式，表示低PRF值。对其它单PRF模式，无效。Unit:Hz
        m_RadarHead->cutconfig[i_cut].DealiasingMode = PREFILLVALUE_INT;
        //速度退模糊方法,1–单PRF,2–双PRF3:2模式,3–双PRF4:3模式,4–双PRF 5:4模式
        m_RadarHead->cutconfig[i_cut].Azimuth = m_RadarDataHead_SBand->ObservationInfo.RHIA / 100.0;  //方位角,RHI模式的方位角,Unit:°
        m_RadarHead->cutconfig[i_cut].Elevation = m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].SwpAngles / 100.0; //仰角,PPI模式的俯仰角,Unit:°
        if (m_RadarHead->taskconfig.ScanType == 2)
        {
            m_RadarHead->cutconfig[i_cut].StartAngle = m_RadarDataHead_SBand->ObservationInfo.RHIH / 100.0; //起始角度，PPI扇扫的起始方位角，或RHI模式的高限仰角,Unit:°
            m_RadarHead->cutconfig[i_cut].EndAngle = m_RadarDataHead_SBand->ObservationInfo.RHIL / 100.0; //结束角度，PPI扇扫的结束方位角，或RHI模式的低限仰角,Unit:°
        }
        else
        {
            m_RadarHead->cutconfig[i_cut].StartAngle = PREFILLVALUE_FLOAT;
            m_RadarHead->cutconfig[i_cut].EndAngle = PREFILLVALUE_FLOAT;
        }
        m_RadarHead->cutconfig[i_cut].AngularResolution = 360.0 / m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].RecordNumber; //角度分辨率，径向数据的角度分辨率，仅用于PPI扫描模式,Unit:°
        m_RadarHead->cutconfig[i_cut].ScanSpeed = m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].DPbinNumber / 100.0; //扫描速度，PPI扫描的方位转速，或RHI扫描的俯仰转速，Unit:Deg/sec,度/秒
        m_RadarHead->cutconfig[i_cut].LogResolution = m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZBinWidth / 10.0; //强度分辨率，强度数据的距离分辨率,Unit:m
        m_RadarHead->cutconfig[i_cut].DopplerResolution = m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].VBinWidth / 10.0; //多普勒分辨率,多普勒数据的距离分辨率，Unit:m
        m_RadarHead->cutconfig[i_cut].StartRange = m_RadarDataHead_SBand->ObservationInfo.ZStartBin * m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZBinWidth / 10.0; //起始距离，数据探测起始距离，Unit:m
        m_RadarHead->cutconfig[i_cut].MaximumRange1 = m_RadarHead->cutconfig[i_cut].LogResolution \
            * m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber;  //最大距离1,对应脉冲重复频率1的最大可探测距离，Unit:m
        m_RadarHead->cutconfig[i_cut].MaximumRange2 = m_RadarHead->cutconfig[i_cut].DopplerResolution \
            * m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].VbinNumber;   //最大距离2,对应脉冲重复频率2的最大可探测距离，Unit:m
        m_RadarHead->cutconfig[i_cut].Sample1 = PREFILLVALUE_INT;    //采样个数1，对应于脉冲重复频率1的采样个数
        m_RadarHead->cutconfig[i_cut].Sample2 = PREFILLVALUE_INT;    //采样个数2，对应于脉冲重复频率2的采样个数
        m_RadarHead->cutconfig[i_cut].PhaseMode = PREFILLVALUE_INT;  //相位编码模式，1–固定相位，2–随机相位，3–SZ编码
        m_RadarHead->cutconfig[i_cut].AtmosphericLoss = PREFILLVALUE_FLOAT;    //大气衰减，双程大气衰减值，精度为小数点后保留6位，Unit:dB/km
        m_RadarHead->cutconfig[i_cut].NyquistSpeed = m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].MaxV / 100.0; //最大不模糊速度，理论最大不模糊速度,Unit:m/s
        m_RadarHead->cutconfig[i_cut].MomentsMask = 0;   //数据类型掩码，以掩码的形式表示当前允许获取的数据类型，其中：0–不允许获取数据，1 –允许获取数据，具体掩码定义见表2-6。

//        switch (m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].DataForm) {
//        case 24:
//            m_RadarHead->cutconfig[i_cut].MomentsMask |= (1<<1)|(1<<2)|(1<<3)|(1<<4);
//            break;
//        case 65:
//            m_RadarHead->cutconfig[i_cut].MomentsMask |= (1<<1)|(1<<2)|(1<<3)|(1<<4)|(1<<7)|(1<<8)|(1<<9)|(1<<10)|(1<<11);
//            break;
//        case 91:
//            m_RadarHead->cutconfig[i_cut].MomentsMask |= (1<<1)|(1<<2)|(1<<3)|(1<<4)|(1<<7)|(1<<8)|(1<<9)|(1<<10)|(1<<16);
//            break;
//        default:
//            break;
//        }
//        m_RadarHead->cutconfig[i_cut].MomentsSizeMask = m_RadarHead->cutconfig[i_cut].MomentsMask;    //数据大小掩码，以掩码形式表示每种数据类型字节数，其中：0–1个字节，1–2个字节，具体掩码定义见表2-6。

        m_RadarHead->cutconfig[i_cut].MiscFilterMask = 0; //滤波设置掩码，0–未应用，1–	应用，具体掩码定义见表2-7。
        m_RadarHead->cutconfig[i_cut].SQIThreshold = PREFILLVALUE_FLOAT;
        m_RadarHead->cutconfig[i_cut].SIGThreshold = PREFILLVALUE_FLOAT;
        m_RadarHead->cutconfig[i_cut].CSRThreshold = PREFILLVALUE_FLOAT;
        m_RadarHead->cutconfig[i_cut].LOGThreshold = PREFILLVALUE_FLOAT;
        m_RadarHead->cutconfig[i_cut].CPAThreshold = PREFILLVALUE_FLOAT;
        m_RadarHead->cutconfig[i_cut].PMIThreshold = PREFILLVALUE_FLOAT;
        m_RadarHead->cutconfig[i_cut].DPLOGThreshold = PREFILLVALUE_FLOAT;
        strncpy(m_RadarHead->cutconfig[i_cut].ThresholdsReserved, "", sizeof(m_RadarHead->cutconfig[i_cut].ThresholdsReserved) - 1);
        m_RadarHead->cutconfig[i_cut].dBTMask = 0;
        m_RadarHead->cutconfig[i_cut].dBZMask = 0;
        m_RadarHead->cutconfig[i_cut].VelocityMask = 0;
        m_RadarHead->cutconfig[i_cut].SpectrumWidthMask = 0;
        m_RadarHead->cutconfig[i_cut].DPMask = 0;
        strncpy(m_RadarHead->cutconfig[i_cut].MaskReserved, "", sizeof(m_RadarHead->cutconfig[i_cut].MaskReserved) - 1);
        m_RadarHead->cutconfig[i_cut].ScanSync = PREFILLVALUE_INT;
        m_RadarHead->cutconfig[i_cut].Direction = PREFILLVALUE_INT;
        m_RadarHead->cutconfig[i_cut].GroundClutterClassifierType = PREFILLVALUE_SHORT;
        m_RadarHead->cutconfig[i_cut].GroundClutterFilterType = PREFILLVALUE_SHORT;
        m_RadarHead->cutconfig[i_cut].GroundClutterFilterNotchWidth = PREFILLVALUE_SHORT;
        m_RadarHead->cutconfig[i_cut].GroundClutterFilterWindow = PREFILLVALUE_SHORT;
        strncpy(m_RadarHead->cutconfig[i_cut].Reserved, "Reserved", sizeof(m_RadarHead->cutconfig[i_cut].Reserved) - 1);
    }

    //----------Radial Block----------
    //----Radial Head----
    int m_radial_of_total = 0;
    for (int i_cut = 0; i_cut < m_RadarHead->taskconfig.CutNumber; i_cut++)
    {
        m_radial_of_total += m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].RecordNumber;
    }
    m_RadarData->radials.resize(m_radial_of_total);

    int i_cut = 0;
    int i_radial_of_cut = 0;

    for (int i_radial_of_total = 0; i_radial_of_total < m_radial_of_total; i_radial_of_total++)
    {
        m_RadarData->radials[i_radial_of_total].radialheader.RadialState = 1; //径向数据状态,0–仰角开始，1–中间数据，2–仰角结束，3–体扫开始，4–体扫结束，5–RHI开始，6–RHI结束。
        if (i_radial_of_total == 0)
        {
            if (m_RadarHead->taskconfig.ScanType < 2) //0-体扫，1-单层PPI，2-单层RHI，
            {
                m_RadarData->radials[i_radial_of_total].radialheader.RadialState = 3;
            }
            else if (m_RadarHead->taskconfig.ScanType == 2)
            {
                m_RadarData->radials[i_radial_of_total].radialheader.RadialState = 5;
            }
        }
        else if (i_radial_of_total == m_radial_of_total - 1)
        {
            if (m_RadarHead->taskconfig.ScanType < 2) //0-体扫，1-单层PPI，2-单层RHI，
            {
                m_RadarData->radials[i_radial_of_total].radialheader.RadialState = 4;
            }
            else if (m_RadarHead->taskconfig.ScanType == 2)
            {
                m_RadarData->radials[i_radial_of_total].radialheader.RadialState = 6;
            }
        }
        else if (i_radial_of_cut == 0)
        {
            m_RadarData->radials[i_radial_of_total].radialheader.RadialState = 0;
        }
        else if (i_radial_of_cut == m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].RecordNumber - 1)
        {
            m_RadarData->radials[i_radial_of_total].radialheader.RadialState = 2;
        }

        m_RadarData->radials[i_radial_of_total].radialheader.SpotBlank = 0;   //消隐标志，0-正常，1-消隐
        m_RadarData->radials[i_radial_of_total].radialheader.SequenceNumber = i_radial_of_total + 1; //序号，每个体扫径向从1计数
        m_RadarData->radials[i_radial_of_total].radialheader.RadialNumber = i_radial_of_cut + 1;  //径向数，每个扫描从1计数
        m_RadarData->radials[i_radial_of_total].radialheader.ElevationNumber = i_cut + 1; //仰角编号，每个体扫从1计数
        m_RadarData->radials[i_radial_of_total].radialheader.Azimuth = m_pLineData[i_radial_of_total].LineDataInfo.Az / 100.0; //方位角，扫描的方位角度，Unit:°
        m_RadarData->radials[i_radial_of_total].radialheader.Elevation = m_pLineData[i_radial_of_total].LineDataInfo.Elev / 100.0;   //仰角，扫描的俯仰角度，Unit:°
        time_t RadialTime;
        RadialTime = time_convert((int)m_RadarDataHead_SBand->ObservationInfo.SYear, (int)m_RadarDataHead_SBand->ObservationInfo.SMonth, (int)m_RadarDataHead_SBand->ObservationInfo.SDay, \
                                  (int)m_pLineData[i_radial_of_total].LineDataInfo.Hh, (int)m_pLineData[i_radial_of_total].LineDataInfo.Mm, (int)m_pLineData[i_radial_of_total].LineDataInfo.Ss) \
                     + 28800;
        if (m_RadarDataHead_SBand->ObservationInfo.SHour == 23 && m_pLineData[i_radial_of_total].LineDataInfo.Hh == 00)
        {
            RadialTime += 86400;
        }
        m_RadarData->radials[i_radial_of_total].radialheader.Seconds = int(RadialTime); //秒，径向数据采集的时间，UTC计数的秒数，从1970年1月1日0时开始计数，Unit:s
        m_RadarData->radials[i_radial_of_total].radialheader.Microseconds = m_pLineData[i_radial_of_total].LineDataInfo.Min;  //微妙，径向素数采集的时间出去UTC秒数后，留下的微秒数，Unit:ms

        m_RadarData->radials[i_radial_of_total].radialheader.MomentNumber = m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].VarNum;
        m_RadarData->radials[i_radial_of_total].radialheader.LengthOfData = m_RadarData->radials[i_radial_of_total].radialheader.MomentNumber * sizeof(MOMENTHEADER) + sizeof(RADIALHEADER);
        for (int i_var = 0; i_var < m_RadarData->radials[i_radial_of_total].radialheader.MomentNumber; i_var++)
        {
            int i_type = m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].VarType[i_var];
            // 1:CorZ 2:V 3:W 4:UnZ 5:ZDR 6:PHDP 7:KDP 8:ROHV 9:LDR 10:SNR
            switch (i_type)
            {
                case 1:
                    m_RadarData->radials[i_radial_of_total].radialheader.LengthOfData += m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber * 2;
                    break;
                case 2:
                    m_RadarData->radials[i_radial_of_total].radialheader.LengthOfData += m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].VbinNumber * 2;
                    break;
                case 3:
                    m_RadarData->radials[i_radial_of_total].radialheader.LengthOfData += m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].VbinNumber * 2;
                    break;
                case 4:
                    m_RadarData->radials[i_radial_of_total].radialheader.LengthOfData += m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber * 2;
                    break;
                case 5:
                    m_RadarData->radials[i_radial_of_total].radialheader.LengthOfData += m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber * 2;
                    break;
                case 6:
                    m_RadarData->radials[i_radial_of_total].radialheader.LengthOfData += m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber * 2;
                    break;
                case 7:
                    m_RadarData->radials[i_radial_of_total].radialheader.LengthOfData += m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber * 2;
                    break;
                case 8:
                    m_RadarData->radials[i_radial_of_total].radialheader.LengthOfData += m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber * 2;
                    break;
                case 9:
                    m_RadarData->radials[i_radial_of_total].radialheader.LengthOfData += m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber * 2;
                    break;
                case 10:
                    m_RadarData->radials[i_radial_of_total].radialheader.LengthOfData += m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber * 2;
                    break;
                default:
                    break;
            }
        }
        strncpy(m_RadarData->radials[i_radial_of_total].radialheader.Reserved, "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].radialheader.Reserved) - 1); //保留字段

        //----Moment Block----
        m_RadarData->radials[i_radial_of_total].momentblock.resize(m_RadarData->radials[i_radial_of_total].radialheader.MomentNumber);
        for (int i_var = 0; i_var < m_RadarData->radials[i_radial_of_total].radialheader.MomentNumber; i_var++)
        {
            int i_type = m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].VarType[i_var];
            // 1:CorZ 2:V 3:W 4:UnZ 5:ZDR 6:PHDP 7:KDP 8:ROHV 10:SNR
            switch (i_type)
            {
                case 1:
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.DataType = 2;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale = 100;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset = 10000;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Flags = PREFILLVALUE_SHORT;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length = \
                        m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength \
                        * m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber;                                 //距离库数据的长度，Unit:Bytes
                    strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved, \
                            "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved) - 1); //保留字段
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentdata.\
                    resize(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length);
                    for (int i = 0; i < m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber; i++)
                    {
                        if (m_pLineData[i_radial_of_total].CorZ[i] != PREFILLVALUE_VTB)
                        {
                            float tmp = (m_pLineData[i_radial_of_total].CorZ[i] - (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Offset[i_var]) * 1.0 / (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Scale[i_var];
                            if (tmp * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale + m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset < 0)
                            {
                                *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                        = (unsigned short) INVALID_BT;
                            }
                            else
                            {
                                *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                        = (unsigned short)(tmp * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale + m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset) ;
                            }

                        }
                        else
                        {
                            *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                    = (unsigned short) INVALID_BT;
                        }
                    }
                    break;
                case 2:
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.DataType = 3;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale = 100;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset = 15000;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Flags = PREFILLVALUE_SHORT;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length = \
                        m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength \
                        * m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].VbinNumber;                                 //距离库数据的长度，Unit:Bytes
                    strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved, \
                            "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved) - 1); //保留字段
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentdata.\
                    resize(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length);
                    for (int i = 0; i < m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].VbinNumber; i++)
                    {
                        if (m_pLineData[i_radial_of_total].V[i] != PREFILLVALUE_VTB)
                        {
                            float tmp = (m_pLineData[i_radial_of_total].V[i] - (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Offset[i_var]) * 1.0 / (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Scale[i_var];
                            *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                    = (unsigned short)(tmp * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale + m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset);
                        }
                        else
                        {
                            *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                    = (unsigned short) INVALID_BT;
                        }
                    }
                    break;
                case 3:
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.DataType = 4;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale = 100;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset = 10000;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Flags = PREFILLVALUE_SHORT;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length = \
                        m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength \
                        * m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].VbinNumber;                                 //距离库数据的长度，Unit:Bytes
                    strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved, \
                            "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved) - 1); //保留字段
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentdata.\
                    resize(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length);
                    for (int i = 0; i < m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].VbinNumber; i++)
                    {
                        if (m_pLineData[i_radial_of_total].W[i] != PREFILLVALUE_VTB)
                        {
                            float tmp = (m_pLineData[i_radial_of_total].W[i] - (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Offset[i_var]) * 1.0 / (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Scale[i_var];
                            *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                    = (unsigned short)(tmp * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale + m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset);
                        }
                        else
                        {
                            *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                    = (unsigned short) INVALID_BT;
                        }
                    }
                    break;
                case 4:
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.DataType = 1;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale = 100;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset = 10000;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Flags = PREFILLVALUE_SHORT;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length = \
                        m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength \
                        * m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber;                                 //距离库数据的长度，Unit:Bytes
                    strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved, \
                            "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved) - 1); //保留字段
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentdata.\
                    resize(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length);
                    for (int i = 0; i < m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber; i++)
                    {
                        if (m_pLineData[i_radial_of_total].UnZ[i] != PREFILLVALUE_VTB)
                        {
                            float tmp = (m_pLineData[i_radial_of_total].UnZ[i] - (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Offset[i_var]) * 1.0 / (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Scale[i_var];
                            if (tmp * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale + m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset < 0)
                            {
                                *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                        = (unsigned short) INVALID_BT;
                            }
                            else
                            {
                                *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                        = (unsigned short)(tmp * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale + m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset);
                            }
                        }
                        else
                        {
                            *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                    = (unsigned short) INVALID_BT;
                        }
                    }
                    break;
                case 5:
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.DataType = 7;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale = 100;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset = 10000;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Flags = PREFILLVALUE_SHORT;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length = \
                        m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength \
                        * m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber;                                 //距离库数据的长度，Unit:Bytes
                    strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved, \
                            "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved) - 1); //保留字段
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentdata.\
                    resize(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length);
                    for (int i = 0; i < m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber; i++)
                    {
                        if (m_pLineData[i_radial_of_total].ZDR[i] != PREFILLVALUE_VTB)
                        {
                            float tmp = (m_pLineData[i_radial_of_total].ZDR[i] - (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Offset[i_var]) * 1.0 / (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Scale[i_var];
                            if (tmp * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale + m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset < 0)
                            {
                                *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                        = (unsigned short) INVALID_BT;
                            }
                            else
                            {
                                *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                        = (unsigned short)(tmp * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale + m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset);
                            }
                        }
                        else
                        {
                            *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                    = (unsigned short) INVALID_BT;
                        }
                    }
                    break;
                case 6:
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.DataType = 10;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale = 100;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset = 10000;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Flags = PREFILLVALUE_SHORT;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length = \
                        m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength \
                        * m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber;                                 //距离库数据的长度，Unit:Bytes
                    strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved, \
                            "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved) - 1); //保留字段
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentdata.\
                    resize(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length);
                    for (int i = 0; i < m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber; i++)
                    {
                        if (m_pLineData[i_radial_of_total].PHDP[i] != PREFILLVALUE_VTB)
                        {
                            float tmp = (m_pLineData[i_radial_of_total].PHDP[i] - (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Offset[i_var]) * 1.0 / (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Scale[i_var];
                            if (tmp * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale + m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset < 0)
                            {
                                *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                        = (unsigned short) INVALID_BT;
                            }
                            else
                            {
                                *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                        = (unsigned short)(tmp * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale + m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset);
                            }
                        }
                        else
                        {
                            *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                    = (unsigned short) INVALID_BT;
                        }
                    }
                    break;
                case 7:
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.DataType = 11;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale = 100;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset = 10000;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Flags = PREFILLVALUE_SHORT;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length = \
                        m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength \
                        * m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber;                                 //距离库数据的长度，Unit:Bytes
                    strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved, \
                            "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved) - 1); //保留字段
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentdata.\
                    resize(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length);
                    for (int i = 0; i < m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber; i++)
                    {
                        if (m_pLineData[i_radial_of_total].KDP[i] != PREFILLVALUE_VTB)
                        {
                            float tmp = (m_pLineData[i_radial_of_total].KDP[i] - (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Offset[i_var]) * 1.0 / (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Scale[i_var];
                            if (tmp * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale + m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset < 0)
                            {
                                *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                        = (unsigned short) INVALID_BT;
                            }
                            else
                            {
                                *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                        = (unsigned short)(tmp * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale + m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset);
                            }
                        }
                        else
                        {
                            *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                    = (unsigned short) INVALID_BT;
                        }
                    }
                    break;
                case 8:
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.DataType = 9;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale = 1000;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset = 10000;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Flags = PREFILLVALUE_SHORT;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length = \
                        m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength \
                        * m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber;                                 //距离库数据的长度，Unit:Bytes
                    strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved, \
                            "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved) - 1); //保留字段
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentdata.\
                    resize(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length);
                    for (int i = 0; i < m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber; i++)
                    {
                        if (m_pLineData[i_radial_of_total].ROHV[i] != PREFILLVALUE_VTB)
                        {
                            float tmp = (m_pLineData[i_radial_of_total].ROHV[i] - (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Offset[i_var]) * 1.0 / (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Scale[i_var];
                            if (tmp * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale + m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset < 0)
                            {
                                *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                        = (unsigned short) INVALID_BT;
                            }
                            else
                            {
                                *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                        = (unsigned short)(tmp * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale + m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset);
                            }
                        }
                        else
                        {
                            *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                    = (unsigned short) INVALID_BT;
                        }
                    }
                    break;
                case 9:
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.DataType = 8;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale = 100;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset = 10000;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Flags = PREFILLVALUE_SHORT;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length = \
                        m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength \
                        * m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber;                                 //距离库数据的长度，Unit:Bytes
                    strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved, \
                            "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved) - 1); //保留字段
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentdata.\
                    resize(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length);
                    for (int i = 0; i < m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber; i++)
                    {
                        if (m_pLineData[i_radial_of_total].LDR[i] != PREFILLVALUE_VTB)
                        {
                            float tmp = (m_pLineData[i_radial_of_total].ROHV[i] - (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Offset[i_var]) * 1.0 / (int)m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Scale[i_var];
                            if (tmp * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale + m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset < 0)
                            {
                                *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                        = (unsigned short) INVALID_BT;
                            }
                            else
                            {
                                *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                        = (unsigned short)(tmp * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale + m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset);
                            }
                        }
                        else
                        {
                            *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                    = (unsigned short) INVALID_BT;
                        }
                    }
                    break;
                case 10:
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.DataType = 16;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Scale = m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Scale[i_var];
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Offset = m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].Offset[i_var];
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Flags = PREFILLVALUE_SHORT;
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length = \
                        m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength \
                        * m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber;                                 //距离库数据的长度，Unit:Bytes
                    strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved, \
                            "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Reserved) - 1); //保留字段
                    m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentdata.\
                    resize(m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.Length);
                    for (int i = 0; i < m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].ZbinNumber; i++)
                    {
                        if (m_pLineData[i_radial_of_total].SNRH[i] != PREFILLVALUE_VTB)
                        {
                            *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                = (unsigned short) m_pLineData[i_radial_of_total].SNRH[i];
                        }
                        else
                        {
                            *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_var).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_var].momentheader.BinLength) \
                                    = (unsigned short) INVALID_BT;
                        }
                    }
                    break;
                default:
                    break;
            }
        }

        i_radial_of_cut ++;
        if (i_radial_of_cut == m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i_cut].RecordNumber)
        {
            cout << "Record number of layer " << i_cut << " is " << i_radial_of_cut << endl;
            i_cut ++;
            i_radial_of_cut = 0;
        }
    }
    if (m_RadarDataHead_SBand != nullptr)
    {
        delete m_RadarDataHead_SBand;
        m_RadarDataHead_SBand = nullptr;
    }
    return 0;
}

bool CNrietFileIO::LoadQCData(char *fileName)
{
    gzFile l_File;
    int gz_status = 0;
    l_File = gzopen(fileName, "rb");
    if (l_File == nullptr)
    {
        cout << "Source file open error." << endl;
        return false;
    }

    m_RadarData = new WRADRAWDATA();
    m_RadarHead = &(m_RadarData->commonBlock);
    COMMONBLOCKPAR *Par_RadarHead = &(m_RadarData->commonBlockPAR);

    // header
    gz_status = gzread(l_File, &m_RadarHead->genericheader, sizeof(GENERICHEADER));
    if (gz_status != sizeof(GENERICHEADER))
    {
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
            m_RadarHead = nullptr;
        }
        gzclose(l_File);
        return false;
    }
    if (m_RadarHead->genericheader.MagicNumber != 0x4D545352)
    {
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
            m_RadarHead = nullptr;
        }

        gzclose(l_File);
        return false;
    }

    gz_status = gzread(l_File, &m_RadarHead->siteconfig, sizeof(SITECONFIG));
    if (gz_status != sizeof(SITECONFIG))
    {
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
            m_RadarHead = nullptr;
        }
        gzclose(l_File);
        return false;
    }

    gz_status = gzread(l_File, &m_RadarHead->taskconfig, sizeof(TASKCONFIG));
    if (gz_status != sizeof(TASKCONFIG))
    {
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
            m_RadarHead = nullptr;
        }
        gzclose(l_File);
        return false;
    }

    m_RadarHead->cutconfig.resize(m_RadarHead->taskconfig.CutNumber);
    for (int icut = 0; icut < m_RadarHead->taskconfig.CutNumber; icut++)
    {
        gz_status = gzread(l_File, &m_RadarHead->cutconfig.at(icut), sizeof(CUTCONFIG));
        if (gz_status != sizeof(CUTCONFIG))
        {
            if (m_RadarData)
            {
                delete m_RadarData;
                m_RadarData = nullptr;
                m_RadarHead = nullptr;
            }
            gzclose(l_File);
            return false;
        }
    }

    gzerror(l_File, &gz_status);
    if (gz_status != 0)
    {
        gzclose(l_File);
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
            m_RadarHead = nullptr;
        }
        return false;
    }

    // data
    RADIAL radial_temp;
    while (gz_status == 0)
    {
        gz_status = gzread(l_File, &radial_temp.radialheader, sizeof(RADIALHEADERPAR));
        if (gz_status != sizeof(RADIALHEADERPAR))
        {
            gzclose(l_File);
            if (m_RadarData)
            {
                delete m_RadarData;
                m_RadarData = nullptr;
                m_RadarHead = nullptr;
            }
            return false;
        }
        gzerror(l_File, &gz_status);
        if (gz_status != 0)
        {
            gzclose(l_File);
            if (m_RadarData)
            {
                delete m_RadarData;
                m_RadarData = nullptr;
                m_RadarHead = nullptr;
            }
            return false;
        }

        radial_temp.momentblock.resize(radial_temp.radialheader.MomentNumber);
        // !!!!!!!!!!!!!!!!!!!!!!!!!
        for (int imoment = 0; imoment < radial_temp.radialheader.MomentNumber; imoment++)
        {
            gz_status = gzread(l_File, &radial_temp.momentblock.at(imoment).momentheader, sizeof(MOMENTHEADER));
            if (gz_status != sizeof(MOMENTHEADER))
            {
                gzclose(l_File);
                if (m_RadarData)
                {
                    delete m_RadarData;
                    m_RadarData = nullptr;
                    m_RadarHead = nullptr;
                }
                return false;
            }
            gzerror(l_File, &gz_status);
            if (gz_status != 0)
            {
                gzclose(l_File);
                if (m_RadarData)
                {
                    delete m_RadarData;
                    m_RadarData = nullptr;
                    m_RadarHead = nullptr;
                }
                return false;
            }

            radial_temp.momentblock.at(imoment).momentdata.resize(radial_temp.momentblock.at(imoment).momentheader.Length);
            gz_status = gzread(l_File, &radial_temp.momentblock.at(imoment).momentdata.at(0), radial_temp.momentblock.at(imoment).momentheader.Length);
            if (gz_status != radial_temp.momentblock.at(imoment).momentheader.Length)
            {
                gzclose(l_File);
                if (m_RadarData)
                {
                    delete m_RadarData;
                    m_RadarData = nullptr;
                    m_RadarHead = nullptr;
                }
                return false;
            }
            gzerror(l_File, &gz_status);
            if (gz_status != 0)
            {
                gzclose(l_File);
                if (m_RadarData)
                {
                    delete m_RadarData;
                    m_RadarData = nullptr;
                    m_RadarHead = nullptr;
                }
                return false;
            }
        }
        // !!!!!!!!!!!!!!!!!!!!!!!!!
        m_RadarData->radials.push_back(radial_temp);

        if (radial_temp.radialheader.RadialState == 4 || radial_temp.radialheader.RadialState == 6)
        {
            break;
        }
    }

    gzclose(l_File);
    return true;
}

bool CNrietFileIO::LoadStandardVTB(char *fileName)
{
    gzFile l_File;
    int gz_status = 0;
    l_File = gzopen(fileName, "rb");
    if (l_File == nullptr)
    {
        cout << "Source file open error." << endl;
        return false;
    }

    m_RadarData = new WRADRAWDATA();
    m_RadarHead = &(m_RadarData->commonBlock);

    gz_status = gzread(l_File, &m_RadarHead->genericheader, sizeof(GENERICHEADER));
    if (gz_status != sizeof(GENERICHEADER))
    {
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
            m_RadarHead = nullptr;
        }
        gzclose(l_File);
        return false;
    }
    if (m_RadarHead->genericheader.MagicNumber != 0x4D545352)
    {
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
            m_RadarHead = nullptr;
        }

        gzclose(l_File);
        return false;
    }

    gz_status = gzread(l_File, &m_RadarHead->siteconfig, sizeof(SITECONFIG));
    if (gz_status != sizeof(SITECONFIG))
    {
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
            m_RadarHead = nullptr;
        }
        gzclose(l_File);
        return false;
    }

    gz_status = gzread(l_File, &m_RadarHead->taskconfig, sizeof(TASKCONFIG));
    if (gz_status != sizeof(TASKCONFIG))
    {
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
            m_RadarHead = nullptr;
        }
        gzclose(l_File);
        return false;
    }

    m_RadarHead->cutconfig.resize(m_RadarHead->taskconfig.CutNumber);
    for (int icut = 0; icut < m_RadarHead->taskconfig.CutNumber; icut++)
    {
        gz_status = gzread(l_File, &m_RadarHead->cutconfig.at(icut), sizeof(CUTCONFIG));
        if (gz_status != sizeof(CUTCONFIG))
        {
            if (m_RadarData)
            {
                delete m_RadarData;
                m_RadarData = nullptr;
                m_RadarHead = nullptr;
            }
            gzclose(l_File);
            return false;
        }
    }

    gzerror(l_File, &gz_status);
    if (gz_status != 0)
    {
        gzclose(l_File);
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
            m_RadarHead = nullptr;
        }
        return false;
    }

    RADIAL radial_temp;
    RADIALHEADER radialheader_temp;
    while (gz_status == 0)
    {
        gz_status = gzread(l_File, &radialheader_temp, sizeof(RADIALHEADER));
        if (gz_status != sizeof(RADIALHEADER))
        {
            if (m_RadarData)
            {
                delete m_RadarData;
                m_RadarData = nullptr;
                m_RadarHead = nullptr;
            }
            gzclose(l_File);
            return false;
        }
        ConvertRadialHeaderNWCtoRadialHeaderPAR(&radialheader_temp, &radial_temp.radialheader);
        gzerror(l_File, &gz_status);
        if (gz_status != 0)
        {
            gzclose(l_File);
            if (m_RadarData)
            {
                delete m_RadarData;
                m_RadarData = nullptr;
                m_RadarHead = nullptr;
            }
            return false;
        }

        radial_temp.momentblock.resize(radial_temp.radialheader.MomentNumber);
        for (int imoment = 0; imoment < radial_temp.radialheader.MomentNumber; imoment ++)
        {
            gz_status = gzread(l_File, &radial_temp.momentblock.at(imoment).momentheader, sizeof(MOMENTHEADER));
            if (gz_status != sizeof(MOMENTHEADER))
            {
                if (m_RadarData)
                {
                    delete m_RadarData;
                    m_RadarData = nullptr;
                    m_RadarHead = nullptr;
                }
                gzclose(l_File);
                return false;
            }
            gzerror(l_File, &gz_status);
            if (gz_status != 0)
            {
                gzclose(l_File);
                if (m_RadarData)
                {
                    delete m_RadarData;
                    m_RadarData = nullptr;
                    m_RadarHead = nullptr;
                }
                return false;
            }

            radial_temp.momentblock.at(imoment).momentdata.resize(radial_temp.momentblock.at(imoment).momentheader.Length);
            gz_status = gzread(l_File, &radial_temp.momentblock.at(imoment).momentdata.at(0), radial_temp.momentblock.at(imoment).momentheader.Length);
            if (gz_status != radial_temp.momentblock.at(imoment).momentheader.Length)
            {
                if (m_RadarData)
                {
                    delete m_RadarData;
                    m_RadarData = nullptr;
                    m_RadarHead = nullptr;
                }
                gzclose(l_File);
                return false;
            }
            gzerror(l_File, &gz_status);
            if (gz_status != 0)
            {
                gzclose(l_File);
                if (m_RadarData)
                {
                    delete m_RadarData;
                    m_RadarData = nullptr;
                    m_RadarHead = nullptr;
                }
                return false;
            }
        }
        m_RadarData->radials.push_back(radial_temp);

        if (radial_temp.radialheader.RadialState == 4 || radial_temp.radialheader.RadialState == 6)
        {
            break;
        }
    }
    gzclose(l_File);

    return true;
}

int CNrietFileIO:: ConvertCommonBLockPARtoCommonBlockNWC(COMMONBLOCKPAR *commonblockPAR, COMMONBLOCK *commonblockNWC)
{
    //genricheader
    commonblockNWC->genericheader = commonblockPAR->genericheader;
    //siteconfig
    commonblockNWC->siteconfig.Latitude = commonblockPAR->siteconfig.Latitude;
    commonblockNWC->siteconfig.Longitude = commonblockPAR->siteconfig.Longitude;
    memcpy(commonblockNWC->siteconfig.SiteCode, commonblockPAR->siteconfig.SiteCode, 8);
    memcpy(commonblockNWC->siteconfig.SiteName, commonblockPAR->siteconfig.SiteName, 32);
    commonblockNWC->siteconfig.Frequency = commonblockPAR->siteconfig.Frequency;
    commonblockNWC->siteconfig.RadarType = commonblockPAR->siteconfig.RadarType;
    commonblockNWC->siteconfig.RdaVersion = commonblockPAR->siteconfig.RdaVersion;
    commonblockNWC->siteconfig.AntennaHeight = commonblockPAR->siteconfig.AntennaHeight;
    commonblockNWC->siteconfig.GroundHeight = commonblockPAR->siteconfig.GroundHeight;
    commonblockNWC->siteconfig.BeamWidthHori = commonblockPAR->cutconfig[0].RxBeamWidth_H; //****
    commonblockNWC->siteconfig.BeamWidthVert = commonblockPAR->cutconfig[0].RxBeamWidth_V; //****


    //taskconfig
    memcpy(commonblockNWC->taskconfig.TaskName, commonblockPAR->taskconfig.TaskName, 32);
    memcpy(commonblockNWC->taskconfig.TaskDescription, commonblockPAR->taskconfig.TaskDescription, 128);
    commonblockNWC->taskconfig.PolarizationType = commonblockPAR->taskconfig.PolarizationType;
    commonblockNWC->taskconfig.ScanType = commonblockPAR->taskconfig.ScanType;
    commonblockNWC->taskconfig.PulseWidth = commonblockPAR->beamconfig[0].SubPulseConfig[0].SubPulseWidth; //脉冲宽度(纳秒，1~10000)
    commonblockNWC->taskconfig.ScanStartTime = commonblockPAR->taskconfig.ScanStartTime;
    commonblockNWC->taskconfig.CutNumber = commonblockPAR->taskconfig.CutNumber;
    commonblockNWC->taskconfig.HorizontalNoise = commonblockPAR->beamconfig[0].SubPulseConfig[0].HorizontalNoise;
    commonblockNWC->taskconfig.VerticalNoise = commonblockPAR->beamconfig[0].SubPulseConfig[0].VerticalNoise;
    commonblockNWC->taskconfig.HorizontalCalibration = commonblockPAR->beamconfig[0].SubPulseConfig[0].HorizontalCalibration;
    commonblockNWC->taskconfig.VerticalNoiseTemperature = commonblockPAR->beamconfig[0].SubPulseConfig[0].VerticalNoiseTemperature;
    commonblockNWC->taskconfig.ZDRCalibration = commonblockPAR->beamconfig[0].SubPulseConfig[0].ZDRCalibration;
    commonblockNWC->taskconfig.PHIDPCalibration = commonblockPAR->beamconfig[0].SubPulseConfig[0].PHIDPCalibration;
    commonblockNWC->taskconfig.LDRCalibration = commonblockPAR->beamconfig[0].SubPulseConfig[0].LDRCalibration;
//    commonblockNWC->taskconfig.ZDRCalibrationInside=0.0;
//    commonblockNWC->taskconfig.PHIDPCalibrationInside=0.0;
//    commonblockNWC->taskconfig.BlindBinNum=1;
//    commonblockNWC->taskconfig.LGTZDRA=1.0;
//    commonblockNWC->taskconfig.LGTZDRB=1.0;
//    commonblockNWC->taskconfig.LGTAZ=1.0;
//    commonblockNWC->taskconfig.BinDilution=0.0;
//    commonblockNWC->taskconfig.AzDilution=0.0;

    //cutconfig
//    vector<CUTCONFIGPAR>::iterator it=commonblockPAR->cutconfig.begin();
//    commonblockNWC->cutconfig.resize(commonblockPAR->cutconfig.size());
    for (auto it : commonblockPAR->cutconfig)
    {
        CUTCONFIG tmp_cutconfig;
        tmp_cutconfig.ProcessMode = it.ProcessMode;
        tmp_cutconfig.WaveForm = it.WaveForm;
        tmp_cutconfig.PRF1 = it.N1PRF1;
        tmp_cutconfig.PRF2 = it.N1PRF2;
        tmp_cutconfig.DealiasingMode = it.DealiasingMode;
        tmp_cutconfig.Azimuth = it.Azimuth;
        tmp_cutconfig.Elevation = it.RxBeamElevation;
        tmp_cutconfig.StartAngle = it.StartAngle;
        tmp_cutconfig.EndAngle = it.EndAngle;
        tmp_cutconfig.AngularResolution = it.AngularResolution;
        tmp_cutconfig.ScanSpeed = it.ScanSpeed;
        tmp_cutconfig.LogResolution = it.LogResolution;
        tmp_cutconfig.DopplerResolution = it.DopplerResolution;
        tmp_cutconfig.MaximumRange1 = it.MaximumRange1;
        tmp_cutconfig.MaximumRange2 = it.MaximumRange2;
        tmp_cutconfig.StartRange = it.StartRange;
        tmp_cutconfig.Sample1 = it.Sample1;
        tmp_cutconfig.Sample2 = it.Sample2;
        tmp_cutconfig.PhaseMode = it.PhaseMode;
        tmp_cutconfig.AtmosphericLoss = it.AtmosphericLoss;
        tmp_cutconfig.NyquistSpeed = it.NyquistSpeed;
        tmp_cutconfig.MomentsMask = it.MomentsMask;
        tmp_cutconfig.MomentsSizeMask = it.MomentsSizeMask;
        tmp_cutconfig.MiscFilterMask = it.MiscFilterMask;
        tmp_cutconfig.SQIThreshold = it.SQIThreshold;
        tmp_cutconfig.SIGThreshold = it.SIGThreshold;
        tmp_cutconfig.CSRThreshold = it.CSRThreshold;
        tmp_cutconfig.LOGThreshold = it.LOGThreshold;
        tmp_cutconfig.CPAThreshold = it.CPAThreshold;
        tmp_cutconfig.PMIThreshold = it.PMIThreshold;
        tmp_cutconfig.DPLOGThreshold = it.DPLOGThreshold;
//        tmp_cutconfig.ThresholdsReserved=it.ThresholdsReserved;
        tmp_cutconfig.dBTMask = it.dBTMask;
        tmp_cutconfig.dBZMask = it.dBZMask;
        tmp_cutconfig.VelocityMask = it.VelocityMask;
        tmp_cutconfig.SpectrumWidthMask = it.SpectrumWidthMask;
        tmp_cutconfig.DPMask = it.DPMask;
//        tmp_cutconfig.MaskReserved=it.MaskReserved;
        tmp_cutconfig.ScanSync = 0;
        tmp_cutconfig.Direction = it.Direction;
        tmp_cutconfig.GroundClutterClassifierType = it.GroundClutterClassifierType;
        tmp_cutconfig.GroundClutterFilterType = it.GroundClutterFilterType;
        tmp_cutconfig.GroundClutterFilterWindow = it.GroundClutterFilterWindow;
        tmp_cutconfig.GroundClutterFilterNotchWidth = it.GroundClutterFilterNotchWidth;
        commonblockNWC->cutconfig.push_back(tmp_cutconfig);
    }
    return 0;
}

bool CNrietFileIO::LoadStandardPARVTB(char *fileName)
{
    gzFile l_File;
    int gz_status = 0;
    l_File = gzopen(fileName, "rb");
    if (l_File == nullptr)
    {
        cout << "Source file open error." << endl;
        return false;
    }

    m_RadarData = new WRADRAWDATA();
    m_RadarHead = &(m_RadarData->commonBlock);
    COMMONBLOCKPAR *Par_RadarHead = &(m_RadarData->commonBlockPAR);

    string rawfilename = string(fileName).substr(string(fileName).find_last_of("/") + 1);

    gz_status = gzread(l_File, &(Par_RadarHead->genericheader), sizeof(GENERICHEADER));
    if (gz_status != sizeof(GENERICHEADER))
    {
        gzclose(l_File);
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
            m_RadarHead = nullptr;
        }
        return false;
    }
    if (Par_RadarHead->genericheader.MagicNumber != 600562)
    {
        gzclose(l_File);
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
            m_RadarHead = nullptr;
        }
        return false;
    }

    gz_status = gzread(l_File, &Par_RadarHead->siteconfig, sizeof(SITECONFIGPAR));
    if (gz_status != sizeof(SITECONFIGPAR))
    {
        gzclose(l_File);
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
            m_RadarHead = nullptr;
        }
        return false;
    }

    gz_status = gzread(l_File, &Par_RadarHead->taskconfig, sizeof(TASKCONFIGPAR));
    if (gz_status != sizeof(TASKCONFIGPAR))
    {
        gzclose(l_File);
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
            m_RadarHead = nullptr;
        }
        return false;
    }

    Par_RadarHead->beamconfig.resize(Par_RadarHead->taskconfig.ScanBeamNumber);
    for (int ibeam = 0; ibeam < Par_RadarHead->taskconfig.ScanBeamNumber; ibeam++)
    {
        gz_status = gzread(l_File, &Par_RadarHead->beamconfig.at(ibeam), sizeof(BEAMCONFIGPAR));
        if (gz_status != sizeof(BEAMCONFIGPAR))
        {
            gzclose(l_File);
            if (m_RadarData)
            {
                delete m_RadarData;
                m_RadarData = nullptr;
                m_RadarHead = nullptr;
            }
            return false;
        }
    }

    Par_RadarHead->cutconfig.resize(Par_RadarHead->taskconfig.CutNumber);
    for (int icut = 0; icut < Par_RadarHead->taskconfig.CutNumber; icut++)
    {
        gz_status = gzread(l_File, &Par_RadarHead->cutconfig.at(icut), sizeof(CUTCONFIGPAR));
        if (gz_status != sizeof(CUTCONFIGPAR))
        {
            gzclose(l_File);
            if (m_RadarData)
            {
                delete m_RadarData;
                m_RadarData = nullptr;
                m_RadarHead = nullptr;
            }
            return false;
        }
    }

    gzerror(l_File, &gz_status);
    if (gz_status != 0)
    {
        gzclose(l_File);
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
            m_RadarHead = nullptr;
        }
        return false;
    }

    ConvertCommonBLockPARtoCommonBlockNWC(Par_RadarHead, m_RadarHead);

    RADIAL radial_temp;
    while (gz_status == 0)
    {
        gz_status = gzread(l_File, &radial_temp.radialheader, sizeof(RADIALHEADERPAR));
        if (gz_status != sizeof(RADIALHEADERPAR))
        {
            gzclose(l_File);
            if (m_RadarData)
            {
                delete m_RadarData;
                m_RadarData = nullptr;
                m_RadarHead = nullptr;
            }
            return false;
        }
        gzerror(l_File, &gz_status);
        if (gz_status != 0)
        {
            gzclose(l_File);
            if (m_RadarData)
            {
                delete m_RadarData;
                m_RadarData = nullptr;
                m_RadarHead = nullptr;
            }
            return false;
        }

        radial_temp.momentblock.resize(radial_temp.radialheader.MomentNumber);
        for (int imoment = 0; imoment < radial_temp.radialheader.MomentNumber; imoment++)
        {
            gz_status = gzread(l_File, &radial_temp.momentblock.at(imoment).momentheader, sizeof(MOMENTHEADER));
            if (gz_status != sizeof(MOMENTHEADER))
            {
                gzclose(l_File);
                if (m_RadarData)
                {
                    delete m_RadarData;
                    m_RadarData = nullptr;
                    m_RadarHead = nullptr;
                }
                return false;
            }
            gzerror(l_File, &gz_status);
            if (gz_status != 0)
            {
                gzclose(l_File);
                if (m_RadarData)
                {
                    delete m_RadarData;
                    m_RadarData = nullptr;
                    m_RadarHead = nullptr;
                }
                return false;
            }

            radial_temp.momentblock.at(imoment).momentdata.resize(radial_temp.momentblock.at(imoment).momentheader.Length);
            gz_status = gzread(l_File, &radial_temp.momentblock.at(imoment).momentdata.at(0), radial_temp.momentblock.at(imoment).momentheader.Length);
            if (gz_status != radial_temp.momentblock.at(imoment).momentheader.Length)
            {
                gzclose(l_File);
                if (m_RadarData)
                {
                    delete m_RadarData;
                    m_RadarData = nullptr;
                    m_RadarHead = nullptr;
                }
                return false;
            }
            gzerror(l_File, &gz_status);
            if (gz_status != 0)
            {
                gzclose(l_File);
                if (m_RadarData)
                {
                    delete m_RadarData;
                    m_RadarData = nullptr;
                    m_RadarHead = nullptr;
                }
                return false;
            }
        }
        m_RadarData->radials.push_back(radial_temp);

        if (radial_temp.radialheader.RadialState == 4 || radial_temp.radialheader.RadialState == 6)
        {
            break;
        }
    }
    gzclose(l_File);

    time_t pro_time_t = m_RadarData->radials.back().radialheader.Seconds;
    tm pro_tm = *(gmtime(&pro_time_t));
    char yyyymmddhhmmss[14] = {0};
    sprintf(&yyyymmddhhmmss[0], "%4.4d", pro_tm.tm_year + 1900);
    sprintf(&yyyymmddhhmmss[4], "%2.2d", pro_tm.tm_mon + 1);
    sprintf(&yyyymmddhhmmss[6], "%2.2d", pro_tm.tm_mday);
    sprintf(&yyyymmddhhmmss[8], "%2.2d", pro_tm.tm_hour);
    sprintf(&yyyymmddhhmmss[10], "%2.2d", pro_tm.tm_min);
    sprintf(&yyyymmddhhmmss[12], "%2.2d", pro_tm.tm_sec);
    rawfilename.replace(12, 14, yyyymmddhhmmss);
    memcpy(&m_RadarData->commonBlockPAR.siteconfig.Reserved[0], rawfilename.c_str(), sizeof(m_RadarData->commonBlockPAR.siteconfig.Reserved) - 1);
    return true;
}

bool CNrietFileIO::LoadBZ2StandardVTB(char *fileName)
{
    m_fileTime = m_radarFileName.mid(15, 14).toStdString();
    int bzstatus;
    FILE *fp = fopen(fileName, "rb");
    if (fp == nullptr)
    {
        cout << "Source file open error." << endl;
        return false;
    }

    BZFILE *bzFp = BZ2_bzReadOpen(&bzstatus, fp, 4, 0, nullptr, 0);
    if (bzstatus < BZ_OK)
    {
        BZ2_bzReadClose(&bzstatus, bzFp);
        fclose(fp);
        cout << "Source file open error." << endl;
        return false;
    }

    m_RadarData = new WRADRAWDATA();
    m_RadarHead = &(m_RadarData->commonBlock);

    // 打开/dev/null用于屏蔽输出
    int fd = open("/dev/null", O_WRONLY);
    if (fd == -1)
    {
        std::cerr << "Failed to open /dev/null" << std::endl;
        return -1;
    }

    // 保存当前的标准输出和标准错误
    int saved_stdout = dup(fileno(stdout));
    int saved_stderr = dup(fileno(stderr));

    // 将标准输出和标准错误重定向到/dev/null
    dup2(fd, fileno(stdout));
    dup2(fd, fileno(stderr));
    BZ2_bzRead(&bzstatus, bzFp, &m_RadarHead->genericheader, sizeof(GENERICHEADER));
    // 关闭/dev/null并恢复原来的标准输出和标准错误
    dup2(saved_stdout, fileno(stdout));
    dup2(saved_stderr, fileno(stderr));
    if (bzstatus < BZ_OK)
    {
        BZ2_bzReadClose(&bzstatus, bzFp);
        fclose(fp);
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
        }
        cout << "Source file open error." << endl;
        return false;
    }

    if (m_RadarHead->genericheader.MagicNumber != 0x4D545352)
    {
        cout << "file ID check fail" << endl;
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
            m_RadarHead = nullptr;
        }

        BZ2_bzReadClose(&bzstatus, bzFp);
        fclose(fp);
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
        }
        return false;
    }

    dup2(fd, fileno(stdout));
    dup2(fd, fileno(stderr));
    BZ2_bzRead(&bzstatus, bzFp, &m_RadarHead->siteconfig, sizeof(SITECONFIG));
    dup2(saved_stdout, fileno(stdout));
    dup2(saved_stderr, fileno(stderr));
    if (bzstatus < BZ_OK)
    {
        BZ2_bzReadClose(&bzstatus, bzFp);
        fclose(fp);
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
        }
        cout << "Source file read error." << endl;
        return false;
    }

    dup2(fd, fileno(stdout));
    dup2(fd, fileno(stderr));
    BZ2_bzRead(&bzstatus, bzFp, &m_RadarHead->taskconfig, sizeof(TASKCONFIG));
    dup2(saved_stdout, fileno(stdout));
    dup2(saved_stderr, fileno(stderr));
    if (bzstatus < BZ_OK)
    {
        BZ2_bzReadClose(&bzstatus, bzFp);
        fclose(fp);
        if (m_RadarData)
        {
            delete m_RadarData;
            m_RadarData = nullptr;
        }
        cout << "Source file read error." << endl;
        return false;
    }
    m_RadarHead->cutconfig.resize(m_RadarHead->taskconfig.CutNumber);

    for (int icut = 0; icut < m_RadarHead->taskconfig.CutNumber; icut++)
    {
        dup2(fd, fileno(stdout));
        dup2(fd, fileno(stderr));
        BZ2_bzRead(&bzstatus, bzFp, &m_RadarHead->cutconfig.at(icut), sizeof(CUTCONFIG));
        dup2(saved_stdout, fileno(stdout));
        dup2(saved_stderr, fileno(stderr));
        if (bzstatus < BZ_OK)
        {
            BZ2_bzReadClose(&bzstatus, bzFp);
            fclose(fp);
            if (m_RadarData)
            {
                delete m_RadarData;
                m_RadarData = nullptr;
            }
            cout << "Source file read error." << endl;
            return false;
        }
    }
    RADIAL radial_temp;
    RADIALHEADER radial_head_temp;
    while (bzstatus != BZ_STREAM_END)
    {
        dup2(fd, fileno(stdout));
        dup2(fd, fileno(stderr));
        BZ2_bzRead(&bzstatus, bzFp, &radial_head_temp, sizeof(RADIALHEADER));
        dup2(saved_stdout, fileno(stdout));
        dup2(saved_stderr, fileno(stderr));

        ConvertRadialHeaderNWCtoRadialHeaderPAR(&radial_head_temp, &radial_temp.radialheader);
        if (bzstatus < BZ_OK)
        {
            BZ2_bzReadClose(&bzstatus, bzFp);
            fclose(fp);
            if (m_RadarData)
            {
                delete m_RadarData;
                m_RadarData = nullptr;
            }
            cout << "Source file read error." << endl;
            return false;
        }
        radial_temp.momentblock.resize(radial_temp.radialheader.MomentNumber);
        for (int imoment = 0; imoment < radial_temp.radialheader.MomentNumber; imoment ++)
        {
            dup2(fd, fileno(stdout));
            dup2(fd, fileno(stderr));
            BZ2_bzRead(&bzstatus, bzFp, &radial_temp.momentblock.at(imoment).momentheader, sizeof(MOMENTHEADER));
            dup2(saved_stdout, fileno(stdout));
            dup2(saved_stderr, fileno(stderr));

            if (bzstatus < BZ_OK)
            {
                BZ2_bzReadClose(&bzstatus, bzFp);
                fclose(fp);
                if (m_RadarData)
                {
                    delete m_RadarData;
                    m_RadarData = nullptr;
                }
                cout << "Source file read error." << endl;
                return false;
            }
            radial_temp.momentblock.at(imoment).momentdata.resize(radial_temp.momentblock.at(imoment).momentheader.Length);
            dup2(fd, fileno(stdout));
            dup2(fd, fileno(stderr));
            BZ2_bzRead(&bzstatus, bzFp, &radial_temp.momentblock.at(imoment).momentdata.at(0), radial_temp.momentblock.at(imoment).momentheader.Length);
            dup2(saved_stdout, fileno(stdout));
            dup2(saved_stderr, fileno(stderr));
            if (bzstatus < BZ_OK)
            {
                BZ2_bzReadClose(&bzstatus, bzFp);
                fclose(fp);
                if (m_RadarData)
                {
                    delete m_RadarData;
                    m_RadarData = nullptr;
                }
                cout << "Source file read error." << endl;
                return false;
            }
        }
        m_RadarData->radials.push_back(radial_temp);

        if (radial_temp.radialheader.RadialState == 4 || radial_temp.radialheader.RadialState == 6)
        {
            break;
        }
    }

    BZ2_bzReadClose(&bzstatus, bzFp);
    fclose(fp);
    close(fd);
    return true;
}

int CNrietFileIO::ConvertRadialHeaderNWCtoRadialHeaderPAR(RADIALHEADER *src, RADIALHEADERPAR *dst)
{
    dst->Azimuth = src->Azimuth;
    dst->Seconds = src->Seconds;
    dst->Elevation = src->Elevation;
    dst->ElevationNumber = src->ElevationNumber;
    dst->SpotBlank = src->SpotBlank;
    dst->RadialState = src->RadialState;
    dst->RadialNumber = src->RadialNumber;
    dst->LengthOfData = src->LengthOfData;
    dst->Microseconds = src->Microseconds;
    dst->MomentNumber = src->MomentNumber;
    dst->SequenceNumber = src->SequenceNumber;
    dst->VerticalEstimatedNoise = src->VerticalEstimatedNoise;
    dst->HorizontalEstimatedNoise = src->HorizontalEstimatedNoise;
    return 0;
}

int CNrietFileIO::LoadCSA(void *temp, void *str)
{
    char *fileName = (char *)str;
    s_Pro_Grid::RadarProduct *SAData = (s_Pro_Grid::RadarProduct *) temp;
    s_Pro_Grid::DataBlock blocklist;
    blocklist.ProDataInfo.DOffset = 0;
    blocklist.ProDataInfo.DScale = 1;
    blocklist.ProductData.resize(3000 * 3000 * sizeof(short));
    SAData->DataBlock.push_back(blocklist);
    //    short tempRaster[3000][3000];
    //    s_Pro_Grid::DataBlock m_ProcessData;
    ifstream fp(fileName, ios::in | ios::binary);
    if (fp.bad())
    {
        std::cout << "Source file open error." << endl;
    }

    string filename;
    char byteArray[28] = {0};
    fp.read(byteArray, 28);


    vector<float> coordinate;
    float fl = 0;
    while (((int)fl) != 10000)
    {
        fp.read((char *)&fl, 4);
        if (((int)fl) != 10000)
        {
            fl = fl / 1000;
            coordinate.push_back(fl);
        }
    }


    char buffer[4];
    long count = 0;
    while (fp.read(buffer, 4))
    {
        int x = 0;
        int y = 0;
        int value = 0;
        fp.read((char *)&x, 4);
        fp.read((char *)&y, 4);
        fp.read((char *)&value, 4);
        int gridindex = 3000 * y + x;

        if (value > 14)
        {
            value = 0;
        }

        *(short *)&SAData->DataBlock.at(0).ProductData.at(gridindex * sizeof(short)) = value * 5;
        //                tempRaster[x][y] = value * 5;
    }

    SAData->GridInfo.ncolumn = 3000;
    SAData->GridInfo.dcolumn = 1000;
    SAData->GridInfo.nrow = 3000;
    SAData->GridInfo.drow = 1000;
    SAData->MapProjInfo.mapproj = 2;
    SAData->MapProjInfo.ctrlon = 119.0;
    SAData->MapProjInfo.ctrlat = 33.0;
    SAData->GridInfo.nz = 1;
    SAData->GridInfo.z.clear();
    SAData->GridInfo.z.push_back(0);
    //        char* str = "RadJw202007200348.00.37.dat";
    string aa(fileName);

    SAData->ProInfo.DataStartTime = time_convert(stoi(aa.substr(aa.length() - 22, 4)), stoi(aa.substr(aa.length() - 18, 2)), stoi(aa.substr(aa.length() - 16, 2)), stoi(aa.substr(aa.length() - 14, 2)), stoi(aa.substr(aa.length() - 12, 2)), 0);
    SAData->ProInfo.DataEndTime = SAData->ProInfo.DataStartTime;
    fp.close();
    return 0;
}

bool CNrietFileIO::IsRadarRawData(void *temp)
{
    WRADRAWDATA *data = (WRADRAWDATA *)temp;
    //WRADRAWDATA* i_pro = &data->at(0);

    if (data->commonBlock.genericheader.MagicNumber != 0x4D545352 && data->commonBlock.genericheader.MagicNumber != 0x4D545353)
    {
        //cout << "Not Radar Standard Data Format!" <<endl;
        return false;
    }

    if (data->commonBlock.genericheader.GenericType != 1)
    {
        //cout << "Not Radar Standard Data Format!" <<endl;
        return false;
    }

    return true;
}

bool CNrietFileIO::IsRadarKJCRawData(void *temp)
{
    WRADRAWDATA *data = (WRADRAWDATA *)temp;
    //WRADRAWDATA* i_pro = &data->at(0);

    if (data->commonBlock.genericheader.MagicNumber != 600562)
    {
        //cout << "Not Radar Standard Data Format!" <<endl;
        return false;
    }

    if (data->commonBlock.genericheader.GenericType != 1)
    {
        //cout << "Not Radar Standard Data Format!" <<endl;
        return false;
    }

    return true;
}

bool CNrietFileIO::IsFakeFile(char *filename)
{
    bool isCheck = false;
    // 使用 strrchr 函数在 filename 字符串中查找最后一个出现的点（.）字符
    char *ext = strrchr(filename, '.');
    if (ext != nullptr)
    {
        if (strncmp(".fake", ext, 5) == 0)
        {
            isCheck = true;
        }
    }
    //    ZlibFlag = isCheck;
    return isCheck;
}

bool CNrietFileIO::IsZlibFile(char *filename)
{
    bool isCheck = false;
    char *ext = strrchr(filename, '.');
    if (ext != nullptr)
    {
        if (strncmp(".gz", ext, 3) == 0)
        {
            isCheck = true;
        }
        if (strncmp(".Z", ext, 2) == 0)
        {
            isCheck = true;
        }
    }
    //    ZlibFlag = isCheck;
    return isCheck;
}

bool CNrietFileIO::IsBZ2File(char *filename)
{
    bool isCheck = false;
    char *ext = strrchr(filename, '.');
    if (ext != nullptr)
    {
        if (strncmp(".bz2", ext, 4) == 0)
        {
            isCheck = true;
        }
    }
    //    ZlibFlag = isCheck;
    return isCheck;
}

bool CNrietFileIO::SaveRadarRawData(void *temp, char *FileName)
{
    WRADRAWDATA *i_pro = (WRADRAWDATA *)temp;
    i_pro->commonBlock.genericheader.MagicNumber = 0x4D545352;
    try
    {
        ofstream fp(FileName, ios::out | ios::binary);
        fp.write((char *) & (i_pro->commonBlock.genericheader), sizeof(GENERICHEADER));
        fp.write((char *) & (i_pro->commonBlock.siteconfig), sizeof(SITECONFIG));
        fp.write((char *) & (i_pro->commonBlock.taskconfig), sizeof(TASKCONFIG));

        for (auto iter : i_pro->commonBlock.cutconfig)
        {
            fp.write((char *)&iter, sizeof(CUTCONFIG));
        }
        for (auto radail : i_pro->radials)
        {
            fp.write((char *)&radail.radialheader, sizeof(RADIALHEADER));
            for (auto moment : radail.momentblock)
            {
                fp.write((char *) & (moment.momentheader), sizeof(MOMENTHEADER));

                fp.write(&moment.momentdata.at(0), moment.momentdata.size());
            }
        }
        fp.close();
    }
    catch (...)
    {
        cout << "Save file error." << endl;
        return false;
    }

    return true;
}

bool CNrietFileIO::SaveZlibRadarRawDataBuf(void *source, Bytef *dest, uLongf *destLen)
{
    WRADRAWDATA *i_pro = (WRADRAWDATA *)source;

    //    Bytef * temp = new Bytef (sizeof (*i_pro));
    uLongf tempLen;

    *destLen = 0;
    i_pro->commonBlock.genericheader.MagicNumber = 0x4D545352;

    compress(dest + *destLen, &tempLen, (const Bytef *) & (i_pro->commonBlock.genericheader), sizeof(GENERICHEADER));
    *destLen += tempLen;
    compress(dest + *destLen, &tempLen, (const Bytef *) & (i_pro->commonBlock.genericheader), sizeof(GENERICHEADER));
    *destLen += tempLen;
    compress(dest + *destLen, &tempLen, (const Bytef *) & (i_pro->commonBlock.siteconfig), sizeof(SITECONFIG));
    *destLen += tempLen;
    compress(dest + *destLen, &tempLen, (const Bytef *) & (i_pro->commonBlock.taskconfig), sizeof(TASKCONFIG));
    *destLen += tempLen;

    for (auto iter : i_pro->commonBlock.cutconfig)
    {

        compress(dest + *destLen, &tempLen, (const Bytef *)&iter, sizeof(CUTCONFIG));
        *destLen += tempLen;
    }
    for (auto radail : i_pro->radials)
    {
        compress(dest + *destLen, &tempLen, (const Bytef *)&radail.radialheader, sizeof(RADIALHEADER));
        *destLen += tempLen;
        for (auto moment : radail.momentblock)
        {
            compress(dest + *destLen, &tempLen, (const Bytef *) & (moment.momentheader), sizeof(MOMENTHEADER));
            *destLen += tempLen;
            compress(dest + *destLen, &tempLen, (const Bytef *)&moment.momentdata.at(0), moment.momentdata.size());
            *destLen += tempLen;
        }
    }

    return true;
}

bool CNrietFileIO::SaveZlibRadarQCData(void *temp, char *FileName)
{
    WRADRAWDATA *i_pro = (WRADRAWDATA *)temp;
    i_pro->commonBlock.genericheader.MagicNumber = 0x4D545352;

    try
    {
        gzFile l_File;
        l_File = gzopen(FileName, "wb");
        gzwrite(l_File, (char *) & (i_pro->commonBlock.genericheader), sizeof(GENERICHEADER));
        gzwrite(l_File, (char *) & (i_pro->commonBlock.siteconfig), sizeof(SITECONFIG));
        gzwrite(l_File, (char *) & (i_pro->commonBlock.taskconfig), sizeof(TASKCONFIG));

        for (auto iter : i_pro->commonBlock.cutconfig)
        {
            gzwrite(l_File, (char *)&iter, sizeof(CUTCONFIG));
        }

        // data
        for (auto iter : i_pro->radials)
        {
            if (iter.radialheader.RadialState == 4 || iter.radialheader.RadialState == 6)
            {
                iter.radialheader.RadialState = 1;
            }
        }
        if (i_pro->commonBlock.taskconfig.ScanType == 2)
        {
            i_pro->radials.back().radialheader.RadialState = 6;
        }
        else
        {
            i_pro->radials.back().radialheader.RadialState = 4;
        }
        for (auto radail : i_pro->radials)
        {
            gzwrite(l_File, (char *)&radail.radialheader, sizeof(RADIALHEADERPAR));
            for (auto moment : radail.momentblock)
            {
                gzwrite(l_File, (char *) & (moment.momentheader), sizeof(MOMENTHEADER));
                gzwrite(l_File, &moment.momentdata.at(0), moment.momentdata.size());
            }
        }
        gzclose(l_File);
    }
    catch (...)
    {
        cout << "Save file error." << endl;
        return false;
    }

    return true;
}

bool CNrietFileIO::SaveZlibRadarRawData(void *temp, char *FileName)
{
    WRADRAWDATA *i_pro = (WRADRAWDATA *)temp;
    i_pro->commonBlock.genericheader.MagicNumber = 0x4D545352;
    try
    {
        gzFile l_File;
        l_File = gzopen(FileName, "wb");
        gzwrite(l_File, (char *) & (i_pro->commonBlock.genericheader), sizeof(GENERICHEADER));
        gzwrite(l_File, (char *) & (i_pro->commonBlock.siteconfig), sizeof(SITECONFIG));
        gzwrite(l_File, (char *) & (i_pro->commonBlock.taskconfig), sizeof(TASKCONFIG));

        for (auto iter : i_pro->commonBlock.cutconfig)
        {
            gzwrite(l_File, (char *)&iter, sizeof(CUTCONFIG));
        }
        for (auto radail : i_pro->radials)
        {
            gzwrite(l_File, (char *)&radail.radialheader, sizeof(RADIALHEADER));
            for (auto moment : radail.momentblock)
            {
                gzwrite(l_File, (char *) & (moment.momentheader), sizeof(MOMENTHEADER));

                gzwrite(l_File, &moment.momentdata.at(0), moment.momentdata.size());
            }
        }
        gzclose(l_File);
    }
    catch (...)
    {
        cout << "Save file error." << endl;
        return false;
    }

    return true;
}


bool CNrietFileIO::SaveZlibRadarKJCRawData(void *temp, char *FileName)
{
    WRADRAWDATA *i_pro = (WRADRAWDATA *)temp;
    i_pro->commonBlock.genericheader.MagicNumber = 600562;
    try
    {
        gzFile l_File;
        l_File = gzopen(FileName, "wb");
        gzwrite(l_File, (char *) & (i_pro->commonBlock.genericheader), sizeof(GENERICHEADER));
        gzwrite(l_File, (char *) & (i_pro->commonBlock.siteconfig), sizeof(SITECONFIG));
        gzwrite(l_File, (char *) & (i_pro->commonBlock.taskconfig), sizeof(TASKCONFIG));

        for (auto iter : i_pro->commonBlock.cutconfig)
        {
            gzwrite(l_File, (char *)&iter, sizeof(CUTCONFIG));
        }
        for (auto radail : i_pro->radials)
        {
            gzwrite(l_File, (char *)&radail.radialheader, sizeof(RADIALHEADER));
            for (auto moment : radail.momentblock)
            {
                gzwrite(l_File, (char *) & (moment.momentheader), sizeof(MOMENTHEADER));

                gzwrite(l_File, &moment.momentdata.at(0), moment.momentdata.size());
            }
        }

        gzwrite(l_File, (char *) & (i_pro->commonBlockPAR.genericheader), sizeof(GENERICHEADER));
        gzwrite(l_File, (char *) & (i_pro->commonBlockPAR.siteconfig), sizeof(SITECONFIGPAR));
        gzwrite(l_File, (char *) & (i_pro->commonBlockPAR.taskconfig), sizeof(TASKCONFIGPAR));
        for (auto iter : i_pro->commonBlockPAR.beamconfig)
        {
            gzwrite(l_File, (char *)&iter, sizeof(BEAMCONFIGPAR));
        }

        for (auto iter : i_pro->commonBlockPAR.cutconfig)
        {
            gzwrite(l_File, (char *)&iter, sizeof(CUTCONFIGPAR));
        }


        for (auto radail : i_pro->radials)
        {
            gzwrite(l_File, (char *)&radail.radialheader, sizeof(RADIALHEADER));
            for (auto moment : radail.momentblock)
            {
                gzwrite(l_File, (char *) & (moment.momentheader), sizeof(MOMENTHEADER));

                gzwrite(l_File, &moment.momentdata.at(0), moment.momentdata.size());
            }
        }
        gzclose(l_File);
    }
    catch (...)
    {
        cout << "Save file error." << endl;
        return false;
    }

    return true;
}


bool CNrietFileIO::SaveBZ2RadarRawData(void *temp, char *FileName)
{
    WRADRAWDATA *i_pro = (WRADRAWDATA *)temp;
    i_pro->commonBlock.genericheader.MagicNumber = 0x4D545352;
    try
    {
        int bzstatus;
        FILE *fp = fopen(FileName, "wb");
        if (fp == nullptr)
        {
            cout << "Target file open error." << endl;
            return false;
        }
        const int BLOCK_MULTIPLIER = 7;
        BZFILE *bzFp = BZ2_bzWriteOpen(&bzstatus, fp, BLOCK_MULTIPLIER, 0, 0);
        if (bzstatus < BZ_OK)
        {
            BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
            fclose(fp);
            cout << "Target file open error." << endl;
            return false;
        }

        BZ2_bzWrite(&bzstatus, fp, (char *) & (i_pro->commonBlock.genericheader), sizeof(GENERICHEADER));
        if (bzstatus < BZ_OK)
        {
            BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
            fclose(fp);
            cout << "Target file write error." << endl;
            return false;
        }
        BZ2_bzWrite(&bzstatus, fp, (char *) & (i_pro->commonBlock.siteconfig), sizeof(SITECONFIG));
        if (bzstatus < BZ_OK)
        {
            BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
            fclose(fp);
            cout << "Target file write error." << endl;
            return false;
        }
        BZ2_bzWrite(&bzstatus, fp, (char *) & (i_pro->commonBlock.taskconfig), sizeof(TASKCONFIG));
        if (bzstatus < BZ_OK)
        {
            BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
            fclose(fp);
            cout << "Target file write error." << endl;
            return false;
        }

        for (auto iter : i_pro->commonBlock.cutconfig)
        {
            BZ2_bzWrite(&bzstatus, fp, (char *)&iter, sizeof(CUTCONFIG));
            if (bzstatus < BZ_OK)
            {
                BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
                fclose(fp);
                cout << "Target file write error." << endl;
                return false;
            }
        }
        for (auto radail : i_pro->radials)
        {
            BZ2_bzWrite(&bzstatus, fp, (char *)&radail.radialheader, sizeof(RADIALHEADER));
            if (bzstatus < BZ_OK)
            {
                BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
                fclose(fp);
                cout << "Target file write error." << endl;
                return false;
            }
            for (auto moment : radail.momentblock)
            {
                BZ2_bzWrite(&bzstatus, fp, (char *) & (moment.momentheader), sizeof(MOMENTHEADER));
                if (bzstatus < BZ_OK)
                {
                    BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
                    fclose(fp);
                    cout << "Target file write error." << endl;
                    return false;
                }
                BZ2_bzWrite(&bzstatus, fp, &moment.momentdata.at(0), moment.momentdata.size());
                if (bzstatus < BZ_OK)
                {
                    BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
                    fclose(fp);
                    cout << "Target file write error." << endl;
                    return false;
                }
            }
        }
        BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
        fclose(fp);
    }
    catch (...)
    {
        cout << "Save file error." << endl;
        return false;
    }

    return true;
}

bool CNrietFileIO::SaveBZ2RadarKJCRawData(void *temp, char *FileName)
{
    WRADRAWDATA *i_pro = (WRADRAWDATA *)temp;
    i_pro->commonBlock.genericheader.MagicNumber = 600562;
    try
    {
        int bzstatus;
        FILE *fp = fopen(FileName, "wb");
        if (fp == nullptr)
        {
            cout << "Target file open error." << endl;
            return false;
        }
        const int BLOCK_MULTIPLIER = 7;
        BZFILE *bzFp = BZ2_bzWriteOpen(&bzstatus, fp, BLOCK_MULTIPLIER, 0, 0);
        if (bzstatus < BZ_OK)
        {
            BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
            fclose(fp);
            cout << "Target file open error." << endl;
            return false;
        }

        BZ2_bzWrite(&bzstatus, fp, (char *) & (i_pro->commonBlock.genericheader), sizeof(GENERICHEADER));
        if (bzstatus < BZ_OK)
        {
            BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
            fclose(fp);
            cout << "Target file write error." << endl;
            return false;
        }
        BZ2_bzWrite(&bzstatus, fp, (char *) & (i_pro->commonBlock.siteconfig), sizeof(SITECONFIG));
        if (bzstatus < BZ_OK)
        {
            BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
            fclose(fp);
            cout << "Target file write error." << endl;
            return false;
        }
        BZ2_bzWrite(&bzstatus, fp, (char *) & (i_pro->commonBlock.taskconfig), sizeof(TASKCONFIG));
        if (bzstatus < BZ_OK)
        {
            BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
            fclose(fp);
            cout << "Target file write error." << endl;
            return false;
        }

        for (auto iter : i_pro->commonBlock.cutconfig)
        {
            BZ2_bzWrite(&bzstatus, fp, (char *)&iter, sizeof(CUTCONFIG));
            if (bzstatus < BZ_OK)
            {
                BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
                fclose(fp);
                cout << "Target file write error." << endl;
                return false;
            }
        }


        BZ2_bzWrite(&bzstatus, fp, (char *) & (i_pro->commonBlockPAR.genericheader), sizeof(GENERICHEADER));
        if (bzstatus < BZ_OK)
        {
            BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
            fclose(fp);
            cout << "Target file write error." << endl;
            return false;
        }
        BZ2_bzWrite(&bzstatus, fp, (char *) & (i_pro->commonBlockPAR.siteconfig), sizeof(SITECONFIGPAR));
        if (bzstatus < BZ_OK)
        {
            BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
            fclose(fp);
            cout << "Target file write error." << endl;
            return false;
        }
        BZ2_bzWrite(&bzstatus, fp, (char *) & (i_pro->commonBlockPAR.taskconfig), sizeof(TASKCONFIGPAR));
        if (bzstatus < BZ_OK)
        {
            BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
            fclose(fp);
            cout << "Target file write error." << endl;
            return false;
        }
        for (auto iter : i_pro->commonBlockPAR.beamconfig)
        {
            BZ2_bzWrite(&bzstatus, fp, (char *)&iter, sizeof(BEAMCONFIGPAR));
            if (bzstatus < BZ_OK)
            {
                BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
                fclose(fp);
                cout << "Target file write error." << endl;
                return false;
            }
        }

        for (auto iter : i_pro->commonBlockPAR.cutconfig)
        {
            BZ2_bzWrite(&bzstatus, fp, (char *)&iter, sizeof(CUTCONFIGPAR));
            if (bzstatus < BZ_OK)
            {
                BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
                fclose(fp);
                cout << "Target file write error." << endl;
                return false;
            }
        }


        for (auto radail : i_pro->radials)
        {
            BZ2_bzWrite(&bzstatus, fp, (char *)&radail.radialheader, sizeof(RADIALHEADER));
            if (bzstatus < BZ_OK)
            {
                BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
                fclose(fp);
                cout << "Target file write error." << endl;
                return false;
            }
            for (auto moment : radail.momentblock)
            {
                BZ2_bzWrite(&bzstatus, fp, (char *) & (moment.momentheader), sizeof(MOMENTHEADER));
                if (bzstatus < BZ_OK)
                {
                    BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
                    fclose(fp);
                    cout << "Target file write error." << endl;
                    return false;
                }
                BZ2_bzWrite(&bzstatus, fp, &moment.momentdata.at(0), moment.momentdata.size());
                if (bzstatus < BZ_OK)
                {
                    BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
                    fclose(fp);
                    cout << "Target file write error." << endl;
                    return false;
                }
            }
        }
        BZ2_bzWriteClose(&bzstatus, bzFp, 0, NULL, NULL);
        fclose(fp);
    }
    catch (...)
    {
        cout << "Save file error." << endl;
        return false;
    }

    return true;
}

bool CNrietFileIO::IsRadarProData(void *temp)
{
    WRADPRODATA *i_pro = (WRADPRODATA *)temp;
    //WRADPRODATA* i_pro = &data->at(0);

    if (i_pro->commonBlock.genericheader.MagicNumber != 0x4D545352 && i_pro->commonBlock.genericheader.MagicNumber != 0x4D545353)
    {
        //        if(m_DebugLevel <= 3){
        //            cout << "Not Radar Standard Product Format!" <<endl;
        //        }
        return false;
    }

    if (i_pro->commonBlock.genericheader.GenericType != 2)
    {
        //        if(m_DebugLevel <= 3){
        //            cout << "Not Radar Standard Product Format!" <<endl;
        //        }
        return false;
    }

    return true;
}

bool CNrietFileIO::IsRadarKJCProData(void *temp)
{
    WRADPRODATA *i_pro = (WRADPRODATA *)temp;
    //WRADPRODATA* i_pro = &data->at(0);

    if (i_pro->commonBlock.genericheader.MagicNumber != 600562)
    {
        //        if(m_DebugLevel <= 3){
        //            cout << "Not Radar Standard Product Format!" <<endl;
        //        }
        return false;
    }

    if (i_pro->commonBlock.genericheader.GenericType != 2)
    {
        //        if(m_DebugLevel <= 3){
        //            cout << "Not Radar Standard Product Format!" <<endl;
        //        }
        return false;
    }

    return true;
}

bool CNrietFileIO::SaveRadarProData(void *temp, char *FileName)
{
    WRADPRODATA *i_pro = (WRADPRODATA *)temp;
    i_pro->commonBlock.genericheader.MagicNumber = 0x4D545352;
    try
    {
        ofstream fp(FileName, ios::out | ios::binary);
        fp.write((char *) & (i_pro->commonBlock.genericheader), sizeof(GENERICHEADER));
        fp.write((char *) & (i_pro->commonBlock.siteconfig), sizeof(SITECONFIG));
        fp.write((char *) & (i_pro->commonBlock.taskconfig), sizeof(TASKCONFIG));

        for (auto iter : i_pro->commonBlock.cutconfig)
        {
            fp.write((char *)&iter, sizeof(CUTCONFIG));
        }

        fp.write((char *) & (i_pro->productheader), sizeof(PRODUCTHEADERBLOCK));
        fp.write(&i_pro->dataBlock.at(0), i_pro->dataBlock.size());

        fp.close();
    }
    catch (...)
    {
        cout << "Save file error." << endl;
        return false;
    }

    //write an empty file to record the data end time of every single cut data.
    if (i_pro->productheader.productheader.ProductType == PTYPE_PPI && i_pro->productheader.productheader.DataType1 == 2)
    {
        string FileDir;
        string FileName;
        char *SiteName = i_pro->commonBlock.siteconfig.SiteCode;
        char *SiteCode = i_pro->commonBlock.siteconfig.SiteCode;
        time_t pro_time_t = i_pro->commonBlock.taskconfig.ScanStartTime;
        tm pro_tm = *(gmtime(&pro_time_t));
        char yyyymmddhhmmss[16] = {0};
        sprintf(&yyyymmddhhmmss[0], "%4.4d", pro_tm.tm_year + 1900);
        sprintf(&yyyymmddhhmmss[4], "%2.2d", pro_tm.tm_mon + 1);
        sprintf(&yyyymmddhhmmss[6], "%2.2d", pro_tm.tm_mday);
        sprintf(&yyyymmddhhmmss[8], "%2.2d", pro_tm.tm_hour);
        sprintf(&yyyymmddhhmmss[10], "%2.2d", pro_tm.tm_min);
        sprintf(&yyyymmddhhmmss[12], "%2.2d", pro_tm.tm_sec);
        char yyyymmdd[16] = {0};
        strncpy(yyyymmdd, yyyymmddhhmmss, 8);
        time_t pro_endtime_t = i_pro->productheader.productheader.DataEndTime;
        tm pro_endtm = *(gmtime(&pro_endtime_t));
        char endyyyymmddhhmmss[16] = {0};
        sprintf(&endyyyymmddhhmmss[0], "%4.4d", pro_endtm.tm_year + 1900);
        sprintf(&endyyyymmddhhmmss[4], "%2.2d", pro_endtm.tm_mon + 1);
        sprintf(&endyyyymmddhhmmss[6], "%2.2d", pro_endtm.tm_mday);
        sprintf(&endyyyymmddhhmmss[8], "%2.2d", pro_endtm.tm_hour);
        sprintf(&endyyyymmddhhmmss[10], "%2.2d", pro_endtm.tm_min);
        sprintf(&endyyyymmddhhmmss[12], "%2.2d", pro_endtm.tm_sec);
        string Proname = "PPI";
        char Elevation[8] = {0}; // Unit:0.1 degree
        sprintf(Elevation, "%d", (int)(i_pro->productheader.productdependentparameter.ppiparameter.Elevation * 10));
        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(yyyymmddhhmmss) + "_" + string(endyyyymmddhhmmss) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
        FileDir = string(SiteName) + "/" + string(yyyymmdd) + "/" + Proname + "/";
        string temp_FileName = FileDir + FileName;
        ofstream fp(temp_FileName.c_str(), ios::out | ios::binary);
        fp.close();
    }

    return true;
}

bool CNrietFileIO::GetRadarProDrawData(void *indata_temp, void *outdata_temp, void *mapinfo_temp, void *gridinfo_temp, void *invalid)
{
    WRADPRODATA *i_pro = (WRADPRODATA *)indata_temp;
    vector<vector<float>> *outdata = (vector<vector<float>> *) outdata_temp;
    vector<vector<float>>().swap(*outdata);
    s_Pro_Grid::MapProjectionParameters *mapinfo = (s_Pro_Grid::MapProjectionParameters *) mapinfo_temp;
    s_Pro_Grid::GridParameters *gridinfo = (s_Pro_Grid::GridParameters *) gridinfo_temp;
    *(float *)invalid = -9999;
    switch (i_pro->productheader.productheader.ProductType)
    {
        case PTYPE_PPI: // 1://PPI
        {
            RADIALFORMAT databloack;
            long long i_shift = 0;
            memcpy(&databloack.RadialHeader, &i_pro->dataBlock.at(i_shift), sizeof(RADIALHEADERBLOCK));
            i_shift += sizeof(RADIALHEADERBLOCK);
            databloack.RadialData.resize(databloack.RadialHeader.NumOfRadials);
            for (int i_Radial = 0; i_Radial < databloack.RadialHeader.NumOfRadials; i_Radial++)
            {
                memcpy(&databloack.RadialData.at(i_Radial).RadialDataHead, &i_pro->dataBlock.at(i_shift), sizeof(RADIALDATAHEADERBLOCK));
                i_shift += sizeof(RADIALDATAHEADERBLOCK);
                int RadialDataDataLength = databloack.RadialData.at(i_Radial).RadialDataHead.NumOfBins * databloack.RadialHeader.BinLength;
                databloack.RadialData.at(i_Radial).RadialDataData.Data.resize(RadialDataDataLength);
                memcpy(&databloack.RadialData.at(i_Radial).RadialDataData.Data.front(), &i_pro->dataBlock.at(i_shift), RadialDataDataLength);
                i_shift += RadialDataDataLength;

            }

            int detecklength = i_pro->commonBlock.cutconfig.front().MaximumRange1;
            int gatelength;
            if (i_pro->productheader.productheader.DataType1 == 3 || i_pro->productheader.productheader.DataType1 == 4)
            {
                gatelength = i_pro->commonBlock.cutconfig.front().LogResolution;
            }
            else
            {
                gatelength = i_pro->commonBlock.cutconfig.front().DopplerResolution;
            }

            gridinfo->nz = 1;
            gridinfo->drow = 50;   //X
            gridinfo->dcolumn = 50;  //Y
            gridinfo->nrow = (unsigned short)ceil(detecklength * 2 / gridinfo->drow);
            gridinfo->nrow = gridinfo->nrow / 2 * 2 + 1;
            gridinfo->ncolumn = (unsigned short)ceil(detecklength * 2 / gridinfo->dcolumn);
            gridinfo->ncolumn = gridinfo->ncolumn / 2 * 2 + 1;
            mapinfo->mapproj = 2;
            mapinfo->ctrlat = i_pro->commonBlock.siteconfig.Latitude;
            mapinfo->ctrlon = i_pro->commonBlock.siteconfig.Longitude;
            outdata->resize(1);
            outdata->front().resize(gridinfo->nrow * gridinfo->ncolumn);
            outdata->front().assign(gridinfo->nrow * gridinfo->ncolumn, *(float *)invalid);

#ifndef ALGORITHM_DEBUG_FILE_IO
            #pragma omp parallel for
#endif
            for (int iy = 0; iy < gridinfo->ncolumn; iy++)
            {
                for (int ix = 0; ix < gridinfo->nrow; ix++)
                {
                    int dx = gridinfo->drow * (ix - gridinfo->nrow / 2);
                    int dy = gridinfo->dcolumn * (iy - gridinfo->ncolumn / 2) * -1;
                    float dis = pow(pow(dx, 2) + pow(dy, 2), 0.5);
                    if (dis > detecklength)
                    {
                        continue;
                    }
                    float az = atan2(dx, dy);
                    az = az / PI * 180;
                    if (az < 0)
                    {
                        az += 360;
                    }
                    float diff_az = i_pro->commonBlock.cutconfig.front().AngularResolution / 1.9;
                    int radialindex = -1;
                    size_t count = databloack.RadialData.size();
                    for (int i_radial = 0; i_radial < count; i_radial++)
                    {
                        if (fabs(az - databloack.RadialData.at(i_radial).RadialDataHead.StartAngle) < diff_az)
                        {
                            diff_az = fabs(az - databloack.RadialData.at(i_radial).RadialDataHead.StartAngle);
                            radialindex = i_radial;
                            break;
                        }
                    }
                    if (radialindex == -1)
                    {
                        continue;
                    }
                    int gateindex = round(dis / gatelength - 1);
                    if (gateindex < 0 || gateindex >= databloack.RadialData.front().RadialDataHead.NumOfBins)
                    {
                        continue;
                    }
                    unsigned short temp_data = *(unsigned short *)&databloack.RadialData.at(radialindex).RadialDataData.Data.at(gateindex * databloack.RadialHeader.BinLength);
                    if (temp_data > INVALID_RSV)
                    {
                        outdata->front().at(iy * gridinfo->nrow + ix) = (temp_data - databloack.RadialHeader.Offset) / databloack.RadialHeader.Scale;
                    }
                }
            }
            return true;
        }
        break;
        case PTYPE_RHI: // 2://RHI
            break;
        case PTYPE_CAPPI: // 3://CAPPI //格点
            break;
        case PTYPE_MAX: //MAX //格点
            break;
        case PTYPE_ET://ET //格点
            break;
        case PTYPE_EB://EB //格点
            break;
        case PTYPE_VIL://VIL //格点
            break;
        case PTYPE_OHP://OHP
            break;
        case PTYPE_PolarOHP://OHP
            break;
        case PTYPE_THP://THP
            break;
        case PTYPE_USP://USP
            break;
        case PTYPE_VAD://VAD
            break;
        case PTYPE_VWP://VWP
            break;
        case PTYPE_STI://STI
            break;
        case PTYPE_HI://HI
            break;
        case PTYPE_M://MESO
            break;
        case PTYPE_TVS://TVS
            break;
        case PTYPE_SS://SS
            break;
        case PTYPE_QPE:
            break;
        case PTYPE_PolarQPE:
            break;
        case PTYPE_HCL: // 51://HCL //MRADIAL
            break;
        default:
            break;
    }
    return false;
}

bool CNrietFileIO::SaveZlibRadarProDataBuf(void *source, Bytef *dest, uLongf *destLen)
{
    WRADPRODATA *i_pro = (WRADPRODATA *)source;
    uLongf tempLen;
    *destLen = 0;
    i_pro->commonBlock.genericheader.MagicNumber = 0x4D545352;

    compress(dest + *destLen, &tempLen, (const Bytef *) & (i_pro->commonBlock.genericheader), sizeof(GENERICHEADER));
    *destLen += tempLen;
    compress(dest + *destLen, &tempLen, (const Bytef *) & (i_pro->commonBlock.siteconfig), sizeof(SITECONFIG));
    *destLen += tempLen;
    compress(dest + *destLen, &tempLen, (const Bytef *) & (i_pro->commonBlock.taskconfig), sizeof(TASKCONFIG));
    *destLen += tempLen;

    for (auto iter : i_pro->commonBlock.cutconfig)
    {
        compress(dest + *destLen, &tempLen, (const Bytef *)&iter, sizeof(CUTCONFIG));
        *destLen += tempLen;
    }

    compress(dest + *destLen, &tempLen, (const Bytef *) & (i_pro->productheader), sizeof(PRODUCTHEADERBLOCK));
    *destLen += tempLen;
    compress(dest + *destLen, &tempLen, (const Bytef *)&i_pro->dataBlock.at(0), i_pro->dataBlock.size());
    *destLen += tempLen;

    return true;
}

bool CNrietFileIO::SaveZlibRadarProData(void *temp, char *FileName)
{
    WRADPRODATA *i_pro = (WRADPRODATA *)temp;
    i_pro->commonBlock.genericheader.MagicNumber = 0x4D545352;
    try
    {
        gzFile l_File;
        l_File = gzopen(FileName, "wb");
        gzwrite(l_File, (char *) & (i_pro->commonBlock.genericheader), sizeof(GENERICHEADER));
        gzwrite(l_File, (char *) & (i_pro->commonBlock.siteconfig), sizeof(SITECONFIG));
        gzwrite(l_File, (char *) & (i_pro->commonBlock.taskconfig), sizeof(TASKCONFIG));

        for (auto iter : i_pro->commonBlock.cutconfig)
        {
            gzwrite(l_File, (char *)&iter, sizeof(CUTCONFIG));
        }

        gzwrite(l_File, (char *) & (i_pro->productheader), sizeof(PRODUCTHEADERBLOCK));
        gzwrite(l_File, &i_pro->dataBlock.at(0), i_pro->dataBlock.size());

        gzclose(l_File);
    }
    catch (...)
    {
        cout << "Save file error." << endl;
        return false;
    }

    return true;
}

bool CNrietFileIO::SaveRadarKJCProData(void *temp, char *FileName)
{
    WRADPRODATA *i_pro = (WRADPRODATA *)temp;
    try
    {
        ofstream fp(FileName, ios::out | ios::binary);

        fp.write((char *) & (i_pro->commonBlockPAR.genericheader), sizeof(GENERICHEADER));
        fp.write((char *) & (i_pro->commonBlockPAR.siteconfig), sizeof(SITECONFIGPAR));
        fp.write((char *) & (i_pro->commonBlockPAR.taskconfig), sizeof(TASKCONFIGPAR));
        for (auto iter : i_pro->commonBlockPAR.beamconfig)
        {
            fp.write((char *)&iter, sizeof(BEAMCONFIGPAR));
        }
        for (auto iter : i_pro->commonBlockPAR.cutconfig)
        {
            fp.write((char *)&iter, sizeof(CUTCONFIGPAR));
        }

        fp.write((char *) & (i_pro->productheader), sizeof(PRODUCTHEADERBLOCK));
        fp.write(&i_pro->dataBlock.at(0), i_pro->dataBlock.size());

        fp.close();


    }
    catch (...)
    {
        cout << "Save file error." << endl;
        return false;
    }

    return true;

}

bool CNrietFileIO::SaveZlibRadarKJCProData(void *temp, char *FileName)
{
    WRADPRODATA *i_pro = (WRADPRODATA *)temp;
    i_pro->commonBlockPAR.genericheader.GenericType = i_pro->commonBlock.genericheader.GenericType;
    try
    {
        QString i_tmp_name;
        i_tmp_name = QString::fromStdString(string(FileName));
        auto strlist = i_tmp_name.split("/");
        if (strlist.size() < 8)
        {
            return false;
        }
        string proname = strlist.at(6).toStdString();

        gzFile l_File;
        l_File = gzopen(FileName, "wb");

        if (proname == "PPIDBT")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_PPIDBT;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_PPIDBT;
        }
        else if (proname == "PPIDBZ")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_PPIDBZ;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_PPIDBZ;
        }
        else if (proname == "PPIV")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_PPIV;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_PPIV;
        }
        else if (proname == "PPISW")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_PPISW;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_PPISW;
        }
        else if (proname == "RHIDBT")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_RHIDBT;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_RHIDBT;
        }
        else if (proname == "RHIDBZ")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_RHIDBZ;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_RHIDBZ;
        }
        else if (proname == "RHIV")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_RHIV;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_RHIV;
        }
        else if (proname == "RHISW")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_RHISW;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_RHISW;
        }
        else if (proname == "CAPPIDBZ")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_CAPPIDBZ;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_CAPPIDBZ;
        }
        else if (proname == "CAPPIDBT")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_CAPPIDBT;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_CAPPIDBT;
        }
        else if (proname == "CAPPIV")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_CAPPIV;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_CAPPIV;
        }
        else if (proname == "CAPPISW")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_CAPPISW;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_CAPPISW;
        }
        else if (proname == "CAPPICR")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_CR;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_CR;
        }
        else if (proname == "ZR")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_ZR;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_ZR;
        }
        else if (proname == "ET")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_ET;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_ET;
        }
        else if (proname == "EB")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_EB;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_EB;
        }
        else if (proname == "VIL")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_VIL;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_VIL;
        }
        else if (proname == "CR")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_CR;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_CR;
        }
        else if (proname == "RVD")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_RVD;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_RVD;
        }
        else if (proname == "ARD")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_ARD;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_ARD;
        }
        else if (proname == "CS")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_CS;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_CS;
        }
        else if (proname == "MAX")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_MAX;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_MAX;
        }
        else if (proname == "WER")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_WER;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_WER;
        }
        else if (proname == "LTA")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_LTA;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_LTA;
        }
        else if (proname == "SWP")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_SWP;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_SWP;
        }
        else if (proname == "OHP")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_OHP;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_OHP;
        }
        else if (proname == "USP")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_USP;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_USP;
        }
        else if (proname == "VWP")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_VWP;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_VWP;
        }
        else if (proname == "VAD")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_VAD;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_VAD;
        }
        else if (proname == "EDWF")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_EDWF;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_EDWF;
        }
        else if (proname == "SS")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_SS;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_SS;
        }
        else if (proname == "GFI")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_GFI;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_GFI;
        }
        else if (proname == "HI")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_HI;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_HI;
        }
        else if (proname == "DBI")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_DBI;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_DBI;
        }
        else if (proname == "M")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_M;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_M;
        }
        else if (proname == "RS")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_RS;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_RS;
        }
        else if (proname == "TVS")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_TVS;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_TVS;
        }
        else if (proname == "STI")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_STI;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_STI;
        }
        else if (proname == "SAT")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_SAT;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_SAT;
        }
        else if (proname == "ACC")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_ACC;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_ACC;
        }
        else if (proname == "LGT")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_LGT;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_LGT;
        }
        else if (proname == "EXP")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_EXP;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_EXP;
        }
        else if (proname == "EV")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_EV;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_EV;
        }
        else if (proname == "SRM")
        {
            i_pro->productheader.productheader.ProductType = KJC::PTYPE_SRM;
            i_pro->commonBlockPAR.genericheader.ProductType = KJC::PTYPE_SRM;
        }
        else
        {
            i_pro->productheader.productheader.ProductType = -1;
        }

        gzwrite(l_File, (char *) & (i_pro->commonBlockPAR.genericheader), sizeof(GENERICHEADER));
        gzwrite(l_File, (char *) & (i_pro->commonBlockPAR.siteconfig), sizeof(SITECONFIGPAR));
        gzwrite(l_File, (char *) & (i_pro->commonBlockPAR.taskconfig), sizeof(TASKCONFIGPAR));
        for (auto iter : i_pro->commonBlockPAR.beamconfig)
        {
            gzwrite(l_File, (char *)&iter, sizeof(BEAMCONFIGPAR));
        }
        for (auto iter : i_pro->commonBlockPAR.cutconfig)
        {
            gzwrite(l_File, (char *)&iter, sizeof(CUTCONFIGPAR));
        }

        gzwrite(l_File, (char *) & (i_pro->productheader), sizeof(PRODUCTHEADERBLOCK));
        gzwrite(l_File, &i_pro->dataBlock.at(0), i_pro->dataBlock.size());

        gzclose(l_File);
    }
    catch (...)
    {
        cout << "Save file error." << endl;
        return false;
    }

    return true;

}

bool CNrietFileIO::IsRadarLatlonData(void *temp)
{
    s_Pro_Grid::RadarProduct *i_pro = (s_Pro_Grid::RadarProduct *)temp;
    if (i_pro->ProInfo.MagicNumber != 0x45673210 && i_pro->ProInfo.MagicNumber != 0x45673211)
    {
        if (m_DebugLevel <= 0)
        {
            cout << "Not Radar Grid Product Format!" << endl;
        }
        return false;
    }
    return true;
}

bool CNrietFileIO::SaveRadarLatlonData(void *temp, char *FileName)
{
    s_Pro_Grid::RadarProduct *i_pro = (s_Pro_Grid::RadarProduct *)temp;
    LLDF_FORMAT ll_temp;
    if (i_pro->ProInfo.ProductionID == 220 || i_pro->ProInfo.ProductionID == 229)
    {
        ll_temp.data.resize(i_pro->GridInfo.nz * 3);
        for (int iz = 0; iz < i_pro->GridInfo.nz; iz++)
        {
            for (int ivar = 0 ; ivar < 3; ivar++)
            {
                strncpy(ll_temp.data[iz * 3 + ivar].header.dataname, i_pro->ProInfo.ProductionName, sizeof(ll_temp.data[iz * 3 + ivar].header.dataname) - 1); // CREF_FZ 文件信息
                strncpy(ll_temp.data[iz * 3 + ivar].header.varname, i_pro->DataBlock.at(ivar).ProDataInfo.VarName, sizeof(ll_temp.data[iz * 3 + ivar].header.varname) - 1); // CREF_FZ 文件信息;    // CREF 变量名称
                strncpy(ll_temp.data[iz * 3 + ivar].header.units, "m/s", sizeof(ll_temp.data[iz * 3 + ivar].header.units)); // dBZ 变量单位，默认dbz
                ll_temp.data[iz * 3 + ivar].header.label = 'L' >> 8 | 'L';
                ll_temp.data[iz * 3 + ivar].header.unitlen = 2;   // 2=short
                ll_temp.data[iz * 3 + ivar].header.nodata = INVALID_BT;     // -32 for radar
                ll_temp.data[iz * 3 + ivar].header.offset = i_pro->DataBlock.at(ivar).ProDataInfo.DOffset;
                ll_temp.data[iz * 3 + ivar].header.levelbytes = i_pro->DataBlock.at(ivar).ProductData.size() / i_pro->GridInfo.nz;	 // data bytes of per-level
                ll_temp.data[iz * 3 + ivar].header.levelnum = i_pro->GridInfo.nz * 3; // level numbers of data 文件内一共的层数
                ll_temp.data[iz * 3 + ivar].header.amp = i_pro->DataBlock.at(ivar).ProDataInfo.DScale;        // amplify factor = 10; 放大系数，dbz乘上放大系数后存储
                ll_temp.data[iz * 3 + ivar].header.compmode = 0;   // 0 = LatLon grid; 1=sparse LatLon grid
                ll_temp.data[iz * 3 + ivar].header.dates = 0; // UTC dates 日期
                ll_temp.data[iz * 3 + ivar].header.seconds = i_pro->ProInfo.ProductionTime;     // UTC seconds 秒
                ll_temp.data[iz * 3 + ivar].header.min_value = 0;   // used in compress mode
                ll_temp.data[iz * 3 + ivar].header.max_value = 0;   // used in compress mode
                ll_temp.data[iz * 3 + ivar].header.enablemultiLevel = 1;	 // 是否存储多层，0表示只有一层，1表示多层
                ll_temp.data[iz * 3 + ivar].header.height = i_pro->GridInfo.z.at(iz); //  or  forecast_time;
                if (iz == i_pro->GridInfo.nz - 1 && ivar == 2)
                {
                    ll_temp.data[iz * 3 + ivar].header.index_nextbytes = 0;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
                }
                else if (iz == 0 && ivar == 0)
                {
                    ll_temp.data[iz * 3 + ivar].header.index_nextbytes = sizeof(LLDF_HEADER) + ll_temp.data[iz * 3 + ivar].header.levelbytes;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
                }
                else
                {
                    ll_temp.data[iz * 3 + ivar].header.index_nextbytes = ll_temp.data[iz * 3 + ivar - 1].header.index_nextbytes + sizeof(LLDF_HEADER) + ll_temp.data[iz * 3 + ivar].header.levelbytes;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
                }

                //                ll_temp.data[iz*3+ivar].header.reserved[0] = 0;
                //                ll_temp.data[iz*3+ivar].header.reserved[1] = 0;

//                ll_temp.data[iz*3+ivar].header.domain.slat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn /50000.0 * (0 - i_pro->GridInfo.ncolumn/2);
//                ll_temp.data[iz*3+ivar].header.domain.wlon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow /50000.0 * (0 - i_pro->GridInfo.nrow/2);;  // 0.01 deg 西南角经纬度
//                ll_temp.data[iz*3+ivar].header.domain.nlat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn /50000.0 * (i_pro->GridInfo.ncolumn -1 - i_pro->GridInfo.ncolumn/2);
//                ll_temp.data[iz*3+ivar].header.domain.elon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow /50000.0 * (i_pro->GridInfo.nrow -1 - i_pro->GridInfo.nrow/2);;  // 0.01 deg 东北角经纬度
                ll_temp.data[iz * 3 + ivar].header.domain.slat = i_pro->MapProjInfo.ctrlat - i_pro->GridInfo.dcolumn * i_pro->GridInfo.ncolumn / 100000.0;
                ll_temp.data[iz * 3 + ivar].header.domain.nlat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn * i_pro->GridInfo.ncolumn / 100000.0;
                ll_temp.data[iz * 3 + ivar].header.domain.wlon = i_pro->MapProjInfo.ctrlon - i_pro->GridInfo.drow * i_pro->GridInfo.nrow / 100000.0; // 0.01 deg 西南角经纬度
                ll_temp.data[iz * 3 + ivar].header.domain.elon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow * i_pro->GridInfo.nrow / 100000.0; // 0.01 deg 东北角经纬度
                ll_temp.data[iz * 3 + ivar].header.domain.clat = i_pro->MapProjInfo.ctrlat;
                ll_temp.data[iz * 3 + ivar].header.domain.clon = i_pro->MapProjInfo.ctrlon; // 0.01 deg  中心经纬度

                ll_temp.data[iz * 3 + ivar].header.domain.dlat = i_pro->GridInfo.dcolumn / 50000.0;
                ll_temp.data[iz * 3 + ivar].header.domain.dlon = i_pro->GridInfo.drow / 50000.0; // minimize = 0.01 deg 经纬度单位间隔
                ll_temp.data[iz * 3 + ivar].data.resize(ll_temp.data[iz * 3 + ivar].header.levelbytes);

                //        ll_temp.data[iz*3+ivar].header.domain.rows = i_pro->GridInfo.nrow;
                //        ll_temp.data[iz*3+ivar].header.domain.cols = i_pro->GridInfo.ncolumn;  // 行列数
                //        memcpy(&ll_temp.data[iz*3+ivar].data.at(0),&i_pro->DataBlock.at(0).ProductData.at(iz*ll_temp.data[iz*3+ivar].header.levelbytes),ll_temp.data[iz*3+ivar].header.levelbytes);

                ll_temp.data[iz * 3 + ivar].header.domain.cols = i_pro->GridInfo.nrow;
                ll_temp.data[iz * 3 + ivar].header.domain.rows = i_pro->GridInfo.ncolumn; // 行列数
                for (int i = 0; i < ll_temp.data[iz * 3 + ivar].header.domain.rows; i++)
                {
                    int shift_org = (ll_temp.data[iz * 3 + ivar].header.domain.rows - 1 - i) * ll_temp.data[iz * 3 + ivar].header.domain.cols * ll_temp.data[iz * 3 + ivar].header.unitlen;
                    int shift = i * ll_temp.data[iz * 3 + ivar].header.domain.cols * ll_temp.data[iz * 3 + ivar].header.unitlen;
                    memcpy(&ll_temp.data[iz * 3 + ivar].data.at(shift), &i_pro->DataBlock.at(ivar).ProductData.at(iz * ll_temp.data[iz * 3 + ivar].header.levelbytes + shift_org), ll_temp.data[iz].header.domain.cols * ll_temp.data[iz].header.unitlen);
                }
            }
        }
    }
    else if (i_pro->ProInfo.ProductionID == 61)
    {
        ll_temp.data.resize(i_pro->GridInfo.nz * 2);
        for (int iz = 0; iz < i_pro->GridInfo.nz; iz++)
        {
            for (int ivar = 0 ; ivar < 2; ivar++)
            {
                strncpy(ll_temp.data[iz * 2 + ivar].header.dataname, i_pro->ProInfo.ProductionName, sizeof(ll_temp.data[iz * 2 + ivar].header.dataname) - 1); // CREF_FZ 文件信息
                strncpy(ll_temp.data[iz * 2 + ivar].header.varname, i_pro->DataBlock.at(ivar).ProDataInfo.VarName, sizeof(ll_temp.data[iz * 2 + ivar].header.varname) - 1); // CREF_FZ 文件信息;    // CREF 变量名称
                strncpy(ll_temp.data[iz * 2 + ivar].header.units, "m/s", sizeof(ll_temp.data[iz * 2 + ivar].header.units)); // dBZ 变量单位，默认dbz
                ll_temp.data[iz * 2 + ivar].header.label = 'L' >> 8 | 'L';
                ll_temp.data[iz * 2 + ivar].header.unitlen = 2;   // 2=short
                ll_temp.data[iz * 2 + ivar].header.nodata = INVALID_BT;     // -32 for radar
                ll_temp.data[iz * 2 + ivar].header.offset = i_pro->DataBlock.at(ivar).ProDataInfo.DOffset;
                ll_temp.data[iz * 2 + ivar].header.levelbytes = i_pro->DataBlock.at(ivar).ProductData.size() / i_pro->GridInfo.nz;	 // data bytes of per-level
                ll_temp.data[iz * 2 + ivar].header.levelnum = i_pro->GridInfo.nz * 2; // level numbers of data 文件内一共的层数
                ll_temp.data[iz * 2 + ivar].header.amp = i_pro->DataBlock.at(ivar).ProDataInfo.DScale;        // amplify factor = 10; 放大系数，dbz乘上放大系数后存储
                ll_temp.data[iz * 2 + ivar].header.compmode = 0;   // 0 = LatLon grid; 1=sparse LatLon grid
                ll_temp.data[iz * 2 + ivar].header.dates = 0; // UTC dates 日期
                ll_temp.data[iz * 2 + ivar].header.seconds = i_pro->ProInfo.ProductionTime;     // UTC seconds 秒
                ll_temp.data[iz * 2 + ivar].header.min_value = 0;   // used in compress mode
                ll_temp.data[iz * 2 + ivar].header.max_value = 0;   // used in compress mode
                ll_temp.data[iz * 2 + ivar].header.enablemultiLevel = 1;	 // 是否存储多层，0表示只有一层，1表示多层
                ll_temp.data[iz * 2 + ivar].header.height = i_pro->GridInfo.z.at(iz); //  or  forecast_time;
                if (iz == i_pro->GridInfo.nz - 1 && ivar == 2)
                {
                    ll_temp.data[iz * 2 + ivar].header.index_nextbytes = 0;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
                }
                else if (iz == 0 && ivar == 0)
                {
                    ll_temp.data[iz * 2 + ivar].header.index_nextbytes = sizeof(LLDF_HEADER) + ll_temp.data[iz * 2 + ivar].header.levelbytes;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
                }
                else
                {
                    ll_temp.data[iz * 2 + ivar].header.index_nextbytes = ll_temp.data[iz * 2 + ivar - 1].header.index_nextbytes + sizeof(LLDF_HEADER) + ll_temp.data[iz * 2 + ivar].header.levelbytes;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
                }


                ll_temp.data[iz * 2 + ivar].header.domain.slat = i_pro->MapProjInfo.ctrlat - i_pro->GridInfo.dcolumn * i_pro->GridInfo.ncolumn / 100000.0;
                ll_temp.data[iz * 2 + ivar].header.domain.nlat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn * i_pro->GridInfo.ncolumn / 100000.0;
                ll_temp.data[iz * 2 + ivar].header.domain.wlon = i_pro->MapProjInfo.ctrlon - i_pro->GridInfo.drow * i_pro->GridInfo.nrow / 100000.0; // 0.01 deg 西南角经纬度
                ll_temp.data[iz * 2 + ivar].header.domain.elon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow * i_pro->GridInfo.nrow / 100000.0; // 0.01 deg 东北角经纬度
                ll_temp.data[iz * 2 + ivar].header.domain.clat = i_pro->MapProjInfo.ctrlat;
                ll_temp.data[iz * 2 + ivar].header.domain.clon = i_pro->MapProjInfo.ctrlon; // 0.01 deg  中心经纬度

                ll_temp.data[iz * 2 + ivar].header.domain.dlat = i_pro->GridInfo.dcolumn / 50000.0;
                ll_temp.data[iz * 2 + ivar].header.domain.dlon = i_pro->GridInfo.drow / 50000.0; // minimize = 0.01 deg 经纬度单位间隔
                ll_temp.data[iz * 2 + ivar].data.resize(ll_temp.data[iz * 2 + ivar].header.levelbytes);


                ll_temp.data[iz * 2 + ivar].header.domain.cols = i_pro->GridInfo.nrow;
                ll_temp.data[iz * 2 + ivar].header.domain.rows = i_pro->GridInfo.ncolumn; // 行列数
                for (int i = 0; i < ll_temp.data[iz * 2 + ivar].header.domain.rows; i++)
                {
                    int shift_org = (ll_temp.data[iz * 2 + ivar].header.domain.rows - 1 - i) * ll_temp.data[iz * 2 + ivar].header.domain.cols * ll_temp.data[iz * 2 + ivar].header.unitlen;
                    int shift = i * ll_temp.data[iz * 2 + ivar].header.domain.cols * ll_temp.data[iz * 2 + ivar].header.unitlen;
                    memcpy(&ll_temp.data[iz * 2 + ivar].data.at(shift), &i_pro->DataBlock.at(ivar).ProductData.at(iz * ll_temp.data[iz * 2 + ivar].header.levelbytes + shift_org), ll_temp.data[iz].header.domain.cols * ll_temp.data[iz].header.unitlen);
                }
            }
        }
    }
    else
    {
        ll_temp.data.resize(i_pro->GridInfo.nz);
        for (int iz = 0; iz < i_pro->GridInfo.nz; iz++)
        {
            strncpy(ll_temp.data[iz].header.dataname, i_pro->ProInfo.ProductionName, sizeof(ll_temp.data[iz].header.dataname) - 1); // CREF_FZ 文件信息
            strncpy(ll_temp.data[iz].header.varname, i_pro->ProInfo.ProductMethod, sizeof(ll_temp.data[iz].header.varname) - 1); // CREF_FZ 文件信息;    // CREF 变量名称
            strncpy(ll_temp.data[iz].header.units, "\0", sizeof(ll_temp.data[iz].header.units));    // dBZ 变量单位，默认dbz
            ll_temp.data[iz].header.label = 'L' >> 8 | 'L';
            ll_temp.data[iz].header.unitlen = 2;       // 2=short
            ll_temp.data[iz].header.nodata = INVALID_BT;         // -32 for radar
            ll_temp.data[iz].header.offset = i_pro->DataBlock.at(0).ProDataInfo.DOffset;
            ll_temp.data[iz].header.levelbytes = i_pro->DataBlock.at(0).ProductData.size() / i_pro->GridInfo.nz;	  // data bytes of per-level
            ll_temp.data[iz].header.levelnum = i_pro->GridInfo.nz;       // level numbers of data 文件内一共的层数
            ll_temp.data[iz].header.amp = i_pro->DataBlock.at(0).ProDataInfo.DScale;            // amplify factor = 10; 放大系数，dbz乘上放大系数后存储
            ll_temp.data[iz].header.compmode = 0;       // 0 = LatLon grid; 1=sparse LatLon grid
            ll_temp.data[iz].header.dates = 0;  // UTC dates 日期
            ll_temp.data[iz].header.seconds = i_pro->ProInfo.ProductionTime;         // UTC seconds 秒
            ll_temp.data[iz].header.min_value = 0;       // used in compress mode
            ll_temp.data[iz].header.max_value = 0;       // used in compress mode
            ll_temp.data[iz].header.enablemultiLevel = 1;	  // 是否存储多层，0表示只有一层，1表示多层
            ll_temp.data[iz].header.height = i_pro->GridInfo.z.at(iz);   //  or  forecast_time;
            if (iz == i_pro->GridInfo.nz - 1)
            {
                ll_temp.data[iz].header.index_nextbytes = 0;	  // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
            }
            else if (iz == 0)
            {
                ll_temp.data[iz].header.index_nextbytes = sizeof(LLDF_HEADER) + ll_temp.data[iz].header.levelbytes;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
            }
            else
            {
                ll_temp.data[iz].header.index_nextbytes = ll_temp.data[iz - 1].header.index_nextbytes + sizeof(LLDF_HEADER) + ll_temp.data[iz].header.levelbytes;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
            }

            //            ll_temp.data[iz].header.reserved[0] = 0;
            //            ll_temp.data[iz].header.reserved[1] = 0;

//            ll_temp.data[iz].header.domain.slat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn /50000.0 * (0 - i_pro->GridInfo.ncolumn/2);
//            ll_temp.data[iz].header.domain.wlon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow /50000.0 * (0 - i_pro->GridInfo.nrow/2);;  // 0.01 deg 西南角经纬度
//            ll_temp.data[iz].header.domain.nlat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn /50000.0 * (i_pro->GridInfo.ncolumn -1 - i_pro->GridInfo.ncolumn/2);
//            ll_temp.data[iz].header.domain.elon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow /50000.0 * (i_pro->GridInfo.nrow -1 - i_pro->GridInfo.nrow/2);;  // 0.01 deg 东北角经纬度
            ll_temp.data[iz].header.domain.slat = i_pro->MapProjInfo.ctrlat - i_pro->GridInfo.dcolumn * i_pro->GridInfo.ncolumn / 100000.0;
            ll_temp.data[iz].header.domain.nlat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn * i_pro->GridInfo.ncolumn / 100000.0;
            ll_temp.data[iz].header.domain.wlon = i_pro->MapProjInfo.ctrlon - i_pro->GridInfo.drow * i_pro->GridInfo.nrow / 100000.0;  // 0.01 deg 西南角经纬度
            ll_temp.data[iz].header.domain.elon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow * i_pro->GridInfo.nrow / 100000.0;  // 0.01 deg 东北角经纬度
            ll_temp.data[iz].header.domain.clat = i_pro->MapProjInfo.ctrlat;
            ll_temp.data[iz].header.domain.clon = i_pro->MapProjInfo.ctrlon;  // 0.01 deg  中心经纬度

            ll_temp.data[iz].header.domain.dlat = i_pro->GridInfo.dcolumn / 50000.0;
            ll_temp.data[iz].header.domain.dlon = i_pro->GridInfo.drow / 50000.0; // minimize = 0.01 deg 经纬度单位间隔
            ll_temp.data[iz].data.resize(ll_temp.data[iz].header.levelbytes);

            //        ll_temp.data[iz].header.domain.rows = i_pro->GridInfo.nrow;
            //        ll_temp.data[iz].header.domain.cols = i_pro->GridInfo.ncolumn;  // 行列数
            //        memcpy(&ll_temp.data[iz].data.at(0),&i_pro->DataBlock.at(0).ProductData.at(iz*ll_temp.data[iz].header.levelbytes),ll_temp.data[iz].header.levelbytes);

            ll_temp.data[iz].header.domain.cols = i_pro->GridInfo.nrow;
            ll_temp.data[iz].header.domain.rows = i_pro->GridInfo.ncolumn;  // 行列数
            for (int i = 0; i < ll_temp.data[iz].header.domain.rows; i++)
            {
                int shift_org = (ll_temp.data[iz].header.domain.rows - 1 - i) * ll_temp.data[iz].header.domain.cols * ll_temp.data[iz].header.unitlen;
                int shift = i * ll_temp.data[iz].header.domain.cols * ll_temp.data[iz].header.unitlen;
                memcpy(&ll_temp.data[iz].data.at(shift), &i_pro->DataBlock.at(0).ProductData.at(iz * ll_temp.data[iz].header.levelbytes + shift_org), ll_temp.data[iz].header.domain.cols * ll_temp.data[iz].header.unitlen);
            }
        }
    }

    try
    {
//        if (i_pro->ProInfo.ProductionID == 304)         // Mosaic CR
//        {
//            // TODO: delete files that contain the same timestamp as 'FileName'
//            string strFullPath = string(FileName);
//            string strPath = strFullPath.substr(0, strFullPath.find_last_of('/'));
//            string strFullName = strFullPath.substr(strFullPath.find_last_of('/') + 1);
//            string strName = strFullName.substr(0, strFullName.find_last_of('.'));
//            string strFeature = strName.substr(0, strName.find_last_of('.'));

//            vector<string> filelist;
//            get_files(strPath, strFeature, filelist);
//            for (int i = 0; i < filelist.size(); ++i){
//                remove(filelist[i].c_str());
//            }
//        }
        ofstream fp(FileName, ios::out | ios::binary);
        for (int iz = 0; iz < ll_temp.data.size(); iz++)
        {
            fp.write((char *) & (ll_temp.data[iz].header), sizeof(LLDF_HEADER));
            fp.write((char *) & (ll_temp.data[iz].data[0]), ll_temp.data[iz].header.levelbytes);
        }
        fp.close();

        if (i_pro->ProInfo.ProductionID == PTYPE_MAX + 300)     // Mosaic CR
        {
            // TODO: save weight to txt
            short weight = 0;
            int scale = i_pro->DataBlock.at(0).ProDataInfo.DScale;
            int offset = i_pro->DataBlock.at(0).ProDataInfo.DOffset;
            int count = 0;
            for (int i = 0; i < i_pro->DataBlock.at(0).ProductData.size() / 2; i += 2)
            {
                if ((*(short *)&i_pro->DataBlock.at(0).ProductData.at(i * 2) - offset) / scale > 15)
                {
                    count++;
                }
            }
            weight = 1000.0 * count / (i_pro->DataBlock.at(0).ProductData.size() / 2);

            string strFullPath = string(FileName);
            string strTxtFileName = strFullPath.substr(0, strFullPath.find_last_of('.')) + ".txt";
            ofstream fp(strTxtFileName.c_str(), ios::out | ios::trunc);
            fp << weight << std::endl;
            fp.close();
        }
        else if (i_pro->ProInfo.ProductionID >= 201 && i_pro->ProInfo.ProductionID <= 211)      // Mosaic CAPPI
        {
            // TODO: output by layer
            for (int layer = 0; layer < ll_temp.data.size(); ++layer)
            {
                if (ll_temp.data[layer].header.height <= 0)
                {
                    continue;
                }
                string strFullPath = string(FileName);
                string strPath = strFullPath.substr(0, strFullPath.find_last_of('/'));
                string strFullName = strFullPath.substr(strFullPath.find_last_of('/') + 1);
                string strName = strFullName.substr(0, strFullName.find_first_of(".latlon"));
                string strSuffix = strFullName.substr(strFullName.find_first_of(".latlon") + 1);
                string strNewFullPath = strPath + "/" + strName + "." + std::to_string(ll_temp.data[layer].header.height) + "." + strSuffix;

                ofstream fp(strNewFullPath, ios::out | ios::binary);
                ll_temp.data[layer].header.index_nextbytes = 0;
                ll_temp.data[layer].header.levelnum = 1;
                ll_temp.data[layer].header.enablemultiLevel = 0;
                fp.write((char *) & (ll_temp.data[layer].header), sizeof(LLDF_HEADER));
                fp.write((char *) & (ll_temp.data[layer].data[0]), ll_temp.data[layer].header.levelbytes);
                fp.close();
            }
        }
        else if (i_pro->ProInfo.ProductionID >= 241 && i_pro->ProInfo.ProductionID <= 251)      // 等仰角面组网产品
        {
            //TODO: output by layer(except for the top one) & output the top layer as RELCR when ProductionID equals 242
            for (int layer = 0; layer < ll_temp.data.size() - 1; ++layer)
            {
                if (ll_temp.data[layer].header.height <= 0)
                {
                    continue;
                }
                string strFullPath = string(FileName);
                string strPath = strFullPath.substr(0, strFullPath.find_last_of('/'));
                string strFullName = strFullPath.substr(strFullPath.find_last_of('/') + 1);
                string strName = strFullName.substr(0, strFullName.find_first_of(".latlon"));
                string strSuffix = strFullName.substr(strFullName.find_first_of(".latlon") + 1);
                string strNewFullPath = strPath + "/" + strName + "." + std::to_string(ll_temp.data[layer].header.height) + "." + strSuffix;

                ofstream fp(strNewFullPath, ios::out | ios::binary);
                ll_temp.data[layer].header.index_nextbytes = 0;
                ll_temp.data[layer].header.levelnum = 1;
                ll_temp.data[layer].header.enablemultiLevel = 0;
                fp.write((char *) & (ll_temp.data[layer].header), sizeof(LLDF_HEADER));
                fp.write((char *) & (ll_temp.data[layer].data[0]), ll_temp.data[layer].header.levelbytes);
                fp.close();
            }
            if (i_pro->ProInfo.ProductionID == 242)
            {
                int layer = ll_temp.data.size() - 1;
                string strFullPath = string(FileName);
                string strPath = strFullPath.substr(0, strFullPath.find_last_of('/'));
                strPath = strPath.replace(strPath.find_last_of("RECR") - 3, 4, "RELCR");
                DIR *dir = opendir(strPath.c_str());
                if (dir)
                {
                    closedir(dir);
                }
                else
                {
                    std::string cmd = "mkdir -p " + strPath;
                    system(cmd.c_str());
                }
                string strFullName = strFullPath.substr(strFullPath.find_last_of('/') + 1);
                strFullName = strFullName.replace(strFullName.find("RECR"), 4, "RELCR");
                string strNewFullPath = strPath + "/" + strFullName;

                ofstream fp(strNewFullPath, ios::out | ios::binary);
                ll_temp.data[layer].header.index_nextbytes = 0;
                ll_temp.data[layer].header.levelnum = 1;
                ll_temp.data[layer].header.enablemultiLevel = 0;
                fp.write((char *) & (ll_temp.data[layer].header), sizeof(LLDF_HEADER));
                fp.write((char *) & (ll_temp.data[layer].data[0]), ll_temp.data[layer].header.levelbytes);
                fp.close();
            }
        }
    }
    catch (...)
    {
        cout << "Save file error." << endl;
        return false;
    }

    return true;
}

bool CNrietFileIO::SaveZlibRadarLatlonDataBuf(void *source, Bytef *dest, uLongf *destLen)
{
    s_Pro_Grid::RadarProduct *i_pro = (s_Pro_Grid::RadarProduct *)source;
    uLongf tempLen;
    *destLen = 0;
    LLDF_FORMAT ll_temp;
    if (i_pro->ProInfo.ProductionID >= 220 && i_pro->ProInfo.ProductionID < 230)
    {
        ll_temp.data.resize(i_pro->GridInfo.nz * 3);
        for (int iz = 0; iz < i_pro->GridInfo.nz; iz++)
        {
            for (int ivar = 0 ; ivar < 3; ivar++)
            {
                strncpy(ll_temp.data[iz * 3 + ivar].header.dataname, i_pro->ProInfo.ProductionName, sizeof(ll_temp.data[iz * 3 + ivar].header.dataname) - 1); // CREF_FZ 文件信息
                strncpy(ll_temp.data[iz * 3 + ivar].header.varname, i_pro->DataBlock.at(ivar).ProDataInfo.VarName, sizeof(ll_temp.data[iz * 3 + ivar].header.varname) - 1); // CREF_FZ 文件信息;    // CREF 变量名称
                strncpy(ll_temp.data[iz * 3 + ivar].header.units, "m/s", sizeof(ll_temp.data[iz * 3 + ivar].header.units)); // dBZ 变量单位，默认dbz
                ll_temp.data[iz * 3 + ivar].header.label = 'L' >> 8 | 'L';
                ll_temp.data[iz * 3 + ivar].header.unitlen = 2;   // 2=short
                ll_temp.data[iz * 3 + ivar].header.nodata = INVALID_BT;     // -32 for radar
                ll_temp.data[iz * 3 + ivar].header.offset = i_pro->DataBlock.at(ivar).ProDataInfo.DOffset;
                ll_temp.data[iz * 3 + ivar].header.levelbytes = i_pro->DataBlock.at(ivar).ProductData.size() / i_pro->GridInfo.nz;	 // data bytes of per-level
                ll_temp.data[iz * 3 + ivar].header.levelnum = i_pro->GridInfo.nz * 3; // level numbers of data 文件内一共的层数
                ll_temp.data[iz * 3 + ivar].header.amp = i_pro->DataBlock.at(ivar).ProDataInfo.DScale;        // amplify factor = 10; 放大系数，dbz乘上放大系数后存储
                ll_temp.data[iz * 3 + ivar].header.compmode = 0;  // 0 = LatLon grid; 1=sparse LatLon grid
                ll_temp.data[iz * 3 + ivar].header.dates = 0; // UTC dates 日期
                ll_temp.data[iz * 3 + ivar].header.seconds = i_pro->ProInfo.ProductionTime;     // UTC seconds 秒
                ll_temp.data[iz * 3 + ivar].header.min_value = 0;   // used in compress mode
                ll_temp.data[iz * 3 + ivar].header.max_value = 0;   // used in compress mode
                ll_temp.data[iz * 3 + ivar].header.enablemultiLevel = 1;	 // 是否存储多层，0表示只有一层，1表示多层
                ll_temp.data[iz * 3 + ivar].header.height = i_pro->GridInfo.z.at(iz); //  or  forecast_time;
                if (iz == i_pro->GridInfo.nz - 1 && ivar == 2)
                {
                    ll_temp.data[iz * 3 + ivar].header.index_nextbytes = 0;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
                }
                else if (iz == 0 && ivar == 0)
                {
                    ll_temp.data[iz * 3 + ivar].header.index_nextbytes = sizeof(LLDF_HEADER) + ll_temp.data[iz * 3 + ivar].header.levelbytes;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
                }
                else
                {
                    ll_temp.data[iz * 3 + ivar].header.index_nextbytes = ll_temp.data[iz * 3 + ivar - 1].header.index_nextbytes + sizeof(LLDF_HEADER) + ll_temp.data[iz * 3 + ivar].header.levelbytes;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
                }

                //                ll_temp.data[iz*3+ivar].header.reserved[0] = 0;
                //                ll_temp.data[iz*3+ivar].header.reserved[1] = 0;

//                ll_temp.data[iz*3+ivar].header.domain.slat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn /50000.0 * (0 - i_pro->GridInfo.ncolumn/2);
//                ll_temp.data[iz*3+ivar].header.domain.wlon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow /50000.0 * (0 - i_pro->GridInfo.nrow/2);;  // 0.01 deg 西南角经纬度
//                ll_temp.data[iz*3+ivar].header.domain.nlat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn /50000.0 * (i_pro->GridInfo.ncolumn -1 - i_pro->GridInfo.ncolumn/2);
//                ll_temp.data[iz*3+ivar].header.domain.elon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow /50000.0 * (i_pro->GridInfo.nrow -1 - i_pro->GridInfo.nrow/2);;  // 0.01 deg 东北角经纬度
                ll_temp.data[iz * 3 + ivar].header.domain.slat = i_pro->MapProjInfo.ctrlat - i_pro->GridInfo.dcolumn * i_pro->GridInfo.ncolumn / 100000.0;
                ll_temp.data[iz * 3 + ivar].header.domain.nlat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn * i_pro->GridInfo.ncolumn / 100000.0;
                ll_temp.data[iz * 3 + ivar].header.domain.wlon = i_pro->MapProjInfo.ctrlon - i_pro->GridInfo.drow * i_pro->GridInfo.nrow / 100000.0; // 0.01 deg 西南角经纬度
                ll_temp.data[iz * 3 + ivar].header.domain.elon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow * i_pro->GridInfo.nrow / 100000.0; // 0.01 deg 东北角经纬度
                ll_temp.data[iz * 3 + ivar].header.domain.clat = i_pro->MapProjInfo.ctrlat;
                ll_temp.data[iz * 3 + ivar].header.domain.clon = i_pro->MapProjInfo.ctrlon; // 0.01 deg  中心经纬度

                ll_temp.data[iz * 3 + ivar].header.domain.dlat = i_pro->GridInfo.dcolumn / 50000.0;
                ll_temp.data[iz * 3 + ivar].header.domain.dlon = i_pro->GridInfo.drow / 50000.0; // minimize = 0.01 deg 经纬度单位间隔
                ll_temp.data[iz * 3 + ivar].data.resize(ll_temp.data[iz * 3 + ivar].header.levelbytes);

                //        ll_temp.data[iz*3+ivar].header.domain.rows = i_pro->GridInfo.nrow;
                //        ll_temp.data[iz*3+ivar].header.domain.cols = i_pro->GridInfo.ncolumn;  // 行列数
                //        memcpy(&ll_temp.data[iz*3+ivar].data.at(0),&i_pro->DataBlock.at(0).ProductData.at(iz*ll_temp.data[iz*3+ivar].header.levelbytes),ll_temp.data[iz*3+ivar].header.levelbytes);

                ll_temp.data[iz * 3 + ivar].header.domain.cols = i_pro->GridInfo.nrow;
                ll_temp.data[iz * 3 + ivar].header.domain.rows = i_pro->GridInfo.ncolumn; // 行列数
                for (int i = 0; i < ll_temp.data[iz * 3 + ivar].header.domain.rows; i++)
                {
                    int shift_org = (ll_temp.data[iz * 3 + ivar].header.domain.rows - 1 - i) * ll_temp.data[iz * 3 + ivar].header.domain.cols * ll_temp.data[iz * 3 + ivar].header.unitlen;
                    int shift = i * ll_temp.data[iz * 3 + ivar].header.domain.cols * ll_temp.data[iz * 3 + ivar].header.unitlen;
                    memcpy(&ll_temp.data[iz * 3 + ivar].data.at(shift), &i_pro->DataBlock.at(ivar).ProductData.at(iz * ll_temp.data[iz * 3 + ivar].header.levelbytes + shift_org), ll_temp.data[iz].header.domain.cols * ll_temp.data[iz].header.unitlen);
                }
            }
        }
    }
    else
    {
        ll_temp.data.resize(i_pro->GridInfo.nz);
        for (int iz = 0; iz < i_pro->GridInfo.nz; iz++)
        {
            strncpy(ll_temp.data[iz].header.dataname, i_pro->ProInfo.ProductionName, sizeof(ll_temp.data[iz].header.dataname) - 1); // CREF_FZ 文件信息
            strncpy(ll_temp.data[iz].header.varname, i_pro->ProInfo.ProductMethod, sizeof(ll_temp.data[iz].header.varname) - 1); // CREF_FZ 文件信息;    // CREF 变量名称
            strncpy(ll_temp.data[iz].header.units, "\0", sizeof(ll_temp.data[iz].header.units));    // dBZ 变量单位，默认dbz
            ll_temp.data[iz].header.label = 'L' >> 8 | 'L';
            ll_temp.data[iz].header.unitlen = 2;       // 2=short
            ll_temp.data[iz].header.nodata = INVALID_BT;         // -32 for radar
            ll_temp.data[iz].header.offset = i_pro->DataBlock.at(0).ProDataInfo.DOffset;
            ll_temp.data[iz].header.levelbytes = i_pro->DataBlock.at(0).ProductData.size() / i_pro->GridInfo.nz;	  // data bytes of per-level
            ll_temp.data[iz].header.levelnum = i_pro->GridInfo.nz;       // level numbers of data 文件内一共的层数
            ll_temp.data[iz].header.amp = i_pro->DataBlock.at(0).ProDataInfo.DScale;            // amplify factor = 10; 放大系数，dbz乘上放大系数后存储
            ll_temp.data[iz].header.compmode = 0;       // 0 = LatLon grid; 1=sparse LatLon grid
            ll_temp.data[iz].header.dates = 0;  // UTC dates 日期
            ll_temp.data[iz].header.seconds = i_pro->ProInfo.ProductionTime;         // UTC seconds 秒
            ll_temp.data[iz].header.min_value = 0;       // used in compress mode
            ll_temp.data[iz].header.max_value = 0;       // used in compress mode
            ll_temp.data[iz].header.enablemultiLevel = 1;	  // 是否存储多层，0表示只有一层，1表示多层
            ll_temp.data[iz].header.height = i_pro->GridInfo.z.at(iz);   //  or  forecast_time;
            if (iz == i_pro->GridInfo.nz - 1)
            {
                ll_temp.data[iz].header.index_nextbytes = 0;	  // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
            }
            else if (iz == 0)
            {
                ll_temp.data[iz].header.index_nextbytes = sizeof(LLDF_HEADER) + ll_temp.data[iz].header.levelbytes;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
            }
            else
            {
                ll_temp.data[iz].header.index_nextbytes = ll_temp.data[iz - 1].header.index_nextbytes + sizeof(LLDF_HEADER) + ll_temp.data[iz].header.levelbytes;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
            }

            //            ll_temp.data[iz].header.reserved[0] = 0;
            //            ll_temp.data[iz].header.reserved[1] = 0;

//            ll_temp.data[iz].header.domain.slat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn /50000.0 * (0 - i_pro->GridInfo.ncolumn/2);
//            ll_temp.data[iz].header.domain.wlon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow /50000.0 * (0 - i_pro->GridInfo.nrow/2);;  // 0.01 deg 西南角经纬度
//            ll_temp.data[iz].header.domain.nlat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn /50000.0 * (i_pro->GridInfo.ncolumn -1 - i_pro->GridInfo.ncolumn/2);
//            ll_temp.data[iz].header.domain.elon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow /50000.0 * (i_pro->GridInfo.nrow -1 - i_pro->GridInfo.nrow/2);;  // 0.01 deg 东北角经纬度
            ll_temp.data[iz].header.domain.slat = i_pro->MapProjInfo.ctrlat - i_pro->GridInfo.dcolumn * i_pro->GridInfo.ncolumn / 100000.0;
            ll_temp.data[iz].header.domain.nlat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn * i_pro->GridInfo.ncolumn / 100000.0;
            ll_temp.data[iz].header.domain.wlon = i_pro->MapProjInfo.ctrlon - i_pro->GridInfo.drow * i_pro->GridInfo.nrow / 100000.0;  // 0.01 deg 西南角经纬度
            ll_temp.data[iz].header.domain.elon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow * i_pro->GridInfo.nrow / 100000.0;  // 0.01 deg 东北角经纬度
            ll_temp.data[iz].header.domain.clat = i_pro->MapProjInfo.ctrlat;
            ll_temp.data[iz].header.domain.clon = i_pro->MapProjInfo.ctrlon;  // 0.01 deg  中心经纬度

            ll_temp.data[iz].header.domain.dlat = i_pro->GridInfo.dcolumn / 50000.0;
            ll_temp.data[iz].header.domain.dlon = i_pro->GridInfo.drow / 50000.0; // minimize = 0.01 deg 经纬度单位间隔
            ll_temp.data[iz].data.resize(ll_temp.data[iz].header.levelbytes);

            //        ll_temp.data[iz].header.domain.rows = i_pro->GridInfo.nrow;
            //        ll_temp.data[iz].header.domain.cols = i_pro->GridInfo.ncolumn;  // 行列数
            //        memcpy(&ll_temp.data[iz].data.at(0),&i_pro->DataBlock.at(0).ProductData.at(iz*ll_temp.data[iz].header.levelbytes),ll_temp.data[iz].header.levelbytes);

            ll_temp.data[iz].header.domain.cols = i_pro->GridInfo.nrow;
            ll_temp.data[iz].header.domain.rows = i_pro->GridInfo.ncolumn;  // 行列数
            for (int i = 0; i < ll_temp.data[iz].header.domain.rows; i++)
            {
                int shift_org = (ll_temp.data[iz].header.domain.rows - 1 - i) * ll_temp.data[iz].header.domain.cols * ll_temp.data[iz].header.unitlen;
                int shift = i * ll_temp.data[iz].header.domain.cols * ll_temp.data[iz].header.unitlen;
                memcpy(&ll_temp.data[iz].data.at(shift), &i_pro->DataBlock.at(0).ProductData.at(iz * ll_temp.data[iz].header.levelbytes + shift_org), ll_temp.data[iz].header.domain.cols * ll_temp.data[iz].header.unitlen);
            }
        }
    }

    for (int iz = 0; iz < ll_temp.data.size(); iz++)
    {
        compress(dest + *destLen, &tempLen, (const Bytef *) & (ll_temp.data[iz].header), sizeof(LLDF_HEADER));
        *destLen += tempLen;
        compress(dest + *destLen, &tempLen, (const Bytef *) & (ll_temp.data[iz].data[0]), ll_temp.data[iz].header.levelbytes);
        *destLen += tempLen;
    }

    return true;
}

bool CNrietFileIO::SaveZlibRadarLatlonData(void *temp, char *FileName)
{
    s_Pro_Grid::RadarProduct *i_pro = (s_Pro_Grid::RadarProduct *)temp;
    LLDF_FORMAT ll_temp;
    if (i_pro->ProInfo.ProductionID == 220 || i_pro->ProInfo.ProductionID == 229)
    {
        ll_temp.data.resize(i_pro->GridInfo.nz * 3);
        for (int iz = 0; iz < i_pro->GridInfo.nz; iz++)
        {
            for (int ivar = 0 ; ivar < 3; ivar++)
            {
                strncpy(ll_temp.data[iz * 3 + ivar].header.dataname, i_pro->ProInfo.ProductionName, sizeof(ll_temp.data[iz * 3 + ivar].header.dataname) - 1); // CREF_FZ 文件信息
                strncpy(ll_temp.data[iz * 3 + ivar].header.varname, i_pro->DataBlock.at(ivar).ProDataInfo.VarName, sizeof(ll_temp.data[iz * 3 + ivar].header.varname) - 1); // CREF_FZ 文件信息;    // CREF 变量名称
                strncpy(ll_temp.data[iz * 3 + ivar].header.units, "m/s", sizeof(ll_temp.data[iz * 3 + ivar].header.units)); // dBZ 变量单位，默认dbz
                ll_temp.data[iz * 3 + ivar].header.label = 'L' >> 8 | 'L';
                ll_temp.data[iz * 3 + ivar].header.unitlen = 2;   // 2=short
                ll_temp.data[iz * 3 + ivar].header.nodata = INVALID_BT;     // -32 for radar
                ll_temp.data[iz * 3 + ivar].header.offset = i_pro->DataBlock.at(ivar).ProDataInfo.DOffset;
                ll_temp.data[iz * 3 + ivar].header.levelbytes = i_pro->DataBlock.at(ivar).ProductData.size() / i_pro->GridInfo.nz;	 // data bytes of per-level
                ll_temp.data[iz * 3 + ivar].header.levelnum = i_pro->GridInfo.nz * 3; // level numbers of data 文件内一共的层数
                ll_temp.data[iz * 3 + ivar].header.amp = i_pro->DataBlock.at(ivar).ProDataInfo.DScale;        // amplify factor = 10; 放大系数，dbz乘上放大系数后存储
                ll_temp.data[iz * 3 + ivar].header.compmode = 0;  // 0 = LatLon grid; 1=sparse LatLon grid
                ll_temp.data[iz * 3 + ivar].header.dates = 0; // UTC dates 日期
                ll_temp.data[iz * 3 + ivar].header.seconds = i_pro->ProInfo.ProductionTime;     // UTC seconds 秒
                ll_temp.data[iz * 3 + ivar].header.min_value = 0;   // used in compress mode
                ll_temp.data[iz * 3 + ivar].header.max_value = 0;   // used in compress mode
                ll_temp.data[iz * 3 + ivar].header.enablemultiLevel = 1;	 // 是否存储多层，0表示只有一层，1表示多层
                ll_temp.data[iz * 3 + ivar].header.height = i_pro->GridInfo.z.at(iz); //  or  forecast_time;
                if (iz == i_pro->GridInfo.nz - 1 && ivar == 2)
                {
                    ll_temp.data[iz * 3 + ivar].header.index_nextbytes = 0;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
                }
                else if (iz == 0 && ivar == 0)
                {
                    ll_temp.data[iz * 3 + ivar].header.index_nextbytes = sizeof(LLDF_HEADER) + ll_temp.data[iz * 3 + ivar].header.levelbytes;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
                }
                else
                {
                    ll_temp.data[iz * 3 + ivar].header.index_nextbytes = ll_temp.data[iz * 3 + ivar - 1].header.index_nextbytes + sizeof(LLDF_HEADER) + ll_temp.data[iz * 3 + ivar].header.levelbytes;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
                }

                //                ll_temp.data[iz*3+ivar].header.reserved[0] = 0;
                //                ll_temp.data[iz*3+ivar].header.reserved[1] = 0;

//                ll_temp.data[iz*3+ivar].header.domain.slat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn /50000.0 * (0 - i_pro->GridInfo.ncolumn/2);
//                ll_temp.data[iz*3+ivar].header.domain.wlon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow /50000.0 * (0 - i_pro->GridInfo.nrow/2);;  // 0.01 deg 西南角经纬度
//                ll_temp.data[iz*3+ivar].header.domain.nlat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn /50000.0 * (i_pro->GridInfo.ncolumn -1 - i_pro->GridInfo.ncolumn/2);
//                ll_temp.data[iz*3+ivar].header.domain.elon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow /50000.0 * (i_pro->GridInfo.nrow -1 - i_pro->GridInfo.nrow/2);  // 0.01 deg 东北角经纬度
                ll_temp.data[iz * 3 + ivar].header.domain.slat = i_pro->MapProjInfo.ctrlat - i_pro->GridInfo.dcolumn * i_pro->GridInfo.ncolumn / 100000.0;
                ll_temp.data[iz * 3 + ivar].header.domain.nlat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn * i_pro->GridInfo.ncolumn / 100000.0;
                ll_temp.data[iz * 3 + ivar].header.domain.wlon = i_pro->MapProjInfo.ctrlon - i_pro->GridInfo.drow * i_pro->GridInfo.nrow / 100000.0; // 0.01 deg 西南角经纬度
                ll_temp.data[iz * 3 + ivar].header.domain.elon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow * i_pro->GridInfo.nrow / 100000.0; // 0.01 deg 东北角经纬度
                ll_temp.data[iz * 3 + ivar].header.domain.clat = i_pro->MapProjInfo.ctrlat;
                ll_temp.data[iz * 3 + ivar].header.domain.clon = i_pro->MapProjInfo.ctrlon; // 0.01 deg  中心经纬度

                ll_temp.data[iz * 3 + ivar].header.domain.dlat = i_pro->GridInfo.dcolumn / 50000.0;
                ll_temp.data[iz * 3 + ivar].header.domain.dlon = i_pro->GridInfo.drow / 50000.0; // minimize = 0.01 deg 经纬度单位间隔
                ll_temp.data[iz * 3 + ivar].data.resize(ll_temp.data[iz * 3 + ivar].header.levelbytes);

                //        ll_temp.data[iz*3+ivar].header.domain.rows = i_pro->GridInfo.nrow;
                //        ll_temp.data[iz*3+ivar].header.domain.cols = i_pro->GridInfo.ncolumn;  // 行列数
                //        memcpy(&ll_temp.data[iz*3+ivar].data.at(0),&i_pro->DataBlock.at(0).ProductData.at(iz*ll_temp.data[iz*3+ivar].header.levelbytes),ll_temp.data[iz*3+ivar].header.levelbytes);

                ll_temp.data[iz * 3 + ivar].header.domain.cols = i_pro->GridInfo.nrow;
                ll_temp.data[iz * 3 + ivar].header.domain.rows = i_pro->GridInfo.ncolumn; // 行列数
                for (int i = 0; i < ll_temp.data[iz * 3 + ivar].header.domain.rows; i++)
                {
                    int shift_org = (ll_temp.data[iz * 3 + ivar].header.domain.rows - 1 - i) * ll_temp.data[iz * 3 + ivar].header.domain.cols * ll_temp.data[iz * 3 + ivar].header.unitlen;
                    int shift = i * ll_temp.data[iz * 3 + ivar].header.domain.cols * ll_temp.data[iz * 3 + ivar].header.unitlen;
                    memcpy(&ll_temp.data[iz * 3 + ivar].data.at(shift), &i_pro->DataBlock.at(ivar).ProductData.at(iz * ll_temp.data[iz * 3 + ivar].header.levelbytes + shift_org), ll_temp.data[iz].header.domain.cols * ll_temp.data[iz].header.unitlen);
                }
            }
        }
    }
    else if (i_pro->ProInfo.ProductionID == 61 || i_pro->ProInfo.ProductionID == 64)
    {
        ll_temp.data.resize(i_pro->GridInfo.nz * 2);
        for (int iz = 0; iz < i_pro->GridInfo.nz; iz++)
        {
            for (int ivar = 0 ; ivar < 2; ivar++)
            {
                strncpy(ll_temp.data[iz * 2 + ivar].header.dataname, i_pro->ProInfo.ProductionName, sizeof(ll_temp.data[iz * 2 + ivar].header.dataname) - 1); // CREF_FZ 文件信息
                strncpy(ll_temp.data[iz * 2 + ivar].header.varname, i_pro->DataBlock.at(ivar).ProDataInfo.VarName, sizeof(ll_temp.data[iz * 2 + ivar].header.varname) - 1); // CREF_FZ 文件信息;    // CREF 变量名称
                strncpy(ll_temp.data[iz * 2 + ivar].header.units, "m/s", sizeof(ll_temp.data[iz * 2 + ivar].header.units)); // dBZ 变量单位，默认dbz
                ll_temp.data[iz * 2 + ivar].header.label = 'L' >> 8 | 'L';
                ll_temp.data[iz * 2 + ivar].header.unitlen = 2;   // 2=short
                ll_temp.data[iz * 2 + ivar].header.nodata = INVALID_BT;     // -32 for radar
                ll_temp.data[iz * 2 + ivar].header.offset = i_pro->DataBlock.at(ivar).ProDataInfo.DOffset;
                ll_temp.data[iz * 2 + ivar].header.levelbytes = i_pro->DataBlock.at(ivar).ProductData.size();	 // data bytes of per-level
                ll_temp.data[iz * 2 + ivar].header.levelnum = i_pro->GridInfo.nz * 2; // level numbers of data 文件内一共的层数
                ll_temp.data[iz * 2 + ivar].header.amp = i_pro->DataBlock.at(ivar).ProDataInfo.DScale;        // amplify factor = 10; 放大系数，dbz乘上放大系数后存储
                ll_temp.data[iz * 2 + ivar].header.compmode = 0;  // 0 = LatLon grid; 1=sparse LatLon grid
                ll_temp.data[iz * 2 + ivar].header.dates = 0; // UTC dates 日期
                ll_temp.data[iz * 2 + ivar].header.seconds = i_pro->ProInfo.ProductionTime;     // UTC seconds 秒
                ll_temp.data[iz * 2 + ivar].header.min_value = 0;   // used in compress mode
                ll_temp.data[iz * 2 + ivar].header.max_value = 0;   // used in compress mode
                ll_temp.data[iz * 2 + ivar].header.enablemultiLevel = 1;	 // 是否存储多层，0表示只有一层，1表示多层
                ll_temp.data[iz * 2 + ivar].header.height = i_pro->GridInfo.z.at(iz); //  or  forecast_time;
                if (iz == i_pro->GridInfo.nz - 1 && ivar == 1)
                {
                    ll_temp.data[iz * 2 + ivar].header.index_nextbytes = 0;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
                }
                else if (iz == 0 && ivar == 0)
                {
                    ll_temp.data[iz * 2 + ivar].header.index_nextbytes = sizeof(LLDF_HEADER) + ll_temp.data[iz * 2 + ivar].header.levelbytes;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
                }
                else
                {
                    ll_temp.data[iz * 2 + ivar].header.index_nextbytes = ll_temp.data[iz * 2 + ivar - 1].header.index_nextbytes + sizeof(LLDF_HEADER) + ll_temp.data[iz * 2 + ivar].header.levelbytes;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
                }

                ll_temp.data[iz * 2 + ivar].header.domain.slat = i_pro->MapProjInfo.ctrlat - i_pro->GridInfo.dcolumn * i_pro->GridInfo.ncolumn / 100000.0;
                ll_temp.data[iz * 2 + ivar].header.domain.nlat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn * i_pro->GridInfo.ncolumn / 100000.0;
                ll_temp.data[iz * 2 + ivar].header.domain.wlon = i_pro->MapProjInfo.ctrlon - i_pro->GridInfo.drow * i_pro->GridInfo.nrow / 100000.0; // 0.01 deg 西南角经纬度
                ll_temp.data[iz * 2 + ivar].header.domain.elon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow * i_pro->GridInfo.nrow / 100000.0; // 0.01 deg 东北角经纬度
                ll_temp.data[iz * 2 + ivar].header.domain.clat = i_pro->MapProjInfo.ctrlat;
                ll_temp.data[iz * 2 + ivar].header.domain.clon = i_pro->MapProjInfo.ctrlon; // 0.01 deg  中心经纬度

                ll_temp.data[iz * 2 + ivar].header.domain.dlat = i_pro->GridInfo.dcolumn / 50000.0;
                ll_temp.data[iz * 2 + ivar].header.domain.dlon = i_pro->GridInfo.drow / 50000.0; // minimize = 0.01 deg 经纬度单位间隔
                ll_temp.data[iz * 2 + ivar].data.resize(ll_temp.data[iz * 2 + ivar].header.levelbytes);
                ll_temp.data[iz * 2 + ivar].header.domain.cols = i_pro->GridInfo.nrow;
                ll_temp.data[iz * 2 + ivar].header.domain.rows = i_pro->GridInfo.ncolumn; // 行列数
//                ll_temp.data[iz*2+ivar].data.resize(ll_temp.data[iz*2+ivar].header.domain.rows * ll_temp.data[iz*2+ivar].header.domain.cols * ll_temp.data[iz*2+ivar].header.unitlen);

                for (int i = 0; i < ll_temp.data[iz * 2 + ivar].header.domain.rows; i++)
                {
                    int shift_org = (ll_temp.data[iz * 2 + ivar].header.domain.rows - 1 - i) * ll_temp.data[iz * 2 + ivar].header.domain.cols * ll_temp.data[iz * 2 + ivar].header.unitlen;
                    int shift = i * ll_temp.data[iz * 2 + ivar].header.domain.cols * ll_temp.data[iz * 2 + ivar].header.unitlen;
//                    memcpy(&ll_temp.data[iz*2+ivar].data.at(shift),&i_pro->DataBlock.at(ivar).ProductData.at(iz*ll_temp.data[iz*2+ivar].header.levelbytes + shift_org),ll_temp.data[iz].header.domain.cols * ll_temp.data[iz].header.unitlen);
                    memcpy(&ll_temp.data[iz * 2 + ivar].data.at(shift), &i_pro->DataBlock.at(iz * 2 + ivar).ProductData.at(shift), ll_temp.data[iz].header.domain.cols * ll_temp.data[iz].header.unitlen);
                }
            }
        }
    }
    else
    {
        ll_temp.data.resize(i_pro->GridInfo.nz);
        for (int iz = 0; iz < i_pro->GridInfo.nz; iz++)
        {
            strncpy(ll_temp.data[iz].header.dataname, i_pro->ProInfo.ProductionName, sizeof(ll_temp.data[iz].header.dataname) - 1); // CREF_FZ 文件信息
            strncpy(ll_temp.data[iz].header.varname, i_pro->ProInfo.ProductMethod, sizeof(ll_temp.data[iz].header.varname) - 1); // CREF_FZ 文件信息;    // CREF 变量名称
            strncpy(ll_temp.data[iz].header.units, "\0", sizeof(ll_temp.data[iz].header.units));    // dBZ 变量单位，默认dbz
            ll_temp.data[iz].header.label = 'L' >> 8 | 'L';
            ll_temp.data[iz].header.unitlen = 2;       // 2=short
            ll_temp.data[iz].header.nodata = INVALID_BT;         // -32 for radar
            ll_temp.data[iz].header.offset = i_pro->DataBlock.at(0).ProDataInfo.DOffset;
            ll_temp.data[iz].header.levelbytes = i_pro->DataBlock.at(0).ProductData.size() / i_pro->GridInfo.nz;	  // data bytes of per-level
            ll_temp.data[iz].header.levelnum = i_pro->GridInfo.nz;       // level numbers of data 文件内一共的层数
            ll_temp.data[iz].header.amp = i_pro->DataBlock.at(0).ProDataInfo.DScale;            // amplify factor = 10; 放大系数，dbz乘上放大系数后存储
            ll_temp.data[iz].header.compmode = 0;       // 0 = LatLon grid; 1=sparse LatLon grid
            ll_temp.data[iz].header.dates = 0;  // UTC dates 日期
            ll_temp.data[iz].header.seconds = i_pro->ProInfo.ProductionTime;         // UTC seconds 秒
            ll_temp.data[iz].header.min_value = 0;       // used in compress mode
            ll_temp.data[iz].header.max_value = 0;       // used in compress mode
            ll_temp.data[iz].header.enablemultiLevel = 1;	  // 是否存储多层，0表示只有一层，1表示多层
            ll_temp.data[iz].header.height = i_pro->GridInfo.z.at(iz);   //  or  forecast_time;
            if (iz == i_pro->GridInfo.nz - 1)
            {
                ll_temp.data[iz].header.index_nextbytes = 0;	  // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
            }
            else if (iz == 0)
            {
                ll_temp.data[iz].header.index_nextbytes = sizeof(LLDF_HEADER) + ll_temp.data[iz].header.levelbytes;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
            }
            else
            {
                ll_temp.data[iz].header.index_nextbytes = ll_temp.data[iz - 1].header.index_nextbytes + sizeof(LLDF_HEADER) + ll_temp.data[iz].header.levelbytes;	 // 存下一层的开始位置，当只有一层或者已经是最后一层时，值为0
            }

            //            ll_temp.data[iz].header.reserved[0] = 0;
            //            ll_temp.data[iz].header.reserved[1] = 0;

//            ll_temp.data[iz].header.domain.slat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn /50000.0 * (0 - i_pro->GridInfo.ncolumn/2);
//            ll_temp.data[iz].header.domain.wlon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow /50000.0 * (0 - i_pro->GridInfo.nrow/2);  // 0.01 deg 西南角经纬度
//            ll_temp.data[iz].header.domain.nlat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn /50000.0 * (i_pro->GridInfo.ncolumn -1 - i_pro->GridInfo.ncolumn/2);
//            ll_temp.data[iz].header.domain.elon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow /50000.0 * (i_pro->GridInfo.nrow -1 - i_pro->GridInfo.nrow/2);  // 0.01 deg 东北角经纬度
            ll_temp.data[iz].header.domain.slat = i_pro->MapProjInfo.ctrlat - i_pro->GridInfo.dcolumn * i_pro->GridInfo.ncolumn / 100000.0;
            ll_temp.data[iz].header.domain.nlat = i_pro->MapProjInfo.ctrlat + i_pro->GridInfo.dcolumn * i_pro->GridInfo.ncolumn / 100000.0;
            ll_temp.data[iz].header.domain.wlon = i_pro->MapProjInfo.ctrlon - i_pro->GridInfo.drow * i_pro->GridInfo.nrow / 100000.0;  // 0.01 deg 西南角经纬度
            ll_temp.data[iz].header.domain.elon = i_pro->MapProjInfo.ctrlon + i_pro->GridInfo.drow * i_pro->GridInfo.nrow / 100000.0;  // 0.01 deg 东北角经纬度
            ll_temp.data[iz].header.domain.clat = i_pro->MapProjInfo.ctrlat;
            ll_temp.data[iz].header.domain.clon = i_pro->MapProjInfo.ctrlon;  // 0.01 deg  中心经纬度

            ll_temp.data[iz].header.domain.dlat = i_pro->GridInfo.dcolumn / 50000.0;
            ll_temp.data[iz].header.domain.dlon = i_pro->GridInfo.drow / 50000.0;  // minimize = 0.01 deg 经纬度单位间隔
            ll_temp.data[iz].data.resize(ll_temp.data[iz].header.levelbytes);

            //        ll_temp.data[iz].header.domain.rows = i_pro->GridInfo.nrow;
            //        ll_temp.data[iz].header.domain.cols = i_pro->GridInfo.ncolumn;  // 行列数
            //        memcpy(&ll_temp.data[iz].data.at(0),&i_pro->DataBlock.at(0).ProductData.at(iz*ll_temp.data[iz].header.levelbytes),ll_temp.data[iz].header.levelbytes);

            ll_temp.data[iz].header.domain.cols = i_pro->GridInfo.nrow;
            ll_temp.data[iz].header.domain.rows = i_pro->GridInfo.ncolumn;  // 行列数
            for (int i = 0; i < ll_temp.data[iz].header.domain.rows; i++)
            {
                int shift_org = (ll_temp.data[iz].header.domain.rows - 1 - i) * ll_temp.data[iz].header.domain.cols * ll_temp.data[iz].header.unitlen;
                int shift = i * ll_temp.data[iz].header.domain.cols * ll_temp.data[iz].header.unitlen;
                memcpy(&ll_temp.data[iz].data.at(shift), &i_pro->DataBlock.at(0).ProductData.at(iz * ll_temp.data[iz].header.levelbytes + shift_org), ll_temp.data[iz].header.domain.cols * ll_temp.data[iz].header.unitlen);
            }
        }
    }

    try
    {
        gzFile l_File;
        l_File = gzopen(FileName, "wb");

        for (int iz = 0; iz < ll_temp.data.size(); iz++)
        {
            gzwrite(l_File, (char *) & (ll_temp.data[iz].header), sizeof(LLDF_HEADER));
            gzwrite(l_File, (char *) & (ll_temp.data[iz].data[0]), ll_temp.data[iz].header.levelbytes);
        }
        gzclose(l_File);

        if (i_pro->ProInfo.ProductionID == PTYPE_MAX + 300)     // Mosaic CR
        {
            // TODO: save weight to txt
            short weight = 0;
            int scale = i_pro->DataBlock.at(0).ProDataInfo.DScale;
            int offset = i_pro->DataBlock.at(0).ProDataInfo.DOffset;
            if (scale == 0 || i_pro->DataBlock.at(0).ProductData.size() == 0)
            {
                weight = 0;
            }
            else
            {
                int count = 0;
                for (int i = 0; i < i_pro->DataBlock.at(0).ProductData.size() / 2; i += 2)
                {
                    if ((*(short *)&i_pro->DataBlock.at(0).ProductData.at(i * 2) - offset) / scale > 15)
                    {
                        count++;
                    }
                }
                weight = 1000.0 * count / (i_pro->DataBlock.at(0).ProductData.size() / 2);
            }
            string strFullPath = string(FileName);
            string strTxtFileName = strFullPath.substr(0, strFullPath.find_last_of('.')) + ".txt";
            ofstream ofs;
            ofs.open(strTxtFileName.c_str(), ios::out | ios::trunc);
            if (ofs.is_open())
            {
                ofs << weight << endl;
                ofs.close();
            }
        }
        else if (i_pro->ProInfo.ProductionID >= 201 && i_pro->ProInfo.ProductionID <= 211)      // Mosaic CAPPI
        {
            // TODO: output by layer
            for (int layer = 0; layer < ll_temp.data.size(); ++layer)
            {
                if (ll_temp.data[layer].header.height <= 0)
                {
                    continue;
                }
                string strFullPath = string(FileName);
                string strPath = strFullPath.substr(0, strFullPath.find_last_of('/'));
                string strFullName = strFullPath.substr(strFullPath.find_last_of('/') + 1);
                string strName = strFullName.substr(0, strFullName.find_first_of(".latlon"));
                string strSuffix = strFullName.substr(strFullName.find_first_of(".latlon") + 1);
                string strNewFullPath = strPath + "/" + strName + "_" + std::to_string(ll_temp.data[layer].header.height) + "." + strSuffix;
                gzFile l_subFile;
                l_subFile = gzopen(strNewFullPath.c_str(), "wb");
                ll_temp.data[layer].header.index_nextbytes = 0;
                ll_temp.data[layer].header.levelnum = 1;
                ll_temp.data[layer].header.enablemultiLevel = 0;
                gzwrite(l_subFile, (char *) & (ll_temp.data[layer].header), sizeof(LLDF_HEADER));
                gzwrite(l_subFile, (char *) & (ll_temp.data[layer].data[0]), ll_temp.data[layer].header.levelbytes);
                gzclose(l_subFile);
            }
        }
        else if (i_pro->ProInfo.ProductionID >= 241 && i_pro->ProInfo.ProductionID <= 251)      // 等仰角面组网产品
        {
            //TODO: output by layer(except for the top one) & output the top layer as RELCR when ProductionID equals 242
            for (int layer = 0; layer < ll_temp.data.size() - 1; ++layer)
            {
                if (ll_temp.data[layer].header.height <= 0)
                {
                    continue;
                }
                string strFullPath = string(FileName);
                string strPath = strFullPath.substr(0, strFullPath.find_last_of('/'));
                string strFullName = strFullPath.substr(strFullPath.find_last_of('/') + 1);
                string strName = strFullName.substr(0, strFullName.find_first_of(".latlon"));
                string strSuffix = strFullName.substr(strFullName.find_first_of(".latlon") + 1);
                string strNewFullPath = strPath + "/" + strName + "_" + std::to_string(ll_temp.data[layer].header.height) + "." + strSuffix;
                gzFile l_subFile;
                l_subFile = gzopen(strNewFullPath.c_str(), "wb");
                ll_temp.data[layer].header.index_nextbytes = 0;
                ll_temp.data[layer].header.levelnum = 1;
                ll_temp.data[layer].header.enablemultiLevel = 0;
                gzwrite(l_subFile, (char *) & (ll_temp.data[layer].header), sizeof(LLDF_HEADER));
                gzwrite(l_subFile, (char *) & (ll_temp.data[layer].data[0]), ll_temp.data[layer].header.levelbytes);
                gzclose(l_subFile);
            }
            if (i_pro->ProInfo.ProductionID == 242)
            {
                int layer = ll_temp.data.size() - 1;
                string strFullPath = string(FileName);
                string strPath = strFullPath.substr(0, strFullPath.find_last_of('/'));
                strPath = strPath.replace(strPath.find_last_of("RECR") - 3, 4, "RELCR");
                DIR *dir = opendir(strPath.c_str());
                if (dir)
                {
                    closedir(dir);
                }
                else
                {
                    std::string cmd = "mkdir -p " + strPath;
                    system(cmd.c_str());
                }
                string strFullName = strFullPath.substr(strFullPath.find_last_of('/') + 1);
                strFullName = strFullName.replace(strFullName.find("RECR"), 4, "RELCR");
                string strNewFullPath = strPath + "/" + strFullName;
                gzFile l_subFile;
                l_subFile = gzopen(strNewFullPath.c_str(), "wb");
                ll_temp.data[layer].header.index_nextbytes = 0;
                ll_temp.data[layer].header.levelnum = 1;
                ll_temp.data[layer].header.enablemultiLevel = 0;
                gzwrite(l_subFile, (char *) & (ll_temp.data[layer].header), sizeof(LLDF_HEADER));
                gzwrite(l_subFile, (char *) & (ll_temp.data[layer].data[0]), ll_temp.data[layer].header.levelbytes);
                gzclose(l_subFile);
            }
        }
    }
    catch (...)
    {
        cout << "Save file error." << endl;
        return false;
    }

    return true;
}

void CNrietFileIO::getSITECODE(string SITECODE)
{
    m_SITECODE = SITECODE;
}

void CNrietFileIO::gettime_opticalFlow(string Time_opticalFlow)
{
    m_time_opticalFlow = Time_opticalFlow;
}

void *CNrietFileIO::GetFileName(void *data, int standard = 0)
{
    memset(&m_aFileName[0], 0x00, sizeof(m_aFileName) / sizeof(m_aFileName[0]));
    if (standard == 0)
    {
        if (IsRadarRawData(data))
        {
            return GetRadarRawFileName(data);
        }

        if (IsRadarProData(data))
        {
            return GetRadarProFileName(data);
        }

        if (IsRadarLatlonData(data))
        {
            return GetRadarLatlonFileName(data);
        }
    }
    else if (standard == 1)
    {
        if (IsRadarKJCProData(data))
        {
            return GetRadarKJCProFileName(data);
        }

        if (IsRadarLatlonData(data))
        {
            return GetRadarKJCLatlonFileName(data);
        }
    }
    else if (standard == 2)
    {
        return GetRadarQCFileName(data);
    }
    return nullptr;
}

char *CNrietFileIO::GetRadarRawFileName(void *ProPoint)
{
    WRADRAWDATA *RadarProduct = (WRADRAWDATA *)ProPoint;

    //char* fp;

    string FileDir;
    string FileName;
    //WRADPRODATA_PARA_IN* RadarProduct = (WRADPRODATA_PARA_IN*)ProPoint;
    char *SiteName = RadarProduct->commonBlock.siteconfig.SiteName;
    char *SiteCode = RadarProduct->commonBlock.siteconfig.SiteCode;
    //string Proname;

    time_t pro_time_t = RadarProduct->commonBlock.taskconfig.ScanStartTime;

    tm pro_tm = *(gmtime(&pro_time_t));
    char yyyymmddhhmmss[16] = {0};

    sprintf(&yyyymmddhhmmss[0], "%4.4d", pro_tm.tm_year + 1900);
    sprintf(&yyyymmddhhmmss[4], "%2.2d", pro_tm.tm_mon + 1);
    sprintf(&yyyymmddhhmmss[6], "%2.2d", pro_tm.tm_mday);
    sprintf(&yyyymmddhhmmss[8], "%2.2d", pro_tm.tm_hour);
    sprintf(&yyyymmddhhmmss[10], "%2.2d", pro_tm.tm_min);
    sprintf(&yyyymmddhhmmss[12], "%2.2d", pro_tm.tm_sec);
    char yyyymmdd[16] = {0};
    strncpy(yyyymmdd, yyyymmddhhmmss, 8);
    char yyyymmddhh[16] = {0};
    strncpy(yyyymmddhh, yyyymmddhhmmss, 10);

    FileName = "Z_RADR_I_" + string(SiteCode) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_CAP_FMT.bin";
    FileDir = string(SiteCode) + "/" + string(yyyymmdd) + "/" + string(yyyymmddhh) + "/";
    if (RadarProduct->commonBlock.cutconfig.front().dBTMask == 0)
    {
        FileDir += "Std/";
    }
    else if (RadarProduct->commonBlock.cutconfig.front().dBTMask == 1)
    {
        FileDir += "StdQC/";
    }

    if (RadarProduct->commonBlock.taskconfig.ScanType == 0 || RadarProduct->commonBlock.taskconfig.ScanType == 1)
    {
        FileDir += "VTB/" ;
    }
    else if (RadarProduct->commonBlock.taskconfig.ScanType == 2)
    {
        FileDir += "RHI/" ;
    }
    else
    {
        FileDir += "UNKNOWN/" ;
    }
    //    FileDir = string(SiteCode) + "/" + string(yyyymmdd) + "/" ;

    string temp = FileDir + FileName;
    strncpy(m_aFileName, temp.c_str(), 127);

    return m_aFileName;
}

char *CNrietFileIO::GetRadarQCFileName(void *data)
{
    WRADRAWDATA *QCFile = (WRADRAWDATA *)data;

    string FileDir;
    string FileName;
//    char *SiteCode = QCFile->commonBlock.siteconfig.SiteCode;
//    std::string sitecode;
//    sitecode = m_SITECODE;
    if (m_SITECODE.size() < 5)
    {
        m_SITECODE.insert(0, 5 - m_SITECODE.size(), '0');
    }
//    sitecode.assign(SiteCode);
    string Proname = "QC";

    // radartype
    short radartype = QCFile->commonBlock.siteconfig.RadarType;
    string RadarType;
    switch (radartype)
    {
        case 1:
            RadarType = "SC00";
            break;
        case 2:
            RadarType = "SB00";
            break;
        case 3:
            RadarType = "SC00";
            break;
        case 4:
            RadarType = "SAD0";
            break;
        case 5:
            RadarType = "SBD0";
            break;
        case 6:
            RadarType = "SCD0";
            break;
        case 33:
            RadarType = "CA00";
            break;
        case 34:
            RadarType = "CB00";
            break;
        case 35:
            RadarType = "CC00";
            break;
        case 36:
            RadarType = "CCJ0";
            break;
        case 37:
            RadarType = "CD00";
            break;
        case 38:
            RadarType = "CAD0";
            break;
        case 39:
            RadarType = "CBD0";
            break;
        case 40:
            RadarType = "CCD0";
            break;
        case 41:
            RadarType = "CCJD";
            break;
        case 42:
            RadarType = "CDD0";
            break;
        case 65:
            RadarType = "XA00";
            break;
        case 66:
            RadarType = "XAD0";
            break;
        case 720:
            RadarType = "720A";
            break;
        case 721:
            RadarType = "7210";
            break;
        case 717:
            RadarType = "7170";
            break;
        case 784: // NewDual_784
            RadarType = "06SD";
            break;
        default:
            RadarType = "UnKnown";
            break;
    }

//    // ScanStartTime
//    time_t pro_time_t = QCFile->commonBlock.taskconfig.ScanStartTime;

//    tm pro_tm = *(gmtime(&pro_time_t));
//    char yyyymmddhhmmss[16] = {0};

//    sprintf(&yyyymmddhhmmss[0], "%4.4d", pro_tm.tm_year + 1900);
//    sprintf(&yyyymmddhhmmss[4], "%2.2d", pro_tm.tm_mon + 1);
//    sprintf(&yyyymmddhhmmss[6], "%2.2d", pro_tm.tm_mday);
//    sprintf(&yyyymmddhhmmss[8], "%2.2d", pro_tm.tm_hour);
//    sprintf(&yyyymmddhhmmss[10], "%2.2d", pro_tm.tm_min);
//    sprintf(&yyyymmddhhmmss[12], "%2.2d", pro_tm.tm_sec);
//    char yyyymmdd[16] = {0};
//    strncpy(yyyymmdd, yyyymmddhhmmss, 8);
//    char yyyymmddhh[16] = {0};
//    strncpy(yyyymmddhh, yyyymmddhhmmss, 10);

    char Elevation[8] = {0}; // Unit:0.1 degree
    strcpy(Elevation, "NUL");

    std::string sitecode;
    auto it = std::find_if(m_SITECODE.begin(), m_SITECODE.end(), [](char c)
    {
        return c != '0';
    });
    // 如果找到了，取出该位置及其后面的字符
    if (it != m_SITECODE.end())
    {
        sitecode = std::string(it, m_SITECODE.end());
    }
    string frontdir = "QC";
    FileName = "KLG" + m_SITECODE + RadarType + m_fileTime + "_" + Proname;
//    FileDir = frontdir + "/" + sitecode + "/" + m_fileTime.substr(0, 8) + "/" + m_fileTime.substr(0, 10) + "/";
    FileDir = frontdir + "/" + sitecode + "/" + m_fileTime.substr(0, 8) + "/";
//m_FileName_out->at(i_pro) = new char[128];
    string temp = FileDir + FileName;
    strncpy(m_aFileName, temp.c_str(), 127);
//    std::cout << "file path:" << temp << endl;
    return m_aFileName;
}

char *CNrietFileIO::GetRadarProFileName(void *ProPoint)
{
    WRADPRODATA_PARA_IN *RadarProduct = (WRADPRODATA_PARA_IN *)ProPoint;

    //char* fp;
    const char *nul = "NUL";
    char Elevation[8] = {0}; // Unit:0.1 degree
    char MaxDistance[8] = {0}; // Unit:km
    char BinResolutionofRadial[8] = {0}; //Unit:100m
    char RowResolutionofGrid[8] = {0};   //Unit:100m
    char ColumnResolutionofGrid[8] = {0}; //Unit:100m
    string FileDir;
    string FileName;
    //WRADPRODATA_PARA_IN* RadarProduct = (WRADPRODATA_PARA_IN*)ProPoint;
//    char *SiteName = RadarProduct->commonBlock.siteconfig.SiteCode;
//    char *SiteCode = RadarProduct->commonBlock.siteconfig.SiteCode;
//    std::string sitecode;
//    sitecode = m_SITECODE;
    if (m_SITECODE.size() < 5)
    {
        m_SITECODE.insert(0, 5 - m_SITECODE.size(), '0');
    }
//    sitecode.assign(SiteCode);

    string Proname;

    sprintf(MaxDistance, "%d", RadarProduct->commonBlock.cutconfig.at(0).MaximumRange1 / 1000);
    if (RadarProduct->commonBlock.cutconfig.at(0).LogResolution >= 100)
    {
        sprintf(BinResolutionofRadial, "%d", RadarProduct->commonBlock.cutconfig.at(0).LogResolution / 100);
    }
    else
    {
        sprintf(BinResolutionofRadial, "%.1f", RadarProduct->commonBlock.cutconfig.at(0).LogResolution / 100.0);
    }

    for (int i_cut = 0; i_cut < RadarProduct->commonBlock.cutconfig.size(); i_cut++)
    {
        if (fabs(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation - RadarProduct->commonBlock.cutconfig.at(i_cut).Elevation) < 0.1)
        {
            sprintf(MaxDistance, "%d", RadarProduct->commonBlock.cutconfig.at(i_cut).MaximumRange1 / 1000);
            if (RadarProduct->commonBlock.cutconfig.at(i_cut).LogResolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", RadarProduct->commonBlock.cutconfig.at(i_cut).LogResolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", RadarProduct->commonBlock.cutconfig.at(i_cut).LogResolution / 100.0);
            }
            break;
        }
    }

    time_t pro_time_t = RadarProduct->commonBlock.taskconfig.ScanStartTime;

    tm pro_tm = *(gmtime(&pro_time_t));
    char yyyymmddhhmmss[16] = {0};

    sprintf(&yyyymmddhhmmss[0], "%4.4d", pro_tm.tm_year + 1900);
    sprintf(&yyyymmddhhmmss[4], "%2.2d", pro_tm.tm_mon + 1);
    sprintf(&yyyymmddhhmmss[6], "%2.2d", pro_tm.tm_mday);
    sprintf(&yyyymmddhhmmss[8], "%2.2d", pro_tm.tm_hour);
    sprintf(&yyyymmddhhmmss[10], "%2.2d", pro_tm.tm_min);
    sprintf(&yyyymmddhhmmss[12], "%2.2d", pro_tm.tm_sec);
    char yyyymmdd[16] = {0};
    strncpy(yyyymmdd, yyyymmddhhmmss, 8);
    char yyyymmddhh[16] = {0};
    strncpy(yyyymmddhh, yyyymmddhhmmss, 10);

//    time_t pro_time_t_exp = RadarProduct->productheader.productheader.DataEndTime;
//    tm pro_tm_exp = *(gmtime(&pro_time_t_exp));
//    char yyyymmddhhmmss_exp[16] = {0};
//    sprintf(&yyyymmddhhmmss_exp[0], "%4.4d", pro_tm_exp.tm_year + 1900);
//    sprintf(&yyyymmddhhmmss_exp[4], "%2.2d", pro_tm_exp.tm_mon + 1);
//    sprintf(&yyyymmddhhmmss_exp[6], "%2.2d", pro_tm_exp.tm_mday);
//    sprintf(&yyyymmddhhmmss_exp[8], "%2.2d", pro_tm_exp.tm_hour);
//    sprintf(&yyyymmddhhmmss_exp[10], "%2.2d", pro_tm_exp.tm_min);
//    sprintf(&yyyymmddhhmmss_exp[12], "%2.2d", pro_tm_exp.tm_sec);
//    char yyyymmdd_exp[16] = {0};
//    strncpy(yyyymmdd_exp, yyyymmddhhmmss_exp, 8);
//    char yyyymmddhh_exp[16] = {0};
//    strncpy(yyyymmddhh_exp, yyyymmddhhmmss_exp, 10);

    string frontdir = "RADA/RADA_PUP/";

    // radartype
    short radartype = RadarProduct->commonBlock.siteconfig.RadarType;
    string RadarType;
    switch (radartype)
    {
        case 1:
            RadarType = "SC00";
            break;
        case 2:
            RadarType = "SB00";
            break;
        case 3:
            RadarType = "SC00";
            break;
        case 4:
            RadarType = "SAD0";
            break;
        case 5:
            RadarType = "SBD0";
            break;
        case 6:
            RadarType = "SCD0";
            break;
        case 33:
            RadarType = "CA00";
            break;
        case 34:
            RadarType = "CB00";
            break;
        case 35:
            RadarType = "CC00";
            break;
        case 36:
            RadarType = "CCJ0";
            break;
        case 37:
            RadarType = "CD00";
            break;
        case 38:
            RadarType = "CAD0";
            break;
        case 39:
            RadarType = "CBD0";
            break;
        case 40:
            RadarType = "CCD0";
            break;
        case 41:
            RadarType = "CCJD";
            break;
        case 42:
            RadarType = "CDD0";
            break;
        case 65:
            RadarType = "XA00";
            break;
        case 66:
            RadarType = "XAD0";
            break;
        case 720:
            RadarType = "720A";
            break;
        case 721:
            RadarType = "7210";
            break;
        case 717:
            RadarType = "7170";
            break;
        case 784: // NewDual_784
            RadarType = "06SD";
            break;
        default:
            RadarType = "UnKnown";
            break;
    }

    string Syyyymmdd_exp;
    string Syyyymmddhh_exp;
    string Syyyymmddhhmmss_exp;

    time_t pro_time_t_exp = RadarProduct->productheader.productheader.DataEndTime;
    tm pro_tm_exp = *(gmtime(&pro_time_t_exp));
    char yyyymmddhhmmss_exp[16] = {0};
    sprintf(&yyyymmddhhmmss_exp[0], "%4.4d", pro_tm_exp.tm_year + 1900);
    sprintf(&yyyymmddhhmmss_exp[4], "%2.2d", pro_tm_exp.tm_mon + 1);
    sprintf(&yyyymmddhhmmss_exp[6], "%2.2d", pro_tm_exp.tm_mday);
    sprintf(&yyyymmddhhmmss_exp[8], "%2.2d", pro_tm_exp.tm_hour);
    sprintf(&yyyymmddhhmmss_exp[10], "%2.2d", pro_tm_exp.tm_min);
    sprintf(&yyyymmddhhmmss_exp[12], "%2.2d", pro_tm_exp.tm_sec);
    char yyyymmdd_exp[16] = {0};
    strncpy(yyyymmdd_exp, yyyymmddhhmmss_exp, 8);
    char yyyymmddhh_exp[16] = {0};
    strncpy(yyyymmddhh_exp, yyyymmddhhmmss_exp, 10);

    if (RadarType == "720A" || RadarType == "7210" || RadarType == "7170" || RadarType == "06SD")
    {
        Syyyymmdd_exp = m_fileTime.substr(0, 8);
        Syyyymmddhh_exp = m_fileTime.substr(0, 10);
        Syyyymmddhhmmss_exp = m_fileTime.substr(0, 14);
    }
    else
    {
        Syyyymmdd_exp = string(yyyymmdd_exp);
        Syyyymmddhh_exp = string(yyyymmddhh_exp);
        Syyyymmddhhmmss_exp = string(yyyymmddhhmmss_exp);
    }

    float multiplied;
    int rounded;

    string yyyymmdd_opticalFlow, yyyymmddhh_opticalFlow;
    yyyymmdd_opticalFlow = m_time_opticalFlow.substr(0, 8);
    yyyymmddhh_opticalFlow = m_time_opticalFlow.substr(0, 10);

    switch (RadarProduct->productheader.productheader.ProductType)
    {
        case PTYPE_PPI: // 1://PPI
            switch (RadarProduct->productheader.productheader.DataType1)
            {
                case 1:
                    Proname = "DBT";
                    break;
                case 2:
                    Proname = "DBZ";
                    break;
                case 3:
                    Proname = "V";
                    break;
                case 4:
                    Proname = "SW";
                    break;
                case 5:
                    Proname = "SQI";
                    break;
                case 7:
                    Proname = "ZDR";
                    break;
                case 8:
                    Proname = "LDR";
                    break;
                case 9:
                    Proname = "CC";
                    break;
                case 10:
                    Proname = "PHDP";
                    break;
                case 11:
                    Proname = "KDP";
                    break;
                case 15:
                    Proname = "CF";
                    break;
                case 16:
                    Proname = "SNRH";
                    break;
                case 17:
                    Proname = "SNRV";
                    break;
                default:
                    Proname = "UnKnown";
                    break;
            }
            Proname = "PPI" + Proname;
            //if (RadarProduct->commonBlock.cutconfig.front().dBTMask == 1) Proname = "QC" + Proname;
            //if (((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100){
            //    sprintf(BinResolutionofRadial,"%d",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100);
            //}
            //else{
            sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            //}
//            sprintf(Elevation, "%d", (int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 10));
            multiplied = RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 10.0f;
            rounded = qRound(multiplied);
            sprintf(Elevation, "%d", rounded);
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname + string(Elevation);
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_RHI: // 2://RHI
            switch (RadarProduct->productheader.productheader.DataType1)
            {
                case 1:
                    Proname = "DBT";
                    break;
                case 2:
                    Proname = "DBZ";
                    break;
                case 3:
                    Proname = "V";
                    break;
                case 4:
                    Proname = "SW";
                    break;
                case 7:
                    Proname = "ZDR";
                    break;
                case 8:
                    Proname = "LDR";
                    break;
                case 9:
                    Proname = "CC";
                    break;
                case 10:
                    Proname = "PHDP";
                    break;
                case 11:
                    Proname = "KDP";
                    break;
                case 15:
                    Proname = "CF";
                    break;
                case 16:
                    Proname = "SNRH";
                    break;
                case 17:
                    Proname = "SNRV";
                    break;
                default:
                    Proname = "UnKnown";
                    break;
            }
            Proname = "RHI" + Proname;
            //if (RadarProduct->commonBlock.cutconfig.front().dBTMask == 1) Proname = "QC" + Proname;
//            sprintf(Elevation, "%d", (int)round(RadarProduct->productheader.productdependentparameter.rhiparameter.Azimuth * 10));
            sprintf(Elevation, "%d", (int)round(RadarProduct->productheader.productdependentparameter.rhiparameter.Azimuth));
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_SRM: //SRM PPI
            Proname = "SRM";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
//            sprintf(Elevation, "%d", (int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 10));
            multiplied = RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 10.0f;
            rounded = qRound(multiplied);
            sprintf(Elevation, "%d", rounded);
//            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + Proname + string(Elevation);
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname + string(Elevation);
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_ML:
            Proname = "ML";
            sprintf(Elevation, "%d", (int)(RadarProduct->productheader.productdependentparameter.mlparameter.Elevation * 10));
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + Proname + string(Elevation);
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + "NUL" + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_CAPPI: // 3://CAPPI //格点
            switch (RadarProduct->productheader.productheader.DataType1)
            {
                case 1:
                    Proname = "DBT";
                    break;
                case 2:
                    Proname = "DBZ";
                    break;
                case 3:
                    Proname = "V";
                    break;
                case 4:
                    Proname = "SW";
                    break;
                case 7:
                    Proname = "ZDR";
                    break;
                case 8:
                    Proname = "LDR";
                    break;
                case 9:
                    Proname = "CC";
                    break;
                case 10:
                    Proname = "PHDP";
                    break;
                case 11:
                    Proname = "KDP";
                    break;
                case 16:
                    Proname = "SNRH";
                    break;
                case 17:
                    Proname = "SNRV";
                    break;
                default:
                    Proname = "UnKnown";
                    break;
            }
            Proname = "CAPPI" + Proname;
            if (((CAPPIFORMAT *)RadarProduct->productdatapoint)->CappiData.at(0).RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((CAPPIFORMAT *)RadarProduct->productdatapoint)->CappiData.at(0).RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((CAPPIFORMAT *)RadarProduct->productdatapoint)->CappiData.at(0).RadialHeader.Resolution / 100.0);
            }
            strcpy(Elevation, "NUL");
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_MAX: //MAX //格点
            strcpy(Elevation, "NUL");
            Proname = "MAX";
            if (((MAXFORMAT *)RadarProduct->productdatapoint)->MAXData->RasterHeader.RowResolution >= 100)
            {
                sprintf(RowResolutionofGrid, "%d", ((MAXFORMAT *)RadarProduct->productdatapoint)->MAXData->RasterHeader.RowResolution / 100);
            }
            else
            {
                sprintf(RowResolutionofGrid, "%.1f", ((MAXFORMAT *)RadarProduct->productdatapoint)->MAXData->RasterHeader.RowResolution / 100.0);
            }
            if (((MAXFORMAT *)RadarProduct->productdatapoint)->MAXData->RasterHeader.ColumnResolution >= 100)
            {
                sprintf(ColumnResolutionofGrid, "%d", ((MAXFORMAT *)RadarProduct->productdatapoint)->MAXData->RasterHeader.ColumnResolution / 100);
            }
            else
            {
                sprintf(ColumnResolutionofGrid, "%.1f", ((MAXFORMAT *)RadarProduct->productdatapoint)->MAXData->RasterHeader.ColumnResolution / 100.0);
            }
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(RowResolutionofGrid) + "x" + string(ColumnResolutionofGrid) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_ET://ET //格点
            strcpy(Elevation, "NUL");
            Proname = "ET";
            if (((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.RowResolution >= 100)
            {
                sprintf(RowResolutionofGrid, "%d", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.RowResolution / 100);
            }
            else
            {
                sprintf(RowResolutionofGrid, "%.1f", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.RowResolution / 100.0);
            }
            if (((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution >= 100)
            {
                sprintf(ColumnResolutionofGrid, "%d", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution / 100);
            }
            else
            {
                sprintf(ColumnResolutionofGrid, "%.1f", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution / 100.0);
            }
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(RowResolutionofGrid) + "x" + string(ColumnResolutionofGrid) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_EB://EB //格点
            strcpy(Elevation, "NUL");
            Proname = "EB";
            if (((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.RowResolution >= 100)
            {
                sprintf(RowResolutionofGrid, "%d", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.RowResolution / 100);
            }
            else
            {
                sprintf(RowResolutionofGrid, "%.1f", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.RowResolution / 100.0);
            }
            if (((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution >= 100)
            {
                sprintf(ColumnResolutionofGrid, "%d", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution / 100);
            }
            else
            {
                sprintf(ColumnResolutionofGrid, "%.1f", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution / 100.0);
            }
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(RowResolutionofGrid) + "x" + string(ColumnResolutionofGrid) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
            break;
        case PTYPE_VIL://VIL //格点
            strcpy(Elevation, "NUL");
            Proname = "VIL";
            if (((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.RowResolution >= 100)
            {
                sprintf(RowResolutionofGrid, "%d", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.RowResolution / 100);
            }
            else
            {
                sprintf(RowResolutionofGrid, "%.1f", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.RowResolution / 100.0);
            }
            if (((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution >= 100)
            {
                sprintf(ColumnResolutionofGrid, "%d", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution / 100);
            }
            else
            {
                sprintf(ColumnResolutionofGrid, "%.1f", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution / 100.0);
            }
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(RowResolutionofGrid) + "x" + string(ColumnResolutionofGrid) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
            break;
        case PTYPE_CR://CR RADIAL_FORMAT
            Proname = "CR";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            strcpy(Elevation, "NUL");
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
            break;
        case PTYPE_CRH_RADIAL://CRH RADIAL_FORMAT
            Proname = "CRH";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            strcpy(Elevation, "NUL");
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
            break;
        case PTYPE_ET_RADIAL://ET RADIAL_FORMAT
            Proname = "ET";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            strcpy(Elevation, "NUL");
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
            break;
        case PTYPE_EB_RADIAL://EB RADIAL_FORMAT
            Proname = "EB";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            strcpy(Elevation, "NUL");
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
            break;
        case PTYPE_VIL_RADIAL://ET RADIAL_FORMAT
            Proname = "VIL";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            strcpy(Elevation, "NUL");
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
            break;
        case PTYPE_OHP://OHP
            Proname = "OHP";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            //sprintf(Elevation,"%d",(int)(RadarProduct->commonBlock.cutconfig.at(0).Elevation*10));
            strcpy(Elevation, "NUL");
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_PolarOHP://OHP
            Proname = "PolarOHP";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            //sprintf(Elevation,"%d",(int)(RadarProduct->commonBlock.cutconfig.at(0).Elevation*10));
            strcpy(Elevation, "NUL");
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + Proname + string(Elevation);
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_THP://THP
            strcpy(Elevation, "NUL");
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + Proname + string(Elevation);
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_USP://USP
            strcpy(Elevation, "NUL");
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + Proname + string(Elevation);
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_VAD://VAD
            Proname = "VAD";
            strcpy(Elevation, "NUL");
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + "NUL" + "_" + "NUL" + "_" + "NUL" + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_VWP://VWP
            Proname = "VWP";
            strcpy(Elevation, "NUL");
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + "NUL" + "_" + "NUL" + "_" + "NUL" + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_STI://STI
            Proname = "STI";
            strcpy(Elevation, "NUL");
            strcpy(BinResolutionofRadial, "NUL");
//            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + Proname + string(Elevation);
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_HI://HI
            Proname = "HI";
            strcpy(Elevation, "NUL");
            strcpy(BinResolutionofRadial, "NUL");
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_M://MESO
            Proname = "M";
            strcpy(Elevation, "NUL");
            strcpy(BinResolutionofRadial, "NUL");
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_TVS://TVS
            Proname = "TVS";
            strcpy(Elevation, "NUL");
            strcpy(BinResolutionofRadial, "NUL");
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + Proname + string(Elevation);
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_SS://SS
            Proname = "SS";
            strcpy(Elevation, "NUL");
            strcpy(BinResolutionofRadial, "NUL");
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_DB://DB
            Proname = "DB";
            strcpy(Elevation, "NUL");
            strcpy(BinResolutionofRadial, "NUL");
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_GF://GF
            Proname = "GF";
            strcpy(Elevation, "NUL");
            strcpy(BinResolutionofRadial, "NUL");
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_RS://RS
            Proname = "RS";
            strcpy(Elevation, "NUL");
            strcpy(BinResolutionofRadial, "NUL");
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + Proname + string(Elevation);
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_QPE:
            Proname = "QPE";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            //sprintf(Elevation,"%d",(int)(RadarProduct->commonBlock.cutconfig.at(0).Elevation*10));
            strcpy(Elevation, "NUL");
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_PolarQPE:
            Proname = "PolarQPE";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            //sprintf(Elevation,"%d",(int)(RadarProduct->commonBlock.cutconfig.at(0).Elevation*10));
            strcpy(Elevation, "NUL");
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + Proname + string(Elevation);
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_STP: // 27 STP RADIAL
            Proname = "STP";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            strcpy(Elevation, "NUL");
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + Proname + string(Elevation);
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_PolarSTP:    // 57 PolarSTP RADIAL
            Proname = "PolarSTP";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            strcpy(Elevation, "NUL");
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + Proname + string(Elevation);
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_HCL: // 51://HCL //MRADIAL
            Proname = "HCL";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            //        strcpy(Elevation,"NUL");
            sprintf(Elevation, "%d", (int)(RadarProduct->productheader.productdependentparameter.hclparameter.Elevation * 10));
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + Proname + string(Elevation);
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_RVD: // 101 RVD RADIAL
            Proname += "RVD";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
//            sprintf(Elevation, "%d", (int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 10));
            multiplied = RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 10.0f;
            rounded = qRound(multiplied);
            sprintf(Elevation, "%d", rounded);
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname + string(Elevation);
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_ARD: // 102 ARD RADIAL
            Proname += "ARD";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
//            sprintf(Elevation, "%d", (int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 10));
            multiplied = RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 10.0f;
            rounded = qRound(multiplied);
            sprintf(Elevation, "%d", rounded);
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname + string(Elevation);
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_CS: // 103 CS RADIAL
            Proname += "CS";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
//            sprintf(Elevation, "%d", (int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 10));
            multiplied = RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 10.0f;
            rounded = qRound(multiplied);
            sprintf(Elevation, "%d", rounded);
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname + string(Elevation);
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_FLOW://62//光流外推
            Proname += "EXP";
            // product end time
            if (RadarType == "720A" || RadarType == "7210" || RadarType == "7170" || RadarType == "06SD")
            {
                Syyyymmdd_exp = m_fileTime.substr(0, 8);
                Syyyymmddhh_exp = m_fileTime.substr(0, 10);
                Syyyymmddhhmmss_exp = string(yyyymmddhhmmss_exp);
                FileName = "KLG" + m_SITECODE + RadarType + string(m_fileTime.substr(0, 14)) + "_" + Proname + Syyyymmddhhmmss_exp;
            }
            else
            {
                Syyyymmdd_exp = yyyymmdd_opticalFlow;
                Syyyymmddhh_exp = yyyymmddhh_opticalFlow;
                Syyyymmddhhmmss_exp = string(yyyymmddhhmmss_exp);
                FileName = "KLG" + m_SITECODE + RadarType + m_time_opticalFlow + "_" + Proname + Syyyymmddhhmmss_exp;
            }
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_NUL" + "." + string(SiteCode) +  "." + string(yyyymmddhhmmss_exp) + ".BIN";
            break;
        case PTYPE_LTA:
            Proname = "LTA";
//            sprintf(BinResolutionofRadial, "%d", ((CAPPIFORMAT *)RadarProduct->productdatapoint)->CappiData.at(0).RadialHeader.Resolution);
//            strcpy(Elevation, "NUL");
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_" + \
//                       RadarType + "_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "_FMT.bin";
            break;
        case PTYPE_LTM:
            Proname = "LTM";
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
//            sprintf(BinResolutionofRadial, "%d", ((CAPPIFORMAT *)RadarProduct->productdatapoint)->CappiData.at(0).RadialHeader.Resolution);
//            strcpy(Elevation, "NUL");
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_" + \
//                       RadarType + "_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "_FMT.bin";
            break;
        case PTYPE_LTH:
            Proname = "LTH";
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;
//            sprintf(BinResolutionofRadial, "%d", ((CAPPIFORMAT *)RadarProduct->productdatapoint)->CappiData.at(0).RadialHeader.Resolution);
//            strcpy(Elevation, "NUL");
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_" + \
//                       RadarType + "_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "_FMT.bin";
            break;
        default:
            Proname = "UnKnown";
            FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + Proname + string(Elevation);
//            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + to_string(RadarProduct->productheader.productheader.ProductType) + "_" + string(nul) + "_" + string(nul) + "_" + string(nul) + "." + string(SiteCode) + ".BIN";
            break;
    }

    std::string sitecode;
    auto it = std::find_if(m_SITECODE.begin(), m_SITECODE.end(), [](char c)
    {
        return c != '0';
    });
    // 如果找到了，取出该位置及其后面的字符
    if (it != m_SITECODE.end())
    {
        sitecode = std::string(it, m_SITECODE.end());
    }
    else
    {
        sitecode = m_SITECODE;
    }
//    FileDir = string(SiteName) + "/" + string(yyyymmdd) + "/" + string(yyyymmddhh) + "/" + Proname + "/";
    FileDir = frontdir + sitecode + "/" + Syyyymmdd_exp + "/" + Syyyymmddhh_exp + "/" + Proname + "/";
//m_FileName_out->at(i_pro) = new char[128];
    string temp = FileDir + FileName;
    strncpy(m_aFileName, temp.c_str(), 127);
//    std::cout << "file path:" << temp << endl;
    return m_aFileName;
}

/**
 * @brief CNrietFileIO::GetRadarProFileName_JS
 * @param ProPoint
 * @return
 */
char *CNrietFileIO::GetRadarProFileName_JS(void *ProPoint)
{
    WRADPRODATA_PARA_IN *RadarProduct = (WRADPRODATA_PARA_IN *)ProPoint;

    //char* fp;
    const char *nul = "NUL";
    char Elevation[8] = {0}; // Unit:0.1 degree
    char MaxDistance[8] = {0}; // Unit:km
    char BinResolutionofRadial[8] = {0}; //Unit:100m
    char RowResolutionofGrid[8] = {0};   //Unit:100m
    char ColumnResolutionofGrid[8] = {0}; //Unit:100m
    string FileDir;
    string FileName;
    //WRADPRODATA_PARA_IN* RadarProduct = (WRADPRODATA_PARA_IN*)ProPoint;
    char *SiteName = RadarProduct->commonBlock.siteconfig.SiteCode;
    char *SiteCode = RadarProduct->commonBlock.siteconfig.SiteCode;

    string Proname;

    sprintf(MaxDistance, "%d", RadarProduct->commonBlock.cutconfig.at(0).MaximumRange1 / 1000);
    if (RadarProduct->commonBlock.cutconfig.at(0).LogResolution >= 100)
    {
        sprintf(BinResolutionofRadial, "%d", RadarProduct->commonBlock.cutconfig.at(0).LogResolution / 100);
    }
    else
    {
        sprintf(BinResolutionofRadial, "%.1f", RadarProduct->commonBlock.cutconfig.at(0).LogResolution / 100.0);
    }

    for (int i_cut = 0; i_cut < RadarProduct->commonBlock.cutconfig.size(); i_cut++)
    {
        if (fabs(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation - RadarProduct->commonBlock.cutconfig.at(i_cut).Elevation) < 0.1)
        {
            sprintf(MaxDistance, "%d", RadarProduct->commonBlock.cutconfig.at(i_cut).MaximumRange1 / 1000);
            if (RadarProduct->commonBlock.cutconfig.at(i_cut).LogResolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", RadarProduct->commonBlock.cutconfig.at(i_cut).LogResolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", RadarProduct->commonBlock.cutconfig.at(i_cut).LogResolution / 100.0);
            }
            break;
        }
    }

    time_t pro_time_t = RadarProduct->commonBlock.taskconfig.ScanStartTime;

    tm pro_tm = *(gmtime(&pro_time_t));
    char yyyymmddhhmmss[16] = {0};

    sprintf(&yyyymmddhhmmss[0], "%4.4d", pro_tm.tm_year + 1900);
    sprintf(&yyyymmddhhmmss[4], "%2.2d", pro_tm.tm_mon + 1);
    sprintf(&yyyymmddhhmmss[6], "%2.2d", pro_tm.tm_mday);
    sprintf(&yyyymmddhhmmss[8], "%2.2d", pro_tm.tm_hour);
    sprintf(&yyyymmddhhmmss[10], "%2.2d", pro_tm.tm_min);
    sprintf(&yyyymmddhhmmss[12], "%2.2d", pro_tm.tm_sec);
    char yyyymmdd[16] = {0};
    strncpy(yyyymmdd, yyyymmddhhmmss, 8);
    char yyyymmddhh[16] = {0};
    strncpy(yyyymmddhh, yyyymmddhhmmss, 10);

    time_t pro_time_t_exp = RadarProduct->productheader.productheader.DataEndTime;
    tm pro_tm_exp = *(gmtime(&pro_time_t_exp));
    char yyyymmddhhmmss_exp[16] = {0};
    sprintf(&yyyymmddhhmmss_exp[0], "%4.4d", pro_tm_exp.tm_year + 1900);
    sprintf(&yyyymmddhhmmss_exp[4], "%2.2d", pro_tm_exp.tm_mon + 1);
    sprintf(&yyyymmddhhmmss_exp[6], "%2.2d", pro_tm_exp.tm_mday);
    sprintf(&yyyymmddhhmmss_exp[8], "%2.2d", pro_tm_exp.tm_hour);
    sprintf(&yyyymmddhhmmss_exp[10], "%2.2d", pro_tm_exp.tm_min);
    sprintf(&yyyymmddhhmmss_exp[12], "%2.2d", pro_tm_exp.tm_sec);

    switch (RadarProduct->productheader.productheader.ProductType)
    {
        case PTYPE_PPI: // 1://PPI
            switch (RadarProduct->productheader.productheader.DataType1)
            {
                case 1:
                    Proname = "UnR";
                    break;
                case 2:
                    Proname = "R";
                    break;
                case 3:
                    Proname = "V";
                    break;
                case 4:
                    Proname = "W";
                    break;
                case 5:
                    Proname = "SQI";
                    break;
                case 7:
                    Proname = "ZDR";
                    break;
                case 8:
                    Proname = "LDR";
                    break;
                case 9:
                    Proname = "CC";
                    break;
                case 10:
                    Proname = "PHDP";
                    break;
                case 11:
                    Proname = "KDP";
                    break;
                case 16:
                    Proname = "SNRH";
                    break;
                case 17:
                    Proname = "SNRV";
                    break;
                default:
                    Proname = "UnKnown";
                    break;
            }
            Proname += "PPI";
            if (RadarProduct->commonBlock.cutconfig.front().dBTMask == 1)
            {
                Proname = "QC" + Proname;
            }
            //if (((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100){
            //    sprintf(BinResolutionofRadial,"%d",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100);
            //}
            //else{
            sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            //}
            sprintf(Elevation, "%d", (int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 10));
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_RHI: // 2://RHI
            switch (RadarProduct->productheader.productheader.DataType1)
            {
                case 1:
                    Proname = "UnR";
                    break;
                case 2:
                    Proname = "R";
                    break;
                case 3:
                    Proname = "V";
                    break;
                case 4:
                    Proname = "W";
                    break;
                case 7:
                    Proname = "ZDR";
                    break;
                case 8:
                    Proname = "LDR";
                    break;
                case 9:
                    Proname = "CC";
                    break;
                case 10:
                    Proname = "PHDP";
                    break;
                case 11:
                    Proname = "KDP";
                    break;
                case 16:
                    Proname = "SNRH";
                    break;
                case 17:
                    Proname = "SNRV";
                    break;
                default:
                    Proname = "UnKnown";
                    break;
            }
            Proname += "RHI";
            if (RadarProduct->commonBlock.cutconfig.front().dBTMask == 1)
            {
                Proname = "QC" + Proname;
            }
            sprintf(Elevation, "%d", (int)round(RadarProduct->productheader.productdependentparameter.rhiparameter.Azimuth * 10));
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_SRM: //SRM PPI
            Proname = "SRM";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            sprintf(Elevation, "%d", (int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 10));
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_CAPPI: // 3://CAPPI //格点
            if (RadarProduct->productheader.productheader.DataType1 == 1)
            {
                Proname = "UnRCAR";
            }
            if (RadarProduct->productheader.productheader.DataType1 == 2)
            {
                Proname = "RCAR";
            }
            if (RadarProduct->productheader.productheader.DataType1 == 3)
            {
                Proname = "VCAR";
            }
            if (RadarProduct->productheader.productheader.DataType1 == 4)
            {
                Proname = "WCAR";
            }
            if (RadarProduct->productheader.productheader.DataType1 == 7)
            {
                Proname = "ZDRCAR";
            }
            if (RadarProduct->productheader.productheader.DataType1 == 8)
            {
                Proname = "LDRCAR";
            }
            if (RadarProduct->productheader.productheader.DataType1 == 9)
            {
                Proname = "CCCAR";
            }
            if (RadarProduct->productheader.productheader.DataType1 == 10)
            {
                Proname = "PHDPCAR";
            }
            if (RadarProduct->productheader.productheader.DataType1 == 11)
            {
                Proname = "KDPCAR";
            }
            if (RadarProduct->productheader.productheader.DataType1 == 16)
            {
                Proname = "SNRHCAR";
            }
            if (((CAPPIFORMAT *)RadarProduct->productdatapoint)->CappiData.at(0).RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((CAPPIFORMAT *)RadarProduct->productdatapoint)->CappiData.at(0).RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((CAPPIFORMAT *)RadarProduct->productdatapoint)->CappiData.at(0).RadialHeader.Resolution / 100.0);
            }
            strcpy(Elevation, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_MAX: //MAX //格点
            strcpy(Elevation, "NUL");
            Proname = "MAX";
            if (((MAXFORMAT *)RadarProduct->productdatapoint)->MAXData->RasterHeader.RowResolution >= 100)
            {
                sprintf(RowResolutionofGrid, "%d", ((MAXFORMAT *)RadarProduct->productdatapoint)->MAXData->RasterHeader.RowResolution / 100);
            }
            else
            {
                sprintf(RowResolutionofGrid, "%.1f", ((MAXFORMAT *)RadarProduct->productdatapoint)->MAXData->RasterHeader.RowResolution / 100.0);
            }
            if (((MAXFORMAT *)RadarProduct->productdatapoint)->MAXData->RasterHeader.ColumnResolution >= 100)
            {
                sprintf(ColumnResolutionofGrid, "%d", ((MAXFORMAT *)RadarProduct->productdatapoint)->MAXData->RasterHeader.ColumnResolution / 100);
            }
            else
            {
                sprintf(ColumnResolutionofGrid, "%.1f", ((MAXFORMAT *)RadarProduct->productdatapoint)->MAXData->RasterHeader.ColumnResolution / 100.0);
            }
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(RowResolutionofGrid) + "x" + string(ColumnResolutionofGrid) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_ET://ET //格点
            strcpy(Elevation, "NUL");
            Proname = "ET";
            if (((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.RowResolution >= 100)
            {
                sprintf(RowResolutionofGrid, "%d", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.RowResolution / 100);
            }
            else
            {
                sprintf(RowResolutionofGrid, "%.1f", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.RowResolution / 100.0);
            }
            if (((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution >= 100)
            {
                sprintf(ColumnResolutionofGrid, "%d", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution / 100);
            }
            else
            {
                sprintf(ColumnResolutionofGrid, "%.1f", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution / 100.0);
            }
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(RowResolutionofGrid) + "x" + string(ColumnResolutionofGrid) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_EB://EB //格点
            strcpy(Elevation, "NUL");
            Proname = "EB";
            if (((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.RowResolution >= 100)
            {
                sprintf(RowResolutionofGrid, "%d", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.RowResolution / 100);
            }
            else
            {
                sprintf(RowResolutionofGrid, "%.1f", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.RowResolution / 100.0);
            }
            if (((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution >= 100)
            {
                sprintf(ColumnResolutionofGrid, "%d", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution / 100);
            }
            else
            {
                sprintf(ColumnResolutionofGrid, "%.1f", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution / 100.0);
            }
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(RowResolutionofGrid) + "x" + string(ColumnResolutionofGrid) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_VIL://VIL //格点
            strcpy(Elevation, "NUL");
            Proname = "VIL";
            if (((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.RowResolution >= 100)
            {
                sprintf(RowResolutionofGrid, "%d", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.RowResolution / 100);
            }
            else
            {
                sprintf(RowResolutionofGrid, "%.1f", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.RowResolution / 100.0);
            }
            if (((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution >= 100)
            {
                sprintf(ColumnResolutionofGrid, "%d", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution / 100);
            }
            else
            {
                sprintf(ColumnResolutionofGrid, "%.1f", ((RASTERFORMAT *)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution / 100.0);
            }
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(RowResolutionofGrid) + "x" + string(ColumnResolutionofGrid) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_CR://CR RADIAL_FORMAT
            Proname = "CR";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            strcpy(Elevation, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_CRH_RADIAL://CRH RADIAL_FORMAT
            Proname = "CRH";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            strcpy(Elevation, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_ET_RADIAL://ET RADIAL_FORMAT
            Proname = "ET";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            strcpy(Elevation, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_EB_RADIAL://EB RADIAL_FORMAT
            Proname = "EB";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            strcpy(Elevation, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_VIL_RADIAL://ET RADIAL_FORMAT
            Proname = "VIL";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            strcpy(Elevation, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_OHP://OHP
            Proname = "OHP";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            //sprintf(Elevation,"%d",(int)(RadarProduct->commonBlock.cutconfig.at(0).Elevation*10));
            strcpy(Elevation, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_PolarOHP://OHP
            Proname = "PolarOHP";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            //sprintf(Elevation,"%d",(int)(RadarProduct->commonBlock.cutconfig.at(0).Elevation*10));
            strcpy(Elevation, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_THP://THP
            strcpy(Elevation, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_USP://USP
            strcpy(Elevation, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_VAD://VAD
            Proname = "VAD";
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + "NUL" + "_" + "NUL" + "_" + "NUL" + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_VWP://VWP
            Proname = "VWP";
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + "NUL" + "_" + "NUL" + "_" + "NUL" + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_STI://STI
            Proname = "STI";
            strcpy(Elevation, "NUL");
            strcpy(BinResolutionofRadial, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_HI://HI
            Proname = "HI";
            strcpy(Elevation, "NUL");
            strcpy(BinResolutionofRadial, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_M://MESO
            Proname = "M";
            strcpy(Elevation, "NUL");
            strcpy(BinResolutionofRadial, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_TVS://TVS
            Proname = "TVS";
            strcpy(Elevation, "NUL");
            strcpy(BinResolutionofRadial, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_SS://SS
            Proname = "SS";
            strcpy(Elevation, "NUL");
            strcpy(BinResolutionofRadial, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_DB://DB
            Proname = "DB";
            strcpy(Elevation, "NUL");
            strcpy(BinResolutionofRadial, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_GF://GF
            Proname = "GF";
            strcpy(Elevation, "NUL");
            strcpy(BinResolutionofRadial, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_RS://RS
            Proname = "RS";
            strcpy(Elevation, "NUL");
            strcpy(BinResolutionofRadial, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_QPE:
            Proname = "QPE";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            //sprintf(Elevation,"%d",(int)(RadarProduct->commonBlock.cutconfig.at(0).Elevation*10));
            strcpy(Elevation, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_PolarQPE:
            Proname = "PolarQPE";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            //sprintf(Elevation,"%d",(int)(RadarProduct->commonBlock.cutconfig.at(0).Elevation*10));
            strcpy(Elevation, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_STP: // 27 STP RADIAL
            Proname = "STP";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            strcpy(Elevation, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_PolarSTP:    // 57 PolarSTP RADIAL
            Proname = "PolarSTP";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            strcpy(Elevation, "NUL");
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_HCL: // 51://HCL //MRADIAL
            Proname = "HCL";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            //        strcpy(Elevation,"NUL");
            sprintf(Elevation, "%d", (int)(RadarProduct->productheader.productdependentparameter.hclparameter.Elevation * 10));
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_RVD: // 101 RVD RADIAL
            Proname += "RVD";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            sprintf(Elevation, "%d", (int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 10));
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_ARD: // 102 ARD RADIAL
            Proname += "ARD";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            sprintf(Elevation, "%d", (int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 10));
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_CS: // 103 CS RADIAL
            Proname += "CS";
            if (((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100)
            {
                sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
            }
            else
            {
                sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT *)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
            }
            sprintf(Elevation, "%d", (int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 10));
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
            break;
        case PTYPE_FLOW://62//光流外推
            Proname += "EXP";
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_NUL" + "." + string(SiteCode) +  "." + string(yyyymmddhhmmss_exp) + ".BIN";
            break;
        default:
            Proname = "UnKnown";
            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + to_string(RadarProduct->productheader.productheader.ProductType) + "_" + string(nul) + "_" + string(nul) + "_" + string(nul) + "." + string(SiteCode) + ".BIN";
            break;
    }
    FileDir = string(SiteName) + "/" + string(yyyymmdd) + "/" + string(yyyymmddhh) + "/" + Proname + "/";
    //m_FileName_out->at(i_pro) = new char[128];
    string temp = FileDir + FileName;
    strncpy(m_aFileName, temp.c_str(), 127);

    return m_aFileName;
}

/**
 * @brief CNrietFileIO::GetRadarKJCProFileName
 * @param ProPoint
 * @return
 */
char *CNrietFileIO::GetRadarKJCProFileName(void *ProPoint)
{
    WRADPRODATA_PARA_IN *RadarProduct = (WRADPRODATA_PARA_IN *)ProPoint;

    char nameFromRawfile[64] = {0};
    strncpy(nameFromRawfile, RadarProduct->commonBlockPAR.siteconfig.Reserved, 26);
    string sitename = string(nameFromRawfile).substr(3, 5);
    string yyyymmdd = string(nameFromRawfile).substr(12, 8);
    string yyyymmddhh = string(nameFromRawfile).substr(12, 10);

    char Elevation[8] = {0}; // Unit:0.1 degree
    string FileDir;
    string FileName;
    string Proname;
    switch (RadarProduct->productheader.productheader.ProductType)
    {
        case PTYPE_PPI: // 1://PPI
            switch (RadarProduct->productheader.productheader.DataType1)
            {
                case 1:
                    Proname = "DBT";
                    break;
                case 2:
                    Proname = "DBZ";
                    break;
                case 3:
                    Proname = "V";
                    break;
                case 4:
                    Proname = "SW";
                    break;
                case 5:
                    Proname = "SQI";
                    break;
                case 7:
                    Proname = "ZDR";
                    break;
                case 8:
                    Proname = "LDR";
                    break;
                case 9:
                    Proname = "CC";
                    break;
                case 10:
                    Proname = "PHDP";
                    break;
                case 11:
                    Proname = "KDP";
                    break;
                case 16:
                    Proname = "SNRH";
                    break;
                case 17:
                    Proname = "SNRV";
                    break;
                default:
                    Proname = "UnKnown";
                    break;
            }
            sprintf(Elevation, "%d", (int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 100));
//        Proname = "PPI"+Proname+Elevation;
            Proname = "PPI" + Proname;
            break;
        case PTYPE_RHI: // 2://RHI
            switch (RadarProduct->productheader.productheader.DataType1)
            {
                case 1:
                    Proname = "DBT";
                    break;
                case 2:
                    Proname = "DBZ";
                    break;
                case 3:
                    Proname = "V";
                    break;
                case 4:
                    Proname = "SW";
                    break;
                case 5:
                    Proname = "SQI";
                    break;
                case 7:
                    Proname = "ZDR";
                    break;
                case 8:
                    Proname = "LDR";
                    break;
                case 9:
                    Proname = "CC";
                    break;
                case 10:
                    Proname = "PHDP";
                    break;
                case 11:
                    Proname = "KDP";
                    break;
                case 16:
                    Proname = "SNRH";
                    break;
                case 17:
                    Proname = "SNRV";
                    break;
                default:
                    Proname = "UnKnown";
                    break;
            }
            Proname = "RHI" + Proname;
            break;
        case PTYPE_CAPPI: // 3://CAPPI
            switch (RadarProduct->productheader.productheader.DataType1)
            {
                case 1:
                    Proname = "DBT";
                    break;
                case 2:
                    Proname = "DBZ";
                    break;
                case 3:
                    Proname = "V";
                    break;
                case 4:
                    Proname = "SW";
                    break;
                case 5:
                    Proname = "SQI";
                    break;
                case 7:
                    Proname = "ZDR";
                    break;
                case 8:
                    Proname = "LDR";
                    break;
                case 9:
                    Proname = "CC";
                    break;
                case 10:
                    Proname = "PHDP";
                    break;
                case 11:
                    Proname = "KDP";
                    break;
                case 16:
                    Proname = "SNRH";
                    break;
                case 17:
                    Proname = "SNRV";
                    break;
                default:
                    Proname = "UnKnown";
                    break;
            }
            Proname = "CAPPI" + Proname;
            break;
        case PTYPE_MAX: //MAX //格点
            Proname = "MAX";
            break;
        case PTYPE_ET://ET //格点
            Proname = "ET";
            break;
        case PTYPE_EB://EB //格点
            Proname = "EB";
            break;
        case PTYPE_SRM:     // RADIAL_FORMAT
            sprintf(Elevation, "%d", (int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 100));
            Proname = "SRM";
            break;
        case PTYPE_VIL://VIL //格点
            Proname = "VIL";
            break;
        case PTYPE_CR://CR RADIAL_FORMAT
            Proname = "CR";
            break;
        case PTYPE_CRH_RADIAL://CRH RADIAL_FORMAT
            Proname = "CRH";
            break;
        case PTYPE_ET_RADIAL://ET RADIAL_FORMAT
            Proname = "ET";
            break;
        case PTYPE_EB_RADIAL://EB RADIAL_FORMAT
            Proname = "EB";
            break;
        case PTYPE_VIL_RADIAL://ET RADIAL_FORMAT
            Proname = "VIL";
            break;
        case PTYPE_OHP://OHP
            Proname = "OHP";
            break;
        case PTYPE_PolarOHP://OHP
            Proname = "PolarOHP";
            break;
        case PTYPE_THP://THP
            Proname = "THP";
            break;
        case PTYPE_USP://USP
            Proname = "USP";
            break;
        case PTYPE_VAD://VAD
            Proname = "VAD";
            break;
        case PTYPE_VWP://VWP
            Proname = "VWP";
            break;
        case PTYPE_STI://STI
            Proname = "STI";
            break;
        case PTYPE_HI://HI
            Proname = "HI";
            break;
        case PTYPE_M://MESO
            Proname = "M";
            break;
        case PTYPE_TVS://TVS
            Proname = "TVS";
            break;
        case PTYPE_SS://SS
            Proname = "SS";
            break;
        case PTYPE_DB://DB
            Proname = "DBI";
            break;
        case PTYPE_GF://GF
            Proname = "GFI";
            break;
        case PTYPE_RS://RS
            Proname = "RS";
            break;
        case PTYPE_QPE:
            Proname = "ZR";
            break;
        case PTYPE_STP: // 27 STP RADIAL
            Proname = "STP";
            break;
        case PTYPE_HCL: // 51://HCL //MRADIAL
            Proname = "HCL";
            break;
        case PTYPE_RVD: // 101 RVD RADIAL
            sprintf(Elevation, "%d", (int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 100));
            Proname = "RVD";
            break;
        case PTYPE_ARD: // 102 ARD RADIAL
            sprintf(Elevation, "%d", (int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 100));
            Proname = "ARD";
            break;
        case PTYPE_CS: // 103 CS RADIAL
            sprintf(Elevation, "%d", (int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation * 100));
            Proname = "CS";
            break;
        case PTYPE_FLOW://62//光流外推
            Proname = "EXP";
            break;
        case PTYPE_SAT:
            Proname = "SAT";
            break;
        case PTYPE_ACC:
            Proname = "ACC";
            break;
        case PTYPE_LGT:
            Proname = "LGT";
            break;
        default:
            Proname = "UnKnown";
            break;
    }
    if (RadarProduct->productheader.productheader.ProductType == PTYPE_PPI || RadarProduct->productheader.productheader.ProductType == PTYPE_RVD
            || RadarProduct->productheader.productheader.ProductType == PTYPE_ARD || RadarProduct->productheader.productheader.ProductType == PTYPE_CS \
            || RadarProduct->productheader.productheader.ProductType == PTYPE_SRM)
    {
        FileName = string(nameFromRawfile) + "_" + Proname + string(Elevation);
    }
    else if (RadarProduct->productheader.productheader.ProductType == PTYPE_FLOW)
    {
        time_t pro_time_t_exp = RadarProduct->productheader.productheader.DataEndTime;
        tm pro_tm_exp = *(gmtime(&pro_time_t_exp));
        char yyyymmddhhmmss_exp[16] = {0};
        sprintf(&yyyymmddhhmmss_exp[0], "%4.4d", pro_tm_exp.tm_year + 1900);
        sprintf(&yyyymmddhhmmss_exp[4], "%2.2d", pro_tm_exp.tm_mon + 1);
        sprintf(&yyyymmddhhmmss_exp[6], "%2.2d", pro_tm_exp.tm_mday);
        sprintf(&yyyymmddhhmmss_exp[8], "%2.2d", pro_tm_exp.tm_hour);
        sprintf(&yyyymmddhhmmss_exp[10], "%2.2d", pro_tm_exp.tm_min);
        sprintf(&yyyymmddhhmmss_exp[12], "%2.2d", pro_tm_exp.tm_sec);
        FileName = string(nameFromRawfile) + "_" + Proname + string(yyyymmddhhmmss_exp);
    }
    else
    {
        FileName = string(nameFromRawfile) + "_" + Proname;
    }
    FileDir = sitename + "/" + yyyymmdd + "/" + yyyymmddhh + "/" + Proname + "/";
    //m_FileName_out->at(i_pro) = new char[128];
    string temp = FileDir + FileName;
    strncpy(m_aFileName, temp.c_str(), temp.length());

    return m_aFileName;

}

/**
 * @brief CNrietFileIO::GetRadarLatlonFileName
 * @param temp
 * @return
 */
char *CNrietFileIO::GetRadarLatlonFileName(void *temp)
{
    s_Pro_Grid::RadarProduct *i_pro = (s_Pro_Grid::RadarProduct *)temp;

    //char* fp;
    const char *nul = "NUL";
    char Elevation[8] = {0}; // Unit:0.1 degree

    string FileDir;
    string FileName;
//    char *SiteName;
//    if (i_pro->ProInfo.ProductionID < 200)
//    {
//        SiteName = i_pro->SiteInfo.front().SiteCode;
//    }
//    else
//    {
//        SiteName = (char *)"MOSAIC";
//    }
//    std::string sitecode;
//    sitecode.assign(SiteName);
//    // 替换第一个 '/' 为其他字符，例如 '_'
//    size_t pos = sitecode.find('/', 0);
//    if (pos != std::string::npos)
//    {
//        sitecode.replace(pos, 1, "_"); // 替换第一个 '/'
//    }

    if (m_SITECODE.size() < 5)
    {
        m_SITECODE.insert(0, 5 - m_SITECODE.size(), '0');
    }

    string Proname;
    string R1, R2;
    switch (i_pro->ProInfo.ProductionID)
    {
        //    101 = dBTCAPPI  // 不经过地物杂波消除的dBT值= UnZ/100
        //    102 = dBZCAPPI    // 经过地物杂波消除的dBZ值= CorZ/100
        //    103 = VCAPPI    // 速度值= V/100
        //                    // 正值表示远离雷达的速度，负值表示朝向雷达的速度
        //    104 = WCAPPI    // 谱宽值= W/100
        //    107 = ZDR       // 反射率差值= ZDR/100，单位db
        //    110 = PHDP;     // 差分传播相移= PHDP-(-18000)/100，单位度
        //    111 = KDP;      // 差分传播相移常数= KDP/100，单位度/公里
        //    109 = ROHV;     // 相关系数值= ROHV/100
        //    108 = LDR;      // 退偏振比= LDR/100
        case 101:
            Proname = "UnRCAPPI";
            break;
        case 102:
            Proname = "RCAPPI";
            break;
        case 103:
            Proname = "VCAPPI";
            break;
        case 104:
            Proname = "WCAPPI";
            break;
        case 107:
            Proname = "ZDRCAPPI";
            break;
        case 110:
            Proname = "PHDPCAPPI";
            break;
        case 111:
            Proname = "KDPCAPPI";
            break;
        case 109:
            Proname = "CCCAPPI";
            break;
        case 108:
            Proname = "LDRCAPPI";
            break;
        case 202:
            Proname = "R";
            break;
        case 207:
            Proname = "ZDR";
            break;
        case 209:
            Proname = "CC";
            break;
        case 211:
            Proname = "KDP";
            break;
        case PTYPE_MAX+300:
            Proname = "CR";
            break;
        case PTYPE_ET+300:
            Proname = "ET";
            break;
        case PTYPE_EB+300:
            Proname = "EB";
            break;
        case PTYPE_VIL+300:
            Proname = "VIL";
            break;
        case PTYPE_QPE+300:
            Proname = "QPE";
            break;
        case PTYPE_OHP+300:
            Proname = "OHP";
            break;
        case PTYPE_PolarQPE+300:
            Proname = "PolarQPE";
            break;
        case PTYPE_PolarOHP+300:
            Proname = "PolarOHP";
            break;
        case 220:
            Proname = "DDA";
            R1 = i_pro->SiteInfo.front().SiteCode;
            R2 = i_pro->SiteInfo.back().SiteCode;
            Proname = Proname + "_" + R1 + "_" + R2;
            break;
        case 221:
            Proname = "VOR";
            R1 = i_pro->SiteInfo.front().SiteCode;
            R2 = i_pro->SiteInfo.back().SiteCode;
            Proname = Proname + "_" + R1 + "_" + R2;
            break;
        case 222:
            Proname = "DIV";
            R1 = i_pro->SiteInfo.front().SiteCode;
            R2 = i_pro->SiteInfo.back().SiteCode;
            Proname = Proname + "_" + R1 + "_" + R2;
            break;
        case 229:
            Proname = "WindMosaic";
            break;
        case 230:
            Proname = "VORMosaic";
            break;
        case 231:
            Proname = "DIVMosaic";
            break;
        case 241:
            Proname = "TECR";
            break;
        case 242:
            Proname = "RECR";
            break;
        case 243:
            Proname = "VECR";
            break;
        case 244:
            Proname = "WECR";
            break;
        case 247:
            Proname = "ZDRECR";
            break;
        case 248:
            Proname = "LDRECR";
            break;
        case 249:
            Proname = "ROHVECR";
            break;
        case 250:
            Proname = "PHDPECR";
            break;
        case 251:
            Proname = "KDPECR";
            break;
//        case 61:
////        Proname = "FLOWUV";
//            Proname = "EV";
//            break;
        case PTYPE_UV:
            Proname = "EV";
            break;
        case PTYPE_2DUV:
            Proname = "2DEV";
            break;
        case PTYPE_FLOW:
            Proname = "EXP";
            break;
        case PTYPE_QPF:
            Proname = "QPF";
            break;
        default:
            Proname = "UnKnown";
            break;
    }
    //if (i_pro->ProInfo.ProductionID > 100 && i_pro->ProInfo.ProductionID < 120)
    //    if (i_pro->ParametersInfo.cappiparameter.QCMask == 1) Proname = "QC" + Proname;
    time_t pro_time_t = i_pro->ProInfo.ProductionTime;
//    time_t pro_time_t = i_pro->ProInfo.DataEndTime;

    tm pro_tm = *(gmtime(&pro_time_t));
    char yyyymmddhhmmss[16] = {0};

    sprintf(&yyyymmddhhmmss[0], "%4.4d", pro_tm.tm_year + 1900);
    sprintf(&yyyymmddhhmmss[4], "%2.2d", pro_tm.tm_mon + 1);
    sprintf(&yyyymmddhhmmss[6], "%2.2d", pro_tm.tm_mday);
    sprintf(&yyyymmddhhmmss[8], "%2.2d", pro_tm.tm_hour);
    sprintf(&yyyymmddhhmmss[10], "%2.2d", pro_tm.tm_min);
    sprintf(&yyyymmddhhmmss[12], "%2.2d", pro_tm.tm_sec);
    char yyyymmdd[16] = {0};
    strncpy(yyyymmdd, yyyymmddhhmmss, 8);
    char yyyymmddhh[16] = {0};
    strncpy(yyyymmddhh, yyyymmddhhmmss, 10);


//    time_t pro_time_t_exp = i_pro->ProInfo.DataEndTime;
//    tm pro_tm_exp = *(gmtime(&pro_time_t_exp));
//    char yyyymmddhhmmss_exp[16] = {0};
//    sprintf(&yyyymmddhhmmss_exp[0], "%4.4d", pro_tm_exp.tm_year + 1900);
//    sprintf(&yyyymmddhhmmss_exp[4], "%2.2d", pro_tm_exp.tm_mon + 1);
//    sprintf(&yyyymmddhhmmss_exp[6], "%2.2d", pro_tm_exp.tm_mday);
//    sprintf(&yyyymmddhhmmss_exp[8], "%2.2d", pro_tm_exp.tm_hour);
//    sprintf(&yyyymmddhhmmss_exp[10], "%2.2d", pro_tm_exp.tm_min);
//    sprintf(&yyyymmddhhmmss_exp[12], "%2.2d", pro_tm_exp.tm_sec);
//    char yyyymmdd_exp[16] = {0};
//    strncpy(yyyymmdd_exp, yyyymmddhhmmss_exp, 8);
//    char yyyymmddhh_exp[16] = {0};
//    strncpy(yyyymmddhh_exp, yyyymmddhhmmss_exp, 10);

    string frontdir = "RADA/RADA_PUP/";


    // radartype
    short radartype = i_pro->SiteInfo.at(0).RadarType;
    string RadarType;
    switch (radartype)
    {
        case 1:
            RadarType = "SC00";
            break;
        case 2:
            RadarType = "SB00";
            break;
        case 3:
            RadarType = "SC00";
            break;
        case 4:
            RadarType = "SAD0";
            break;
        case 5:
            RadarType = "SBD0";
            break;
        case 6:
            RadarType = "SCD0";
            break;
        case 33:
            RadarType = "CA00";
            break;
        case 34:
            RadarType = "CB00";
            break;
        case 35:
            RadarType = "CC00";
            break;
        case 36:
            RadarType = "CCJ0";
            break;
        case 37:
            RadarType = "CD00";
            break;
        case 38:
            RadarType = "CAD0";
            break;
        case 39:
            RadarType = "CBD0";
            break;
        case 40:
            RadarType = "CCD0";
            break;
        case 41:
            RadarType = "CCJD";
            break;
        case 42:
            RadarType = "CDD0";
            break;
        case 65:
            RadarType = "XA00";
            break;
        case 66:
            RadarType = "XAD0";
            break;
        case 720:
            RadarType = "720A";
            break;
        case 721:
            RadarType = "7210";
            break;
        case 717:
            RadarType = "7170";
            break;
        case 784: // NewDual_784
            RadarType = "06SD";
            break;
        default:
            RadarType = "UnKnown";
            break;
    }

    string Syyyymmdd_exp;
    string Syyyymmddhh_exp;
    string Syyyymmddhhmmss_exp;

    if (RadarType == "720A" || RadarType == "7210" || RadarType == "7170" || RadarType == "06SD")
    {
        Syyyymmdd_exp = m_fileTime.substr(0, 8);
        Syyyymmddhh_exp = m_fileTime.substr(0, 10);
        Syyyymmddhhmmss_exp = m_fileTime.substr(0, 14);
    }
    else
    {
        time_t pro_time_t_exp = i_pro->ProInfo.DataEndTime;
        tm pro_tm_exp = *(gmtime(&pro_time_t_exp));
        char yyyymmddhhmmss_exp[16] = {0};
        sprintf(&yyyymmddhhmmss_exp[0], "%4.4d", pro_tm_exp.tm_year + 1900);
        sprintf(&yyyymmddhhmmss_exp[4], "%2.2d", pro_tm_exp.tm_mon + 1);
        sprintf(&yyyymmddhhmmss_exp[6], "%2.2d", pro_tm_exp.tm_mday);
        sprintf(&yyyymmddhhmmss_exp[8], "%2.2d", pro_tm_exp.tm_hour);
        sprintf(&yyyymmddhhmmss_exp[10], "%2.2d", pro_tm_exp.tm_min);
        sprintf(&yyyymmddhhmmss_exp[12], "%2.2d", pro_tm_exp.tm_sec);
        char yyyymmdd_exp[16] = {0};
        strncpy(yyyymmdd_exp, yyyymmddhhmmss_exp, 8);
        char yyyymmddhh_exp[16] = {0};
        strncpy(yyyymmddhh_exp, yyyymmddhhmmss_exp, 10);

        Syyyymmdd_exp = string(yyyymmdd_exp);
        Syyyymmddhh_exp = string(yyyymmddhh_exp);
        Syyyymmddhhmmss_exp = string(yyyymmddhhmmss_exp);
    }

    strcpy(Elevation, "NUL");
    FileName = "KLG" + m_SITECODE + RadarType + Syyyymmddhhmmss_exp + "_" + Proname;

//    FileName = "PRODUCT_RADR_" + Proname + "_" + string(yyyymmddhhmmss) + ".latlon";

//    if (i_pro->ProInfo.ProductionID == 61)
//    {
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_NUL" + "_NUL" + "." + string(SiteName) + ".BIN";
//    }

//    if (i_pro->ProInfo.ProductionID == PTYPE_MAX+300){
//        short weight = 0;
//        int scale = i_pro->DataBlock.at(0).ProDataInfo.DScale;
//        int offset = i_pro->DataBlock.at(0).ProDataInfo.DOffset;
//        int count = 0;
//        for (int i = 0; i < i_pro->DataBlock.at(0).ProductData.size()/2; i+=2){
//            if ( (*(short*)&i_pro->DataBlock.at(0).ProductData.at(i*2) -offset )/ scale > 15) count ++;
//        }
//        weight = 1000.0 * count / (i_pro->DataBlock.at(0).ProductData.size()/2);
//        FileName = FileName + "." +to_string(weight);
//    }
//    FileDir = string(SiteName) + "/" + string(yyyymmdd) + "/" + string(yyyymmddhh) + "/" + Proname + "/";

    std::string sitecode;
    auto it = std::find_if(m_SITECODE.begin(), m_SITECODE.end(), [](char c)
    {
        return c != '0';
    });
    // 如果找到了，取出该位置及其后面的字符
    if (it != m_SITECODE.end())
    {
        sitecode = std::string(it, m_SITECODE.end());
    }
    else
    {
        sitecode = m_SITECODE;
    }

//    FileDir = string(SiteName) + "/" + string(yyyymmdd) + "/" + string(yyyymmddhh) + "/" + Proname + "/";
    FileDir = frontdir + sitecode + "/" + Syyyymmdd_exp + "/" + Syyyymmddhh_exp + "/" + Proname + "/";
    //m_FileName_out->at(i_pro) = new char[128];
    string temp_FileName = FileDir + FileName;
    strncpy(m_aFileName, temp_FileName.c_str(), temp_FileName.length());
//    std::cout << "file path:" << temp << endl;

    return m_aFileName;
    //return nullptr;
}

char *CNrietFileIO::GetRadarKJCLatlonFileName(void *temp)
{
    s_Pro_Grid::RadarProduct *i_pro = (s_Pro_Grid::RadarProduct *)temp;

    string FileDir;
    string FileName;
    char *SiteName;
    if (i_pro->ProInfo.ProductionID < 200)
    {
        SiteName = i_pro->SiteInfo.front().SiteCode;
    }
    else
    {
        SiteName = (char *)"MOSAIC";
    }

    string Proname;
    string R1, R2;
    switch (i_pro->ProInfo.ProductionID)
    {
        case 101:
            Proname = "UnRCAPPI";
            break;
        case 102:
            Proname = "RCAPPI";
            break;
        case 103:
            Proname = "VCAPPI";
            break;
        case 104:
            Proname = "WCAPPI";
            break;
        case 107:
            Proname = "ZDRCAPPI";
            break;
        case 110:
            Proname = "PHDPCAPPI";
            break;
        case 111:
            Proname = "KDPCAPPI";
            break;
        case 109:
            Proname = "CCCAPPI";
            break;
        case 108:
            Proname = "LDRCAPPI";
            break;
        case 202:
            Proname = "R";
            break;
        case 207:
            Proname = "ZDR";
            break;
        case 209:
            Proname = "CC";
            break;
        case 211:
            Proname = "KDP";
            break;
        case PTYPE_MAX+300:
            Proname = "CR";
            break;
        case PTYPE_ET+300:
            Proname = "ET";
            break;
        case PTYPE_EB+300:
            Proname = "EB";
            break;
        case PTYPE_VIL+300:
            Proname = "VIL";
            break;
        case PTYPE_QPE+300:
            Proname = "QPE";
            break;
        case PTYPE_OHP+300:
            Proname = "OHP";
            break;
        case PTYPE_PolarQPE+300:
            Proname = "PolarQPE";
            break;
        case PTYPE_PolarOHP+300:
            Proname = "PolarOHP";
            break;
        case 220:
            Proname = "DDA";
            R1 = i_pro->SiteInfo.front().SiteCode;
            R2 = i_pro->SiteInfo.back().SiteCode;
            Proname = Proname + "_" + R1 + "_" + R2;
            break;
        case 221:
            Proname = "VOR";
            R1 = i_pro->SiteInfo.front().SiteCode;
            R2 = i_pro->SiteInfo.back().SiteCode;
            Proname = Proname + "_" + R1 + "_" + R2;
            break;
        case 222:
            Proname = "DIV";
            R1 = i_pro->SiteInfo.front().SiteCode;
            R2 = i_pro->SiteInfo.back().SiteCode;
            Proname = Proname + "_" + R1 + "_" + R2;
            break;
        case 229:
            Proname = "WindMosaic";
            break;
        case 230:
            Proname = "VORMosaic";
            break;
        case 231:
            Proname = "DIVMosaic";
            break;
        case 241:
            Proname = "TECR";
            break;
        case 242:
            Proname = "RECR";
            break;
        case 243:
            Proname = "VECR";
            break;
        case 244:
            Proname = "WECR";
            break;
        case 247:
            Proname = "ZDRECR";
            break;
        case 248:
            Proname = "LDRECR";
            break;
        case 249:
            Proname = "ROHVECR";
            break;
        case 250:
            Proname = "PHDPECR";
            break;
        case 251:
            Proname = "KDPECR";
            break;
        case 61:
            Proname = "EV";
            break;
        default:
            Proname = "UnKnown";
            break;
    }
    time_t pro_time_t = i_pro->ProInfo.DataEndTime;

    tm pro_tm = *(gmtime(&pro_time_t));
    char yyyymmddhhmmss[16] = {0};

    sprintf(&yyyymmddhhmmss[0], "%4.4d", pro_tm.tm_year + 1900);
    sprintf(&yyyymmddhhmmss[4], "%2.2d", pro_tm.tm_mon + 1);
    sprintf(&yyyymmddhhmmss[6], "%2.2d", pro_tm.tm_mday);
    sprintf(&yyyymmddhhmmss[8], "%2.2d", pro_tm.tm_hour);
    sprintf(&yyyymmddhhmmss[10], "%2.2d", pro_tm.tm_min);
    sprintf(&yyyymmddhhmmss[12], "%2.2d", pro_tm.tm_sec);
    char yyyymmdd[16] = {0};
    strncpy(yyyymmdd, yyyymmddhhmmss, 8);
    char yyyymmddhh[16] = {0};
    strncpy(yyyymmddhh, yyyymmddhhmmss, 10);

    FileName = "PRODUCT_RADR_" + Proname + "_" + string(yyyymmddhhmmss) + ".latlon";

    if (i_pro->ProInfo.ProductionID == 61)
    {
        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_NUL" + "_NUL" + "." + string(SiteName) + ".BIN";
    }

    FileDir = string(SiteName) + "/" + string(yyyymmdd) + "/" + string(yyyymmddhh) + "/" + Proname + "/";
    string temp_FileName = FileDir + FileName;
    strncpy(m_aFileName, temp_FileName.c_str(), temp_FileName.length());

    return m_aFileName;
}

char *CNrietFileIO::GetKJCFileName(void *temp)
{
    s_Pro_Grid::RadarProduct *i_pro = (s_Pro_Grid::RadarProduct *)temp;
//    WRADPRODATA_PARA_IN* i_pro = (WRADPRODATA_PARA_IN*)temp;


//    char* SiteCode = i_pro->SiteInfo.begin()->SiteCode;

//    time_t pro_time_t = i_pro->ProInfo.ProductionTime;//time!!!!!!
//    char* SiteCode =i_pro->commonBlock.siteconfig.SiteCode;
//    time_t pro_time_t=i_pro->productheader.productheader.DataEndTime;

//    tm pro_tm = *(gmtime(&pro_time_t));
//    char yyyymmddhhmmss[16] = {0};

//    sprintf(&yyyymmddhhmmss[0],"%4.4d",pro_tm.tm_year +1900);
//    sprintf(&yyyymmddhhmmss[4],"%2.2d",pro_tm.tm_mon + 1);
//    sprintf(&yyyymmddhhmmss[6],"%2.2d",pro_tm.tm_mday);
//    sprintf(&yyyymmddhhmmss[8],"%2.2d",pro_tm.tm_hour);
//    sprintf(&yyyymmddhhmmss[10],"%2.2d",pro_tm.tm_min);
//    sprintf(&yyyymmddhhmmss[12],"%2.2d",pro_tm.tm_sec);

//    string Proname;
//    char Elevation[8] = {0}; // Unit:0.1 degree
//    switch (i_pro->productheader.productheader.ProductType)
//    {
//    case PTYPE_PPI: // 1://PPI
//        switch (i_pro->productheader.productheader.DataType1) {
//        case 1:
//            Proname = "UnR";
//            break;
//        case 2:
//            Proname = "R";
//            break;
//        case 3:
//            Proname = "V";
//            break;
//        case 4:
//            Proname = "W";
//            break;
//        case 5:
//            Proname = "SQI";
//            break;
//        case 7:
//            Proname = "ZDR";
//            break;
//        case 8:
//            Proname = "LDR";
//            break;
//        case 9:
//            Proname = "CC";
//            break;
//        case 10:
//            Proname = "PHDP";
//            break;
//        case 11:
//            Proname = "KDP";
//            break;
//        case 16:
//            Proname = "SNRH";
//            break;
//        case 17:
//            Proname = "SNRV";
//            break;
//        default:
//            Proname = "UnKnown";
//            break;
//        }
//        Proname += "PPI";
//        if (RadarProduct->commonBlock.cutconfig.front().dBTMask == 1) Proname = "QC" + Proname;
//        //if (((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100){
//        //    sprintf(BinResolutionofRadial,"%d",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100);
//        //}
//        //else{
//            sprintf(BinResolutionofRadial,"%.1f",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100.0);
//        //}
//        sprintf(Elevation,"%d",(int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation*10));
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_RHI: // 2://RHI
//        switch (RadarProduct->productheader.productheader.DataType1) {
//        case 1:
//            Proname = "UnR";
//            break;
//        case 2:
//            Proname = "R";
//            break;
//        case 3:
//            Proname = "V";
//            break;
//        case 4:
//            Proname = "W";
//            break;
//        case 7:
//            Proname = "ZDR";
//            break;
//        case 8:
//            Proname = "LDR";
//            break;
//        case 9:
//            Proname = "CC";
//            break;
//        case 10:
//            Proname = "PHDP";
//            break;
//        case 11:
//            Proname = "KDP";
//            break;
//        case 16:
//            Proname = "SNRH";
//            break;
//        case 17:
//            Proname = "SNRV";
//            break;
//        default:
//            Proname = "UnKnown";
//            break;
//        }
//        Proname += "RHI";
//        if (RadarProduct->commonBlock.cutconfig.front().dBTMask == 1) Proname = "QC" + Proname;
//        sprintf(Elevation,"%d",(int)round(RadarProduct->productheader.productdependentparameter.rhiparameter.Azimuth * 10));
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_SRM: //SRM PPI
//        Proname = "SRM";
//        if (((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100){
//            sprintf(BinResolutionofRadial,"%d",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100);
//        }
//        else{
//            sprintf(BinResolutionofRadial,"%.1f",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100.0);
//        }
//        sprintf(Elevation,"%d",(int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation*10));
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_CAPPI: // 3://CAPPI //格点
//        if(RadarProduct->productheader.productheader.DataType1 == 1)
//            Proname = "UnRCAR";
//        if(RadarProduct->productheader.productheader.DataType1 == 2)
//            Proname = "RCAR";
//        if(RadarProduct->productheader.productheader.DataType1 == 3)
//            Proname = "VCAR";
//        if(RadarProduct->productheader.productheader.DataType1 == 4)
//            Proname = "WCAR";
//        if(RadarProduct->productheader.productheader.DataType1 == 7)
//            Proname = "ZDRCAR";
//        if(RadarProduct->productheader.productheader.DataType1 == 8)
//            Proname = "LDRCAR";
//        if(RadarProduct->productheader.productheader.DataType1 == 9)
//            Proname = "CCCAR";
//        if(RadarProduct->productheader.productheader.DataType1 == 10)
//            Proname = "PHDPCAR";
//        if(RadarProduct->productheader.productheader.DataType1 == 11)
//            Proname = "KDPCAR";
//        if(RadarProduct->productheader.productheader.DataType1 == 16)
//            Proname = "SNRHCAR";
//        if (((CAPPIFORMAT*)RadarProduct->productdatapoint)->CappiData.at(0).RadialHeader.Resolution >= 100){
//            sprintf(BinResolutionofRadial,"%d",((CAPPIFORMAT*)RadarProduct->productdatapoint)->CappiData.at(0).RadialHeader.Resolution/100);
//        }
//        else{
//            sprintf(BinResolutionofRadial,"%.1f",((CAPPIFORMAT*)RadarProduct->productdatapoint)->CappiData.at(0).RadialHeader.Resolution/100.0);
//        }
//        strcpy(Elevation,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_MAX: //MAX //格点
//        strcpy(Elevation,"NUL");
//        Proname = "MAX";
//        if (((MAXFORMAT*)RadarProduct->productdatapoint)->MAXData->RasterHeader.RowResolution >=100){
//            sprintf(RowResolutionofGrid,"%d",((MAXFORMAT*)RadarProduct->productdatapoint)->MAXData->RasterHeader.RowResolution/100);
//        }
//        else{
//            sprintf(RowResolutionofGrid,"%.1f",((MAXFORMAT*)RadarProduct->productdatapoint)->MAXData->RasterHeader.RowResolution/100.0);
//        }
//        if (((MAXFORMAT*)RadarProduct->productdatapoint)->MAXData->RasterHeader.ColumnResolution >= 100){
//            sprintf(ColumnResolutionofGrid,"%d",((MAXFORMAT*)RadarProduct->productdatapoint)->MAXData->RasterHeader.ColumnResolution/100);
//        }
//        else{
//            sprintf(ColumnResolutionofGrid,"%.1f",((MAXFORMAT*)RadarProduct->productdatapoint)->MAXData->RasterHeader.ColumnResolution/100.0);
//        }
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(RowResolutionofGrid) + "x" + string(ColumnResolutionofGrid) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_ET://ET //格点
//        strcpy(Elevation,"NUL");
//        Proname = "ET";
//        if (((RASTERFORMAT*)RadarProduct->productdatapoint)->RasterHeader.RowResolution >= 100){
//            sprintf(RowResolutionofGrid,"%d",((RASTERFORMAT*)RadarProduct->productdatapoint)->RasterHeader.RowResolution/100);
//        }
//        else {
//            sprintf(RowResolutionofGrid,"%.1f",((RASTERFORMAT*)RadarProduct->productdatapoint)->RasterHeader.RowResolution/100.0);
//        }
//        if (((RASTERFORMAT*)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution >= 100){
//            sprintf(ColumnResolutionofGrid,"%d",((RASTERFORMAT*)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution/100);
//        }
//        else{
//            sprintf(ColumnResolutionofGrid,"%.1f",((RASTERFORMAT*)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution/100.0);
//        }
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(RowResolutionofGrid) + "x" + string(ColumnResolutionofGrid) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_EB://EB //格点
//        strcpy(Elevation,"NUL");
//        Proname = "EB";
//        if (((RASTERFORMAT*)RadarProduct->productdatapoint)->RasterHeader.RowResolution >= 100){
//            sprintf(RowResolutionofGrid,"%d",((RASTERFORMAT*)RadarProduct->productdatapoint)->RasterHeader.RowResolution/100);
//        }
//        else {
//            sprintf(RowResolutionofGrid,"%.1f",((RASTERFORMAT*)RadarProduct->productdatapoint)->RasterHeader.RowResolution/100.0);
//        }
//        if (((RASTERFORMAT*)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution >= 100){
//            sprintf(ColumnResolutionofGrid,"%d",((RASTERFORMAT*)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution/100);
//        }
//        else{
//            sprintf(ColumnResolutionofGrid,"%.1f",((RASTERFORMAT*)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution/100.0);
//        }
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(RowResolutionofGrid) + "x" + string(ColumnResolutionofGrid) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_VIL://VIL //格点
//        strcpy(Elevation,"NUL");
//        Proname = "VIL";
//        if (((RASTERFORMAT*)RadarProduct->productdatapoint)->RasterHeader.RowResolution >= 100){
//            sprintf(RowResolutionofGrid,"%d",((RASTERFORMAT*)RadarProduct->productdatapoint)->RasterHeader.RowResolution/100);
//        }
//        else {
//            sprintf(RowResolutionofGrid,"%.1f",((RASTERFORMAT*)RadarProduct->productdatapoint)->RasterHeader.RowResolution/100.0);
//        }
//        if (((RASTERFORMAT*)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution >= 100){
//            sprintf(ColumnResolutionofGrid,"%d",((RASTERFORMAT*)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution/100);
//        }
//        else{
//            sprintf(ColumnResolutionofGrid,"%.1f",((RASTERFORMAT*)RadarProduct->productdatapoint)->RasterHeader.ColumnResolution/100.0);
//        }
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(RowResolutionofGrid) + "x" + string(ColumnResolutionofGrid) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_CR://CR RADIAL_FORMAT
//        Proname = "CR";
//        if (((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100){
//            sprintf(BinResolutionofRadial,"%d",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100);
//        }
//        else{
//            sprintf(BinResolutionofRadial,"%.1f",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100.0);
//        }
//        strcpy(Elevation,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_CRH_RADIAL://CRH RADIAL_FORMAT
//        Proname = "CRH";
//        if (((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100){
//            sprintf(BinResolutionofRadial,"%d",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100);
//        }
//        else{
//            sprintf(BinResolutionofRadial,"%.1f",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100.0);
//        }
//        strcpy(Elevation,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_ET_RADIAL://ET RADIAL_FORMAT
//        Proname = "ET";
//        if (((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100){
//            sprintf(BinResolutionofRadial,"%d",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100);
//        }
//        else{
//            sprintf(BinResolutionofRadial,"%.1f",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100.0);
//        }
//        strcpy(Elevation,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_EB_RADIAL://EB RADIAL_FORMAT
//        Proname = "EB";
//        if (((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100){
//            sprintf(BinResolutionofRadial,"%d",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100);
//        }
//        else{
//            sprintf(BinResolutionofRadial,"%.1f",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100.0);
//        }
//        strcpy(Elevation,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_VIL_RADIAL://ET RADIAL_FORMAT
//        Proname = "VIL";
//        if (((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100){
//            sprintf(BinResolutionofRadial,"%d",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100);
//        }
//        else{
//            sprintf(BinResolutionofRadial,"%.1f",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100.0);
//        }
//        strcpy(Elevation,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_OHP://OHP
//        Proname = "OHP";
//        if (((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100){
//            sprintf(BinResolutionofRadial,"%d",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100);
//        }
//        else{
//            sprintf(BinResolutionofRadial,"%.1f",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100.0);
//        }
//        //sprintf(Elevation,"%d",(int)(RadarProduct->commonBlock.cutconfig.at(0).Elevation*10));
//        strcpy(Elevation,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_PolarOHP://OHP
//        Proname = "PolarOHP";
//        if (((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100){
//            sprintf(BinResolutionofRadial,"%d",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100);
//        }
//        else{
//            sprintf(BinResolutionofRadial,"%.1f",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100.0);
//        }
//        //sprintf(Elevation,"%d",(int)(RadarProduct->commonBlock.cutconfig.at(0).Elevation*10));
//        strcpy(Elevation,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_THP://THP
//        strcpy(Elevation,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_USP://USP
//        strcpy(Elevation,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_VAD://VAD
//        Proname = "VAD";
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + "NUL" + "_" + "NUL" + "_" + "NUL" + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_VWP://VWP
//        Proname = "VWP";
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + "NUL" + "_" + "NUL" + "_" + "NUL" + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_STI://STI
//        Proname = "STI";
//        strcpy(Elevation,"NUL");
//        strcpy(BinResolutionofRadial,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_HI://HI
//        Proname = "HI";
//        strcpy(Elevation,"NUL");
//        strcpy(BinResolutionofRadial,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_M://MESO
//        Proname = "M";
//        strcpy(Elevation,"NUL");
//        strcpy(BinResolutionofRadial,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_TVS://TVS
//        Proname = "TVS";
//        strcpy(Elevation,"NUL");
//        strcpy(BinResolutionofRadial,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_SS://SS
//        Proname = "SS";
//        strcpy(Elevation,"NUL");
//        strcpy(BinResolutionofRadial,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_DB://DB
//        Proname = "DB";
//        strcpy(Elevation,"NUL");
//        strcpy(BinResolutionofRadial,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_GF://GF
//        Proname = "GF";
//        strcpy(Elevation,"NUL");
//        strcpy(BinResolutionofRadial,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_RS://RS
//        Proname = "RS";
//        strcpy(Elevation,"NUL");
//        strcpy(BinResolutionofRadial,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_QPE:
//        Proname = "QPE";
//        if (((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100){
//            sprintf(BinResolutionofRadial,"%d",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100);
//        }
//        else{
//            sprintf(BinResolutionofRadial,"%.1f",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100.0);
//        }
//        //sprintf(Elevation,"%d",(int)(RadarProduct->commonBlock.cutconfig.at(0).Elevation*10));
//        strcpy(Elevation,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_PolarQPE:
//        Proname = "PolarQPE";
//        if (((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100){
//            sprintf(BinResolutionofRadial,"%d",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100);
//        }
//        else{
//            sprintf(BinResolutionofRadial,"%.1f",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100.0);
//        }
//        //sprintf(Elevation,"%d",(int)(RadarProduct->commonBlock.cutconfig.at(0).Elevation*10));
//        strcpy(Elevation,"NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_STP: // 27 STP RADIAL
//        Proname = "STP";
//        if (((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100){
//            sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
//        }
//        else{
//            sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
//        }
//        strcpy(Elevation, "NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_PolarSTP:    // 57 PolarSTP RADIAL
//        Proname = "PolarSTP";
//        if (((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100){
//            sprintf(BinResolutionofRadial, "%d", ((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100);
//        }
//        else{
//            sprintf(BinResolutionofRadial, "%.1f", ((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution / 100.0);
//        }
//        strcpy(Elevation, "NUL");
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_HCL: // 51://HCL //MRADIAL
//        Proname = "HCL";
//        if (((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100){
//            sprintf(BinResolutionofRadial,"%d",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100);
//        }
//        else{
//            sprintf(BinResolutionofRadial,"%.1f",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100.0);
//        }
//        //        strcpy(Elevation,"NUL");
//        sprintf(Elevation,"%d",(int)(RadarProduct->productheader.productdependentparameter.hclparameter.Elevation*10));
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_RVD: // 101 RVD RADIAL
//        Proname += "RVD";
//        if (((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100){
//            sprintf(BinResolutionofRadial,"%d",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100);
//        }
//        else{
//            sprintf(BinResolutionofRadial,"%.1f",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100.0);
//        }
//        sprintf(Elevation,"%d",(int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation*10));
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_ARD: // 102 ARD RADIAL
//        Proname += "ARD";
//        if (((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100){
//            sprintf(BinResolutionofRadial,"%d",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100);
//        }
//        else{
//            sprintf(BinResolutionofRadial,"%.1f",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100.0);
//        }
//        sprintf(Elevation,"%d",(int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation*10));
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_CS: // 103 CS RADIAL
//        Proname += "CS";
//        if (((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution >= 100){
//            sprintf(BinResolutionofRadial,"%d",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100);
//        }
//        else{
//            sprintf(BinResolutionofRadial,"%.1f",((RADIALFORMAT*)RadarProduct->productdatapoint)->RadialHeader.Resolution/100.0);
//        }
//        sprintf(Elevation,"%d",(int)(RadarProduct->productheader.productdependentparameter.ppiparameter.Elevation*10));
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
//        break;
//    case PTYPE_FLOW://62//光流外推
//        Proname += "EXP";
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname +"_" + string(BinResolutionofRadial) + "_" + string(MaxDistance)+"_NUL" + "." + string(SiteCode) +  "."+string(yyyymmddhhmmss_exp)+".BIN";
//        break;
//    default:
//        Proname = "UnKnown";
//        FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + to_string(RadarProduct->productheader.productheader.ProductType) + "_" + string(nul) + "_" + string(nul) + "_" + string(nul) + "." + string(SiteCode) + ".BIN";
//        break;
//    }
//    FileDir = string(SiteName) + "/" + string(yyyymmdd) + "/" + string(yyyymmddhh) + "/" + Proname + "/";
//    //m_FileName_out->at(i_pro) = new char[128];
//    string temp = FileDir + FileName;
//    strncpy(m_aFileName,temp.c_str(),127);




    return "";
}

void CNrietFileIO::get_files(const string strDir, const string strFeature, vector<string> &filelist)
{
    // TODO: get files list from a dir
    if (strDir.empty())
    {
        return;
    }
    struct stat s;
    stat(strDir.c_str(), &s);
    if (!S_ISDIR(s.st_mode))
    {
        return;
    }
    DIR *dirhand = opendir(strDir.c_str());
    if (!dirhand)
    {
        exit(EXIT_FAILURE);
    }
    dirent *fp = nullptr;
    while ((fp = readdir(dirhand)) != nullptr)
    {
        if (fp->d_name[0] != '.')
        {
            string filename = strDir + "/" + string(fp->d_name);
            struct stat filemod;
            stat(filename.c_str(), &filemod);
            if (S_ISREG(filemod.st_mode) && strstr(filename.c_str(), strFeature.c_str()))
            {
                filelist.push_back(filename);
            }
        }
    }
}

void CNrietFileIO::GetFileNameList(void *ProPoint, void *str_out)
{
    vector<string> *m_FileName_out = (vector<string> *)str_out;
    if (m_FileName_out->size() > 0)
    {
        m_FileName_out->clear();
    }
    vector<WRADPRODATA_PARA_IN> *RadarProduct = (vector<WRADPRODATA_PARA_IN> *)ProPoint;

    //    m_FileName_out->reserve(RadarProduct->size());
    m_FileName_out->resize(RadarProduct->size());

    for (int i_pro = 0; i_pro < RadarProduct->size(); i_pro++)
    {
        //char* fp;
        const char *nul = "NUL";
        char Elevation[8] = {0}; // Unit:0.1 degree
        char MaxDistance[8] = {0}; // Unit:km
        char BinResolutionofRadial[8] = {0}; //Unit:100m
        char RowResolutionofGrid[8] = {0};   //Unit:100m
        char ColumnResolutionofGrid[8] = {0}; //Unit:100m
        string FileDir;
        string FileName;
        //WRADPRODATA_PARA_IN* RadarProduct = (WRADPRODATA_PARA_IN*)ProPoint;
        char *SiteName = RadarProduct->at(i_pro).commonBlock.siteconfig.SiteCode;
        char *SiteCode = RadarProduct->at(i_pro).commonBlock.siteconfig.SiteCode;
        string Proname;
        sprintf(MaxDistance, "%d", \
                RadarProduct->at(i_pro).commonBlock.cutconfig.at(0).MaximumRange1 / 1000);
        if (RadarProduct->at(i_pro).commonBlock.cutconfig.at(0).LogResolution >= 100)
        {
            sprintf(BinResolutionofRadial, "%d", RadarProduct->at(i_pro).commonBlock.cutconfig.at(0).LogResolution / 100);
        }
        else
        {
            sprintf(BinResolutionofRadial, "%.1f", RadarProduct->at(i_pro).commonBlock.cutconfig.at(0).LogResolution / 100.0);
        }
        time_t pro_time_t = RadarProduct->at(i_pro).commonBlock.taskconfig.ScanStartTime;

        tm pro_tm = *(gmtime(&pro_time_t));
        char yyyymmddhhmmss[16] = {0};

        sprintf(&yyyymmddhhmmss[0], "%4.4d", pro_tm.tm_year + 1900);
        sprintf(&yyyymmddhhmmss[4], "%2.2d", pro_tm.tm_mon + 1);
        sprintf(&yyyymmddhhmmss[6], "%2.2d", pro_tm.tm_mday);
        sprintf(&yyyymmddhhmmss[8], "%2.2d", pro_tm.tm_hour);
        sprintf(&yyyymmddhhmmss[10], "%2.2d", pro_tm.tm_min);
        sprintf(&yyyymmddhhmmss[12], "%2.2d", pro_tm.tm_sec);
        char yyyymmdd[16] = {0};
        strncpy(yyyymmdd, yyyymmddhhmmss, 8);

        switch (RadarProduct->at(i_pro).productheader.productheader.ProductType)
        {
            case PTYPE_PPI: // 1://PPI
                //sprintf(Elevation,"%d",(int)round(RadarProduct->at(i_pro).productheader.productdependentparameter.ppiparameter.Elevation * 10));
                //FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
                break;
            case PTYPE_RHI: // 2://RHI
                //sprintf(Elevation,"%d",(int)round(RadarProduct->at(i_pro).productheader.productdependentparameter.rhiparameter.Azimuth * 10));
                //FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
                break;
            case PTYPE_CAPPI: // 3://CAPPI //格点
                //            ((RASTERFORMAT*)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.
                //            sprintf(RowResolutionofGrid,"%d",((RASTERFORMAT*)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.RowResolution);
                //            sprintf(ColumnResolutionofGrid,"%d",((RASTERFORMAT*)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.RowSideLength);
                //            sprintf(Elevation,"%d",(int)round(RadarProduct->at(i_pro).productheader.productdependentparameter.cappiparameter.Layer));
                //            FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(RowResolutionofGrid) + "x" + string(ColumnResolutionofGrid) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
                break;
            case PTYPE_MAX: //MAX //格点
                strcpy(Elevation, "NUL");
                Proname = "MAX";
                if (((MAXFORMAT *)RadarProduct->at(i_pro).productdatapoint)->MAXData->RasterHeader.RowResolution >= 100)
                {
                    sprintf(RowResolutionofGrid, "%d", ((MAXFORMAT *)RadarProduct->at(i_pro).productdatapoint)->MAXData->RasterHeader.RowResolution / 100);
                }
                else
                {
                    sprintf(RowResolutionofGrid, "%.1f", ((MAXFORMAT *)RadarProduct->at(i_pro).productdatapoint)->MAXData->RasterHeader.RowResolution / 100.0);
                }
                if (((MAXFORMAT *)RadarProduct->at(i_pro).productdatapoint)->MAXData->RasterHeader.ColumnResolution >= 100)
                {
                    sprintf(ColumnResolutionofGrid, "%d", ((MAXFORMAT *)RadarProduct->at(i_pro).productdatapoint)->MAXData->RasterHeader.ColumnResolution / 100);
                }
                else
                {
                    sprintf(ColumnResolutionofGrid, "%.1f", ((MAXFORMAT *)RadarProduct->at(i_pro).productdatapoint)->MAXData->RasterHeader.ColumnResolution / 100.0);
                }
                FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(RowResolutionofGrid) + "x" + string(ColumnResolutionofGrid) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
                break;
            case PTYPE_ET://ET //格点
                strcpy(Elevation, "NUL");
                Proname = "ET";
                if (((RASTERFORMAT *)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.RowResolution >= 100)
                {
                    sprintf(RowResolutionofGrid, "%d", ((RASTERFORMAT *)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.RowResolution / 100);
                }
                else
                {
                    sprintf(RowResolutionofGrid, "%.1f", ((RASTERFORMAT *)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.RowResolution / 100.0);
                }
                if (((RASTERFORMAT *)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.ColumnResolution >= 100)
                {
                    sprintf(ColumnResolutionofGrid, "%d", ((RASTERFORMAT *)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.ColumnResolution / 100);
                }
                else
                {
                    sprintf(ColumnResolutionofGrid, "%.1f", ((RASTERFORMAT *)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.ColumnResolution / 100.0);
                }
                FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(RowResolutionofGrid) + "x" + string(ColumnResolutionofGrid) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
                break;
            case PTYPE_EB://EB //格点
                strcpy(Elevation, "NUL");
                Proname = "EB";
                if (((RASTERFORMAT *)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.RowResolution >= 100)
                {
                    sprintf(RowResolutionofGrid, "%d", ((RASTERFORMAT *)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.RowResolution / 100);
                }
                else
                {
                    sprintf(RowResolutionofGrid, "%.1f", ((RASTERFORMAT *)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.RowResolution / 100.0);
                }
                if (((RASTERFORMAT *)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.ColumnResolution >= 100)
                {
                    sprintf(ColumnResolutionofGrid, "%d", ((RASTERFORMAT *)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.ColumnResolution / 100);
                }
                else
                {
                    sprintf(ColumnResolutionofGrid, "%.1f", ((RASTERFORMAT *)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.ColumnResolution / 100.0);
                }
                FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(RowResolutionofGrid) + "x" + string(ColumnResolutionofGrid) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
                break;
            case PTYPE_VIL://VIL //格点
                strcpy(Elevation, "NUL");
                Proname = "VIL";
                if (((RASTERFORMAT *)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.RowResolution >= 100)
                {
                    sprintf(RowResolutionofGrid, "%d", ((RASTERFORMAT *)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.RowResolution / 100);
                }
                else
                {
                    sprintf(RowResolutionofGrid, "%.1f", ((RASTERFORMAT *)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.RowResolution / 100.0);
                }
                if (((RASTERFORMAT *)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.ColumnResolution >= 100)
                {
                    sprintf(ColumnResolutionofGrid, "%d", ((RASTERFORMAT *)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.ColumnResolution / 100);
                }
                else
                {
                    sprintf(ColumnResolutionofGrid, "%.1f", ((RASTERFORMAT *)RadarProduct->at(i_pro).productdatapoint)->RasterHeader.ColumnResolution / 100.0);
                }
                FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(RowResolutionofGrid) + "x" + string(ColumnResolutionofGrid) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
                break;
            case PTYPE_OHP://OHP
                strcpy(Elevation, "NUL");
                FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
                break;
            case PTYPE_THP://THP
                strcpy(Elevation, "NUL");
                FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
                break;
            case PTYPE_PolarOHP://PolarOHP
                strcpy(Elevation, "NUL");
                FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
                break;
            case PTYPE_USP://USP
                strcpy(Elevation, "NUL");
                FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
                break;
            case PTYPE_VAD://VAD
                Proname = "VAD";
                FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + "NUL" + "_" + "NUL" + "_" + "NUL" + "." + string(SiteCode) + ".BIN";
                break;
            case PTYPE_VWP://VWP
                Proname = "VWP";
                FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + "NUL" + "_" + "NUL" + "_" + "NUL" + "." + string(SiteCode) + ".BIN";
                break;
            case PTYPE_STI://STI
                strcpy(Elevation, "NUL");
                FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
                break;
            case PTYPE_HI://HI
                strcpy(Elevation, "NUL");
                FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
                break;
            case PTYPE_M://MESO
                strcpy(Elevation, "NUL");
                FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
                break;
            case PTYPE_TVS://TVS
                strcpy(Elevation, "NUL");
                FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
                break;
            case PTYPE_SS://SS
                strcpy(Elevation, "NUL");
                FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + Proname + "_" + string(BinResolutionofRadial) + "_" + string(MaxDistance) + "_" + string(Elevation) + "." + string(SiteCode) + ".BIN";
                break;
            default:
                FileName = "Z_RADR_I_" + string(SiteName) + "_" + string(yyyymmddhhmmss) + "_P_DOR_X_" + to_string(RadarProduct->at(i_pro).productheader.productheader.ProductType) + "_" + string(nul) + "_" + string(nul) + "_" + string(nul) + "." + string(SiteCode) + ".BIN";
                break;
        }
        FileDir = string(SiteName) + "/" + string(yyyymmdd) + "/" + Proname + "/";
        //m_FileName_out->at(i_pro) = new char[128];
        //string temp = FileDir + FileName;
        m_FileName_out->at(i_pro) = FileDir + FileName;
        //temp.copy(m_FileName_out[i_pro],127,0);
    }
    //return (void*)&m_FileName_out;
}

void CNrietFileIO::Get_nNumSum()
{
    m_nRadialNumSum = 0;
    m_nLayerNum = m_RadarDataHead->ObservationInfo.SType;
    if (m_nLayerNum > 100)
    {
        m_nLayerNum -= 100;
        for (int i = 0; i < m_nLayerNum; i++)
        {
            m_nRadialNumSum += m_RadarDataHead->ObservationInfo.LayerInfo[i].RecordNumber;
        }
        //m_nRadialNum = m_RadarDataHead->ObservationInfo.LayerInfo[0].RecordNumber;
    }
    else if (m_nLayerNum == 10 || m_nLayerNum == 1 || m_nLayerNum == 20)
    {
        m_nLayerNum = 1;
        m_nRadialNumSum = m_RadarDataHead->ObservationInfo.LayerInfo[0].RecordNumber;
    }

    return;
}

void CNrietFileIO::Get_nNumSum_SBand_PhasedArray()
{
    m_nRadialNumSum = 0;
    m_nLayerNum = m_RadarDataHead_SBand->ObservationInfo.SType;
    m_nValidLayerNum = 0;
    m_nValidRadialNumSum = 0;
    if (m_nLayerNum > 100)
    {
        m_nLayerNum -= 100;
        for (int i = 0; i < m_nLayerNum; i++)
        {
            m_nRadialNumSum += m_RadarDataHead_SBand->ObservationInfo.LayerInfo[i].RecordNumber;
        }
    }
    else if (m_nLayerNum == 10 || m_nLayerNum == 1 || m_nLayerNum == 20)
    {
        m_nLayerNum = 1;
        m_nRadialNumSum = m_RadarDataHead_SBand->ObservationInfo.LayerInfo[0].RecordNumber;
    }
    m_validLayer.resize(m_nLayerNum);
    m_validLayer.assign(m_validLayer.size(), false);
    unsigned short minZbinWidth = m_RadarDataHead_SBand->ObservationInfo.LayerInfo[0].ZBinWidth;
    for (int nlayer = 0; nlayer < m_nLayerNum; ++nlayer)
    {
        if (m_RadarDataHead_SBand->ObservationInfo.LayerInfo[nlayer].ZBinWidth < minZbinWidth)
        {
            minZbinWidth = m_RadarDataHead_SBand->ObservationInfo.LayerInfo[nlayer].ZBinWidth;
        }
    }
    for (int nlayer = 0; nlayer < m_nLayerNum; ++nlayer)
    {
        if (m_RadarDataHead_SBand->ObservationInfo.LayerInfo[nlayer].ZBinWidth == minZbinWidth)
        {
            m_validLayer[nlayer] = true;
            m_nValidLayerNum++;
            m_nValidRadialNumSum += m_RadarDataHead_SBand->ObservationInfo.LayerInfo[nlayer].RecordNumber;
        }
    }

    return;
}

void CNrietFileIO::Sort_pLineData()
{
    int i_RadialNumSum = 0;
    //	NewLineDataBlock tempLineData;
    for (int i_Layer = 0; i_Layer < m_nLayerNum; i_Layer++)
    {
        int sort_start = i_RadialNumSum;
        int sort_end = sort_start + m_RadarDataHead->ObservationInfo.LayerInfo[i_Layer].RecordNumber - 1;
        i_RadialNumSum = sort_end + 1;
        Sort_Data(&m_pLineData[sort_start], m_RadarDataHead->ObservationInfo.LayerInfo[i_Layer].RecordNumber);
    }
}

void CNrietFileIO::Sort_Data(NewLineDataBlock *DataPoint, int nSortNum)
{
    if (nSortNum == 1)
    {
        return;
    }
    if (nSortNum == 0)
    {
        return;
    }
    int Temp_Index = (nSortNum - 1) / 2;
    unsigned short Temp_Az = DataPoint[Temp_Index].LineDataInfo.Az;
    NewLineDataBlock *tempLineData = new (NewLineDataBlock);
    int i_Sort = 0;
    int i_Sort_End = nSortNum - 1;
    //	if (nSortNum > 20) cout << nSortNum << endl;

    for (i_Sort; i_Sort < nSortNum; i_Sort++)
    {
        if (DataPoint[i_Sort].LineDataInfo.Az < Temp_Az  && i_Sort > Temp_Index)
        {
            *tempLineData = DataPoint[Temp_Index];
            DataPoint[Temp_Index] = DataPoint[i_Sort];
            DataPoint[i_Sort] = *tempLineData;
            Temp_Index = i_Sort;
        }
        if (DataPoint[i_Sort].LineDataInfo.Az > Temp_Az)
        {
            for (i_Sort_End; i_Sort_End > i_Sort; i_Sort_End--)
            {
                if (DataPoint[i_Sort_End].LineDataInfo.Az < Temp_Az)
                {
                    *tempLineData = DataPoint[i_Sort_End];
                    DataPoint[i_Sort_End] = DataPoint[i_Sort];
                    DataPoint[i_Sort] = *tempLineData;
                    if (i_Sort > Temp_Index)
                    {
                        *tempLineData = DataPoint[Temp_Index];
                        DataPoint[Temp_Index] = DataPoint[i_Sort];
                        DataPoint[i_Sort] = *tempLineData;
                        Temp_Index = i_Sort;
                    }
                    break;
                }
                else if (i_Sort_End == Temp_Index)
                {
                    *tempLineData = DataPoint[Temp_Index];
                    DataPoint[Temp_Index] = DataPoint[i_Sort];
                    DataPoint[i_Sort] = *tempLineData;
                    Temp_Index = i_Sort;
                    break;
                }
            }

        }
        if (i_Sort >= i_Sort_End)
        {
            break;
        }
    }
    delete tempLineData;
    if (Temp_Index >= 2)
    {
        Sort_Data(DataPoint, Temp_Index);
    }
    if (nSortNum - Temp_Index - 2 >= 2)
    {
        Sort_Data(&DataPoint[Temp_Index + 1], nSortNum - Temp_Index - 1);
    }

    return;
}

void CNrietFileIO::Normalize_Az()
{
    m_nRadialNum = GetMaxRadialNum();
    unsigned short i_dAz = (unsigned short)25 * (((m_pLineData[m_RadarDataHead->ObservationInfo.LayerInfo[0].RecordNumber - 1].LineDataInfo.Az - m_pLineData[0].LineDataInfo.Az)\
                           / m_nRadialNum) / 25 + 1);
    m_nRadialNum = (m_pLineData[m_RadarDataHead->ObservationInfo.LayerInfo[0].RecordNumber - 1].LineDataInfo.Az - m_pLineData[0].LineDataInfo.Az) / i_dAz;
    if (m_pLineData[0].LineDataInfo.Az < i_dAz)
    {
        m_nRadialNum++;
    }
    cout << "The Data is remapped to ";
    cout << m_nRadialNum;
    cout << " records per PPI" << endl;
    //m_nRadialNum = (int)360 * m_nRadialNum % 360;
    unsigned short *i_Radar_Az = new unsigned short[m_nRadialNum];
    for (int i_Az = 0; i_Az < m_nRadialNum; i_Az++)
    {
        if (m_pLineData[0].LineDataInfo.Az < i_dAz)
        {
            i_Radar_Az[i_Az] = (unsigned short)i_Az * i_dAz + m_pLineData[0].LineDataInfo.Az / i_dAz * i_dAz;
        }
        else
        {
            i_Radar_Az[i_Az] = (unsigned short)(i_Az + 1) * i_dAz + m_pLineData[0].LineDataInfo.Az / i_dAz * i_dAz;
        }
    }

    //cout << *i_Radar_Az << endl;

    RadarDataHead *i_TempRadarDataHead = m_RadarDataHead;      // 雷达数据头
    NewLineDataBlock *i_TemppLineData = m_pLineData;      // 径向数据指针
    m_RadarDataHead = new RadarDataHead();
    m_pLineData = new NewLineDataBlock[m_nRadialNum * m_nLayerNum];
    short MissingValue[3000] = {-32768};
    memcpy(m_RadarDataHead, i_TempRadarDataHead, sizeof(RadarDataHead));
    int i_RadialSum_org = 0;
    for (int i_Layer = 0; i_Layer < m_nLayerNum; i_Layer++)
    {
        int i_Radial_org = 0;
        for (int i_Radial = 0; i_Radial < m_nRadialNum ; i_Radial++)
            for (i_Radial_org; i_Radial_org < i_TempRadarDataHead->ObservationInfo.LayerInfo[i_Layer].RecordNumber; i_Radial_org++)
            {
                int dAzback = 9999;
                int dAzfor = 9999;

                if (i_Radar_Az[i_Radial] <= i_TemppLineData[i_RadialSum_org + i_Radial_org].LineDataInfo.Az)
                {
                    if (i_Radar_Az[i_Radial + 1] > i_TemppLineData[i_RadialSum_org + i_Radial_org].LineDataInfo.Az)
                    {
                        if (i_Radial == 0)
                        {
                            dAzback = 36000 - i_TemppLineData[i_RadialSum_org + i_TempRadarDataHead->ObservationInfo.LayerInfo[i_Layer].RecordNumber - 1].LineDataInfo.Az;
                            dAzfor = i_TemppLineData[i_RadialSum_org + i_Radial_org].LineDataInfo.Az - i_Radar_Az[i_Radial];
                            if (dAzback < dAzfor)
                            {
                                //cout << "new az =";
                                //cout << i_Radar_Az[i_Radial] << endl;
                                //cout << "org az = ";
                                //cout << i_TemppLineData[i_RadialSum_org + i_TempRadarDataHead->ObservationInfo.LayerInfo[i_Layer].RecordNumber - 1].LineDataInfo.Az << endl;
                                memcpy(&m_pLineData[i_Layer * m_nRadialNum + i_Radial], &i_TemppLineData[i_RadialSum_org + i_TempRadarDataHead->ObservationInfo.LayerInfo[i_Layer].RecordNumber - 1], sizeof(NewLineDataBlock));
                                //m_pLineData[i_Layer * m_nRadialNum + i_Radial].LineDataInfo.Elev = m_RadarDataHead->ObservationInfo.LayerInfo[i_Layer].SwpAngles;
                                m_pLineData[i_Layer * m_nRadialNum + i_Radial].LineDataInfo.Az = i_Radar_Az[i_Radial];
                                break;
                            }
                            else
                            {
                                //cout << "new az =";
                                //cout << i_Radar_Az[i_Radial] << endl;
                                //cout << "org az = ";
                                //cout << i_TemppLineData[i_RadialSum_org + i_Radial_org].LineDataInfo.Az << endl;
                                memcpy(&m_pLineData[i_Layer * m_nRadialNum + i_Radial], &i_TemppLineData[i_RadialSum_org + i_Radial_org ], sizeof(NewLineDataBlock));
                                //m_pLineData[i_Layer * m_nRadialNum + i_Radial].LineDataInfo.Elev = m_RadarDataHead->ObservationInfo.LayerInfo[i_Layer].SwpAngles;
                                m_pLineData[i_Layer * m_nRadialNum + i_Radial].LineDataInfo.Az = i_Radar_Az[i_Radial];
                                break;
                            }
                        }
                        else
                        {
                            //cout << "new az =";
                            //cout << i_Radar_Az[i_Radial] << endl;
                            //cout << "org az = ";
                            //cout << i_TemppLineData[i_RadialSum_org + i_Radial_org].LineDataInfo.Az << endl;
                            memcpy(&m_pLineData[i_Layer * m_nRadialNum + i_Radial], &i_TemppLineData[i_RadialSum_org + i_Radial_org], sizeof(NewLineDataBlock));
                            //m_pLineData[i_Layer * m_nRadialNum + i_Radial].LineDataInfo.Elev = m_RadarDataHead->ObservationInfo.LayerInfo[i_Layer].SwpAngles;
                            m_pLineData[i_Layer * m_nRadialNum + i_Radial].LineDataInfo.Az = i_Radar_Az[i_Radial];
                            break;
                        }
                    }
                    else
                    {
                        m_pLineData[i_Layer * m_nRadialNum + i_Radial].LineDataInfo.Elev = m_RadarDataHead->ObservationInfo.LayerInfo[i_Layer].SwpAngles;
                        m_pLineData[i_Layer * m_nRadialNum + i_Radial].LineDataInfo.Az = i_Radar_Az[i_Radial];
                        memcpy(&m_pLineData[i_Layer * m_nRadialNum + i_Radial].UnZ, &MissingValue, sizeof(short[3000]));
                        memcpy(&m_pLineData[i_Layer * m_nRadialNum + i_Radial].CorZ, &MissingValue, sizeof(short[3000]));
                        memcpy(&m_pLineData[i_Layer * m_nRadialNum + i_Radial].V, &MissingValue, sizeof(short[3000]));
                        memcpy(&m_pLineData[i_Layer * m_nRadialNum + i_Radial].W, &MissingValue, sizeof(short[3000]));
                        memcpy(&m_pLineData[i_Layer * m_nRadialNum + i_Radial].ZDR, &MissingValue, sizeof(short[3000]));
                        memcpy(&m_pLineData[i_Layer * m_nRadialNum + i_Radial].ROHV, &MissingValue, sizeof(short[3000]));
                        memcpy(&m_pLineData[i_Layer * m_nRadialNum + i_Radial].KDP, &MissingValue, sizeof(short[3000]));
                        memcpy(&m_pLineData[i_Layer * m_nRadialNum + i_Radial].PHDP, &MissingValue, sizeof(short[3000]));
                        memcpy(&m_pLineData[i_Layer * m_nRadialNum + i_Radial].LDR, &MissingValue, sizeof(short[3000]));

                        break;
                    }
                }
                if (i_Radar_Az[i_Radial] > i_TemppLineData[i_RadialSum_org + i_Radial_org].LineDataInfo.Az)
                {
                    if (i_Radar_Az[i_Radial] <= i_TemppLineData[i_RadialSum_org + i_Radial_org + 1].LineDataInfo.Az)
                    {
                        dAzback = i_Radar_Az[i_Radial] - i_TemppLineData[i_RadialSum_org + i_Radial_org].LineDataInfo.Az;
                        dAzfor = i_TemppLineData[i_RadialSum_org + i_Radial_org + 1].LineDataInfo.Az - i_Radar_Az[i_Radial];
                        if (dAzback < dAzfor)
                        {
                            //cout << "new az =";
                            //cout << i_Radar_Az[i_Radial] << endl;
                            //cout << "org az = ";
                            //cout << i_TemppLineData[i_RadialSum_org + i_Radial_org].LineDataInfo.Az << endl;
                            memcpy(&m_pLineData[i_Layer * m_nRadialNum + i_Radial], &i_TemppLineData[i_RadialSum_org + i_Radial_org], sizeof(NewLineDataBlock));
                            //m_pLineData[i_Layer * m_nRadialNum + i_Radial].LineDataInfo.Elev = m_RadarDataHead->ObservationInfo.LayerInfo[i_Layer].SwpAngles;
                            m_pLineData[i_Layer * m_nRadialNum + i_Radial].LineDataInfo.Az = i_Radar_Az[i_Radial];
                            break;
                        }
                        else
                        {
                            //cout << "new az =";
                            //cout << i_Radar_Az[i_Radial] << endl;
                            //cout << "org az = ";
                            //cout << i_TemppLineData[i_RadialSum_org + i_Radial_org + 1].LineDataInfo.Az << endl;
                            memcpy(&m_pLineData[i_Layer * m_nRadialNum + i_Radial], &i_TemppLineData[i_RadialSum_org + i_Radial_org + 1], sizeof(NewLineDataBlock));
                            //m_pLineData[i_Layer * m_nRadialNum + i_Radial].LineDataInfo.Elev = m_RadarDataHead->ObservationInfo.LayerInfo[i_Layer].SwpAngles;
                            m_pLineData[i_Layer * m_nRadialNum + i_Radial].LineDataInfo.Az = i_Radar_Az[i_Radial];
                            break;
                        }
                    }
                    else if (i_Radar_Az[i_Radial] > 36000 - i_dAz)
                    {
                        dAzback = i_Radar_Az[i_Radial] - i_TemppLineData[i_RadialSum_org + i_Radial_org].LineDataInfo.Az;
                        dAzfor = i_TemppLineData[i_RadialSum_org].LineDataInfo.Az + 36000 - i_Radar_Az[i_Radial];
                        if (dAzback < dAzfor)
                        {
                            //cout << "new az =";
                            //cout << i_Radar_Az[i_Radial] << endl;
                            //cout << "org az = ";
                            //cout << i_TemppLineData[i_RadialSum_org + i_Radial_org].LineDataInfo.Az << endl;
                            memcpy(&m_pLineData[i_Layer * m_nRadialNum + i_Radial], &i_TemppLineData[i_RadialSum_org + i_Radial_org], sizeof(NewLineDataBlock));
                            //m_pLineData[i_Layer * m_nRadialNum + i_Radial].LineDataInfo.Elev = m_RadarDataHead->ObservationInfo.LayerInfo[i_Layer].SwpAngles;
                            m_pLineData[i_Layer * m_nRadialNum + i_Radial].LineDataInfo.Az = i_Radar_Az[i_Radial];
                            break;
                        }
                        else
                        {
                            //cout << "new az =";
                            //cout << i_Radar_Az[i_Radial] << endl;
                            //cout << "org az = ";
                            //cout << i_TemppLineData[i_RadialSum_org + i_Radial_org + 1].LineDataInfo.Az << endl;
                            memcpy(&m_pLineData[i_Layer * m_nRadialNum + i_Radial], &i_TemppLineData[i_RadialSum_org], sizeof(NewLineDataBlock));
                            //m_pLineData[i_Layer * m_nRadialNum + i_Radial].LineDataInfo.Elev = m_RadarDataHead->ObservationInfo.LayerInfo[i_Layer].SwpAngles;
                            m_pLineData[i_Layer * m_nRadialNum + i_Radial].LineDataInfo.Az = i_Radar_Az[i_Radial];
                            break;
                        }
                    }
                }



            }
        i_RadialSum_org += i_TempRadarDataHead->ObservationInfo.LayerInfo[i_Layer].RecordNumber;
        m_RadarDataHead->ObservationInfo.LayerInfo[i_Layer].RecordNumber = m_nRadialNum;
    }


    delete[] i_Radar_Az;
    delete i_TempRadarDataHead;
    delete[] i_TemppLineData;
    return;
}

int CNrietFileIO::GetMaxRadialNum()
{
    int MaxRadialNum = 0;
    for (int i_Layer = 0; i_Layer < m_nLayerNum; i_Layer++)
    {
        if (m_RadarDataHead->ObservationInfo.LayerInfo[i_Layer].RecordNumber > MaxRadialNum)
        {
            MaxRadialNum = m_RadarDataHead->ObservationInfo.LayerInfo[i_Layer].RecordNumber;
        }
    }
    return MaxRadialNum;
}

int CNrietFileIO::ConvertInternalVTBtoStandardFormat1_0()
{
    m_RadarData = new WRADRAWDATA();
    m_RadarHead = &(m_RadarData->commonBlock);

    //----------Common Block----------
    //----Generic Headare----
    m_RadarHead->genericheader.MagicNumber = 0x4D545352;     //固定标志，用来指示雷达数据文件。
    m_RadarHead->genericheader.MajorVersion = 1;             //主版本号
    m_RadarHead->genericheader.MinorVersion = 0;             //次版本号
    m_RadarHead->genericheader.GenericType = 1;              //文件类型，1-基数据文件；2-产品文件
    m_RadarHead->genericheader.ProductType = PREFILLVALUE_INT;   //文件类型为1时不适应
    strncpy(m_RadarHead->genericheader.Reserved, "Reserved", sizeof(m_RadarHead->genericheader.Reserved) - 1); //保留字段

    //----Site Config----
    strncpy(m_RadarHead->siteconfig.SiteCode, m_RadarDataHead->SiteInfo.StationNumber, sizeof(m_RadarHead->siteconfig.SiteCode) - 1); //站号具有唯一性，用来区别不同的雷达站
    strncpy(m_RadarHead->siteconfig.SiteName, m_RadarDataHead->SiteInfo.Station, sizeof(m_RadarHead->siteconfig.SiteName) - 1);      //站点名称，如BeiJing
    m_RadarHead->siteconfig.Latitude = m_RadarDataHead->SiteInfo.LatitudeValue / 1000.0; //雷达站天线所在位置纬度，Unit:°
    m_RadarHead->siteconfig.Longitude = m_RadarDataHead->SiteInfo.LongitudeValue / 1000.0; //雷达站天线所在位置精度，Unit:°
    m_RadarHead->siteconfig.AntennaHeight = m_RadarDataHead->SiteInfo.Height / 1000.0;   //天线馈源水平时海拔高度，Unit:m
    m_RadarHead->siteconfig.GroundHeight = m_RadarDataHead->OtherInfo.CenterAltValue / 1000.0; //雷达塔楼地面海拔高度，Unit:m
    //    m_RadarDataHead->PerformanceInfo.WaveLength = 30;   //X波段波长为30 mm
    //  以下3变量原始数据中为0
    m_RadarHead->siteconfig.Frequency = 299792458.0 / m_RadarDataHead->PerformanceInfo.WaveLength / 1000.0; //工作频率，Unit:MHz
    m_RadarHead->siteconfig.BeamWidthHori = m_RadarDataHead->PerformanceInfo.HorBeamW / 100.0;           //水平波束宽度，Unit:°
    m_RadarHead->siteconfig.BeamWidthVert = m_RadarDataHead->PerformanceInfo.VerBeamW / 100.0;           //垂直波束宽度，Unit:°

    m_RadarHead->siteconfig.RdaVersion = 1;      //RDA版本号
    m_RadarHead->siteconfig.RadarType = m_RadarDataHead->OtherInfo.RadarType;     //雷达类型   1–SA;    2–SB;    3–SC;    4–SAD;    33–CA;    34–CB;    35–CC;    36–CCJ;    37–CD    ;101-X
    strncpy(m_RadarHead->siteconfig.Reserved, "Reserved", sizeof(m_RadarHead->siteconfig.Reserved) - 1); //保留字段

    //----Task Config----
    strncpy(m_RadarHead->taskconfig.TaskName, "VCP", sizeof(m_RadarHead->taskconfig.TaskName) - 1);    //任务名称,如VCP21
    strncpy(m_RadarHead->taskconfig.TaskDescription, "Reserved", sizeof(m_RadarHead->taskconfig.TaskDescription) - 1); //任务描述
    m_RadarHead->taskconfig.PolarizationType = int(m_RadarDataHead->PerformanceInfo.Polarizations) + 1; //极化方式，1-水平极化，2-垂直极化，3-水平/垂直同时，4-水平/垂直交替
    //    m_RadarHead->taskconfig.ScanType = ;//扫描任务类型，0-体扫，1-单层PPI，2-单层RHI，3-单层扇扫，4-扇体扫，5-多层RHI，6-手工扫描
    if (m_RadarDataHead->ObservationInfo.SType == 1)
    {
        m_RadarHead->taskconfig.ScanType = 2;
        m_RadarHead->taskconfig.CutNumber = 1;
    }
    else if (m_RadarDataHead->ObservationInfo.SType == 10)
    {
        m_RadarHead->taskconfig.ScanType = 1;    //可能为3，当前版本不做判断
        m_RadarHead->taskconfig.CutNumber = 1;
    }
    else if (m_RadarDataHead->ObservationInfo.SType == 20)
    {
        cout << "Cannot deal with this type" << endl;
        return -1;
    }
    else if (m_RadarDataHead->ObservationInfo.SType > 100)
    {
        m_RadarHead->taskconfig.ScanType = 0;
        m_RadarHead->taskconfig.CutNumber = m_RadarDataHead->ObservationInfo.SType - 100;
    }

    m_RadarHead->taskconfig.PulseWidth = int(m_RadarDataHead->ObservationInfo.LayerInfo[0].PluseW) * 1000;//发射脉冲宽度，Unit:ns 纳秒

    time_t ScanStartTime = time_convert((int)m_RadarDataHead->ObservationInfo.SYear, (int)m_RadarDataHead->ObservationInfo.SMonth, (int)m_RadarDataHead->ObservationInfo.SDay, \
                                        (int)m_RadarDataHead->ObservationInfo.SHour, (int)m_RadarDataHead->ObservationInfo.SMinute, (int)m_RadarDataHead->ObservationInfo.SSecond);
    //cout << ScanStartTime <<endl;//date +%s，从 1970 年 1 月 1 日 00:00:00 UTC 到目前为止的秒数（时间戳）
    m_RadarHead->taskconfig.ScanStartTime = int(ScanStartTime);//扫描开始时间，扫描开始时间为UTC标准时间计数,1970年1月1日0时为起始计数基准点,Unit:s,

    //m_RadarHead->taskconfig.CutNumber = ;//根据扫描任务类型确定的扫描层数，见ScanType处
    m_RadarHead->taskconfig.HorizontalNoise = PREFILLVALUE_FLOAT;//水平通道的噪声电平,Unit:dBm 分贝毫瓦
    m_RadarHead->taskconfig.VerticalNoise = PREFILLVALUE_FLOAT;//垂直通道的噪声电平,Unit:dBm 分贝毫瓦
    m_RadarHead->taskconfig.HorizontalCalibration = PREFILLVALUE_FLOAT;//水平通道的反射率标定常数,Unit:dB
    m_RadarHead->taskconfig.VerticalCalibration = PREFILLVALUE_FLOAT;//垂直通道的反射率标定常数,Unit:dB
    m_RadarHead->taskconfig.HorizontalNoiseTemperature = PREFILLVALUE_FLOAT;//水平通道噪声温度，Unit:K 开氏温度
    m_RadarHead->taskconfig.VerticalNoiseTemperature = PREFILLVALUE_FLOAT;//垂直通道噪声温度，Unit:K 开氏温度
    m_RadarHead->taskconfig.ZDRCalibration = PREFILLVALUE_FLOAT;//ZDR标定偏差,Unit:dB
    m_RadarHead->taskconfig.PHIDPCalibration = PREFILLVALUE_FLOAT;//差分相移标定偏差，Unit:°
    m_RadarHead->taskconfig.LDRCalibration = PREFILLVALUE_FLOAT;//系统LDR标定偏差,Unit:dB
    strncpy(m_RadarHead->taskconfig.Reserved, "Reserved", sizeof(m_RadarHead->taskconfig.Reserved) - 1); //保留字段

    //----Cut Congig----
    //    m_RadarHead->cutconfig.reserve(m_RadarHead->taskconfig.CutNumber);
    m_RadarHead->cutconfig.resize(m_RadarHead->taskconfig.CutNumber);
    for (int i_cut = 0; i_cut < m_RadarHead->taskconfig.CutNumber; i_cut++)
    {
        m_RadarHead->cutconfig[i_cut].ProcessMode = 3;//int(m_RadarDataHead->PerformanceInfo.VelocityP);  //处理模式,1-PPP,2-FFT
        m_RadarHead->cutconfig[i_cut].WaveForm = PREFILLVALUE_INT;
        //波形类别，0 – CS连续监测，1 – CD连续多普勒，2 – CDX多普勒扩展，3 – Rx Test，4 – BATCH批模式，5 – Dual PRF双PRF，6 - Staggered PRT 参差PRT
        m_RadarHead->cutconfig[i_cut].PRF1 = m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].PRF1 / 10; //脉冲重复频率1，对于Batch、双PRF和参差PRT模式，表示高PRF值。对于其它单PRF模式，表示唯一的PRF值。Unit:Hz
        m_RadarHead->cutconfig[i_cut].PRF2 = m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].PRF2 / 10; //脉冲重复频率2，对Batch、双PRF和参差PRT模式，表示低PRF值。对其它单PRF模式，无效。Unit:Hz
        m_RadarHead->cutconfig[i_cut].DealiasingMode = PREFILLVALUE_INT;
        //速度退模糊方法,1–单PRF,2–双PRF3:2模式,3–双PRF4:3模式,4–双PRF 5:4模式
        m_RadarHead->cutconfig[i_cut].Azimuth = m_RadarDataHead->ObservationInfo.RHIA / 100.0;  //方位角,RHI模式的方位角,Unit:°
        m_RadarHead->cutconfig[i_cut].Elevation = m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].SwpAngles / 100.0; //仰角,PPI模式的俯仰角,Unit:°
        if (m_RadarHead->taskconfig.ScanType == 2)
        {
            m_RadarHead->cutconfig[i_cut].StartAngle = m_RadarDataHead->ObservationInfo.RHIH / 100.0; //起始角度，PPI扇扫的起始方位角，或RHI模式的高限仰角,Unit:°
            m_RadarHead->cutconfig[i_cut].EndAngle = m_RadarDataHead->ObservationInfo.RHIL / 100.0; //结束角度，PPI扇扫的结束方位角，或RHI模式的低限仰角,Unit:°
        }
        else
        {
            m_RadarHead->cutconfig[i_cut].StartAngle = PREFILLVALUE_FLOAT;
            m_RadarHead->cutconfig[i_cut].EndAngle = PREFILLVALUE_FLOAT;
        }
        m_RadarHead->cutconfig[i_cut].AngularResolution = 360.0 / m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].RecordNumber; //角度分辨率，径向数据的角度分辨率，仅用于PPI扫描模式,Unit:°
        m_RadarHead->cutconfig[i_cut].ScanSpeed = m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].DPbinNumber / 100.0; //扫描速度，PPI扫描的方位转速，或RHI扫描的俯仰转速，Unit:Deg/sec,度/秒
        m_RadarHead->cutconfig[i_cut].LogResolution = m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZBinWidth / 10.0; //强度分辨率，强度数据的距离分辨率,Unit:m
        m_RadarHead->cutconfig[i_cut].DopplerResolution = m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].VBinWidth / 10.0; //多普勒分辨率,多普勒数据的距离分辨率，Unit:m
        m_RadarHead->cutconfig[i_cut].StartRange = m_RadarDataHead->ObservationInfo.ZStartBin * m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZBinWidth / 10.0; //起始距离，数据探测起始距离，Unit:m
        m_RadarHead->cutconfig[i_cut].MaximumRange1 = m_RadarHead->cutconfig[i_cut].LogResolution \
            * m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber;  //最大距离1,对应脉冲重复频率1的最大可探测距离，Unit:m
        m_RadarHead->cutconfig[i_cut].MaximumRange2 = m_RadarHead->cutconfig[i_cut].DopplerResolution \
            * m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].VbinNumber;   //最大距离2,对应脉冲重复频率2的最大可探测距离，Unit:m
        m_RadarHead->cutconfig[i_cut].Sample1 = PREFILLVALUE_INT;    //采样个数1，对应于脉冲重复频率1的采样个数
        m_RadarHead->cutconfig[i_cut].Sample2 = PREFILLVALUE_INT;    //采样个数2，对应于脉冲重复频率2的采样个数
        m_RadarHead->cutconfig[i_cut].PhaseMode = PREFILLVALUE_INT;  //相位编码模式，1–固定相位，2–随机相位，3–SZ编码
        m_RadarHead->cutconfig[i_cut].AtmosphericLoss = PREFILLVALUE_FLOAT;    //大气衰减，双程大气衰减值，精度为小数点后保留6位，Unit:dB/km
        m_RadarHead->cutconfig[i_cut].NyquistSpeed = m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].MaxV / 100.0; //最大不模糊速度，理论最大不模糊速度,Unit:m/s
        m_RadarHead->cutconfig[i_cut].MomentsMask = 0;   //数据类型掩码，以掩码的形式表示当前允许获取的数据类型，其中：0–不允许获取数据，1 –允许获取数据，具体掩码定义见表2-6。
        //65,91 ConZ+UnZ+V+W+Zdr+PHdp+Kdp+ROhv+Ldr//
        //        m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].DataForm = 91;
        switch (m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].DataForm)
        {
            case 24:
                m_RadarHead->cutconfig[i_cut].MomentsMask |= (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4);
                break;
            case 65:
                m_RadarHead->cutconfig[i_cut].MomentsMask |= (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4) | (1 << 7) | (1 << 8) | (1 << 9) | (1 << 10) | (1 << 11);
                break;
            case 91:
                m_RadarHead->cutconfig[i_cut].MomentsMask |= (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4) | (1 << 7) | (1 << 8) | (1 << 9) | (1 << 10) | (1 << 16);
                break;
            default:
                break;
        }

        m_RadarHead->cutconfig[i_cut].MomentsSizeMask = m_RadarHead->cutconfig[i_cut].MomentsMask;    //数据大小掩码，以掩码形式表示每种数据类型字节数，其中：0–1个字节，1–2个字节，具体掩码定义见表2-6。
        m_RadarHead->cutconfig[i_cut].MiscFilterMask = 0; //滤波设置掩码，0–未应用，1–	应用，具体掩码定义见表2-7。
        m_RadarHead->cutconfig[i_cut].SQIThreshold = PREFILLVALUE_FLOAT;
        m_RadarHead->cutconfig[i_cut].SIGThreshold = PREFILLVALUE_FLOAT;
        m_RadarHead->cutconfig[i_cut].CSRThreshold = PREFILLVALUE_FLOAT;
        m_RadarHead->cutconfig[i_cut].LOGThreshold = PREFILLVALUE_FLOAT;
        m_RadarHead->cutconfig[i_cut].CPAThreshold = PREFILLVALUE_FLOAT;
        m_RadarHead->cutconfig[i_cut].PMIThreshold = PREFILLVALUE_FLOAT;
        m_RadarHead->cutconfig[i_cut].DPLOGThreshold = PREFILLVALUE_FLOAT;
        strncpy(m_RadarHead->cutconfig[i_cut].ThresholdsReserved, "", sizeof(m_RadarHead->cutconfig[i_cut].ThresholdsReserved) - 1);
        m_RadarHead->cutconfig[i_cut].dBTMask = 0;
        m_RadarHead->cutconfig[i_cut].dBZMask = 0;
        m_RadarHead->cutconfig[i_cut].VelocityMask = 0;
        m_RadarHead->cutconfig[i_cut].SpectrumWidthMask = 0;
        m_RadarHead->cutconfig[i_cut].DPMask = 0;
        strncpy(m_RadarHead->cutconfig[i_cut].MaskReserved, "", sizeof(m_RadarHead->cutconfig[i_cut].MaskReserved) - 1);
        m_RadarHead->cutconfig[i_cut].ScanSync = PREFILLVALUE_INT;
        m_RadarHead->cutconfig[i_cut].Direction = PREFILLVALUE_INT;
        m_RadarHead->cutconfig[i_cut].GroundClutterClassifierType = PREFILLVALUE_SHORT;
        m_RadarHead->cutconfig[i_cut].GroundClutterFilterType = PREFILLVALUE_SHORT;
        m_RadarHead->cutconfig[i_cut].GroundClutterFilterNotchWidth = PREFILLVALUE_SHORT;
        m_RadarHead->cutconfig[i_cut].GroundClutterFilterWindow = PREFILLVALUE_SHORT;
        strncpy(m_RadarHead->cutconfig[i_cut].Reserved, "Reserved", sizeof(m_RadarHead->cutconfig[i_cut].Reserved) - 1);
    }

    //----------Radial Block----------
    //----Radial Head----
    int m_radial_of_total = 0;
    for (int i_cut = 0; i_cut < m_RadarHead->taskconfig.CutNumber; i_cut++)
    {
        m_radial_of_total += m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].RecordNumber;
    }
    //    m_RadarData->radials.reserve(m_radial_of_total);
    m_RadarData->radials.resize(m_radial_of_total);

    int i_cut = 0;
    int i_radial_of_cut = 0;

    for (int i_radial_of_total = 0; i_radial_of_total < m_radial_of_total; i_radial_of_total++)
    {
        m_RadarData->radials[i_radial_of_total].radialheader.RadialState = 1; //径向数据状态,0–仰角开始，1–中间数据，2–仰角结束，3–体扫开始，4–体扫结束，5–RHI开始，6–RHI结束。
        if (i_radial_of_total == 0)
        {
            if (m_RadarHead->taskconfig.ScanType < 2) //0-体扫，1-单层PPI，2-单层RHI，
            {
                m_RadarData->radials[i_radial_of_total].radialheader.RadialState = 3;
            }
            else if (m_RadarHead->taskconfig.ScanType == 2)
            {
                m_RadarData->radials[i_radial_of_total].radialheader.RadialState = 5;
            }
        }
        else if (i_radial_of_total == m_radial_of_total - 1)
        {
            if (m_RadarHead->taskconfig.ScanType < 2) //0-体扫，1-单层PPI，2-单层RHI，
            {
                m_RadarData->radials[i_radial_of_total].radialheader.RadialState = 4;
            }
            else if (m_RadarHead->taskconfig.ScanType == 2)
            {
                m_RadarData->radials[i_radial_of_total].radialheader.RadialState = 6;
            }
        }
        else if (i_radial_of_cut == 0)
        {
            m_RadarData->radials[i_radial_of_total].radialheader.RadialState = 0;
        }
        else if (i_radial_of_cut == m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].RecordNumber - 1)
        {
            m_RadarData->radials[i_radial_of_total].radialheader.RadialState = 2;
        }

        m_RadarData->radials[i_radial_of_total].radialheader.SpotBlank = 0;   //消隐标志，0-正常，1-消隐
        m_RadarData->radials[i_radial_of_total].radialheader.SequenceNumber = i_radial_of_total + 1; //序号，每个体扫径向从1计数
        m_RadarData->radials[i_radial_of_total].radialheader.RadialNumber = i_radial_of_cut + 1;  //径向数，每个扫描从1计数
        m_RadarData->radials[i_radial_of_total].radialheader.ElevationNumber = i_cut + 1; //仰角编号，每个体扫从1计数
        m_RadarData->radials[i_radial_of_total].radialheader.Azimuth = m_pLineData[i_radial_of_total].LineDataInfo.Az / 100.0; //方位角，扫描的方位角度，Unit:°
        m_RadarData->radials[i_radial_of_total].radialheader.Elevation = m_pLineData[i_radial_of_total].LineDataInfo.Elev / 100.0;   //仰角，扫描的俯仰角度，Unit:°
        time_t RadialTime;
        RadialTime = time_convert((int)m_RadarDataHead->ObservationInfo.SYear, (int)m_RadarDataHead->ObservationInfo.SMonth, (int)m_RadarDataHead->ObservationInfo.SDay, \
                                  (int)m_pLineData[i_radial_of_total].LineDataInfo.Hh, (int)m_pLineData[i_radial_of_total].LineDataInfo.Mm, (int)m_pLineData[i_radial_of_total].LineDataInfo.Ss);
        if (m_RadarDataHead->ObservationInfo.SHour == 23 && m_pLineData[i_radial_of_total].LineDataInfo.Hh == 00)
        {
            RadialTime += 86400;
        }
        m_RadarData->radials[i_radial_of_total].radialheader.Seconds = int(RadialTime); //秒，径向数据采集的时间，UTC计数的秒数，从1970年1月1日0时开始计数，Unit:s
//        m_RadarData->radials[i_radial_of_total].radialheader.Seconds = int(ScanStartTime); // modified for ship
        m_RadarData->radials[i_radial_of_total].radialheader.Microseconds = m_pLineData[i_radial_of_total].LineDataInfo.Min;  //微妙，径向素数采集的时间出去UTC秒数后，留下的微秒数，Unit:ms
        switch (m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].DataForm)
        {
            case 24:
                m_RadarData->radials[i_radial_of_total].radialheader.LengthOfData = (2 * m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber + \
                    m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].VbinNumber + \
                    m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].WbinNumber) * 2;    //数据长度，仅本径向数据块所占用的长度，Unit:Bytes
                m_RadarData->radials[i_radial_of_total].radialheader.MomentNumber = 4;    //径向数据类别（如Z,V,W等各占一种）的数量
                // Add moment header length
                m_RadarData->radials[i_radial_of_total].radialheader.LengthOfData += m_RadarData->radials[i_radial_of_total].radialheader.MomentNumber * sizeof(MOMENTHEADER) + sizeof(RADIALHEADER);
                break;
            case 65:
                m_RadarData->radials[i_radial_of_total].radialheader.LengthOfData = (7 * m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber + \
                    m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].VbinNumber + \
                    m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].WbinNumber) * 2;    //数据长度，仅本径向数据块所占用的长度，Unit:Bytes
                m_RadarData->radials[i_radial_of_total].radialheader.MomentNumber = 9;    //径向数据类别（如Z,V,W等各占一种）的数量
                // Add moment header length
                m_RadarData->radials[i_radial_of_total].radialheader.LengthOfData += m_RadarData->radials[i_radial_of_total].radialheader.MomentNumber * sizeof(MOMENTHEADER) + sizeof(RADIALHEADER);
                break;
            case 91:
                m_RadarData->radials[i_radial_of_total].radialheader.LengthOfData = (7 * m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber + \
                    m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].VbinNumber + \
                    m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].WbinNumber) * 2;    //数据长度，仅本径向数据块所占用的长度，Unit:Bytes
                m_RadarData->radials[i_radial_of_total].radialheader.MomentNumber = 9;    //径向数据类别（如Z,V,W等各占一种）的数量
                // Add moment header length
                m_RadarData->radials[i_radial_of_total].radialheader.LengthOfData += m_RadarData->radials[i_radial_of_total].radialheader.MomentNumber * sizeof(MOMENTHEADER) + sizeof(RADIALHEADER);
                break;
            default:
                break;
        }

        strncpy(m_RadarData->radials[i_radial_of_total].radialheader.Reserved, "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].radialheader.Reserved) - 1); //保留字段

        //----Moment Block----
        //        m_RadarData->radials[i_radial_of_total].momentblock.reserve(m_RadarData->radials[i_radial_of_total].radialheader.MomentNumber);
        m_RadarData->radials[i_radial_of_total].momentblock.resize(m_RadarData->radials[i_radial_of_total].radialheader.MomentNumber);

        int tempparam = m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].DataForm;
        int i_moment = 0;


        if (tempparam == 11 || tempparam == 21 || tempparam == 22 || tempparam == 24 || tempparam == 26 || tempparam == 60 || tempparam == 61 || tempparam == 62 || tempparam == 65 || tempparam == 91) //!-------填补ConZ值
        {
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.DataType = 2;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Scale = 100;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset = 10000;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Flags = PREFILLVALUE_SHORT;  //标志，保留
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length = \
                m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength \
                * m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber;                                 //距离库数据的长度，Unit:Bytes
            strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved, \
                    "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved) - 1); //保留字段
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentdata.\
            resize(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length);
            for (int i = 0; i < m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber; i++)
            {
                if (m_pLineData[i_radial_of_total].CorZ[i] != PREFILLVALUE_VTB)
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                        = (unsigned short)(m_pLineData[i_radial_of_total].CorZ[i] + m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset);
                }
                else
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                            = (unsigned short) INVALID_BT;
                }
            }
            i_moment ++;
        }
        if (tempparam == 12 || tempparam == 21 || tempparam == 23 || tempparam == 24 || tempparam == 26 || tempparam == 60 || tempparam == 65) //!-------填补UnZ值
        {
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.DataType = 1;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Scale = 100;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset = 10000;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Flags = PREFILLVALUE_SHORT;  //标志，保留
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length = \
                m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength \
                * m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber;                                 //距离库数据的长度，Unit:Bytes
            strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved, \
                    "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved) - 1); //保留字段
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentdata.\
            resize(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length);
            for (int i = 0; i < m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber; i++)
            {
                if (m_pLineData[i_radial_of_total].UnZ[i] != PREFILLVALUE_VTB)
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                        = (unsigned short) m_pLineData[i_radial_of_total].UnZ[i] + m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset;
                }
                else
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                            = (unsigned short) INVALID_BT;
                }
            }
            i_moment ++;
        }
        if (tempparam == 13 || tempparam == 22 || tempparam == 23 || tempparam == 24 || tempparam == 26 || tempparam == 25 || tempparam == 60 || tempparam == 61 || tempparam == 62 || tempparam == 65 || tempparam == 91) //!-----填补V值
        {
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.DataType = 3;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Scale = 100;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset = 15000; //0
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Flags = PREFILLVALUE_SHORT;  //标志，保留
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length = \
                m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength \
                * m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].VbinNumber;                                 //距离库数据的长度，Unit:Bytes
            strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved, \
                    "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved) - 1); //保留字段
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentdata.\
            resize(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length);
            for (int i = 0; i < m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].VbinNumber; i++)
            {
                if (m_pLineData[i_radial_of_total].V[i] != PREFILLVALUE_VTB)
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                        = (unsigned short) m_pLineData[i_radial_of_total].V[i] + m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset;
                }
                else
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                            = (unsigned short) INVALID_BT;
                }
            }
            i_moment ++;
        }
        if (tempparam == 14 || tempparam == 22 || tempparam == 23 || tempparam == 24 || tempparam == 26 || tempparam == 25 || tempparam == 60 || tempparam == 61 || tempparam == 62 || tempparam == 65 || tempparam == 91) //!-----填补W值
        {
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.DataType = 4;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Scale = 100;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset = 10000;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Flags = PREFILLVALUE_SHORT;  //标志，保留
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length = \
                m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength \
                * m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].VbinNumber;                                 //距离库数据的长度，Unit:Bytes
            strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved, \
                    "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved) - 1); //保留字段
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentdata.\
            resize(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length);
            for (int i = 0; i < m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].VbinNumber; i++)
            {
                if (m_pLineData[i_radial_of_total].W[i] != PREFILLVALUE_VTB)
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                        = (unsigned short) m_pLineData[i_radial_of_total].W[i] + m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset;
                }
                else
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                            = (unsigned short) INVALID_BT;
                }
            }
            i_moment ++;
        }

        if (tempparam == 60 || tempparam == 61 || tempparam == 62 || tempparam == 65 || tempparam == 91)  //ZDR
        {
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.DataType = 7;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Scale = 100;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset = 10000;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Flags = PREFILLVALUE_SHORT;  //标志，保留
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length = \
                m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength \
                * m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber;                                 //距离库数据的长度，Unit:Bytes
            strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved, \
                    "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved) - 1); //保留字段
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentdata.\
            resize(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length);
            for (int i = 0; i < m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber; i++)
            {
                if (m_pLineData[i_radial_of_total].ZDR[i] != PREFILLVALUE_VTB)
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                        = (unsigned short) m_pLineData[i_radial_of_total].ZDR[i] + m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset;
                }
                else
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                            = (unsigned short) INVALID_BT;
                }
            }
            i_moment ++;
        }
        if (tempparam == 61 || tempparam == 62 || tempparam == 65) //PHDP
        {
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.DataType = 10;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Scale = 100;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset = 10000;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Flags = PREFILLVALUE_SHORT;  //标志，保留
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length = \
                m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength \
                * m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber;                                 //距离库数据的长度，Unit:Bytes
            strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved, \
                    "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved) - 1); //保留字段
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentdata.\
            resize(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length);
            for (int i = 0; i < m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber; i++)
            {
                if (m_pLineData[i_radial_of_total].PHDP[i] != PREFILLVALUE_VTB)
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                        = (unsigned short) m_pLineData[i_radial_of_total].PHDP[i] + 18000 + m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset;
                }
                else
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                            = (unsigned short) INVALID_BT;
                }
            }
            i_moment ++;
        }
        if (tempparam == 61 || tempparam == 62 || tempparam == 65) //KDP
        {
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.DataType = 11;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Scale = 100;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset = 10000;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Flags = PREFILLVALUE_SHORT;  //标志，保留
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length = \
                m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength \
                * m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber;                                 //距离库数据的长度，Unit:Bytes
            strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved, \
                    "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved) - 1); //保留字段
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentdata.\
            resize(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length);
            for (int i = 0; i < m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber; i++)
            {
                if (m_pLineData[i_radial_of_total].KDP[i] != PREFILLVALUE_VTB)
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                        = (unsigned short) m_pLineData[i_radial_of_total].KDP[i] + m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset;
                }
                else
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                            = (unsigned short) INVALID_BT;
                }
            }
            i_moment ++;
        }
        if (tempparam == 61 || tempparam == 62 || tempparam == 91) //ROHV
        {
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.DataType = 9;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Scale = 1000;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset = 10000;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Flags = PREFILLVALUE_SHORT;  //标志，保留
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length = \
                m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength \
                * m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber;                                 //距离库数据的长度，Unit:Bytes
            strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved, \
                    "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved) - 1); //保留字段
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentdata.\
            resize(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length);
            for (int i = 0; i < m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber; i++)
            {
                if (m_pLineData[i_radial_of_total].ROHV[i] != PREFILLVALUE_VTB)
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                        = (unsigned short) m_pLineData[i_radial_of_total].ROHV[i] + m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset;
                }
                else
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                            = (unsigned short) INVALID_BT;
                }
            }
            i_moment ++;
        }

        if (tempparam == 91) //仅对91——SNRH
        {
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.DataType = 16;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Scale = 100;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset = 10000;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Flags = PREFILLVALUE_SHORT;  //标志，保留
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length = \
                m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength \
                * m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber;                                 //距离库数据的长度，Unit:Bytes
            strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved, \
                    "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved) - 1); //保留字段
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentdata.\
            resize(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length);
            for (int i = 0; i < m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber; i++)
            {
                if (m_pLineData[i_radial_of_total].SNRH[i] != PREFILLVALUE_VTB)
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                        = (unsigned short) m_pLineData[i_radial_of_total].SNRH[i] + m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset;
                }
                else
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                            = (unsigned short) INVALID_BT;
                }
            }
            i_moment ++;
        }

        if (tempparam == 91) //仅对91——PHDP
        {
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.DataType = 10;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Scale = 100;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset = 10000;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Flags = PREFILLVALUE_SHORT;  //标志，保留
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length = \
                m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength \
                * m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber;                                 //距离库数据的长度，Unit:Bytes
            strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved, \
                    "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved) - 1); //保留字段
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentdata.\
            resize(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length);
            for (int i = 0; i < m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber; i++)
            {
                if (m_pLineData[i_radial_of_total].PHDP[i] != PREFILLVALUE_VTB)
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                        = (unsigned short) m_pLineData[i_radial_of_total].PHDP[i] + 18000 + m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset;
                }
                else
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                            = (unsigned short) INVALID_BT;
                }
            }
            i_moment ++;
        }

        if (tempparam == 61 || tempparam == 65 || tempparam == 91) //LDRH
        {
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.DataType = 8;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Scale = 100;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset = 10000;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Flags = PREFILLVALUE_SHORT;  //标志，保留
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length = \
                m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength \
                * m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber;                                 //距离库数据的长度，Unit:Bytes
            strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved, \
                    "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved) - 1); //保留字段
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentdata.\
            resize(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length);
            for (int i = 0; i < m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber; i++)
            {
                if (m_pLineData[i_radial_of_total].LDR[i] != PREFILLVALUE_VTB)
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                        = (unsigned short) m_pLineData[i_radial_of_total].LDR[i] + m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset;
                }
                else
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                            = (unsigned short) INVALID_BT;
                }
            }
            i_moment ++;
        }
        if (tempparam == 65) //ROHV
        {
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.DataType = 9;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Scale = 1000;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset = 10000;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Flags = PREFILLVALUE_SHORT;  //标志，保留
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length = \
                m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength \
                * m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber;                                 //距离库数据的长度，Unit:Bytes
            strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved, \
                    "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved) - 1); //保留字段
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentdata.\
            resize(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length);
            for (int i = 0; i < m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber; i++)
            {
                if (m_pLineData[i_radial_of_total].ROHV[i] != PREFILLVALUE_VTB)
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                        = (unsigned short) m_pLineData[i_radial_of_total].ROHV[i] + m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset;
                }
                else
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                            = (unsigned short) INVALID_BT;
                }
            }
            i_moment ++;
        }

        if (tempparam == 91) //仅对91——UnZ
        {
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.DataType = 1;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Scale = 100;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset = 10000;
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength = 2;         //库字节长度，Unit:Bytes
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Flags = PREFILLVALUE_SHORT;  //标志，保留
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length = \
                m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength \
                * m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber;                                 //距离库数据的长度，Unit:Bytes
            strncpy(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved, \
                    "Reserved", sizeof(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Reserved) - 1); //保留字段
            m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentdata.\
            resize(m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Length);
            for (int i = 0; i < m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber; i++)
            {
                if (m_pLineData[i_radial_of_total].UnZ[i] != PREFILLVALUE_VTB)
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                        = (unsigned short) m_pLineData[i_radial_of_total].UnZ[i] + m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.Offset;
                }
                else
                {
                    *(unsigned short *)&m_RadarData->radials[i_radial_of_total].momentblock.at(i_moment).momentdata.at(i * m_RadarData->radials[i_radial_of_total].momentblock[i_moment].momentheader.BinLength) \
                            = (unsigned short) INVALID_BT;
                }
            }
            i_moment ++;
        }

        i_radial_of_cut ++;
        if (i_radial_of_cut == m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].RecordNumber)
        {
            cout << "Record number of layer " << i_cut << " is " << i_radial_of_cut << endl;
            i_cut ++;
            i_radial_of_cut = 0;
        }
    }
    return 0;
}

int CNrietFileIO::ConvertStandardFormat1_0toInternalVTB()
{

    m_RadarDataHead = new RadarDataHead();
    m_pLineData = new NewLineDataBlock[m_RadarData->radials.size()];

    //----------RadarDataHead----------
    m_RadarDataHead->FileID[0] = 'R';
    m_RadarDataHead->FileID[1] = 'D';
    m_RadarDataHead->VersionNo = -2.5;
    m_RadarDataHead->FileHeaderLength = 12 + sizeof(RADARSITE) + sizeof(RADARPERFORMANCEPARAM) + sizeof(RADAROBSERVATIONPARAM) + sizeof(RADAROTHERINFORMATION);

    strncpy(m_RadarDataHead->SiteInfo.StationNumber, m_RadarHead->siteconfig.SiteCode, sizeof(m_RadarDataHead->SiteInfo.StationNumber) - 1); //站号具有唯一性，用来区别不同的雷达站
    strncpy(m_RadarDataHead->SiteInfo.Station, m_RadarHead->siteconfig.SiteName, sizeof(m_RadarDataHead->SiteInfo.Station) - 1);      //站点名称，如BeiJing
    m_RadarDataHead->SiteInfo.LatitudeValue = m_RadarHead->siteconfig.Latitude * 1000.0;   //雷达站天线所在位置纬度，Unit:°
    m_RadarDataHead->SiteInfo.LongitudeValue = m_RadarHead->siteconfig.Longitude * 1000.0; //雷达站天线所在位置精度，Unit:°
    m_RadarDataHead->SiteInfo.Height = m_RadarHead->siteconfig.AntennaHeight * 1000.0;     //天线馈源水平时海拔高度，Unit:m
    m_RadarDataHead->OtherInfo.CenterAltValue = m_RadarHead->siteconfig.GroundHeight * 1000.0; //雷达塔楼地面海拔高度，Unit:m

    m_RadarDataHead->OtherInfo.RadarType =  m_RadarHead->siteconfig.RadarType;     //雷达类型   1–SA;    2–SB;    3–SC;    4–SAD;    33–CA;    34–CB;    35–CC;    36–CCJ;    37–CD    ;101-X

    m_RadarDataHead->PerformanceInfo.Polarizations = (unsigned char)(m_RadarHead->taskconfig.PolarizationType) - 1; //极化方式，1-水平极化，2-垂直极化，3-水平/垂直同时，4-水平/垂直交替
    //    m_RadarHead->taskconfig.ScanType = ;//扫描任务类型，0-体扫，1-单层PPI，2-单层RHI，3-单层扇扫，4-扇体扫，5-多层RHI，6-手工扫描
    if (m_RadarHead->taskconfig.ScanType == 2 && m_RadarHead->taskconfig.CutNumber == 1)
    {
        m_RadarDataHead->ObservationInfo.SType = 1;
    }
    else if (m_RadarHead->taskconfig.ScanType == 1 && m_RadarHead->taskconfig.CutNumber == 1)
    {
        m_RadarDataHead->ObservationInfo.SType = 10;
    }
    else if (m_RadarHead->taskconfig.ScanType == 0)
    {
        m_RadarDataHead->ObservationInfo.SType = m_RadarHead->taskconfig.CutNumber + 100;
    }
    for (int i_cut = 0; i_cut < m_RadarHead->taskconfig.CutNumber; i_cut++)
    {
        m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].PluseW = (unsigned short)(m_RadarHead->taskconfig.PulseWidth / 1000) ;//发射脉冲宽度，Unit:ns 纳秒
    }

    for (int i_cut = 0; i_cut < m_RadarHead->taskconfig.CutNumber; i_cut++)
    {
        m_RadarDataHead->PerformanceInfo.VelocityP = (unsigned char)(m_RadarHead->cutconfig[i_cut].ProcessMode);  //处理模式,1-PPP,2-FFT

        m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].PRF1 = m_RadarHead->cutconfig[i_cut].PRF1 * 10;   //脉冲重复频率1，对于Batch、双PRF和参差PRT模式，表示高PRF值。对于其它单PRF模式，表示唯一的PRF值。Unit:Hz
        m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].PRF2 = m_RadarHead->cutconfig[i_cut].PRF2 * 10;   //脉冲重复频率2，对Batch、双PRF和参差PRT模式，表示低PRF值。对其它单PRF模式，无效。Unit:Hz

        m_RadarDataHead->ObservationInfo.RHIA = m_RadarHead->cutconfig[i_cut].Azimuth * 100.0;    //方位角,RHI模式的方位角,Unit:°
        m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].SwpAngles = m_RadarHead->cutconfig[i_cut].Elevation * 100.0;  //仰角,PPI模式的俯仰角,Unit:°
        if (m_RadarHead->taskconfig.ScanType == 2)
        {
            m_RadarDataHead->ObservationInfo.RHIH = m_RadarHead->cutconfig[i_cut].StartAngle * 100.0; //起始角度，PPI扇扫的起始方位角，或RHI模式的高限仰角,Unit:°
            m_RadarDataHead->ObservationInfo.RHIL = m_RadarHead->cutconfig[i_cut].EndAngle * 100.0;   //结束角度，PPI扇扫的结束方位角，或RHI模式的低限仰角,Unit:°
        }
        m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].RecordNumber = 360.0 / m_RadarHead->cutconfig[i_cut].AngularResolution; //角度分辨率，径向数据的角度分辨率，仅用于PPI扫描模式,Unit:°
        m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].DPbinNumber = m_RadarHead->cutconfig[i_cut].ScanSpeed * 100.0;  //扫描速度，PPI扫描的方位转速，或RHI扫描的俯仰转速，Unit:Deg/sec,度/秒
        m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZBinWidth = m_RadarHead->cutconfig[i_cut].LogResolution * 10.0;  //强度分辨率，强度数据的距离分辨率,Unit:m
        m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].VBinWidth = m_RadarHead->cutconfig[i_cut].DopplerResolution * 10.0;   //多普勒分辨率,多普勒数据的距离分辨率，Unit:m
        m_RadarDataHead->ObservationInfo.ZStartBin = m_RadarHead->cutconfig[i_cut].StartRange / m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZBinWidth * 10.0; //起始距离，数据探测起始距离，Unit:m
        m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].ZbinNumber = m_RadarHead->cutconfig[i_cut].MaximumRange1 / m_RadarHead->cutconfig[i_cut].LogResolution;  //最大距离1,对应脉冲重复频率1的最大可探测距离，Unit:m
        m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].VbinNumber = m_RadarHead->cutconfig[i_cut].MaximumRange2 / m_RadarHead->cutconfig[i_cut].DopplerResolution;   //最大距离2,对应脉冲重复频率2的最大可探测距离，Unit:m
        m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].MaxV = m_RadarHead->cutconfig[i_cut].NyquistSpeed * 100.0;   //最大不模糊速度，理论最大不模糊速度,Unit:m/s
        m_RadarDataHead->ObservationInfo.LayerInfo[i_cut].DataForm = 91;
    }

    for (int i_radial = 0; i_radial < m_RadarData->radials.size(); i_radial++)
    {
        m_pLineData[i_radial].LineDataInfo.Elev = m_RadarData->radials.at(i_radial).radialheader.Elevation * 100;
        m_pLineData[i_radial].LineDataInfo.Az = m_RadarData->radials.at(i_radial).radialheader.Azimuth * 100;

        for (int i_moment = 0; i_moment < m_RadarData->radials.at(i_radial).momentblock.size(); i_moment ++)
        {
            switch (m_RadarData->radials.at(i_radial).momentblock.at(i_moment).momentheader.DataType)
            {
                case 1:  //dbt
                    memcpy(&m_pLineData[i_radial].UnZ[0], &m_RadarData->radials.at(i_radial).momentblock.at(i_moment).momentdata.at(0), \
                           m_RadarData->radials.at(i_radial).momentblock.at(i_moment).momentdata.size());
                    break;
                case 2:  //dbz
                    memcpy(&m_pLineData[i_radial].CorZ[0], &m_RadarData->radials.at(i_radial).momentblock.at(i_moment).momentdata.at(0), \
                           m_RadarData->radials.at(i_radial).momentblock.at(i_moment).momentdata.size());
                    break;
                case 3:  //v
                    memcpy(&m_pLineData[i_radial].V[0], &m_RadarData->radials.at(i_radial).momentblock.at(i_moment).momentdata.at(0), \
                           m_RadarData->radials.at(i_radial).momentblock.at(i_moment).momentdata.size());
                    break;
                case 4:  //w
                    memcpy(&m_pLineData[i_radial].W[0], &m_RadarData->radials.at(i_radial).momentblock.at(i_moment).momentdata.at(0), \
                           m_RadarData->radials.at(i_radial).momentblock.at(i_moment).momentdata.size());
                    break;
                case 7:  //zdr
                    memcpy(&m_pLineData[i_radial].ZDR[0], &m_RadarData->radials.at(i_radial).momentblock.at(i_moment).momentdata.at(0), \
                           m_RadarData->radials.at(i_radial).momentblock.at(i_moment).momentdata.size());
                    break;
                case 8:  //ldr
                    memcpy(&m_pLineData[i_radial].LDR[0], &m_RadarData->radials.at(i_radial).momentblock.at(i_moment).momentdata.at(0), \
                           m_RadarData->radials.at(i_radial).momentblock.at(i_moment).momentdata.size());
                    break;
                case 9:  //cc
                    memcpy(&m_pLineData[i_radial].ROHV[0], &m_RadarData->radials.at(i_radial).momentblock.at(i_moment).momentdata.at(0), \
                           m_RadarData->radials.at(i_radial).momentblock.at(i_moment).momentdata.size());
                    break;
                case 11: //kdp
                    memcpy(&m_pLineData[i_radial].KDP[0], &m_RadarData->radials.at(i_radial).momentblock.at(i_moment).momentdata.at(0), \
                           m_RadarData->radials.at(i_radial).momentblock.at(i_moment).momentdata.size());
                    break;
                default:
                    break;

            }
        }
    }

    return 0;
}

int CNrietFileIO::ConvertFMTtoFakePhasedArray()
{
    WRADRAWDATA i_RadarData_temp = *m_RadarData;

    m_RadarData->commonBlock.taskconfig.CutNumber *= 5;
    m_RadarData->commonBlock.cutconfig.resize(m_RadarData->commonBlock.cutconfig.size() * 5);
    m_RadarData->radials.reserve(m_RadarData->radials.size() * 5);
    m_RadarData->radials.clear();

    // 记录每一层扫描径向开始和结束的位置
    vector<short> ElRadialNum, ElRadialIndex;
    ElRadialNum.resize(i_RadarData_temp.commonBlock.cutconfig.size());
    ElRadialIndex.resize(i_RadarData_temp.commonBlock.cutconfig.size());
    int ElIndex = 0;
    for (int NoRadial = 0; NoRadial < i_RadarData_temp.radials.size(); NoRadial++)
    {
        if (i_RadarData_temp.radials[NoRadial].radialheader.RadialState == 0 || i_RadarData_temp.radials[NoRadial].radialheader.RadialState == 3)
        {
            ElRadialIndex.at(ElIndex) = NoRadial;
        }
        else if (i_RadarData_temp.radials[NoRadial].radialheader.RadialState == 2 || i_RadarData_temp.radials[NoRadial].radialheader.RadialState == 4)
        {
            ElRadialNum.at(ElIndex) = NoRadial - ElRadialIndex.at(ElIndex) + 1;
            ElIndex++;
        }
    }

    for (int i_radial = 0; i_radial < i_RadarData_temp.radials.size(); i_radial++)
    {
        int scale;
        if (i_RadarData_temp.commonBlock.cutconfig.at(i_RadarData_temp.radials.at(i_radial).radialheader.ElevationNumber - 1).MaximumRange1 > 300000)
        {
            scale = 2;
        }
        else
        {
            scale = 4;
        }

        for (int i_moment = 0; i_moment < i_RadarData_temp.radials.at(i_radial).momentblock.size(); i_moment++)
        {
            vector<unsigned char> temp;
            temp.resize(i_RadarData_temp.radials.at(i_radial).momentblock.at(i_moment).momentdata.size());
            memcpy(&temp.at(0), &i_RadarData_temp.radials.at(i_radial).momentblock.at(i_moment).momentdata.at(0), temp.size());
            i_RadarData_temp.radials.at(i_radial).momentblock.at(i_moment).momentdata.resize(i_RadarData_temp.radials.at(i_radial).momentblock.at(i_moment).momentdata.size()*scale);
            for (int i_gate = 0; i_gate < scale - 1; i_gate++)
            {
                *(unsigned char *)&i_RadarData_temp.radials.at(i_radial).momentblock.at(i_moment).momentdata.at(i_gate) = 0;
            }
            for (int i_gate = scale - 1; i_gate < i_RadarData_temp.radials.at(i_radial).momentblock.at(i_moment).momentdata.size(); i_gate++)
            {
                if (i_gate % scale == scale - 1)
                {
                    *(unsigned char *)&i_RadarData_temp.radials.at(i_radial).momentblock.at(i_moment).momentdata.at(i_gate) = temp.at(i_gate / scale);
                }
                else
                {
                    if (temp.at(i_gate / scale - 1) && temp.at(i_gate / scale))
                    {
                        *(unsigned char *)&i_RadarData_temp.radials.at(i_radial).momentblock.at(i_moment).momentdata.at(i_gate) \
                                = (temp.at(i_gate / scale - 1) * (scale - 1 - i_gate % scale) + temp.at(i_gate / scale) * (i_gate % scale + 1)) / scale;
                    }
                    else
                    {
                        *(unsigned char *)&i_RadarData_temp.radials.at(i_radial).momentblock.at(i_moment).momentdata.at(i_gate) = 0;
                    }
                }
            }
        }

        i_RadarData_temp.radials.at(i_radial).radialheader.LengthOfData = (i_RadarData_temp.radials.at(i_radial).momentblock.front().momentdata.size() + sizeof(MOMENTHEADER)) * i_RadarData_temp.radials.at(i_radial).radialheader.MomentNumber + sizeof(RADIALHEADER);
    }
    int RadialIndex = 0;
    int cut_index_org = 0;
    for (int i_cut = 0; i_cut < m_RadarData->commonBlock.cutconfig.size(); i_cut++)
    {
        if (i_cut / 5 < 4)
        {
            cut_index_org = i_cut / 10 * 2 + i_cut % 2;
            m_RadarData->commonBlock.cutconfig.at(i_cut) = i_RadarData_temp.commonBlock.cutconfig.at(cut_index_org);
            m_RadarData->commonBlock.cutconfig.at(i_cut).Elevation \
                                              = i_RadarData_temp.commonBlock.cutconfig.at(cut_index_org).Elevation + 0.1 * (i_cut - (i_cut / 10 * 10 + i_cut % 2));
        }
        else if (i_cut / 5 != i_RadarData_temp.commonBlock.cutconfig.size() - 1)
        {
            cut_index_org = i_cut / 5;
            m_RadarData->commonBlock.cutconfig.at(i_cut) = i_RadarData_temp.commonBlock.cutconfig.at(cut_index_org);

            m_RadarData->commonBlock.cutconfig.at(i_cut).Elevation \
                                              = (i_RadarData_temp.commonBlock.cutconfig.at(cut_index_org + 1).Elevation * (i_cut - i_cut / 5 * 5)  \
                                                 + i_RadarData_temp.commonBlock.cutconfig.at(cut_index_org).Elevation * ((i_cut / 5 + 1) * 5 - i_cut)) / 5;
        }
        else
        {
            cut_index_org = i_cut / 5;
            m_RadarData->commonBlock.cutconfig.at(i_cut) = i_RadarData_temp.commonBlock.cutconfig.at(cut_index_org);
            m_RadarData->commonBlock.cutconfig.at(i_cut).Elevation = i_RadarData_temp.commonBlock.cutconfig.at(cut_index_org).Elevation + (i_cut - i_cut / 5 * 5);
        }
        m_RadarData->radials.insert(m_RadarData->radials.begin() + RadialIndex, i_RadarData_temp.radials.begin() + ElRadialIndex.at(cut_index_org), \
                                    i_RadarData_temp.radials.begin() + ElRadialIndex.at(cut_index_org) + ElRadialNum.at(cut_index_org));
        m_RadarData->radials.at(RadialIndex).radialheader.RadialState = 0;
        m_RadarData->radials.back().radialheader.RadialState = 2;
        for (int i_radial = RadialIndex; i_radial < m_RadarData->radials.size(); i_radial++)
        {
            m_RadarData->radials.at(i_radial).radialheader.Elevation = m_RadarData->commonBlock.cutconfig.at(i_cut).Elevation;
            m_RadarData->radials.at(i_radial).radialheader.SequenceNumber = i_radial + 1;
            m_RadarData->radials.at(i_radial).radialheader.ElevationNumber = i_cut + 1;

        }
        RadialIndex += ElRadialNum.at(cut_index_org);
    }

    m_RadarData->radials.front().radialheader.RadialState = 3;
    m_RadarData->radials.back().radialheader.RadialState = 4;

    return 0;
}

time_t CNrietFileIO::time_convert(int year, int month, int day, int hour, int minute, int second)
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

int CNrietFileIO::FreeBlock()
{
    return 0;
}

int CNrietFileIO::FreeData()
{
    if (m_RadarDataHead != nullptr)
    {
        delete m_RadarDataHead;
    }
    if (m_pLineData != nullptr)
    {
        delete [] m_pLineData;
    }
    if (m_RadarData != nullptr)
    {
        delete m_RadarData;
    }
    m_RadarDataHead = nullptr;      // 雷达数据头
    m_pLineData = nullptr;      // 径向数据指针
    m_RadarData = nullptr;
    m_RadarHead = nullptr;     //  标准格式雷达数据头

    return 0;
}

void *CNrietFileIO::PutHeadPoint()
{
    void *head;
    head = (void *)m_RadarDataHead;
    return head;
}

void *CNrietFileIO::PutDataPoint()
{
    void *buffer;
    buffer = (void *)m_pLineData;
    return buffer;
}

void *CNrietFileIO::PutRadarRawData()
{
    void *buffer;
    buffer = (void *)m_RadarData;
    return buffer;
}
