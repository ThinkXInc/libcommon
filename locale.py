# api/helpers/locale.py

# Locale class loads and manages locale-specific data from JSON files.
# It supports loading from a specified path or the default 'libcommon/locales' directory.
# Multiple files can be loaded by passing a list of file paths.

# Usage:
# - Single file from a custom path: 
#       Locale('application/locales/errors.json')

# - Single file from default directory: 
#       Locale('top_view.json')

# - Multiple files: 
#       Locale(['application/locales/errors.json', 'top_view.json'])

# JSON file structure:
# {
#     "key": {
#         "en": "English message $0",
#         "ja": "Japanese message $0",
#         ...
#     },
#     ...
# }
import os
import json
from pathlib import Path
from typing import List, Union
from libcommon.language import Language

# Set logger
from libcommon.logger import Logger
from libcommon.color import *

logger = Logger('Locale')
logger.setLevel(logger.INFO)

# L-1: config 依存を除去。DEFAULT_LANG は既定 'en'(getlang のフォールバックのみで使用)。
# アプリ起動時に configure_locale() で上書き可能。check_config はアプリ側の責務に移譲。
_DEFAULT_LANG = 'en'


def configure_locale(default_lang: str) -> None:
    global _DEFAULT_LANG
    _DEFAULT_LANG = default_lang


COMMON_LOCALES_ROOT = (Path(__file__).parent / 'locales').absolute()
COMMON_LOCALES_FILE_PATHS = [
    f'{COMMON_LOCALES_ROOT}/api_response.json',
    f'{COMMON_LOCALES_ROOT}/errors.json',
    f'{COMMON_LOCALES_ROOT}/validation_errors.json',
]

class Locale:
    """
    A class to handle locale-specific data loading.

    Loads locale data from JSON files either from a specified directory or 
    from the default location at 'libcommon/locales' if no directory is given.

    Example Usage:
    --------------
    # Loading a locale file from a custom directory
    locale_data = Locale('application/locales/inquiry.json').json()

    # Loading a locale file from the default 'libcommon/locales' directory
    locale_data = Locale('validation_errors.json').json()

    # Loading multiple locale files from both custom and default directories
    locale_data = Locale([
        'application/locales/inquiry.json',
        'validation_errors.json']).json()

    """
    __required_langs__: List[str] = ['en', 'ja', 'zh'] #Language.values()  # ['en', 'ja',..] 
    __file_paths__: List[str] = []
    __dict__: dict = {}

    def __init__(self, file_paths: Union[str, List[str]]):
        """
        Initializes a new instance of the Locale class.
        """
        self.__file_paths__ = []
        file_paths = file_paths if isinstance(file_paths, list) else [file_paths]

        logger.debug(light_green(f'Locale object initialized with file paths {file_paths}'))

        for file_path in file_paths:
            self.__file_paths__.append(file_path)

        self.__dict__ = self.load_files(self.__file_paths__)

    @staticmethod
    def load_files(file_paths: List[str]) -> dict:
        """
        Loads locale data from the specified files.
        """
        data = {}
        for file_path in file_paths:
            with open(file_path) as f:
                data.update(json.load(f))
        return data

    def add_locale_file(self, new_file_path: str):
        """
        Adds a new locale file to the current Locale instance.

        Args:
            new_file_path (str): The path to the new locale file to be loaded.

        Raises:
            FileNotFoundError: If the new file path does not exist.
            ValueError: If the file content is not a valid JSON.
        """
        # Ensure the file exists
        if not os.path.exists(new_file_path):
            raise FileNotFoundError(f"No file found at {new_file_path}")

        # Load the new locale file
        with open(new_file_path, 'r') as file:
            new_data = json.load(file)

        # Count the number of keys in the loaded JSON
        key_count = len(new_data.keys())

        # Update the locale dictionary with new data
        self.__dict__.update(new_data)

        # Add new file path to the list of file paths
        self.__file_paths__.append(new_file_path)

        logger.debug(light_green(f'Added new locale file: {new_file_path}'))
        logger.info(f'Locale data updated with file: {new_file_path}')
        logger.debug(f'The loaded JSON file contains {key_count} keys.')

    def get(self, key: str, lang: str, locale_args: list = None) -> str:
        """
        Retrieves a localized message from the json data based on the provided key and language.

        Args:
            key (str): The identifier for the message to retrieve. 
                       This should correspond to an existing key in the json data.

            lang (str): The language in which the message is desired. 
                        This should correspond to one of the names defined in `Language.names()`.

            *args (tuple, optional): Additional arguments that may be used to replace placeholders 
                                     (in the form of $i) in the retrieved message.

        Returns:
            message (str): The localized message retrieved from the json data. 

        Raises:
            KeyError: If the provided key is not found in the json data.
            ValueError: If the provided language is not found for the given key in the json data, 
                        or if a placeholder in the message cannot be replaced by the provided arguments.
        """
        if key not in self.__dict__:
            raise KeyError(f'No key "{key}" found in {self.__file_paths__}')

        if lang not in self.__dict__[key]:
            raise ValueError(f'No lang "{lang}" of key "{key}" found in {self.__file_paths__}')

        m = self.__dict__[key][lang]
        if locale_args:
            for i, arg in enumerate(locale_args):
                if f'${i}' not in m:
                    raise ValueError(f'${i} not in the message:{m}')
                if isinstance(arg, int) or isinstance(arg, float):
                    arg = str(arg)
                m = m.replace(f'${i}', arg)

        logger.debug(f'locale generated message -> "{m}" (key: {key} lang: {lang}) ')
        return m

    def to_json_string(self):
        """Return a hashable text set.

        returns:
            - messages_dict (json) : a text collection json object including all languages
        """
        #self.check_langs()
        return json.dumps(
            self.__dict__,
            sort_keys=True,
            indent=4,
            separators=(',', ': '))

    def json(self):
        """Return the dictionary.

        returns:
            - messages_dict (dict) : a text collection dict object including all langs
        """
        return self.dict()

    def dict(self):
        """Return the dictionary.

        returns:
            - messages_dict (dict) : a text collection dict object including all langs
        """
        #self.check_langs()
        return self.__dict__

    def check_langs(self):
        """Check if lang is complete.

        returns:
            - ok (bool) : if not, assertion error raises.
        """
        for key, d in self.__dict__.items():
            for lang in self.__required_langs__:
                if lang not in d:
                    message = f'{key} doesn\'t include lang {lang}'
                    logger.error(red(message))
                    assert False, message
        return True
 
    @staticmethod
    def getlang(request):
        """Get lang from HTTP request object.

        language is set by the format as below.
        https://xxx.com/aa/?lang=ja

        if "?lang={}" doesn't exist in url, 
        Config.DEFAULT_LANG is used.

        args:
            - request (Flask Request Object)

        return:
            - lang (str) : eg. ja

        """
        lang = request.args.get('lang') \
            if Language.is_valid_value(request.args.get('lang')) \
            else _DEFAULT_LANG
        return lang