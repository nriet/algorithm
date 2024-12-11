#ifndef STRUCT_PRODUCTPARAMDEF_H
#define STRUCT_PRODUCTPARAMDEF_H

#include <string>
#include <vector>
using namespace  std;



typedef struct
{
    char time[500];
    int hail_id;  //
    int sort;
    float lon;
    float lat;
    float azimuth;
    int hail_range;
    int possibility_of_hail;
    int possibility_of_severe_hail;
    float size_of_hail;
}HiParam;


typedef struct
{
    char time[500];
    int storm_id;  //
    int sort;
    float lon;
    float lat;
    float azimuth;
    float lon_forecast_one;
    float lat_forecast_one;
    float lon_forecast_two;
    float lat_forecast_two;
    float lon_forecast_three;
    float lat_forecast_three;
    float lon_forecast_n;
    float lat_forecast_n;
    int storm_range;
    float speed;
    float direction;
    int top_height;
    int bottom_height;
    int height_of_maximum_reflectivity;
    int height;
    int vil;
    int maximum_reflectivity;
}StiParam;

typedef struct
{
    char time[500];
    int feature_id;  //
    int feature_type;
    int storm_id;
    int sort;
    float lon;
    float lat;
    float azimuth;
    float elevation;
    int m_range;
    int height;
}MParam;

typedef struct
{
    char time[500];
    int storm_id;
    int type;
    int sort;
    float lon;
    float lat;
    float azimuth;
    float elevation;
    int tvs_range;
}TvsParam;

typedef struct
{
    string stationId;
    int dateStr;
    string productCode;
    string datetimeStr;
    long long milliSecond;
    double des;
}ProdLatlon;


typedef struct
{
    int type;
    char name[256];  //
    char producer[256];
    char desc[500];
    int time;
}ProductInfo;

typedef struct
{
    char name[256];  //
    int type;
    int level;
    char log[500];
}LogInfo;

typedef struct
{
    char datafilename[255];  //
    char firstscantime[255];
    char savetime[255];  //

}DSLogInfo;


typedef struct
{
    string code;
    string stationId;
    string productCode;
    //string datetimeStr;
    char datetime[255];
    long long milliSecond;
    string elevIndex;
    string pathStr;
    int productType;
    int fileSize;
}ProdPathInfo;

typedef struct
{
    string stationId;
    char starttime[255];
    char endtime[255];
    string Scantype;
}ProdTimeInfo;


#endif // STRUCT_PRODUCTPARAMDEF_H
