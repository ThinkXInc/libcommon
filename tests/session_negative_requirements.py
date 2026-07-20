# tests/session_negative_requirements.py
#
# Machine-readable traceability from auth-spec 05 Session requirements to pytest tests.

SESSION_NEGATIVE_REQUIREMENTS = {
    'SESSION-NEG-01': {
        'specification': '同一ブラウザで 2 つの認証を並行開始できる。',
        'test': 'test_negative_session_same_browser_starts_two_parallel_authentications',
        'session_apis': {'browser_context_id'},
    },
    'SESSION-NEG-02': {
        'specification': (
            '1 つ目の Session ローテーション後も 2 つ目が成功する'
            '（browser_context_id 引き継ぎ）。'
        ),
        'test': 'test_negative_session_rotation_preserves_browser_context_id',
        'session_apis': {'browser_context_id', 'id', 'start'},
    },
    'SESSION-NEG-03': {
        'specification': 'clear_current で当該 Session だけが失効する。',
        'test': 'test_negative_session_clear_current_revokes_only_current_browser',
        'session_apis': {'clear_current'},
    },
    'SESSION-NEG-04': {
        'specification': 'revoke_all でユーザーの全端末 Session が失効する。',
        'test': 'test_negative_session_revoke_all_revokes_every_browser',
        'session_apis': {'revoke_all'},
    },
}
