from pathlib import Path
from libcommon.locale import Locale

# L-1: config 依存を除去。DEFAULT_LANG は既定 'en'(呼び出し側は常に lang を明示するため
# この既定値は挙動に影響しない)。check_config はアプリ側の責務に移譲。
DEFAULT_LANG = 'en'

DEFAULT_LOCALE_FILE_PATHS = [
    (Path(__file__).parent.parent / 'locales' / 'errors.json').absolute(),
    (Path(__file__).parent.parent / 'locales' / 'validation_errors.json').absolute(),
    (Path(__file__).parent.parent / 'locales' / 'api_response.json').absolute(),
]

def get_locale_text(locale_file_path, key, lang = DEFAULT_LANG, locale_args: list = None):
    for locale_file_path in DEFAULT_LOCALE_FILE_PATHS:
        if not locale_file_path.exists():
            raise FileNotFoundError(f"Locale file not found at {locale_file_path}")
    locale = Locale(DEFAULT_LOCALE_FILE_PATHS)
    return locale.get(key, lang, locale_args = None)