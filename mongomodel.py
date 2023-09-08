from mongoengine import Document, StringField, DateTimeField, ObjectIdField
from datetime import datetime
from bson import ObjectId

class MongoModel(Document):
    # Generic Fields
    created = DateTimeField(default=datetime.utcnow)
    updated = DateTimeField(default=datetime.utcnow)
    
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

