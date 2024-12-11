#include "lib_qc.h"
#include "algorithm"

bool cmpVOL(const RADIAL &a, const RADIAL &b)
{
    if (a.radialheader.ElevationNumber == b.radialheader.ElevationNumber)
    {
        return a.radialheader.Azimuth < b.radialheader.Azimuth;
    }
    else
    {
        return a.radialheader.ElevationNumber < b.radialheader.ElevationNumber;
    }
}

bool cmpRHI(const RADIAL &a, const RADIAL &b)
{
    return a.radialheader.Elevation < b.radialheader.Elevation;
}

bool cmpDateType(const MOMENTBLOCK &a, const MOMENTBLOCK &b)
{
    return a.momentheader.DataType < b.momentheader.DataType;
}

CNrietAlogrithm *GetAlgoInstance()
{
    return (new CAlgoQC());
}

int CAlgoQC::Init()
{
    //    cout << "Algorithm QC inited" <<endl;
    return 0;
}

int CAlgoQC::Uninit()
{
    //    cout << "Algorithm QC Uninited" <<endl;
    return 0;
}

int CAlgoQC::LoadParameters(void *temp)
{
    QCflag.resize(2);
    QCflag[0] = 1;
    QCflag[1] = 1;
    std::vector<QCParams> *params = (std::vector<QCParams> *)temp;
    for (int i = 0; i < params->size(); i++)
    {
        if (strcmp(params->at(i).FuncName, "QCFLAG") == 0)
        {
            if (params->at(i).Type.size() == 2)
            {
                QCflag[0] = (short)params->at(i).Type[0];
                QCflag[1] = (short)params->at(i).Type[1];
            }
            if (!(QCflag.at(0) || QCflag.at(1)))
            {
                return -1;
            }
        }

        if (strcmp(params->at(i).FuncName, "CalculateKDP") == 0)
        {
            m_params_calculateKDP = params->at(i);
        }

        if (strcmp(params->at(i).FuncName, "Zdr_PHDP_Correct") == 0)
        {
            m_params_Zdr_PHDP_Correct = params->at(i);
        }

        if (strcmp(params->at(i).FuncName, "UnflodVel_phase_unwrapping") == 0)
        {
            m_params_UnflodVel = params->at(i);
        }

        if (strcmp(params->at(i).FuncName, "AttenuationCorrection") == 0)
        {
            m_params_AttenuationCorrection = params->at(i);
        }
    }

    return 0;
}

int CAlgoQC::LoadStdCommonBlock(void *head)
{
    return 0;
}

int CAlgoQC::LoadStdRadailBlock(void *radial)
{
    return 0;
}

int CAlgoQC::LoadStdData(void *temp)
{
    m_radardata_org = (WRADRAWDATA *)temp;
    if (m_radardata_out_list)
    {
        vector<WRADRAWDATA>().swap(*m_radardata_out_list);
        delete m_radardata_out_list;
        m_radardata_out_list = nullptr;
    }

    m_radardata_out_list = new vector<WRADRAWDATA>;

    if (m_radardata_org->radials.size() == 1)
    {
        m_single_radial_mode = true;
        float elev = m_radardata_org->radials.front().radialheader.Elevation;
        for (int i_cut = 0; i_cut < m_radardata_org->commonBlock.cutconfig.size(); i_cut++)
        {
            // 计算浮点数的绝对值
            if (fabs(m_radardata_org->commonBlock.cutconfig.at(i_cut).Elevation - elev) > 0.1)
            {
                m_radardata_org->commonBlock.cutconfig.erase(m_radardata_org->commonBlock.cutconfig.begin() + i_cut);
                i_cut--;
            }
        }
        if (m_radardata_org->commonBlock.cutconfig.size() != 1)
        {
            return -1;
        }
    }
    else
    {
        m_single_radial_mode = false;
    }

    if (m_single_radial_mode)
    {
        m_radardata_out_list->push_back(*m_radardata_org);
        for (int i_cut = 0; i_cut < m_radardata_out_list->back().commonBlock.cutconfig.size(); i_cut++)
        {
            m_radardata_out_list->back().commonBlock.cutconfig.at(i_cut).dBTMask = 1;
            m_radardata_out_list->back().commonBlock.cutconfig.at(i_cut).dBZMask = 1;
            m_radardata_out_list->back().commonBlock.cutconfig.at(i_cut).VelocityMask = 1;
            m_radardata_out_list->back().commonBlock.cutconfig.at(i_cut).SpectrumWidthMask = 1;
            m_radardata_out_list->back().commonBlock.cutconfig.at(i_cut).DPMask = 1;
        }
    }
    else
    {
        if (QCflag.at(0) == 1)
        {
            m_radardata_out_list->push_back(*m_radardata_org);
            for (int i_cut = 0; i_cut < m_radardata_out_list->back().commonBlock.cutconfig.size(); i_cut++)
            {
                m_radardata_out_list->back().commonBlock.cutconfig.at(i_cut).dBTMask = 0;
                m_radardata_out_list->back().commonBlock.cutconfig.at(i_cut).dBZMask = 0;
                m_radardata_out_list->back().commonBlock.cutconfig.at(i_cut).VelocityMask = 0;
                m_radardata_out_list->back().commonBlock.cutconfig.at(i_cut).SpectrumWidthMask = 0;
                m_radardata_out_list->back().commonBlock.cutconfig.at(i_cut).DPMask = 0;
            }
        }
        if (QCflag.at(1) == 1)
        {
            m_radardata_out_list->push_back(*m_radardata_org);
            for (int i_cut = 0; i_cut < m_radardata_out_list->back().commonBlock.cutconfig.size(); i_cut++)
            {
                m_radardata_out_list->back().commonBlock.cutconfig.at(i_cut).dBTMask = 1;
                m_radardata_out_list->back().commonBlock.cutconfig.at(i_cut).dBZMask = 1;
                m_radardata_out_list->back().commonBlock.cutconfig.at(i_cut).VelocityMask = 1;
                m_radardata_out_list->back().commonBlock.cutconfig.at(i_cut).SpectrumWidthMask = 1;
                m_radardata_out_list->back().commonBlock.cutconfig.at(i_cut).DPMask = 1;
            }
        }
        //    cout <<12<<endl;
        //    *m_radardata_out = *m_radardata_org;

        m_LayerNum = m_radardata_out_list->at(0).commonBlock.cutconfig.size();
        ElRadialNum.resize(m_radardata_out_list->at(0).commonBlock.cutconfig.size());
        ElRadialIndex.resize(m_radardata_out_list->at(0).commonBlock.cutconfig.size());
    }
    //    cout <<13<<endl;
    //    m_radardata_out->commonBlock.taskconfig.ZDRCalibration = 32;
    //    m_radardata_out->commonBlock.taskconfig.PHIDPCalibration = 692;
    //    m_radardata_out->commonBlock.taskconfig.ZDRCalibrationInside = 32;
    //    m_radardata_out->commonBlock.taskconfig.PHIDPCalibrationInside = 337;
    //    m_radardata_out->commonBlock.taskconfig.BlindBinNum = 106;
    return 0;
}

int CAlgoQC::SetDebugLevel(int temp)
{
    m_DebugLevel = temp;
    return 0;
}

int CAlgoQC::MakeProduct()
{
    int status = 0;

    // now 变量现在包含了从Epoch到当前时间的秒数
    time_t now = time(nullptr);
    time_t past;

    if (m_single_radial_mode)
    {
        GetRadarParameters();
        status = Zdr_PHDP_Correct();//Phdp及Zdr订正

        if (m_DebugLevel <= 0)
        {
            now = time(nullptr);
            set_time_str();
            cout << time_str;
            cout << " Algo_QC:: ";
            cout << "Zdr_PHDP_Correct: ";
            cout << "Status: " << status << endl;
        }
        if (status)
        {
            return status;
        }

        status = CalculateKDP();//最小二乘法计算KDP

        if (m_DebugLevel <= 0)
        {
            now = time(nullptr);
            set_time_str();
            cout << time_str;
            cout << " Algo_QC:: ";
            cout << "CalculateKDP: ";
            cout << "Status: " << status << endl;
        }
        if (status)
        {
            return status;
        }

        status = AttenuationCorrection();//衰减订正e

        if (m_DebugLevel <= 0)
        {
            now = time(nullptr);
            set_time_str();
            cout << time_str;
            cout << " Algo_QC:: ";
            cout << "AttenuationCorrection: ";
            cout << "Status: " << status << endl;
        }
        if (status)
        {
            return status;
        }
    }
    else
    {
        for (int ipro = 0; ipro < m_radardata_out_list->size(); ipro++)
        {
            m_radardata_out = &m_radardata_out_list->at(ipro);

            status = Sort_RadialData();
            if (m_DebugLevel <= 0)
            {
                now = time(nullptr);
                set_time_str();
                cout << time_str;
                cout << " Algo_QC:: ";
                cout << "Sort_RadialData: ";
                cout << "Status: " << status << endl;
            }

            status = DeleteInvalidData();
            if (m_DebugLevel <= 0)
            {
                now = time(nullptr);
                set_time_str();
                cout << time_str;
                cout << " Algo_QC:: ";
                cout << "DeleteInvalidData: ";
                cout << "Status: " << status << endl;
            }
            if (status)
            {
                return status;
            }

            GetRadialNumOfEl();
            GetRadialIndexOfEl();
            GetRadarParameters();

            status = Normalize_Az();
            if (m_DebugLevel <= 0)
            {
                now = time(nullptr);
                set_time_str();
                cout << time_str;
                cout << " Algo_QC:: ";
                cout << "Normalize_Az: ";
                cout << "Status: " << status << endl;
            }
            if (status)
            {
                //return status;
            }



//            // merge start
//            GetRadialNumOfEl();
//            GetRadialIndexOfEl();
//            for (int i = 0; i < m_radardata_out->commonBlock.taskconfig.CutNumber; ++i)
//            {
//                for (int radialdel = i + 1; radialdel < m_radardata_out->commonBlock.taskconfig.CutNumber; ++radialdel)
//                {
//                    if (fabs(m_radardata_out->radials.at(ElRadialIndex.at(i)).radialheader.Elevation - m_radardata_out->radials.at(ElRadialIndex.at(radialdel)).radialheader.Elevation) < 0.01)
//                    {
//                        // taskconfig
//                        m_radardata_out->commonBlock.taskconfig.CutNumber -= 1;
//                        // cutconfig
//                        m_radardata_out->commonBlock.cutconfig.at(i).DopplerResolution = m_radardata_out->commonBlock.cutconfig.at(radialdel).DopplerResolution;
//                        m_radardata_out->commonBlock.cutconfig.at(i).NyquistSpeed = m_radardata_out->commonBlock.cutconfig.at(radialdel).NyquistSpeed;
//                        m_radardata_out->commonBlock.cutconfig.erase(m_radardata_out->commonBlock.cutconfig.begin() + radialdel);
//                        // radials
//                        int binnum1 = m_radardata_out->radials.at(ElRadialIndex.at(i)).momentblock.at(0).momentheader.Length / m_radardata_out->radials.at(ElRadialIndex.at(i)).momentblock.at(0).momentheader.BinLength;
//                        for (int j = 0; j < ElRadialNum.at(i); j++)
//                        {
//                            // radial
//                            vector<int> DateType_list;
//                            for (int k = 0; k < m_radardata_out->radials.at(ElRadialIndex.at(i) + j).momentblock.size(); ++k)
//                            {
//                                if (find(DateType_list.begin(), DateType_list.end(), m_radardata_out->radials.at(ElRadialIndex.at(i) + j).momentblock.at(k).momentheader.DataType) == DateType_list.end())
//                                {
//                                    DateType_list.push_back(m_radardata_out->radials.at(ElRadialIndex.at(i) + j).momentblock.at(k).momentheader.DataType);
//                                }
//                            }
//                            int Length2 = m_radardata_out->radials.at(ElRadialIndex.at(radialdel) + j).momentblock.at(0).momentheader.Length;
//                            int BinLength2 = m_radardata_out->radials.at(ElRadialIndex.at(radialdel) + j).momentblock.at(0).momentheader.BinLength;
//                            int binnum2 = Length2 / BinLength2;
//                            for (int k = 0; k < m_radardata_out->radials.at(ElRadialIndex.at(radialdel) + j).momentblock.size(); ++k)
//                            {
//                                if (find(DateType_list.begin(), DateType_list.end(), m_radardata_out->radials.at(ElRadialIndex.at(radialdel) + j).momentblock.at(k).momentheader.DataType) == DateType_list.end())
//                                {
//                                    // not exist
//                                    // momentblock
//                                    m_radardata_out->radials.at(ElRadialIndex.at(i) + j).momentblock.push_back(m_radardata_out->radials.at(ElRadialIndex.at(radialdel) + j).momentblock.at(k));
//                                    m_radardata_out->radials.at(ElRadialIndex.at(i) + j).momentblock.back().momentdata.resize(binnum1 * BinLength2, 0);
//                                    //// size
//                                    m_radardata_out->radials.at(ElRadialIndex.at(i) + j).momentblock.back().momentheader.Length = binnum1 * BinLength2;
//                                    int momentblock_size = binnum1 * BinLength2 + sizeof(m_radardata_out->radials.at(ElRadialIndex.at(i) + j).momentblock.back().momentheader);
//                                    // radialheader
//                                    m_radardata_out->radials.at(ElRadialIndex.at(i) + j).radialheader.MomentNumber += 1;
//                                    m_radardata_out->radials.at(ElRadialIndex.at(i) + j).radialheader.LengthOfData += momentblock_size;
//                                }
//                            }
//                        }
//                        // delete radials
//                        for (int m_radial = ElRadialIndex.at(radialdel); m_radial < m_radardata_out->radials.size(); ++m_radial)
//                        {
//                            m_radardata_out->radials.at(m_radial).radialheader.ElevationNumber -= 1;
//                        }
//                        m_radardata_out->radials.erase(m_radardata_out->radials.begin() + ElRadialIndex.at(radialdel), m_radardata_out->radials.begin() + ElRadialIndex.at(radialdel) + ElRadialNum.at(radialdel));
//                        m_LayerNum = m_radardata_out->commonBlock.cutconfig.size();
//                        GetRadialNumOfEl();
//                        GetRadialIndexOfEl();
//                    }
//                }
//            }
//            // sort
//            for (int i = 0; i < m_radardata_out->radials.size(); ++i)
//            {
//                sort(m_radardata_out->radials.at(i).momentblock.begin(), m_radardata_out->radials.at(i).momentblock.end(), cmpDateType);
//            }

//            // merge end

            // merge start
            GetRadialNumOfEl();
            GetRadialIndexOfEl();
            for (int i = 0; i < m_radardata_out->commonBlock.taskconfig.CutNumber - 1; ++i)
            {
                if (fabs(m_radardata_out->radials.at(ElRadialIndex.at(i)).radialheader.Elevation - m_radardata_out->radials.at(ElRadialIndex.at(i + 1)).radialheader.Elevation) < 0.2)
                {
                    if ((m_radardata_out->radials.at(ElRadialIndex.at(i + 1)).radialheader.MomentNumber == 2) || (m_radardata_out->radials.at(ElRadialIndex.at(i + 1)).radialheader.MomentNumber == 3))
                    {
                        // taskconfig
                        m_radardata_out->commonBlock.taskconfig.CutNumber -= 1;
                        // cutconfig
                        m_radardata_out->commonBlock.cutconfig.at(i).DopplerResolution = m_radardata_out->commonBlock.cutconfig.at(i + 1).DopplerResolution;
                        m_radardata_out->commonBlock.cutconfig.at(i).NyquistSpeed = m_radardata_out->commonBlock.cutconfig.at(i + 1).NyquistSpeed;
                        m_radardata_out->commonBlock.cutconfig.erase(m_radardata_out->commonBlock.cutconfig.begin() + i + 1);
                        // radials
                        int binnum1 = m_radardata_out->radials.at(ElRadialIndex.at(i)).momentblock.at(0).momentheader.Length / m_radardata_out->radials.at(ElRadialIndex.at(i)).momentblock.at(0).momentheader.BinLength;
                        for (int j = 0; j < ElRadialNum.at(i); j++)
                        {
                            // radial
                            vector<int> DateType_list;
                            for (int k = 0; k < m_radardata_out->radials.at(ElRadialIndex.at(i) + j).momentblock.size(); ++k)
                            {
                                if (find(DateType_list.begin(), DateType_list.end(), m_radardata_out->radials.at(ElRadialIndex.at(i) + j).momentblock.at(k).momentheader.DataType) == DateType_list.end())
                                {
                                    DateType_list.push_back(m_radardata_out->radials.at(ElRadialIndex.at(i) + j).momentblock.at(k).momentheader.DataType);
                                }
                            }
                            int Length2 = m_radardata_out->radials.at(ElRadialIndex.at(i + 1) + j).momentblock.at(0).momentheader.Length;
                            int BinLength2 = m_radardata_out->radials.at(ElRadialIndex.at(i + 1) + j).momentblock.at(0).momentheader.BinLength;
                            int binnum2 = Length2 / BinLength2;
                            for (int k = 0; k < m_radardata_out->radials.at(ElRadialIndex.at(i + 1) + j).momentblock.size(); ++k)
                            {
                                if (find(DateType_list.begin(), DateType_list.end(), m_radardata_out->radials.at(ElRadialIndex.at(i + 1) + j).momentblock.at(k).momentheader.DataType) == DateType_list.end())
                                {
                                    // not exist
                                    // momentblock
                                    m_radardata_out->radials.at(ElRadialIndex.at(i) + j).momentblock.push_back(m_radardata_out->radials.at(ElRadialIndex.at(i + 1) + j).momentblock.at(k));
                                    m_radardata_out->radials.at(ElRadialIndex.at(i) + j).momentblock.back().momentdata.resize(binnum1 * BinLength2, 0);
                                    //// size
                                    m_radardata_out->radials.at(ElRadialIndex.at(i) + j).momentblock.back().momentheader.Length = binnum1 * BinLength2;
                                    int momentblock_size = binnum1 * BinLength2 + sizeof(m_radardata_out->radials.at(ElRadialIndex.at(i) + j).momentblock.back().momentheader);
                                    // radialheader
                                    m_radardata_out->radials.at(ElRadialIndex.at(i) + j).radialheader.MomentNumber += 1;
                                    m_radardata_out->radials.at(ElRadialIndex.at(i) + j).radialheader.LengthOfData += momentblock_size;
                                }
                            }
                        }
                        // delete radials
                        for (int m_radial = ElRadialIndex.at(i + 1); m_radial < m_radardata_out->radials.size(); ++m_radial)
                        {
                            m_radardata_out->radials.at(m_radial).radialheader.ElevationNumber -= 1;
                        }
                        m_radardata_out->radials.erase(m_radardata_out->radials.begin() + ElRadialIndex.at(i + 1), m_radardata_out->radials.begin() + ElRadialIndex.at(i + 1) + ElRadialNum.at(i + 1));
                        m_LayerNum = m_radardata_out->commonBlock.cutconfig.size();
                        GetRadialNumOfEl();
                        GetRadialIndexOfEl();
                    }
                }
            }
            // sort
            for (int i = 0; i < m_radardata_out->radials.size(); ++i)
            {
                sort(m_radardata_out->radials.at(i).momentblock.begin(), m_radardata_out->radials.at(i).momentblock.end(), cmpDateType);
            }

            // merge end

            GetRadialNumOfEl();
            GetRadialIndexOfEl();
            GetRadarParameters();

            if (m_radardata_out->commonBlock.cutconfig.front().dBTMask == 0)
            {
                status = CalculateKDP();//最小二乘法计算KDP

                if (m_DebugLevel <= 0)
                {
                    now = time(nullptr);
                    set_time_str();
                    cout << time_str;
                    cout << " Algo_QC:: ";
                    cout << "CalculateKDP: ";
                    cout << "Status: " << status << endl;
                }
                if (status)
                {
                    //return status;
                }
                GetRadarParameters();
            }

            if (m_radardata_out->commonBlock.cutconfig.front().dBTMask == 1)
            {
                status = Zdr_PHDP_Correct();//Phdp及Zdr订正
                if (m_DebugLevel <= 0)
                {
                    now = time(nullptr);
                    set_time_str();
                    cout << time_str;
                    cout << " Algo_QC:: ";
                    cout << "Zdr_PHDP_Correct: ";
                    cout << "Status: " << status << endl;
                }
                if (status)
                {
                    //return status;
                }

                status = CalculateKDP();//最小二乘法计算KDP
                if (m_DebugLevel <= 0)
                {
                    now = time(nullptr);
                    set_time_str();
                    cout << time_str;
                    cout << " Algo_QC:: ";
                    cout << "CalculateKDP: ";
                    cout << "Status: " << status << endl;
                }
                if (status)
                {
                    //return status;
                }
                GetRadarParameters();

                status = AttenuationCorrection();//衰减订正e
                if (m_DebugLevel <= 0)
                {
                    now = time(nullptr);
                    set_time_str();
                    cout << time_str;
                    cout << " Algo_QC:: ";
                    cout << "AttenuationCorrection: ";
                    cout << "Status: " << status << endl;
                }
                if (status)
                {
                    //return status;
                }

                if (m_params_UnflodVel.Method == 0)
                {
                    status = UnfoldVel_shearb1s();
                }
                else
                {
                    status = UnflodVel_phase_unwrapping();
                }
                if (m_DebugLevel <= 0)
                {
                    now = time(nullptr);
                    set_time_str();
                    cout << time_str;
                    cout << " Algo_QC:: ";
                    cout << "UnfoldVel: ";
                    cout << "Status: " << status << endl;
                }
                if (status)
                {
                    //return status;
                }
            }
        }

        SmoothData_Dot = 3;                 //资料平滑点数
//        status = SmoothData(SmoothData_Dot);//资料平滑点数
//        if (m_DebugLevel <= 0){
//            now = time(nullptr);
//            set_time_str();
//            cout << time_str;
//            cout << " Algo_QC:: ";
//            cout << "SmoothData: ";
//            cout << "Status: "<< status << endl;
//        }
//        if (status) {
//            //return status;
//        }

        RadialSmooth_Dot = 5;                   //径向平滑点数
//        status = RadialSmooth(RadialSmooth_Dot);//资料平滑点数
//        if (m_DebugLevel <= 0){
//            now = time(nullptr);
//            set_time_str();
//            cout << time_str;
//            cout << " Algo_QC:: ";
//            cout << "RadialSmooth: ";
//            cout << "Status: "<< status << endl;
//        }
//        if (status) {
//            //return status;
//        }
    }

    return status;
}

void *CAlgoQC::GetProduct()
{
    return (void *)m_radardata_out_list;
}

int CAlgoQC::FreeData()
{
    if (m_radardata_out_list)
    {
        vector<WRADRAWDATA>().swap(*m_radardata_out_list);
        delete m_radardata_out_list;
        m_radardata_out_list = nullptr;
    }
    return 0;
}

void CAlgoQC::set_time_str()
{
    time_t now = time(nullptr);
    strftime(time_str, sizeof(time_str), "-- %m/%d/%Y %H:%M:%S ", localtime(&now));
    //    set_time_str();
    //    cout << time_str;
}

int CAlgoQC::GetRadarParameters()
{
    m_LayerNum = m_radardata_out->commonBlock.cutconfig.size();
    nRadialNum = ElRadialNum[0];

    m_AnglarResolution = m_radardata_out->commonBlock.cutconfig.front().AngularResolution;

    indexUnZH.resize(m_LayerNum);
    indexUnZH.assign(m_LayerNum, -1);
    indexV = indexUnZH;
    indexW = indexUnZH;
    indexZH = indexUnZH;
    indexZDR = indexUnZH;
    indexPHDP = indexUnZH;
    indexKDP = indexUnZH;
    indexSNR = indexUnZH;
    indexROHV = indexUnZH;

    nBinNumZ = indexUnZH;
    nBinNumV = indexUnZH;

    nBinWidthZ.resize(m_LayerNum);
    nBinWidthZ.assign(m_LayerNum, -1);
    nBinWidthV = nBinWidthZ;

    for (int icut = 0; icut < m_LayerNum; icut++)
    {
        for (int i = 0; i < m_radardata_out->radials.at(ElRadialIndex.at(icut)).radialheader.MomentNumber; i++)
        {
            int moment = m_radardata_out->radials.at(ElRadialIndex.at(icut)).radialheader.MomentNumber;
            if (m_radardata_out->radials.at(ElRadialIndex.at(icut)).momentblock.at(i).momentheader.DataType == 1)
            {
                // 滤波前反射率
                indexUnZH.at(icut) = i;
            }
            else if (m_radardata_out->radials.at(ElRadialIndex.at(icut)).momentblock.at(i).momentheader.DataType == 2)
            {
                // 滤波后反射率
                indexZH.at(icut) = i;
                nBinNumZ.at(icut) = m_radardata_out->radials.at(ElRadialIndex.at(icut)).momentblock.at(i).momentdata.size() / m_radardata_out->radials.at(ElRadialIndex.at(icut)).momentblock.at(i).momentheader.BinLength;
                nBinWidthZ.at(icut) = m_radardata_out->commonBlock.cutconfig.at(icut).LogResolution * 0.001;
            }
            else if (m_radardata_out->radials.at(ElRadialIndex.at(icut)).momentblock.at(i).momentheader.DataType == 7)
            {
                // 差分反射率
                indexZDR.at(icut) = i;
            }
            else if (m_radardata_out->radials.at(ElRadialIndex.at(icut)).momentblock.at(i).momentheader.DataType == 10)
            {
                // 差分相移
                indexPHDP.at(icut) = i;
            }
            else if (m_radardata_out->radials.at(ElRadialIndex.at(icut)).momentblock.at(i).momentheader.DataType == 3)
            {
                // 径向速度
                indexV.at(icut) = i;
                nBinNumV.at(icut) = m_radardata_out->radials.at(ElRadialIndex.at(icut)).momentblock.at(i).momentdata.size() / m_radardata_out->radials.at(ElRadialIndex.at(icut)).momentblock.at(i).momentheader.BinLength;
                nBinWidthV.at(icut) = m_radardata_out->commonBlock.cutconfig.at(icut).DopplerResolution * 0.001;
            }
            else if (m_radardata_out->radials.at(ElRadialIndex.at(icut)).momentblock.at(i).momentheader.DataType == 11)
            {
                // 差分相移率
                indexKDP.at(icut) = i;
            }
            else if (m_radardata_out->radials.at(ElRadialIndex.at(icut)).momentblock.at(i).momentheader.DataType == 4)
            {
                // 谱宽
                indexW.at(icut) = i;
            }
            else if (m_radardata_out->radials.at(ElRadialIndex.at(icut)).momentblock.at(i).momentheader.DataType == 16)
            {
                // 水平通道SNR
                indexSNR.at(icut) = i;
            }
            else if (m_radardata_out->radials.at(ElRadialIndex.at(icut)).momentblock.at(i).momentheader.DataType == 9)
            {
                // 协相关系数
                indexROHV.at(icut) = i;
            }
        }
    }

    nBinNum = m_radardata_out->radials.at(0).momentblock.at(0).momentheader.Length / m_radardata_out->radials.at(0).momentblock.at(0).momentheader.BinLength;
    nBinWidth = m_radardata_out->commonBlock.cutconfig.at(0).LogResolution * 0.001;

    if (m_DebugLevel <= 0)
    {
        set_time_str();
        cout << time_str;
        cout << " Algo_QC:: LogResolution";
        cout << m_radardata_out->commonBlock.cutconfig.at(0).LogResolution * 0.001 << endl;
    }

    UnZHindex = -1;
    Vindex = -1;
    ZHindex = -1;
    ZDRindex = -1;
    PHDPindex = -1;
    KDPindex = -1;
    Windex = -1;
    SNRindex = -1;
    ROHVindex = -1;

    for (int i = 0; i < m_radardata_out->radials.at(0).radialheader.MomentNumber; i++)
    {
        if (m_radardata_out->radials.at(0).momentblock.at(i).momentheader.DataType == 1)
        {
            UnZHindex = i;
        }
        else if (m_radardata_out->radials.at(0).momentblock.at(i).momentheader.DataType == 2)
        {
            ZHindex = i;
        }
        else if (m_radardata_out->radials.at(0).momentblock.at(i).momentheader.DataType == 7)
        {
            ZDRindex = i;
        }
        else if (m_radardata_out->radials.at(0).momentblock.at(i).momentheader.DataType == 10)
        {
            PHDPindex = i;
        }
        else if (m_radardata_out->radials.at(0).momentblock.at(i).momentheader.DataType == 3)
        {
            Vindex = i;
        }
        else if (m_radardata_out->radials.at(0).momentblock.at(i).momentheader.DataType == 11)
        {
            KDPindex = i;
        }
        else if (m_radardata_out->radials.at(0).momentblock.at(i).momentheader.DataType == 4)
        {
            Windex = i;
        }
        else if (m_radardata_out->radials.at(0).momentblock.at(i).momentheader.DataType == 16)
        {
            //            m_radardata_out->radials.at(0).momentblock.at(i).momentheader.DataType = 11;
            //            KDPindex = i;
            //            SNRindex = -1;
            SNRindex = i;
        }
        else if (m_radardata_out->radials.at(0).momentblock.at(i).momentheader.DataType == 9)
        {
            ROHVindex = i;
        }
    }

    if (m_DebugLevel <= 0)
    {
        cout << "UnZ = " << UnZHindex << endl;
        cout << "Vindex = " << Vindex << endl;
        cout << "ZHindex = " << ZHindex << endl;
        cout << "ZDRindex = " << ZDRindex << endl;
        cout << "PHDPindex = " << PHDPindex << endl;
        cout << "KDPindex = " << KDPindex << endl;
        cout << "Windex = " << Windex << endl;
        cout << "SNRindex = " << SNRindex << endl;
        cout << "ROHVindex = " << ROHVindex << endl;
    }
    return 0;
}

int CAlgoQC::DeleteInvalidData()
{
    int t_expire = m_radardata_out->commonBlock.taskconfig.ScanStartTime;
    if (m_DebugLevel <= 0)
    {
        set_time_str();
        cout << time_str;
        cout << " Algo_QC:: ";
        cout << "Expire time is " << t_expire << endl;
    }
    if (m_radardata_out->radials.size() > 0)
    {
        for (int i_radial = 0; i_radial < m_radardata_out->radials.size(); i_radial++)
        {
            if (m_radardata_out->radials.at(i_radial).radialheader.Seconds > m_radardata_out->commonBlock.taskconfig.ScanStartTime + 1800 \
                    || m_radardata_out->radials.at(i_radial).momentblock.size() == 0)
//            if (m_radardata_out->radials.at(i_radial).radialheader.Seconds < m_radardata_out->commonBlock.taskconfig.ScanStartTime - 100 \
//                    || m_radardata_out->radials.at(i_radial).radialheader.Seconds > m_radardata_out->commonBlock.taskconfig.ScanStartTime + 1800 \
//                    || m_radardata_out->radials.at(i_radial).radialheader.SpotBlank == 1 || m_radardata_out->radials.at(i_radial).momentblock.size() == 0)
            {
                auto itr = m_radardata_out->radials.begin() + i_radial;
                itr = m_radardata_out->radials.erase(itr);
                i_radial --;
            }
        }
    }

    m_LayerNum = m_radardata_out->commonBlock.cutconfig.size();
    GetRadialNumOfEl();
    GetRadialIndexOfEl();
    for (int i_cut = m_LayerNum - 1; i_cut >= 0; --i_cut)
    {
        if (ElRadialNum[i_cut] == 0)
        {
            m_radardata_out->commonBlock.cutconfig.erase(m_radardata_out->commonBlock.cutconfig.begin() + i_cut);
            for (int i_radial = ElRadialIndex[i_cut]; i_radial < m_radardata_out->radials.size(); ++i_radial)
            {
                m_radardata_out->radials[i_radial].radialheader.ElevationNumber--;
            }
        }
    }
    m_LayerNum = m_radardata_out->commonBlock.cutconfig.size();

    if (m_radardata_out->radials.size() < 50)
    {
        return -1;
    }

    return 0;
}

