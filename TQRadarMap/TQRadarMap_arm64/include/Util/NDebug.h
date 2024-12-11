#ifndef NDEBUG_H
#define NDEBUG_H

#include "ProductFactory.h"
#include "CIceUtil.h"
#include "Topics.h"

// Debug level
typedef enum debug_level
{
    DBG_DEBUG = 0,
    DBG_INFO = 1,
    DBG_WARN = 2,
    DBG_ERROR = 3,
}DEBUG_LEVEL_T;

#define LOG_RECORD(type, level, log, domain)    do \
            {   \
                string topic = Topics::Tpc_SVR_PF_SysLog_Collect;\
                auto proxy = CIceUtilSton.getTopicPrx(topic);   \
                auto publisher = proxy->getPublisher()->ice_oneway();   \
                auto _logMgr = Ice::uncheckedCast<ProductFactory::MQ_LogMgrPrx>(publisher);    \
                if (_logMgr)   \
                {   \
                    _logMgr->SystemLogAsync(type, level, log, domain, nullptr,    \
                                                       [this](exception_ptr e){ \
                                                            try {   \
                                                                rethrow_exception(e);   \
                                                            }   \
                                                            catch (...) {}\
                                                        }   \
                                                       );   \
                }   \
            } while(0)

#define NRIET_DEBUG_ERROR(level, logger, msg)   do \
                        {   \
                            if(logger && (DBG_ERROR >= level)){  \
                                logger->error(string(__FUNCTION__) +"-"+ to_string(__LINE__) + ":" + msg);   \
                                LOG_RECORD(1, DBG_ERROR, msg, string(__FILE__) + ":" + string(__FUNCTION__));\
                            } \
                        }while(0)

#define NRIET_DEBUG_INFO(level, logger, tag, msg)   do \
                        {   \
                            if(logger && (DBG_INFO >= level)){  \
                                logger->trace(tag, string(__FUNCTION__) + ":" + msg);   \
                            }\
                        }while(0)

#define NRIET_DEBUG_WARN(level, logger, msg)   do \
                        {   \
                            if(logger && (DBG_WARN >= level)){  \
                                logger->warning(string(__FUNCTION__) +"-"+ to_string(__LINE__) + ":" + msg);   \
                                LOG_RECORD(1, DBG_WARN, msg,  string(__FILE__) + ":" + string(__FUNCTION__));\
                            }   \
                        }while(0)

#define NRIET_DEBUG_DEBUG(level, logger, tag, msg)   do \
                        {   \
                            if(logger && (DBG_DEBUG >= level)){  \
                                logger->trace(tag, string(__FUNCTION__) + ":" + msg);   \
                                }   \
                        }while(0)

#define NRIET_DEBUG_TRACE NRIET_DEBUG_DEBUG

#endif // NDEBUG_H
