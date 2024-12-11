#pragma once
#include "vector"

typedef struct
{
    char code[50];  //
    char name[50];
    float longtitude;
    float latitude;
    float height;
    int type;
    char mark[50];
    char id[50];  //36 byte
    char secret[50];
    char status;
}Equipment;

typedef std::vector<Equipment> EquipmentSeq;

typedef struct
{
    char siteCode[50];
    char siteName[50];
    float longtitude;
    float latitude;
    float height;
    char id[50];  //36 byte
    char token[50];
    char status;    // online status
    char active;    // active status
    char ip[50];
}WeatherRadar;

typedef std::vector<WeatherRadar> WeatherRadarSeq;