int CAlgoQC::Sort_RadialData()
{
//    int i_RadialNumSum = m_radardata_out->radials.size();

//    for (int i_Radial = 0; i_Radial < i_RadialNumSum; i_Radial++)
//    {
//        int i_Index = 0;
//        for (i_Index = i_Radial+1; i_Index < min(i_Radial + 50, i_RadialNumSum); i_Index++)
//        {
//            if(m_radardata_out->radials.at(i_Index).radialheader.SequenceNumber \
//                    < m_radardata_out->radials.at(i_Radial).radialheader.SequenceNumber){
//                RADIAL temp = m_radardata_out->radials.at(i_Radial);
//                m_radardata_out->radials.at(i_Radial) = m_radardata_out->radials.at(i_Index);
//                m_radardata_out->radials.at(i_Index) = temp;
//                break;
//            }
//        }
//    }

//    if (m_radardata_out->commonBlock.taskconfig.ScanType == 2 \
//            || m_radardata_out->commonBlock.taskconfig.ScanType == 3 \
//            || m_radardata_out->commonBlock.taskconfig.ScanType == 4 \
//            || m_radardata_out->commonBlock.taskconfig.ScanType == 5 \
//            || m_radardata_out->commonBlock.taskconfig.ScanType == 6)
//    {
//        return 0;
//    }
//    else if (m_radardata_out->commonBlock.taskconfig.ScanType == 0 \
//             || m_radardata_out->commonBlock.taskconfig.ScanType == 1 )
//    {
//        int i_start = 0;
//        int i_end = 0;
//        for (int i_cut = 0; i_cut < ElRadialIndex.size(); i_cut++)
//        {
//            i_start = ElRadialIndex.at(i_cut);
//            if (i_cut == ElRadialIndex.size()-1){
//                i_end = m_radardata_out->radials.size()-1;
//            }
//            else
//            {
//                i_end = ElRadialIndex.at(i_cut+1) -1;
//            }
//            Sort_Data_Iter(i_start,i_end);
//        }
//    }

    if (m_radardata_out->commonBlock.taskconfig.ScanType == 2)
    {
        sort(m_radardata_out->radials.begin(), m_radardata_out->radials.end(), cmpRHI);
    }
    else
    {
        sort(m_radardata_out->radials.begin(), m_radardata_out->radials.end(), cmpVOL);
    }
    return 0;
}

int CAlgoQC::Normalize_Az(WRADRAWDATA *radardata_in, WRADRAWDATA *radardata_out)
{
    if (radardata_out->commonBlock.taskconfig.ScanType != 0 \
            && radardata_out->commonBlock.taskconfig.ScanType != 1)
    {
        *radardata_out = *radardata_in;
        return -1;
    }

    *radardata_out = *radardata_in;
    int i_RadialNumSum = radardata_out->radials.size();

    for (int i_Radial = 0; i_Radial < i_RadialNumSum; i_Radial++)
    {
        int i_Index = 0;
        //        for (i_Index = i_Radial+1; i_Index < i_RadialNumSum; i_Index++)
        for (i_Index = i_Radial + 1; i_Index < min(i_Radial + 50, i_RadialNumSum); i_Index++)
        {
            if (radardata_out->radials.at(i_Index).radialheader.SequenceNumber \
                    < radardata_out->radials.at(i_Radial).radialheader.SequenceNumber)
            {
                RADIAL temp = radardata_out->radials.at(i_Radial);
                radardata_out->radials.at(i_Radial) = radardata_out->radials.at(i_Index);
                radardata_out->radials.at(i_Index) = temp;
                break;
            }
        }
    }

    int LayerNum = radardata_out->commonBlock.cutconfig.size();
    int ElIndex = 1;

    vector<short> i_ElRadialNum;
    vector<short> i_ElRadialIndex;
    i_ElRadialNum.resize(LayerNum);
    i_ElRadialIndex.resize(LayerNum);

    int LayerRadialNum = 0;
    if (LayerNum == 1)
    {
        i_ElRadialNum.at(0) = radardata_out->radials.size();
    }
    else
    {
        for (int NoRadial = 0; NoRadial < radardata_out->radials.size(); NoRadial++)
        {
            if (radardata_out->radials[NoRadial].radialheader.ElevationNumber == ElIndex)
            {
                LayerRadialNum++;
            }
            else
            {
                i_ElRadialNum[ElIndex - 1] = LayerRadialNum;
                ElIndex++;
                LayerRadialNum = 1;
                //            continue;
            }
        }
        i_ElRadialNum[ElIndex - 1] = LayerRadialNum;
    }

    int RadialIndex = 0;
    for (int i = 0; i < radardata_out->commonBlock.cutconfig.size(); i++)
    {
        if (i == 0)
        {
            RadialIndex = 0;
        }
        else
        {
            RadialIndex = RadialIndex + i_ElRadialNum[i - 1];
        }
        i_ElRadialIndex[i] = RadialIndex;
    }


    int i_start = 0;
    int i_end = 0;
    for (int i_cut = 0; i_cut < i_ElRadialIndex.size(); i_cut++)
    {
        i_start = i_ElRadialIndex.at(i_cut);
        if (i_cut == i_ElRadialIndex.size() - 1)
        {
            i_end = radardata_in->radials.size() - 1;
        }
        else
        {
            i_end = i_ElRadialIndex.at(i_cut + 1) - 1;
        }
        Sort_Data_Iter(i_start, i_end, radardata_out);
    }


    int i_CutStatus = 0;   //0:first cut of VTB, 1:middle cut of VTB,  2:last cut of VTB    3:single PPI scan    4:complete VTB
    if (radardata_out->commonBlock.cutconfig.size() == 1)
    {
        if (radardata_out->commonBlock.taskconfig.ScanType == 1)
        {
            i_CutStatus = 3;
        }
        else if (radardata_out->commonBlock.taskconfig.ScanType == 0)
        {
            if (radardata_out->radials.front().radialheader.ElevationNumber == 1)
            {
                i_CutStatus = 0;
            }
            else if (radardata_out->radials.back().radialheader.ElevationNumber == radardata_out->commonBlock.taskconfig.CutNumber)
            {
                i_CutStatus = 2;
            }
            else
            {
                i_CutStatus = 1;
            }
        }
    }
    else
    {
        if (radardata_out->commonBlock.taskconfig.ScanType == 0)
        {
            if (radardata_out->radials.front().radialheader.ElevationNumber == 1 \
                    && radardata_out->radials.back().radialheader.ElevationNumber == radardata_out->commonBlock.taskconfig.CutNumber)
            {
                i_CutStatus = 4;
            }
        }
        else
        {
            if (m_DebugLevel <= 3)
            {
                set_time_str();
                cout << time_str;
                cout << " Algo_QC:: ";
                cout << "Not supproted format!" << endl;
            }
            return -1;
        }

    }
    float i_dAz = radardata_out->commonBlock.cutconfig[0].AngularResolution / 1.1;
    if (i_dAz <= 0.1)
    {
        i_dAz = 0.1;
    } //3600
    else if (i_dAz <= 0.2)
    {
        i_dAz = 0.2;
    } //1800
    else if (i_dAz <= 0.25)
    {
        i_dAz = 0.25;
    } //1440

    else if (i_dAz <= 0.5)
    {
        i_dAz = 0.5;
    } //720
    else if (i_dAz <= 0.75)
    {
        i_dAz = 0.75;
    } //480
    else if (i_dAz <= 1.0)
    {
        i_dAz = 1.0;
    } //360
    else if (i_dAz <= 1.5)
    {
        i_dAz = 1.5;
    } //240
    else if (i_dAz <= 2.0)
    {
        i_dAz = 2.0;
    } //180
    else if (i_dAz <= 3.0)
    {
        i_dAz = 3.0;
    } //120
    else
    {
        if (m_DebugLevel <= 0)
        {
            set_time_str();
            cout << time_str;
            cout << " Algo_QC:: ";
            cout << "DAz is greater than 3.0 degree!" << endl;
        }
        return -1;
    }

    for (int i_cut = 0; i_cut < radardata_out->commonBlock.cutconfig.size(); i_cut++)
    {
        radardata_out->commonBlock.cutconfig[i_cut].AngularResolution = i_dAz;
    }

    float i_StartAngle = radardata_out->radials.front().radialheader.Azimuth;
    float i_EndAngle = radardata_out->radials.back().radialheader.Azimuth;

    if (i_CutStatus == 0 || i_CutStatus == 1 || i_CutStatus == 2 || i_CutStatus == 3 || i_CutStatus == 4)
    {
        i_StartAngle = 0;
        i_EndAngle = 360 - i_dAz;
    }
    int i_nRadialNumofCut = (i_EndAngle - i_StartAngle) / i_dAz + 1;
    int i_nCutNum = radardata_out->commonBlock.cutconfig.size();

    //float i_Radar_Az;
    vector<RADIAL> i_Radial_Temp;

    //i_Radar_Az.resize(i_nRadialNumofCut);
    i_Radial_Temp.resize(i_nRadialNumofCut * i_nCutNum);
    float i_LeftIndex = -1;
    float i_RightIndex = -1;
    int i_LeftIndex_org = -1;
    int i_RightIndex_org = -1;
    int i_StartIndex_org = 0;
    int i_IndexofCut = -1;
    //int i_IndexofTotal = -1;
    for (int i_Radial = 0; i_Radial < radardata_out->radials.size(); i_Radial++)
    {
        int i_cut_number = radardata_out->radials[i_Radial].radialheader.ElevationNumber - 1;
        if (fabs(radardata_out->radials[i_Radial + 1].radialheader.Azimuth - radardata_out->radials[i_Radial].radialheader.Azimuth) < 180)
        {
            i_LeftIndex_org = i_Radial;
            i_RightIndex_org = i_Radial + 1;
            i_LeftIndex = (radardata_out->radials[i_LeftIndex_org].radialheader.Azimuth - i_StartAngle) / i_dAz;
            i_RightIndex = (radardata_out->radials[i_RightIndex_org].radialheader.Azimuth - i_StartAngle) / i_dAz;
        }
        else
        {
            i_LeftIndex_org = i_Radial;
            i_RightIndex_org = i_StartIndex_org;
            i_StartIndex_org = i_Radial + 1;
            i_LeftIndex = (radardata_out->radials[i_LeftIndex_org].radialheader.Azimuth - 360 - i_StartAngle) / i_dAz;
            i_RightIndex = (radardata_out->radials[i_RightIndex_org].radialheader.Azimuth - i_StartAngle) / i_dAz;
        }
        //        if (m_DebugLevel <= 0){
        //            set_time_str();
        //            cout << time_str;
        //            cout << " Algo_QC:: ";
        //            cout <<i_LeftIndex_org<<"---"<<i_RightIndex_org<<endl;
        //            cout << radardata_out->radials[i_LeftIndex_org].radialheader.Azimuth<< "---";
        //            cout << radardata_out->radials[i_RightIndex_org].radialheader.Azimuth <<endl;
        //            cout << i_LeftIndex <<"---"<<i_RightIndex<<endl;
        //        }
        if (floor(i_RightIndex) - ceil(i_LeftIndex) > (int)3.0 / i_dAz)
        {
            continue;
        }
        for (int i = ceil(i_LeftIndex); i <= floor(i_RightIndex); i += max((int)(floor(i_RightIndex) - ceil(i_LeftIndex)), 1))
        {
            i_IndexofCut  = i;

            if (i_IndexofCut < 0)
            {
                i_IndexofCut += i_nRadialNumofCut;
            }
            if (i_IndexofCut == i_nRadialNumofCut)
            {
                i_IndexofCut -= i_nRadialNumofCut;
            }
            //            if (m_DebugLevel <= 0){
            //                set_time_str();
            //                cout << time_str;
            //                cout << " Algo_QC:: ";
            //                cout << ceil(i_IndexofCut) *i_dAz +i_StartAngle<<endl;
            //                cout << endl;
            //            }
            if (i_CutStatus == 0 || i_CutStatus == 1 || i_CutStatus == 2 || i_CutStatus == 3)
            {
                i_Radial_Temp[i_IndexofCut].radialheader.Azimuth = i_IndexofCut * i_dAz + i_StartAngle;
                CalcRadial(&radardata_out->radials[i_LeftIndex_org], &radardata_out->radials[i_RightIndex_org], &i_Radial_Temp[i_IndexofCut]);
            }
            else if (i_CutStatus == 4)
            {
                i_Radial_Temp[i_cut_number * i_nRadialNumofCut + i_IndexofCut].radialheader.Azimuth = i_IndexofCut * i_dAz + i_StartAngle;
                CalcRadial(&radardata_out->radials[i_LeftIndex_org], &radardata_out->radials[i_RightIndex_org], &i_Radial_Temp[i_cut_number * i_nRadialNumofCut + i_IndexofCut]);
            }
            //        if (fabs(i_Radial_Temp[i_cut_number * i_nRadialNumofCut + i_IndexofCut].radialheader.Azimuth-360)<0.001)
            //            i_Radial_Temp[i_cut_number * i_nRadialNumofCut + i_IndexofCut].radialheader.Azimuth = 0;
        }
    }

    // dealing with missing radial
    int i_Radial_of_Cut = 0;
    int i_Cut = -1;
    if (i_CutStatus == 0 || i_CutStatus == 1 || i_CutStatus == 2 || i_CutStatus == 3)
    {
        i_Cut = radardata_out->radials[0].radialheader.ElevationNumber - 1;
    }
    else if (i_CutStatus == 4)
    {
        i_Cut = 0;
    }
    for (int i_Radial = 0; i_Radial < i_Radial_Temp.size(); i_Radial++)
    {
        if (i_Radial_Temp[i_Radial].momentblock.size() == 0)
        {
            RADIAL i_missing;
            if (i_CutStatus == 0 || i_CutStatus == 1 || i_CutStatus == 2 || i_CutStatus == 3)
            {
                i_missing = radardata_in->radials.at(i_ElRadialIndex[0]);
            }
            else if (i_CutStatus == 4)
            {
                i_missing = radardata_in->radials.at(i_ElRadialIndex[i_Cut]);
            }
            if (i_missing.momentblock.front().momentheader.BinLength == 1)
            {
                vector<unsigned short> i_missing_value;
                for (int i_moment = 0; i_moment < i_missing.momentblock.size(); i_moment++)
                {
                    i_missing.momentblock.at(i_moment).momentheader.BinLength = 2;
                    i_missing.momentblock.at(i_moment).momentheader.Length *= 2;
                    i_missing.momentblock.at(i_moment).momentdata.resize(i_missing.momentblock.at(i_moment).momentdata.size() * 2);
                    i_missing_value.resize(i_missing.momentblock.at(i_moment).momentdata.size() / 2);
                    i_missing_value.assign(i_missing.momentblock.at(i_moment).momentdata.size() / 2, INVALID_BT);
                    memcpy(&i_missing.momentblock.at(i_moment).momentdata[0], &i_missing_value[0], i_missing.momentblock.at(i_moment).momentdata.size());
                }
            }
            else if (i_missing.momentblock.front().momentheader.BinLength == 2)
            {
                vector<unsigned short> i_missing_value;
                for (int i_moment = 0; i_moment < i_missing.momentblock.size(); i_moment++)
                {
                    i_missing_value.resize(i_missing.momentblock.at(i_moment).momentdata.size() / 2);
                    i_missing_value.assign(i_missing.momentblock.at(i_moment).momentdata.size() / 2, INVALID_BT);
                    memcpy(&i_missing.momentblock.at(i_moment).momentdata[0], &i_missing_value[0], i_missing.momentblock.at(i_moment).momentdata.size());
                }
            }

            i_Radial_Temp[i_Radial] = i_missing;
            //            i_Radial_Temp[i_Radial].radialheader.Elevation = i_Radial_Temp[i_Radial-i_Radial_of_Cut].radialheader.Elevation;
            i_Radial_Temp[i_Radial].radialheader.Azimuth = round(i_Radial_of_Cut) * i_dAz + i_StartAngle;
            i_Radial_Temp[i_Radial].radialheader.ElevationNumber = i_Cut + 1;
            //            i_Radial_Temp[i_Radial].radialheader.RadialNumber = i_Radial_of_Cut+1;
            //i_Radial_Temp[i_Radial].radialheader.RadialState += 100;
        }
        i_Radial_Temp[i_Radial].radialheader.RadialNumber = i_Radial_of_Cut + 1;
        if (i_CutStatus == 0 || i_CutStatus == 3 || i_CutStatus == 4)
        {
            i_Radial_Temp[i_Radial].radialheader.SequenceNumber = i_Radial + 1;
        }
        else if (i_CutStatus == 1 || i_CutStatus == 2)
        {
            i_Radial_Temp[i_Radial].radialheader.SequenceNumber = i_Cut * i_nRadialNumofCut + i_Radial + 1;
        }

        if (i_Radial == 0)
        {
            if (i_CutStatus == 0 || i_CutStatus == 4)
            {
                i_Radial_Temp[i_Radial].radialheader.RadialState = 3;
            }
            else
            {
                i_Radial_Temp[i_Radial].radialheader.RadialState = 0;
            }
        }
        else if (i_Radial == i_Radial_Temp.size() - 1)
        {
            if (i_CutStatus == 2 || i_CutStatus == 3)
            {
                i_Radial_Temp[i_Radial].radialheader.RadialState = 4;
            }
            else
            {
                i_Radial_Temp[i_Radial].radialheader.RadialState = 2;
            }
        }
        else if (i_Radial_of_Cut == 0)
        {
            i_Radial_Temp[i_Radial].radialheader.RadialState = 0;
        }
        else if (i_Radial_of_Cut == i_nRadialNumofCut - 1)
        {
            i_Radial_Temp[i_Radial].radialheader.RadialState = 2;
        }
        else
        {
            i_Radial_Temp[i_Radial].radialheader.RadialState = 1;
        }

        i_Radial_of_Cut ++;
        if (i_Radial_of_Cut == i_nRadialNumofCut)
        {
            i_Cut ++;
            i_Radial_of_Cut = 0;
        }
    }

    //swap to output
    radardata_out->radials.clear();
    radardata_out->radials.swap(i_Radial_Temp);
    return 0;

}

