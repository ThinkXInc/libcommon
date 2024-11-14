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

class PartialSuccessFormat(SuccessFormat):
    def __init__(self, message: str, data: Any = None, error_detail: str = None):
        # Add a field for error details if partial success
        partial_success_data = data if data else {}
        if error_detail:
            partial_success_data['error_detail'] = error_detail
        super().__init__(data=partial_success_data, code=SuccessCode.PARTIAL_SUCCESS, message=message)
