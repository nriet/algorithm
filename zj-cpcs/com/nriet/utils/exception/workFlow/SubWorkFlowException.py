from com.nriet.utils.exception.SysException import SysException
from com.nriet.config.ResponseCodeAndMsgEum import SUB_WORK_FLOW_ERROR_CODE,SUB_WORK_FLOW_ERROR_MSG


class SubWorkFlowException(SysException):
    def __init__(self,response_msg=SUB_WORK_FLOW_ERROR_MSG,response_code=SUB_WORK_FLOW_ERROR_CODE):
        super().__init__(response_msg,response_code)