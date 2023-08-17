#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# enum_locale.py
#
# subclass from Enum
#
# usage:
#   class Animal(EnumLocale):
#       CAT = 1
#       DOG = 2
#       COW = 3
#
#       __ja__ = {1: '猫', 2: '犬', 3: '牛'}
#
#
#   > Animal(3).name
#   > COW
#   > Animal.valueFromIndex(3, 'ja')
#   > 牛
#   > Animal.__ja__
#   > {1: '猫', 2: '犬', 3: '牛'}
#   > Animal.itemlist()
#   > ['CAT', 'DOG', 'COW']
#
#   > Animal.is_valid_name('CAT')
#   > True
#   > Animal.is_valid_name('FROG')
#   > False
#   > Animal.is_valid_value(1)
#   > True
#   > Animal.is_valid_value(99)
#   > False
#
#   > Animal.to_dict()
#   {
#     "names": ["CAT", "DOG", "COW"],
#     "values": [0, 1, 2],
#     "ja": ["猫", "犬", "牛"],
#     "en": ["Cat", "Dog", "Cow"],
#     ...
#   }


from enum import Enum

class EnumLocale(Enum):
    @classmethod
    def valueFromIndex(cls, index: int, lang='ja'):
        try:
            index = int(index)
        except (TypeError, ValueError) as e:
            return None

        if index > 0 and index < len(list(cls))+1:
            if lang == 'en':
                return cls(index).name
            else:
                value_dict = getattr(cls, '__'+lang+'__')
                return value_dict[index]
        return None

    @classmethod
    def indexFromName(cls, name: str) -> int:
        """Return index from name.

        usage:
          > Animal.indexFromName('DOG')
          > 2  # Animal.DOG.value
          > Animal.indexFromName('not in list')
          > None
        """
        if name not in cls.__members__.keys():
            return None
        else:
            return cls[name].value

    @classmethod
    def indexFromDict(cls, name: str, dictname: str) -> int:
        """Return index from japanese word

        """
        _dict = getattr(cls, '__' + dictname + '__')
        if name not in _dict.values():
            return None
        else:
            return list(_dict.keys())[int(list(_dict.values()).index(name))]

    @classmethod
    def labelsIndexFromVal(cls, val: str) -> int:
        """Return index x from cls.__labels__ = {x: val} with val.

        ex)
          __labels__ = {
              1: 'A',
              2: 'B',
              3: 'C'
          }
          > Answer.labelsIndexFromVal('A')
          1
        """
        _dict = getattr(cls, '__labels__')
        if val not in _dict.values():
            return None
        else:
            return list(_dict.keys())[int(list(_dict.values()).index(val))]

    @classmethod
    def itemlist(cls):
        """Returns names.
        
        returns:
            - names (list) : eg. ["CAT, "DOG", "COW"]
        """
        return [name for name, member in cls.__members__.items()]

    @classmethod
    def names(cls):
        """Returns names.
        
        returns:
            - names (list) : eg. ["CAT, "DOG", "COW"]
        """
        return [e.name for e in cls]

    @classmethod
    def values(cls):
        """Returns values.
        
        returns:
            - names (list) : eg. [1, 2, 3]
        """
        return [e.value for e in cls]

    @classmethod
    def order(cls):
        """Return values(1,2,...) in order.
        """
        return [e.value for e in list(cls)]

    @classmethod
    def serialize(cls, lang='ja'):
        enum_dict = {e.name: e.value for e in cls}

        try:
            titles_dict = getattr(cls, '__' + lang + '__')
        except AttributeError:
            titles_dict = {
                (i + 1): e.name
                for i, e in enumerate(cls)}
        finally:
            enum_dict['order'] = cls.order()
            enum_dict['titles_dict'] = titles_dict

            return enum_dict

    @classmethod
    def is_valid_name(cls, name: str):
        """Check if the value is valid as language name.

        args:
            - name (str) : eg. ja

        returns:
            - is_valid (bool) :
        """
        if name is None:
            return False
        return name in cls.names()

    def is_valid_value(cls, value):
        """Check if the number is valid as language value.

        args:
            - value (int or str) : eg. 100 

        returns:
            - is_valid (bool) :
        """
        if value is None:
            return False
        return value in cls.values()

    @classmethod
    def to_dict(cls) -> dict:
        d = {}
        d["names"] = cls.names()
        d["values"] = cls.values()

        # find __xx__ in the class properties
        props = vars(cls)
        for key, val in props.items():
            if key.startswith('__') and isinstance(val, dict):
                d[key] = [v for k, v in val.items()]
        return d
