#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# tools/redisbase.py
#
#
# MODEL DEFINITION:
# 1. create a subclass.
# 2. set each definitions as below in the subclass.
#
#    __key_name_rule__ = ''  # ex) activity:{timestamp}:user_id={user_id}
#    __redis_data_type__ = None  # RedisDataType enum class
#    __expiration_days__ = None  # number of days until expired. ex) 3
#    __structure__ = {}  # define keys and the data type
#    __required_fields__ = []  # lists required keys
#    __default_values__ = {}  # set default values to some keys
#    __validators__ = {}  # set pairs like key: validatefunc()
#
#
# Interface:
# - get()
# - save()
# - delete()
#
#
# BASIC USAGE EXAMPLE:
#
# class Tree(RedisBase):
#    __key_name_rule__ = 'tree:{tree_id}'
#    __redis_data_type__ = RedisDataType.HASH
#    __expiration_days__ = 3
#    __structure__ = {
#       'key': str,
#       'tree_id': int,
#       'plant_family': str,
#       'leaves': int,
#    }
#    __required_fields__ = ['key', 'tree_id']
#    __default_values__ = {
#        'leaves': 0
#    }
#    __validators__ = {
#        'plant_family': {validation method here}
#    }
#
#
# > new_tree = Tree({
# >    'key': 'tree:101',
# >    'tree_id': 101,
# >    'plant_family': 'fagaceae',
# >    'leaves': 3243500000
# >    })
# > new_tree.save()
# > 3  # fields count returned by redis-cli
# > new_tree.get()
# > [('key', 'tree101'), ('tree_id', '101'), ('plant_family', 'fagaceae'),
# ('leaves', '3243500000')]
# > new_tree.delete()
# > 1  # this is also the value returned by redis-cli


import datetime
import time
from enum import Enum

import redis
from redis import StrictRedis

from general.config import Config
from tools.modelbase import ModelBase


class RedisDataType(Enum):
    STRING = 1
    LIST = 2
    HASH = 3
    SET = 4
    ZSET = 5


class InvalidFormat(Exception):
    pass


class RedisBaseFailedToRemoveFromZSET(Exception):
    pass


class RedisBaseFailedToDeleteKey(Exception):
    pass


