from pathlib import Path
from config import Config, check_config
from libcommon.locale import Locale

# Check if all keys and values are satisfied
REQUIRED_KEYS = [
    'DEFAULT_LANG',
]
check_config(Config, REQUIRED_KEYS)

def get_locale_text(locale_file_path, key, lang = Config.DEFAULT_LANG):
    locale_file_path = (Path(__file__).parent.parent / 'locales' / 'errors.json').absolute()
    if not locale_file_path.exists():
        raise FileNotFoundError(f"Locale file not found at {locale_file_path}")

    locale = Locale(locale_file_path)
    return locale.get(key, lang)