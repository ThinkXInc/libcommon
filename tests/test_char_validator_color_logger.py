# tests/test_char_validator_color_logger.py
#
# T-L6: validator / color / logger。
# Validator 全 ValidationType の判定表、color 各関数が ANSI コードを含む文字列を返すこと、
# Logger が例外なく初期化できること。

from golden_utils import assert_golden

from libcommon.validator import Validator, ValidationType
from libcommon import color as C
from libcommon.logger import Logger


VALIDATOR_CASES = [
    ('required_empty', '', ValidationType.required),
    ('required_none', None, ValidationType.required),
    ('required_value', 'x', ValidationType.required),
    ('email_valid', 'test@example.com', ValidationType.email),
    ('email_invalid', 'notanemail', ValidationType.email),
    ('password_valid', 'Abcdef12', ValidationType.password),
    ('password_too_short', 'Abc1', ValidationType.password),
    ('password_no_upper', 'abcdef12', ValidationType.password),
    ('tel_valid', '090-1234-5678', ValidationType.tel),
    ('tel_invalid', 'abc', ValidationType.tel),
    ('postal_valid', '1234567', ValidationType.postal_code),
    ('postal_invalid', '!!!', ValidationType.postal_code),
    ('max_length_ok', 'short', ValidationType.max_length),
    ('unknown_type', 'x', 'no_such_type'),
]


def test_validator_decision_table():
    table = {}
    for label, value, vtype in VALIDATOR_CASES:
        try:
            table[label] = Validator.check(value, vtype)
        except Exception as e:
            table[label] = f'RAISES:{type(e).__name__}'
    assert_golden('validator/decision_table', table)


def test_validator_required_type_mismatch():
    # required_type を指定し型不一致なら False
    assert_golden('validator/required_type_mismatch', {
        'int_as_str': Validator.check(123, ValidationType.required, str),
        'str_as_str': Validator.check('123', ValidationType.required, str),
    })


COLOR_FUNCS = [
    'black', 'red', 'green', 'yellow', 'orange', 'blue', 'purple', 'magenta',
    'cyan', 'white', 'grey', 'light_red', 'light_green', 'light_yellow',
    'light_blue', 'light_magenta', 'light_cyan', 'light_white', 'bold', 'underline',
]


def test_color_functions_wrap_ansi():
    out = {}
    for name in COLOR_FUNCS:
        s = getattr(C, name)('X')
        # ANSI エスケープを含み、リセットで終わること
        assert '\033[' in s and s.endswith('\033[0m'), f'{name}: {s!r}'
        out[name] = s
    assert_golden('color/functions', out)


def test_logger_initializes_without_error():
    lg = Logger()
    lg.setLevel(lg.DEBUG)
    lg2 = Logger('named-logger')
    lg2.setLevel(lg2.INFO)
    assert lg is not None and lg2 is not None
