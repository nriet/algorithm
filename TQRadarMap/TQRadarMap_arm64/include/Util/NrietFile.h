#ifndef NRIET_FILE_H
#define NRIET_FILE_H
#include <string>
using namespace std;

class CNrietFile
{
public:
    virtual ~CNrietFile() = default;

    virtual int LoadDataFromFile(void*, int = 0) = 0;
    virtual void* PutHeadPoint(void) = 0;
    virtual void* PutDataPoint(void) = 0;
    virtual void* PutRadarRawData(void) = 0;
    virtual void* GetFileName(void* , int = 0) = 0;
    virtual int GetDrawData(void*, void*, void*, void*, void*) = 0;
    virtual int LoadDataAndSaveFile(void*, void*, int = 0) = 0;
    virtual int FreeData(void) = 0;
    virtual int SetDebugLevel(int) = 0;
    virtual int LoadCSA(void*,void*)=0;
    virtual void getSITECODE(string)=0;
    virtual void gettime_opticalFlow(string)=0;
};

#endif // NRIET_ALGORITHM_H
