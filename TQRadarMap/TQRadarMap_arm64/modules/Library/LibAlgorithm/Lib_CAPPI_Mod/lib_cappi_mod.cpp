#include "lib_cappi_mod.h"

CNrietAlogrithm * GetAlgoInstance()
{
    return (new CAlgoCAPPI());
}

int CAlgoCAPPI::Init()
{
    return 0;
}

int CAlgoCAPPI::Uninit()
{
    if (m_GridLat)
    {
        delete[] m_GridLat;
        m_GridLat = nullptr;
    }
    if (m_GridLon)
    {
        delete[] m_GridLon;
        m_GridLon = nullptr;
    }
    if (m_GridHeight)
    {
        delete[] m_GridHeight;
        m_GridHeight = nullptr;
    }
    if (m_RadarPro)
    {
        delete m_RadarPro;
        m_RadarPro = nullptr;
    }
    return 0;
}

int CAlgoCAPPI::LoadStdCommonBlock(void *head)
{
    return 0;
}

int CAlgoCAPPI::LoadStdRadailBlock(void* radial)
{
    return 0;
}

int CAlgoCAPPI::SetDebugLevel(int temp)
{
    m_DebugLevel = temp;
    return 0;
}

void CAlgoCAPPI::set_time_str()
{
    time_t now = time(nullptr);
    strftime(time_str,sizeof (time_str),"-- %m/%d/%Y %H:%M:%S ",localtime(&now));
}

int CAlgoCAPPI::LoadParameters(void* head)
{
    m_RadarProParameters_org = (RadarProductList*)head;

    for(int i_Pro = 0; i_Pro<m_RadarProParameters_org->size();i_Pro++){
        if (m_RadarProParameters_org->at(i_Pro).ProInfo.ProductionID < 101 || m_RadarProParameters_org->at(i_Pro).ProInfo.ProductionID > 111)
        {
            if (m_DebugLevel <= 0){
                set_time_str();
                cout << time_str;
                cout << " Algo_CAPPI::";
                cout << "Wrong Production ID number. Exit!" << endl;
            }
            return -1;
        }
    }

    return 0;
}

int CAlgoCAPPI::LoadStdData(void * data)
{

    m_RadarData_org = (WRADRAWDATA*)data;
    m_RadarHead_org = &m_RadarData_org->commonBlock;
    //    m_LayerNum = m_RadarHead_org->taskconfig.CutNumber;
    m_LayerNum = m_RadarHead_org->cutconfig.size();
    m_nRadialNumSum = (int)m_RadarData_org->radials.size();

    if (m_DebugLevel <= 0){
        for (int i_cut = 0;i_cut < m_RadarHead_org->cutconfig.size();i_cut++){
            set_time_str();
            cout << time_str;
            cout << " Algo_CAPPI::" ;
            cout << m_RadarHead_org->cutconfig[i_cut].Elevation <<endl;
        }
    }

    if (m_DebugLevel <= 0){
        set_time_str();
        cout << time_str;
        cout << " Algo_CAPPI::" ;
        cout << m_RadarData_org->commonBlock.siteconfig.SiteCode;
        cout <<",lat:" << m_RadarData_org->commonBlock.siteconfig.Latitude;
        cout <<",lon:" << m_RadarData_org->commonBlock.siteconfig.Longitude;
        cout <<",elev:" << m_RadarData_org->commonBlock.cutconfig.front().Elevation;
        cout <<"---"<<m_RadarData_org->commonBlock.cutconfig.back().Elevation;
        cout <<endl;
    }
    if (m_LayerNum == 1)
        if (m_DebugLevel <= 0){
            {
                set_time_str();
                cout << time_str;
                cout << " Algo_CAPPI::" ;
                cout << "Can not make CAPPI with 1 layer observation!" << endl;
            }
            return -1;
        }
    if (m_LayerNum == 2 && fabs(m_RadarData_org->commonBlock.cutconfig.back().Elevation - m_RadarData_org->commonBlock.cutconfig.front().Elevation) > 6)
    {
        if (m_DebugLevel <= 0){
            {
                set_time_str();
                cout << time_str;
                cout << " Algo_CAPPI::" ;
                cout << "The elev diff of 2 layers is greater than 6. Can not make CAPPI!" << endl;
            }
            return -1;
        }
    }

    return 0;
}

/* 产品ID，
101 = UnRCAPPI  // 不经过地物杂波消除的dBT值= UnZ/100
102 = RCAPPI    // 经过地物杂波消除的dBZ值= CorZ/100
103 = VCAPPI    // 速度值= V/100
                // 正值表示远离雷达的速度，负值表示朝向雷达的速度
104 = WCAPPI    // 谱宽值= W/100
107 = ZDR       // 反射率差值= ZDR/100，单位db
110 = PHDP;     // 差分传播相移= PHDP-(-180.000)/100，单位度
111 = KDP;      // 差分传播相移常数= KDP/100，单位度/公里
109 = ROHV;     // 相关系数值= ROHV/100
108 = LDR;      // 退偏振比= LDR/100
*/

int CAlgoCAPPI::MakeProduct()
{
    if (m_RadarData_org == nullptr || m_RadarData_org->commonBlock.taskconfig.ScanType > 1)//非体扫和PPI不处理
        return -1;

    GetRadialNumOfEl();                    //确定每层的径向数
    GetRadialIndexOfEl();                  //确定每层的第一根径向数据序号

    int status = 0;

    status = InitProHead();
    if (status)return status;

    GetVarInfo();

    status = GetRadarPara();
    if (status) return status;

    status = InitGridPara();
    if (status) return status;

    status = InitProGrid();
    if (status) return status;

    status = CalcCAPPI();
    if (status) return status;

    status = FreeBlock();
    if (status) return status;

    if (m_DebugLevel <= 0){
        string ProName;
        for(auto iter:*m_RadarPro){
            if (iter.SiteInfo.size()>0){
                set_time_str();
                cout << time_str;
                cout << " Algo_CAPPI::" ;
                cout << "Time of ";
                cout << iter.SiteInfo.front().SiteCode;
                cout << " ";
                cout << iter.ProInfo.ProductionName;
                cout << " is ";
                cout << iter.ProInfo.ProductionTime;
                cout << "." << endl;
            }
        }
    }

    return 0;
}

int CAlgoCAPPI::InitProHead()
{
    try
    {
        m_RadarPro = new(RadarProductList);
    }
    catch (bad_alloc)
    {
        return -1;
    }

    *m_RadarPro=(*m_RadarProParameters_org);

    m_moment_index.resize(m_RadarPro->size());
    VarIndex VarIndex_temp;
    for (int i_Pro = 0; i_Pro < m_RadarPro->size();i_Pro++) {
        m_RadarPro->at(i_Pro).ParametersInfo.cappiparameter.QCMask = m_RadarData_org->commonBlock.cutconfig.front().dBTMask;
        for (int i_cut = 0; i_cut < m_RadarData_org->commonBlock.cutconfig.size(); i_cut++){
            for (int i_moment = 0;i_moment < m_RadarData_org->radials[ElRadialIndex.at(i_cut)].momentblock.size();i_moment ++) {
                if ( m_RadarData_org->radials[0].momentblock[i_moment].momentheader.DataType == \
                     m_RadarPro->at(i_Pro).ProInfo.ProductionID - 100 ) {
                    VarIndex_temp.cut_index = i_cut;
                    VarIndex_temp.moment_index = i_moment;
                    m_moment_index.at(i_Pro).push_back(VarIndex_temp);
                    break;
                }
            }
        }
    }

    return 0;
}

