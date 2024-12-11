#include "lib_ppis.h"

CNrietAlogrithm *GetAlgoInstance()
{
    return (new CAlgoPPIS());
}

int CAlgoPPIS::Init()
{
    cout << "Algorithm CAlgoPPIS inited" << endl;
    return 0;
}

int CAlgoPPIS::Uninit()
{
    cout << "Algorithm CAlgoPPIS Uninited" << endl;
    return 0;
}

int CAlgoPPIS::LoadStdCommonBlock(void *head)
{
    return 0;
}

int CAlgoPPIS::LoadStdRadailBlock(void *radial)
{
    return 0;
}

int CAlgoPPIS::SetDebugLevel(int temp)
{
    m_DebugLevel = temp;
    return 0;
}

void CAlgoPPIS::set_time_str()
{
    time_t now = time(nullptr);
    strftime(time_str, sizeof(time_str), "-- %m/%d/%Y %H:%M:%S ", localtime(&now));
}

int CAlgoPPIS::LoadStdData(void *Radardata)
{
    m_RadarData_org = (WRADRAWDATA *)Radardata;
    m_LayerNum = m_RadarData_org->commonBlock.taskconfig.CutNumber;
    return 0;
}

int CAlgoPPIS::LoadParameters(void *temp)
{
    m_RadarProParameters_org = (WRADPROLIST_IN *)temp;
    m_ProNum = m_RadarProParameters_org->size();
    for (int i_ProNum = 0; i_ProNum < m_ProNum; i_ProNum++)
    {
        if (m_RadarProParameters_org->at(i_ProNum).productheader.productheader.ProductType != PTYPE_PPI)
        {
            if (m_DebugLevel <= 0)
            {
                set_time_str();
                cout << time_str;
                cout << "Algo_PPIS::";
                cout << "Can only make PPI pro, Exit! " << endl;
            }
            return -1;
            //            m_RadarProParameters_org->erase(m_RadarProParameters_org->begin()+i_ProNum);
            //            i_ProNum--;
            //            m_ProNum--;
        }
    }

    if (m_ProNum <= 0)
    {
        if (m_DebugLevel <= 0)
        {
            set_time_str();
            cout << time_str;
            cout << "Algo_PPIS::";
            cout << "Can not load valid product paras, Exit!" << endl;
        }
        return -1;
    }

    return 0;
}

int CAlgoPPIS::MakeProduct()
{

    if (m_RadarData_org == nullptr || m_RadarData_org->commonBlock.taskconfig.ScanType > 1)//非体扫和PPI不处理
    {
        return -1;
    }

    GetRadialNumOfEl();                    //确定每层的径向数
    GetRadialIndexOfEl();                  //确定每层的第一根径向数据序号
    SetProOutHead();

    MakePPIPro();

    return 0;
}

int CAlgoPPIS::GetRadialNumOfEl()
{
    int ElIndex = 1;
    int LayerRadialNum = 0;
    ElRadialNum.resize(m_LayerNum);
    for (int NoRadial = 0; NoRadial < m_RadarData_org->radials.size(); NoRadial++)
    {
        if (m_RadarData_org->radials[NoRadial].radialheader.ElevationNumber == ElIndex)
        {
            LayerRadialNum++;
        }
        else
        {
            ElRadialNum[ElIndex - 1] = LayerRadialNum;
            ElIndex++;
            LayerRadialNum = 1;
            //            continue;
        }
    }
    ElRadialNum[ElIndex - 1] = LayerRadialNum;
    return 0;
}

int CAlgoPPIS::GetRadialIndexOfEl()
{
    int RadialIndex = 0;
    ElRadialIndex.resize(m_LayerNum);
    for (int i = 0; i < m_LayerNum; i++)
    {
        if (i == 0)
        {
            RadialIndex = 0;
        }
        else
        {
            RadialIndex = RadialIndex + ElRadialNum[i - 1];
        }
        ElRadialIndex[i] = RadialIndex;
    }
    return 0;
}

