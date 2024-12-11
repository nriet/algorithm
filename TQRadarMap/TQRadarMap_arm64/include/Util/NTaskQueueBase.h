#pragma once

#include <Ice/Ice.h>
#include <IceStorm/IceStorm.h>
#include <Topics.h>

class CTaskQueueBase : public IceUtil::Thread
{
public:
    IceStorm::TopicManagerPrxPtr m_pTopicMgr;
    Ice::CommunicatorPtr m_pCommunicator;
    Ice::LoggerPtr m_pLogger;
};
