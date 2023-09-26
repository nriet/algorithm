# 此脚本为 返回值以及返回信息的枚举脚本
'''
返回类型：json

cipas业务系统返回格式：
{
    "response_code":"0000",
    "response_msg":"Call succeed.",
    "other_params":...

}

流水线返回格式：
{
    "monitor":{
                "returnCode" :"0",
                "returnMessage" :"Call succeed."
            },
    "otherParams":...
}
'''



# 调用成功
SUCCESS_CODE='0'
CIPAS_SUCCESS_CODE='0000'

SUCCESS_MSG='Call succeed'

# 用户验证失败相关
USER_USER_ID_MISSING_CODE='-1001'
USER_USER_ID_MISSING_MSG='Missing userID'

USER_USER_ID_ERROR_CODE='-1002'
USER_USER_ID_ERROR_MSG='UserID error'

USER_PASSWORD_MISSING_CODE='-1003'
USER_PASSWORD_MISSING_MSG='Missing password'

USER_PASSWORD_ERROR_CODE='-1004'
USER_PASSWORD_ERROR_MSG='Password error'

# 接口与资料不匹配相关
INTERFACE_ID_ERROR_CODE='-2001'
INTERFACE_ID_ERROR_MSG='InterfaceID error'

DATACODE_ERROR_CODE='-2002'
DATACODE_ERROR_MSG='InterfaceID error'

# 参数错误相关
PARAMETER_VALUE_ERROR_CODE='-3001'
PARAMETER_VALUE_ERROR_MSG='Parameter value error'

PARAMETER_VALUE_MISSING_CODE='-3002'
PARAMETER_VALUE_MISSING_MSG='Missing parameter value %s'

PARAMETER_USELESS_CODE='-3003'
PARAMETER_USELESS_MSG='Useless parameter'

INPUT_PAGE_PARAM_FORMAT_ERROR_CODE='-3104'
INPUT_PAGE_PARAM_FORMAT_ERROR_MSG='Input page param format error'

INPUT_PAGE_PARAM_MISSING_CODE='-3105'
INPUT_PAGE_PARAM_MISSING_MSG='Page params error: lack of %s'

JSON_FORMAT_ERROR_CODE='-3106'
JSON_FORMAT_ERROR_MSG='Json File %s format error'

#权限相关
AUTHRORITY_ERROR_CODE='-4001'
AUTHRORITY_ERROR_MSG='No right to access the data'

#数据相关
DATA_OUT_OF_SCALE_CODE='-5001'
DATA_OUT_OF_SCALE_MSG='Time span is out of range'

LACK_OF_DATA_TO_INSERT_CODE='-5002'
LACK_OF_DATA_TO_INSERT_MSG='Lack of data to insert'

DATA_ALL_MISS_CODE='-5003'
DATA_ALL_MISS_MSG='All data are missing'

LATLON_DIFFERENT_ERROR_CODE='-5004'
LATLON_DIFFERENT_ERROR_MSG='The longitude and latitude resolutions of the two groups of data are inconsistent'


#数据库连接相关
DB_CONNECT_ERROR_CODE='-6001'
DB_CONNECT_ERROR_MSG='Fail to connect server'

#数据库操作相关
DB_MANIPULATE_ERROR_CODE='-7001'
DB_MANIPULATE_ERROR_MSG='DB SQL error'

DB_DATA_NOT_FOUND_ERROR_CODE='-7101'
DB_DATA_NOT_FOUND_ERROR_MSG='DB data not found'

DB_CREATE_TEMP_TABLE_ERROR_CODE='-7102'
DB_CREATE_TEMP_TABLE_ERROR_MSG='Create temp table: %s failed'

DB_INSERT_PROP_TABLE_ERROR_CODE='-7103'
DB_INSERT_PROP_TABLE_ERROR_MSG='Insert index product table: %s failed'

DB_INSERT_TEMP_TABLE_ERROR_CODE='-7104'
DB_INSERT_TEMP_TABLE_ERROR_MSG='Insert temp table: %s failed'

#文件错误相关
FILE_NOT_FOUND_ERROR_CODE='-8001'
FILE_NOT_FOUND_ERROR_MSG='File: %s cannot be found'

# 服务端处理异常相关
SERVER_HANDLING_ERROR_CODE='-9001'
SERVER_HANDLING_ERROR_MSG='Server handling exceptions'

WORK_FLOW_ERROR_CODE='-9100'
WORK_FLOW_ERROR_MSG='WorkFlow error occurred'

SUB_WORK_FLOW_ERROR_CODE='-9101'
SUB_WORK_FLOW_ERROR_MSG='SubWorkFlow error occurred'

ALGORITHM_ERROR_CODE="-9102"
ALGORITHM_ERROR_MSG="algorithm error occurred"

DRAW_CONTROLLER_ERROR_CODE='-9150'
DRAW_CONTROLLER_ERROR_MSG='DrawComponent error occurred!'





# 其他类型错误
OTHER_HANDLE_ERROR_CODE='-10'
OTHER_HANDLE_ERROR_MSG='Other error occurred'

# 自定义错误
CUSTOM_ERROR_CODE='-11'
CUSTOM_ERROR_MSG='Custom error occurred'







