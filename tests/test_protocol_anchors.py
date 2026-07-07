# tests/test_protocol_anchors.py
#
# L-2: PROTOCOL.md v1 契約錨テスト([凍結])。
#
# ★ このテストが落ちる変更は PROTOCOL.md §6(互換性ルール)違反である。★
#   PROTOCOL.md v1 は上位契約であり、APIErrorFormat の出力外形 {field_name, code, message, reason}
#   と成功系の外形 {code, message} は auth プロトコル §5/§3 の土台。変更は「追加のみ」許される
#   (既存キーの削除・改名・型変更は禁止。大原則6)。
#
# T-L1(特性ゴールデン)とは独立に、仕様そのものを明示参照するアンカーとしてここに置く。

from golden_utils import make_app

from libcommon.web.http_response_formatter import (
    SuccessFormat, SuccessCode, APIErrorFormat, ErrorCode,
)

app = make_app()

# PROTOCOL.md §5: エラー応答の錨キー集合
ERROR_ANCHOR_KEYS = {'field_name', 'code', 'message', 'reason'}
# PROTOCOL.md §3: 成功応答の外形
SUCCESS_ANCHOR_KEYS = {'code', 'message'}


def _body(fmt):
    with app.test_request_context():
        return fmt.response_json().get_json()


def test_api_error_format_contains_four_anchor_keys():
    # (a) APIErrorFormat().response_json() のキー集合が {field_name, code, message, reason} を含む
    body = _body(APIErrorFormat(field_name='user_id', code=ErrorCode.BAD_REQUEST, message='bad'))
    assert ERROR_ANCHOR_KEYS.issubset(body.keys()), body


def test_success_format_contains_code_and_message():
    # (b) 成功系の外形に code/message が必ず含まれる
    body = _body(SuccessFormat(data={}, code=SuccessCode.OK, message='ok'))
    assert SUCCESS_ANCHOR_KEYS.issubset(body.keys()), body


def test_success_format_with_data_keeps_code_and_message():
    # 成功系は data を top-level 展開するが code/message は保たれる
    body = _body(SuccessFormat(data={'id': 1, 'name': 'x'}, code=SuccessCode.CREATED, message='created'))
    assert SUCCESS_ANCHOR_KEYS.issubset(body.keys()), body


def test_adding_protocol_version_does_not_break_error_anchor_keys():
    # (c) protocol_version を「追加」しても既存キーは壊れない(extra_data 経由の追加合成)
    body = _body(APIErrorFormat(
        field_name='user_id', code=ErrorCode.BAD_REQUEST, message='bad',
        extra_data={'protocol_version': 'v1'},
    ))
    assert ERROR_ANCHOR_KEYS.issubset(body.keys()), body
    assert body['protocol_version'] == 'v1'


def test_dict_composition_addition_preserves_base_keys():
    # (c) dict 合成として: 追加キーは既存キーを落とさない(§6 の「追加のみ」規則の骨格)
    base = {'field_name': '', 'code': 400, 'message': 'm', 'reason': 'BAD_REQUEST'}
    extended = {**base, 'protocol_version': 'v1'}
    assert ERROR_ANCHOR_KEYS.issubset(extended.keys())
    for k, v in base.items():
        assert extended[k] == v  # 既存キーの値は不変
