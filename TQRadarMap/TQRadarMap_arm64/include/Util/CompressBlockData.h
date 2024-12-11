#ifndef COMPRESSBLOCKDATA_H
#define COMPRESSBLOCKDATA_H

#include <vector>
#include <iostream>
#include <zlib.h>
using namespace std;

namespace BlockDataCompress {

    vector<uint8_t> zlib_mem_compress(const void *source , size_t sourceLen)
    {
        vector<uint8_t> buffer(compressBound(sourceLen));
        uLong desLen = buffer.size();
        auto err = compress(buffer.data(),&desLen,reinterpret_cast<const Bytef*>(source),ulong(sourceLen));
        if(err == Z_OK){
            cout<<"zlib compress successful"<<endl;
        }else{
            cout<<"zlib compress error:" <<err<<endl;
        }
        return vector<uint8_t>(buffer.data(),buffer.data() + desLen);
    }

    vector<uint8_t> zlib_mem_uncompress(const void *src,size_t srcSize,size_t desSize)
    {
        for(;;){
            vector<uint8_t> cappidata(desSize);
            uLong desLen = cappidata.size();
            auto err = uncompress(cappidata.data(),&desLen,reinterpret_cast<const Bytef*>(src),uLong(srcSize));
            if(err == Z_OK){
                cout<<"cappi uncompress successful"<<endl;
                return  vector<uint8_t>(cappidata.data(),cappidata.data()+desLen);
            }else if(err == Z_BUF_ERROR){
                desSize<<=2;
                cout<<"cappi uncompress Z_BUF_ERROR:"<<err<<endl;
            }else{
                break;
            }
        }
    }
}

#endif // COMPRESSBLOCKDATA_H
