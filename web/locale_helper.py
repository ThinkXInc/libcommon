from pathlib import Path
from config import Config, check_config
from libcommon.locale import Locale

# Check if all keys and values are satisfied
REQUIRED_KEYS = [
    'DEFAULT_LANG',
]
check_config(Config, REQUIRED_KEYS)

DEFAULT_LOCALE_FILE_PATHS = [
    (Path(__file__).parent.parent / 'locales' / 'errors.json').absolute(),
    (Path(__file__).parent.parent / 'locales' / 'validation_errors.json').absolute(),
    (Path(__file__).parent.parent / 'locales' / 'api_response.json').absolute(),
]

def get_locale_text(locale_file_path, key, lang = Config.DEFAULT_LANG):
    for locale_file_path in DEFAULT_LOCALE_FILE_PATHS:
        if not locale_file_path.exists():
            raise FileNotFoundError(f"Locale file not found at {locale_file_path}")
    locale = Locale(DEFAULT_LOCALE_FILE_PATHS)
    return locale.get(key, lang)