void CAlgoQC::Sort_Data_Iter(int i_start, int i_end, WRADRAWDATA *radardata_out)
{
    if (i_start == i_end)
    {
        return;
    }

    int Temp_Index = i_start + (i_end - i_start) / 2;
    float Temp_Az = radardata_out->radials[Temp_Index].radialheader.Azimuth;
    RADIAL tempRadialData;
    int i_Sort = i_start;
    int i_Sort_End = i_end;
    //	if (nSortNum > 20) cout << nSortNum << endl;

    for (i_Sort; i_Sort <= i_end; i_Sort++)
    {
        if (radardata_out->radials[i_Sort].radialheader.Azimuth < Temp_Az  && i_Sort > Temp_Index)
        {
            tempRadialData = radardata_out->radials[Temp_Index];
            radardata_out->radials[Temp_Index] = radardata_out->radials[i_Sort];
            radardata_out->radials[i_Sort] = tempRadialData;
            Temp_Index = i_Sort;
        }
        if (radardata_out->radials[i_Sort].radialheader.Azimuth > Temp_Az)
        {
            for (i_Sort_End; i_Sort_End > i_Sort; i_Sort_End--)
            {
                if (radardata_out->radials[i_Sort_End].radialheader.Azimuth < Temp_Az)
                {
                    tempRadialData = radardata_out->radials[i_Sort_End];
                    radardata_out->radials[i_Sort_End] = radardata_out->radials[i_Sort];
                    radardata_out->radials[i_Sort] = tempRadialData;
                    if (i_Sort > Temp_Index)
                    {
                        tempRadialData = radardata_out->radials[Temp_Index];
                        radardata_out->radials[Temp_Index] = radardata_out->radials[i_Sort];
                        radardata_out->radials[i_Sort] = tempRadialData;
                        Temp_Index = i_Sort;
                    }
                    break;
                }
                else if (i_Sort_End == Temp_Index)
                {
                    tempRadialData = radardata_out->radials[Temp_Index];
                    radardata_out->radials[Temp_Index] = radardata_out->radials[i_Sort];
                    radardata_out->radials[i_Sort] = tempRadialData;
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
    if (Temp_Index - i_start >= 2)
    {
        Sort_Data_Iter(i_start, Temp_Index - 1, radardata_out);
    }
    if (i_end - Temp_Index >= 2)
    {
        Sort_Data_Iter(Temp_Index + 1, i_end, radardata_out);
    }

    return;
}

int CAlgoQC::Normalize_Az()
{
    if (m_radardata_out->commonBlock.taskconfig.ScanType == 3 \
            || m_radardata_out->commonBlock.taskconfig.ScanType == 4 \
            || m_radardata_out->commonBlock.taskconfig.ScanType == 5 \
            || m_radardata_out->commonBlock.taskconfig.ScanType == 6)
    {
        return 0;
    }
    if (m_radardata_out->commonBlock.taskconfig.ScanType == 2)
    {
        return Normalize_RHI();
    }

    int i_CutStatus = 0;   //0:first cut of VTB, 1:middle cut of VTB,  2:last cut of VTB    3:single PPI scan    4:complete VTB
    if (m_radardata_out->commonBlock.cutconfig.size() == 1)
    {
        if (m_radardata_out->commonBlock.taskconfig.ScanType == 1)
        {
            i_CutStatus = 3;
        }
        else if (m_radardata_out->commonBlock.taskconfig.ScanType == 0)
        {
            if (m_radardata_out->radials.front().radialheader.ElevationNumber == 1)
            {
                i_CutStatus = 0;
            }
            else if (m_radardata_out->radials.back().radialheader.ElevationNumber == m_radardata_out->commonBlock.taskconfig.CutNumber)
            {
                i_CutStatus = 2;
            }
            else
            {
                i_CutStatus = 1;
            }
        }
    }
    else
    {
        if (m_radardata_out->commonBlock.taskconfig.ScanType == 0)
        {
            if (m_radardata_out->radials.front().radialheader.ElevationNumber == 1 \
                    && m_radardata_out->radials.back().radialheader.ElevationNumber == m_radardata_out->commonBlock.taskconfig.CutNumber)
            {
                i_CutStatus = 4;
            }
        }
        else
        {
            if (m_DebugLevel <= 0)
            {
                set_time_str();
                cout << time_str;
                cout << " Algo_QC:: ";
                cout << "Not supproted format!" << endl;
            }
            return -1;
        }

    }
    float i_dAz = m_radardata_out->commonBlock.cutconfig[0].AngularResolution / 1.1;
    if (i_dAz <= 0.1)
    {
        i_dAz = 0.1;
    } //3600
    else if (i_dAz <= 0.2)
    {
        i_dAz = 0.2;
    } //1800
    else if (i_dAz <= 0.25)
    {
        i_dAz = 0.25;
    } //1440
    else if (i_dAz <= 0.5)
    {
        i_dAz = 0.5;
    } //720
    else if (i_dAz <= 0.75)
    {
        i_dAz = 0.75;
    } //480
    else if (i_dAz <= 1.0)
    {
        i_dAz = 1.0;
    } //360
    else if (i_dAz <= 1.5)
    {
        i_dAz = 1.5;
    } //240
    else if (i_dAz <= 2.0)
    {
        i_dAz = 2.0;
    } //180
    else if (i_dAz <= 3.0)
    {
        i_dAz = 3.0;
    } //120
    else if (i_dAz <= 4.0)
    {
        i_dAz = 4.0;
    } //90
    else if (i_dAz <= 5.0)
    {
        i_dAz = 5.0;
    } //72
    else if (i_dAz <= 6.0)
    {
        i_dAz = 6.0;
    } //60
    else if (i_dAz <= 7.5)
    {
        i_dAz = 7.5;
    } //48
    else
    {
        if (m_DebugLevel <= 0)
        {
            set_time_str();
            cout << time_str;
            cout << " Algo_QC:: ";
            cout << "DAz is greater than 3.0 degree!" << endl;
        }
        return -1;
    }
    cout << "i_dAz:" << i_dAz << endl;

    for (int i_cut = 0; i_cut < m_radardata_out->commonBlock.cutconfig.size(); i_cut++)
    {
        m_radardata_out->commonBlock.cutconfig[i_cut].AngularResolution = i_dAz;
    }

    // RHI
    float i_StartAngle = m_radardata_out->radials.front().radialheader.Azimuth;
    float i_EndAngle = m_radardata_out->radials.back().radialheader.Azimuth;

    if (i_CutStatus == 0 || i_CutStatus == 1 || i_CutStatus == 2 || i_CutStatus == 3 || i_CutStatus == 4)
    {
        i_StartAngle = 0;
        i_EndAngle = 360 - i_dAz;
    }
    int i_nRadialNumofCut = (i_EndAngle - i_StartAngle) / i_dAz + 1;
    int i_nCutNum = m_radardata_out->commonBlock.cutconfig.size();

    if (m_DebugLevel <= 0)
    {
        set_time_str();
        cout << time_str;
        cout << " Algo_QC:: ";
        cout << "The Data is remapped to ";
        cout << i_nRadialNumofCut;
        cout << " records per PPI" << endl;
    }

    //float i_Radar_Az;
    vector<RADIAL> i_Radial_Temp;

    //i_Radar_Az.resize(i_nRadialNumofCut);
    i_Radial_Temp.resize(i_nRadialNumofCut * i_nCutNum);
    float i_LeftIndex = -1;
    float i_RightIndex = -1;
    int i_LeftIndex_org = -1;
    int i_RightIndex_org = -1;
    int i_StartIndex_org = 0;
    int i_IndexofCut = -1;
    //int i_IndexofTotal = -1;
    for (int i_Radial = 0; i_Radial < m_radardata_out->radials.size(); i_Radial++)
    {
        int i_cut_number = m_radardata_out->radials[i_Radial].radialheader.ElevationNumber - 1;
        if (fabs(m_radardata_out->radials[i_Radial + 1].radialheader.Azimuth - m_radardata_out->radials[i_Radial].radialheader.Azimuth) < 180\
                && i_Radial != m_radardata_out->radials.size() - 1)
        {
            i_LeftIndex_org = i_Radial;
            i_RightIndex_org = i_Radial + 1;
            i_LeftIndex = (m_radardata_out->radials[i_LeftIndex_org].radialheader.Azimuth - i_StartAngle) / i_dAz;
            i_RightIndex = (m_radardata_out->radials[i_RightIndex_org].radialheader.Azimuth - i_StartAngle) / i_dAz;
        }
        else
        {
            i_LeftIndex_org = i_Radial;
            i_RightIndex_org = i_StartIndex_org;
            i_StartIndex_org = i_Radial + 1;
            i_LeftIndex = (m_radardata_out->radials[i_LeftIndex_org].radialheader.Azimuth - 360 - i_StartAngle) / i_dAz;
            i_RightIndex = (m_radardata_out->radials[i_RightIndex_org].radialheader.Azimuth - i_StartAngle) / i_dAz;
        }

        if (floor(i_RightIndex) - ceil(i_LeftIndex) > (int)3.0 / i_dAz)
        {
            continue;
        }
        for (int i = ceil(i_LeftIndex); i <= floor(i_RightIndex); i += 1) //max((int)(floor(i_RightIndex)-ceil(i_LeftIndex)),1))
        {
            i_IndexofCut  = i;

            if (i_IndexofCut < 0)
            {
                i_IndexofCut += i_nRadialNumofCut;
            }
            if (i_IndexofCut == i_nRadialNumofCut)
            {
                i_IndexofCut -= i_nRadialNumofCut;
            }

            if (i_CutStatus == 0 || i_CutStatus == 1 || i_CutStatus == 2 || i_CutStatus == 3)
            {
                i_Radial_Temp[i_IndexofCut].radialheader.Azimuth = i_IndexofCut * i_dAz + i_StartAngle;
                CalcRadial(&m_radardata_out->radials[i_LeftIndex_org], &m_radardata_out->radials[i_RightIndex_org], &i_Radial_Temp[i_IndexofCut]);
            }
            else if (i_CutStatus == 4)
            {
                i_Radial_Temp[i_cut_number * i_nRadialNumofCut + i_IndexofCut].radialheader.Azimuth = i_IndexofCut * i_dAz + i_StartAngle;
                CalcRadial(&m_radardata_out->radials[i_LeftIndex_org], &m_radardata_out->radials[i_RightIndex_org], &i_Radial_Temp[i_cut_number * i_nRadialNumofCut + i_IndexofCut]);
            }
        }
    }

    // dealing with missing radial
    int i_Radial_of_Cut = 0;
    int i_Cut = -1;
    if (i_CutStatus == 0 || i_CutStatus == 1 || i_CutStatus == 2 || i_CutStatus == 3)
    {
        i_Cut = m_radardata_out->radials[0].radialheader.ElevationNumber - 1;
    }
    else if (i_CutStatus == 4)
    {
        i_Cut = 0;
    }
    for (int i_Radial = 0; i_Radial < i_Radial_Temp.size(); i_Radial++)
    {
        if (i_Radial_Temp[i_Radial].momentblock.size() == 0)
        {
            RADIAL i_missing;
            if (i_CutStatus == 0 || i_CutStatus == 1 || i_CutStatus == 2 || i_CutStatus == 3)
            {
                i_missing = m_radardata_out->radials.at(ElRadialIndex[0]);  //mark
            }
            else if (i_CutStatus == 4)
            {
                i_missing = m_radardata_out->radials.at(ElRadialIndex[i_Cut]);
            }
            if (i_missing.momentblock.front().momentheader.BinLength == 1)
            {
                vector<unsigned short> i_missing_value;
                for (int i_moment = 0; i_moment < i_missing.momentblock.size(); i_moment++)
                {
                    i_missing.momentblock.at(i_moment).momentheader.BinLength = 2;
                    i_missing.momentblock.at(i_moment).momentheader.Length *= 2;
                    i_missing.momentblock.at(i_moment).momentdata.resize(i_missing.momentblock.at(i_moment).momentdata.size() * 2);
                    i_missing_value.resize(i_missing.momentblock.at(i_moment).momentdata.size() / 2);
                    i_missing_value.assign(i_missing.momentblock.at(i_moment).momentdata.size() / 2, INVALID_BT);
                    memcpy(&i_missing.momentblock.at(i_moment).momentdata[0], &i_missing_value[0], i_missing.momentblock.at(i_moment).momentdata.size());
                }
            }
            else if (i_missing.momentblock.front().momentheader.BinLength == 2)
            {
                vector<unsigned short> i_missing_value;
                for (int i_moment = 0; i_moment < i_missing.momentblock.size(); i_moment++)
                {
                    i_missing_value.resize(i_missing.momentblock.at(i_moment).momentdata.size() / 2);
                    i_missing_value.assign(i_missing.momentblock.at(i_moment).momentdata.size() / 2, INVALID_BT);
                    memcpy(&i_missing.momentblock.at(i_moment).momentdata[0], &i_missing_value[0], i_missing.momentblock.at(i_moment).momentdata.size());
                }
            }

            i_Radial_Temp[i_Radial] = i_missing;
            //            i_Radial_Temp[i_Radial].radialheader.Elevation = i_Radial_Temp[i_Radial-i_Radial_of_Cut].radialheader.Elevation;
            i_Radial_Temp[i_Radial].radialheader.Azimuth = round(i_Radial_of_Cut) * i_dAz + i_StartAngle;
            i_Radial_Temp[i_Radial].radialheader.ElevationNumber = i_Cut + 1;
            //            i_Radial_Temp[i_Radial].radialheader.RadialNumber = i_Radial_of_Cut+1;
            //i_Radial_Temp[i_Radial].radialheader.RadialState += 100;
        }
        i_Radial_Temp[i_Radial].radialheader.RadialNumber = i_Radial_of_Cut + 1;
        if (i_CutStatus == 0 || i_CutStatus == 3 || i_CutStatus == 4)
        {
            i_Radial_Temp[i_Radial].radialheader.SequenceNumber = i_Radial + 1;
        }
        else if (i_CutStatus == 1 || i_CutStatus == 2)
        {
            i_Radial_Temp[i_Radial].radialheader.SequenceNumber = i_Cut * i_nRadialNumofCut + i_Radial + 1;
        }

        if (i_Radial == 0)
        {
            if (i_CutStatus == 0 || i_CutStatus == 4)
            {
                i_Radial_Temp[i_Radial].radialheader.RadialState = 3;
            }
            else
            {
                i_Radial_Temp[i_Radial].radialheader.RadialState = 0;
            }
        }
        else if (i_Radial == i_Radial_Temp.size() - 1)
        {
            if (i_CutStatus == 2 || i_CutStatus == 3)
            {
                i_Radial_Temp[i_Radial].radialheader.RadialState = 4;
            }
            else
            {
                i_Radial_Temp[i_Radial].radialheader.RadialState = 2;
            }
        }
        else if (i_Radial_of_Cut == 0)
        {
            i_Radial_Temp[i_Radial].radialheader.RadialState = 0;
        }
        else if (i_Radial_of_Cut == i_nRadialNumofCut - 1)
        {
            i_Radial_Temp[i_Radial].radialheader.RadialState = 2;
        }
        else
        {
            i_Radial_Temp[i_Radial].radialheader.RadialState = 1;
        }

        i_Radial_of_Cut ++;
        if (i_Radial_of_Cut == i_nRadialNumofCut)
        {
            i_Cut ++;
            i_Radial_of_Cut = 0;
        }
    }

    //swap to output
    m_radardata_out->radials.clear();
    m_radardata_out->radials.swap(i_Radial_Temp);
    return 0;
}

int CAlgoQC::Normalize_RHI()
{
    if (m_radardata_out->commonBlock.taskconfig.ScanType != 2)
    {
        if (m_DebugLevel <= 0)
        {
            set_time_str();
            cout << time_str;
            cout << " Algo_QC:: ";
            cout << "Not supproted format!" << endl;
        }
        return -1;
    }

    //寻找最大的库数，归一化到最长的库数
    int maxBinNum = 0;
    for (int i_radial = 0; i_radial < m_radardata_out->radials.size(); ++i_radial)
    {
        for (int i_moment = 0; i_moment < m_radardata_out->radials[i_radial].radialheader.MomentNumber; ++i_moment)
        {
            int t_binNum = m_radardata_out->radials[i_radial].momentblock[i_moment].momentheader.Length \
                           / m_radardata_out->radials[i_radial].momentblock[i_moment].momentheader.BinLength;
            if (t_binNum > maxBinNum)
            {
                maxBinNum = t_binNum;
            }
        }
    }

    for (int i_radial = 0; i_radial < m_radardata_out->radials.size(); ++i_radial)
    {
        for (int i_moment = 0; i_moment < m_radardata_out->radials[i_radial].radialheader.MomentNumber; ++i_moment)
        {
            if (m_radardata_out->radials[i_radial].momentblock[i_moment].momentheader.BinLength == 1)
            {
                MOMENTBLOCK tmp_Moment;
                memcpy(&tmp_Moment.momentheader, &m_radardata_out->radials[i_radial].momentblock[i_moment].momentheader, sizeof(MOMENTHEADER));
                tmp_Moment.momentheader.BinLength   = 2;
                tmp_Moment.momentheader.Length      = 2 * maxBinNum;
                tmp_Moment.momentdata.resize(tmp_Moment.momentheader.Length);
                unsigned short *desData = (unsigned short *)&tmp_Moment.momentdata[0];
                unsigned char *srcData  = (unsigned char *)&m_radardata_out->radials[i_radial].momentblock[i_moment].momentdata[0];
                int t_oldBinNum = m_radardata_out->radials[i_radial].momentblock[i_moment].momentheader.Length \
                                  / m_radardata_out->radials[i_radial].momentblock[i_moment].momentheader.BinLength;
                for (int i_bin = 0; i_bin < maxBinNum; ++i_bin)
                {
                    desData[i_bin] = i_bin < t_oldBinNum ? srcData[i_bin] : INVALID_BT; // 扩展到统一库数，多出来的赋无效数值
                }
                m_radardata_out->radials[i_radial].momentblock.erase(m_radardata_out->radials[i_radial].momentblock.begin() + i_moment);
                m_radardata_out->radials[i_radial].momentblock.insert(m_radardata_out->radials[i_radial].momentblock.begin() + i_moment, tmp_Moment);
            }
            else if (m_radardata_out->radials[i_radial].momentblock[i_moment].momentheader.BinLength == 2 \
                     && m_radardata_out->radials[i_radial].momentblock[i_moment].momentheader.Length < 2 * maxBinNum)
            {
                MOMENTBLOCK tmp_Moment;
                memcpy(&tmp_Moment.momentheader, &m_radardata_out->radials[i_radial].momentblock[i_moment].momentheader, sizeof(MOMENTHEADER));
                tmp_Moment.momentheader.BinLength   = 2;
                tmp_Moment.momentheader.Length      = 2 * maxBinNum;
                tmp_Moment.momentdata.resize(tmp_Moment.momentheader.Length);
                unsigned short *desData = (unsigned short *)&tmp_Moment.momentdata[0];
                unsigned short *srcData  = (unsigned short *)&m_radardata_out->radials[i_radial].momentblock[i_moment].momentdata[0];
                int t_oldBinNum = m_radardata_out->radials[i_radial].momentblock[i_moment].momentheader.Length \
                                  / m_radardata_out->radials[i_radial].momentblock[i_moment].momentheader.BinLength;
                for (int i_bin = 0; i_bin < maxBinNum; ++i_bin)
                {
                    desData[i_bin] = i_bin < t_oldBinNum ? srcData[i_bin] : INVALID_BT; // 扩展到统一库数，多出来的赋无效数值
                }
                m_radardata_out->radials[i_radial].momentblock.erase(m_radardata_out->radials[i_radial].momentblock.begin() + i_moment);
                m_radardata_out->radials[i_radial].momentblock.insert(m_radardata_out->radials[i_radial].momentblock.begin() + i_moment, tmp_Moment);
            }
        }
    }

    return 0;
}

void CAlgoQC::Sort_Data_Iter(int i_start, int i_end)
{
    if (i_start == i_end)
    {
        return;
    }

    int Temp_Index = i_start + (i_end - i_start) / 2;
    int i_Sort = i_start;
    int i_Sort_End = i_end;
    //	if (nSortNum > 20) cout << nSortNum << endl;

    for (i_Sort; i_Sort <= i_end; i_Sort++)
    {
        float Temp_Az = m_radardata_out->radials[Temp_Index].radialheader.Azimuth;
        RADIAL tempRadialData;
        if (m_radardata_out->radials[i_Sort].radialheader.Azimuth < Temp_Az  && i_Sort > Temp_Index)
        {
            tempRadialData = m_radardata_out->radials[Temp_Index];
            m_radardata_out->radials[Temp_Index] = m_radardata_out->radials[i_Sort];
            m_radardata_out->radials[i_Sort] = tempRadialData;
            Temp_Index = i_Sort;
        }
        if (m_radardata_out->radials[i_Sort].radialheader.Azimuth > Temp_Az)
        {
            for (i_Sort_End; i_Sort_End > i_Sort; i_Sort_End--)
            {
                if (m_radardata_out->radials[i_Sort_End].radialheader.Azimuth < Temp_Az)
                {
                    tempRadialData = m_radardata_out->radials[i_Sort_End];
                    m_radardata_out->radials[i_Sort_End] = m_radardata_out->radials[i_Sort];
                    m_radardata_out->radials[i_Sort] = tempRadialData;
                    if (i_Sort > Temp_Index)
                    {
                        tempRadialData = m_radardata_out->radials[Temp_Index];
                        m_radardata_out->radials[Temp_Index] = m_radardata_out->radials[i_Sort];
                        m_radardata_out->radials[i_Sort] = tempRadialData;
                        Temp_Index = i_Sort;
                    }
                    break;
                }
                else if (i_Sort_End == Temp_Index)
                {
                    tempRadialData = m_radardata_out->radials[Temp_Index];
                    m_radardata_out->radials[Temp_Index] = m_radardata_out->radials[i_Sort];
                    m_radardata_out->radials[i_Sort] = tempRadialData;
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
    //    if (m_DebugLevel <= 0){
    //        set_time_str();
    //        cout << time_str;
    //        cout << " Algo_QC:: ";
    //        cout << "\n\n\n" <<endl;
    //        cout << i_start <<"-----"<<i_end<<endl;
    //        cout << Temp_Index <<"-----"<<Temp_Az<<endl;

    //        for (int i = i_start ;i<=i_end;i++)
    //            cout << i << ":" <<m_radardata_out->radials[i].radialheader.Azimuth <<endl;


    //        cout << i_start <<"-----"<<i_end<<endl;
    //        cout << Temp_Index <<"-----"<<Temp_Az<<endl;
    //        cout << "\n\n\n" <<endl;
    //    }
    if (Temp_Index - i_start >= 2)
    {
        Sort_Data_Iter(i_start, Temp_Index - 1);
    }
    if (i_end - Temp_Index >= 2)
    {
        Sort_Data_Iter(Temp_Index + 1, i_end);
    }

    return;
}

void CAlgoQC::CalcRadial(RADIAL *front, RADIAL *back, RADIAL *target)
{
    double az_front = front->radialheader.Azimuth;
    double az_back = back->radialheader.Azimuth;
    double az_target = target->radialheader.Azimuth;
    double dAz;
    if (fabs(az_back - 360.0) < 0.0001)
    {
        az_back -= 360.0;
    }
    if (az_front - az_back > 180.0)
    {
        az_front -= 360.0;
    }
    if (az_target - az_back > 180.0)
    {
        az_target -= 360.0;
    }
    if (az_target - az_front < az_back - az_target)
    {
        *target = *front;
        dAz = az_target - az_front;
    }
    else
    {
        *target = *back;
        dAz = az_back - az_target;
    }

    if (az_target >= 0)
    {
        target->radialheader.Azimuth = az_target;
    }
    else
    {
        target->radialheader.Azimuth = az_target + 360.0;
    }
    //    if (dAz <= 0.1) return;

    for (int i_moment = 0; i_moment < front->momentblock.size(); i_moment ++)
    {
        //        if (front->momentblock[i_moment].momentheader.BinLength != 2){
        //            if (m_DebugLevel <= 3){
        //                set_time_str();
        //                cout << time_str;
        //                cout << " Algo_QC:: ";
        //                cout <<"Not support now!" <<endl;
        //            }
        //            return;
        //        }
        if (front->momentblock[i_moment].momentheader.BinLength == 2)
        {
            unsigned short *data_front = (unsigned short *) & (front->momentblock[i_moment].momentdata[0]);
            unsigned short *data_back = (unsigned short *) & (back->momentblock[i_moment].momentdata[0]);
            unsigned short *data_target = (unsigned short *) & (target->momentblock[i_moment].momentdata[0]);
            for (int i_data = 0; i_data < front->momentblock[i_moment].momentdata.size() \
                    / front->momentblock[i_moment].momentheader.BinLength; i_data++)
            {
                if (data_front[i_data] <= INVALID_RSV)
                {
                    data_target[i_data] = data_front[i_data];
                }
                else if (data_back[i_data] <= INVALID_RSV)
                {
                    data_target[i_data] = data_back[i_data];
                }
                else
                {
                    data_target[i_data] = (data_front[i_data] * (az_back - az_target) \
                                           + data_back[i_data] * (az_target - az_front)) \
                                          / (az_back - az_front);
                }
            }
        }
        else if (front->momentblock[i_moment].momentheader.BinLength == 1)
        {
            unsigned char *data_front = (unsigned char *) & (front->momentblock[i_moment].momentdata[0]);
            unsigned char *data_back = (unsigned char *) & (back->momentblock[i_moment].momentdata[0]);
            target->momentblock[i_moment].momentheader.BinLength = 2;
            target->momentblock[i_moment].momentheader.Length *= 2;
            target->momentblock.at(i_moment).momentdata.resize(target->momentblock.at(i_moment).momentdata.size() * 2);
            unsigned short *data_target = (unsigned short *) & (target->momentblock[i_moment].momentdata[0]);
            for (int i_data = 0; i_data < front->momentblock[i_moment].momentdata.size() \
                    / front->momentblock[i_moment].momentheader.BinLength; i_data++)
            {
                if (data_front[i_data] <= INVALID_RSV)
                {
                    data_target[i_data] = data_front[i_data];
                }
                else if (data_back[i_data] <= INVALID_RSV)
                {
                    data_target[i_data] = data_back[i_data];
                }
                else
                {
                    data_target[i_data] = (data_front[i_data] * (az_back - az_target) \
                                           + data_back[i_data] * (az_target - az_front)) \
                                          / (az_back - az_front);
                }
            }
        }
    }
}

//衰减订正=========================================================================================================================
int CAlgoQC::AttenuationCorrection()
{
    if (!FunctionValid(m_params_AttenuationCorrection))
    {
        return 0;
    }
//    if(m_radardata_out->commonBlock.siteconfig.RadarType <= 4) return 0;

    for (int i_cut = 0; i_cut < m_radardata_out->commonBlock.cutconfig.size(); i_cut++)
    {
        if (indexZH.at(i_cut) == -1 || indexZDR.at(i_cut) == -1 || indexKDP.at(i_cut) == -1)
        {
            continue;
        }
        int KDPOffset = m_radardata_out->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(indexKDP.at(i_cut)).momentheader.Offset;
        int KDPScale = m_radardata_out->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(indexKDP.at(i_cut)).momentheader.Scale;
        int ZHOffset = m_radardata_out->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(indexZH.at(i_cut)).momentheader.Offset;
        int ZHScale = m_radardata_out->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(indexZH.at(i_cut)).momentheader.Scale;
        int ZDROffset = m_radardata_out->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(indexZDR.at(i_cut)).momentheader.Offset;
        int ZDRScale = m_radardata_out->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(indexZDR.at(i_cut)).momentheader.Scale;
        #pragma omp parallel for
        for (int iradial = ElRadialIndex.at(i_cut); iradial < ElRadialIndex.at(i_cut) + ElRadialNum.at(i_cut); iradial++)
        {
            float AZh = 0;
            float AZDR = 0;
            for (int ibin = 1; ibin < nBinNumZ.at(i_cut); ibin++)
            {
                //            if(tempdata.datablock.at(iradial).radialline.at(ZHindex).momentline.at(ibin)!=PREFILLVALUE && tempdata.datablock.at(iradial).radialline.at(PHDPindex).momentline.at(ibin)!=PREFILLVALUE){
                //                short ZHcor = tempdata.datablock.at(iradial).radialline.at(ZHindex).momentline.at(ibin) + 0.32 * tempdata.datablock.at(iradial).radialline.at(PHDPindex).momentline.at(ibin);
                //                memcpy(&m_radardata_out->radials.at(iradial).momentblock.at(ZHindex).momentdata.at(2*ibin),&ZHcor,2);

                //            }
                //            if(tempdata.datablock.at(iradial).radialline.at(ZDRindex).momentline.at(ibin)!=PREFILLVALUE && tempdata.datablock.at(iradial).radialline.at(PHDPindex).momentline.at(ibin)!=PREFILLVALUE){
                //                short ZDRcor = tempdata.datablock.at(iradial).radialline.at(ZDRindex).momentline.at(ibin) + 0.059 * (tempdata.datablock.at(iradial).radialline.at(PHDPindex).momentline.at(ibin)-tempdata.datablock.at(iradial).radialline.at(PHDPindex).momentline.at(ibin-1));
                //                memcpy(&m_radardata_out->radials.at(iradial).momentblock.at(ZDRindex).momentdata.at(2*ibin),&ZDRcor,2);
                //            }

                unsigned short *KDPdata = (unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexKDP.at(i_cut)).momentdata.at(0);
                unsigned short *ZHdata = (unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexZH.at(i_cut)).momentdata.at(0);
                unsigned short *ZDRdata = (unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexZDR.at(i_cut)).momentdata.at(0);
                if (KDPdata[ibin] > INVALID_RSV)
                {
                    float KDP = (1.0 * KDPdata[ibin] - KDPOffset) / KDPScale;
                    float ZHcor = (1.0 * ZHdata[ibin] - ZHOffset) / ZHScale + AZh;
                    if (m_radardata_out->commonBlock.siteconfig.RadarType == 75)   //X波段雷达衰减订正
                    {
                        float kAZh;
                        if (ZHcor <= 15)
                        {
                            if (KDP < 0)
                            {
                                kAZh = 0;
                            }
                            else if (KDP < 1.5)
                            {
                                kAZh = 0.216;
                            }
                            else if (KDP < 3.0)
                            {
                                kAZh = 0.218;
                            }
                            else if (KDP < 4.5)
                            {
                                kAZh = 0.201;
                            }
                            else if (KDP < 6.0)
                            {
                                kAZh = 0.125;
                            }
                            else if (KDP < 7.5)
                            {
                                kAZh = 0.1;
                            }
                            else
                            {
                                kAZh = 0.75 / KDP;
                            }
                        }
                        else if (ZHcor <= 30)
                        {
                            if (KDP < 0)
                            {
                                kAZh = 0;
                            }
                            else if (KDP < 1.5)
                            {
                                kAZh = 0.2;
                            }
                            else if (KDP < 3.0)
                            {
                                kAZh = 0.193;
                            }
                            else if (KDP < 4.5)
                            {
                                kAZh = 0.167;
                            }
                            else if (KDP < 6.0)
                            {
                                kAZh = 0.178;
                            }
                            else if (KDP < 7.5)
                            {
                                kAZh = 0.1;
                            }
                            else
                            {
                                kAZh = 0.75 / KDP;
                            }
                        }
                        else if (ZHcor <= 45)
                        {
                            if (KDP < 0)
                            {
                                kAZh = 0;
                            }
                            else if (KDP < 1.5)
                            {
                                kAZh = 0.202;
                            }
                            else if (KDP < 3.0)
                            {
                                kAZh = 0.175;
                            }
                            else if (KDP < 4.5)
                            {
                                kAZh = 0.163;
                            }
                            else if (KDP < 6.0)
                            {
                                kAZh = 0.189;
                            }
                            else if (KDP < 7.5)
                            {
                                kAZh = 0.12;
                            }
                            else
                            {
                                kAZh = 0.8 / KDP;
                            }
                        }
                        else
                        {
                            if (KDP < 0)
                            {
                                kAZh = 0;
                            }
                            else if (KDP < 1.5)
                            {
                                kAZh = 0.369;
                            }
                            else if (KDP < 3.0)
                            {
                                kAZh = 0.234;
                            }
                            else if (KDP < 4.5)
                            {
                                kAZh = 0.187;
                            }
                            else if (KDP < 6.0)
                            {
                                kAZh = 0.154;
                            }
                            else if (KDP < 7.5)
                            {
                                kAZh = 0.12;
                            }
                            else
                            {
                                kAZh = 0.8 / KDP;
                            }
                        }
                        //                kAZh = 0.247;
                        AZh += kAZh * KDP * nBinWidthZ.at(i_cut) * 2;
                        float kAZdr = 1.28 * pow(AZh, 1.156);
                        if (KDP < 10)
                        {
                            AZDR += 0.059 * KDP * nBinWidthZ.at(i_cut) * 2;
                        }
                        //                AZDR = 0.033 * KDP;
                    }
                    else      //海口C波段雷达衰减订正
                    {
                        AZh += 0.2 * KDP * nBinWidth * 2;
                        if (KDP < 10)
                        {
                            AZDR += 0.036 * KDP * nBinWidth * 2;
                        }
                    }
                }
                if (ZHdata[ibin] > INVALID_RSV)
                {

                    ZHdata[ibin] += (AZh * ZHScale);
                    //memcpy(&m_radardata_out->radials.at(iradial).momentblock.at(indexZH.at(i_cut)).momentdata.at(2*ibin),&ZHcor,2);

                }
                if (ZDRdata[ibin] > INVALID_RSV)
                {
                    ZDRdata[ibin] += (AZDR * ZDRScale);
                    //                    unsigned short ZDRcor = tempdata.datablock.at(iradial).radialline.at(indexZDR.at(i_cut)).momentline.at(ibin) + (AZDR * ZDRScale);
                    //                    memcpy(&m_radardata_out->radials.at(iradial).momentblock.at(indexZDR.at(i_cut)).momentdata.at(2*ibin),&ZDRcor,2);
                }

            }
        }
    }
    return 0;
}

//避雷针影响订正
int CAlgoQC::LGT_Correct()
{
    if (m_radardata_out->commonBlock.siteconfig.RadarType != 75)
    {
        return 0;
    }

    float LGT_Azi = m_radardata_out->commonBlock.taskconfig.LGTAZ;
    float a = m_radardata_out->commonBlock.taskconfig.LGTZDRA;  // * ZDRscale;
    float b = m_radardata_out->commonBlock.taskconfig.LGTZDRB;
    float LGT_Range = 15.0;
    //GCXRD
    //    a=7;
    //    LGT_Azi=28;
    //    b=5;
    if (fabs(LGT_Azi - PREFILLVALUE_FLOAT) < 1e-5 || fabs(a - PREFILLVALUE_FLOAT) < 1e-5 || fabs(b - PREFILLVALUE_FLOAT) < 1e-5)
    {
        return 0;
    }

    for (int i_cut = 0; i_cut < m_radardata_out->commonBlock.cutconfig.size(); i_cut++)
    {
        if (indexZH.at(i_cut) == -1 || indexZDR.at(i_cut) == -1)
        {
            continue;
        }




        for (int iradial = ElRadialIndex.at(i_cut); iradial < ElRadialIndex.at(i_cut) + ElRadialNum.at(i_cut); iradial ++)
        {
            int ZDROffset = m_radardata_out->radials.at(iradial).momentblock.at(indexZDR.at(i_cut)).momentheader.Offset;
            int ZDRScale = m_radardata_out->radials.at(iradial).momentblock.at(indexZDR.at(i_cut)).momentheader.Scale;

            float temp_az = m_radardata_out->radials.at(iradial).radialheader.Azimuth;
            while (temp_az >= 90)
            {
                temp_az -= 90;
            }
            if (fabs(temp_az - LGT_Azi) < LGT_Range || 90 - fabs(temp_az - LGT_Azi) < LGT_Range)
            {
                float d_az = fmin(fabs(temp_az - LGT_Azi), 90 - fabs(temp_az - LGT_Azi));
                for (auto i_bin = 0; i_bin < nBinNum; i_bin++)
                {
                    unsigned short temp_Zdr = *((unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexZDR.at(i_cut)).momentdata.at(i_bin * 2));
                    if (temp_Zdr > INVALID_RSV)
                    {
                        temp_Zdr -= a / (sqrt(2 * PI) * b) * exp(-pow((d_az), 2) / (2 * b * b)) * ZDRScale;
                        memcpy(&m_radardata_out->radials.at(iradial).momentblock.at(indexZDR.at(i_cut)).momentdata.at(i_bin * 2), &temp_Zdr, 2);
                    }
                }
            }
        }
    }
    return 0;

    //    int startlayer = -1,endlayer = -1;
    //    //    int CalcLength = 6;                     //计算降水径向上的范围
    //    //    int CalcNum = round(CalcLength / nBinWidth) / 2 * 2 + 1;  //计算径向路径上的库数
    //    //    float validScale = 0.7 ;  //每个库圈的有效数据比

    //    //    short ZH =0,Zdr = 0;
    //    //    int ZHoffset = m_radardata_out->radials.at(0).momentblock.at(ZHindex).momentheader.Offset;
    //    //    int ZHscale = m_radardata_out->radials.at(0).momentblock.at(ZHindex).momentheader.Scale;
    //    int ZDRoffset = m_radardata_out->radials.at(0).momentblock.at(ZDRindex).momentheader.Offset;
    //    int ZDRscale = m_radardata_out->radials.at(0).momentblock.at(ZDRindex).momentheader.Scale;

    //    //    vector<short>temp_Zdri;  //存储每个库圈满足条件的Zdr值
    //    //    vector<short>temp_ZdrC;  //存储所有库圈满足判断条件的Zdr值

    //    //    for(int i=0; i<m_LayerNum; i++){           //判断层数范围，具体取哪层数据进行计算
    //    //        if( m_radardata_out->commonBlock.cutconfig.at(i).Elevation >= 2.0 && m_radardata_out->commonBlock.cutconfig.at(i).Elevation <= 3.0){
    //    //            startlayer = i;
    //    //            endlayer = i;
    //    //            break;
    //    //        }
    //    //    }

    //    int startradial = -1, endradial = -1; //LGT_Radial = -1;
    //    float LGT_Azi = m_radardata_org->commonBlock.taskconfig.LGTAZ;
    //    //    float LGT_Azi = 28.0;               //手动取避雷针影响方位角（高淳）28.0°,，大丰（87°）范围限定在0~90°之间

    //    startlayer = 0;
    //    endlayer = m_radardata_org->commonBlock.cutconfig.size() - 1;

    //    float startAzi = LGT_Azi - 15.;    //避雷针左侧影响范围
    //    float endAzi = LGT_Azi + 15.;        //避雷针右侧影响范围
    //    CalradialNum = round((endAzi - startAzi) / m_AnglarResolution);     //避雷针影响范围对应的径向数，在qc.h里面添加全局变量
    //    if (startAzi < 0){
    //        startAzi = startAzi + 360;
    //    }

    //    if (endAzi >= 360){
    //        endAzi = endAzi - 360;
    //    }

    //    //计算第一根避雷针所在径向和影响区间的首尾径向
    //    if (m_radardata_out->commonBlock.taskconfig.ScanType == 0 || m_radardata_out->commonBlock.taskconfig.ScanType == 1){
    //        for(int El_radial = ElRadialIndex[0]; El_radial < (ElRadialIndex[0] + nRadialNum) ; El_radial++)
    //        {
    //            float Value1 = 15.0, Value2 = 15, Value3 = 15;
    //            if(fabs(startAzi - m_radardata_out->radials.at(El_radial).radialheader.Azimuth)<Value1)
    //            {
    //                Value1 = fabs(startAzi - m_radardata_out->radials.at(El_radial).radialheader.Azimuth);
    //                startradial = El_radial;
    //            }
    //            if(fabs(endAzi - m_radardata_out->radials.at(El_radial).radialheader.Azimuth)<Value2)
    //            {
    //                Value2 = fabs(endAzi - m_radardata_out->radials.at(El_radial).radialheader.Azimuth);
    //                endradial = El_radial;
    //            }
    //            if(fabs(LGT_Azi - m_radardata_out->radials.at(El_radial).radialheader.Azimuth)<Value3)
    //            {
    //                Value3 = fabs(LGT_Azi - m_radardata_out->radials.at(El_radial).radialheader.Azimuth);
    //                //            LGT_Radial = El_radial;
    //            }
    //        }
    //    }
    //    else if (m_radardata_out->commonBlock.taskconfig.ScanType == 2){
    //        float temp_az = m_radardata_out->radials.front().radialheader.Azimuth;
    //        while (temp_az >= 90){
    //            temp_az -= 90;
    //        }
    //        if (fabs(temp_az - LGT_Azi) < 15 || 90 - fabs(temp_az - LGT_Azi) < 15 ){
    //            startradial = 0;
    //            endradial = m_radardata_out->radials.size()-1;
    //        }
    //    }

    //    if (startlayer < 0 || endlayer < startlayer) return -1;

    //    //        int ValidCycle = 0;
    //    //        //计算ZDR方差、标准差
    //    //        int Sum_Zdr = 0;
    //    //        float SumVar_Zdr = 0;
    //    //        float Ave_Zdr = 0;
    //    //        float Std_Zdr = 0;
    //    //        for (int ilayer = startlayer; ilayer <= endlayer; ilayer++){

    //    //            for(int i_bin = 200; i_bin < 200 + CalcNum ; i_bin++)//
    //    //            {
    //    //                int count = 0;
    //    //                int SumBin_Zdr = 0;
    //    //                temp_Zdri.clear();
    //    //                if(endradial > startradial){
    //    //                    for (int El_radial = startradial; El_radial < endradial ; El_radial++)
    //    //                    {
    //    //                        ZH = (GetPointData(m_radardata_out ,El_radial,ZHindex, i_bin) - ZHoffset) / ZHscale;
    //    //                        Zdr = GetPointData(m_radardata_out ,El_radial,ZDRindex, i_bin);
    //    //                        //SNR = (GetPointData(m_radardata_out ,El_radial,SNRindex, i_bin) - SNRoffset) / SNRscale;
    //    //                        if(  ZH>5 && ZH<25 ) //判断条件
    //    //                        {
    //    //                            SumBin_Zdr += Zdr; //Zdr求和
    //    //                            temp_Zdri.push_back(Zdr);
    //    //                            count++;
    //    //                        }
    //    //                    }
    //    //                }
    //    //                else
    //    //                    if(endradial <= startradial){
    //    //                        for (int El_radial = startradial; El_radial < ElRadialIndex[ilayer] + nRadialNum ; El_radial++)
    //    //                        {

    //    //                            ZH = (GetPointData(m_radardata_out ,El_radial,ZHindex, i_bin) - ZHoffset) / ZHscale;
    //    //                            Zdr = GetPointData(m_radardata_out ,El_radial,ZDRindex, i_bin);
    //    //                            if(  ZH>5 && ZH<25 ) //判断条件
    //    //                            {
    //    //                                SumBin_Zdr += Zdr; //Zdr求和
    //    //                                temp_Zdri.push_back(Zdr);
    //    //                                count++;
    //    //                            }
    //    //                        }
    //    //                        for (int El_radial =  ElRadialIndex[ilayer]; El_radial < endradial ; El_radial++)
    //    //                        {
    //    //                            ZH = (GetPointData(m_radardata_out ,El_radial,ZHindex, i_bin) - ZHoffset) / ZHscale;
    //    //                            Zdr = GetPointData(m_radardata_out ,El_radial,ZDRindex, i_bin);
    //    //                            if(  ZH>5 && ZH<25 ) //判断条件
    //    //                            {
    //    //                                SumBin_Zdr += Zdr; //Zdr求和
    //    //                                temp_Zdri.push_back(Zdr);
    //    //                                count++;
    //    //                            }
    //    //                        }
    //    //                    }

    //    //                if (count >=  round(CalradialNum * validScale) ) //满足点数要求
    //    //                {
    //    //                    Sum_Zdr += SumBin_Zdr;
    //    //                    temp_ZdrC.insert(temp_ZdrC.end(),temp_Zdri.begin(),temp_Zdri.end());
    //    //                    ValidCycle++;
    //    //                }
    //    //                else//丢失点数超出范围，跳出循环
    //    //                {
    //    //                    break;
    //    //                }
    //    //            }
    //    //        }
    //    //        if(ValidCycle >= CalcNum * validScale){
    //    //            Ave_Zdr = Sum_Zdr / temp_ZdrC.size(); //Zdr求平均
    //    //            for (int j = 0; j < temp_ZdrC.size(); j++){
    //    //                SumVar_Zdr += pow(temp_ZdrC.at(j) - Ave_Zdr,2);//距平平方求和
    //    //            }
    //    //            Std_Zdr = sqrt(SumVar_Zdr / temp_ZdrC.size());//标准差

    //    //**********************************

    //    float a = m_radardata_org->commonBlock.taskconfig.LGTZDRA * ZDRscale;
    //    float b = m_radardata_org->commonBlock.taskconfig.LGTZDRB;
    //    m_radardata_out->commonBlock.taskconfig.LGTAZ = LGT_Azi;
    //    //        float a = 7 * ZDRscale;
    //    //        float b = 5;
    //    m_radardata_out->commonBlock.taskconfig.LGTZDRA = m_radardata_org->commonBlock.taskconfig.LGTZDRA;
    //    m_radardata_out->commonBlock.taskconfig.LGTZDRB = b;


    //    if(endradial > startradial){
    //        for (int times = 0; times < 4; times++){
    //            int i_startradial = startradial + times * (nRadialNum/4);//避雷针四个起始径向，间隔90°
    //            int i_endradial = endradial + times * (nRadialNum/4);    //避雷针四个结束径向
    //            int i_LGT_Radial = LGT_Radial + times * (nRadialNum/4);    //避雷针四个峰值径向
    //            //避雷针四个区域循环

    //            for (auto i_radial = i_startradial; i_radial < i_endradial; i_radial++){
    //                for (auto i_bin = 0; i_bin < nBinNum; i_bin++ ){
    //                    if(i_radial < ElRadialIndex[startlayer]+nRadialNum){             //第四根避雷针影响范围没有跨正北方向
    //                        short temp_Zdr = *((short*)&m_radardata_out->radials.at(i_radial).momentblock.at(ZDRindex).momentdata.at(i_bin * 2));
    //                        if (temp_Zdr != PREFILLVALUE){
    //                            temp_Zdr -= a/(sqrt(2*PI)*b) * exp(-pow(( m_radardata_out->radials.at(i_LGT_Radial).radialheader.Azimuth - m_radardata_out->radials.at(i_radial).radialheader.Azimuth),2)/(2*b*b));
    //                            memcpy(&m_radardata_out->radials.at(i_radial).momentblock.at(ZDRindex).momentdata.at(i_bin * 2),&temp_Zdr,2);
    //                        }

    //                    }
    //                    else{
    //                        int ii_radial = i_radial - nRadialNum; //  第四根避雷针影响范围跨正北方向
    //                        short temp_Zdr = *((short*)&m_radardata_out->radials.at(ii_radial).momentblock.at(ZDRindex).momentdata.at(i_bin * 2));
    //                        if (temp_Zdr != PREFILLVALUE){
    //                            temp_Zdr -= a/(sqrt(2*PI)*b) * exp(-pow(( i_LGT_Radial - i_radial),2)/(2*b*b));
    //                            memcpy(&m_radardata_out->radials.at(ii_radial).momentblock.at(ZDRindex).momentdata.at(i_bin * 2),&temp_Zdr,2);
    //                        }
    //                    }
    //                }

    //            }
    //        }

    //    }

    //    else {
    //        if(endradial <= startradial){       //第一根避雷针开始径向跨正北方向
    //            for (int times = 0; times < 4; times++){
    //                int i_startradial = startradial + times * (nRadialNum/4) - nRadialNum;//避雷针开始方位，间隔90°
    //                int i_endradial = endradial + times * (nRadialNum/4) ;//避雷针结束四个方位，间隔90°
    //                int i_LGT_Radial = LGT_Radial + times * (nRadialNum/4);//避雷针影响方位，间隔90°
    //                //避雷针四个区域循环
    //                for (auto i_radial = i_startradial; i_radial < i_endradial; i_radial++){
    //                    for (auto i_bin = 0; i_bin<nBinNum; i_bin++ ){
    //                        if(i_radial >= ElRadialIndex[startlayer]){               //第一根避雷针没有影响范围跨正北方向
    //                            short temp_Zdr = *((short*)&m_radardata_out->radials.at(i_radial).momentblock.at(ZDRindex).momentdata.at(i_bin * 2));
    //                            if (temp_Zdr != PREFILLVALUE){
    //                                temp_Zdr -= a/(sqrt(2*PI)*b) * exp(-pow((i_LGT_Radial- i_radial),2)/(2*b*b));
    //                                memcpy(&m_radardata_out->radials.at(i_radial).momentblock.at(ZDRindex).momentdata.at(i_bin * 2),&temp_Zdr,2);
    //                            }
    //                        }
    //                        else{
    //                            int ii_radial = i_radial + nRadialNum;
    //                            short temp_Zdr = *((short*)&m_radardata_out->radials.at(ii_radial).momentblock.at(ZDRindex).momentdata.at(i_bin * 2));
    //                            if (temp_Zdr != PREFILLVALUE){
    //                                temp_Zdr -= a/(sqrt(2*PI)*b) * exp(-pow((i_LGT_Radial- i_radial),2)/(2*b*b));
    //                                memcpy(&m_radardata_out->radials.at(ii_radial).momentblock.at(ZDRindex).momentdata.at(i_bin * 2),&temp_Zdr,2);
    //                            }
    //                        }
    //                    }
    //                }
    //            }
    //        }
    //    }

    //    return 0;
}

//计算KDP=========================================================================================================================
int CAlgoQC::CalculateKDP()
{
    if (m_DebugLevel <= 0)
    {
        set_time_str();
        cout << time_str;
        cout << " Algo_QC:: ";
        cout << "<CalculateKDP> ! " << endl;
    }
    if (!FunctionValid(m_params_calculateKDP))
    {
        return 0;
    }
//    if (m_radardata_out->commonBlock.siteconfig.RadarType == 4) return 0;

    for (int i_cut = 0; i_cut < m_radardata_out->commonBlock.cutconfig.size(); i_cut++)
    {
        if (indexPHDP.at(i_cut) == -1)
        {
            continue;
        }
        int KDPscale = 0, KDPoffset = 0;
        int CalcLength = 6;  //km
        int CalcNum = int(round(CalcLength / nBinWidthZ.at(i_cut))) / 2 * 2 + 1;
        int minNum = CalcNum * 0.8;
        if (m_DebugLevel <= 0)
        {
            set_time_str();
            cout << time_str;
            cout << " Algo_QC:: ";
            cout << "<CalculateKDP> : ";
            cout << " nBinWidth: " << nBinWidthZ.at(i_cut);
            cout << " CalcNum: " << CalcNum;
            cout << " minNum: " << minNum;
            cout << endl;
        }

        float temp_KDPf;
        unsigned short temp_KDPi;

        int PHDPoffset = m_radardata_out->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(indexPHDP.at(i_cut)).momentheader.Offset;
        int PHDPscale = m_radardata_out->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(indexPHDP.at(i_cut)).momentheader.Scale;

        if (indexKDP.at(i_cut) == -1)
        {
            KDPoffset = 10000;
            KDPscale = 100;
            indexKDP.at(i_cut) = m_radardata_out->radials.at(ElRadialIndex.at(i_cut)).momentblock.size();
            for (int i_radial = ElRadialIndex.at(i_cut); i_radial < ElRadialIndex.at(i_cut) + ElRadialNum.at(i_cut); i_radial ++)
            {
                m_radardata_out->radials.at(i_radial).radialheader.MomentNumber = m_radardata_out->radials.at(i_radial).radialheader.MomentNumber + 1;
                m_radardata_out->radials.at(i_radial).momentblock.resize(m_radardata_out->radials.at(i_radial).momentblock.size() + 1);
            }
        }
        else
        {
            KDPoffset = m_radardata_out->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(indexKDP.at(i_cut)).momentheader.Offset;
            KDPscale = m_radardata_out->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(indexKDP.at(i_cut)).momentheader.Scale;
        }
        for (int i_radial = ElRadialIndex.at(i_cut); i_radial < ElRadialIndex.at(i_cut) + ElRadialNum.at(i_cut); i_radial ++)
        {
            m_radardata_out->radials.at(i_radial).momentblock.at(indexKDP.at(i_cut)).momentheader.BinLength = 2 ;
            m_radardata_out->radials.at(i_radial).momentblock.at(indexKDP.at(i_cut)).momentheader.DataType = 11;
            m_radardata_out->radials.at(i_radial).momentblock.at(indexKDP.at(i_cut)).momentheader.Flags = PREFILLVALUE_SHORT;
            m_radardata_out->radials.at(i_radial).momentblock.at(indexKDP.at(i_cut)).momentheader.Length = m_radardata_out->radials.at(i_radial).momentblock.at(indexPHDP.at(i_cut)).momentheader.Length;
            m_radardata_out->radials.at(i_radial).momentblock.at(indexKDP.at(i_cut)).momentheader.Offset = KDPoffset;
            m_radardata_out->radials.at(i_radial).momentblock.at(indexKDP.at(i_cut)).momentheader.Scale = KDPscale ;
            m_radardata_out->radials.at(i_radial).momentblock.at(indexKDP.at(i_cut)).momentdata.resize(m_radardata_out->radials.at(i_radial).momentblock.at(indexPHDP.at(i_cut)).momentdata.size());
        }

        #pragma omp parallel for
        for (int i_radial = ElRadialIndex.at(i_cut); i_radial < ElRadialIndex.at(i_cut) + ElRadialNum.at(i_cut); i_radial ++)
        {
            for (int i_bin = 0; i_bin < nBinNumZ.at(i_cut); i_bin++)
            {
                int count = 0;
                int miscount = 0;
                unsigned short PHIDP = 0;
                long long sum_xy = 0;
                long long sum_x = 0;
                long long sum_y = 0;
                long long sum_xx = 0;
                for (int k = i_bin - CalcNum / 2; k < i_bin + 1 + CalcNum / 2; k++)
                {
                    if (k < 0 || k >= nBinNumZ.at(i_cut))
                    {
                        miscount++;
                    }
                    else
                    {
                        PHIDP = GetPointData(m_radardata_out, i_radial, indexPHDP.at(i_cut), k);
                        if (PHIDP <= INVALID_RSV)
                        {
                            miscount++;
                        }
                        else
                        {
                            sum_xy += k * PHIDP;
                            sum_x += k;
                            sum_y += PHIDP;
                            sum_xx += k * k;
                            count ++;
                        }
                    }
                    if (miscount > CalcNum - minNum)
                    {
                        break;
                    }
                }
                if (count >= minNum)
                {
                    //                    if (m_DebugLevel <= 0)
                    //                    {
                    //                        set_time_str();
                    //                        cout << time_str;
                    //                        cout << " Algo_QC:: ";
                    //                        cout << "<CalculateKDP> : ";
                    //                        cout << i_bin << " @ " << i_radial;
                    //                        cout << " count = " << count;
                    //                        cout << " x: "<< sum_x;
                    //                        cout << " y: "<< sum_y;
                    //                        cout << " xx: "<< sum_xx;
                    //                        cout << " xy: "<< sum_xy;
                    //                        cout << endl;
                    //                    }
                    if (sum_x == 0 || sum_y == 0 || sum_xx == 0 || sum_xy == 0)
                    {
                        temp_KDPf = PREFILLVALUE_FLOAT;
                    }
                    else
                    {
                        temp_KDPf = 1.0 * (sum_xy - 1.0 * sum_x * sum_y / count) \
                                    / (sum_xx -  1.0 * sum_x * sum_x / count) / PHDPscale / nBinWidthZ.at(i_cut) / 2;
                    }
                }
                else
                {
                    temp_KDPf = PREFILLVALUE_FLOAT;
                }
                if (temp_KDPf >= PREFILLVALUE_FLOAT - 1 && temp_KDPf <= PREFILLVALUE_FLOAT + 1)
                {
                    temp_KDPi = INVALID_BT;
                }
                if (temp_KDPf < 0.01)
                {
                    temp_KDPf = 0.01;
                }
                else
                {
                    temp_KDPi = temp_KDPf * KDPscale + KDPoffset;
                }
                memcpy(&m_radardata_out->radials.at(i_radial).momentblock.at(indexKDP.at(i_cut)).momentdata.at(i_bin * 2), &temp_KDPi, 2);

            }
        }
    }
    return 0;
}

//偏振量质控===================================================================================================================
int CAlgoQC::PolarQC()
{
    for (int i_cut = 0; i_cut < m_radardata_out->commonBlock.cutconfig.size(); i_cut++)
    {
        if (0 && indexSNR.at(i_cut) != -1)
        {
            int  threshold = 5;
            #pragma omp parallel for
            for (int iradial = ElRadialIndex.at(i_cut); iradial < ElRadialIndex.at(i_cut) + ElRadialNum.at(i_cut); iradial++)
            {
                for (int ibin = 0; ibin < nBinNumZ.at(i_cut); ibin++)
                {
                    if ((*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexSNR.at(i_cut)).momentdata.at(2 * ibin)) <= INVALID_RSV)
                    {
                        continue;
                    }
                    if ((1.0 * (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexSNR.at(i_cut)).momentdata.at(2 * ibin)) \
                            - m_radardata_out->radials.at(iradial).momentblock.at(indexSNR.at(i_cut)).momentheader.Offset) / m_radardata_out->radials.at(iradial).momentblock.at(SNRindex).momentheader.Scale < threshold)
                    {
                        if (indexZH.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexZH.at(i_cut)).momentdata.at(2 * ibin)) = INVALID_BT;
                        }
                        if (indexZDR.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexZDR.at(i_cut)).momentdata.at(2 * ibin)) = INVALID_BT;
                        }
                        if (indexROHV.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexROHV.at(i_cut)).momentdata.at(2 * ibin)) = INVALID_BT;
                        }
                        if (indexV.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexV.at(i_cut)).momentdata.at(2 * ibin)) = INVALID_BT;
                        }
                        if (indexPHDP.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexPHDP.at(i_cut)).momentdata.at(2 * ibin)) = INVALID_BT;
                        }
                        if (indexW.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexW.at(i_cut)).momentdata.at(2 * ibin)) = INVALID_BT;
                        }
                    }
                }
            }
        }

        if (indexPHDP.at(i_cut) != -1)
        {
            int  threshold = 5;
            int nBin = 4;
            vector<vector<bool>> valid;
            valid.resize(ElRadialNum.at(i_cut));
            for (int i = 0; i < valid.size(); i++)
            {
                valid.at(i).resize(nBinNumZ.at(i_cut));
            }

            #pragma omp parallel for
            for (int iradial = ElRadialIndex.at(i_cut); iradial < ElRadialIndex.at(i_cut) + ElRadialNum.at(i_cut); iradial++)
            {
                for (int j = 0; j < nBinNumZ.at(i_cut); j++)
                {
                    valid.at(iradial - ElRadialIndex.at(i_cut)).at(j) = true;
                    if (j < nBin)
                    {
                        valid.at(iradial - ElRadialIndex.at(i_cut)).at(j) = false;
                    }
                    int count = 0;
                    int sum = 0;
                    int ave = 0;
                    for (int ibin = max(0, j - nBin); ibin <= min(nBinNumZ.at(i_cut) - 1, j + nBin); ibin++)
                    {
                        if ((*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexPHDP.at(i_cut)).momentdata.at(2 * ibin)) > INVALID_RSV)
                        {
                            count ++;
                            sum += (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexPHDP.at(i_cut)).momentdata.at(2 * ibin));
                        }
                    }
                    if (count > nBin)
                    {
                        ave = sum / count;
                        float sum_pow = 0;
                        int scale = m_radardata_out->radials.at(iradial).momentblock.at(indexPHDP.at(i_cut)).momentheader.Scale;
                        for (int ibin = max(0, j - nBin); ibin <= min(nBinNumZ.at(i_cut) - 1, j + nBin); ibin++)
                        {
                            if ((*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexPHDP.at(i_cut)).momentdata.at(2 * ibin)) > INVALID_RSV)
                            {
                                sum_pow += pow(*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexPHDP.at(i_cut)).momentdata.at(2 * ibin) - ave, 2);
                            }
                        }
                        sum_pow /= count;
                        float sdphdp = sqrtf(sum_pow);
                        if (sdphdp > threshold * scale)
                        {
                            valid.at(iradial - ElRadialIndex.at(i_cut)).at(j) = false;
                        }
                        //                    *(unsigned short*)&m_radardata_out->radials.at(i).momentblock.at(indexW.at(i_cut)).momentdata.at(2*j) = sdphdp;
                    }
                }
            }
            for (int iradial = ElRadialIndex.at(i_cut); iradial < ElRadialIndex.at(i_cut) + ElRadialNum.at(i_cut); iradial++)
            {
                for (int j = 0; j < nBinNumZ.at(i_cut); j++)
                {
                    if (valid.at(iradial - ElRadialIndex.at(i_cut)).at(j) == false)
                    {
                        if (indexZH.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexZH.at(i_cut)).momentdata.at(2 * j)) = INVALID_BT;
                        }
                        if (indexZDR.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexZDR.at(i_cut)).momentdata.at(2 * j)) = INVALID_BT;
                        }
                        if (indexROHV.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexROHV.at(i_cut)).momentdata.at(2 * j)) = INVALID_BT;
                        }
                        if (indexV.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexV.at(i_cut)).momentdata.at(2 * j)) = INVALID_BT;
                        }
                        if (indexPHDP.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexPHDP.at(i_cut)).momentdata.at(2 * j)) = INVALID_BT;
                        }
                        if (indexW.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexW.at(i_cut)).momentdata.at(2 * j)) = INVALID_BT;
                        }
                    }
                }
            }
        }

        if (0 && indexZH.at(i_cut) != -1)
        {
            int  threshold = 5;   // plot the figure of sdZH and find the threshold
            int nBin = 4;
            vector<vector<bool>> valid;
            valid.resize(ElRadialNum.at(i_cut));
            for (int i = 0; i < valid.size(); i++)
            {
                valid.at(i).resize(nBinNumZ.at(i_cut));
            }

            #pragma omp parallel for
            for (int iradial = ElRadialIndex.at(i_cut); iradial < ElRadialIndex.at(i_cut) + ElRadialNum.at(i_cut); iradial++)
            {
                for (int j = 0; j < nBinNumZ.at(i_cut); j++)
                {
                    valid.at(iradial - ElRadialIndex.at(i_cut)).at(j) = true;
                    if (j < nBin)
                    {
                        valid.at(iradial - ElRadialIndex.at(i_cut)).at(j) = false;
                    }
                    int count = 0;
                    int sum = 0;
                    int ave = 0;
                    for (int ibin = max(0, j - nBin); ibin <= min(nBinNumZ.at(i_cut) - 1, j + nBin); ibin++)
                    {
                        if ((*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexZH.at(i_cut)).momentdata.at(2 * ibin)) > INVALID_RSV)
                        {
                            count ++;
                            sum += (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexZH.at(i_cut)).momentdata.at(2 * ibin));
                        }
                    }
                    if (count > nBin)
                    {
                        ave = sum / count;
                        float sum_pow = 0;
                        int scale = m_radardata_out->radials.at(iradial).momentblock.at(indexZH.at(i_cut)).momentheader.Scale;
                        for (int ibin = max(0, j - nBin); ibin <= min(nBinNumZ.at(i_cut) - 1, j + nBin); ibin++)
                        {
                            if ((*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexZH.at(i_cut)).momentdata.at(2 * ibin)) > INVALID_RSV)
                            {
                                sum_pow += pow(*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexZH.at(i_cut)).momentdata.at(2 * ibin) - ave, 2);
                            }
                        }
                        sum_pow /= count;
                        float sdzh = sqrtf(sum_pow);
                        if (sdzh > threshold * scale)
                        {
                            valid.at(iradial - ElRadialIndex.at(i_cut)).at(j) = false;
                        }
                        //                    *(unsigned short*)&m_radardata_out->radials.at(i).momentblock.at(indexW.at(i_cut)).momentdata.at(2*j) = sdphdp;
                    }
                }
            }
            for (int iradial = ElRadialIndex.at(i_cut); iradial < ElRadialIndex.at(i_cut) + ElRadialNum.at(i_cut); iradial++)
            {
                for (int j = 0; j < nBinNumZ.at(i_cut); j++)
                {
                    if (valid.at(iradial - ElRadialIndex.at(i_cut)).at(j) == false)
                    {
                        if (indexZH.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexZH.at(i_cut)).momentdata.at(2 * j)) = INVALID_BT;
                        }
                        if (indexZDR.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexZDR.at(i_cut)).momentdata.at(2 * j)) = INVALID_BT;
                        }
                        if (indexROHV.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexROHV.at(i_cut)).momentdata.at(2 * j)) = INVALID_BT;
                        }
                        if (indexV.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexV.at(i_cut)).momentdata.at(2 * j)) = INVALID_BT;
                        }
                        if (indexPHDP.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexPHDP.at(i_cut)).momentdata.at(2 * j)) = INVALID_BT;
                        }
                        if (indexW.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexW.at(i_cut)).momentdata.at(2 * j)) = INVALID_BT;
                        }
                    }
                }
            }
        }

        if (0 && indexROHV.at(i_cut) != -1)
        {
            #pragma omp parallel for
            for (int iradial = ElRadialIndex.at(i_cut); iradial < ElRadialIndex.at(i_cut) + ElRadialNum.at(i_cut); iradial++)
            {
                for (int j = 0; j < nBinNumZ.at(i_cut); j++)
                {
                    if ((*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexROHV.at(i_cut)).momentdata.at(2 * j)) <= INVALID_RSV)
                    {
                        continue;
                    }
                    if ((1.0 * (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexROHV.at(i_cut)).momentdata.at(2 * j)) \
                            - m_radardata_out->radials.at(iradial).momentblock.at(indexROHV.at(i_cut)).momentheader.Offset) / m_radardata_out->radials.at(iradial).momentblock.at(indexROHV.at(i_cut)).momentheader.Scale < 0.9)
                    {
                        if (indexPHDP.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexPHDP.at(i_cut)).momentdata.at(2 * j)) = INVALID_BT;
                        }
                        if (indexZDR.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexZDR.at(i_cut)).momentdata.at(2 * j)) = INVALID_BT;
                        }
                        if (indexZH.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexZH.at(i_cut)).momentdata.at(2 * j)) = INVALID_BT;
                        }
                        if (indexUnZH.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexUnZH.at(i_cut)).momentdata.at(2 * j)) = INVALID_BT;
                        }
                        if (indexROHV.at(i_cut) != -1)
                        {
                            (*(unsigned short *)&m_radardata_out->radials.at(iradial).momentblock.at(indexROHV.at(i_cut)).momentdata.at(2 * j)) = INVALID_BT;
                        }
                    }
                }
            }
        }
    }

    return 0;
}

