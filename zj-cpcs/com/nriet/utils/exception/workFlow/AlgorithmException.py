from com.nriet.utils.exception.SysException import SysException
from com.nriet.config.ResponseCodeAndMsgEum import ALGORITHM_ERROR_CODE,ALGORITHM_ERROR_MSG

class AlgorithmException(SysException):
    def __init__(self,response_msg=ALGORITHM_ERROR_MSG,response_code=ALGORITHM_ERROR_CODE):
        super().__init__(response_msg,response_code)