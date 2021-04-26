#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# mongobase_test.py
# Gate.
#
# unittest for mongobase.py
#

from nose.tools import eq_, ok_
from tools.app_testcase import AppTestCase
from tools.mongobase import MongoBase
from tools.validator import Validator
from bson.objectid import ObjectId
import datetime


class MongoBaseTestCase(AppTestCase):
    GENERIC_ID = 9999999999999999
    GENERIC_ID_2 = 88888888888888888

    def setUp(self):
        super().setUp()

        # define sample class
        class Dog(MongoBase):
            __collection__ = 'dogs'
            __structure__ = {
                '_id': ObjectId,
                'name': str,
                'has_babies': bool,
                'babies_num': int,
                'favorite_food': str,
                'born': datetime.datetime
            }
            __required_fields__ = ['name']
            __indexed_keys__ = ['name', 'favorite_food']
            __default_values__ = {
                'has_babies': False,
                'babies_num': 0,
                'favorite_food': ''
            }
            __validators__ = {
                'name': Validator.validate_length('name', 0, 10)
            }

            def save(self, should_return_if_exists=False):
                if not self._id:
                    self._id = self.incrementalId()
                return self.insertIfNotExistsWithKeys(
                    should_return_if_exists, '_id')

        self.Dog = Dog

    def generateDogDict(self, _id):
        return {
            '_id': _id,
            'name': 'hum',
            'has_babies': True,
            'babies_num': 101,
            'favorite_food': 'spam',
            'born': datetime.datetime.now()
        }

    def test_insertIfNotExistsWithKeys(self):
        dog = self.Dog(self.generateDogDict(self.GENERIC_ID))
        saved_dog = dog.insertIfNotExistsWithKeys(False, '_id')
        eq_(saved_dog._id, self.GENERIC_ID)

    def test_remove(self):
        ok_(self.Dog.remove({'_id': self.GENERIC_ID}))

    def test_textSearch(self):
        dog = self.Dog(self.generateDogDict(self.GENERIC_ID_2))

        dog.save()

        search_results = self.Dog.textSearch('hum', limit=1, skip=0)
        ok_(search_results)

        search_results = self.Dog.textSearch('humm', limit=1, skip=0)
        ok_(search_results)

        search_results = self.Dog.textSearch('humstar', limit=1, skip=0)
        ok_(search_results)

        search_results = self.Dog.textSearch('pig', limit=1, skip=0)
        eq_(search_results, [])

        search_results = self.Dog.textSearch('spam', limit=1, skip=0)
        ok_(search_results)

    def prepareDogs(self):
        dog1 = self.Dog({
            'name': 'egg',
            'has_babies': True,
            'babies_num': 102,
            'favorite_food': 'dogfood',
            'born': datetime.datetime.now()
        })
        dog1.save()

        dog2 = self.Dog({
            'name': 'bacon',
            'has_babies': False,
            'babies_num': 0,
            'favorite_food': 'meat',
            'born': datetime.datetime.now()
        })
        dog2.save()

        dog3 = self.Dog({
            'name': 'potato',
            'has_babies': True,
            'babies_num': 100,
            'favorite_food': 'meat',
            'born': datetime.datetime.now()
        })
        dog3.save()

        return dog1, dog2, dog3

    def test_count(self):
        self.Dog.remove({})
        self.prepareDogs()

        eq_(self.Dog.count(
            {'name': 'egg'}), 1)
        eq_(self.Dog.count(
            {}), 3)
        eq_(self.Dog.count(
            {'babies_num': {'$gte': 1}, 'babies_num': {'$lte': 103}}), 3)