//Zdr，PHDP订正=========================================================================================================================
int CAlgoQC::Zdr_PHDP_Correct()
{
    if (!FunctionValid(m_params_Zdr_PHDP_Correct))
    {
        return 0;
    }
//    if(m_radardata_out->commonBlock.siteconfig.RadarType != 75) return 0;

    //    [GCXR]
    //    path=../../..
    //    ZDRC=32
    //    ZDRCIN=11
    //    PHDPC=18680
    //    PHDPCIN=17820
    //    BlindBinNum=106

    if (0)
    {
        int ZHscale = 0, ZHoffset = 0;
        int ZDRscale = 0, ZDRoffset = 0;
        int PHDPscale = 0, PHDPoffset = 0;

        ZHoffset = m_radardata_out->radials.at(0).momentblock.at(ZHindex).momentheader.Offset;
        ZHscale = m_radardata_out->radials.at(0).momentblock.at(ZHindex).momentheader.Scale;
        ZDRoffset = m_radardata_out->radials.at(0).momentblock.at(ZDRindex).momentheader.Offset;
        ZDRscale = m_radardata_out->radials.at(0).momentblock.at(ZDRindex).momentheader.Scale;
        PHDPoffset = m_radardata_out->radials.at(0).momentblock.at(PHDPindex).momentheader.Offset;
        PHDPscale = m_radardata_out->radials.at(0).momentblock.at(PHDPindex).momentheader.Scale;

        int CalcLength = 3;  //盲区外，km
        int CalcNum = round(CalcLength / nBinWidth) / 2 * 2 + 1;
        int InvalidNum = 1 / nBinWidth ;
        float minScale = 0.8;
        //int InsideRange = 6;//盲区位置，km
        int Bin_Blind; // = round((InsideRange + 0.5) / nBinWidth)/2 * 2 + 1;//m_radardata_out->commonBlock.taskconfig.PulseWidth * 300000 / nBinWidth;
        int startlayer = -1, endlayer = -1;
        int iRadial_count = 0, iRadial_countIn = 0;
        vector<short>temp_PHDPi;
        vector<short>temp_Zdri;
        vector<short>temp_SNRi;
        vector<short>temp_bin_blind;

        vector<short>temp_ZdrC;
        vector<short>temp_PHDPC;
        vector<short>temp_ZdrCIn;
        vector<short>temp_PHDPCIn;
        float ZdrC = 0, ZdrCIn = 0;
        float PHDPC = 0, PHDPCIn = 0;
        bool isBreakLoop = false, isBreakLoopIn = false;
        //    if (SNRindex!=-1){
        for (int i = 0; i < m_LayerNum; i++)
        {
            if (m_radardata_out->commonBlock.cutconfig.at(i).Elevation >= 2.8 \
                    && m_radardata_out->commonBlock.cutconfig.at(i).Elevation <= 3.7)
            {
                startlayer = i;
                endlayer = i;
                break;
            }
        }

        if (startlayer >= 0 && endlayer >= startlayer)
        {
            for (int ilayer = startlayer; ilayer <= endlayer && !isBreakLoop; ilayer++)
            {
                //        temp_bin_blind.resize(nRadialNum);
                //        temp_bin_blind.assign(nRadialNum,-32768);
                temp_bin_blind.clear();
                for (int El_radial = ElRadialIndex[ilayer]; El_radial < (ElRadialIndex[ilayer] + nRadialNum); El_radial++)
                {
                    short diff_SNR  = -32768;
                    int bin_blind = 20;

                    for (int i_bin = 20; i_bin < 12.0 / nBinWidth ; i_bin ++)
                    {
                        short SNR_front = GetPointData(m_radardata_out, El_radial, SNRindex, i_bin - 1);
                        short SNR = GetPointData(m_radardata_out, El_radial, SNRindex, i_bin);
                        if (SNR_front != PREFILLVALUE && SNR != PREFILLVALUE && abs(SNR - SNR_front) > diff_SNR)
                        {
                            diff_SNR = abs(SNR - SNR_front);
                            bin_blind = i_bin;
                            //                    temp_bin_blind.at(El_radial - ElRadialIndex[ilayer]) = i_bin;
                        }
                    }
                    if (bin_blind > 20)
                    {
                        temp_bin_blind.push_back(bin_blind);
                    }
                }

                QuickSort(&temp_bin_blind[0], 0, temp_bin_blind.size() - 1); //排序
                if (temp_bin_blind.size() > 0)
                {
                    Bin_Blind = temp_bin_blind[nRadialNum / 2];
                }
                else
                {
                    Bin_Blind = 106;
                }

                bool bFind = false;
                temp_ZdrCIn.clear();
                temp_PHDPCIn.clear();
                //盲区内
                iRadial_countIn = 0;
                for (int El_radial = ElRadialIndex[ilayer]; El_radial < (ElRadialIndex[ilayer] + nRadialNum) && !isBreakLoopIn ; El_radial++)
                {
                    vector<short> temp;
                    temp.resize(m_radardata_out->radials.at(El_radial).momentblock.at(SNRindex).momentdata.size() / 2);
                    memcpy(&temp.at(0), &m_radardata_out->radials.at(El_radial).momentblock.at(SNRindex).momentdata.at(0), \
                           m_radardata_out->radials.at(El_radial).momentblock.at(SNRindex).momentdata.size());
                    temp_PHDPi.clear();
                    temp_Zdri.clear();
                    short ZH = 0, Zdr = 0, PHDP = 0;
                    int miscount = 0, count = 0;
                    //计算PHDP标准差
                    float Ave_PHDP = 0;
                    double Sum_PHDP = 0;
                    float Std_PHDP = 0;

                    for (int i_bin = Bin_Blind - 1; i_bin >= InvalidNum; i_bin--) //盲区内
                    {
                        ZH = (GetPointData(m_radardata_out, El_radial, ZHindex, i_bin) - ZHoffset) / ZHscale;
                        PHDP = GetPointData(m_radardata_out, El_radial, PHDPindex, i_bin);
                        Zdr = GetPointData(m_radardata_out, El_radial, ZDRindex, i_bin);
                        if (ZH < 10 || ZH > 20 || PHDP == PREFILLVALUE) //判断条件
                        {
                            miscount++;
                        }
                        else
                        {
                            Ave_PHDP += PHDP; //PHDP求和
                            temp_PHDPi.push_back(PHDP);
                            temp_Zdri.push_back(Zdr);
                            count ++;
                        }
                        if (miscount > (Bin_Blind - 1 - InvalidNum) * (1 - minScale)) //丢失点数超出范围，跳出循环
                        {
                            break;
                        }
                    }
                    if (count >= (Bin_Blind - 1 - InvalidNum) * 0.5) //满足点数要求
                    {
                        Ave_PHDP /= count; //PHDP求平均
                        for (int j = 0; j < count; j++)
                        {
                            Sum_PHDP += pow(temp_PHDPi.at(j) - Ave_PHDP, 2); //距平平方求和
                        }
                        Std_PHDP = sqrt(Sum_PHDP / count);//标准差
                        if (Std_PHDP > 0 && Std_PHDP / PHDPscale < 3.0) //判断PHDP标准差是否小于15°
                        {
                            temp_ZdrCIn.insert(temp_ZdrCIn.end(), temp_Zdri.begin(), temp_Zdri.end());
                            temp_PHDPCIn.insert(temp_PHDPCIn.end(), temp_PHDPi.begin(), temp_PHDPi.end());
                            iRadial_countIn++;
                        }
                        else
                        {
                            continue;
                        }
                    }

                }
                if (iRadial_countIn >= nRadialNum / 40)
                {
                    int Zdr_n = temp_ZdrCIn.size();

                    //                for ( int i = 0; i < Zdr_n; i++){
                    //                    ZdrCIn +=  temp_ZdrCIn.at(i);
                    //                    PHDPCIn += temp_PHDPCIn.at(i);
                    //                }
                    //                ZdrCIn /= Zdr_n;       //Zdr 求平均
                    //                PHDPCIn /= Zdr_n;     //PHDPC 求平均

                    QuickSort(&temp_ZdrCIn[0], 0, Zdr_n - 1); //排序
                    QuickSort(&temp_PHDPCIn[0], 0, Zdr_n - 1); //排序
                    //求中值
                    ZdrCIn = temp_ZdrCIn[(Zdr_n - 1) / 2] - (0.17 * ZDRscale + ZDRoffset);
                    PHDPCIn = temp_PHDPCIn[(Zdr_n - 1) / 2];

                    isBreakLoopIn = true;  //满足径向要求，逻辑值判断跳出多循环

                    bFind = true;
                }
                if (bFind == false)
                {
                    continue;
                }
                bFind = false;
                isBreakLoopIn = false;
                temp_ZdrC.clear();
                temp_PHDPC.clear();
                //盲区外
                iRadial_count = 0;
                for (int El_radial = ElRadialIndex[ilayer]; El_radial < (ElRadialIndex[ilayer] + nRadialNum) && !isBreakLoopIn ; El_radial++)
                {
                    temp_PHDPi.clear();
                    temp_Zdri.clear();
                    short ZH = 0, Zdr = 0, PHDP = 0;
                    int miscount = 0, count = 0;
                    //计算PHDP标准差
                    float Ave_PHDP = 0;
                    float Sum_PHDP = 0;
                    float Std_PHDP = 0;
                    for (int i_bin = Bin_Blind; i_bin < Bin_Blind + CalcNum ; i_bin++) //盲区外
                    {
                        ZH = (GetPointData(m_radardata_out, El_radial, ZHindex, i_bin) - ZHoffset) / ZHscale;
                        PHDP = GetPointData(m_radardata_out, El_radial, PHDPindex, i_bin);
                        Zdr = GetPointData(m_radardata_out, El_radial, ZDRindex, i_bin);
                        if (ZH < 15 || ZH > 20 || PHDP == PREFILLVALUE) //判断条件
                        {
                            miscount++;
                        }
                        else
                        {
                            Ave_PHDP += PHDP; //PHDP求和
                            temp_PHDPi.push_back(PHDP);
                            temp_Zdri.push_back(Zdr);
                            count ++;
                        }

                        if (miscount > CalcNum  * (1 - minScale)) //丢失点数超出范围，跳出循环
                        {
                            break;
                        }
                    }
                    if (count >= CalcNum * minScale) //满足点数要求
                    {
                        Ave_PHDP /= count; //PHDP求平均
                        for (int j = 0; j < count; j++)
                        {
                            Sum_PHDP += pow(temp_PHDPi.at(j) - Ave_PHDP, 2); //距平平方求和
                        }
                        Std_PHDP = sqrt(Sum_PHDP / count);//标准差
                        if (Std_PHDP > 0 && Std_PHDP / PHDPscale < 1.5) //判断PHDP标准差是否小于15°
                        {
                            temp_ZdrC.insert(temp_ZdrC.end(), temp_Zdri.begin(), temp_Zdri.end());
                            temp_PHDPC.insert(temp_PHDPC.end(), temp_PHDPi.begin(), temp_PHDPi.end());
                            iRadial_count++;
                        }
                        else
                        {
                            continue;
                        }

                    }

                }
                if (iRadial_count >= nRadialNum / 20)
                {
                    int Zdr_n = temp_ZdrC.size();

                    //                for ( int i = 0; i < Zdr_n; i++){
                    //                    ZdrC +=  temp_ZdrC.at(i);
                    //                    PHDPC += temp_PHDPC.at(i);
                    //                }
                    //                ZdrC /= Zdr_n;          //Zdr 求平均
                    //                PHDPC /= Zdr_n;        //PHDP 求平均

                    QuickSort(&temp_ZdrC[0], 0, Zdr_n - 1); //排序
                    QuickSort(&temp_PHDPC[0], 0, Zdr_n - 1); //排序
                    //求中值
                    ZdrC = temp_ZdrC[(Zdr_n - 1) / 2] - (0.17 * ZDRscale + ZDRoffset);
                    PHDPC = temp_PHDPC[(Zdr_n - 1) / 2];

                    isBreakLoopIn = true;    //满足径向要求，逻辑值判断跳出多循环
                    bFind = true;


                }
                if (bFind)
                {
                    m_radardata_out->commonBlock.taskconfig.ZDRCalibration = ZdrC;
                    m_radardata_out->commonBlock.taskconfig.PHIDPCalibration = PHDPC + PHDPoffset;
                    m_radardata_out->commonBlock.taskconfig.ZDRCalibrationInside = ZdrCIn;
                    m_radardata_out->commonBlock.taskconfig.PHIDPCalibrationInside = PHDPCIn + PHDPoffset;
                    m_radardata_out->commonBlock.taskconfig.BlindBinNum = Bin_Blind;

                    cout << "ZdrCIn:" << ZdrCIn << endl;
                    cout << "PHDPCIn:" << PHDPCIn << endl;

                    cout << "ZdrC:" << ZdrC << endl;
                    cout << "PHDPC:" << PHDPC << endl;
                    isBreakLoop = true;
                }
            }
        }
    }

    for (int i_cut = 0; i_cut < m_radardata_out->commonBlock.cutconfig.size(); i_cut++)
    {
        if (indexZH.at(i_cut) == -1 || indexPHDP.at(i_cut) == -1 || indexZDR.at(i_cut) == -1)
        {
            return -1;
        }

        int PHDPScale = m_radardata_out->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(indexPHDP.at(i_cut)).momentheader.Offset;
        int PHDPOffset = m_radardata_out->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(indexPHDP.at(i_cut)).momentheader.Scale;
        int ZHOffset = m_radardata_out->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(indexZH.at(i_cut)).momentheader.Offset;
        int ZHScale = m_radardata_out->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(indexZH.at(i_cut)).momentheader.Scale;
        int ZDROffset = m_radardata_out->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(indexZDR.at(i_cut)).momentheader.Offset;
        int ZDRScale = m_radardata_out->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(indexZDR.at(i_cut)).momentheader.Scale;

        //    m_radardata_out->commonBlock.taskconfig.PHIDPCalibration = -7900;
        //    m_radardata_out->commonBlock.taskconfig.PHIDPCalibrationInside = -8000;

        //#pragma omp parallel for
        for (auto i_radial = ElRadialIndex.at(i_cut); i_radial < ElRadialIndex.at(i_cut) + ElRadialNum.at(i_cut); i_radial++)
        {
            //            m_radardata_out->radials.at(i_radial).momentblock.at(indexPHDP.at(i_cut)).momentheader.Offset = PHDPOffset;
            for (auto i_bin = 0; i_bin < m_radardata_out->commonBlock.taskconfig.BlindBinNum; i_bin++)
            {
                unsigned short temp_Zdr = *((unsigned short *)&m_radardata_out->radials.at(i_radial).momentblock.at(indexZDR.at(i_cut)).momentdata.at(i_bin * 2));
                if (temp_Zdr > INVALID_RSV)
                {
                    temp_Zdr -= m_radardata_out->commonBlock.taskconfig.ZDRCalibrationInside;
                    memcpy(&m_radardata_out->radials.at(i_radial).momentblock.at(indexZDR.at(i_cut)).momentdata.at(i_bin * 2), &temp_Zdr, 2);
                }
                unsigned short temp_PHDP = *((unsigned short *)&m_radardata_out->radials.at(i_radial).momentblock.at(indexPHDP.at(i_cut)).momentdata.at(i_bin * 2));
                if (!strncmp(m_radardata_out->commonBlock.siteconfig.SiteCode, "PKXRD", 5)) //浦口数据8个库以内phdp有抖动，KDP异常，滤掉
                {
                    if (i_bin < 8)
                    {
                        temp_PHDP = INVALID_BT;
                    }
                }
                if (temp_PHDP > INVALID_RSV)
                {
                    temp_PHDP -= m_radardata_out->commonBlock.taskconfig.PHIDPCalibrationInside;
                    memcpy(&m_radardata_out->radials.at(i_radial).momentblock.at(indexPHDP.at(i_cut)).momentdata.at(i_bin * 2), &temp_PHDP, 2);
                }
            }
            for (auto i_bin = m_radardata_out->commonBlock.taskconfig.BlindBinNum; i_bin < nBinNum; i_bin++)
            {
                unsigned short temp_Zdr = *((unsigned short *)&m_radardata_out->radials.at(i_radial).momentblock.at(indexZDR.at(i_cut)).momentdata.at(i_bin * 2));
                if (temp_Zdr > INVALID_RSV)
                {
                    temp_Zdr -= m_radardata_out->commonBlock.taskconfig.ZDRCalibration;
                    memcpy(&m_radardata_out->radials.at(i_radial).momentblock.at(indexZDR.at(i_cut)).momentdata.at(i_bin * 2), &temp_Zdr, 2);
                }
                unsigned short temp_PHDP = *((unsigned short *)&m_radardata_out->radials.at(i_radial).momentblock.at(indexPHDP.at(i_cut)).momentdata.at(i_bin * 2));
                if (temp_PHDP > INVALID_RSV)
                {
                    temp_PHDP -= m_radardata_out->commonBlock.taskconfig.PHIDPCalibration;
                    memcpy(&m_radardata_out->radials.at(i_radial).momentblock.at(indexPHDP.at(i_cut)).momentdata.at(i_bin * 2), &temp_PHDP, 2);
                }
            }
        }
    }

    return 0;
}

