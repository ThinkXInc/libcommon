# tests/test_char_formats.py
#
# T-L1: フォーマット族の契約形状(原則6 / PROTOCOL.md §5 の錨)。
# SuccessFormat / APIErrorFormat / ValidationErrorsFormat と、http_errors / http_successes /
# validation_errors の全具象クラスについて、(JSON本文, HTTPステータス) を凍結。
# APIErrorFormat 系は {field_name, code, message, reason} の4キーが出ることを明示アサート。

import pytest

from golden_utils import assert_golden, make_app

from libcommon.web.http_response_formatter import (
    SuccessFormat, SuccessCode, APIErrorFormat, ErrorCode,
    ValidationErrorFormat, ValidationErrorsFormat,
)
from libcommon.web import http_errors as E
from libcommon.web import http_successes as S
from libcommon.web import validation_errors as V

app = make_app()


def _http_response_golden(name, obj, anchor_4keys=False):
    """http_response() を app 文脈で呼び (body, status) を凍結。"""
    with app.test_request_context():
        resp, status = obj.http_response()
        body = resp.get_json()
    if anchor_4keys:
        # PROTOCOL.md §5 の錨: この4キーが必ず出ること
        for k in ('field_name', 'code', 'message', 'reason'):
            assert k in body, f"missing anchor key {k} in {name}: {body}"
    assert_golden(name, {'body': body, 'status': status})


# ---- 基底クラス(原則6 の錨) ----

def test_base_success_format():
    obj = SuccessFormat(data={'x': 1}, code=SuccessCode.OK, message='ok')
    _http_response_golden('formats/base_success_format', obj)


def test_base_api_error_format():
    obj = APIErrorFormat(field_name='user_id', code=ErrorCode.BAD_REQUEST, message='bad')
    _http_response_golden('formats/base_api_error_format', obj, anchor_4keys=True)


def test_base_validation_errors_format():
    errs = [
        ValidationErrorFormat(field_name='email', value='x', message='required'),
        ValidationErrorFormat(field_name='pw', value=None, message='too short'),
    ]
    obj = ValidationErrorsFormat(errors=errs, code=ErrorCode.BAD_REQUEST, message='validation')
    _http_response_golden('formats/base_validation_errors_format', obj)


def test_validation_error_format_dict_shape():
    obj = ValidationErrorFormat(field_name='email', value='v', message='m')
    assert_golden('formats/validation_error_format_dict', obj.dict())


# ---- http_errors.py の全具象クラス(APIErrorFormat 派生) ----

ERROR_CLASSES_LANG = [
    ('unexpected', E.UnexpectedAPIErrorFormat),
    ('invalid_content_type', E.InvalidContentTypeAPIErrorFormat),
    ('forbidden', E.ForbiddenAPIErrorFormat),
    ('resource_not_found', E.ResourceNotFoundAPIErrorFormat),
    ('bad_request', E.BadRequestAPIErrorFormat),
    ('unauthorized', E.UnauthorizedAPIErrorFormat),
    ('rate_limit_exceeded', E.RateLimitExceededAPIErrorFormat),
    ('incorrect_password', E.IncorrectPasswordAPIErrorFormat),
    ('user_already_exists', E.UserAlreadyExistsErrorFormat),
    ('invalid_password_format', E.InvalidPasswordFormatErrorFormat),
]


@pytest.mark.parametrize('key,cls', ERROR_CLASSES_LANG)
def test_http_error_classes_en(key, cls):
    obj = cls(lang='en')
    _http_response_golden(f'formats/error_{key}_en', obj, anchor_4keys=True)


def test_http_error_unauthorized_ja():
    # 多言語の実挙動も1件凍結(localize が効いていること)
    obj = E.UnauthorizedAPIErrorFormat(lang='ja')
    _http_response_golden('formats/error_unauthorized_ja', obj, anchor_4keys=True)


def test_http_error_google_oauth_token():
    obj = E.GoogleOauthTokenErrorFormat(error_message='Missing token', code=ErrorCode.UNAUTHORIZED)
    _http_response_golden('formats/error_google_oauth_token', obj, anchor_4keys=True)


# ---- http_successes.py の全具象クラス(SuccessFormat 派生) ----

def test_success_ok():
    _http_response_golden('formats/success_ok', S.OKAPISuccessFormat(message='done', data={'id': 1}))


def test_success_created():
    _http_response_golden('formats/success_created', S.CreatedAPISuccessFormat(message='created', data={'id': 2}))


def test_success_accepted():
    _http_response_golden('formats/success_accepted', S.AcceptedAPISuccessFormat(message='accepted', data=None))


def test_success_partial():
    obj = S.PartialSuccessFormat(message='partial', data={'id': 3}, error_detail='some failed')
    _http_response_golden('formats/success_partial', obj)


# ---- validation_errors.py の全具象クラス(ValidationErrorFormat 派生 / .dict() 形状) ----

def test_validation_required():
    obj = V.RequiredFieldsNotSatisfiedFormat(field_name='email', value=None, lang='en')
    assert_golden('formats/verr_required_en', obj.dict())


def test_validation_email_format():
    obj = V.InvalidEmailFormatErrorFormat(field_name='email', value='x', lang='en')
    assert_golden('formats/verr_email_format_en', obj.dict())


def test_validation_max_length():
    obj = V.MaxLengthExceededErrorFormat(field_name='name', value='toolong', lang='en')
    assert_golden('formats/verr_max_length_en', obj.dict())


def test_validation_invalid_format():
    obj = V.InvalidFormatErrorFormat(field_name='age', value='x', lang='en')
    assert_golden('formats/verr_invalid_format_en', obj.dict())


def test_validation_regex_match_failed():
    obj = V.RegexMatchFailedErrorFormat(field_name='email', value='x', lang='en', locale_key='email_format')
    assert_golden('formats/verr_regex_match_failed_en', obj.dict())


def test_validation_min_length_missing_key_raises():
    # 'min_length' はロケールに存在しない → Locale.get が KeyError(既知の欠落。findings 参照)。
    # 例外型のみ凍結する(メッセージには絶対パスが含まれ非可搬なため body には残さない)。
    with pytest.raises(KeyError):
        V.MinLengthNotReachedErrorFormat(field_name='pw', value='x', lang='en')
    assert_golden('formats/verr_min_length_missing_key', {'raises': 'KeyError'})
