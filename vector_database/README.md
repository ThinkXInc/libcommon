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
pip install qdrant_client transformers
```

# Basic Sample Usage/API

#### VectorDataBase

1. **Initialization**:

   Create an instance of the `VectorDataBase`.

   ```python
   from libcommon.vector_database.sentence_encoder import SentenceEncoder
   encoder = SentenceEncoder(checkpoint="path_to_checkpoint")
   database = VectorDataBase(host="localhost", port=6333, encoder=encoder)
   ```

2. **Collections**:

   - Check if a collection exists:

     ```python
     exists = database.collection_exists("collection_name")
     ```

   - Create a collection:

     ```python
     config = {...}  # Dictionary specifying collection configuration
     database.create_collection("collection_name", collection_config=config)
     ```

3. **Operations**:

   - Save a sentence:

     ```python
     uuid = database.save("This is a sample sentence.", "collection_name")
     ```

   - Search for a sentence:

     ```python
     results = database.search("Find me a similar sentence.", "collection_name", num_results=5)
     ```

#### SentenceEncoder

1. **Initialization**:

   Load the model and tokenizer:

   ```python
   from libcommon.vector_database.sentence_encoder import SentenceEncoder
   encoder = SentenceEncoder(checkpoint="path_to_checkpoint")
   ```

2. **Encode a Sentence**:

   Get the vector representation:

   ```python
   vector = encoder("This is a sample sentence.")
   ```


# Sentence Encoder and Vector Database Integration

This README provides an overview of the integration of sentence encoders (like MPNet and MiniLM) with a vector database for document storage and retrieval.

## Setting up Encoders

Before utilizing the vector database, you need to initialize your sentence encoders. In our example, we're using two different models: MPNet and MiniLM, both loaded from `sentence-transformers`.

```python
max_sequence_size = 4096
encoder_mpnet_checkpoint = 'sentence-transformers/all-mpnet-base-v2'
mpnet_embedding_dim = 768
encoder_minilm_checkpoint = 'sentence-transformers/all-MiniLM-L6-v2'
minilm_embedding_dim = 384

# Initialize MPNet encoder
encoder_mpnet = SentenceEncoder(
    encoder_mpnet_checkpoint, embedding_dim=mpnet_embedding_dim, device='cuda:2')

# Initialize MiniLM encoder
encoder_minilm = SentenceEncoder(
    encoder_minilm_checkpoint, embedding_dim=minilm_embedding_dim, device='cuda:3')
```

## Vector Database Integration

### Initialize VectorDatabase
```python
vdb = VectorDataBase(
    host=db_host,  # Your running qdrant server host
    port=db_port,  # Your running qdrant server port
    encoder=encoder,  # SentenceEncoder instance
    test_on_memory=False  # if true, write only to memory
)

# create collection if not exist
collection_name = \
    vdb.knowledgebase_collection_name(user_id)
if not vdb.collection_exists(collection_name):
    vdb.create_collection(collection_name=collection_name)
```

### Saving Documents

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

### Searching for Relevant Documents

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