//资料平滑=========================================================================================================================
int CAlgoQC::SmoothData(int dot)
{
    if (m_radardata_out == nullptr)                        // 如果数据加载失败，结束
    {
        return -1;
    }

    if (m_DebugLevel <= 0)
    {
        set_time_str();
        cout << time_str;
        cout << " Algo_QC:: ";
        cout << "<SmoothData> ! " << endl;
    }
    if (m_radardata_out->commonBlock.taskconfig.ScanType == 2)
    {
        SmoothDataRHI(dot);
    }
    else if (m_radardata_out->commonBlock.taskconfig.ScanType == 0 || m_radardata_out->commonBlock.taskconfig.ScanType == 1)
    {
        SmoothDataPPI(dot);
    }
    return 0;
}

int CAlgoQC::SmoothDataPPI(int dot)
{
    // 申请临时内存区，并进行初始化
    short *l_pnTempValue, *l_pnRadialNo;
    l_pnRadialNo = new short[dot]();
    l_pnTempValue = new short[dot * dot]();
    //l_pnRadialNo = (short *)calloc(sizeof(short), dot);
    //l_pnTempValue = (short *)calloc(sizeof(short), dot * dot);

    for (int i = 0; i < m_radardata_out->radials.size(); i++)
    {
        for (int j = 0; j < m_radardata_out->radials.front().radialheader.MomentNumber; j++)
        {
            //            Tempmomentline.reserve(nBinNum);
            Tempmomentline.resize(nBinNum);
            memcpy(&Tempmomentline[0], &m_radardata_out->radials[i].momentblock[j].momentdata[0], m_radardata_out->radials[i].momentblock[j].momentdata.size());
            tempmoment.momentline.assign(Tempmomentline.begin(), Tempmomentline.end());
            tempradial.radialline.push_back(tempmoment);
            tempmoment.momentline.clear();
            Tempmomentline.clear();
        }
        tempdata.datablock.push_back(tempradial);

        tempradial.radialline.clear();

    }

    int Offset = 0;
    int Scale = 0;
    int i_invalidCount = 0;
    short value = PREFILLVALUE;
    //#pragma omp parallel for
    for (int i_layer = 0; i_layer < (m_radardata_out->commonBlock.cutconfig.size()); i_layer++)
    {
        for (int i_radial = 0; i_radial < nRadialNum; i_radial++)
        {
            //            cout<<"SmoothData------"<<"current layer: "<<i_layer<<"   current radial: "<<i_radial<<endl;
            for (int i_dot = 0; i_dot < dot; i_dot++)
            {
                l_pnRadialNo[i_dot] = i_layer * nRadialNum + i_radial + i_dot - dot / 2;
                if (l_pnRadialNo[i_dot] < 0)
                {
                    l_pnRadialNo[i_dot] = l_pnRadialNo[i_dot] + nRadialNum;
                }
                if (l_pnRadialNo[i_dot] > m_radardata_out->radials.size() - 1)
                {
                    l_pnRadialNo[i_dot] = l_pnRadialNo[i_dot] - nRadialNum;
                }
            }
            //逐要素循环
            for (int i_moment = 0; i_moment < m_radardata_out->radials.front().radialheader.MomentNumber; i_moment++)
            {
                //逐库循环
                for (int i_bin = dot / 2; i_bin < nBinNum - dot / 2; i_bin++)
                {
                    if (tempdata.datablock.at(i_layer * nRadialNum + i_radial).radialline.at(i_moment).momentline.at(i_bin) == PREFILLVALUE)
                    {
                        continue;
                    }

                    // 取出参与中值滤波的dot×dot个点

                    for (int i_dot = 0; i_dot < dot; i_dot++)
                        for (int j_dot = 0; j_dot < dot; j_dot++)
                        {
                            l_pnTempValue[i_dot * dot + j_dot] = tempdata.datablock.at(l_pnRadialNo[i_dot]).radialline.at(i_moment).momentline.at(i_bin + j_dot - (dot - 1) / 2);
                        }

                    // 排序
                    QuickSort(l_pnTempValue, 0, dot * dot - 1);
                    i_invalidCount = 0;
                    value = PREFILLVALUE;
                    for (int i_dot = 0; i_dot < dot * dot ; i_dot++)
                    {
                        //if (((l_pnTempValue[i_dot] <5 && l_pnTempValue[i_dot]>=0) || l_pnTempValue[i_dot] == PREFILLVALUE))//无效值
                        if ((l_pnTempValue[i_dot] == PREFILLVALUE))//无效值
                        {
                            i_invalidCount += 1;
                        }
                    }
                    if (i_invalidCount / dot / dot > 0.8)
                    {
                        short value = PREFILLVALUE;
                        memcpy(&m_radardata_out->radials.at(i_layer * nRadialNum + i_radial).momentblock.at(i_moment).momentdata.at(2 * i_bin), &value, 2);
                    }
                    else
                    {
                        short value = l_pnTempValue[dot * dot / 2];
                        memcpy(&m_radardata_out->radials.at(i_layer * nRadialNum + i_radial).momentblock.at(i_moment).momentdata.at(2 * i_bin), &value, 2);
                    }
                }
            }
        }
    }
    // 释放临时内存
    delete[] l_pnTempValue;
    delete[] l_pnRadialNo;
    tempdata.datablock.clear();
    //delete m_radardata_temp;
    return 0;
}

int CAlgoQC::SmoothDataRHI(int dot)
{
    // 申请临时内存区，并进行初始化
    short *l_pnTempValue, *l_pnRadialNo;
    l_pnRadialNo = new short[dot]();
    l_pnTempValue = new short[dot * dot]();
    //l_pnRadialNo = (short *)calloc(sizeof(short), dot);
    //l_pnTempValue = (short *)calloc(sizeof(short), dot * dot);
    //WRADRAWDATA* m_radardata_temp(m_radardata_out);
    //==============================================================
    //    Tempmomentline.reserve(nBinNum);
    Tempmomentline.resize(nBinNum);
    for (int i = 0; i < m_radardata_out->radials.size(); i++)
    {
        for (int j = 0; j < m_radardata_out->radials.front().radialheader.MomentNumber; j++)
        {
            memcpy(&Tempmomentline[0], &m_radardata_out->radials[i].momentblock[j].momentdata[0], m_radardata_out->radials[i].momentblock[j].momentdata.size());
            tempmoment.momentline.assign(Tempmomentline.begin(), Tempmomentline.end());
            tempradial.radialline.push_back(tempmoment);
            tempmoment.momentline.clear();
        }
        tempdata.datablock.push_back(tempradial);
        tempradial.radialline.clear();
    }
    int testSize = tempdata.datablock.size();
    //========================================================

    // 逐径向处理
    for (int i_radial = dot / 2; i_radial < m_radardata_out->radials.size() - dot / 2; i_radial++)
    {
        // 获取滤波所需的各径向号
        for (int i_dot = 0; i_dot < dot; i_dot++)
        {
            l_pnRadialNo[i_dot] = i_radial + i_dot - dot / 2;
        }
        for (int i_moment = 0; i_moment < m_radardata_out->radials.front().radialheader.MomentNumber; i_moment++)
        {
            //            int Offset = m_radardata_out->radials.at(i_radial).momentblock.at(i_moment).momentheader.Offset;
            //            int Scale = m_radardata_out->radials.at(i_radial).momentblock.at(i_moment).momentheader.Scale;
            //逐库循环
            for (int i_bin = dot / 2; i_bin < nBinNum - dot / 2; i_bin++)
            {
                if (tempdata.datablock.at(i_radial).radialline.at(i_moment).momentline.at(i_bin) == PREFILLVALUE)
                {
                    continue;
                }

                // 取出参与中值滤波的dot×dot个点

                for (int i_dot = 0; i_dot < dot; i_dot++)
                    for (int j_dot = 0; j_dot < dot; j_dot++)
                    {
                        l_pnTempValue[i_dot * dot + j_dot] = tempdata.datablock.at(l_pnRadialNo[i_dot]).radialline.at(i_moment).momentline.at(i_bin + j_dot - dot / 2);
                        //                        l_pnTempValue[i_dot*dot+j_dot] = GetPointData(m_radardata_temp, l_pnRadialNo[i_dot],i_moment,i_bin);
                    }

                // 排序
                QuickSort(l_pnTempValue, 0, dot * dot - 1);
                int i_invalidCount = 0;
                for (int i_dot = 0; i_dot < dot * dot ; i_dot++)
                {
                    //if ((l_pnTempValue[i_dot] <5 && l_pnTempValue[i_dot]>=0))//无效值
                    //   i_invalidCount += 1;
                    if (l_pnTempValue[i_dot] == PREFILLVALUE)//无效值
                    {
                        i_invalidCount += 1;
                    }
                }
                short value = PREFILLVALUE;
                if (i_invalidCount / dot / dot > 0.6)
                {
                    value = PREFILLVALUE;
                }
                else
                {
                    value = l_pnTempValue[dot * dot / 2]; // 用中值替代
                }
                memcpy(&m_radardata_out->radials.at(i_radial).momentblock.at(i_moment).momentdata.at(2 * i_bin), &value, 2);
            }

        }
    }

    // 释放临时内存
    delete[] l_pnTempValue;
    delete[] l_pnRadialNo;
    tempdata.datablock.clear();
    //delete m_radardata_temp;
    return 0;
}

//径向平滑=========================================================================================================================
int CAlgoQC::RadialSmooth(int dot)
{
    if (m_radardata_out == nullptr)                        // 如果数据加载失败，结束
    {
        return -1;
    }

    if (m_DebugLevel <= 0)
    {
        set_time_str();
        cout << time_str;
        cout << " Algo_QC:: ";
        cout << "<RadialSmooth> ! " << endl;
    }
    // 申请临时内存区，并进行初始化
    short *l_pnTempValue;
    l_pnTempValue = new short[dot]();
    //l_pnTempValue = (short *)calloc(sizeof(short), dot);
    for (int i = 0; i < m_radardata_out->radials.size(); i++)
    {
        for (int j = 0; j < m_radardata_out->radials.front().radialheader.MomentNumber; j++)
        {
            //Tempmomentline.reserve(nBinNum);
            Tempmomentline.resize(nBinNum);
            memcpy(&Tempmomentline[0], &m_radardata_out->radials[i].momentblock[j].momentdata[0], m_radardata_out->radials[i].momentblock[j].momentdata.size());
            tempmoment.momentline.assign(Tempmomentline.begin(), Tempmomentline.end());
            tempradial.radialline.push_back(tempmoment);
            tempmoment.momentline.clear();
            //Tempmomentline.clear();
        }
        tempdata.datablock.push_back(tempradial);

        tempradial.radialline.clear();

    }
    //    #pragma omp parallel for num_threads(8)
    for (int i_radial = 0; i_radial < m_radardata_out->radials.size(); i_radial++)
    {
        //逐要素循环
        for (int i_moment = 0; i_moment < m_radardata_out->radials.front().radialheader.MomentNumber; i_moment++)
        {
            //逐库循环
            for (int i_bin = dot / 2; i_bin < nBinNum - dot / 2; i_bin++)
            {
                // 取出参与中值滤波的dot个点
                for (int i_dot = 0; i_dot < dot; i_dot++)
                {
                    l_pnTempValue[i_dot] = tempdata.datablock.at(i_radial).radialline.at(i_moment).momentline.at(i_bin + i_dot - (dot - 1) / 2);
                }

                // 排序
                QuickSort(l_pnTempValue, 0, dot - 1);
                int i_invalidCount = 0;
                short sum = 0;
                for (int i_dot = 0; i_dot < dot ; i_dot++)
                {
                    if (l_pnTempValue[i_dot] == PREFILLVALUE)//无效值
                    {
                        i_invalidCount += 1;
                    }
                    else
                    {
                        sum = sum + l_pnTempValue[i_dot];
                    }
                }
                if (i_invalidCount / dot > 0.7)
                {
                    short value = PREFILLVALUE;
                    memcpy(&m_radardata_out->radials.at(i_radial).momentblock.at(i_moment).momentdata.at(2 * i_bin), &value, 2);
                }
                else
                {
                    short value = l_pnTempValue[2];
                    //                    short value = sum / (dot - i_invalidCount);
                    memcpy(&m_radardata_out->radials.at(i_radial).momentblock.at(i_moment).momentdata.at(2 * i_bin), &value, 2);
                }
            }

        }
    }

    delete[] l_pnTempValue;
    tempdata.datablock.clear();
    return 0;
}

int CAlgoQC::FillingGap()
{
    int length = 500;
    //    int DotNum = 5;

    for (int icut = 0 ; icut < m_radardata_out->commonBlock.cutconfig.size(); icut++)
    {
        #pragma omp parallel for
        for (int i = ElRadialIndex.at(icut); i < ElRadialIndex.at(icut) + ElRadialNum.at(icut); i++)
        {
            for (int j = 0; j < m_radardata_out->radials.at(i).radialheader.MomentNumber; j++)
            {
                int DotNum;
                if (j == indexV.at(icut) || j == indexW.at(icut))
                {
                    DotNum = (floor)(length / m_radardata_out->commonBlock.cutconfig.at(icut).DopplerResolution);
                }
                else
                {
                    DotNum = (floor)(length / m_radardata_out->commonBlock.cutconfig.at(icut).LogResolution);
                }
                int BinNum = m_radardata_out->radials.at(i).momentblock.at(j).momentdata.size() / m_radardata_out->radials.at(i).momentblock.at(j).momentheader.BinLength;
                for (int ibin = 1 ; ibin < BinNum - 1; ibin++)
                {
                    if (*(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin * 2) > INVALID_RSV)
                    {
                        continue;
                    }
                    int front_Index = -9999;
                    int back_Index = -9999;
                    unsigned short value_front, value_back;

                    for (int ibin_in = max(0, ibin - 1); ibin_in >=  max(0, ibin - (DotNum)) ; ibin_in--)
                    {
                        if (*(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin_in * 2) > INVALID_RSV)
                        {
                            front_Index = ibin_in;
                            value_front = *(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin_in * 2);
                            break;
                        }
                    }
                    for (int ibin_in = min(BinNum - 1, ibin + 1); ibin_in <=  min(BinNum - 1, ibin + (DotNum)) ; ibin_in++)
                    {
                        if (*(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin_in * 2) > INVALID_RSV)
                        {
                            back_Index = ibin_in;
                            value_back = *(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin_in * 2);
                            break;
                        }
                    }
                    if (back_Index == -9999 || front_Index == -9999)
                    {
                        ibin += DotNum;
                        continue;
                    }
                    if (back_Index - front_Index <= DotNum)
                    {
                        *(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin * 2) = \
                                (value_front * (back_Index - ibin) + value_back * (ibin - front_Index)) \
                                / (back_Index - front_Index);
                    }
                }
            }
        }
    }

    for (int icut = 0 ; icut < m_radardata_out->commonBlock.cutconfig.size(); icut++)
    {
        #pragma omp parallel for
        for (int j = 0; j < m_radardata_out->radials.at(ElRadialIndex[icut]).radialheader.MomentNumber; j++)
        {
            int BinNum = m_radardata_out->radials.at(ElRadialIndex[icut]).momentblock.at(j).momentdata.size() / m_radardata_out->radials.at(ElRadialIndex[icut]).momentblock.at(j).momentheader.BinLength;
            for (int ibin = 0 ; ibin < BinNum; ibin++)
            {
                int DotNum = 3;
                for (int i = ElRadialIndex[icut]; i < ElRadialIndex[icut] + ElRadialNum[icut]; i++)
                {
                    if (*(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin * 2) > INVALID_RSV)
                    {
                        continue;
                    }
                    int front_Index = -9999;
                    int back_Index = -9999;
                    unsigned short value_front, value_back;

                    for (int iradial = i - 1; iradial >=  i - DotNum ; iradial--)
                    {
                        if (m_radardata_out->commonBlock.taskconfig.ScanType == 2 && iradial < 0)
                        {
                            break;
                        }
                        int i_radial = iradial < ElRadialIndex[icut] ? iradial + ElRadialNum[icut] : iradial;

                        if (*(unsigned short *)&m_radardata_out->radials.at(i_radial).momentblock.at(j).momentdata.at(ibin * 2) > INVALID_RSV)
                        {
                            front_Index = iradial;
                            value_front = *(unsigned short *)&m_radardata_out->radials.at(i_radial).momentblock.at(j).momentdata.at(ibin * 2);
                            break;
                        }
                    }
                    for (int iradial = i + 1; iradial <=  i + DotNum ; iradial++)
                    {
                        if (m_radardata_out->commonBlock.taskconfig.ScanType == 2 && iradial >= ElRadialIndex[icut] + ElRadialNum[icut])
                        {
                            break;
                        }
                        int i_radial = iradial >= ElRadialIndex[icut] + ElRadialNum[icut] ? iradial - ElRadialNum[icut] : iradial;
                        if (*(unsigned short *)&m_radardata_out->radials.at(i_radial).momentblock.at(j).momentdata.at(ibin * 2) > INVALID_RSV)
                        {
                            back_Index = iradial;
                            value_back = *(unsigned short *)&m_radardata_out->radials.at(i_radial).momentblock.at(j).momentdata.at(ibin * 2);
                            break;
                        }
                    }
                    if (back_Index == -9999 || front_Index == -9999)
                    {
                        i += DotNum;
                        continue;
                    }
                    if (back_Index - front_Index <= DotNum)
                    {
                        *(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin * 2) = \
                                (value_front * (back_Index - i) + value_back * (i - front_Index)) \
                                / (back_Index - front_Index);
                    }
                }
            }
        }
    }
    for (int icut = 0 ; icut < m_radardata_out->commonBlock.cutconfig.size(); icut++)
    {
        #pragma omp parallel for
        for (int i = 0; i < m_radardata_out->radials.size(); i++)
        {
            for (int j = 0; j < m_radardata_out->radials.at(i).radialheader.MomentNumber; j++)
            {
                int DotNum;
                if (j == indexV.at(icut) || j == indexW.at(icut))
                {
                    DotNum = (floor)(length / m_radardata_out->commonBlock.cutconfig.at(icut).DopplerResolution);
                }
                else
                {
                    DotNum = (floor)(length / m_radardata_out->commonBlock.cutconfig.at(icut).LogResolution);
                }
                int BinNum = m_radardata_out->radials.at(i).momentblock.at(j).momentdata.size() / m_radardata_out->radials.at(i).momentblock.at(j).momentheader.BinLength;
                for (int ibin = 1 ; ibin < BinNum - 1; ibin++)
                {
                    if (*(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin * 2) > INVALID_RSV)
                    {
                        continue;
                    }
                    int front_Index = -9999;
                    int back_Index = -9999;
                    unsigned short value_front, value_back;

                    for (int ibin_in = max(0, ibin - 1); ibin_in >=  max(0, ibin - (DotNum)) ; ibin_in--)
                    {
                        if (*(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin_in * 2) > INVALID_RSV)
                        {
                            front_Index = ibin_in;
                            value_front = *(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin_in * 2);
                            break;
                        }
                    }
                    for (int ibin_in = min(BinNum - 1, ibin + 1); ibin_in <=  min(BinNum - 1, ibin + (DotNum)) ; ibin_in++)
                    {
                        if (*(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin_in * 2) > INVALID_RSV)
                        {
                            back_Index = ibin_in;
                            value_back = *(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin_in * 2);
                            break;
                        }
                    }
                    if (back_Index == -9999 || front_Index == -9999)
                    {
                        ibin += DotNum;
                        continue;
                    }
                    if (back_Index - front_Index <= DotNum)
                    {
                        *(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin * 2) = \
                                (value_front * (back_Index - ibin) + value_back * (ibin - front_Index)) \
                                / (back_Index - front_Index);
                    }
                }
            }
        }
    }
    return 0;
}

