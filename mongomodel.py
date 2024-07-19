from mongoengine import Document, StringField, DateTimeField, ObjectIdField, DoesNotExist, ValidationError
from datetime import datetime
import pytz
from bson import ObjectId

# Logger
from libcommon.logger import Logger
from libcommon.color import *
logger = Logger()
logger.setLevel(logger.INFO)

class MongoModel(Document):
    # Generic Fields
    created = DateTimeField(default=lambda: datetime.now(pytz.utc))  # timezone-aware UTC datetime
    updated = DateTimeField(default=lambda: datetime.now(pytz.utc))  # timezone-aware UTC datetime
    
    # Meta Information
    meta = {
        'abstract': True  # This ensures that the base class won't be used to create any collection
    }

    # ex)
    # meta = {
    #     'collection': 'user',
    #     'indexes': [
    #         {'fields': ['email'], 'type': 'hashed'},
    #         # ... (other indexes)
    #     ]
    # }

    
    def response_json(self, excludes=[]):
        d = self.to_mongo().to_dict()
        for key, value in d.items():
            if isinstance(value, ObjectId):
                d[key] = str(value)
        return {x: d[x] for x in d if x not in excludes}

    @classmethod
    def get_or_create(cls, defaults=None, **kwargs):
        defaults = defaults or {}
        try:
            obj = cls.objects(**kwargs).first()
            if obj:
                return obj, False
            else:
                obj = cls(**kwargs, **defaults)
                obj.save()
                return obj, True
        except ValidationError as e:
            logger.error(f'Validation error on creating {cls.__name__}: {e}')
            raise

    @classmethod
    def count(cls):
        return cls.objects.count()