int CAlgoPPIS::SetProOutHead()
{
    time_t now = time(nullptr);

    try
    {
        m_RadarPro_out = new WRADPROLIST_OUT();
    }
    catch (bad_alloc)
    {
        return -1;
    }
//    m_RadarPro_out->reserve(m_ProNum);
    m_RadarPro_out->resize(m_ProNum);

    for (int i_ProNum = 0; i_ProNum < m_ProNum; i_ProNum++)
    {
        if (m_RadarProParameters_org->at(i_ProNum).productheader.productheader.ProductType == PTYPE_PPI)
        {
            m_RadarPro_out->at(i_ProNum).commonBlock = m_RadarData_org->commonBlock;
            m_RadarPro_out->at(i_ProNum).commonBlockPAR = m_RadarData_org->commonBlockPAR;
            m_RadarPro_out->at(i_ProNum).commonBlock.genericheader.GenericType = 2;
            m_RadarPro_out->at(i_ProNum).commonBlock.genericheader.ProductType = PTYPE_PPI;

            m_RadarPro_out->at(i_ProNum).productheader = m_RadarProParameters_org->at(i_ProNum).productheader;

            //            memset(m_RadarPro_out->at(i_ProNum).productheader.productheader.ProductName, 0x00, sizeof(m_RadarPro_out->at(i_ProNum).productheader.productheader.ProductName)/sizeof(m_RadarPro_out->at(i_ProNum).productheader.productheader.ProductName[0]));
            //            switch (m_RadarPro_out->at(i_ProNum).productheader.productheader.DataType1) {

            //            default:
            string productName = "PPI";
            strncpy(m_RadarPro_out->at(i_ProNum).productheader.productheader.ProductName, productName.c_str(), sizeof(m_RadarPro_out->at(i_ProNum).productheader.productheader.ProductName)); //productName.length());
            //            }

            m_RadarPro_out->at(i_ProNum).productheader.productheader.ProductGennerationTime = (int)now;
            m_RadarPro_out->at(i_ProNum).productheader.productheader.ProductType = PTYPE_PPI;
            m_RadarPro_out->at(i_ProNum).productheader.productheader.ScanStartTime = m_RadarData_org->commonBlock.taskconfig.ScanStartTime;
            m_RadarPro_out->at(i_ProNum).productheader.productheader.DataStartTime = m_RadarData_org->radials.front().radialheader.Seconds;
            m_RadarPro_out->at(i_ProNum).productheader.productheader.DataEndTime = m_RadarData_org->radials.back().radialheader.Seconds;
            m_RadarPro_out->at(i_ProNum).productheader.productheader.ProjectionType = 2;
            //m_RadarPro_out->at(i_ProNum).productheader.productheader.DataType1 = 0;
            m_RadarPro_out->at(i_ProNum).productheader.productheader.DataType2 = 0;
        }
    }
    return 0;
}

