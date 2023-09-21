import sys
sys.path.append('../')

from libcommon.vector_database.sentence_encoder import SentenceEncoder
from libcommon.vector_database.vector_database import VectorDatabase, Document
from libcommon.color import red, yellow, cyan, green
from bson.objectid import ObjectId
from uuid import uuid4
from datetime import datetime
from libcommon.dateutils import datetime_to_iso8061
import time

# Setup and Initialization
encoder_mpnet_checkpoint = 'sentence-transformers/all-mpnet-base-v2'
mpnet_embedding_dim = 768
encoder_device = 'cuda:2'
host = 'localhost'
port = 6333

encoder = SentenceEncoder(
    encoder_mpnet_checkpoint, embedding_dim=mpnet_embedding_dim, device=encoder_device
)

vdb = VectorDatabase(
    host=host,
    port=port,
    encoder=encoder,
    test_on_memory=False
)

# Ensure collection_name and material_id are provided
user_identifier = "USER001"
collection_name = vdb.knowledgebase_collection_name(user_identifier)
material_id = str(ObjectId())

# Test block 1: Collection existence and creation
try:
    if vdb.collection_exists(collection_name):
        vdb.delete_collection(collection_name)
    if not vdb.collection_exists(collection_name):
        vdb.create_collection(collection_name=collection_name)
    print(green('Test 1 passed: Collection existence and creation'))
except Exception as e:
    print(red(e))
    assert False

# Test block 2: Save document if not already present based on keywords
try:
    sentence = 'The first principle is that you must not fool yourself — and you are the easiest person to fool.'
    keywords = ['Hello world', 'Test']
    document = vdb.find_one(collection_name=collection_name, keywords=keywords)
    if not document:
        metadata = {'material_id': material_id, 'user_id': user_identifier, 'updated': datetime_to_iso8061(datetime.now())}
        vdb.save(collection_name=collection_name, sentence=sentence, keywords=keywords, metadata=metadata)
    print(green('Test 2 passed: Save document based on keywords'))
except Exception as e:
    print(red(e))
    assert False

print('wait for saving..')
time.sleep(2)


# Test block 3: Save another document based on material_id
try:
    sentence = 'For a successful technology, reality must take precedence over public relations, for nature cannot be fooled.'
    document = vdb.find_one(collection_name=collection_name, metadata={"material_id": material_id})
    if not document:
        metadata = {'material_id': material_id, 'user_id': user_identifier, 'updated': datetime_to_iso8061(datetime.now())}
        vdb.save(collection_name=collection_name, sentence=sentence, keywords=keywords, metadata=metadata)
    print(green('Test 3 passed: Save another document based on material_id'))
except Exception as e:
    print(red(e))
    assert False

# Test block 4: Update document by material_id
try:
    new_sentence = 'This is the new reality =>' + datetime.now().strftime('%H:%M:%S')
    results = vdb.find_one_and_update(collection_name, new_sentence, metadata={'material_id': material_id})
    print(green('Test 4 passed: Update document by material_id'))
except Exception as e:
    print(red(e))
    assert False

# Test block 5: Search by similarity
try:
    sentence = 'True reality.'
    results = vdb.search(sentence, collection_name, num_results=3)
    print(green('Test 5 passed: Search by similarity'))
except Exception as e:
    print(red(e))
    assert False

print(green('All tests passed!'))