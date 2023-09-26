from com.nriet.utils.exception.SysException import SysException
from com.nriet.config.ResponseCodeAndMsgEum import WORK_FLOW_ERROR_CODE,WORK_FLOW_ERROR_MSG


class WorkFlowException(SysException):
    def __init__(self,response_msg=WORK_FLOW_ERROR_MSG,response_code=WORK_FLOW_ERROR_CODE):
        super().__init__(response_msg,response_code)
