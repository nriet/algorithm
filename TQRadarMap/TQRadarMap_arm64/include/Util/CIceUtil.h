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
* File:CIceUtil.h
* Author:Nriet
* time 2023-05-24
*************************************************************************/
#pragma once

#include <Ice/Ice.h>
#include <IceStorm/IceStorm.h>
#include "Singleton.h"

class CIceUtil : public Singleton<CIceUtil>
{
public:
    CIceUtil(Ice::CommunicatorPtr&);

    IceStorm::TopicPrxPtr getTopicPrx(std::string& topic);
    IceStorm::TopicManagerPrxPtr getTopicManager();
    IceStorm::TopicManagerPrxPtr getTopicManagerByString(std::string& identity);
    std::vector<Ice::ObjectPrxPtr> subscribeWithUUID(std::string& topic, const ::std::shared_ptr<Ice::Object>& servant, bool order = false);
    std::vector<Ice::ObjectPrxPtr> subscribe(std::string& topic, const ::std::shared_ptr<Ice::Object>& servant, Ice::Identity&id, bool order = false);
    std::vector<Ice::ObjectPrxPtr> subscribeWithUUID(Ice::ObjectAdapterPtr& adapter,std::string& topic, const ::std::shared_ptr<Ice::Object>& servant, bool order = false);
    std::vector<Ice::ObjectPrxPtr> subscribe(Ice::ObjectAdapterPtr& adapter,std::string& topic, const ::std::shared_ptr<Ice::Object>& servant, Ice::Identity&id, bool order = false);
    std::vector<Ice::ObjectPrxPtr> subscribe(Ice::ObjectPrxPtr& subscriber,std::string& topic, bool order = false);

    void unSubscribe(std::string&topic, Ice::ObjectPrxPtr& subscriber);

    std::vector<std::string>stringSplit(const std::string& str, const char delim);
    std::string getRemoteIp(const Ice::Current & current);
    std::string generateUUIDWithoutDash();
private:
    bool isValidIP(const std::string &ip);
    Ice::LoggerPtr m_pLogger;
    Ice::CommunicatorPtr m_pCommunicator;
    IceStorm::TopicManagerPrxPtr m_pTopicMgr;
};

#define CIceUtilSton CIceUtil::getSingleton()

