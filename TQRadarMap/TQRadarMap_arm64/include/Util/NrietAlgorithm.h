#include <string>
using namespace std;
#ifndef NRIET_ALGORITHM_H
#define NRIET_ALGORITHM_H

class CNrietAlogrithm
{
public:
    virtual ~CNrietAlogrithm() = default;
    virtual int Init(void){return 0;};
    virtual int LoadIni(void*){return 0;}; //INIParser
    virtual int LoadParameters(void*){return 0;};
    virtual int LoadStdCommonBlock(void*){return 0;};
    virtual int LoadStdRadailBlock(void*){return 0;};
    virtual int LoadStdData(void*){return 0;};
    virtual int MakeProduct(void){return 0;};
    virtual int GetFileName(string){return 0;};
    virtual int MakePreQPE(void){return 0;};
    virtual int FreeData(void){return 0;};
    virtual int Uninit(void){return 0;};
    virtual int SetDebugLevel(int){return 0;};

#if defined (ALGORITHM_RECOGNITION_STORM_C) || defined (ALGORITHM_RECOGNITION_MESO_C)
    typedef void(*RecognitionHooker)(void* result, void* arg);
    virtual int LoadCallBack(RecognitionHooker, void*) = 0;
#else
    virtual void* GetProduct(void){return nullptr;};
#endif
};

#endif // NRIET_ALGORITHM_H
