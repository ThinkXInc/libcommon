#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# api/helpers/locale.py
#
# usage 1 (single message):
#   errors_locale = Locale(f'path/to/errors.json')
#   print(errors_locale.message('value_error', 'ja', first_name, last_name))

# usage 2 (dictionary of a view):
#   view_text_dict = Locale(f'path/to/view.json')
#
#  
# errors.json
#  {
#     "user_already_exists": {
#         "en": "user from $0 already exists.",
#         "ja": "$0はすでに存在するユーザーです。",
#         ...
#     },
#   ...
#  }
#
# top_view.json
#  {
#     "page_title": {
#         "en": "Hello $0.",
#         "ja": "こんにちは $0",
#         ...
#     },
#   ...
#  }


import logging
import json
from config import Config
from typing import List, Union
from libcommon.language import Language

class Locale:
    __langs__: List[str] = ['en', 'ja', 'zh']
    __file_paths__: List[str] = []
    __dict__: dict = {}

    def __init__(self, file_paths: Union[str, List[str]]):
        self.__file_paths__ = file_paths if isinstance(file_paths, list) else [file_paths]
        self.__dict__ = self.load_files(self.__file_paths__)

    @staticmethod
    def load_files(file_paths: List[str]) -> dict:
        data = {}
        for file_path in file_paths:
            with open(file_path) as f:
                data.update(json.load(f))
        return data

    def message(self, key: str, lang: str, *args) -> str:
        """Generate a message of key and lang.

        args:
            - key (str): 
            - lang (str): lang name defined in Language.names()
            - *args (tuple): replaced with $i
        returns:
            - message (str): message for the key and lang
        """
        assert key in self.__dict__, f'no key {key} found in errors.json'
        assert lang in self.__dict__[key], \
            f'no lang {lang} of key {key} found in errors.json'
        m = self.__dict__[key][lang]
        for i, arg in enumerate(args):
            assert f'${i}' in m, f'${i} not in the message:{m}'
            m = m.replace(f'${i}', arg)
        logging.debug(f'error message generated for key:{key} lang:{lang} as {m}')
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
            for lang in self.__langs__:
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