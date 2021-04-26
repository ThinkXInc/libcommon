#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# modelbase_test.py
# Gate.
#
# unittest for modelbase.py
#

from nose.tools import raises
from tools.modelbase import ModelBase
from bson.objectid import ObjectId
from tools.validator import Validator
from tools.app_testcase import AppTestCase
from general.exceptions import RequiredKeyIsNotSatisfied
from general.exceptions import TextTooLong
from general.commons import LongText
import datetime


class ModelBaseTestCase(AppTestCase):

    def setUp(self):
        super().setUp()

        # define sample class
        class Dog(ModelBase):
            __structure__ = {
                '_id': ObjectId,
                'name': str,
                'has_babies': bool,
                'babies_num': int,
                'favorite_food': str,
                'born': datetime.datetime
            }
            __required_fields__ = ['name']
            __default_values__ = {
                'has_babies': False,
                'babies_num': 0,
                'favorite_food': ''
            }
            __validators__ = {
                'name': Validator.validate_length('name', 0, 10)
            }

        self.Dog = Dog

    def generateValidDogDict(self, _id):
        return {
            '_id': _id,
            'name': 'John',
            'has_babies': True,
            'babies_num': 2,
            'favorite_food': 'Raw fish',
            'born': datetime.datetime.now()
            }

    @raises(TypeError)
    def test_validate(self):
        dog_valid = self.Dog(self.generateValidDogDict(_id=1))
        try:
            dog_valid.validate()
        except TypeError:
            assert False
        else:
            assert True

        dog_invalid = self.Dog(self.generateValidDogDict(_id=1))
        dog_invalid.has_babies = 'False'
        dog_invalid.validate()

    @raises(TextTooLong)
    def test_validate_length(self):
        dog_with_too_long_name = self.Dog(self.generateValidDogDict(_id=1))
        dog_with_too_long_name.name = LongText.longtext()
        dog_with_too_long_name.validate()

    def test_serialize(self):
        dog = self.Dog(self.generateValidDogDict(_id=1))
        dog_serialized = dog.serialize()
        assert isinstance(dog_serialized['born'], str)

    @raises(RequiredKeyIsNotSatisfied)
    def test_checkRequiredFields(self):
        dog = self.Dog(self.generateValidDogDict(_id=1))
        dog.name = None
        dog._checkRequiredFields()
