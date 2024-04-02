## Vector Database with Sentence Encoder

### Description

This software provides an interface for managing and querying vectorized representations of sentences using the Qdrant database. Leveraging the power of HuggingFace Transformers, it facilitates the embedding of sentences, making them searchable in a high-dimensional vector space. Useful for various NLP applications including semantic search, recommendation systems, and knowledge management.

### Prerequisites

- **Python**: Version 3.9 or higher.
- **Libraries**:
  - Install `qdrant_client`: To interface with the Qdrant database.
  - Install `transformers`: To use HuggingFace Transformers for sentence encoding.

To install the necessary libraries, you can use:

```
pip install pydantic qdrant_client transformers
```


# Usage Examples 

This README provides an overview of the integration of sentence encoders (like MPNet and MiniLM) with a vector database for document storage and retrieval.

## Setting up Encoders

Before utilizing the vector database, you need to initialize your sentence encoders. In our example, we're using two different models: MPNet and MiniLM, both loaded from `sentence-transformers`.

### Initialize MPNet encoder
```python
from libcommon.vector_database.sentence_encoder import SentenceEncoder
encoder_mpnet_checkpoint = 'sentence-transformers/all-mpnet-base-v2'
mpnet_embedding_dim = 768
encoder_mpnet = SentenceEncoder(
    encoder_mpnet_checkpoint, embedding_dim=mpnet_embedding_dim, device='cuda:2')
```

### Initialize MiniLM encoder
```python
encoder_minilm_checkpoint = 'sentence-transformers/all-MiniLM-L6-v2'
minilm_embedding_dim = 384
encoder_minilm = SentenceEncoder(
    encoder_minilm_checkpoint, embedding_dim=minilm_embedding_dim, device='cuda:3')
```

### Initialize VectorDatabase
```python
from libcommon.vector_database.vector_database import VectorDatabase
vdb = VectorDatabase(
    host=db_host,  # Your running qdrant server host
    port=db_port,  # Your running qdrant server port
    encoder=encoder,  # SentenceEncoder instance
    test_on_memory=False  # if true, write only to memory
)
```
### Create a collection if not exist
```python
collection_name = \
    vdb.documents_collection_name(user_id)
if not vdb.collection_exists(collection_name):
    vdb.create_collection(collection_name=collection_name)
```

### Save a document

```python
doc_instance = vdb.save(
    collection_name=collection_name,
    sentence=doc,
    keywords=keywords
)
```

### Search for Relevant Documents

```python
documents = vdb.search(
    sentence=query,
    collection_name=collection_name,
    num_results=num_results
)
```

### Find a Document

```python
doc = vdb.find_one(
    collection_name=collection_name,
    new_sentence=new_sentence,
    keywords=keywords,
    metadata=metadata
)
```

### Find and Update a Document

```python
updated_doc = vdb.find_one_and_update(
    collection_name=collection_name,
    new_sentence=new_sentence,
    keywords=keywords,
    metadata=metadata
)
```

### Delete a Collection

```python
vdb.delete_collection(collection_name=collection_name)
```


### Configurable Options

- Collection settings can be modified using the `CollectionOptions` class, which provides detailed optimization options. For in-depth details, refer to the Qdrant documentation.

- The `QueryFilter` class provides a structured way to handle filter conditions for search queries.

---

For more detailed information and to expand on the software's capabilities, refer to the provided source code.
