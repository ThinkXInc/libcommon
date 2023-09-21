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

# Basic Sample Usage/API

#### VectorDatabase & SentenceEncoder

1. **Initialization**:

   Create an instance of the `VectorDatabase`.

   ```python
   from libcommon.vector_database.sentence_encoder import SentenceEncoder
   from libcommon.vector_database.vector_database import VectorDatabase
   path_to_checkpoint = 'sentence-transformers/all-mpnet-base-v2'
   embedding_dim = 768
   encoder = SentenceEncoder(checkpoint=path_to_checkpoint, embedding_dim=embedding_dim)
   database = VectorDatabase(host="localhost", port=6333, encoder=encoder)
   ```

2. **Collections**:

   - Check if a collection exists:

     ```python
     collection_name = "my_collection"
     exists = database.collection_exists(collection_name)
     ```

   - Create a collection:

     ```python
     config = {...}  # Dictionary specifying collection configuration
     database.create_collection(collection_name, collection_config=config)
     ```

3. **Operations**:

   - Save a sentence:

     ```python
     uuid = database.save("This is a sample sentence.", collection_name)
     ```

   - Search for a sentence:

     ```python
     results = database.search("Find me a similar sentence.", collection_name, num_results=5)
     ```

#### SentenceEncoder

1. **Initialization**:

   Load the model and tokenizer:

   ```python
   from libcommon.vector_database.sentence_encoder import SentenceEncoder
   path_to_checkpoint = 'path_to_checkpoint'
   encoder = SentenceEncoder(checkpoint=path_to_checkpoint)
   ```

   You can specify the tokenizer model.  Oterwise, `AutoTokenizer(path_to_checkpoint)` is used.
   ```python
   from libcommon.vector_database.sentence_encoder import SentenceEncoder
   path_to_checkpoint = 'path/to/model'
   tokenizer_checkpoint = 'path/to/tokenizer'
   encoder = SentenceEncoder(checkpoint=path_to_checkpoint, tokenizer_checkpoint=tokenizer_checkpoint)
   ```

   You can also set a tokenizer.
   ```python
   from libcommon.vector_database.sentence_encoder import SentenceEncoder
   path_to_checkpoint = 'path/to/model'
   tokenizer = AutoTokenizer('path/to/tokenizer')
   encoder = SentenceEncoder(checkpoint=path_to_checkpoint, tokenizer=tokenizer)
   ```


2. **Encode a Sentence**:

   Get the vector representation:

   ```python
   vector = encoder("This is a sample sentence.")
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

## Vector Database Integration

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
    vdb.knowledgebase_collection_name(user_id)
if not vdb.collection_exists(collection_name):
    vdb.create_collection(collection_name=collection_name)
```
### Save a document
example:
```python
def save_document(self, doc: str, keywords: Optional[List[str]] = []) -> None:
    """Stores a document in the external knowledgebase."""
    logger.debug(f'save :\ndoc => {doc}\nkeywords => {keywords}')
    vdb.save(
        sentence=doc,
        keywords=keywords,
        collection_name=collection_name)
```
### Search for Relevant Documents
example:
```python
def search_relevant_documents(self, query: str, num_results=3) -> List[str]:
    """Search relevant documents."""
    return vdb.search(
        query,
        collection_name,
        num_results=num_results)
```

### Configurable Options

- Collection settings can be modified using the `CollectionOptions` class, which provides detailed optimization options. For in-depth details, refer to the Qdrant documentation.

- The `QueryFilter` class provides a structured way to handle filter conditions for search queries.

---

For more detailed information and to expand on the software's capabilities, refer to the provided source code.