int CAlgoCAPPI::GetRadialNumOfEl()
{
    int ElIndex = 1;
    int LayerRadialNum = 0;
    ElRadialNum.resize(m_LayerNum);
    for (int NoRadial = 0; NoRadial < m_RadarData_org->radials.size(); NoRadial++)
    {
        if (m_RadarData_org->radials[NoRadial].radialheader.ElevationNumber == \
                ElIndex -1 + m_RadarData_org->radials.front().radialheader.ElevationNumber)
            LayerRadialNum++;
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

int CAlgoCAPPI::GetRadialIndexOfEl()
{
    int RadialIndex = 0;
    ElRadialIndex.resize(m_LayerNum);
    for (int i=0; i<m_LayerNum; i++)
    {
        if (i == 0)
            RadialIndex = 0;
        else
            RadialIndex = RadialIndex + ElRadialNum[i -1];
        ElRadialIndex[i] = RadialIndex;
    }
    return 0;
}

void CAlgoCAPPI::GetVarInfo()
{
    m_VarInfo.clear();
    int proNum  = m_RadarProParameters_org->size();
    m_VarInfo.resize(proNum);
    for (int i_pro = 0; i_pro < proNum; ++i_pro)
    {
        VARCAPPIINFO info;
        info.varCutNum  = 0;
        info.Range      = 0;
        for (int i_cut = 0; i_cut < m_LayerNum; ++i_cut)
        {
            for (int i_moment = 0; i_moment < m_RadarData_org->radials[ElRadialIndex[i_cut]].momentblock.size(); ++i_moment)
            {
                if (m_RadarData_org->radials[ElRadialIndex[i_cut]].momentblock[i_moment].momentheader.DataType \
                        == (m_RadarProParameters_org->at(i_pro).ProInfo.ProductionID - 100))
                {
                    info.varCutNum++;
                    info.varElCutIndex.resize(info.varCutNum);
                    info.varMomentIndex.resize(info.varCutNum);
                    info.varElRadialNum.resize(info.varCutNum);
                    info.varElRadialIndex.resize(info.varCutNum);
                    info.varBinNum.resize(info.varCutNum);
                    info.varBinWidth.resize(info.varCutNum);
                    info.varElCutIndex[info.varCutNum - 1]      = i_cut;
                    info.varMomentIndex[info.varCutNum - 1]     = i_moment;
                    info.varElRadialNum[info.varCutNum - 1]     = ElRadialNum[i_cut];
                    info.varElRadialIndex[info.varCutNum - 1]   = ElRadialIndex[i_cut];
                    int binWidth, binNum;
                    if ((m_RadarProParameters_org->at(i_pro).ProInfo.ProductionID - 100) == 3 ||
                        (m_RadarProParameters_org->at(i_pro).ProInfo.ProductionID - 100) == 4)
                    {
                        binWidth    = m_RadarData_org->commonBlock.cutconfig[i_cut].DopplerResolution;
                    } else {
                        binWidth    = m_RadarData_org->commonBlock.cutconfig[i_cut].LogResolution;
                    }
                    binNum          = m_RadarData_org->radials[ElRadialIndex[i_cut]].momentblock[i_moment].momentheader.Length \
                                    / m_RadarData_org->radials[ElRadialIndex[i_cut]].momentblock[i_moment].momentheader.BinLength;
                    info.varBinNum[info.varCutNum - 1]          = binNum;
                    info.varBinWidth[info.varCutNum - 1]        = binWidth;
                    if (info.Range < binNum*binWidth)
                    {
                        info.Range  = binNum * binWidth;
                        info.BinNum = binNum;
                        info.BinWidth   = binWidth;
                    }
                    break;
                }
            }
        }
        info.DataType       = m_RadarProParameters_org->at(i_pro).ProInfo.ProductionID - 100;
        info.RadarWestLongitude = m_RadarHead_org->siteconfig.Longitude - \
                (info.BinWidth*info.BinNum)/(110000.0*cos(m_RadarHead_org->siteconfig.Latitude/180.0*PI));
        info.RadarEastLongitude = m_RadarHead_org->siteconfig.Longitude + \
                (info.BinWidth*info.BinNum)/(110000.0*cos(m_RadarHead_org->siteconfig.Latitude/180.0*PI));
        info.RadarSouthLatitude = m_RadarHead_org->siteconfig.Latitude - \
                (info.BinWidth*info.BinNum)/110000.0;
        info.RadarNorthLatitude = m_RadarHead_org->siteconfig.Latitude + \
                (info.BinWidth*info.BinNum)/110000.0;

        m_VarInfo[i_pro]    = info;
    }
}

int CAlgoCAPPI::GetRadarPara()
{
    m_binNumber = m_RadarData_org->radials[0].momentblock[0].momentheader.Length \
            / m_RadarData_org->radials[0].momentblock[0].momentheader.BinLength;
    m_binWidth = m_RadarHead_org->cutconfig[0].LogResolution;
    float elev = m_RadarHead_org->cutconfig[0].Elevation;
    float tmpV = 0;
    Calclonlat(m_RadarHead_org->siteconfig.Longitude, m_RadarHead_org->siteconfig.Latitude, m_RadarHead_org->siteconfig.AntennaHeight, \
               elev, 0, m_binWidth*m_binNumber, tmpV, m_RadarNorthLatitude);        //雷达北边界
    Calclonlat(m_RadarHead_org->siteconfig.Longitude, m_RadarHead_org->siteconfig.Latitude, m_RadarHead_org->siteconfig.AntennaHeight, \
               elev, 180, m_binWidth*m_binNumber, tmpV, m_RadarSouthLatitude);      //雷达南边界
    Calclonlat(m_RadarHead_org->siteconfig.Longitude, m_RadarHead_org->siteconfig.Latitude, m_RadarHead_org->siteconfig.AntennaHeight, \
               elev, 90, m_binWidth*m_binNumber, m_RadarEastLongitude, tmpV);       //雷达东边界
    Calclonlat(m_RadarHead_org->siteconfig.Longitude, m_RadarHead_org->siteconfig.Latitude, m_RadarHead_org->siteconfig.AntennaHeight, \
               elev, 270, m_binWidth*m_binNumber, m_RadarWestLongitude, tmpV);      //雷达西边界

//    m_RadarWestLongitude = m_RadarHead_org->siteconfig.Longitude - \
//            (m_binWidth*m_binNumber)/(110000.0*cos(m_RadarHead_org->siteconfig.Latitude/180.0*PI));
//    //雷达西边界，以北纬60°为例，东西方向约55000 m/°
//    m_RadarEastLongitude = m_RadarHead_org->siteconfig.Longitude + \
//            (m_binWidth*m_binNumber)/(110000.0*cos(m_RadarHead_org->siteconfig.Latitude/180.0*PI));
//    //雷达东边界
//    m_RadarSouthLatitude = m_RadarHead_org->siteconfig.Latitude - \
//            (m_binWidth*m_binNumber)/110000.0;
//    //雷达南边界，南北方向约110000.0 m/°
//    m_RadarNorthLatitude = m_RadarHead_org->siteconfig.Latitude + \
//            (m_binWidth*m_binNumber)/110000.0;
//    //雷达北边界
    return 0;
}

int CAlgoCAPPI::InitGridPara()
{
    for (int i_Pro = 0 ; i_Pro<m_RadarPro->size();i_Pro++) {
        if (m_RadarProParameters_org->at(i_Pro).ProInfo.ProductionID - 100 == 2){
            m_binNumber = m_VarInfo.at(i_Pro).BinNum;
            m_binWidth  = m_VarInfo.at(i_Pro).BinWidth;
        }
    }
    for (int i_Pro = 0 ; i_Pro<m_RadarPro->size();i_Pro++) {
        if (m_RadarPro->at(i_Pro).MapProjInfo.ctrlat == PREFILLVALUE || m_RadarPro->at(i_Pro).MapProjInfo.ctrlon == PREFILLVALUE)
        {
            m_RadarPro->at(i_Pro).MapProjInfo.ctrlat = m_RadarHead_org->siteconfig.Latitude;
            m_RadarPro->at(i_Pro).MapProjInfo.ctrlon = m_RadarHead_org->siteconfig.Longitude;
        }
        if (m_RadarPro->at(i_Pro).GridInfo.drow == abs(PREFILLVALUE) || m_RadarPro->at(i_Pro).GridInfo.dcolumn == abs(PREFILLVALUE)) {
            m_RadarPro->at(i_Pro).GridInfo.drow = m_RadarHead_org->cutconfig.front().LogResolution * 2;
            m_RadarPro->at(i_Pro).GridInfo.dcolumn = m_RadarHead_org->cutconfig.front().LogResolution * 2;
        }
        if (m_RadarPro->at(i_Pro).GridInfo.nrow == abs(PREFILLVALUE) || m_RadarPro->at(i_Pro).GridInfo.ncolumn == abs(PREFILLVALUE)) {
            // unit of drow and dcolumn: 1/50000degree
//            m_RadarPro->at(i_Pro).GridInfo.nrow = ceil(1.0*(m_binWidth*m_binNumber)/(110000.0*cos(m_RadarHead_org->siteconfig.Latitude/180.0*PI))/m_RadarPro->at(i_Pro).GridInfo.drow*50000/50)*100;
//            m_RadarPro->at(i_Pro).GridInfo.ncolumn = ceil(1.0*(m_binWidth*m_binNumber)/110000.0/m_RadarPro->at(i_Pro).GridInfo.dcolumn*50000/50)*100;
//            m_RadarPro->at(i_Pro).GridInfo.nrow = 2 * ceil((m_RadarNorthLatitude - m_RadarPro->at(i_Pro).MapProjInfo.ctrlat) / m_RadarPro->at(i_Pro).GridInfo.drow * 50000.0);
//            m_RadarPro->at(i_Pro).GridInfo.ncolumn = 2 * ceil((m_RadarEastLongitude - m_RadarPro->at(i_Pro).MapProjInfo.ctrlon) / m_RadarPro->at(i_Pro).GridInfo.dcolumn * 50000.0);
            m_RadarPro->at(i_Pro).GridInfo.nrow = 2 * ceil((m_RadarEastLongitude - m_RadarPro->at(i_Pro).MapProjInfo.ctrlon) / m_RadarPro->at(i_Pro).GridInfo.dcolumn * 50000.0);
            m_RadarPro->at(i_Pro).GridInfo.ncolumn = 2 * ceil((m_RadarNorthLatitude - m_RadarPro->at(i_Pro).MapProjInfo.ctrlat) / m_RadarPro->at(i_Pro).GridInfo.drow * 50000.0);
        }
        if (m_RadarPro->at(i_Pro).MapProjInfo.mapproj == 1) // 1=Lambert; 2=lat-lon
        {
            if(m_DebugLevel <= 0){
                set_time_str();
                cout << time_str;
                cout << " Algo_CAPPI::" ;
                cout << "Do not support Lambert map projection(1) now! Please use lat-lon map projection(2)!" << endl;
            }
            return -1;
        }
        else if (m_RadarPro->at(i_Pro).MapProjInfo.mapproj == 2)
        {
            if(m_DebugLevel <= 0 && i_Pro == 0){
                set_time_str();
                cout << time_str;
                cout << " Algo_CAPPI::" ;
                cout << "Use lat-lon!";
                cout << "central lat = ";
                cout << m_RadarPro->at(i_Pro).MapProjInfo.ctrlat;
                cout << "; lon = ";
                cout << m_RadarPro->at(i_Pro).MapProjInfo.ctrlon;
                cout << "; nx = ";
                cout << m_RadarPro->at(i_Pro).GridInfo.nrow;
                cout << "; dx = ";
                cout << m_RadarPro->at(i_Pro).GridInfo.drow / 50000.0;
                cout << " °";
                cout << "; ny = ";
                cout << m_RadarPro->at(i_Pro).GridInfo.ncolumn;
                cout << "; dy = ";
                cout << m_RadarPro->at(i_Pro).GridInfo.dcolumn / 50000.0;
                cout << " °";
                cout << "; nz = ";
                cout << (int)m_RadarPro->at(i_Pro).GridInfo.nz;
                cout << ";" << endl;
            }
        }
    }

    int GridNum = (int)m_RadarPro->at(0).GridInfo.nz * m_RadarPro->at(0).GridInfo.ncolumn * m_RadarPro->at(0).GridInfo.nrow;
    m_GridLat = new float[GridNum];
    m_GridLon = new float[GridNum];
    m_GridHeight = new float[GridNum];
    #pragma omp parallel for
    for (int iz = 0; iz < m_RadarPro->at(0).GridInfo.nz; iz++)
        for (int iy = 0; iy < m_RadarPro->at(0).GridInfo.ncolumn; iy++)
            for (int ix = 0; ix < m_RadarPro->at(0).GridInfo.nrow; ix++)
            {
                int GridIndex = iz * m_RadarPro->at(0).GridInfo.nrow * m_RadarPro->at(0).GridInfo.ncolumn + iy * m_RadarPro->at(0).GridInfo.nrow + ix;
                if (m_RadarPro->at(0).MapProjInfo.mapproj == 1) // 1=Lambert; 2=lat-lon
                {

                }
                else if (m_RadarPro->at(0).MapProjInfo.mapproj == 2)
                {
                    m_GridLon[GridIndex] = m_RadarPro->at(0).MapProjInfo.ctrlon + \
                            (ix - m_RadarPro->at(0).GridInfo.nrow / 2) * m_RadarPro->at(0).GridInfo.drow / 50000.0;      //单位 °
                    m_GridLat[GridIndex] = m_RadarPro->at(0).MapProjInfo.ctrlat + \
                            (iy - m_RadarPro->at(0).GridInfo.ncolumn / 2) * m_RadarPro->at(0).GridInfo.dcolumn / 50000.0;
                }
                m_GridHeight[GridIndex] = m_RadarPro->at(0).GridInfo.z[iz];
            }
    return 0;
}

int CAlgoCAPPI::InitProGrid()
{
    int GridNum = (int)m_RadarPro->at(0).GridInfo.nz * m_RadarPro->at(0).GridInfo.ncolumn * m_RadarPro->at(0).GridInfo.nrow;
    #pragma omp parallel for
    for (int i_Pro = 0 ; i_Pro<m_RadarPro->size();i_Pro++) {
        if (m_VarInfo.at(i_Pro).varElCutIndex.size() == 0) continue;
        m_RadarPro->at(i_Pro).SiteInfo.resize(1);
        memcpy(m_RadarPro->at(i_Pro).SiteInfo.at(0).SiteCode, m_RadarHead_org->siteconfig.SiteCode, sizeof(m_RadarPro->at(i_Pro).SiteInfo.at(0).SiteCode));
        memcpy(m_RadarPro->at(i_Pro).SiteInfo.at(0).SiteName, m_RadarHead_org->siteconfig.SiteName, sizeof(m_RadarPro->at(i_Pro).SiteInfo.at(0).SiteName));
        m_RadarPro->at(i_Pro).SiteInfo.at(0).Latitude = m_RadarHead_org->siteconfig.Latitude;
        m_RadarPro->at(i_Pro).SiteInfo.at(0).Longitude = m_RadarHead_org->siteconfig.Longitude;
        m_RadarPro->at(i_Pro).SiteInfo.at(0).AntennaHeight = m_RadarHead_org->siteconfig.AntennaHeight;
        m_RadarPro->at(i_Pro).SiteInfo.at(0).GroundHeight = m_RadarHead_org->siteconfig.GroundHeight;
        m_RadarPro->at(i_Pro).SiteInfo.at(0).Frequency = m_RadarHead_org->siteconfig.Frequency;
        m_RadarPro->at(i_Pro).SiteInfo.at(0).BeamWidthHori = m_RadarHead_org->siteconfig.BeamWidthHori;
        m_RadarPro->at(i_Pro).SiteInfo.at(0).BeamWidthVert = m_RadarHead_org->siteconfig.BeamWidthVert;
        m_RadarPro->at(i_Pro).SiteInfo.at(0).RdaVersion = m_RadarHead_org->siteconfig.RdaVersion;
        m_RadarPro->at(i_Pro).SiteInfo.at(0).RadarType = m_RadarHead_org->siteconfig.RadarType;
        if(m_RadarData_org->commonBlock.genericheader.MagicNumber == 0x4D545352)
            m_RadarPro->at(i_Pro).ProInfo.MagicNumber=0x45673210;
        else if(m_RadarData_org->commonBlock.genericheader.MagicNumber == 0x4D545353)
            m_RadarPro->at(i_Pro).ProInfo.MagicNumber=0x45673211;
        //        m_RadarPro->at(i_Pro).ProInfo.MagicNumber=0x45673210;
        switch(m_RadarPro->at(i_Pro).ProInfo.ProductionID)
        {
        case 101:
            strncpy(m_RadarPro->at(i_Pro).ProInfo.ProductionName, "dBTCAPPI",sizeof (m_RadarPro->at(i_Pro).ProInfo.ProductionName)-1);
            break;
        case 102:
            strncpy(m_RadarPro->at(i_Pro).ProInfo.ProductionName, "dBZCAPPI",sizeof (m_RadarPro->at(i_Pro).ProInfo.ProductionName)-1);
            break;
        case 103:
            strncpy(m_RadarPro->at(i_Pro).ProInfo.ProductionName, "VCAPPI",sizeof (m_RadarPro->at(i_Pro).ProInfo.ProductionName)-1);
            break;
        case 104:
            strncpy(m_RadarPro->at(i_Pro).ProInfo.ProductionName, "WCAPPI",sizeof (m_RadarPro->at(i_Pro).ProInfo.ProductionName)-1);
            break;
        case 107:
            strncpy(m_RadarPro->at(i_Pro).ProInfo.ProductionName, "ZDRCAPPI",sizeof (m_RadarPro->at(i_Pro).ProInfo.ProductionName)-1);
            break;
        case 108:
            strncpy(m_RadarPro->at(i_Pro).ProInfo.ProductionName, "LDRCAPPI",sizeof (m_RadarPro->at(i_Pro).ProInfo.ProductionName)-1);
            break;
        case 109:
            strncpy(m_RadarPro->at(i_Pro).ProInfo.ProductionName, "ROHVCAPPI",sizeof (m_RadarPro->at(i_Pro).ProInfo.ProductionName)-1);
            break;
        case 110:
            strncpy(m_RadarPro->at(i_Pro).ProInfo.ProductionName, "PHDPCAPPI",sizeof (m_RadarPro->at(i_Pro).ProInfo.ProductionName)-1);
            break;
        case 111:
            strncpy(m_RadarPro->at(i_Pro).ProInfo.ProductionName, "KDPCAPPI",sizeof (m_RadarPro->at(i_Pro).ProInfo.ProductionName)-1);
            break;
        }
        strncpy(m_RadarPro->at(i_Pro).ProInfo.ProductMethod, "interp8", sizeof(m_RadarPro->at(i_Pro).ProInfo.ProductMethod)-1);
        m_RadarPro->at(i_Pro).ProInfo.DataStartTime = PREFILLVALUE; //m_RadarHead_org->taskconfig.ScanStartTime;                                          //数据开始的时间，自1970年1月1日以来的秒数
        m_RadarPro->at(i_Pro).ProInfo.DataEndTime = PREFILLVALUE;
        m_RadarPro->at(i_Pro).ProInfo.ProductionTime = PREFILLVALUE;
//        int time_temp_start = 2e10;
//        int time_temp_end = -1;
//        for (int i_radial = m_RadarData_org->radials.size()-1; i_radial > 0; i_radial-=10){
//            if (m_RadarData_org->radials[i_radial].radialheader.Seconds \
//                    - m_RadarHead_org->taskconfig.ScanStartTime < 1000) {
//                if (m_RadarData_org->radials[i_radial].radialheader.Seconds > time_temp_end) {
//                    time_temp_end = m_RadarData_org->radials[i_radial].radialheader.Seconds;
//                }
//                if (m_RadarData_org->radials[i_radial].radialheader.Seconds < time_temp_start) {
//                    time_temp_start = m_RadarData_org->radials[i_radial].radialheader.Seconds;
//                }
//            }
//        }

        //m_RadarPro->at(i_Pro).ProInfo.DataStartTime = time_temp_start;
        //m_RadarPro->at(i_Pro).ProInfo.DataEndTime = time_temp_end;  //数据结束的时间，自1970年1月1日以来的秒数
        //如果是KJC，则从Reserved中取出结束时间，赋值给m_RadarPro->at(i_Pro).ProInfo.DataEndTime
        //如果不是KJC，则无所谓结束时间是啥，但此时Reserved为0，无法取出时间
        time_t ScanEndTime = m_RadarData_org->radials.back().radialheader.Seconds;
        if(m_RadarData_org->commonBlockPAR.siteconfig.Reserved[0] != '\0'){
            char nameFromRawfile[64]={0};
            strncpy(nameFromRawfile,m_RadarData_org->commonBlockPAR.siteconfig.Reserved,26);
            string SYear=string(nameFromRawfile).substr(12,4);
            string SMonth=string(nameFromRawfile).substr(16,2);
            string SDay=string(nameFromRawfile).substr(18,2);
            string SHour=string(nameFromRawfile).substr(20,2);
            string SMinute=string(nameFromRawfile).substr(22,2);
            string SSecond=string(nameFromRawfile).substr(24,2);
            ScanEndTime = time_convert(atoi(SYear.c_str()), atoi(SMonth.c_str()), atoi(SDay.c_str()), atoi(SHour.c_str()), atoi(SMinute.c_str()), atoi(SSecond.c_str()));
        }
        m_RadarPro->at(i_Pro).ProInfo.DataStartTime = m_RadarData_org->commonBlock.taskconfig.ScanStartTime;
        m_RadarPro->at(i_Pro).ProInfo.DataEndTime = ScanEndTime;//m_RadarData_org->radials.back().radialheader.Seconds;  //数据结束的时间，自1970年1月1日以来的秒数
//        m_RadarPro->at(i_Pro).ProInfo.ProductionTime = m_RadarPro->at(i_Pro).ProInfo.DataStartTime;    //数据产品生成的时间，自1970年1月1日以来的秒数
        m_RadarPro->at(i_Pro).ProInfo.ProductionTime = m_RadarData_org->commonBlock.taskconfig.ScanStartTime;
        m_RadarPro->at(i_Pro).ProInfo.DataFormat = 102;   //产品格式   1=径向格式  2=栅格格式  101=多层径向格式  102=多层栅格格式   201=特定格式   202=文本格式

        m_RadarPro->at(i_Pro).DataBlock.resize(1);
        m_RadarPro->at(i_Pro).DataBlock.at(0).ProDataInfo.DScale = m_RadarData_org->radials[m_VarInfo.at(i_Pro).varElRadialIndex.front()].momentblock[m_VarInfo.at(i_Pro).varMomentIndex.front()].momentheader.Scale;
        m_RadarPro->at(i_Pro).DataBlock.at(0).ProDataInfo.DOffset = m_RadarData_org->radials[m_VarInfo.at(i_Pro).varElRadialIndex.front()].momentblock[m_VarInfo.at(i_Pro).varMomentIndex.front()].momentheader.Offset;
        m_RadarPro->at(i_Pro).DataBlock.at(0).ProDataInfo.DZero = INVALID_BT;
        m_RadarPro->at(i_Pro).DataBlock.at(0).ProDataInfo.BinLength = m_RadarData_org->radials[m_VarInfo.at(i_Pro).varElRadialIndex.front()].momentblock[m_VarInfo.at(i_Pro).varMomentIndex.front()].momentheader.BinLength;

        m_RadarPro->at(i_Pro).DataBlock.at(0).ProductData.resize(GridNum * m_RadarPro->at(i_Pro).DataBlock.at(0).ProDataInfo.BinLength);
        vector<unsigned short> temp(GridNum,INVALID_BT);
        memcpy(&m_RadarPro->at(i_Pro).DataBlock.at(0).ProductData.at(0),&temp.at(0),m_RadarPro->at(i_Pro).DataBlock.at(0).ProductData.size());
    }

    return 0;
}

int CAlgoCAPPI::CalcCAPPI()
{
    #pragma omp parallel for
    for (int iz = 0; iz < m_RadarPro->at(0).GridInfo.nz; iz++)
    {
        if (m_DebugLevel <= 0){
            set_time_str();
            cout << time_str;
            cout << "Algo_CAPPI::";
            cout << "Thread num = "<< omp_get_thread_num() << ". ";
            cout << "Height of layer ";
            cout << iz + 1;
            cout << " is ";
            cout << m_RadarPro->at(0).GridInfo.z[iz];
            cout << " m." << endl;
        }
        for (int iy = 0; iy < m_RadarPro->at(0).GridInfo.ncolumn; iy++)
            for (int ix = 0; ix < m_RadarPro->at(0).GridInfo.nrow; ix++)
            {
                int GridIndex = iz * m_RadarPro->at(0).GridInfo.nrow * m_RadarPro->at(0).GridInfo.ncolumn + iy * m_RadarPro->at(0).GridInfo.nrow + ix;
                int status  = CalcOneGrid_NEW(GridIndex);
            }
    }

    if (m_DebugLevel <= 0){
        set_time_str();
        cout << time_str;
        cout << " Algo_CAPPI::" ;
        cout <<"Time of layer "<<m_RadarData_org->radials.front().radialheader.ElevationNumber<<" is "<<m_RadarData_org->radials.at(m_RadarData_org->radials.size()/2).radialheader.Seconds<<". ";
        cout <<"Time of layer "<<m_RadarData_org->radials.back().radialheader.ElevationNumber<<" is "<<m_RadarData_org->radials.back().radialheader.Seconds<<". ";
        cout << endl;
    }

    return 0;
}

int CAlgoCAPPI::CalcOneGrid(int iGrid)
{
    int status = 0;

    float i_GridtoRadarElev;   //仰角，计数单位 度
    float i_GridtoRadarAz;     //方位，计数单位 度
    float i_GridtoRadarDis;    //库长，以 米为计数单位
    float i_GridtoRadarBin;

    if ((m_GridLat[iGrid] < m_RadarSouthLatitude) || (m_GridLat[iGrid] > m_RadarNorthLatitude) || \
            (m_GridLon[iGrid] < m_RadarWestLongitude) || (m_GridLon[iGrid] > m_RadarEastLongitude)) return 0;

    status = CalcGridtoRadarLoc(&i_GridtoRadarElev, &i_GridtoRadarAz, &i_GridtoRadarDis, iGrid);
    if (status) return 0;

    for (int i_Pro = 0; i_Pro < m_RadarPro->size();i_Pro++) {
        if (m_moment_index.at(i_Pro).size() == 0 ) continue;
        int i_DataType = m_RadarPro->at(i_Pro).ProInfo.ProductionID - 100;
        if (i_DataType == 3 || i_DataType == 4) {
            m_binWidth = m_RadarHead_org->cutconfig[m_moment_index.at(i_Pro).front().cut_index].DopplerResolution;
        }
        else {
            m_binWidth = m_RadarHead_org->cutconfig[m_moment_index.at(i_Pro).front().cut_index].LogResolution;
        }

        i_GridtoRadarBin = i_GridtoRadarDis / m_binWidth;

        int i_BinFarIndex = ceil(i_GridtoRadarBin);
        int i_BinNearIndex = floor(i_GridtoRadarBin);
        int i_RecordLowLeftIndex;
        int i_RecordLowRightIndex;
        int i_RecordHighLeftIndex;
        int i_RecordHighRightIndex;
        int i_moment_index_low;
        int i_moment_index_high;

        status = FindGridtoRadarIndex(i_GridtoRadarElev, i_GridtoRadarAz, i_Pro, &i_RecordLowLeftIndex, &i_RecordLowRightIndex, &i_RecordHighLeftIndex, &i_RecordHighRightIndex,&i_moment_index_low,&i_moment_index_high);
        if (status) return 0;

        unsigned short i_RadarDataLowLeftNear;
        unsigned short i_RadarDataLowLeftFar;
        unsigned short i_RadarDataLowRightNear;
        unsigned short i_RadarDataLowRightFar;
        unsigned short i_RadarDataHighLeftNear;
        unsigned short i_RadarDataHighLeftFar;
        unsigned short i_RadarDataHighRightNear;
        unsigned short i_RadarDataHighRightFar;

        unsigned short* i_RadarDataTemp;
        int i_BinNum;
        i_RadarDataTemp = (unsigned short*)&(m_RadarData_org->radials[i_RecordLowLeftIndex].momentblock[i_moment_index_low].momentdata[0]);
        i_BinNum = m_RadarData_org->radials[i_RecordLowLeftIndex].momentblock[i_moment_index_low].momentdata.size()/2;
        if (i_BinNearIndex >= i_BinNum){
            i_RadarDataLowLeftNear = INVALID_BT;
        }
        else {
            i_RadarDataLowLeftNear = *(i_RadarDataTemp+i_BinNearIndex);
        }
        if (i_BinNearIndex >= i_BinNum){
            i_RadarDataLowLeftFar = INVALID_BT;
        }
        else {
            i_RadarDataLowLeftFar = *(i_RadarDataTemp+i_BinFarIndex);
        }

        i_RadarDataTemp = (unsigned short*)&(m_RadarData_org->radials[i_RecordLowRightIndex].momentblock[i_moment_index_low].momentdata[0]);
        if (i_BinNearIndex >= i_BinNum){
            i_RadarDataLowRightNear = INVALID_BT;
        }
        else {
            i_RadarDataLowRightNear = *(i_RadarDataTemp+i_BinNearIndex);
        }
        if (i_BinNearIndex >= i_BinNum){
            i_RadarDataLowRightFar = INVALID_BT;
        }
        else {
            i_RadarDataLowRightFar = *(i_RadarDataTemp+i_BinFarIndex);
        }

        i_RadarDataTemp = (unsigned short*)&(m_RadarData_org->radials[i_RecordHighLeftIndex].momentblock[i_moment_index_high].momentdata[0]);
        i_BinNum = m_RadarData_org->radials[i_RecordHighLeftIndex].momentblock[i_moment_index_high].momentdata.size()/2;
        if (i_BinNearIndex >= i_BinNum){
            i_RadarDataHighLeftNear = INVALID_BT;
        }
        else {
            i_RadarDataHighLeftNear = *(i_RadarDataTemp+i_BinNearIndex);
        }
        if (i_BinNearIndex >= i_BinNum){
            i_RadarDataHighLeftFar = INVALID_BT;
        }
        else {
            i_RadarDataHighLeftFar = *(i_RadarDataTemp+i_BinFarIndex);
        }

        i_RadarDataTemp = (unsigned short*)&(m_RadarData_org->radials[i_RecordHighRightIndex].momentblock[i_moment_index_high].momentdata[0]);
        if (i_BinNearIndex >= i_BinNum){
            i_RadarDataHighRightNear = INVALID_BT;
        }
        else {
            i_RadarDataHighRightNear = *(i_RadarDataTemp+i_BinNearIndex);
        }
        if (i_BinNearIndex >= i_BinNum){
            i_RadarDataHighRightFar = INVALID_BT;
        }
        else {
            i_RadarDataHighRightFar = *(i_RadarDataTemp+i_BinFarIndex);
        }

        int CountNum = 0;
        float Sum = 0;
        if (i_RadarDataLowLeftNear > INVALID_RSV)
        {
            Sum += i_RadarDataLowLeftNear;
            CountNum++;
        }
        if (i_RadarDataLowLeftFar > INVALID_RSV)
        {
            Sum += i_RadarDataLowLeftFar;
            CountNum++;
        }
        if (i_RadarDataLowRightNear > INVALID_RSV)
        {
            Sum += i_RadarDataLowRightNear;
            CountNum++;
        }
        if (i_RadarDataLowRightFar > INVALID_RSV)
        {
            Sum += i_RadarDataLowRightFar;
            CountNum++;
        }
        if (i_RadarDataHighLeftNear > INVALID_RSV)
        {
            Sum += i_RadarDataHighLeftNear;
            CountNum++;
        }
        if (i_RadarDataHighLeftFar > INVALID_RSV)
        {
            Sum += i_RadarDataHighLeftFar;
            CountNum++;
        }
        if (i_RadarDataHighRightNear > INVALID_RSV)
        {
            Sum += i_RadarDataHighLeftNear;
            CountNum++;
        }
        if(i_RadarDataHighRightFar > INVALID_RSV)
        {
            Sum += i_RadarDataHighRightFar;
            CountNum++;
        }

        if (CountNum < 6)return 0;
        Sum /= CountNum;

        if (i_RadarDataLowLeftNear <= INVALID_RSV)
        {
            i_RadarDataLowLeftNear = Sum;
        }
        if (i_RadarDataLowLeftFar <= INVALID_RSV)
        {
            i_RadarDataLowLeftFar = Sum;
        }
        if (i_RadarDataLowRightNear <= INVALID_RSV)
        {
            i_RadarDataLowRightNear = Sum;
        }
        if (i_RadarDataLowRightFar <= INVALID_RSV)
        {
            i_RadarDataLowRightFar = Sum;
        }
        if (i_RadarDataHighLeftNear <= INVALID_RSV)
        {
            i_RadarDataHighLeftNear = Sum;
        }
        if (i_RadarDataHighLeftFar <= INVALID_RSV)
        {
            i_RadarDataHighLeftFar = Sum;
        }
        if (i_RadarDataHighRightNear <= INVALID_RSV)
        {
            i_RadarDataHighLeftNear = Sum;
        }
        if(i_RadarDataHighRightFar <= INVALID_RSV)
        {
            i_RadarDataHighRightFar = Sum;
        }


        float i_ProLowLeft = (i_RadarDataLowLeftNear * (i_BinFarIndex - i_GridtoRadarBin) - i_RadarDataLowLeftFar * (i_BinNearIndex - i_GridtoRadarBin)) / (i_BinFarIndex - i_BinNearIndex);
        float i_ProLowRight = (i_RadarDataLowRightNear * (i_BinFarIndex - i_GridtoRadarBin) - i_RadarDataLowRightFar * (i_BinNearIndex - i_GridtoRadarBin)) / (i_BinFarIndex - i_BinNearIndex);
        float i_ProHighLeft = (i_RadarDataHighLeftNear * (i_BinFarIndex - i_GridtoRadarBin) - i_RadarDataHighLeftFar * (i_BinNearIndex - i_GridtoRadarBin)) / (i_BinFarIndex - i_BinNearIndex);
        float i_ProHighRight = (i_RadarDataHighRightNear * (i_BinFarIndex - i_GridtoRadarBin) - i_RadarDataHighRightFar * (i_BinNearIndex - i_GridtoRadarBin)) / (i_BinFarIndex - i_BinNearIndex);
        float i_ProLow, i_ProHigh;
        if (m_RadarData_org->radials[i_RecordLowRightIndex].radialheader.Azimuth <= 1 && m_RadarData_org->radials[i_RecordLowLeftIndex].radialheader.Azimuth >= 359)
            if (i_GridtoRadarAz <= 1)
                i_ProLow = (i_ProLowLeft * (m_RadarData_org->radials[i_RecordLowRightIndex].radialheader.Azimuth - i_GridtoRadarAz) - \
                            i_ProLowRight * (m_RadarData_org->radials[i_RecordLowLeftIndex].radialheader.Azimuth - 360 - i_GridtoRadarAz)) / \
                        (m_RadarData_org->radials[i_RecordLowRightIndex].radialheader.Azimuth + 360 - m_RadarData_org->radials[i_RecordLowLeftIndex].radialheader.Azimuth);
            else
                i_ProLow = (i_ProLowLeft * (m_RadarData_org->radials[i_RecordLowRightIndex].radialheader.Azimuth + 360 - i_GridtoRadarAz) - \
                            i_ProLowRight * (m_RadarData_org->radials[i_RecordLowLeftIndex].radialheader.Azimuth - i_GridtoRadarAz)) / \
                        (m_RadarData_org->radials[i_RecordLowRightIndex].radialheader.Azimuth + 360 - m_RadarData_org->radials[i_RecordLowLeftIndex].radialheader.Azimuth);
        else
            i_ProLow = (i_ProLowLeft * (m_RadarData_org->radials[i_RecordLowRightIndex].radialheader.Azimuth - i_GridtoRadarAz) - \
                        i_ProLowRight * (m_RadarData_org->radials[i_RecordLowLeftIndex].radialheader.Azimuth - i_GridtoRadarAz)) / \
                    (m_RadarData_org->radials[i_RecordLowRightIndex].radialheader.Azimuth - m_RadarData_org->radials[i_RecordLowLeftIndex].radialheader.Azimuth);
        if (m_RadarData_org->radials[i_RecordHighRightIndex].radialheader.Azimuth <= 1 && m_RadarData_org->radials[i_RecordHighLeftIndex].radialheader.Azimuth >= 359)
            if (i_GridtoRadarAz <= 1)
                i_ProHigh = (i_ProHighLeft * (m_RadarData_org->radials[i_RecordHighRightIndex].radialheader.Azimuth - i_GridtoRadarAz) - \
                             i_ProHighRight * (m_RadarData_org->radials[i_RecordHighLeftIndex].radialheader.Azimuth - 360 - i_GridtoRadarAz)) / \
                        (m_RadarData_org->radials[i_RecordHighRightIndex].radialheader.Azimuth + 360 - m_RadarData_org->radials[i_RecordHighLeftIndex].radialheader.Azimuth);
            else
                i_ProHigh = (i_ProHighLeft * (m_RadarData_org->radials[i_RecordHighRightIndex].radialheader.Azimuth + 360 - i_GridtoRadarAz) - \
                             i_ProHighRight * (m_RadarData_org->radials[i_RecordHighLeftIndex].radialheader.Azimuth - i_GridtoRadarAz)) / \
                        (m_RadarData_org->radials[i_RecordHighRightIndex].radialheader.Azimuth + 360 - m_RadarData_org->radials[i_RecordHighLeftIndex].radialheader.Azimuth);
        else
            i_ProHigh = (i_ProHighLeft * (m_RadarData_org->radials[i_RecordHighRightIndex].radialheader.Azimuth - i_GridtoRadarAz) - \
                         i_ProHighRight * (m_RadarData_org->radials[i_RecordHighLeftIndex].radialheader.Azimuth - i_GridtoRadarAz)) / \
                    (m_RadarData_org->radials[i_RecordHighRightIndex].radialheader.Azimuth - m_RadarData_org->radials[i_RecordHighLeftIndex].radialheader.Azimuth);
        float i_ProTemp = (i_ProLow * (m_RadarData_org->radials[i_RecordHighRightIndex].radialheader.Elevation - i_GridtoRadarElev) - \
                           i_ProHigh * (m_RadarData_org->radials[i_RecordLowRightIndex].radialheader.Elevation - i_GridtoRadarElev)) / \
                (m_RadarData_org->radials[i_RecordHighRightIndex].radialheader.Elevation - m_RadarData_org->radials[i_RecordLowRightIndex].radialheader.Elevation);

        unsigned short i_ProTemp_short = (unsigned short)i_ProTemp;
        if (i_Pro == 1 && i_ProTemp_short < 10000)
            i_ProTemp_short = INVALID_BT;
        memcpy(&m_RadarPro->at(i_Pro).DataBlock.at(0).ProductData.at(iGrid*2),&i_ProTemp_short,2);
    }
    return 0;
}

int CAlgoCAPPI::CalcOneGrid_NEW(int iGrid)
{
    int status = 0;

    float i_GridtoRadarElev;   //仰角，计数单位 度
    float i_GridtoRadarAz;     //方位，计数单位 度
    float i_GridtoRadarDis;    //库长，以 米为计数单位
    float i_GridtoRadarBin;

    status = CalcGridtoRadarLoc(&i_GridtoRadarElev, &i_GridtoRadarAz, &i_GridtoRadarDis, iGrid);
    if (status) return 0;

    for (int i_Pro = 0; i_Pro < m_RadarPro->size();i_Pro++) {
        if ((m_GridLat[iGrid] < m_VarInfo.at(i_Pro).RadarSouthLatitude) || (m_GridLat[iGrid] > m_VarInfo.at(i_Pro).RadarNorthLatitude) || \
            (m_GridLon[iGrid] < m_VarInfo.at(i_Pro).RadarWestLongitude) || (m_GridLon[iGrid] > m_VarInfo.at(i_Pro).RadarEastLongitude))
            continue;

        if (m_VarInfo.at(i_Pro).varElCutIndex.size() == 0) continue;

        i_GridtoRadarBin = i_GridtoRadarDis / m_VarInfo.at(i_Pro).BinWidth;

        int i_BinFarIndex = ceil(i_GridtoRadarBin);
        int i_BinNearIndex = floor(i_GridtoRadarBin);
        int i_RecordLowLeftIndex;
        int i_RecordLowRightIndex;
        int i_RecordHighLeftIndex;
        int i_RecordHighRightIndex;
        int i_moment_index_low;
        int i_moment_index_high;

        status = FindGridtoRadarIndex_NEW(i_GridtoRadarElev, i_GridtoRadarAz, i_Pro, &i_RecordLowLeftIndex, &i_RecordLowRightIndex, &i_RecordHighLeftIndex, &i_RecordHighRightIndex,&i_moment_index_low,&i_moment_index_high);
        if (status) continue;

        unsigned short i_RadarDataLowLeftNear;
        unsigned short i_RadarDataLowLeftFar;
        unsigned short i_RadarDataLowRightNear;
        unsigned short i_RadarDataLowRightFar;
        unsigned short i_RadarDataHighLeftNear;
        unsigned short i_RadarDataHighLeftFar;
        unsigned short i_RadarDataHighRightNear;
        unsigned short i_RadarDataHighRightFar;

        unsigned short* i_RadarDataTemp;
        int i_BinNum;
        i_RadarDataTemp = (unsigned short*)&(m_RadarData_org->radials[i_RecordLowLeftIndex].momentblock[i_moment_index_low].momentdata[0]);
        i_BinNum = m_RadarData_org->radials[i_RecordLowLeftIndex].momentblock[i_moment_index_low].momentdata.size()/2;
        if (i_BinNearIndex >= i_BinNum){
            i_RadarDataLowLeftNear = INVALID_BT;
        }
        else {
            i_RadarDataLowLeftNear = *(i_RadarDataTemp+i_BinNearIndex);
        }
        if (i_BinFarIndex >= i_BinNum){
            i_RadarDataLowLeftFar = INVALID_BT;
        }
        else {
            i_RadarDataLowLeftFar = *(i_RadarDataTemp+i_BinFarIndex);
        }

        i_RadarDataTemp = (unsigned short*)&(m_RadarData_org->radials[i_RecordLowRightIndex].momentblock[i_moment_index_low].momentdata[0]);
        if (i_BinNearIndex >= i_BinNum){
            i_RadarDataLowRightNear = INVALID_BT;
        }
        else {
            i_RadarDataLowRightNear = *(i_RadarDataTemp+i_BinNearIndex);
        }
        if (i_BinFarIndex >= i_BinNum){
            i_RadarDataLowRightFar = INVALID_BT;
        }
        else {
            i_RadarDataLowRightFar = *(i_RadarDataTemp+i_BinFarIndex);
        }

        i_RadarDataTemp = (unsigned short*)&(m_RadarData_org->radials[i_RecordHighLeftIndex].momentblock[i_moment_index_high].momentdata[0]);
        i_BinNum = m_RadarData_org->radials[i_RecordHighLeftIndex].momentblock[i_moment_index_high].momentdata.size()/2;
        if (i_BinNearIndex >= i_BinNum){
            i_RadarDataHighLeftNear = INVALID_BT;
        }
        else {
            i_RadarDataHighLeftNear = *(i_RadarDataTemp+i_BinNearIndex);
        }
        if (i_BinFarIndex >= i_BinNum){
            i_RadarDataHighLeftFar = INVALID_BT;
        }
        else {
            i_RadarDataHighLeftFar = *(i_RadarDataTemp+i_BinFarIndex);
        }

        i_RadarDataTemp = (unsigned short*)&(m_RadarData_org->radials[i_RecordHighRightIndex].momentblock[i_moment_index_high].momentdata[0]);
        if (i_BinNearIndex >= i_BinNum){
            i_RadarDataHighRightNear = INVALID_BT;
        }
        else {
            i_RadarDataHighRightNear = *(i_RadarDataTemp+i_BinNearIndex);
        }
        if (i_BinFarIndex >= i_BinNum){
            i_RadarDataHighRightFar = INVALID_BT;
        }
        else {
            i_RadarDataHighRightFar = *(i_RadarDataTemp+i_BinFarIndex);
        }

        int CountNum = 0;
        float Sum = 0;
        if (i_RadarDataLowLeftNear > INVALID_RSV)
        {
            Sum += i_RadarDataLowLeftNear;
            CountNum++;
        }
        if (i_RadarDataLowLeftFar > INVALID_RSV)
        {
            Sum += i_RadarDataLowLeftFar;
            CountNum++;
        }
        if (i_RadarDataLowRightNear > INVALID_RSV)
        {
            Sum += i_RadarDataLowRightNear;
            CountNum++;
        }
        if (i_RadarDataLowRightFar > INVALID_RSV)
        {
            Sum += i_RadarDataLowRightFar;
            CountNum++;
        }
        if (i_RadarDataHighLeftNear > INVALID_RSV)
        {
            Sum += i_RadarDataHighLeftNear;
            CountNum++;
        }
        if (i_RadarDataHighLeftFar > INVALID_RSV)
        {
            Sum += i_RadarDataHighLeftFar;
            CountNum++;
        }
        if (i_RadarDataHighRightNear > INVALID_RSV)
        {
            Sum += i_RadarDataHighLeftNear;
            CountNum++;
        }
        if(i_RadarDataHighRightFar > INVALID_RSV)
        {
            Sum += i_RadarDataHighRightFar;
            CountNum++;
        }

        if (CountNum < 6)return 0;
        Sum /= CountNum;

        if (i_RadarDataLowLeftNear <= INVALID_RSV)
        {
            i_RadarDataLowLeftNear = Sum;
        }
        if (i_RadarDataLowLeftFar <= INVALID_RSV)
        {
            i_RadarDataLowLeftFar = Sum;
        }
        if (i_RadarDataLowRightNear <= INVALID_RSV)
        {
            i_RadarDataLowRightNear = Sum;
        }
        if (i_RadarDataLowRightFar <= INVALID_RSV)
        {
            i_RadarDataLowRightFar = Sum;
        }
        if (i_RadarDataHighLeftNear <= INVALID_RSV)
        {
            i_RadarDataHighLeftNear = Sum;
        }
        if (i_RadarDataHighLeftFar <= INVALID_RSV)
        {
            i_RadarDataHighLeftFar = Sum;
        }
        if (i_RadarDataHighRightNear <= INVALID_RSV)
        {
            i_RadarDataHighLeftNear = Sum;
        }
        if(i_RadarDataHighRightFar <= INVALID_RSV)
        {
            i_RadarDataHighRightFar = Sum;
        }

        float i_ProLowLeft = (i_RadarDataLowLeftNear * (i_BinFarIndex - i_GridtoRadarBin) - i_RadarDataLowLeftFar * (i_BinNearIndex - i_GridtoRadarBin)) / (i_BinFarIndex - i_BinNearIndex);
        float i_ProLowRight = (i_RadarDataLowRightNear * (i_BinFarIndex - i_GridtoRadarBin) - i_RadarDataLowRightFar * (i_BinNearIndex - i_GridtoRadarBin)) / (i_BinFarIndex - i_BinNearIndex);
        float i_ProHighLeft = (i_RadarDataHighLeftNear * (i_BinFarIndex - i_GridtoRadarBin) - i_RadarDataHighLeftFar * (i_BinNearIndex - i_GridtoRadarBin)) / (i_BinFarIndex - i_BinNearIndex);
        float i_ProHighRight = (i_RadarDataHighRightNear * (i_BinFarIndex - i_GridtoRadarBin) - i_RadarDataHighRightFar * (i_BinNearIndex - i_GridtoRadarBin)) / (i_BinFarIndex - i_BinNearIndex);
        float i_ProLow, i_ProHigh;
        if (m_RadarData_org->radials[i_RecordLowRightIndex].radialheader.Azimuth <= 1 && m_RadarData_org->radials[i_RecordLowLeftIndex].radialheader.Azimuth >= 359)
            if (i_GridtoRadarAz <= 1)
                i_ProLow = (i_ProLowLeft * (m_RadarData_org->radials[i_RecordLowRightIndex].radialheader.Azimuth - i_GridtoRadarAz) - \
                            i_ProLowRight * (m_RadarData_org->radials[i_RecordLowLeftIndex].radialheader.Azimuth - 360 - i_GridtoRadarAz)) / \
                        (m_RadarData_org->radials[i_RecordLowRightIndex].radialheader.Azimuth + 360 - m_RadarData_org->radials[i_RecordLowLeftIndex].radialheader.Azimuth);
            else
                i_ProLow = (i_ProLowLeft * (m_RadarData_org->radials[i_RecordLowRightIndex].radialheader.Azimuth + 360 - i_GridtoRadarAz) - \
                            i_ProLowRight * (m_RadarData_org->radials[i_RecordLowLeftIndex].radialheader.Azimuth - i_GridtoRadarAz)) / \
                        (m_RadarData_org->radials[i_RecordLowRightIndex].radialheader.Azimuth + 360 - m_RadarData_org->radials[i_RecordLowLeftIndex].radialheader.Azimuth);
        else
            i_ProLow = (i_ProLowLeft * (m_RadarData_org->radials[i_RecordLowRightIndex].radialheader.Azimuth - i_GridtoRadarAz) - \
                        i_ProLowRight * (m_RadarData_org->radials[i_RecordLowLeftIndex].radialheader.Azimuth - i_GridtoRadarAz)) / \
                    (m_RadarData_org->radials[i_RecordLowRightIndex].radialheader.Azimuth - m_RadarData_org->radials[i_RecordLowLeftIndex].radialheader.Azimuth);
        if (m_RadarData_org->radials[i_RecordHighRightIndex].radialheader.Azimuth <= 1 && m_RadarData_org->radials[i_RecordHighLeftIndex].radialheader.Azimuth >= 359)
            if (i_GridtoRadarAz <= 1)
                i_ProHigh = (i_ProHighLeft * (m_RadarData_org->radials[i_RecordHighRightIndex].radialheader.Azimuth - i_GridtoRadarAz) - \
                             i_ProHighRight * (m_RadarData_org->radials[i_RecordHighLeftIndex].radialheader.Azimuth - 360 - i_GridtoRadarAz)) / \
                        (m_RadarData_org->radials[i_RecordHighRightIndex].radialheader.Azimuth + 360 - m_RadarData_org->radials[i_RecordHighLeftIndex].radialheader.Azimuth);
            else
                i_ProHigh = (i_ProHighLeft * (m_RadarData_org->radials[i_RecordHighRightIndex].radialheader.Azimuth + 360 - i_GridtoRadarAz) - \
                             i_ProHighRight * (m_RadarData_org->radials[i_RecordHighLeftIndex].radialheader.Azimuth - i_GridtoRadarAz)) / \
                        (m_RadarData_org->radials[i_RecordHighRightIndex].radialheader.Azimuth + 360 - m_RadarData_org->radials[i_RecordHighLeftIndex].radialheader.Azimuth);
        else
            i_ProHigh = (i_ProHighLeft * (m_RadarData_org->radials[i_RecordHighRightIndex].radialheader.Azimuth - i_GridtoRadarAz) - \
                         i_ProHighRight * (m_RadarData_org->radials[i_RecordHighLeftIndex].radialheader.Azimuth - i_GridtoRadarAz)) / \
                    (m_RadarData_org->radials[i_RecordHighRightIndex].radialheader.Azimuth - m_RadarData_org->radials[i_RecordHighLeftIndex].radialheader.Azimuth);
        float i_ProTemp = (i_ProLow * (m_RadarData_org->radials[i_RecordHighRightIndex].radialheader.Elevation - i_GridtoRadarElev) - \
                           i_ProHigh * (m_RadarData_org->radials[i_RecordLowRightIndex].radialheader.Elevation - i_GridtoRadarElev)) / \
                (m_RadarData_org->radials[i_RecordHighRightIndex].radialheader.Elevation - m_RadarData_org->radials[i_RecordLowRightIndex].radialheader.Elevation);

        unsigned short i_ProTemp_short = (unsigned short)i_ProTemp;
        float tmp = 0;
        if (i_Pro == 1){
            if (i_ProTemp_short > INVALID_RSV){
                tmp = (i_ProTemp_short - m_RadarPro->at(i_Pro).DataBlock.at(0).ProDataInfo.DOffset) / m_RadarPro->at(i_Pro).DataBlock.at(0).ProDataInfo.DScale;
                if (tmp < 0) i_ProTemp_short = INVALID_BT;
            }
        }
        memcpy(&m_RadarPro->at(i_Pro).DataBlock.at(0).ProductData.at(iGrid*2), &i_ProTemp_short, 2);
    }
    return 0;
}

int CAlgoCAPPI::CalcGridtoRadarLoc(float* i_GridtoRadarElev, float* i_GridtoRadarAz, float* i_GridtoRadarDis, int iGrid)
{
    float GridLat = m_GridLat[iGrid] / 180.0 * PI;    //unit:°
    float GridLon = m_GridLon[iGrid] / 180.0 * PI;    //unit:°
    float GridHeight = m_GridHeight[iGrid] / 1000.0;  //unit:km
    float RadarLat = m_RadarHead_org->siteconfig.Latitude / 180.0 * PI;
    float RadarLon = m_RadarHead_org->siteconfig.Longitude / 180.0 * PI;
    float RadarHeight = m_RadarHead_org->siteconfig.AntennaHeight / 1000.0;

    float S = R0 * acos(sin(GridLat) * sin(RadarLat) + cos(GridLat) * cos(RadarLat) * cos(GridLon - RadarLon));
    float temp_Elev = atan( (cos(S / Rm) - Rm / (Rm + GridHeight - RadarHeight)) / sin(S / Rm));
    *i_GridtoRadarElev = temp_Elev / PI * 180.0; // * 100;
    if (*i_GridtoRadarElev < m_RadarData_org->radials[0].radialheader.Elevation) return -1;
    if (*i_GridtoRadarElev > m_RadarData_org->radials[m_nRadialNumSum - 1].radialheader.Elevation) return -1;

    float temp_Dis = sin(S / Rm) * (Rm + GridHeight - RadarHeight) / cos(temp_Elev);
    *i_GridtoRadarDis = temp_Dis * 1000; // * 10;
    if (*i_GridtoRadarDis > m_binNumber* m_binWidth) return -1;


    float sinAz = cos(GridLat) * sin(GridLon - RadarLon) / sin(S / R0);
    if (sinAz >= 1) *i_GridtoRadarAz = PI / 2;
    else if (sinAz <= -1) *i_GridtoRadarAz = PI * 3 / 2;
    else
    {
        if (GridLat > RadarLat&& GridLon > RadarLon)
            *i_GridtoRadarAz = asin(sinAz);
        else if (GridLat <= RadarLat)
            *i_GridtoRadarAz = PI - asin(sinAz);
        else if (GridLat > RadarLat&& GridLon < RadarLon)
            *i_GridtoRadarAz = 2 * PI + asin(sinAz);
        else if (GridLat > RadarLat&& GridLon == RadarLon)
            *i_GridtoRadarAz = 0;
    }

    *i_GridtoRadarAz = *i_GridtoRadarAz / PI * 180.0; // * 100;
    return 0;
}

int CAlgoCAPPI::CalcGridtoRadarLoc_NEW(float *i_GridtoRadarElev, float *i_GridtoRadarAz, float *i_GridtoRadarDis, int iGrid, int iPro)
{
    float GridLat = m_GridLat[iGrid] / 180.0 * PI;    //unit:°
    float GridLon = m_GridLon[iGrid] / 180.0 * PI;    //unit:°
    float GridHeight = m_GridHeight[iGrid] / 1000.0;  //unit:km
    float RadarLat = m_RadarHead_org->siteconfig.Latitude / 180.0 * PI;
    float RadarLon = m_RadarHead_org->siteconfig.Longitude / 180.0 * PI;
    float RadarHeight = m_RadarHead_org->siteconfig.AntennaHeight / 1000.0;

    float S = R0 * acos(sin(GridLat) * sin(RadarLat) + cos(GridLat) * cos(RadarLat) * cos(GridLon - RadarLon));
    float temp_Elev = atan( (cos(S / Rm) - Rm / (Rm + GridHeight - RadarHeight)) / sin(S / Rm));
    *i_GridtoRadarElev = temp_Elev / PI * 180.0; // * 100;
    if (*i_GridtoRadarElev < m_RadarData_org->radials[0].radialheader.Elevation) return -1;
    if (*i_GridtoRadarElev > m_RadarData_org->radials[m_nRadialNumSum - 1].radialheader.Elevation) return -1;

    float temp_Dis = sin(S / Rm) * (Rm + GridHeight - RadarHeight) / cos(temp_Elev);
    *i_GridtoRadarDis = temp_Dis * 1000; // * 10;
    if (*i_GridtoRadarDis > m_VarInfo.at(iPro).BinNum* m_VarInfo.at(iPro).BinWidth) return -1;

    float sinAz = cos(GridLat) * sin(GridLon - RadarLon) / sin(S / R0);
    if (sinAz >= 1) *i_GridtoRadarAz = PI / 2;
    else if (sinAz <= -1) *i_GridtoRadarAz = PI * 3 / 2;
    else
    {
        if (GridLat > RadarLat&& GridLon > RadarLon)
            *i_GridtoRadarAz = asin(sinAz);
        else if (GridLat <= RadarLat)
            *i_GridtoRadarAz = PI - asin(sinAz);
        else if (GridLat > RadarLat&& GridLon < RadarLon)
            *i_GridtoRadarAz = 2 * PI + asin(sinAz);
        else if (GridLat > RadarLat&& GridLon == RadarLon)
            *i_GridtoRadarAz = 0;
    }

    *i_GridtoRadarAz = *i_GridtoRadarAz / PI * 180.0; // * 100;
    return 0;
}

int CAlgoCAPPI::FindGridtoRadarIndex(double i_GridtoRadarElev, double i_GridtoRadarAz, int i_Pro, int* i_RecordLowLeftIndex, int* i_RecordLowRightIndex, int* i_RecordHighLeftIndex, int* i_RecordHighRightIndex, int* i_moment_index_low, int* i_moment_index_high)
{
    //int i_RadialSum = 0;
    int i_flag = 0;
    int i_radial_cut = m_RadarData_org->radials.size() / m_RadarData_org->commonBlock.cutconfig.size();
    if (i_GridtoRadarElev <= m_RadarData_org->radials[0].radialheader.Elevation) return -1;
    if (i_GridtoRadarElev >= m_RadarData_org->radials.back().radialheader.Elevation) return -1;
    float dAz = m_RadarData_org->radials[1].radialheader.Azimuth - m_RadarData_org->radials[0].radialheader.Azimuth;
    if (i_GridtoRadarAz > dAz && i_GridtoRadarAz < m_RadarData_org->radials[0].radialheader.Azimuth) return -1;
    if (i_GridtoRadarAz < 360-dAz && i_GridtoRadarAz > m_RadarData_org->radials.back().radialheader.Azimuth) return -1;

    for (int i_radial = 0; i_radial < i_radial_cut; i_radial ++)
    {
        if( i_GridtoRadarAz < m_RadarData_org->radials[i_radial].radialheader.Azimuth + dAz \
                && i_GridtoRadarAz >= m_RadarData_org->radials[i_radial].radialheader.Azimuth ) {
            *i_RecordLowLeftIndex = i_radial;
            i_flag++;
        }
        if( i_GridtoRadarAz < dAz && i_GridtoRadarAz >= m_RadarData_org->radials[i_radial].radialheader.Azimuth -360 \
                && i_GridtoRadarAz < m_RadarData_org->radials[i_radial].radialheader.Azimuth -360 + dAz){
            *i_RecordLowLeftIndex = i_radial;
            i_flag++;
        }
        if( i_GridtoRadarAz >= 360-dAz && i_GridtoRadarAz >= m_RadarData_org->radials[i_radial].radialheader.Azimuth +360 -dAz && \
                i_GridtoRadarAz < m_RadarData_org->radials[i_radial].radialheader.Azimuth +360 ) {
            *i_RecordLowRightIndex = i_radial;
            i_flag++;
        }
        if( i_GridtoRadarAz < 360-dAz && i_GridtoRadarAz >= m_RadarData_org->radials[i_radial].radialheader.Azimuth -dAz \
                && i_GridtoRadarAz < m_RadarData_org->radials[i_radial].radialheader.Azimuth ) {
            *i_RecordLowRightIndex = i_radial;
            i_flag++;
        }
        if(i_flag == 2) break;
    }
    if(i_flag <2) return -1;
    int i_cutNum = m_RadarData_org->commonBlock.cutconfig.size();
    if (m_RadarData_org->commonBlock.cutconfig.back().Elevation \
            - m_RadarData_org->commonBlock.cutconfig.at(m_RadarData_org->commonBlock.cutconfig.size()-2).Elevation > 8) {
        i_cutNum --;
    }

    for (int i_cut_index = 1; i_cut_index < m_moment_index.at(i_Pro).size(); i_cut_index++) {
        auto i_cut = m_moment_index.at(i_Pro).at(i_cut_index).cut_index;
        if (m_RadarData_org->radials[*i_RecordLowLeftIndex+i_cut*i_radial_cut].radialheader.Elevation >= i_GridtoRadarElev) {
            *i_RecordHighLeftIndex = *i_RecordLowLeftIndex + i_cut * i_radial_cut;
            *i_RecordHighRightIndex = *i_RecordLowRightIndex + i_cut * i_radial_cut;
            *i_moment_index_high = m_moment_index.at(i_Pro).at(i_cut_index).moment_index;
            *i_RecordLowLeftIndex += m_moment_index.at(i_Pro).at(i_cut_index - 1).cut_index * i_radial_cut;
            *i_RecordLowRightIndex += m_moment_index.at(i_Pro).at(i_cut_index - 1).cut_index * i_radial_cut;
            *i_moment_index_low = m_moment_index.at(i_Pro).at(i_cut_index - 1).moment_index;
            return 0;
        }
    }

    return -1;
}

int CAlgoCAPPI::FindGridtoRadarIndex_NEW(double i_GridtoRadarElev, double i_GridtoRadarAz, int i_Pro, int *i_RecordLowLeftIndex, int *i_RecordLowRightIndex, int *i_RecordHighLeftIndex, int *i_RecordHighRightIndex, int *i_moment_index_low, int *i_moment_index_high)
{
    //int i_RadialSum = 0;
    int i_flag = 0;
    int i_radial_cut = m_RadarData_org->radials.size() / m_RadarData_org->commonBlock.cutconfig.size();
    if (i_GridtoRadarElev <= m_RadarData_org->radials[0].radialheader.Elevation) return -1;
    if (i_GridtoRadarElev >= m_RadarData_org->radials.back().radialheader.Elevation) return -1;
    float dAz = m_RadarData_org->radials[1].radialheader.Azimuth - m_RadarData_org->radials[0].radialheader.Azimuth;
    if (i_GridtoRadarAz > dAz && i_GridtoRadarAz < m_RadarData_org->radials[0].radialheader.Azimuth) return -1;
    if (i_GridtoRadarAz < 360-dAz && i_GridtoRadarAz > m_RadarData_org->radials.back().radialheader.Azimuth) return -1;

    for (int i_radial = 0; i_radial < i_radial_cut; i_radial ++)
    {
        if( i_GridtoRadarAz < m_RadarData_org->radials[i_radial].radialheader.Azimuth + dAz \
                && i_GridtoRadarAz >= m_RadarData_org->radials[i_radial].radialheader.Azimuth ) {
            *i_RecordLowLeftIndex = i_radial;
            i_flag++;
        }
        if( i_GridtoRadarAz < dAz && i_GridtoRadarAz >= m_RadarData_org->radials[i_radial].radialheader.Azimuth -360 \
                && i_GridtoRadarAz < m_RadarData_org->radials[i_radial].radialheader.Azimuth -360 + dAz){
            *i_RecordLowLeftIndex = i_radial;
            i_flag++;
        }
        if( i_GridtoRadarAz >= 360-dAz && i_GridtoRadarAz >= m_RadarData_org->radials[i_radial].radialheader.Azimuth +360 -dAz && \
                i_GridtoRadarAz < m_RadarData_org->radials[i_radial].radialheader.Azimuth +360 ) {
            *i_RecordLowRightIndex = i_radial;
            i_flag++;
        }
        if( i_GridtoRadarAz < 360-dAz && i_GridtoRadarAz >= m_RadarData_org->radials[i_radial].radialheader.Azimuth -dAz \
                && i_GridtoRadarAz < m_RadarData_org->radials[i_radial].radialheader.Azimuth ) {
            *i_RecordLowRightIndex = i_radial;
            i_flag++;
        }
        if(i_flag == 2) break;
    }
    if(i_flag <2) return -1;
    int i_cutNum = m_RadarData_org->commonBlock.cutconfig.size();
    if (m_RadarData_org->commonBlock.cutconfig.back().Elevation \
            - m_RadarData_org->commonBlock.cutconfig.at(m_RadarData_org->commonBlock.cutconfig.size()-2).Elevation > 8) {
        i_cutNum --;
    }

    for (int i_cut_index = 1; i_cut_index < m_VarInfo.at(i_Pro).varElCutIndex.size(); i_cut_index++) {
        auto i_cut = m_VarInfo.at(i_Pro).varElCutIndex.at(i_cut_index);
        if (m_RadarData_org->radials[*i_RecordLowLeftIndex+i_cut*i_radial_cut].radialheader.Elevation >= i_GridtoRadarElev) {
            *i_RecordHighLeftIndex = *i_RecordLowLeftIndex + i_cut * i_radial_cut;
            *i_RecordHighRightIndex = *i_RecordLowRightIndex + i_cut * i_radial_cut;
            *i_moment_index_high = m_VarInfo.at(i_Pro).varMomentIndex.at(i_cut_index);
            *i_RecordLowLeftIndex += m_VarInfo.at(i_Pro).varElCutIndex.at(i_cut_index - 1) * i_radial_cut;
            *i_RecordLowRightIndex += m_VarInfo.at(i_Pro).varElCutIndex.at(i_cut_index - 1) * i_radial_cut;
            *i_moment_index_low = m_VarInfo.at(i_Pro).varMomentIndex.at(i_cut_index - 1);
            return 0;
        }
    }

    return -1;
}

void CAlgoCAPPI::Calclonlat(float radar_lon, float radar_lat, int radar_height, float elev, float az, float dst, float &tagLon, float &tagLat)
{
    float arc = R0 * 1000 + radar_height;
    float leo2 = dst * dst + arc * arc + 2 * dst * arc * sin(elev * PI / 180.);
    float q = acos((arc * arc + leo2 - dst * dst) / (2 * arc * sqrt(leo2)));
    az = az * PI / 180.;
    radar_lon = radar_lon * PI / 180.;
    radar_lat = radar_lat * PI / 180.;
    float lat = asin(sin(radar_lat) * cos(q) + cos(radar_lat) * sin(q) * cos(az));
    float lon = radar_lon + atan2(sin(az) * sin(q) * cos(radar_lat), cos(q) - sin(radar_lat) * sin(lat));
    tagLon = lon * 180. / PI;
    tagLat = lat * 180. / PI;
}

int CAlgoCAPPI::FreeBlock()
{
    if (m_RadarProParameters_org)
    {
        //        delete m_RadarProParameters_org;
        m_RadarProParameters_org = NULL;
    }
    if (m_RadarHead_org)
    {
        //        delete m_RadarHead_org;
        m_RadarHead_org = NULL;
    }
    if (m_RadarData_org)
    {
        //        delete m_RadarData_org;
        m_RadarData_org = NULL;
    }

    vector<vector<VarIndex>> ().swap(m_moment_index);

    if (m_GridLat)
    {
        delete[] m_GridLat;
        m_GridLat = NULL;
    }
    if (m_GridLon)
    {
        delete[] m_GridLon;
        m_GridLon = NULL;
    }
    if (m_GridHeight)
    {
        delete[] m_GridHeight;
        m_GridHeight = NULL;
    }
    return 0;
}

void* CAlgoCAPPI::GetProduct()
{
    void* head;
    head = m_RadarPro;
    return head;
}

int CAlgoCAPPI::FreeData()
{
    if (m_RadarPro)
    {
        delete m_RadarPro;
        m_RadarPro = NULL;
    }

    return 0;
}

time_t CAlgoCAPPI::time_convert(int year, int month, int day, int hour,int minute, int second)
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
    TimeStamp = TimeStamp + offset;
    return TimeStamp;

}
