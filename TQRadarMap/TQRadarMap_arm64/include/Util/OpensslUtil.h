#pragma once

#include <iostream>
#include "openssl/aes.h"

class OpensslUtil
{
public:
    OpensslUtil();

    bool AesEncrypt(const std::string &plain, std::string &cipher, const std::string &key);
    bool AesDecrypt(const std::string &cipher, std::string &plain, const std::string &key);

    int AesEncrypt_v1(const std::string &plain, char* cipher, const std::string &key);
    int AesDecrypt_v1(char* const cipher, int length, char* plain, const std::string &key);
};