class RedisBase(ModelBase):
    __key_name_rule__ = ''  # ex) activity:{timestamp}:user_id={user_id}
    __redis_data_type__ = None
    __expiration_days__ = None
    __expiration_hours__ = None
    __redis_host__ = Config.REDIS_HOST_SESSION
    __redis_port__ = Config.REDIS_PORT_SESSION
    __redis_db__ = Config.REDIS_DB_NUMBER_SESSION
    __redis_decode_responses__ = True  # return str, not binary in default

    # set up redis client
    pool = redis.ConnectionPool(host=__redis_host__, port=__redis_port__, db=__redis_db__,
                                decode_responses=__redis_decode_responses__)
    __redis = StrictRedis(connection_pool=pool)

    def __init__(self, init_dict):
        # correct types
        init_dict = self.correctTypesAsStructure(init_dict)
        super().__init__(init_dict)

        # timestamp when created
        self.created = time.time()

    def correctTypesAsStructure(self, init_dict):
        """Correct types of values in init_dict according to
        the __structre__.

        Return corrected init_dict
        """
        for key in self.__structure__:
            if (key in init_dict) \
                    and isinstance(self.__structure__[key], type) \
                    and init_dict[key]:
                # str
                if self.__structure__[key] == str:
                    init_dict[key] = str(init_dict[key])
                # float
                if self.__structure__[key] == float:
                    init_dict[key] = float(init_dict[key])
                # int
                if self.__structure__[key] == int:
                    init_dict[key] = int(init_dict[key])
        return init_dict

    def get(self):
        """Get stored data.

        Execute fetch command  according to the data type.
            get (string) / lrange (list) / hgetall (hash) /
            smembers (set) / zrange (zset)

        when __structure__ returns (returned when the key doesn't exist)
          STRING:
           - str (None)
          LIST:
           - list ([])
          HASH:
           - dict ({})
          SET:
           - set (set())
          ZSET:
           - [] ([])
        """
        return self.getByKey(self.key)

    def delete(self):
        """Delete by key.
        """
        result = self.__redis.delete(self.key)
        if not result:
            raise RedisBaseFailedToDeleteKey('{}'.format(self.key))
        return result

    def __setExpiration(self, expiration_time_in_seconds: int):
        """Set redis expiration.
        """
        return self.__redis.expire(self.key, expiration_time_in_seconds)

    def save(self, expiration_days=None, expiration_hours=None):
        """Store as redis data type.

        Execute save command according to the data type.
            set (string) / rpush (list) / hmset (hash) /
            sadd (set) / hmset (zset)

        When it failed, return False.
        When it succeeded, return what redis save command returns.
        """
        # validate
        self.validate()
        # check required fields
        assert self._is_required_fields_satisfied(), 'reqired key error.'

        # check key
        if 'key' not in self or ('key' in self and self.key is None):
            raise InvalidFormat('key is required.')
            return False

        result = None

        # save
        if self.__redis_data_type__ == RedisDataType.STRING:
            # no key 'val'
            if 'val' not in self or ('val' in self and self.val is None):
                raise InvalidFormat('val is required to save STRING')
                return False
            result = self.__redis.set(self.key, self.val)
        elif self.__redis_data_type__ == RedisDataType.LIST:
            # no key 'val'
            if 'val' not in self or ('val' in self and self.val is None):
                raise InvalidFormat('val is required to save LIST')
                return False
            self.__redis.rpush(self.key, self.val)
        elif self.__redis_data_type__ == RedisDataType.HASH:
            d = self.purify()
            d.pop('key', None)
            _d = d.copy()
            for key, val in _d.items():
                if val is None:
                    d.pop(key, None)
            result = self.__redis.hmset(self.key, d)
        elif self.__redis_data_type__ == RedisDataType.SET:
            # no key 'members'
            if 'members' not in self or \
                    ('members' in self and self.val is None):
                raise InvalidFormat('members is required to save SET.')
                return False
            # 'members' is not of type list
            if not isinstance(self.members, list):
                raise InvalidFormat('members must be of type list.')
                return False
            # 'members' has no members
            if not len(self.members):
                raise InvalidFormat('members\'s length must not be zero.')
                return False
            result = self.__redis.sadd(self.key, *set(self.members))
        elif self.__redis_data_type__ == RedisDataType.ZSET:
            d = self.purify()
            d.pop('key', None)
            # no name
            if 'name' not in self or \
                    ('name' in self and self.val is None):
                raise InvalidFormat('name is required to save ZSET.')
            # no val
            if 'val' not in self or \
                    ('val' in self and self.val is None):
                raise InvalidFormat('val is required to save ZSET.')
            result = self.__redis.zadd(self.key, self.val, self.name)

        # set expiration if needed
        if self.__expiration_days__ or expiration_days:
            expiration_days = expiration_days if expiration_days else \
                self.__expiration_days__
            self.__setExpiration(
                self.expirationTimeDaysInSeconds(expiration_days))
        elif self.__expiration_hours__ or expiration_hours:
            expiration_hours = expiration_hours if expiration_hours else \
                self.__expiration_hours__
            self.__setExpiration(
                self.expirationTimeHoursInSeconds(expiration_hours))

        return result

    # @classmethod
    # def redisClient(cls):
    #     """Return redis client.
    #
    #     This must be called from the subclass.
    #     """
    #     return StrictRedis(
    #         host=cls.__redis_host__,
    #         port=cls.__redis_port__,
    #         db=cls.__redis_db__,
    #         decode_responses=cls.__redis_decode_responses__)

    @classmethod
    def createPipeline(cls, transaction=True):
        """Set new pipeline as RedisBase.pipe.
        """
        return cls.__redis.pipeline(transaction)

    @classmethod
    def executePipeline(cls, pipe):
        """Execute pipeline.
        """
        return pipe.execute()

    @classmethod
    def keys(cls, pattern):
        """Return a list of keys matching pattern.
        """
        return cls.__redis.keys(pattern)

    @classmethod
    def getByKey(cls, key):
        """Get stored data.

        Execute fetch command  according to the data type.
            get (string) / lrange (list) / hgetall (hash) /
            smembers (set) / zrange (zset)

        This must be called from the subclass.
        """
        __redis_data_type__ = cls.__redis_data_type__
        if __redis_data_type__ == RedisDataType.STRING:
            return cls.__redis.keys(key)
        elif __redis_data_type__ == RedisDataType.LIST:
            return cls.__redis.lrange(key, 0, -1)
        elif __redis_data_type__ == RedisDataType.HASH:
            return cls.__redis.hgetall(key)
        elif __redis_data_type__ == RedisDataType.SET:
            return cls.__redis.smembers(key)
        elif __redis_data_type__ == RedisDataType.ZSET:
            return cls.__redis.zrange(key, 0, -1, withscores=True)

    @classmethod
    def saveByDataType(
            cls,
            data_type: RedisDataType,
            key=None,  # key
            val=None,  # STRING, LIST, ZSET
            name=None,  # ZSET
            members=None,  # SET
            dictionary=None,  # HASH
    ):
        """Save by RedisDataType.
        """
        # save
        if data_type == RedisDataType.STRING:
            return cls.__redis.set(key, val)
        elif data_type == RedisDataType.LIST:
            return cls.__redis.rpush(key, val)
        elif data_type == RedisDataType.HASH:
            return cls.__redis.hmset(key, dictionary)
        elif data_type == RedisDataType.SET:
            return cls.__redis.sadd(key, *set(members))
        elif data_type == RedisDataType.ZSET:
            return cls.__redis.zadd(key, val, name)

    @classmethod
    def removeElementFromZSET(cls, key, *name):
        """Delete a (name, value) from ZSET (zrem).

        This must be called from the subclass.
        """
        result = cls.__redis.zrem(key, *name)
        if not result:
            print('The name {} in key {} doesn\'t exist.'.format(name, key))
        return result

    @staticmethod
    def expirationTimeDaysInSeconds(expiration_days: int) -> int:
        """Calcurate relative seconds from expiration days.
        """
        td = datetime.timedelta(days=expiration_days)
        return int(td.total_seconds())

    @staticmethod
    def expirationTimeHoursInSeconds(expiration_hours: int) -> int:
        """Calcurate relative seconds from expiration hours.
        """
        td = datetime.timedelta(hours=expiration_hours)
        return int(td.total_seconds())
