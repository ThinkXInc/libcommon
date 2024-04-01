from typing import Any
from libcommon.web.http_response_formatter import SuccessFormat, SuccessCode

class OKAPISuccessFormat(SuccessFormat):
    def __init__(self, message: str, saved_data: Any = None):
        super().__init__(saved_data=saved_data, code=SuccessCode.OK.value, message=message)

    def http_response(self) -> tuple:
        return self.response_json(), self.code

class CreatedAPISuccessFormat(SuccessFormat):
    def __init__(self, message: str, saved_data: Any = None):
        super().__init__(saved_data=saved_data, code=SuccessCode.CREATED.value, message=message)

    def http_response(self) -> tuple:
        return self.response_json(), self.code

class AcceptedAPISuccessFormat(SuccessFormat):
    def __init__(self, message: str, saved_data: Any = None):
        super
