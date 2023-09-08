#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# models/enums/language.py
#
# Language Enum Module.
# 
# This module provides a `Language` enumeration that represents different languages 
# following the ISO 639-1 standard language codes. Each language has several attributes, 
# including its ISO code, name, and regional variations.
# 
# The main class defined in this module is:
#     - Language : an enumeration for various languages.
# 
# References:
#     ISO 639-1 standard language codes:
#     https://www.andiamo.co.uk/resources/iso-language-codes/
#
# Attributes:
#     __ja__ (dict): A dictionary with language codes as keys and names in Japanese as values.
#     __en__ (dict): A dictionary with language codes as keys and names in English as values.
#     __label__ (dict): A dictionary with language codes as keys and names in the represented languages as values.
# 
# Examples:
#     >>> Language.JA
#     'ja'
#     >>> Language.__ja__[Language.JA]
#     '日本語'
#     >>> Language.__en__[Language.JA]
#     'Japanese'
#
# usage:
#  > Language.values()
#  ['ja', 'en', 'zh',...]
#  
#  > Language.lang_label_map()
#  {'ja': '日本語', 'en': 'English', 'zh': '中文', 'ko': '한국어', 'fr': 'Français', ...}
#
#  > Language.lang_label_map(only=['en', 'ja'])
#  {'ja': '日本語', 'en': 'English'}
#
#  > Language.valueFromIndex(2)
#  'en'
#
#  > Language.indexFromName('EN')
#  2
#
#  > Language.indexFromDict('English', 'en')
#  2
#
#  > Language.labelsIndexFromVal('日本語')
#  1
#
#  > Language.itemlist()
#  ['JA', 'EN', 'ZH', 'KO', 'FR', ...]
#
#  > Language.names()
#  ['JA', 'EN', 'ZH', 'KO', 'FR', ...]
#
#  > Language.values()
#  ['ja', 'en', 'zh', 'ko', 'fr', ...]
#
#  > Language.order()
#  ['ja', 'en', 'zh', 'ko', 'fr', ...]
#
#  > Language.serialize('en')
#  {
#      'JA': 'ja',
#      'EN': 'en',
#      'ZH': 'zh',
#      'KO': 'ko',
#      'FR': 'fr',
#      'order': ['ja', 'en', 'zh', 'ko', 'fr', ...],
#      'titles_dict': {'ja': 'Japanese', 'en': 'English', 'zh': 'Chinese', 'ko': 'Korean', 'fr': 'French', ...}
#  }
#
#  > Language.is_valid_name('EN')
#  True
#
#  > Language.is_valid_value('ja')
#  True
#
#  > Language.to_dict()
#  {
#      'names': ['JA', 'EN', 'ZH', 'KO', 'FR', ...],
#      'values': ['ja', 'en', 'zh', 'ko', 'fr', ...],
#      '__ja__': ['日本語', '英語', '中国語', '韓国語', 'フランス語', ...],
#      '__en__': ['Japanese', 'English', 'Chinese', 'Korean', 'French', ...],
#      '__label__': ['日本語', 'English', '中文', '한국어', 'Français', ...]
#  }
#
#  These values (ja, en, zh,..) follows ISO 639.
#
#    ISO 639 - 1 standard language codes:
#    https://www.andiamo.co.uk/resources/iso-language-codes/
# 

from collections import namedtuple
from typing import List, Dict, Optional
from libcommon.enumlocale import EnumLocale

Record = namedtuple(
    'Record',
    [
        'name',  # eg. Language.JA 
        'value',  # eg. Language.JA.value is 'ja'
        'ja',  # eg. 日本語
        'en',  # eg. Japanese
        'en_with_region',  # eg. Japanese
        'label'  # Label in the language itself
    ]
)

_records = [
    # basic 4
    Record(u"JA", "ja", u"日本語", u"Japanese", "Japanese", u"日本語"),
    Record(u"EN", "en", u"英語", u"English", "English(Standard)", "English"),
    Record(u"ZH", "zh", u"中国語", u"Chinese", "Chinese(PRC)", "中文"),
    Record(u"KO", "ko", u"韓国語", u"Korean", "Korean", "한국어"),
    # europe 5
    Record(u"FR", "fr", u"フランス語", u"French", "French(Standard)", "Français"),
    Record(u"DE", "de", u"ドイツ語", u"German", "German(Standard)", "Deutsch"),
    Record(u"RU", "ru", u"ロシア語", u"Russian", "Russian(Standard)", "Русский"),
    Record(u"ES", "es", u"スペイン語", u"Spanish", "Spanish(Standard)", "Español"),
    Record(u"IT", "it", u"イタリア語", u"Italian", "Italian(Standard)", "Italiano"),
    # asia 6
    Record(u"VI", "vi", u"ベトナム語", u"Vietnamese", "Vietnamese(Standard)", "Tiếng Việt"),
    Record(u"TH", "th", u"タイ語", u"Thai", "Thai(Standard)", "ภาษาไทย"),
    Record(u"HI", "hi", u"ヒンディー語", u"Hindi", "Hindi(Standard)", "हिन्दी"),
    Record(u"ID", "id", u"インドネシア語", u"Indonesian", "Indonesian(Standard)", "Bahasa Indonesia"),
    Record(u"MS", "ms", u"マレーシア語", u"Malaysian", "Malaysian(Standard)", "Bahasa Melayu"),
    Record(u"TL", "tl", u"タガログ語", u"Tagalog", "Tagalog(Standard)", "Tagalog"),

    # chinese - dialects
    #zh_cn = 301  # Chinese(PRC)
    #zh_hk = 302  # Chinese(HongKong)
    #zh_sg = 303  # Chinese(Singapore)
    #zh_tw = 304  # Chinese(Taiwan)

    ## english - dialects
    #en_us = 201  # English(United States)
    #en_gb = 202  # English(United Kingdom)
    #en_au = 203  # English(Australia)
    #en_bz = 204
    #en_ca = 205
    #en_ie = 206
    #en_jm = 207
    #en_nz = 208
    #en_za = 209
    #en_tt = 210
]

d = {}
__ja__, __en__, __label__ = {}, {}, {}
for _record in _records:
    name = _record.name
    value = _record.value
    d[name] = value
    __ja__[value] = _record.ja
    __en__[value] = _record.en
    __label__[value] = _record.label

Language = EnumLocale('Language', d)
Language.__ja__ = __ja__
Language.__en__ = __en__
Language.__label__ = __label__

# Add lang_label_map() method to the Language class
def lang_label_map(cls, only: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Method to return a dictionary mapping language codes to their names in the represented languages.

    Args:
        only (Optional[List[str]], optional): A list of language codes that should be included in the returned dictionary. 
                                              If not provided, labels for all languages will be included.

    Returns:
        Dict[str, str]: A dictionary with language codes as keys and names in the represented languages as values.
    """
    if only is None or len(only) == 0:
        return cls.__label__
    else:
        return {code: name for code, name in cls.__label__.items() if code in only}

# add all __ja__, __en__, ...
# NOTE: the method below misses irregular format
#       like __en_with_ragion__
# for lang in langs:
#     value_dict = getattr(cls, '__'+lang+'__')
#     if value_dict:
#         d[lang] = [val for name, val in value_dict.items()]

Language.lang_label_map = classmethod(lang_label_map)