int CAlgoQC::VOutlierFiltering()
{
    int length = 150;

    for (int icut = 0; icut < m_radardata_out->commonBlock.cutconfig.size(); icut++)
    {
        if (indexV.at(icut) == -1)
        {
            continue;
        }
        int DotNum = (floor)(length / m_radardata_out->commonBlock.cutconfig.at(icut).DopplerResolution);
        if (DotNum == 0)
        {
            continue;
        }
        int scale = *(unsigned short *)&m_radardata_out->radials.at(ElRadialIndex[icut]).momentblock.at(indexV.at(icut)).momentheader.Scale;
        int offset = *(unsigned short *)&m_radardata_out->radials.at(ElRadialIndex[icut]).momentblock.at(indexV.at(icut)).momentheader.Offset;
        #pragma omp parallel for
        for (int i = ElRadialIndex[icut]; i < ElRadialIndex[icut] + ElRadialNum[icut]; i++)
        {
            int BinNum = m_radardata_out->radials.at(i).momentblock.at(indexV.at(icut)).momentdata.size() \
                         / m_radardata_out->radials.at(i).momentblock.at(indexV.at(icut)).momentheader.BinLength;
            for (int idot = 1; idot < DotNum ; idot++)
            {
                for (int ibin = 1 ; ibin < BinNum - idot; ibin++)
                {
                    if (*(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(indexV.at(icut)).momentdata.at(ibin * 2) <= INVALID_RSV)
                    {
                        continue;
                    }
                    //            bool flag = true;
                    unsigned short value = *(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(indexV.at(icut)).momentdata.at(ibin * 2);
                    unsigned short value2 = *(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(indexV.at(icut)).momentdata.at((ibin + idot - 1) * 2);
                    unsigned short value_front = *(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(indexV.at(icut)).momentdata.at(ibin * 2 - 2);
                    unsigned short value_back = *(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(indexV.at(icut)).momentdata.at((ibin + idot - 1) * 2 + 2);
                    unsigned short front = value_front - value;
                    unsigned short back = value2 - value_back;
                    unsigned short threshold = 10 * scale;
                    //            for (int ibin_in = max(0, ibin-(DotNum/2)); ibin_in <  min(BinNum-1,ibin + (DotNum/2)) ;ibin_in++){
                    if (int(fabs(front)) > threshold && int(fabs(back)) > threshold)
                    {
                        if (front * back > 0 &&  fabs(value - offset)  < threshold)
                        {
                            continue;
                        }
                        else
                        {
                            *(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(indexV.at(icut)).momentdata.at(ibin * 2) = INVALID_BT;
                        }
                    }
                }
            }
        }
    }


    return 0;
}

int CAlgoQC::OutlierFiltering()
{
    int DotNum = 3;
    int MissNum = 5;
    #pragma omp parallel for
    for (int i = 0; i < m_radardata_out->radials.size(); i++)
    {
        for (int j = 0; j < m_radardata_out->radials.at(i).radialheader.MomentNumber; j++)
        {
            int BinNum = m_radardata_out->radials.at(i).momentblock.at(j).momentdata.size() / m_radardata_out->radials.at(i).momentblock.at(j).momentheader.BinLength;
            for (int ibin = 0 ; ibin < BinNum; ibin++)
            {
                if (*(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin * 2) <= INVALID_RSV)
                {
                    continue;
                }
                bool flag = true;

                for (int ibin_in = max(0, ibin - (DotNum - 1 + MissNum)); ibin_in <=  max(0, ibin - (DotNum)) ; ibin_in++)
                {
                    if (*(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin_in * 2) > INVALID_RSV)
                    {
                        flag = false;
                        break;
                    }
                }
                for (int ibin_in = min(BinNum - 1, ibin + (DotNum - 1 + MissNum)); ibin_in >=  min(BinNum - 1, ibin + (DotNum)) ; ibin_in--)
                {
                    if (*(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin_in * 2) > INVALID_RSV)
                    {
                        flag = false;
                        break;
                    }
                }
                if (flag)
                {
                    for (int ibin_in = max(0, ibin - (DotNum - 1)); ibin_in <=  min(BinNum - 1, ibin + (DotNum - 1)) ; ibin_in++)
                    {
                        *(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin_in * 2) = INVALID_BT;
                    }
                }
            }
        }
    }
    //    DotNum = 10;
    //    MissNum = 15;
    //#pragma omp parallel for
    //    for (int i=0; i<m_radardata_out->radials.size(); i++)
    //    {
    //        for (int j=0; j<m_radardata_out->radials.at(i).radialheader.MomentNumber; j++)
    //        {
    //            int BinNum = m_radardata_out->radials.at(i).momentblock.at(j).momentdata.size() / m_radardata_out->radials.at(i).momentblock.at(j).momentheader.BinLength;
    //            for (int ibin = 0 ; ibin < BinNum; ibin++ )
    //            {
    //                if ( *(unsigned short*)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin*2) <= INVALID_RSV ) continue;
    //                bool flag = true;

    //                for (int ibin_in = max(0, ibin-(DotNum-1+MissNum)); ibin_in <=  max(0,ibin - (DotNum)) ;ibin_in++){
    //                    if ( *(unsigned short*)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin_in*2) > INVALID_RSV ) {
    //                        flag = false;
    //                        break;
    //                    }
    //                }
    //                for (int ibin_in = min(BinNum-1, ibin+(DotNum-1+MissNum)); ibin_in >=  min(BinNum-1,ibin + (DotNum)) ;ibin_in--){
    //                    if ( *(unsigned short*)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin_in*2) > INVALID_RSV ) {
    //                        flag = false;
    //                        break;
    //                    }
    //                }
    //                if (flag) {
    //                    for (int ibin_in = max(0,ibin - (DotNum-1)); ibin_in <=  min(BinNum-1,ibin + (DotNum-1)) ;ibin_in++){
    //                        *(unsigned short*)&m_radardata_out->radials.at(i).momentblock.at(j).momentdata.at(ibin_in*2) = INVALID_BT;
    //                    }
    //                }
    //            }
    //        }
    //    }
    return 0;
}

/*
fast two-dimensional phase-unwrapping algorithm based on sorting by reliability following a noncontinuous path
*/

unsigned short CAlgoQC::code(double value, int offset, int scale)
{
    if (fabs(value) > 1e-5)
    {
        return (unsigned short)(value * scale + offset);
    }
    else
    {
        return INVALID_BT;
    }
}

double CAlgoQC::decode(unsigned short temp, int offset, int scale)
{
    if (temp <= INVALID_RSV)
    {
        return  0;
    }
    else
    {
        return (temp - offset) / (scale * 1.0);
    }
}

int CAlgoQC::UnflodVel_phase_unwrapping()
{
    if (!FunctionValid(m_params_UnflodVel))
    {
        return 0;
    }
    for (int i_cut = 0; i_cut < m_radardata_out->commonBlock.cutconfig.size(); ++i_cut)
    {
        if (indexV.at(i_cut) == -1)
        {
            continue;
        }
        if (m_VPPI != NULL)
        {
            free(m_VPPI);
            m_VPPI  = NULL;
        }
        if (m_unwarpV != NULL)
        {
            free(m_unwarpV);
            m_unwarpV  = NULL;
        }
        if (m_inputMask != NULL)
        {
            free(m_inputMask);
            m_inputMask  = NULL;
        }
        m_velny     = m_radardata_out->commonBlock.cutconfig.at(i_cut).NyquistSpeed;    // 最大不模糊速度(m/s，0~100)
        if (m_velny <= 0)
        {
            continue;
        }
        m_scale     = PI / m_velny;
        int Voffset = m_radardata_out->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(indexV.at(i_cut)).momentheader.Offset;
        int Vscale  = m_radardata_out->radials.at(ElRadialIndex.at(i_cut)).momentblock.at(indexV.at(i_cut)).momentheader.Scale;
        m_XNum      = ElRadialNum.at(i_cut);        // AzNum
        m_YNum      = nBinNumV.at(i_cut);           // BinNum
        m_VPPI      = (double *)calloc(m_XNum * m_YNum, sizeof(double));
        m_unwarpV   = (double *)calloc(m_XNum * m_YNum, sizeof(double));
        m_inputMask = (unsigned char *)calloc(m_XNum * m_YNum, sizeof(unsigned char));

        // m_VPPI解码 + m_unwarpV初始化 + m_inputMask设置
        for (int i = 0; i < m_XNum * m_YNum; ++i)
        {
            m_VPPI[i]       = 0;
            m_unwarpV[i]    = 0;
        }
        for (int i_radial = 0; i_radial < ElRadialNum[i_cut]; i_radial++)
        {
            int radialNum   = i_radial + ElRadialIndex[i_cut];
            for (int i_bin = 0; i_bin < nBinNumV.at(i_cut); i_bin++)
            {
                unsigned short value = GetPointData(m_radardata_out, radialNum, indexV.at(i_cut), i_bin);
                if (value > INVALID_RSV)
                {
                    m_inputMask[i_bin * m_XNum + i_radial]  = NOMASK;
                    m_VPPI[i_bin * m_XNum + i_radial]   = decode(value, Voffset, Vscale);
                    m_VPPI[i_bin * m_XNum + i_radial]   *= m_scale;
                }
                else
                {
                    m_inputMask[i_bin * m_XNum + i_radial] = MASK;
                }
            }
        }
//        // m_VPPI缩放 + m_unwarpV初始化 + m_inputMask设置
//        for (int i = 0; i < m_XNum*m_YNum; ++i){
//            m_unwarpV[i]    = 0;
//            if (m_inputMask[i] == NOMASK)
//                m_VPPI[i]       *= m_scale;
//        }
        // 相位展开退模糊
        unwrap2D(m_VPPI, m_unwarpV, m_inputMask, m_XNum, m_YNum, m_XConnect, m_YConnect);

        // code 4 unwarpV
        //m_radardata_out->commonBlock.cutconfig.at(i_cut).NyquistSpeed   *= 3;       // 修改最大不模糊速度值,参数值由pixel->increment决定
        for (int i_radial = 0; i_radial < ElRadialNum[i_cut]; ++i_radial)
        {
            int radialNum   = i_radial + ElRadialIndex[i_cut];
            for (int i_bin = 0; i_bin < nBinNumV.at(i_cut); ++i_bin)
            {
                double tmpValue = m_unwarpV[i_bin * ElRadialNum.at(i_cut) + i_radial];
                if (m_scale != 0)
                {
                    tmpValue    /= m_scale;
                }
                unsigned short value = INVALID_BT;
                if (!m_inputMask[i_bin * ElRadialNum.at(i_cut) + i_radial])
                {
                    value = (unsigned short)(tmpValue * Vscale + Voffset);
                }
//                unsigned short value    = code(tmpValue, Voffset, Vscale);
                memcpy(&m_radardata_out->radials.at(radialNum).momentblock.at(indexV.at(i_cut)).momentdata.at(2 * i_bin), &value, 2);
            }
        }
        // free calloc
        if (m_VPPI != NULL)
        {
            free(m_VPPI);
            m_VPPI  = NULL;
        }
        if (m_unwarpV != NULL)
        {
            free(m_unwarpV);
            m_unwarpV  = NULL;
        }
        if (m_inputMask != NULL)
        {
            free(m_inputMask);
            m_inputMask  = NULL;
        }
    }
    return 0;
}

void CAlgoQC::unwrap2D(double *wrapped_image, double *unwrappedImage, unsigned char *input_mask, int image_width, int image_height, int wrap_around_x, int wrap_around_y)
{
    params_t params = {TWOPI, wrap_around_x, wrap_around_y};
    unsigned char *extended_mask;
    PIXELM *pixel;
    EDGE *edge;
    int image_size  = image_height * image_width;
    int No_of_Edges_initially   = 2 * image_width * image_height;

    extended_mask   = (unsigned char *)calloc(image_size, sizeof(unsigned char));
    pixel           = (PIXELM *)calloc(image_size, sizeof(PIXELM));
    edge            = (EDGE *)calloc(No_of_Edges_initially, sizeof(EDGE));

    extend_mask(input_mask, extended_mask, image_width, image_height, &params);
    initialisePIXELs(wrapped_image, input_mask, extended_mask, pixel, image_width, image_height);
    calculate_reliability(wrapped_image, pixel, image_width, image_height, &params);
    horizontalEDGEs(pixel, edge, image_width, image_height, &params);
    verticalEDGEs(pixel, edge, image_width, image_height, &params);

    if (params.no_of_edges != 0)
    {
        // sort the EDGEs depending on their reliability.
        // the PIXELs with higher reliability (smaller value) unwrap first
        quicker_sort(edge, edge + params.no_of_edges - 1);
    }

    // gather PIXELs into group
    gatherPIXELs(edge, &params);

    unwrapImage(pixel, image_width, image_height);
    maskImage(pixel, input_mask, image_width, image_height);

    // copy the image from PIXELM structure to the unwrapped phase array
    returnImage(pixel, unwrappedImage, image_width, image_height);

    free(edge);
    free(pixel);
    free(extended_mask);
}

void CAlgoQC::extend_mask(unsigned char *input_mask, unsigned char *extended_mask, int image_width, int image_height, params_t *params)
{
    int i, j;
    int image_width_plus_one    = image_width + 1;
    int image_width_minus_one   = image_width - 1;
    unsigned char *IMP  = input_mask    + image_width + 1;      // input mask pointer
    unsigned char *EMP  = extended_mask + image_width + 1;      // extended mask pointer

    // extend the mask for the image except borders
    for (i = 1; i < image_height - 1; ++i)
    {
        for (j = 1; j < image_width - 1; ++j)
        {
            if ((*IMP) == NOMASK && (*(IMP + 1) == NOMASK) && (*(IMP - 1) == NOMASK) &&
                    (*(IMP + image_width) == NOMASK) && (*(IMP - image_width) == NOMASK) &&
                    (*(IMP - image_width_minus_one) == NOMASK) && (*(IMP - image_width_plus_one) == NOMASK) &&
                    (*(IMP + image_width_minus_one) == NOMASK) && (*(IMP + image_width_plus_one) == NOMASK))
            {
                *EMP    = NOMASK;
            }
            ++EMP;
            ++IMP;
        }
        EMP += 2;
        IMP += 2;
    }

    if (params->x_connectivity == 1)
    {
        // extend the mask for the right border of the image
        IMP = input_mask    + 2 * image_width - 1;
        EMP = extended_mask + 2 * image_width - 1;
        for (i = 1; i < image_height - 1; ++i)
        {
            if ((*IMP) == NOMASK && (*(IMP - 1) == NOMASK) && (*(IMP + 1) == NOMASK) &&
                    (*(IMP + image_width) == NOMASK) && (*(IMP - image_width) == NOMASK) &&
                    (*(IMP - image_width - 1) == NOMASK) && (*(IMP - image_width + 1) == NOMASK) &&
                    (*(IMP + image_width - 1) == NOMASK) && (*(IMP - 2 * image_width + 1) == NOMASK))
            {
                *EMP    = NOMASK;
            }
            EMP += image_width;
            IMP += image_width;
        }
        // extend the mask for the left border of the image
        IMP = input_mask    + image_width;
        EMP = extended_mask + image_width;
        for (i = 1; i < image_height - 1; ++i)
        {
            if ((*IMP) == NOMASK && (*(IMP - 1) == NOMASK) && (*(IMP + 1) == NOMASK) &&
                    (*(IMP + image_width) == NOMASK) && (*(IMP - image_width) == NOMASK) &&
                    (*(IMP - image_width + 1) == NOMASK) && *(IMP + image_width + 1) == NOMASK &&
                    (*(IMP + image_width - 1) == NOMASK) && (*(IMP + 2 * image_width - 1) == NOMASK))
            {
                *EMP    = NOMASK;
            }
            EMP += image_width;
            IMP += image_width;
        }
    }

    if (params->y_connectivity == 1)
    {
        // extend the mask for the top border of the image
        IMP = input_mask    + 1;
        EMP = extended_mask + 1;
        for (i = 1; i < image_width - 1; ++i)
        {
            if ((*IMP) == NOMASK && (*(IMP - 1) == NOMASK) && (*(IMP + 1) == NOMASK) &&
                    (*(IMP + image_width) == NOMASK) && (*(IMP + image_width * (image_height - 1)) == NOMASK) &&
                    (*(IMP + image_width + 1) == NOMASK) && (*(IMP + image_width - 1) == NOMASK) &&
                    (*(IMP + image_width * (image_height - 1) - 1) == NOMASK) && (*(IMP + image_width * (image_height - 1) + 1) == NOMASK))
            {
                *EMP    = NOMASK;
            }
            EMP++;
            IMP++;
        }

        // extend the mask for the bottom border of the image
        IMP = input_mask    + image_width * (image_height - 1) + 1;
        EMP = extended_mask + image_width * (image_height - 1) + 1;
        for (i = 1; i < image_width - 1; ++i)
        {
            if ((*IMP) == NOMASK && (*(IMP - 1) == NOMASK) && (*(IMP + 1) == NOMASK) &&
                    (*(IMP - image_width) == NOMASK) && (*(IMP - image_width - 1) == NOMASK) && (*(IMP - image_width + 1) == NOMASK) &&
                    (*(IMP - image_width * (image_height - 1)) == NOMASK) &&
                    (*(IMP - image_width * (image_height - 1) - 1) == NOMASK) &&
                    (*(IMP - image_width * (image_height - 1) + 1) == NOMASK))
            {
                *EMP    = NOMASK;
            }
            EMP++;
            IMP++;
        }
    }
}

void CAlgoQC::initialisePIXELs(double *wrapped_image, unsigned char *input_mask, unsigned char *extended_mask, PIXELM *pixel, int image_width, int image_height)
{
    PIXELM *pixel_pointer   = pixel;
    double *wrapped_image_pointer       = wrapped_image;
    unsigned char *input_mask_pointer   = input_mask;
    unsigned char *extended_mask_pointer = extended_mask;
    int i, j;

    for (i = 0; i < image_height; i++)
    {
        for (j = 0; j < image_width; j++)
        {
            pixel_pointer->increment                = 0;
            pixel_pointer->number_of_pixels_in_group = 1;
            pixel_pointer->value                    = *wrapped_image_pointer;
            pixel_pointer->reliability              = 9999999. + rand();
            pixel_pointer->input_mask               = *input_mask_pointer;
            pixel_pointer->extended_mask            = *extended_mask_pointer;
            pixel_pointer->head                     = pixel_pointer;
            pixel_pointer->last                     = pixel_pointer;
            pixel_pointer->next                     = nullptr;
            pixel_pointer->new_group                = 0;
            pixel_pointer->group                    = -1;
            pixel_pointer++;
            wrapped_image_pointer++;
            input_mask_pointer++;
            extended_mask_pointer++;
        }
    }
}

void CAlgoQC::calculate_reliability(double *wrappedImage, PIXELM *pixel, int image_width, int image_height, params_t *params)
{
    int image_width_plus_one    = image_width + 1;
    int image_width_minus_one   = image_width - 1;
    PIXELM *pixel_pointer       = pixel + image_width_plus_one;
    double *WIP                 = wrappedImage + image_width_plus_one;
    double H, V, D1, D2;
    int i, j;

    for (i = 1; i < image_height - 1; ++i)
    {
        for (j = 1; j < image_width - 1; ++j)
        {
            if (pixel_pointer->extended_mask == NOMASK)
            {
                H   = wrap(*(WIP - 1) - *WIP) - wrap(*WIP - * (WIP + 1));
                V   = wrap(*(WIP - image_width) - *WIP) - wrap(*WIP - * (WIP + image_width));
                D1  = wrap(*(WIP - image_width_plus_one) - *WIP) - wrap(*WIP - * (WIP + image_width_plus_one));
                D2  = wrap(*(WIP - image_width_minus_one) - *WIP) - wrap(*WIP - * (WIP + image_width_minus_one));
                pixel_pointer->reliability  = H * H + V * V + D1 * D1 + D2 * D2;
            }
            pixel_pointer++;
            WIP++;
        }
        pixel_pointer += 2;
        WIP += 2;
    }

    if (params->x_connectivity == 1)
    {
        // calculating the reliability for the left border of the image
        PIXELM *pixel_pointer   = pixel + image_width;
        double *WIP             = wrappedImage + image_width;

        for (i = 1; i < image_height - 1; ++i)
        {
            if (pixel_pointer->extended_mask == NOMASK)
            {
                H   = wrap(*(WIP + image_width - 1) - *WIP) - wrap(*WIP - * (WIP + 1));
                V   = wrap(*(WIP - image_width) - *WIP) - wrap(*WIP - * (WIP + image_width));
                D1  = wrap(*(WIP - 1) - *WIP) - wrap(*WIP - * (WIP + image_width_plus_one));
                D2  = wrap(*(WIP - image_width_minus_one) - *WIP) - wrap(*WIP - * (WIP + 2 * image_width - 1));
                pixel_pointer->reliability  = H * H + V * V + D1 * D1 + D2 * D2;
            }
            pixel_pointer += image_width;
            WIP += image_width;
        }

        // calculating the reliability for the right border of the image
        pixel_pointer   = pixel + 2 * image_width - 1;
        WIP             = wrappedImage + 2 * image_width - 1;

        for (i = 1; i < image_height - 1; ++i)
        {
            if (pixel_pointer->extended_mask == NOMASK)
            {
                H   = wrap(*(WIP - 1) - *WIP) - wrap(*WIP - * (WIP - image_width_minus_one));
                V   = wrap(*(WIP - image_width) - *WIP) - wrap(*WIP - * (WIP + image_width));
                D1  = wrap(*(WIP - image_width_plus_one) - *WIP) - wrap(*WIP - * (WIP + 1));
                D2  = wrap(*(WIP - 2 * image_width - 1) - *WIP) - wrap(*WIP - * (WIP + image_width_minus_one));
                pixel_pointer->reliability  = H * H + V * V + D1 * D1 + D2 * D2;
            }
            pixel_pointer += image_width;
            WIP += image_width;
        }
    }

    if (params->y_connectivity == 1)
    {
        // calculating the reliability for the top border of the image
        PIXELM *pixel_pointer   = pixel + 1;
        double *WIP             = wrappedImage + 1;

        for (i = 1; i < image_width - 1; ++i)
        {
            if (pixel_pointer->extended_mask == NOMASK)
            {
                H   = wrap(*(WIP - 1) - *WIP) - wrap(*WIP - * (WIP + 1));
                V   = wrap(*(WIP + image_width * (image_height - 1)) - *WIP) - wrap(*WIP - * (WIP + image_width));
                D1  = wrap(*(WIP + image_width * (image_height - 1) - 1) - *WIP) - wrap(*WIP - * (WIP + image_width_plus_one));
                D2  = wrap(*(WIP + image_width * (image_height - 1) + 1) - *WIP) - wrap(*WIP - * (WIP + image_width_minus_one));
                pixel_pointer->reliability  = H * H + V * V + D1 * D1 + D2 * D2;
            }
            pixel_pointer++;
            WIP++;
        }

        // calculating the reliability for the bottom border of the image
        pixel_pointer   = pixel + (image_height - 1) * image_width + 1;
        WIP             = wrappedImage + (image_height - 1) * image_width + 1;

        for (i = 1; i < image_width - 1; ++i)
        {
            if (pixel_pointer->extended_mask == NOMASK)
            {
                H   = wrap(*(WIP - 1) - *WIP) - wrap(*WIP - * (WIP + 1));
                V   = wrap(*(WIP - image_width) - *WIP) - wrap(*WIP - * (WIP - (image_height - 1) * image_width));
                D1  = wrap(*(WIP - image_width_plus_one) - *WIP) - wrap(*WIP - * (WIP - (image_height - 1) * (image_width) + 1));
                D2  = wrap(*(WIP - image_width_minus_one) - *WIP) - wrap(*WIP - * (WIP - (image_height - 1) * (image_width) - 1));
                pixel_pointer->reliability  = H * H + V * V + D1 * D1 + D2 * D2;
            }
            pixel_pointer++;
            WIP++;
        }
    }
}

double CAlgoQC::wrap(double pixel_value)
{
    double wrapped_pixel_value;
    if (pixel_value > m_unamValue)
    {
        wrapped_pixel_value = pixel_value - TWOPI;
    }
    else if (pixel_value < -m_unamValue)
    {
        wrapped_pixel_value = pixel_value + TWOPI;
    }
    else
    {
        wrapped_pixel_value = pixel_value;
    }
    return wrapped_pixel_value;
}

int CAlgoQC::find_wrap(double pixelL_value, double pixelR_value)
{
    double difference;
    int wrap_value;
    difference  = pixelL_value - pixelR_value;
    if (difference > m_unamValue)
    {
        wrap_value = -1;
    }
    else if (difference < -m_unamValue)
    {
        wrap_value = 1;
    }
    else
    {
        wrap_value = 0;
    }

    return wrap_value;
}

yes_no CAlgoQC::find_pivot(EDGE *left, EDGE *right, double *pivot_ptr)
{
    EDGE a, b, c, *p;
    a   = *left;
    b   = *(left + (right - left) / 2);
    c   = *right;
    o3(a, b, c);

    if (a.reliab > b.reliab)
    {
        *pivot_ptr  = b.reliab;
        return yes;
    }

    if (b.reliab < c.reliab)
    {
        *pivot_ptr  = c.reliab;
        return yes;
    }

    for (p = left + 1; p <= right; ++p)
    {
        if (p->reliab != left->reliab)
        {
            *pivot_ptr  = (p->reliab < left->reliab) ? left->reliab : p->reliab;
            return yes;
        }
    }
    return no;
}

EDGE *CAlgoQC::partition(EDGE *left, EDGE *right, double pivot)
{
    while (left <= right)
    {
        while (left->reliab < pivot)
        {
            ++left;
        }
        while (right->reliab >= pivot)
        {
            --right;
        }
        if (left < right)
        {
            swap_edge(*left, *right);
            ++left;
            --right;
        }
    }
    return left;
}

void CAlgoQC::horizontalEDGEs(PIXELM *pixel, EDGE *edge, int image_width, int image_height, params_t *params)
{
    int i, j;
    EDGE *edge_pointer      = edge;
    PIXELM *pixel_pointer   = pixel;
    int no_of_edges         = params->no_of_edges;

    for (i = 0; i < image_height; i++)
    {
        for (j = 0; j < image_width - 1; j++)
        {
            if (pixel_pointer->input_mask == NOMASK && (pixel_pointer + 1)->input_mask == NOMASK)
            {
                edge_pointer->pointer_1 = pixel_pointer;
                edge_pointer->pointer_2 = pixel_pointer + 1;
                edge_pointer->reliab    = pixel_pointer->reliability + (pixel_pointer + 1)->reliability;
                edge_pointer->increment = find_wrap(pixel_pointer->value, (pixel_pointer + 1)->value);
                edge_pointer++;
                no_of_edges++;
            }
            pixel_pointer++;
        }
        pixel_pointer++;
    }

    // construct edges at the right border of the image
    if (params->x_connectivity == 1)
    {
        pixel_pointer   = pixel + image_width - 1;
        for (i = 0; i < image_height; i++)
        {
            if (pixel_pointer->input_mask == NOMASK && (pixel_pointer - image_width + 1)->input_mask == NOMASK)
            {
                edge_pointer->pointer_1 = pixel_pointer;
                edge_pointer->pointer_2 = (pixel_pointer - image_width + 1);
                edge_pointer->reliab    = pixel_pointer->reliability + (pixel_pointer - image_width + 1)->reliability;
                edge_pointer->increment = find_wrap(pixel_pointer->value, (pixel_pointer - image_width + 1)->value);
                edge_pointer++;
                no_of_edges++;
            }
            pixel_pointer   += image_width;
        }
    }
    params->no_of_edges = no_of_edges;
}

void CAlgoQC::verticalEDGEs(PIXELM *pixel, EDGE *edge, int image_width, int image_height, params_t *params)
{
    int i, j;
    int no_of_edges         = params->no_of_edges;
    PIXELM *pixel_pointer   = pixel;
    EDGE *edge_pointer      = edge + no_of_edges;

    for (i = 0; i < image_height - 1; i++)
    {
        for (j = 0; j < image_width; j++)
        {
            if (pixel_pointer->input_mask == NOMASK && (pixel_pointer + image_width)->input_mask == NOMASK)
            {
                edge_pointer->pointer_1  = pixel_pointer;
                edge_pointer->pointer_2  = (pixel_pointer + image_width);
                edge_pointer->reliab     = pixel_pointer->reliability + (pixel_pointer + image_width)->reliability;
                edge_pointer->increment  = find_wrap(pixel_pointer->value, (pixel_pointer + image_width)->value);
                edge_pointer++;
                no_of_edges++;
            }
            pixel_pointer++;
        }
    }

    // construct edges that connect at the bottom border of the image
    if (params->y_connectivity == 1)
    {
        pixel_pointer   = pixel + image_width * (image_height - 1);
        for (i = 0; i < image_width; i++)
        {
            if (pixel_pointer->input_mask == NOMASK && (pixel_pointer - image_width * (image_height - 1))->input_mask == NOMASK)
            {
                edge_pointer->pointer_1 = pixel_pointer;
                edge_pointer->pointer_2 = (pixel_pointer - image_width * (image_height - 1));
                edge_pointer->reliab    = pixel_pointer->reliability + (pixel_pointer - image_width * (image_height - 1))->reliability;
                edge_pointer->increment = find_wrap(pixel_pointer->value, (pixel_pointer - image_width * (image_height - 1))->value);
                edge_pointer++;
                no_of_edges++;
            }
            pixel_pointer++;
        }
    }
    params->no_of_edges = no_of_edges;
}

void CAlgoQC::quicker_sort(EDGE *left, EDGE *right)
{
    EDGE *p;
    double pivot;

    if (find_pivot(left, right, &pivot) == yes)
    {
        p   = partition(left, right, pivot);
        quicker_sort(left, p - 1);
        quicker_sort(p, right);
    }
}

void CAlgoQC::gatherPIXELs(EDGE *edge, params_t *params)
{
    int k;
    PIXELM *PIXEL1;
    PIXELM *PIXEL2;
    PIXELM *group1;
    PIXELM *group2;
    EDGE *pointer_edge  = edge;
    int incremento;

    for (k = 0; k < params->no_of_edges; k++)
    {
        PIXEL1  = pointer_edge->pointer_1;
        PIXEL2  = pointer_edge->pointer_2;

        // PIXELM 1 and PIXELM 2 belong to different groups
        // initially each pixel is a group by it self and one pixel can construct a group
        // no else or else if to this if
        if (PIXEL2->head != PIXEL1->head)
        {
            // PIXELM 2 is alone in its group
            // merge this piexl with PIXELM 1 group and find the number of 2 pi to add
            // to or subtract to unwrap it
            if ((PIXEL2->next == NULL) && (PIXEL2->head == PIXEL2))
            {
                PIXEL1->head->last->next    = PIXEL2;
                PIXEL1->head->last          = PIXEL2;
                (PIXEL1->head->number_of_pixels_in_group)++;
                PIXEL2->head                = PIXEL1->head;
                PIXEL2->increment           = PIXEL1->increment - pointer_edge->increment;
            }

            // PIXELM 1 is alone in its group
            // merge this pixel with PIXELM 2 group and find the number of 2 pi to add
            // to or subtract to unwrap it
            else if ((PIXEL1->next == NULL) && (PIXEL1->head == PIXEL1))
            {
                PIXEL2->head->last->next    = PIXEL1;
                PIXEL2->head->last          = PIXEL1;
                (PIXEL2->head->number_of_pixels_in_group)++;
                PIXEL1->head                = PIXEL2->head;
                PIXEL1->increment           = PIXEL2->increment + pointer_edge->increment;
            }

            // PIXELM 1 and PIXELM 2 both have groups
            else
            {
                group1  = PIXEL1->head;
                group2  = PIXEL2->head;
                int num2    = PIXEL2->head->number_of_pixels_in_group;
                int num1    = PIXEL1->head->number_of_pixels_in_group;
                // if the no. of pixels in PIXELM 1 group is larger than the
                // no. of pixels in PIXELM 2 group. Merge PIXELM 2 group to
                // PIXELM 1 group and find the number of wraps between PIXELM 2
                // group and PIXELM 1 group to unwrap PIXELM 2 group with respect
                // to PIXELM 1 group. the no. of wraps will be added to PIXELM 2
                // group in the future.
                if (group1->number_of_pixels_in_group > group2->number_of_pixels_in_group)
                {
                    // merge PIXELM 2 with PIXELM 1 group
                    group1->last->next  = group2;
                    group1->last        = group2->last;
                    group1->number_of_pixels_in_group   = group1->number_of_pixels_in_group + group2->number_of_pixels_in_group;
                    incremento          = PIXEL1->increment - pointer_edge->increment - PIXEL2->increment;
                    // merge the other pixels in PIXELM 2 group to PIXELM 1 group
                    while (group2 != NULL)
                    {
                        group2->head        = group1;
                        group2->increment   += incremento;
                        group2              = group2->next;
                    }
                }

                // if the no. of pixels in PIXELM 2 group is larger than the
                // no. of pixels in PIXELM 1 group. Merge PIXELM 1 group to
                // PIXELM 2 group and find the number of wraps between PIXELM 2
                // group and PIXELM 1 group to unwrap PIXELM 1 group with respect
                // to PIXELM 2 group. the no. of wraps will be added to PIXELM 1
                // group in the future.
                else
                {
                    // merge PIXELM 1 with PIXELM 2 group
                    group2->last->next  = group1;
                    group2->last        = group1->last;
                    group2->number_of_pixels_in_group   = group2->number_of_pixels_in_group + group1->number_of_pixels_in_group;
                    incremento          = PIXEL2->increment + pointer_edge->increment - PIXEL1->increment;
                    // merge the other pixels in PIXELM 1 group to PIXELM 2 group
                    while (group1 != NULL)
                    {
                        group1->head        = group2;
                        group1->increment   += incremento;
                        group1              = group1->next;
                    }
                }
            }
        } //if (PIXEL2->head != PIXEL1->head)
        pointer_edge++;
    }
}

void CAlgoQC::unwrapImage(PIXELM *pixel, int image_width, int image_height)
{
    int i;
    int image_size  = image_width * image_height;
    PIXELM *pixel_pointer   = pixel;

    for (i = 0; i < image_size; i++)
    {
        //        pixel_pointer->value    += TWOPI * (double)(pixel_pointer->increment);
        // limit increment to [-1, 1]
        if (pixel_pointer->increment > 1e-5)
        {
            pixel_pointer->value    += TWOPI;
        }
        else if (pixel_pointer->increment < -(1e-5))
        {
            pixel_pointer->value    -= TWOPI;
        }
        pixel_pointer++;
    }
}

void CAlgoQC::maskImage(PIXELM *pixel, unsigned char *input_mask, int image_width, int image_height)
{
    int image_width_plus_one    = image_width + 1;
    int image_height_plus_one   = image_height + 1;
    int image_width_minus_one   = image_width - 1;
    int image_height_minus_one  = image_height - 1;

    PIXELM *pointer_pixel       = pixel;
    unsigned char *IMP          = input_mask;
    double min                  = 99999999;
    int i;
    int image_size              = image_width * image_height;

    // find the minimum of the unwrapped phase
    for (i = 0; i < image_size; i++)
    {
        if ((pointer_pixel->value < min) && (*IMP == NOMASK))
        {
            min = pointer_pixel->value;
        }
        pointer_pixel++;
        IMP++;
    }

    pointer_pixel   = pixel;
    IMP             = input_mask;

    // set the masked pixels to minimum
    for (i = 0; i < image_size; i++)
    {
        if ((*IMP) == MASK)
        {
            //            pointer_pixel->value    = min;
            pointer_pixel->value    = 0;
        }
        pointer_pixel++;
        IMP++;
    }
}

void CAlgoQC::returnImage(PIXELM *pixel, double *unwrapped_image, int image_width, int image_height)
{
    int i;
    int image_size  = image_width * image_height;
    double *unwrapped_image_pointer = unwrapped_image;
    PIXELM *pixel_pointer           = pixel;

    for (i = 0; i < image_size; i++)
    {
        *unwrapped_image_pointer    = pixel_pointer->value;
        pixel_pointer++;
        unwrapped_image_pointer++;
    }
}

//退速度模糊=========================================================================================================================
int CAlgoQC::UnfoldVel_shearb1s_old()
{
    if (Vindex == -1)
    {
        if (m_DebugLevel <= 0)
        {
            set_time_str();
            cout << time_str;
            cout << " Algo_QC:: ";
            cout << "Can not make <UnfoldVel>! " << endl;
        }
        return -1;
    }

    if (m_DebugLevel <= 0)
    {
        set_time_str();
        cout << time_str;
        cout << " Algo_QC:: ";
        cout << "<UnfoldVel> ! " << endl;
    }
    nVBinWidth = m_radardata_out->commonBlock.cutconfig.at(0).DopplerResolution * 0.001;//km
    nVBinNum = m_radardata_out->radials.at(0).momentblock.at(Vindex).momentheader.Length / m_radardata_out->radials.at(0).momentblock.at(Vindex).momentheader.BinLength;
    m_velny = m_radardata_out->commonBlock.cutconfig.at(0).NyquistSpeed;
    int Voffset = m_radardata_out->radials.at(0).momentblock.at(Vindex).momentheader.Offset;
    int Vscale = m_radardata_out->radials.at(0).momentblock.at(Vindex).momentheader.Scale;
    float KMTOM = 2.5;
    m_max_gate_dist1 = (int)(1. * KMTOM / nVBinWidth);
    m_max_beam_dist1 = (int)(1. / m_AnglarResolution);
    threshold1 = VELNY_SCALE1 * m_velny; //求径向平均速度的阈值
    threshold2 = VELNY_SCALE2 * m_velny; //判断库是否模糊的阈值
    for (int ilayer = 0; ilayer < m_LayerNum; ilayer++)
    {
        for (int i = ElRadialIndex[ilayer]; i < ElRadialIndex[ilayer] + ElRadialNum[ilayer]; i++)
        {
            vector<float> refarray;
            refarray.resize(nBinNum);
            int FrontRadial, BehandRadial;//初始径向的前后径向

            int count = 0;
            int num_clusters = NUM_CLUSTERS;//100
            for (int num = 0; num < num_clusters; num++)//0-100最多找100个初始径向
            {
                int previous_jzero = m_jzero;
                float mean = 0.0;//径向速度均值

                search_1st_beam(mean);

                if (m_jzero == -1)//无初始径向
                {
                    m_dataMarkArrayMM.clear();
                    vector <vector<int>>().swap(m_dataMarkArrayMM);
                    return 0;
                }

                else if (m_jzero == -2)//该层无模糊
                {
                    m_dataMarkArrayMM.clear();
                    vector <vector<int>>().swap(m_dataMarkArrayMM);
                    return 0;
                }
                if (previous_jzero == m_jzero && num > 0)
                {
                    num_clusters = count;//初始径向总数
                    break;
                }
                if (m_jzero >= nRadialNum)
                {
                    m_jzero = m_jzero - nRadialNum;
                }
                count++;
                //下面开始用初始参考径向进行退模糊
                for (int iBin = 0; iBin < nBinNum; iBin++)
                {
                    refarray[iBin] = mean;
                }
                shearb1s_initial(m_jzero, &refarray[0]);
                FrontRadial = m_jzero + 1;//顺时针方向的径向
                BehandRadial = m_jzero - 1;//逆时针方向的径向

                if (FrontRadial >= nRadialNum)
                {
                    FrontRadial = FrontRadial - nRadialNum;
                }

                BehandRadial = BehandRadial + (int)(BehandRadial < 0) * nRadialNum;

                if (BehandRadial >= nRadialNum)
                {
                    BehandRadial = BehandRadial - nRadialNum;
                }

                shearb1s_initial(FrontRadial, &refarray[0]);
                shearb1s_initial(BehandRadial, &refarray[0]);


                //        unfold1(1, m_jzero);
            }
            for (int i = 0; i < nRadialNum; i++)
            {
                //阈值太宽松会把中气旋也订正掉！！！谨慎放宽！！！
                int ReferRadial = i;
                int UnfoldRadial = i + 1;
                int UnfoldRadial2 = i + 2;
                int UnfoldRadial3 = i + 3;
                int UnfoldRadial4 = i + 4;
                //        int UnfoldRadial5 = i + 5;
                //        int UnfoldRadial6 = i + 6;
                //        int UnfoldRadial7 = i + 7;
                //        int UnfoldRadial8 = i + 8;
                //        int UnfoldRadial9 = i + 9;

                if (UnfoldRadial >= nRadialNum)
                {
                    UnfoldRadial = UnfoldRadial - nRadialNum;
                }
                if (UnfoldRadial2 >= nRadialNum)
                {
                    UnfoldRadial2 = UnfoldRadial2 - nRadialNum;
                }
                if (UnfoldRadial3 >= nRadialNum)
                {
                    UnfoldRadial3 = UnfoldRadial3 - nRadialNum;
                }
                if (UnfoldRadial4 >= nRadialNum)
                {
                    UnfoldRadial4 = UnfoldRadial4 - nRadialNum;
                }
                //        if (UnfoldRadial5 >= nRadialNum)
                //            UnfoldRadial5 = UnfoldRadial5 - nRadialNum;
                //        if (UnfoldRadial6 >= nRadialNum)
                //            UnfoldRadial6 = UnfoldRadial6 - nRadialNum;
                //        if (UnfoldRadial7 >= nRadialNum)
                //            UnfoldRadial7 = UnfoldRadial7 - nRadialNum;
                //        if (UnfoldRadial8 >= nRadialNum)
                //            UnfoldRadial8 = UnfoldRadial8 - nRadialNum;
                //        if (UnfoldRadial9 >= nRadialNum)
                //            UnfoldRadial9 = UnfoldRadial9 - nRadialNum;



                across_unfold(ReferRadial, UnfoldRadial);
                across_unfold(ReferRadial, UnfoldRadial2);
                across_unfold(ReferRadial, UnfoldRadial3);
                across_unfold(ReferRadial, UnfoldRadial4);
                //        across_unfold(ReferRadial,UnfoldRadial5);
                //        across_unfold(ReferRadial,UnfoldRadial6);
                //        across_unfold(ReferRadial,UnfoldRadial7);
                //        across_unfold(ReferRadial,UnfoldRadial8);
                //        across_unfold(ReferRadial,UnfoldRadial9);
            }

            for (int i = nRadialNum - 1; i >= 0; i--)
            {
                //阈值太宽松会把中气旋也订正掉！！！谨慎放宽！！！
                int ReferRadial = i;
                int UnfoldRadial = i - 1;
                int UnfoldRadial2 = i - 2;
                int UnfoldRadial3 = i - 3;
                int UnfoldRadial4 = i - 4;
                //        int UnfoldRadial5 = i - 5;
                //        int UnfoldRadial6 = i - 6;
                //        int UnfoldRadial7 = i - 7;
                //        int UnfoldRadial8 = i - 8;
                //        int UnfoldRadial9 = i - 9;

                if (UnfoldRadial < 0)
                {
                    UnfoldRadial = UnfoldRadial + nRadialNum;
                }
                if (UnfoldRadial2 < 0)
                {
                    UnfoldRadial2 = UnfoldRadial2 + nRadialNum;
                }
                if (UnfoldRadial3 < 0)
                {
                    UnfoldRadial3 = UnfoldRadial3 + nRadialNum;
                }
                if (UnfoldRadial4 < 0)
                {
                    UnfoldRadial4 = UnfoldRadial4 + nRadialNum;
                }
                //        if (UnfoldRadial5 < 0)
                //            UnfoldRadial5 = UnfoldRadial5 + nRadialNum;
                //        if (UnfoldRadial6 < 0)
                //            UnfoldRadial6 = UnfoldRadial6 + nRadialNum;
                //        if (UnfoldRadial7 < 0)
                //            UnfoldRadial7 = UnfoldRadial7 + nRadialNum;
                //        if (UnfoldRadial8 < 0)
                //            UnfoldRadial8 = UnfoldRadial8 + nRadialNum;
                //        if (UnfoldRadial9 < 0)
                //            UnfoldRadial9 = UnfoldRadial9 + nRadialNum;


                across_unfold(ReferRadial, UnfoldRadial);
                across_unfold(ReferRadial, UnfoldRadial2);
                across_unfold(ReferRadial, UnfoldRadial3);
                across_unfold(ReferRadial, UnfoldRadial4);
                //        across_unfold(ReferRadial,UnfoldRadial5);
                //        across_unfold(ReferRadial,UnfoldRadial6);
                //        across_unfold(ReferRadial,UnfoldRadial7);
                //        across_unfold(ReferRadial,UnfoldRadial8);
                //        across_unfold(ReferRadial,UnfoldRadial9);
            }

            m_dataMarkArrayMM.clear();
            vector <vector<int>>().swap(m_dataMarkArrayMM);

        }
    }
    return 0;
}

int CAlgoQC::UnfoldVel_shearb1s()
{
    for (int i_cut = 0; i_cut < m_radardata_out->commonBlock.cutconfig.size(); i_cut++)
    {
        if (indexV.at(i_cut) == -1)
        {
            return 0;
        }
        nVBinWidth = nBinWidthV.at(i_cut);//km
        nVBinNum = nBinNumV.at(i_cut);
        m_velny = m_radardata_out->commonBlock.cutconfig.at(0).NyquistSpeed;
        int Voffset = m_radardata_out->radials.at(0).momentblock.at(indexV.at(i_cut)).momentheader.Offset;
        int Vscale = m_radardata_out->radials.at(0).momentblock.at(indexV.at(i_cut)).momentheader.Scale;
        float KMTOM = 2.5;
        m_max_gate_dist1 = (int)(1. * KMTOM / nVBinWidth);
        m_max_beam_dist1 = (int)(1. / m_AnglarResolution);
        threshold1 = VELNY_SCALE1 * m_velny; //求径向平均速度的阈值
        threshold2 = VELNY_SCALE2 * m_velny; //判断库是否模糊的阈值

        Ftempdata.datablock.clear();
        for (int i = ElRadialIndex[i_cut]; i < ElRadialIndex[i_cut] + ElRadialNum[i_cut]; i++)
        {
            Ftempradial.flinedata.clear();
            Ftempradial.flinedata.resize(nBinNumV.at(i_cut));
            for (int j = 0; j < nBinNumV.at(i_cut); j++)
            {
                Ftempradial.flinedata.at(j) = GetPointData(m_radardata_out, i, indexV.at(i_cut), j);
                if (Ftempradial.flinedata.at(j) <= INVALID_RSV)
                {
                    Ftempradial.flinedata.at(j) = PREFILLVALUE_FLOAT;
                }
                if (Ftempradial.flinedata.at(j) > INVALID_RSV)
                {
                    Ftempradial.flinedata.at(j) = (1.0 * Ftempradial.flinedata.at(j) - Voffset) / (Vscale);
                }
            }
            Ftempdata.datablock.push_back(Ftempradial);
        }
        Ftempradial.flinedata.clear();


        UnfoldVel_shearb1s_Core();

        //        m_radardata_out->commonBlock.cutconfig.at(i_cut).NyquistSpeed *= 3;
        for (int iradial = ElRadialIndex[i_cut]; iradial < ElRadialIndex[i_cut] + ElRadialNum[i_cut]; iradial++)
        {
            //            int out = i_cut * nRadialNum + iradial;
            for (int iBin = 0; iBin < nBinNumV.at(i_cut); iBin++)
            {
                if (fabs(Ftempdata.datablock.at(iradial - ElRadialIndex[i_cut]).flinedata.at(iBin) - PREFILLVALUE_FLOAT) > 1e-5)
                {
                    unsigned short value = Ftempdata.datablock.at(iradial - ElRadialIndex[i_cut]).flinedata.at(iBin) * Vscale + Voffset;
                    memcpy(&m_radardata_out->radials.at(iradial).momentblock.at(indexV.at(i_cut)).momentdata.at(2 * iBin), &value, 2);
                }
                else
                {
                    unsigned short value = INVALID_BT;
                    memcpy(&m_radardata_out->radials.at(iradial).momentblock.at(indexV.at(i_cut)).momentdata.at(2 * iBin), &value, 2);
                }
            }
        }
        Ftempdata.datablock.clear();

    }
    return 0;
}

int CAlgoQC::UnfoldVel_shearb1s_Core()
{
    //float* refarray = new float[nBinNum];//保存单根径向的均值，以供逐库退模糊使用
    vector<float> refarray;
    refarray.resize(nVBinNum);
    int FrontRadial, BehandRadial;//初始径向的前后径向
    //将前几个库置空，防止噪声干扰
    for (int iradial = 0; iradial < nRadialNum; iradial++)
    {
        for (int ibin = 0; ibin < 5; ibin++)
        {
            Ftempdata.datablock.at(iradial).flinedata.at(ibin) = PREFILLVALUE_FLOAT;
        }
    }

    //标志数组
    for (int i = 0; i < nRadialNum; i++)
    {
        LineMark.resize(nVBinNum);
        for (int j = 0; j < nVBinNum; j++)
        {
            if (fabs(Ftempdata.datablock.at(i).flinedata.at(j) - PREFILLVALUE_FLOAT) > 1e-5)
            {
                LineMark.at(j) = 0;    //有效值
            }
            else
            {
                LineMark.at(j) = 3;    //无效值
            }
        }
        m_dataMarkArrayMM.push_back(LineMark);
        LineMark.clear();
        vector <int>().swap(LineMark);
    }

    int count = 0;
    int num_clusters = NUM_CLUSTERS;//100
    for (int num = 0; num < num_clusters; num++)//0-100最多找100个初始径向
    {
        int previous_jzero = m_jzero;
        float mean = 0.0;//径向速度均值

        search_1st_beam(mean);

        if (m_jzero == -1)//无初始径向
        {
            m_dataMarkArrayMM.clear();
            vector <vector<int>>().swap(m_dataMarkArrayMM);
            return 0;
        }

        else if (m_jzero == -2)//该层无模糊
        {
            m_dataMarkArrayMM.clear();
            vector <vector<int>>().swap(m_dataMarkArrayMM);
            return 0;
        }
        if (previous_jzero == m_jzero && num > 0)
        {
            num_clusters = count;//初始径向总数
            break;
        }
        if (m_jzero >= nRadialNum)
        {
            m_jzero = m_jzero - nRadialNum;
        }
        count++;
        //下面开始用初始参考径向进行退模糊
        for (int iBin = 0; iBin < nVBinNum; iBin++)
        {
            refarray[iBin] = mean;
        }
        shearb1s_initial(m_jzero, &refarray[0]);
        FrontRadial = m_jzero + 1;//顺时针方向的径向
        BehandRadial = m_jzero - 1;//逆时针方向的径向

        if (FrontRadial >= nRadialNum)
        {
            FrontRadial = FrontRadial - nRadialNum;
        }

        BehandRadial = BehandRadial + (int)(BehandRadial < 0) * nRadialNum;

        if (BehandRadial >= nRadialNum)
        {
            BehandRadial = BehandRadial - nRadialNum;
        }

        shearb1s_initial(FrontRadial, &refarray[0]);
        shearb1s_initial(BehandRadial, &refarray[0]);


        //        unfold1(1, m_jzero);
    }
    for (int i = 0; i < nRadialNum; i++)
    {
        //阈值太宽松会把中气旋也订正掉！！！谨慎放宽！！！
        int ReferRadial = i;
        int UnfoldRadial = i + 1;
        int UnfoldRadial2 = i + 2;
        int UnfoldRadial3 = i + 3;
        int UnfoldRadial4 = i + 4;
        int UnfoldRadial5 = i + 5;
        //        int UnfoldRadial6 = i + 6;
        //        int UnfoldRadial7 = i + 7;
        //        int UnfoldRadial8 = i + 8;
        //        int UnfoldRadial9 = i + 9;

        if (UnfoldRadial >= nRadialNum)
        {
            UnfoldRadial = UnfoldRadial - nRadialNum;
        }
        if (UnfoldRadial2 >= nRadialNum)
        {
            UnfoldRadial2 = UnfoldRadial2 - nRadialNum;
        }
        if (UnfoldRadial3 >= nRadialNum)
        {
            UnfoldRadial3 = UnfoldRadial3 - nRadialNum;
        }
        if (UnfoldRadial4 >= nRadialNum)
        {
            UnfoldRadial4 = UnfoldRadial4 - nRadialNum;
        }
        if (UnfoldRadial5 >= nRadialNum)
        {
            UnfoldRadial5 = UnfoldRadial5 - nRadialNum;
        }
        //        if (UnfoldRadial6 >= nRadialNum)
        //            UnfoldRadial6 = UnfoldRadial6 - nRadialNum;
        //        if (UnfoldRadial7 >= nRadialNum)
        //            UnfoldRadial7 = UnfoldRadial7 - nRadialNum;
        //        if (UnfoldRadial8 >= nRadialNum)
        //            UnfoldRadial8 = UnfoldRadial8 - nRadialNum;
        //        if (UnfoldRadial9 >= nRadialNum)
        //            UnfoldRadial9 = UnfoldRadial9 - nRadialNum;



        across_unfold(ReferRadial, UnfoldRadial);
        across_unfold(ReferRadial, UnfoldRadial2);
        across_unfold(ReferRadial, UnfoldRadial3);
        //        across_unfold(ReferRadial,UnfoldRadial4);
        //        across_unfold(ReferRadial,UnfoldRadial5);
        //        across_unfold(ReferRadial,UnfoldRadial6);
        //        across_unfold(ReferRadial,UnfoldRadial7);
        //        across_unfold(ReferRadial,UnfoldRadial8);
        //        across_unfold(ReferRadial,UnfoldRadial9);
    }

    for (int i = nRadialNum - 1; i >= 0; i--)
    {
        //阈值太宽松会把中气旋也订正掉！！！谨慎放宽！！！
        int ReferRadial = i;
        int UnfoldRadial = i - 1;
        int UnfoldRadial2 = i - 2;
        int UnfoldRadial3 = i - 3;
        int UnfoldRadial4 = i - 4;
        int UnfoldRadial5 = i - 5;
        //        int UnfoldRadial6 = i - 6;
        //        int UnfoldRadial7 = i - 7;
        //        int UnfoldRadial8 = i - 8;
        //        int UnfoldRadial9 = i - 9;

        if (UnfoldRadial < 0)
        {
            UnfoldRadial = UnfoldRadial + nRadialNum;
        }
        if (UnfoldRadial2 < 0)
        {
            UnfoldRadial2 = UnfoldRadial2 + nRadialNum;
        }
        if (UnfoldRadial3 < 0)
        {
            UnfoldRadial3 = UnfoldRadial3 + nRadialNum;
        }
        if (UnfoldRadial4 < 0)
        {
            UnfoldRadial4 = UnfoldRadial4 + nRadialNum;
        }
        if (UnfoldRadial5 < 0)
        {
            UnfoldRadial5 = UnfoldRadial5 + nRadialNum;
        }
        //        if (UnfoldRadial6 < 0)
        //            UnfoldRadial6 = UnfoldRadial6 + nRadialNum;
        //        if (UnfoldRadial7 < 0)
        //            UnfoldRadial7 = UnfoldRadial7 + nRadialNum;
        //        if (UnfoldRadial8 < 0)
        //            UnfoldRadial8 = UnfoldRadial8 + nRadialNum;
        //        if (UnfoldRadial9 < 0)
        //            UnfoldRadial9 = UnfoldRadial9 + nRadialNum;


        across_unfold(ReferRadial, UnfoldRadial);
        across_unfold(ReferRadial, UnfoldRadial2);
        across_unfold(ReferRadial, UnfoldRadial3);
        //        across_unfold(ReferRadial,UnfoldRadial4);
        //                across_unfold(ReferRadial,UnfoldRadial5);
        //        across_unfold(ReferRadial,UnfoldRadial6);
        //        across_unfold(ReferRadial,UnfoldRadial7);
        //        across_unfold(ReferRadial,UnfoldRadial8);
        //        across_unfold(ReferRadial,UnfoldRadial9);
    }

    m_dataMarkArrayMM.clear();
    vector <vector<int>>().swap(m_dataMarkArrayMM);
    return 0;
}

int CAlgoQC::search_1st_beam(float &mean)
{
    int flag = 0;//径向标志符
    int dealiasing_flag = -1;//整层标志符
    int knum = 0;//单根径向不模糊库个数
    float dmean = 0;//单根径向不模糊速度和
    int endBin = nVBinNum - 11;//结束循环库数
    int knref = KNREF_TIMES * KNUM;
    vector <float> numAA;//径向有效值个数
    vector <float> meanAA;//径向平均速度
    mean = 0;//径向平均速度初始化

    for (int iradial = 0; iradial < nRadialNum; iradial++)
    {
        flag = -1;
        knum = 0;
        dmean = 0.0;
        for (int iBin = 4; iBin < endBin; iBin++)
        {
            //阈值太宽松会把中气旋也订正掉！！！谨慎放宽！！！
            float a = Ftempdata.datablock.at(iradial).flinedata.at(iBin);
            float b = Ftempdata.datablock.at(iradial).flinedata.at(iBin + 1);
            float c = Ftempdata.datablock.at(iradial).flinedata.at(iBin + 2);
            float d = Ftempdata.datablock.at(iradial).flinedata.at(iBin + 3);
            float e = Ftempdata.datablock.at(iradial).flinedata.at(iBin + 4);
            float f = Ftempdata.datablock.at(iradial).flinedata.at(iBin + 5);
            //            float g = Ftempdata.datablock.at(iradial).flinedata.at(iBin+6);
            //            float h = Ftempdata.datablock.at(iradial).flinedata.at(iBin+7);
            //            float i = Ftempdata.datablock.at(iradial).flinedata.at(iBin+8);
            //            float j = Ftempdata.datablock.at(iradial).flinedata.at(iBin+9);
            //            float k = Ftempdata.datablock.at(iradial).flinedata.at(iBin+10);
            //            float l = Ftempdata.datablock.at(iradial).flinedata.at(iBin+11);
            if (m_dataMarkArrayMM.at(iradial).at(iBin) > 1)
            {
                continue;    //循环下个库
            }

            if ((m_dataMarkArrayMM.at(iradial).at(iBin + 1) == 0 && (fabs(a - b) > threshold2)) || \
                    (m_dataMarkArrayMM.at(iradial).at(iBin + 2) == 0 && (fabs(a - c) > threshold2)) || \
                    (m_dataMarkArrayMM.at(iradial).at(iBin + 3) == 0 && (fabs(a - d) > threshold2)) || \
                    (m_dataMarkArrayMM.at(iradial).at(iBin + 4) == 0 && (fabs(a - e) > threshold2)) || \
                    (m_dataMarkArrayMM.at(iradial).at(iBin + 5) == 0 && (fabs(a - f) > threshold2)));
            //            ||(m_dataMarkArrayMM.at(iradial).at(iBin+6) == 0 && (fabs(a-g) > threshold2))|| (m_dataMarkArrayMM.at(iradial).at(iBin+7) == 0 && (fabs(a-h) > threshold2))||(m_dataMarkArrayMM.at(iradial).at(iBin+8) == 0 && (fabs(a-i) > threshold2))||(m_dataMarkArrayMM.at(iradial).at(iBin+9) == 0 && (fabs(a-j) > threshold2))||(m_dataMarkArrayMM.at(iradial).at(iBin+10) == 0 && (fabs(a-k) > threshold2))||(m_dataMarkArrayMM.at(iradial).at(iBin+11) == 0 && (fabs(a-l) > threshold2)))
            {
                flag = 1;//径向存在模糊
                dealiasing_flag = 1;//单层存在模糊
                break;//循环下个径向
            }

            if (fabs(Ftempdata.datablock.at(iradial).flinedata.at(iBin)) <= threshold1)
            {
                dmean = dmean + Ftempdata.datablock.at(iradial).flinedata.at(iBin);
                knum = knum + 1;
            }
        }
        if (knum > KNUM && flag == -1)//径向有效速度个数满足阈值，且径向无模糊
        {
            numAA.push_back(float(knum));
            meanAA.push_back(dmean / knum);
        }
        else if (flag == 1)//径向模糊
        {
            numAA.push_back(0);
            meanAA.push_back(PREFILLVALUE_FLOAT);
        }
        else//值太少,无速度
        {
            numAA.push_back(1);
            meanAA.push_back(1);
        }
    }

    //当前层不存在速度模糊
    if (dealiasing_flag == -1)
    {
        m_jzero = -2;
        numAA.clear();
        vector <float>().swap(numAA);
        meanAA.clear();
        vector <float>().swap(meanAA);
        return 0;
    }

    //寻找初始径向
    int j11, j22, j33, j44, j55;
    int maxnum = 0;
    for (int iradial = 0; iradial < nRadialNum; iradial++)
    {
        j11 = iradial;
        j22 = iradial + 1;
        j33 = iradial + 2;
        j44 = iradial + 3;
        j55 = iradial + 4;
        if (j11 >= nRadialNum)
        {
            j11 = j11 - nRadialNum;
        }
        if (j22 >= nRadialNum)
        {
            j22 = j22 - nRadialNum;
        }
        if (j33 >= nRadialNum)
        {
            j33 = j33 - nRadialNum;
        }
        if (j44 >= nRadialNum)
        {
            j44 = j44 - nRadialNum;
        }
        if (j55 >= nRadialNum)
        {
            j55 = j55 - nRadialNum;
        }
        if (((meanAA.at(j11) < 0 && meanAA.at(j22) < 0 && meanAA.at(j44) > 0 && meanAA.at(j55) > 0) ||
                (meanAA.at(j11) > 0 && meanAA.at(j22) > 0 && meanAA.at(j44) < 0 && meanAA.at(j55) < 0)) && numAA.at(j33) > maxnum)
        {
            if (numAA.at(j22) == 0 || numAA.at(j44) == 0)
            {
                maxnum = int(numAA.at(j33));
                m_jzero = j33;
                mean = meanAA.at(j33);//同时获得该径向均值
                flag = 2;//修改标记
            }
        }
    }
    //找不到，放宽标准
    if (flag != 2)
    {
        int j11, j22, j33, j44;
        maxnum = 0;
        for (int iradial = 0; iradial < nRadialNum; iradial++)//循环方位
        {
            j11 = iradial;
            j22 = iradial + 1;
            j33 = iradial + 2;
            j44 = iradial + 3;
            if (j11 >= nRadialNum)
            {
                j11 = j11 - nRadialNum;
            }
            if (j22 >= nRadialNum)
            {
                j22 = j22 - nRadialNum;
            }
            if (j33 >= nRadialNum)
            {
                j33 = j33 - nRadialNum;
            }
            if (j44 >= nRadialNum)
            {
                j44 = j44 - nRadialNum;
            }
            if (((meanAA.at(j11) < 0 && meanAA.at(j22) < 0 && meanAA.at(j33) > 0 && meanAA.at(j44) > 0) ||
                    (meanAA.at(j11) > 0 && meanAA.at(j22) > 0 && meanAA.at(j33) < 0 && meanAA.at(j44) < 0)) && numAA.at(j22) > maxnum)
            {
                maxnum = int(numAA.at(j22));
                m_jzero = j22;//同上
                mean = meanAA.at(j22);
                flag = 2;//修改标记
            }
        }
    }
    //找不到，再放宽标准
    if (flag != 2)
    {
        while (1)
        {
            int kntol = 0;
            mean = m_velny;
            maxnum = 0;
            for (int iradial = 0; iradial < nRadialNum; iradial++)
            {
                knum = 0;
                dmean = 0;
                flag = -1;
                for (int iBin = 4; iBin < endBin; iBin++)
                {
                    if (m_dataMarkArrayMM[iradial][iBin] > 1)
                    {
                        continue;
                    }

                    if ((m_dataMarkArrayMM[iradial][iBin + 1] == 0 && fabs(Ftempdata.datablock.at(iradial).flinedata.at(iBin) - Ftempdata.datablock.at(iradial).flinedata.at(iBin + 1)) > threshold2) ||
                            (m_dataMarkArrayMM[iradial][iBin + 2] == 0 && fabs(Ftempdata.datablock.at(iradial).flinedata.at(iBin) - Ftempdata.datablock.at(iradial).flinedata.at(iBin + 2)) > threshold2))
                    {
                        flag = 1;
                        break;//满足就跳出
                    }
                    dmean = dmean + fabs(Ftempdata.datablock.at(iradial).flinedata.at(iBin));//直接进行了累加，没有要求再满足T1
                    knum = knum + 1;
                }
                //一根径向完毕，没有出现模糊，则进行下面判断
                if (knum > knref && flag == -1)
                {
                    kntol = kntol + 1;//计数，代表的是径向数，这里计算的均值和计数都没有存进数组里，是另外定义的变量
                    dmean = dmean / knum;
                    if (dmean < mean)
                    {
                        m_jzero = iradial;//循环迭代，多次径向循环可获得平均速度最大的径向
                        mean = dmean;
                    }
                }
            }
            if ((kntol >= KTOL) && (mean <= threshold1))//这时才来判断T1,同上一致
            {
                break;
            }
            else
            {
                knref = knref - KNUM;//按4往下降规则
                if (knref < KNUM)//降到4以下就赋值初始值，不玩了
                {
                    numAA.clear();
                    vector <float>().swap(numAA);
                    meanAA.clear();
                    vector <float>().swap(meanAA);
                    m_jzero = -1;

                    return 0;
                }
            }
        }
        int iodd = 0;
        int ieven = 0;
        for (int iBin = 4; iBin < nVBinNum; iBin++)
        {
            if (m_dataMarkArrayMM[m_jzero][iBin] == 0)
            {
                if (Ftempdata.datablock.at(m_jzero).flinedata.at(iBin) < 0.0)
                {
                    ieven = ieven + 1;
                }
                else
                {
                    iodd = iodd + 1;
                }
            }
        }
        //m_jzero初始径向是不模糊的
        if (iodd < ieven)//负的个数多
        {
            mean = -mean;
        }
        else if (iodd == ieven)//正负数一样
        {
            mean = 0;
        }
    }
    numAA.clear();
    vector <float>().swap(numAA);
    meanAA.clear();
    vector <float>().swap(meanAA);
}

int CAlgoQC::shearb1s_initial(int j, float *ref)
{
    //unfold using previous equvalent beam values
    for (int k = 0; k < nVBinNum; k++)
    {
        if (m_dataMarkArrayMM[j][k] == 0 && fabs(ref[k] - PREFILLVALUE_FLOAT) > 1e-5) //如果标记为0，且参考径向的均值大于距离折叠值，即正常数据
        {
            float data = rfold(Ftempdata.datablock.at(j).flinedata.at(k), ref[k], 0.6f);
            Ftempdata.datablock.at(j).flinedata.at(k) = data;
            m_dataMarkArrayMM[j][k] = 1;
        }
    }
    return 0;
}

int CAlgoQC::across_unfold(int i, int j)
{
    float iMean = 0.0;
    int ValidPoint = 0;
    //    for (int k = 0; k<nVBinNum; k++)
    for (int k = 0; k < 300; k++)
    {
        if (m_dataMarkArrayMM[i][k] == 0 || fabs(Ftempdata.datablock.at(i).flinedata.at(k)) <= threshold1)
        {
            iMean = iMean + Ftempdata.datablock.at(i).flinedata.at(k);
            ValidPoint  = ValidPoint + 1;
        }
    }
    iMean = iMean / ValidPoint;
    for (int k = 1; k < nVBinNum - 1; k++)
    {
        if (m_dataMarkArrayMM[j][k] == 0) //如果标记为0,有值
        {
            if (m_dataMarkArrayMM[i][k] == 0 && ((Ftempdata.datablock.at(i).flinedata.at(k) >= 0 && iMean >= 0) || (Ftempdata.datablock.at(i).flinedata.at(k) <= 0 && iMean <= 0)))
            {
                float diff = fabs(Ftempdata.datablock.at(i).flinedata.at(k) - Ftempdata.datablock.at(j).flinedata.at(k));
                float diff2 = fabs(Ftempdata.datablock.at(i).flinedata.at(k - 1) - Ftempdata.datablock.at(j).flinedata.at(k - 1));
                float diff3 = fabs(Ftempdata.datablock.at(i).flinedata.at(k + 1) - Ftempdata.datablock.at(j).flinedata.at(k + 1));
                if (diff > 1.5 * m_velny) // && diff2 > 0.6*m_velny)// && diff3 > 1*m_velny)//大于1*最大不模糊速度
                {
                    if (Ftempdata.datablock.at(j).flinedata.at(k) > Ftempdata.datablock.at(i).flinedata.at(k))//大于均值，进行2的n倍退折叠
                    {
                        Ftempdata.datablock.at(j).flinedata.at(k) = Ftempdata.datablock.at(j).flinedata.at(k) - 2 * m_velny;
                    }
                    else
                    {
                        Ftempdata.datablock.at(j).flinedata.at(k) = Ftempdata.datablock.at(j).flinedata.at(k) + 2 * m_velny;
                    }
                }

            }
            if (m_dataMarkArrayMM[i][k] == 3)
            {
                float diff = fabs(iMean - Ftempdata.datablock.at(j).flinedata.at(k));
                float diff2 = fabs(iMean - Ftempdata.datablock.at(j).flinedata.at(k - 1));
                float diff3 = fabs(iMean - Ftempdata.datablock.at(j).flinedata.at(k + 1));
                if (diff > 1.5 * m_velny) // && diff2 > 0.6*m_velny)// && diff3 > 1*m_velny)//大于1*最大不模糊速度
                {
                    if (Ftempdata.datablock.at(j).flinedata.at(k) > iMean)//大于均值，进行2的n倍退折叠
                    {
                        Ftempdata.datablock.at(j).flinedata.at(k) = Ftempdata.datablock.at(j).flinedata.at(k) - 2 * m_velny;
                    }
                    else
                    {
                        Ftempdata.datablock.at(j).flinedata.at(k) = Ftempdata.datablock.at(j).flinedata.at(k) + 2 * m_velny;
                    }
                }
            }
        }
    }
    return 0;
}

float CAlgoQC::rfold(float datav, float ref, float scale)
{
    int iunf = 0;
    float diff = 0;
    diff = fabs(datav - ref);
    if ((datav > 0 && ref < 0) || (datav < 0 && ref > 0))
    {
        if (diff > scale * m_velny) //大于1*最大不模糊速度
        {
            if (datav > ref)//大于均值，进行2的n倍退折叠
            {
                datav = datav - 2 * m_velny;
            }
            else
            {
                datav = datav + 2 * m_velny;
            }
        }
    }
    return datav;

    //    while (1)//循环判断，直至满足条件
    //    {
    //        diff = fabs(datav - ref);
    //        if (diff > scale*m_velny)//大于1*最大不模糊速度
    //            iunf = iunf + 1;//计数加1
    //        else
    //            break;

    //        if (iunf > 3)//大于三次，强制赋值
    //        {
    //            datav = ref;
    //            break;
    //        }

    //        if (datav > ref)//大于均值，进行2的n倍退折叠
    //            datav = datav - 2 * m_velny;
    //        else
    //            datav = datav + 2 * m_velny;
    //    }//while
}

int CAlgoQC::unfold1(int round_num, int jzero)
{
    vector<float> ref;
    vector<float> ref0;
    ref.resize(nVBinNum);
    ref0.resize(nVBinNum);
    for (int ibin = 0; ibin < nVBinNum; ibin++)
    {
        ref[ibin] = Ftempdata.datablock.at(jzero).flinedata.at(ibin);
        ref0[ibin] = Ftempdata.datablock.at(jzero).flinedata.at(ibin);
    }

    m_max_gate_dist = m_max_gate_dist1 * (int)(pow(3.0, (double)(round_num - 1)) + 0.49); //最大库间隔，重新赋值
    m_max_beam_dist = m_max_beam_dist1 * (int)(pow(3.0, (double)(round_num - 1)) + 0.49); //最大径向间隔
    if (m_max_beam_dist > (nRadialNum / 2))
    {
        m_max_beam_dist = (nRadialNum / 2);
    }

    int jend = jzero - nRadialNum / 2;//初始径向位置减去全部径向的一半，也就是间隔180度

    jend = jend + int(jend < 0) * nRadialNum; //确保jend不是啥不正常的值

    if (jend > jzero)//初始径向角度小于循环结束角度，查看谁大谁小，方便写循环
    {
        for (int iradial = jzero; iradial <= jend; iradial++)
        {
            shearb1s(round_num, 1, iradial, &ref0[0]);//j为某一个径向，逐个方位去退模糊
            chgbeam(iradial, &ref0[0]);//替换退模糊后的数据，标记数组在退模糊过程中就进行修改了，从0到1
        }
    }
    else//初始径向角度大于循环结束角度，先循环到360，再从0开始到结束
    {
        for (int iraidal = jzero; iraidal < nRadialNum; iraidal++)
        {
            shearb1s(round_num, 1, iraidal, &ref0[0]);
            chgbeam(iraidal, &ref0[0]);
        }//for
        for (int iraidal = 0; iraidal <= jend; iraidal++)
        {
            shearb1s(round_num, 1, iraidal, &ref0[0]);
            chgbeam(iraidal, &ref0[0]);
        }//for

        //CCMLogger::Instance().Add("DEALIASING::unfold1______3\n");
    }

    jend = jzero - nRadialNum / 2;
    if (jend < 0)
    {
        jend = jend + nRadialNum;
    }

    if (jend > jzero)//同上
    {
        for (int iraidal = jzero; iraidal >= 0; iraidal--)
        {
            shearb1s(round_num, 0, iraidal, &ref[0]);
            chgbeam(iraidal, &ref[0]);
        }

        for (int iraidal = nRadialNum - 1; iraidal >= jend; iraidal--)
        {
            shearb1s(round_num, 0, iraidal, &ref[0]);
            chgbeam(iraidal, &ref[0]);
        }

        //CCMLogger::Instance().Add("DEALIASING::unfold1______4\n");
    }
    else//同上
    {
        for (int iraidal = jzero; iraidal >= jend; iraidal--)
        {
            shearb1s(round_num, 0, iraidal, &ref[0]);
            chgbeam(iraidal, &ref[0]);
        }
        //CCMLogger::Instance().Add("DEALIASING::unfold1______5\n");
    }

    ref.clear();
    ref0.clear();

    return 0;
}

int CAlgoQC::shearb1s(int round_num, bool flag, int iRial, float *ref)
{
    int k, kk, jj, BehandRadial, j2, j3, jend, flag0;
    float temp, threshold;
    int start = m_max_gate_dist1;
    int end = nVBinNum - m_max_gate_dist1;
    int double_max_gate_dist1 = 2 * m_max_gate_dist1;
    int triple_max_gate_dist1 = 3 * m_max_gate_dist1;
    BehandRadial = 0;

    //get threshold
    threshold = m_velny_scale * m_velny; //0.75*Vn;T2


    int xxu_ray = 1;
    int xxu_gate = 1;

    if (xxu_ray == 1)
    {
        ////test2<<"1-for-k="<<m_max_gate_dist1<<"---"<<"k="<<end<<endl;
        for (k = m_max_gate_dist1; k < end; k++)//库数循环，因为要确保前后有连续的库数(m_max_gate_dist1)，所以得这么循环吧
        {

            if (m_dataMarkArrayMM[iRial][k] == 0)
            {
                if (flag == 1)//flag=1顺时针,flag=0逆时针
                {
                    jend = iRial - m_max_beam_dist;

                    if (jend < iRial)
                    {
                        for (jj = iRial; jj > jend; jj--)//这里是先循环方位，再循环库数
                        {

                            BehandRadial = jj - 1;
                            j2 = jj - 2;
                            j3 = jj - 3;
                            BehandRadial = BehandRadial + int(BehandRadial < 0) * nRadialNum;
                            j2 = j2 + int(j2 < 0) * nRadialNum;
                            j3 = j3 + int(j3 < 0) * nRadialNum; //确保部为负数

                            if (m_dataMarkArrayMM[BehandRadial][k] == 1 &&
                                    fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(j2).flinedata.at(k)) < threshold &&
                                    fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(j3).flinedata.at(k)) < threshold &&
                                    fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(BehandRadial).flinedata.at(k + m_max_gate_dist1)) < threshold &&
                                    fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(BehandRadial).flinedata.at(k + m_max_gate_dist1)) < threshold)
                            {
                                temp = (Ftempdata.datablock.at(BehandRadial).flinedata.at(k) + Ftempdata.datablock.at(j2).flinedata.at(k) + Ftempdata.datablock.at(j3).flinedata.at(k)) / 3;//均值
                                rfold(Ftempdata.datablock.at(iRial).flinedata.at(k), temp, 1.0);//退折叠
                                m_dataMarkArrayMM[iRial][k] = 1;//修改标记
                                break;
                            }
                        }
                    }
                    else//jend>=iRial
                    {
                        flag0 = 0;
                        for (jj = iRial; jj >= 0; jj--)
                        {
                            ////test2<<"1-3-for-jj="<<jj<<"---"<<"jj="<<0<<endl;
                            BehandRadial = jj - 1;
                            j2 = jj - 2;
                            j3 = jj - 3;
                            BehandRadial = BehandRadial + int(BehandRadial < 0) * nRadialNum;
                            j2 = j2 + int(j2 < 0) * nRadialNum;
                            j3 = j3 + int(j3 < 0) * nRadialNum;

                            if (m_dataMarkArrayMM[BehandRadial][k] == 1 &&
                                    fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(j2).flinedata.at(k)) < threshold &&
                                    fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(j3).flinedata.at(k)) < threshold &&
                                    fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(BehandRadial).flinedata.at(k + m_max_gate_dist1)) < threshold &&
                                    fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(BehandRadial).flinedata.at(k - m_max_gate_dist1)) < threshold)
                            {
                                temp = (Ftempdata.datablock.at(BehandRadial).flinedata.at(k) + Ftempdata.datablock.at(j2).flinedata.at(k) + Ftempdata.datablock.at(j3).flinedata.at(k)) / 3;//均值
                                rfold(Ftempdata.datablock.at(iRial).flinedata.at(k), temp, 1.0);//退折叠
                                m_dataMarkArrayMM[iRial][k] = 1;//修改标记

                                flag0 = 1;
                                break;
                            }
                        }

                        if (flag0 == 0)
                        {
                            ////test2<<"1-4-for-jj="<<m_nobeam-1<<"---"<<"jj="<<jend<<endl;
                            for (jj = nRadialNum - 1; jj > jend; jj--)
                            {
                                BehandRadial = jj - 1;
                                j2 = jj - 2;
                                j3 = jj - 3;
                                BehandRadial = BehandRadial + int(BehandRadial < 0) * nRadialNum;
                                j2 = j2 + int(j2 < 0) * nRadialNum;
                                j3 = j3 + int(j3 < 0) * nRadialNum;

                                if (m_dataMarkArrayMM[BehandRadial][k] == 1 &&
                                        fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(j2).flinedata.at(k)) < threshold &&
                                        fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(j3).flinedata.at(k)) < threshold &&
                                        fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(BehandRadial).flinedata.at(k + m_max_gate_dist1)) < threshold &&
                                        fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(BehandRadial).flinedata.at(k - m_max_gate_dist1)) < threshold)
                                {
                                    temp = (Ftempdata.datablock.at(BehandRadial).flinedata.at(k) + Ftempdata.datablock.at(j2).flinedata.at(k) + Ftempdata.datablock.at(j3).flinedata.at(k)) / 3;//均值
                                    rfold(Ftempdata.datablock.at(iRial).flinedata.at(k), temp, 1.0);//退折叠
                                    m_dataMarkArrayMM[iRial][k] = 1;//修改标记
                                    break;
                                }
                            }
                        }
                    }
                }
                else //逆时针
                {
                    jend = iRial + m_max_beam_dist;
                    if (jend > iRial)//没过360
                    {
                        ////test2<<"1-5-for-jj="<<iRial<<"---"<<"jj="<<jend<<endl;
                        for (jj = iRial; jj < jend; jj++)
                        {

                            BehandRadial = jj + 1;
                            j2 = jj + 2;
                            j3 = jj + 3;
                            BehandRadial = BehandRadial - int(BehandRadial >= nRadialNum) * nRadialNum;
                            j2 = j2 - int(j2 >= nRadialNum) * nRadialNum;
                            j3 = j3 - int(j3 >= nRadialNum) * nRadialNum;

                            if (m_dataMarkArrayMM[BehandRadial][k] == 1 &&
                                    fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(j2).flinedata.at(k)) < threshold &&
                                    fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(j3).flinedata.at(k)) < threshold &&
                                    fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(BehandRadial).flinedata.at(k + m_max_gate_dist1)) < threshold &&
                                    fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(BehandRadial).flinedata.at(k - m_max_gate_dist1)) < threshold
                               )
                            {
                                temp = (Ftempdata.datablock.at(BehandRadial).flinedata.at(k) + Ftempdata.datablock.at(j2).flinedata.at(k) + Ftempdata.datablock.at(j3).flinedata.at(k)) / 3;//均值
                                rfold(Ftempdata.datablock.at(iRial).flinedata.at(k), temp, 1.0);//退折叠
                                m_dataMarkArrayMM[iRial][k] = 1;//修改标记
                                break;
                            }//if
                        }//for
                    }
                    else//过了360了，分段进行
                    {
                        flag0 = 0;
                        ////test2<<"1-6-for-jj="<<iRial<<"---"<<"jj="<<m_nobeam<<endl;
                        for (jj = iRial; jj < nRadialNum; jj++)
                        {
                            BehandRadial = jj + 1;
                            j2 = jj + 2;
                            j3 = jj + 3;
                            BehandRadial = BehandRadial - int(BehandRadial >= nRadialNum) * nRadialNum;
                            j2 = j2 - int(j2 >= nRadialNum) * nRadialNum;
                            j3 = j3 - int(j3 >= nRadialNum) * nRadialNum;

                            if (m_dataMarkArrayMM[BehandRadial][k] == 1 &&
                                    fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(j2).flinedata.at(k)) < threshold &&
                                    fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(j3).flinedata.at(k)) < threshold &&
                                    fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(BehandRadial).flinedata.at(k + m_max_gate_dist1)) < threshold &&
                                    fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(BehandRadial).flinedata.at(k - m_max_gate_dist1)) < threshold
                               )
                            {
                                temp = (Ftempdata.datablock.at(BehandRadial).flinedata.at(k) + Ftempdata.datablock.at(j2).flinedata.at(k) + Ftempdata.datablock.at(j3).flinedata.at(k)) / 3;//均值
                                rfold(Ftempdata.datablock.at(iRial).flinedata.at(k), temp, 1.0);//退折叠
                                m_dataMarkArrayMM[iRial][k] = 1;//修改标记
                                flag0 = 1;
                                break;
                            }//if
                        }//for

                        if (flag0 == 0)//前面的都没有退折叠成功
                        {
                            ////test2<<"1-7-for-jj="<<0<<"---"<<"jj="<<jend<<endl;
                            for (jj = 0; jj < jend; jj++)
                            {
                                BehandRadial = jj + 1;
                                j2 = jj + 2;
                                j3 = jj + 3;
                                BehandRadial = BehandRadial - int(BehandRadial >= nRadialNum) * nRadialNum;
                                j2 = j2 - int(j2 >= nRadialNum) * nRadialNum;
                                j3 = j3 - int(j3 >= nRadialNum) * nRadialNum;

                                if (m_dataMarkArrayMM[BehandRadial][k] == 1 &&
                                        fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(j2).flinedata.at(k)) < threshold &&
                                        fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(j3).flinedata.at(k)) < threshold &&
                                        fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(BehandRadial).flinedata.at(k + m_max_gate_dist1)) < threshold &&
                                        fabs(Ftempdata.datablock.at(BehandRadial).flinedata.at(k) - Ftempdata.datablock.at(BehandRadial).flinedata.at(k - m_max_gate_dist1)) < threshold
                                   )
                                {
                                    temp = (Ftempdata.datablock.at(BehandRadial).flinedata.at(k) + Ftempdata.datablock.at(j2).flinedata.at(k) + Ftempdata.datablock.at(j3).flinedata.at(k)) / 3;//均值
                                    rfold(Ftempdata.datablock.at(iRial).flinedata.at(k), temp, 1.0);//退折叠
                                    m_dataMarkArrayMM[iRial][k] = 1;//修改标记
                                    break;
                                }//if
                            }//for
                        }//if
                    }
                }
            }
        }
    }
    //do dealiasing for the first pass

    if (xxu_gate == 1)
    {
        int first;
        if (round_num == 1)
        {
            int num;
            start = nVBinNum - 3 * m_max_gate_dist1 - 1;
            while (1)
            {
                //search initial point寻找起始点，单个径向上
                first = -1;
                ///gln-add 2019-02-14
                if (start < 0)
                {
                    break;
                }
                ///


                int initial_gate = 6;
                num = 0;
                ////test2<<"2--for-k="<<start<<"---"<<"k="<<m_max_gate_dist1<<endl;
                for (k = start; k > m_max_gate_dist1; k--)
                {
                    //标记为1

                    if (m_dataMarkArrayMM[iRial][k] == 1 &&
                            fabs(Ftempdata.datablock.at(iRial).flinedata.at(k) - ref[k]) < threshold &&
                            fabs(Ftempdata.datablock.at(iRial).flinedata.at(k) - ref[k + m_max_gate_dist1]) < threshold &&
                            fabs(Ftempdata.datablock.at(iRial).flinedata.at(k) - ref[k + double_max_gate_dist1]) < threshold &&
                            fabs(Ftempdata.datablock.at(iRial).flinedata.at(k) - Ftempdata.datablock.at(iRial).flinedata.at(k + m_max_gate_dist1)) < threshold &&
                            fabs(Ftempdata.datablock.at(iRial).flinedata.at(k) - Ftempdata.datablock.at(iRial).flinedata.at(k + double_max_gate_dist1)) < threshold)
                    {
                        num++;
                        if (num > 4)
                        {
                            if (flag == 1)
                            {
                                BehandRadial = iRial - initial_gate;
                                BehandRadial = BehandRadial + int(BehandRadial < 0) * nRadialNum;
                            }
                            else if (flag == 0)
                            {
                                BehandRadial = iRial + initial_gate;
                                BehandRadial = BehandRadial - int(BehandRadial >= nRadialNum) * nRadialNum;
                            }//if-elseif

                            if (m_dataMarkArrayMM[BehandRadial][k] <= 2)
                            {
                                first = k + 3;
                                break;
                            }//if
                        }//if
                    }
                    else
                    {
                        k = k - triple_max_gate_dist1;
                        num = 0;
                    }//if-else
                }//for


                if (first == -1)
                {
                    break;    //找不到跳出循环
                }

                //unfold using same beam values
                ////test2<<"3--for-k="<<first+2<<"---"<<"k="<<start<<endl;
                for (k = first + 2; k < start; k++)
                {
                    if ((k - triple_max_gate_dist1) < 0)///gln-add 2019-02-14
                    {
                        break;
                    }

                    if (m_dataMarkArrayMM[iRial][k] > 1)
                    {
                        continue;
                    }


                    if (m_dataMarkArrayMM[iRial][k - m_max_gate_dist1] == 1)
                    {
                        if (fabs(Ftempdata.datablock.at(iRial).flinedata.at(k - m_max_gate_dist1) - Ftempdata.datablock.at(iRial).flinedata.at(k - double_max_gate_dist1)) < threshold
                                //           &&  abs(datav[iRial][k-max_gate_dist1]-ref[k-triple_max_gate_dist1]) < threshold
                                && fabs(Ftempdata.datablock.at(iRial).flinedata.at(k - m_max_gate_dist1) - Ftempdata.datablock.at(iRial).flinedata.at(k - triple_max_gate_dist1)) < threshold)
                        {
                            temp = (Ftempdata.datablock.at(iRial).flinedata.at(k - m_max_gate_dist1) + Ftempdata.datablock.at(iRial).flinedata.at(k - double_max_gate_dist1) + Ftempdata.datablock.at(iRial).flinedata.at(k - triple_max_gate_dist1)) / 3;
                            rfold(Ftempdata.datablock.at(iRial).flinedata.at(k), temp, 1.0);
                            m_dataMarkArrayMM[iRial][k] = 1;
                        }//if
                    }//if
                    else
                    {
                        break;
                    }
                }//for
                ////test2<<"4--for-k="<<first-2<<"---"<<"k="<<m_max_gate_dist1<<endl;
                for (k = first - 2; k > m_max_gate_dist1; k--)
                {
                    if ((k + triple_max_gate_dist1 + 1) > nVBinNum) ///gln-add 2019-02-14
                    {
                        break;
                    }

                    if (m_dataMarkArrayMM[iRial][k] > 1)
                    {
                        continue;
                    }
                    if (m_dataMarkArrayMM[iRial][k + m_max_gate_dist1] == 1)
                    {

                        if (fabs(Ftempdata.datablock.at(iRial).flinedata.at(k + m_max_gate_dist1) - Ftempdata.datablock.at(iRial).flinedata.at(k + double_max_gate_dist1)) < threshold
                                //     &&    abs(datav[iRial][k+max_gate_dist1]-ref[k+triple_max_gate_dist1]) < threshold
                                &&    fabs(Ftempdata.datablock.at(iRial).flinedata.at(k + m_max_gate_dist1) - Ftempdata.datablock.at(iRial).flinedata.at(k + triple_max_gate_dist1)) < threshold)
                        {
                            temp = (Ftempdata.datablock.at(iRial).flinedata.at(k + m_max_gate_dist1) + Ftempdata.datablock.at(iRial).flinedata.at(k + double_max_gate_dist1) + Ftempdata.datablock.at(iRial).flinedata.at(k + triple_max_gate_dist1)) / 3;
                            rfold(Ftempdata.datablock.at(iRial).flinedata.at(k), temp, 1.0);
                            m_dataMarkArrayMM[iRial][k] = 1;
                        }//if
                    }
                    else
                    {
                        start = k;
                        break;
                    }//if-else
                }//for
                if (k < triple_max_gate_dist1)
                {
                    break;
                }
            } //while(1)
            return 0;
        } //if ( round_num == 1 )
        /////////再次检查
        //unfold all left values and
        //check if there are any aliased point and unfold it
        first = nVBinNum / 2;
        ////test2<<"5--for-k="<<first<<"---"<<"k="<<0<<endl;
        for (k = first; k >= 0; k--)
        {
            if (m_dataMarkArrayMM[iRial][k] != 0)
            {
                continue;
            }
            for (kk = k; kk < (k + m_max_gate_dist); kk++)
            {
                if ((kk + double_max_gate_dist1 + 1) > nVBinNum) ///gln-add 2019-02-14
                {
                    break;
                }
                if (m_dataMarkArrayMM[iRial][kk + m_max_gate_dist1] == 1 &&
                        fabs(Ftempdata.datablock.at(iRial).flinedata.at(kk + m_max_gate_dist1) - ref[kk + double_max_gate_dist1]) < threshold &&
                        fabs(Ftempdata.datablock.at(iRial).flinedata.at(kk + m_max_gate_dist1) - Ftempdata.datablock.at(iRial).flinedata.at(kk + double_max_gate_dist1)) < threshold)
                {
                    temp = (ref[kk + double_max_gate_dist1] + Ftempdata.datablock.at(iRial).flinedata.at(kk + m_max_gate_dist1) + Ftempdata.datablock.at(iRial).flinedata.at(kk + double_max_gate_dist1)) / 3;
                    rfold(Ftempdata.datablock.at(iRial).flinedata.at(k), temp, 1.0);
                    m_dataMarkArrayMM[iRial][k] = 1;
                    break;

                }//if
            }//for

            if (m_dataMarkArrayMM[iRial][k] != 0)
            {
                continue;
            }
            ////test2<<"5-1--for-kk="<<k<<"---"<<"k="<<max( k-m_max_gate_dist,double_max_gate_dist1)<<endl;
            for (kk = k; kk > fmax(k - m_max_gate_dist, double_max_gate_dist1); kk--)
            {
                if ((kk - double_max_gate_dist1) < 0)///gln-add 2019-02-14
                {
                    break;
                }
                if (m_dataMarkArrayMM[iRial][kk - m_max_gate_dist1] == 1 &&
                        fabs(Ftempdata.datablock.at(iRial).flinedata.at(kk - m_max_gate_dist1) - ref[kk - double_max_gate_dist1]) < threshold &&
                        fabs(Ftempdata.datablock.at(iRial).flinedata.at(kk - m_max_gate_dist1) - Ftempdata.datablock.at(iRial).flinedata.at(kk - double_max_gate_dist1)) < threshold)
                {
                    temp = (ref[kk - double_max_gate_dist1] + Ftempdata.datablock.at(iRial).flinedata.at(kk - m_max_gate_dist1) + Ftempdata.datablock.at(iRial).flinedata.at(kk - double_max_gate_dist1)) / 3;
                    rfold(Ftempdata.datablock.at(iRial).flinedata.at(k), temp, 1.0);
                    m_dataMarkArrayMM[iRial][k] = 1;
                    break;
                }//if
            }//for
        }//for
        ////test2<<"6--for-k="<<first<<"---"<<"k="<<m_nogate<<endl;
        for (k = first; k < nVBinNum; k++)
        {
            if (m_dataMarkArrayMM[iRial][k] != 0)
            {
                continue;
            }
            ////test2<<"6-1-for-kk="<<k<<"---"<<"k="<<( k-m_max_gate_dist)<<endl;
            for (kk = k; kk > (k - m_max_gate_dist); kk--)
            {
                if ((kk - double_max_gate_dist1) < 0)
                {
                    break;
                }
                if (m_dataMarkArrayMM[iRial][kk - m_max_gate_dist1] == 1 &&
                        fabs(Ftempdata.datablock.at(iRial).flinedata.at(kk - m_max_gate_dist1) - ref[kk - double_max_gate_dist1]) < threshold &&
                        fabs(Ftempdata.datablock.at(iRial).flinedata.at(kk - m_max_gate_dist1) - Ftempdata.datablock.at(iRial).flinedata.at(kk - double_max_gate_dist1)) < threshold)
                {
                    temp = (ref[kk - double_max_gate_dist1] + Ftempdata.datablock.at(iRial).flinedata.at(kk - m_max_gate_dist1) + Ftempdata.datablock.at(iRial).flinedata.at(kk - double_max_gate_dist1)) / 3;
                    rfold(Ftempdata.datablock.at(iRial).flinedata.at(k), temp, 1.0);
                    m_dataMarkArrayMM[iRial][k] = 1;
                    break;
                }//if
            }//if

            if (m_dataMarkArrayMM[iRial][k] != 0)
            {
                continue;
            }
            ////test2<<"6-2-for-kk="<<k<<"---"<<"k="<<min( k+m_max_gate_dist, end - double_max_gate_dist1 )<<endl;
            for (kk = k; kk < fmin(k + m_max_gate_dist, end - double_max_gate_dist1); kk++)
            {
                if ((kk + double_max_gate_dist1 + 1) > nVBinNum) ///gln-add 2019-02-14
                {
                    break;
                }
                if (m_dataMarkArrayMM[iRial][kk + m_max_gate_dist1] == 1 &&
                        fabs(Ftempdata.datablock.at(iRial).flinedata.at(kk + m_max_gate_dist1) - ref[kk + double_max_gate_dist1]) < threshold &&
                        fabs(Ftempdata.datablock.at(iRial).flinedata.at(kk + m_max_gate_dist1) - Ftempdata.datablock.at(iRial).flinedata.at(kk + double_max_gate_dist1)) < threshold)
                {
                    temp = (ref[kk + double_max_gate_dist1] + Ftempdata.datablock.at(iRial).flinedata.at(kk + m_max_gate_dist1) + Ftempdata.datablock.at(iRial).flinedata.at(kk + double_max_gate_dist1)) / 3;
                    rfold(Ftempdata.datablock.at(iRial).flinedata.at(k), temp, 1.0);
                    m_dataMarkArrayMM[iRial][k] = 1;
                    break;
                }//if
            }//for
        }//for

    }


    return 0;
}

