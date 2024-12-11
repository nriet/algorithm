﻿/**********************************************************************
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
* File:WRadDataAggregator.h
* Author:Nriet
* time 2023-05-24
*************************************************************************/
#pragma once

#include <Ice/Ice.h>
#include "WRADStdData.h"
#include "struct_WeatherRadar.h"
#include "DataConvertor.h"
#include "NDebug.h"
#include <cmath>

using namespace WRADStdFormat::Data;

class CWRadDataAggregator
{
    using WRadarStdDataPtr = std::shared_ptr<WRADRAWDATA>;
    using WRadarStdDataIcePtr = std::shared_ptr<Version10::RadarRawData>;
public:
    CWRadDataAggregator(Ice::CommunicatorPtr&);
    CWRadDataAggregator(std::string&, Ice::CommunicatorPtr&);

    bool onReceiveCutData(Version10::RadarRawData&);
    bool onReceiveVTBData(WRADRAWDATA &,Version10::RadarRawData &);
    WRadarStdDataPtr & getDataBySiteCode(std::string&);
    bool getCopyAndFlushBySiteCode(WRADRAWDATA &,std::string&);
    bool copy(WRADRAWDATA &,std::string&, int __n, int __pos);
    bool checkVTBCompleteness(std::string&, int eleNum);
    int size(std::string&);

    bool flushDataBySiteCode(std::string&);

    void setDebugLevel(int);
private:
    Ice::CommunicatorPtr m_pCommunicator;
    Ice::LoggerPtr m_pLogger;
    std::string m_strName;
    int m_nDebugLevel = 0;

    WRadarStdDataPtr & retrieveAndCreateDataBySiteCode(std::string&);

    DataConvertor m_Converter;
    // radar data cache for multi radar
    std::vector<WRadarStdDataPtr> m_vRadarStdVtb;

    static bool sortStdCut(CUTCONFIG, CUTCONFIG);
    static bool sortStdVTB(WRadarStdDataIcePtr, WRadarStdDataIcePtr);
    bool stdDataCachePush(WRadarStdDataIcePtr&);
    WRadarStdDataIcePtr stdDataCacheBack(string);
    bool stdDataCachePopBack(string);
    int stdDataCacheSize(string);
    bool stdDataCacheCheckAndFlush(string);
    std::vector<WRadarStdDataIcePtr> getStdDataCache(string);
    std::map<string, std::vector<WRadarStdDataIcePtr>>m_mStdVtbCache;
};

using CWRadDataAggregatorPtr = std::shared_ptr<CWRadDataAggregator>;