int CAlgoPPIS::MakePPIPro()
{
    for (int i_ProNum = 0; i_ProNum < m_ProNum; i_ProNum++)
    {
        if (m_RadarPro_out->at(i_ProNum).commonBlock.genericheader.ProductType == PTYPE_PPI)
        {
            int b_found = 0;
            for (int i_cut = 0; i_cut < m_RadarData_org->commonBlock.cutconfig.size(); i_cut++)
            {
                if (b_found)
                {
                    break;
                }
                if (m_RadarPro_out->at(i_ProNum).productheader.productdependentparameter.hclparameter.Elevation == m_RadarData_org->commonBlock.cutconfig.at(i_cut).Elevation)
                {
                    for (int i_moment = 0; i_moment < m_RadarData_org->radials.at(ElRadialIndex.at(i_cut)).momentblock.size(); i_moment++)
                    {
                        if (b_found)
                        {
                            break;
                        }
                        if (m_RadarPro_out->at(i_ProNum).productheader.productheader.DataType1 == m_RadarData_org->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(i_moment).momentheader.DataType)
                        {
                            RADIALFORMAT data_temp;
                            data_temp.RadialHeader.DataType = m_RadarPro_out->at(i_ProNum).productheader.productheader.DataType1;
                            data_temp.RadialHeader.Scale = m_RadarData_org->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(i_moment).momentheader.Scale;
                            data_temp.RadialHeader.Offset = m_RadarData_org->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(i_moment).momentheader.Offset;
                            data_temp.RadialHeader.BinLength  = m_RadarData_org->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(i_moment).momentheader.BinLength;
                            if (data_temp.RadialHeader.DataType == 3 || data_temp.RadialHeader.DataType == 4)
                            {
                                data_temp.RadialHeader.Resolution = m_RadarData_org->commonBlock.cutconfig.at(i_cut).DopplerResolution;
                            }
                            else
                            {
                                data_temp.RadialHeader.Resolution = m_RadarData_org->commonBlock.cutconfig.at(i_cut).LogResolution;
                            }
                            data_temp.RadialHeader.StartRange = 0;
                            data_temp.RadialHeader.MaxRange = data_temp.RadialHeader.Resolution \
                                                              * m_RadarData_org->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(i_moment).momentdata.size() \
                                                              / data_temp.RadialHeader.BinLength;
                            data_temp.RadialHeader.NumOfRadials = ElRadialNum.at(i_cut);
                            data_temp.RadialHeader.MaxValue = PREFILLVALUE_INT;
                            data_temp.RadialHeader.MinValue = PREFILLVALUE_INT;
                            data_temp.RadialHeader.AzOfMaxValue = PREFILLVALUE_FLOAT;
                            data_temp.RadialHeader.AzOfMinValue = PREFILLVALUE_INT;
                            data_temp.RadialHeader.RangeOfMaxValue = PREFILLVALUE_INT;
                            data_temp.RadialHeader.RangeOfMinValue = PREFILLVALUE_FLOAT;
                            data_temp.RadialData.resize(data_temp.RadialHeader.NumOfRadials);
                            for (int i_radial = 0; i_radial < data_temp.RadialHeader.NumOfRadials; i_radial++)
                            {
                                data_temp.RadialData.at(i_radial).RadialDataHead.StartAngle = m_RadarData_org->radials.at(ElRadialIndex.at(i_cut) + i_radial).radialheader.Azimuth;
                                data_temp.RadialData.at(i_radial).RadialDataHead.AnglularWidth = m_RadarData_org->commonBlock.cutconfig.at(i_cut).AngularResolution;
                                data_temp.RadialData.at(i_radial).RadialDataHead.NumOfBins = m_RadarData_org->radials.at(ElRadialIndex.at(i_cut) + i_radial).momentblock.at(i_moment).momentdata.size() \
                                                    / data_temp.RadialHeader.BinLength;
                                data_temp.RadialData.at(i_radial).RadialDataData.Data.resize(m_RadarData_org->radials.at(ElRadialIndex.at(i_cut) + i_radial).momentblock.at(i_moment).momentdata.size());
                                data_temp.RadialData.at(i_radial).RadialDataData.Data = m_RadarData_org->radials.at(ElRadialIndex.at(i_cut) + i_radial).momentblock.at(i_moment).momentdata;
                            }

                            int i_shift = 0;
                            int RadialHeadLength = sizeof(data_temp.RadialHeader);
                            int RadialDataHeadLength = sizeof(data_temp.RadialData[0].RadialDataHead);
                            int RadialDataDataLength = data_temp.RadialData[0].RadialDataData.Data.size();
                            m_RadarPro_out->at(i_ProNum).dataBlock.resize(RadialHeadLength + data_temp.RadialHeader.NumOfRadials * (RadialDataHeadLength + RadialDataDataLength));
                            memcpy(&m_RadarPro_out->at(i_ProNum).dataBlock.at(i_shift), &(data_temp.RadialHeader), RadialHeadLength);
                            i_shift += RadialHeadLength;
                            for (int i_radial = 0; i_radial < data_temp.RadialHeader.NumOfRadials; i_radial++)
                            {
                                memcpy(&m_RadarPro_out->at(i_ProNum).dataBlock.at(i_shift), &(data_temp.RadialData[i_radial].RadialDataHead), RadialDataHeadLength);
                                i_shift += RadialDataHeadLength;
                                memcpy(&m_RadarPro_out->at(i_ProNum).dataBlock.at(i_shift), &(data_temp.RadialData[i_radial].RadialDataData.Data[0]), RadialDataDataLength);
                                i_shift += RadialDataDataLength;
//                                if (m_RadarPro_out->at(i_ProNum).productheader.productheader.DataType1 == 1)
//                                {
//                                    for (int i = 0; i < data_temp.RadialData[i_radial].RadialDataData.Data.size(); ++i)
//                                    {
//                                        cout << data_temp.RadialData[i_radial].RadialDataData.Data.at(i) << " ";
//                                    }
//                                }
                            }
                            b_found = 1;

                        }
                    }
                }
            }
        }
    }

    if (m_DebugLevel <= 0)
    {
        set_time_str();
        cout << time_str;
        cout << "Algo_PPI_S::" ;
        cout << "Time of PPI is " << m_RadarPro_out->at(0).productheader.productheader.DataEndTime << endl;
    }
    return 0;
}

void *CAlgoPPIS::GetProduct()
{
    void *temp;
    temp = m_RadarPro_out;
    return temp;
}

int CAlgoPPIS::FreeData()
{
    if (m_RadarPro_out)
    {
        delete m_RadarPro_out;
    }
    m_RadarPro_out = nullptr;


    return 0;
}
