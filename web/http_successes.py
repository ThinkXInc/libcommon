from typing import Any
from libcommon.web.http_response_formatter import SuccessFormat, SuccessCode

class OKAPISuccessFormat(SuccessFormat):
    def __init__(self, message: str, data: Any = None):
        super().__init__(data=data, code=SuccessCode.OK, message=message)

class CreatedAPISuccessFormat(SuccessFormat):
    def __init__(self, message: str, data: Any = None):
        super().__init__(data=data, code=SuccessCode.CREATED, message=message)

class AcceptedAPISuccessFormat(SuccessFormat):
    def __init__(self, message: str, data: Any = None):
        super().__init__(data=data, code=SuccessCode.ACCEPTED, message=message)