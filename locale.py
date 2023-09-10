#!/usr/local/bin/python
# -*- coding:utf-8 -*-

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
import logging
import json
from config import Config
from typing import List, Union
from libcommon.language import Language

LOCALES_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'locales')

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

    def __init__(self, file_paths: Union[str, List[str]], locales_root = LOCALES_ROOT):
        """
        Initializes a new instance of the Locale class.
        """
        self.__file_paths__ = []
        file_paths = file_paths if isinstance(file_paths, list) else [file_paths]

        for file_path in file_paths:
            if '/' in file_path:
                self.__file_paths__.append(file_path)
            else:
                self.__file_paths__.append(os.path.join(locales_root, file_path))

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

    def get(self, key: str, lang: str, *args) -> str:
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
            raise ValueError(f'No lang {lang} of key "{key}" found in {self.__file_paths__}')

        m = self.__dict__[key][lang]
        for i, arg in enumerate(args):
            if f'${i}' not in m:
                raise ValueError(f'${i} not in the message:{m}')
            m = m.replace(f'${i}', arg)

        logging.debug(f'Error message generated for key:{key} lang:{lang} as {m}')
        return m

    def json(self):
        """Return a hashable text set.

        returns:
            - messages_dict (json) : a text collection json object including all languages
        """
        self.check_langs()
        return json.dumps(
            self.__dict__,
            sort_keys=True,
            indent=4,
            separators=(',', ': '))

    def dict(self):
        """Return the dictionary.

        returns:
            - messages_dict (dict) : a text collection dict object including all langs
        """
        self.check_langs()
        return self.__dict__

    def check_langs(self):
        """Check if lang is complete.

        returns:
            - ok (bool) : if not, assertion error raises.
        """
        for key, d in self.__dict__.items():
            for lang in self.__required_langs__:
                if lang not in d:
                    assert False, f'{key} doesn\'t include lang {lang}' 
        return True
 
    @staticmethod
    def getlang(request):
        """Get lang from HTTP request object.

        language is set by the format as below.
        https://xxx.com/aa/?lang=ja

        if "?lang={}" doesn't exist in url, 
        Config.DEFAULT_LANGUAGE is used.

        args:
            - request (Flask Request Object)

        return:
            - lang (str) : eg. ja

        """
        lang = request.args.get('lang') \
            if Language.is_valid_value(request.args.get('lang')) \
            else Config.DEFAULT_LANGUAGE
        return lang