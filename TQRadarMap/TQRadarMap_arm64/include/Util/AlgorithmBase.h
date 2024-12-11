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
* File:AlgorithmBase.h
* Author:Nriet
* time 2023-05-24
*************************************************************************/
#pragma once
#include "FileUtil.h"
#include "WRADStdProduct.h"
#include "Grid.h"

typedef int (*pAlgo_Init)();
typedef int (*pAlgo_LoadParams)(void*);
typedef int (*pAlgo_LoadData)(void*);
typedef int (*pAlgo_MakeProduct)();
typedef void* (*pAlgo_GetProduct)();
typedef int (*pAlgo_FreeData)();
typedef int (*pAlgo_Uninit)();
typedef void (*pAlgo_SetDebugLevel)(int);

typedef int (*pIO_Init)();
typedef int (*pIO_Uninit)();
typedef int (*pIO_LoadDataFromFile)(void*);
typedef void* (*pIO_GetRadarHead)();
typedef void* (*pIO_GetRadarData)();
typedef void* (*pIO_GetRadarRawData)();
typedef int (*pIO_LoadDataandSaveFile)(void*, void*);
typedef void* (*pIO_GetFileName)(void*);
typedef int (*pIO_FreeData)();

// Note: define of ALGORITHM_RECOGNITION_STORM_C
//       should before including "NrietAlgorithm.h"
#ifdef CONFIG_SERVICE_ALGO_RECOGNITION
#define ALGORITHM_RECOGNITION_STORM_C
#define ALGORITHM_RECOGNITION_MESO_C
#endif
#include "NrietAlgorithm.h"

class AlgorithmBase : public CFileUtil
{
public:
    virtual ~AlgorithmBase() = default;

    virtual int doForwardProductEvent(int type, ::std::string name, int time, ::std::string path, ::std::string producer);
    virtual int doForwardProduct(std::string&, WRADStdFormat::Product::Standard &);
    virtual int doForwardProduct(std::string&, Product::Grid::GridProductPtr &);

    // algorithm API
    virtual int algoInit(void){return 0;};
    virtual int algoLoadIni(void*){return 0;};
    virtual int algoLoadParams(void*){return 0;};
    virtual int algoLoadData(void*){return 0;};
    virtual int algoMakeProduct(){return 0;};
    virtual void* algoGetProduct(){return nullptr;};
    virtual int algoFreeData(){return 0;};
    virtual int algoUninit(){return 0;};
    virtual void algoSetDebugLevel(int){return;};
};

class FileIOBase
{
public:
    virtual ~FileIOBase() = default;

//    void * pIoHandle;   // Io lib handle
    // algorithm API
    virtual int ioInit(void) = 0;
    virtual int ioLoadDataFromFile(void*) = 0;
    virtual int ioLoadDataandSaveFile(void*,void*) = 0;
    virtual void* ioGetFilename(void*) = 0;
    virtual int ioFreeData() = 0;
    virtual int ioUninit() = 0;
};