int CAlgoQC::chgbeam(int j, float *ref)
{
    for (int k = 0; k < nVBinNum; k++)
    {
        ref[k] = Ftempdata.datablock.at(j).flinedata.at(k);
    }
    return 0;
}

bool CAlgoQC::FunctionValid(QCParams &params)
{
    int type = m_radardata_out->commonBlock.siteconfig.RadarType;
    if (params.Scope == -1)
    {
        for (auto iter : params.Except)
        {
            if (iter == type)
            {
                return false;
            }
        }
        return true;
    }
    else if (params.Scope == 1)
    {
        for (auto iter : params.Type)
        {
            if (iter == type)
            {
                return true;
            }
        }
    }
    return false;
}

//功能函数=========================================================================================================================

int CAlgoQC::GetRadialNumOfEl()
{
    int ElIndex = 1;
    int LayerRadialNum = 0;
    ElRadialNum.resize(m_LayerNum);
    ElRadialNum.assign(m_LayerNum, 0);
    if (m_LayerNum == 1)
    {
        ElRadialNum.at(0) = m_radardata_out->radials.size();
    }
    else
    {
        for (int NoRadial = 0; NoRadial < m_radardata_out->radials.size(); NoRadial++)
        {
            if (m_radardata_out->radials[NoRadial].radialheader.ElevationNumber == ElIndex)
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
//        if(LayerRadialNum < 500){
//            ElRadialNum[ElIndex - 1] = 720;
//        }else{
//            ElRadialNum[ElIndex - 1] = LayerRadialNum;
//        }
        ElRadialNum[ElIndex - 1] = LayerRadialNum;

    }

    return 0;
}

int CAlgoQC::GetRadialIndexOfEl()
{
    ElRadialIndex.resize(m_LayerNum);
    ElRadialIndex.assign(m_LayerNum, 0);
    int RadialIndex = 0;
    for (int i = 0; i < m_radardata_out->commonBlock.cutconfig.size(); i++)
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

unsigned short CAlgoQC::GetPointData(WRADRAWDATA *DATA, int radialNo, int momentNo, int binNo)
{
    return *(unsigned short *)&DATA->radials.at(radialNo).momentblock.at(momentNo).momentdata[2 * binNo];
}

void CAlgoQC::QuickSort(short *array, int L, int R)
{
    /*********************************************************************
     * 函数名称:QuickSort
     * 说明:快速排序，对数据从左L个到右R个进行快速排序
     * 入口参数:
       short* array,待排序的数组
       int L,左边的边界
       int R,右边的边界
     * 返回值:
       void
    *********************************************************************/
    //    int I, J;
    //    float X, Y;

    //    I=L;
    //    J=R;
    //    X=array[((L+R)/2)];

    //    while(I <= J)
    //    {
    //        while(array[I] < X && I < R)
    //        {
    //            I = I + 1;
    //        }
    //        while(X < array[J] && J> L)
    //        {
    //            J = J - 1;
    //        }
    //        if(I <= J)
    //        {
    //            Y = array[I];
    //            array[I] = array[J];
    //            array[J] = Y;
    //            I = I + 1;
    //            J = J - 1;
    //        }
    //    }
    short temp;
    int i, j;
    for (i = 0; i < R; i++)
    {
        for (j = 0; j < R - i; j++)
        {
            if (array[j] > array[j + 1])
            {
                temp = array[j];
                array[j] = array[j + 1];
                array[j + 1] = temp;
            }

        }
    }

}

int CAlgoQC::WriteLayerData(int ilayer, int imoment)
{
    if (imoment == -1)
    {
        return 0;
    }
    if (ilayer >= m_radardata_out->commonBlock.cutconfig.size())
    {
        return 0;
    }
    //写单层文件
    ofstream OutFile("LayerData.txt");
    if (imoment == indexPHDP.at(ilayer))
    {
        OutFile << "PHDP" << endl;
    }
    else if (imoment == indexKDP.at(ilayer))
    {
        OutFile << "KDP" << endl;
    }
    else if (imoment == indexZH.at(ilayer))
    {
        OutFile << "Z" << endl;
    }
    else if (imoment == indexSNR.at(ilayer))
    {
        OutFile << "Z" << endl;
    }
    else if (imoment == indexV.at(ilayer))
    {
        OutFile << "V" << endl;
    }
    else if (imoment == indexZDR.at(ilayer))
    {
        OutFile << "ZDR" << endl;
    }
    else if (imoment == indexW.at(ilayer))
    {
        OutFile << "W" << endl;
    }
    else if (imoment == indexROHV.at(ilayer))
    {
        OutFile << "ROHV" << endl;
    }
    else if (imoment == indexUnZH.at(ilayer))
    {
        OutFile << "T" << endl;
    }
    int nBin;
    OutFile << ElRadialNum[ilayer] << endl;
    //    OutFile << m_radardata_out->radials[0].momentblock[imoment].momentdata.size()/2 << endl;
    if (imoment == indexV.at(ilayer) || imoment == indexW.at(ilayer))
    {
        nBin = nBinNumV.at(ilayer);
        OutFile << nBinNumV.at(ilayer) << endl;
        OutFile << nBinWidthV.at(ilayer) << endl;//km
    }
    else
    {
        nBin = nBinNumZ.at(ilayer);
        OutFile << nBinNumZ.at(ilayer) << endl;
        OutFile << nBinWidthZ.at(ilayer) << endl;//km
    }

    for (int i_radial = ElRadialIndex[ilayer]; i_radial < ElRadialIndex[ilayer] + ElRadialNum[ilayer]; i_radial++)
    {
        int i = i_radial;
        //        int i = i_radial + 100;
        //        if (i >= ElRadialIndex[ilayer]+ElRadialNum[ilayer]) i = i%(ElRadialIndex[ilayer]+ElRadialNum[ilayer]) + ElRadialIndex[ilayer];
        //        short aa = 0;
        for (int j = 0; j < nBin ; j++)
        {

            if (imoment == ROHVindex)
            {
                if (*(unsigned short *)&m_radardata_out->radials[i].momentblock[imoment].momentdata.at(j * 2) > INVALID_RSV)
                {
                    OutFile << (*(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(imoment).momentdata.at(j * 2) \
                                - m_radardata_out->radials.at(i).momentblock.at(imoment).momentheader.Offset) \
                            / m_radardata_out->radials.at(i).momentblock.at(imoment).momentheader.Scale * 100 / 10 << endl;
                }
                else
                {
                    OutFile << PREFILLVALUE << endl;
                }
            }
            else    //if(imoment == Vindex)
            {
                if (*(unsigned short *)&m_radardata_out->radials[i].momentblock[imoment].momentdata.at(j * 2) > INVALID_RSV)
                {
                    OutFile << (*(unsigned short *)&m_radardata_out->radials.at(i).momentblock.at(imoment).momentdata.at(j * 2) \
                                - m_radardata_out->radials.at(i).momentblock.at(imoment).momentheader.Offset) \
                            / m_radardata_out->radials.at(i).momentblock.at(imoment).momentheader.Scale * 100 << endl;
                }
                else
                {
                    OutFile << PREFILLVALUE << endl;
                }
            }
            //            else{
            //                OutFile << *(unsigned short*)&m_radardata_out->radials.at(i).momentblock.at(imoment).momentdata.at(j*2) - m_radardata_out->radials.at(i).momentblock.at(imoment).momentheader.Offset << endl;
            //            }
        }
    }
    //    tempdata1.datablock.clear();
    OutFile.close();
    //    system("DrawVectorImage.exe");
    return 0;
}
