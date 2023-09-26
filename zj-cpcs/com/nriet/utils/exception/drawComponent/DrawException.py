from com.nriet.utils.exception.SysException import SysException
from com.nriet.config.ResponseCodeAndMsgEum import DRAW_CONTROLLER_ERROR_CODE


class DrawException(SysException):
    def __init__(self,response_msg='DrawComponent error occurred!',response_code=DRAW_CONTROLLER_ERROR_CODE):
        super().__init__(response_msg,response_code)




