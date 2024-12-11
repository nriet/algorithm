#ifndef STRUCT_CALIBRATE_RESULT_H
#define STRUCT_CALIBRATE_RESULT_H
#include <string>
#include <vector>
using namespace std;

enum CalibrateType{
    Calibrate_Az,
    Calibrate_Elev,
    Calibrate_Dynamic,
    Calibrate_Conf_Hori,
    Calibrate_Conf_Vertical,
    Calibrate_Z,
    Calibrate_V,
    Calibrate_N_V,
    Calibrate_N_H,
};

namespace RadarCalibrate {
    typedef enum
    {
        REQUEST_CR_UPDATE,
        REQUEST_CR_ADD,
        REQUEST_CR_DELETE,
    }CALIBRATE_REQUEST_T;

    typedef  struct{
        int id;
        string code;
        string token;
        int stationId;
        int valueType;
        float value;
        int calibrateType;
        int calibrateResult;
        int calibrateTime;

    } calibrate_result;

using calibrateResultSeq = vector<calibrate_result>;
}

#endif // STRUCT_CALIBRATE_RESULT_H
