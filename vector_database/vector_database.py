# llm/vector_database.py
#
from pydantic import BaseModel
from typing import Dict, List, Union, Optional
from uuid import uuid4

from pydantic import ValidationError
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import ApiException, UnexpectedResponse
from qdrant_client.models import Distance, PointStruct, VectorParams, FieldCondition, Filter, MatchValue, MatchAny

from libcommon.vector_database.sentence_encoder import SentenceEncoder

from libcommon.color import bold, cyan, magenta, yellow, green, red
 
from datetime import datetime
from libcommon.dateutils import datetime_to_iso8061

from libcommon.logger import Logger
logger = Logger('VectorDatabase')
logger.setLevel(logger.DEBUG)

class CollectionOptions(BaseModel):
    """
    TODO: achieve more detailed optimization

    https://qdrant.tech/documentation/concepts/collections/
    https://github.com/qdrant/qdrant/blob/master/config/config.yaml

    hnsw_config - see indexing for details.
    wal_config - Write-Ahead-Log related configuration. See more details about WAL
    optimizers_config - see optimizer for details.
    shard_number - which defines how many shards the collection should have. See distributed deployment section for details.
    on_disk_payload - defines where to store payload data. If true - payload will be stored on disk only. Might be useful for limiting the RAM usage in case of large payload.
    quantization_config - see quantization for details.
    """
    hnsw_config: dict
    wal_config: dict
    optimizers_config: dict
    shard_number: dict
    on_disk_payload: dict
    quantization_config: dict


class Document(BaseModel):
    id: str
    payload: Dict
    vector: Optional[List[float]]


class VectorDatabase:
    def __init__(
            self,
            host: str = None,
            port: int = None,
            encoder: SentenceEncoder = None,
            test_on_memory: bool = False
    ):
        """Vector Database Interface.

        Args:
            host (str): Hostname of the Qdrant server. Used in conjunction with port.
            port (int): Port number of the Qdrant server. Used in conjunction with port.
            log_level (int, optional): Integer or literal log level. (Default = ERROR/40)
        """
        # Connect to client
        if not test_on_memory and (host is None or port is None):
            raise ValueError('Must provide either both `host` and `port`.')
        elif test_on_memory:
            self.client = QdrantClient(':memory:')
        else:
            self.client = QdrantClient(host=host, port=port)

        self.encoder = encoder
        self.embedding_dim = encoder.embedding_dim

    def collection_exists(self, collection_name) -> bool:
        """Checks if a collection already exists in the store."""
        exists = collection_name in [c.name for c in self.client.get_collections().collections]
        logger.debug(f'Collection {collection_name} does'
                     f'{"" if exists else " not"} exist in the database')
        return exists

    def chat_history_collection_name(self, user_id):
        return f'{user_id}_chats'

    def knowledgebase_collection_name(self, user_id):
        return f'{user_id}_documents'

    def create_collection(
            self,
            collection_name: str,
            collection_config: Dict = None,
            recreate: bool = False
    ) -> None:
        """Creates the collection in the Qdrant database.

        Args:
            collection_name (str): Name of the Qdrant collection to which to connect.
            collection_config (dict): Dictionary specifying collection configuration, including the vector
                configuration. For more information, refer to https://qdrant.tech/documentation/concepts/collections/
                for a detailed explanation of options.
            recreate (bool, optional): Whether to delete and re-create the collection if it already exists.
                (Default = False)
        """
        if not recreate:
            if self.collection_exists(collection_name):
                # Collection already exists, continue
                logger.warning(
                    f'Collection of name {collection_name} already exists, skipping creation...')
                return

        # Create collection configuration
        collection_config = collection_config or dict()
        vector_params = VectorParams(
            size=self.embedding_dim,
            distance=Distance.COSINE
        )
        logger.debug(f'Creating collection with vector_params: '
                     f'(size={self.embedding_dim}, distance=Distance.COSINE)')

        # Create collection
        if recreate:
            self.client.recreate_collection(collection_name, vectors_config=vector_params, **collection_config)
            logger.info(f'Recreated collection {collection_name}')
        else:
            self.client.create_collection(collection_name, vector_params, **collection_config)
            logger.info(f'Created collection {collection_name}')

    def uuid(self):
        """Generate a random 32-character hexadecimal UUID for the inserted point."""
        return uuid4().hex

    def save(
            self,
            collection_name: str,
            sentence: str,
            keywords: Optional[List[str]] = None,
            metadata: Optional[dict] = None,
            id: Optional[str] = None
        ) -> Document:
        """Inserts or updates an item to the Qdrant store.

        Args:
            sentence (str): String to put to the Qdrant collection.
            collection_name (str): Name of the Qdrant collection to which to connect.
            id (Optional[str]): must be UUID. uuid4().hex (32-character hexadecimal) is used if not set.
            keywords (Optional[List[str]]): Optional keywords related to the sentence.
            metadata (Optional[dict]): Additional metadata for the payload.

        Returns:
            Document: Document instance with id, text, keywords, and vector.
        """

        vector = self.encoder(sentence).squeeze().tolist()

        # Creating the payload
        payload = {
            "text": sentence,
            "keywords": keywords if keywords else []
        }
        
        # Merge the metadata into the payload
        if metadata:
            payload.update(metadata)

        # Create a random UUID (should have extremely minimal collisions)
        uuid = id or self.uuid()
        try:
            # Insert/update the point
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=uuid,
                        vector=vector,
                        payload=payload
                    )
                ]
            )

            # Optional logging
            logger.info(yellow(f'Successfully inserted point id:{uuid} in collection {collection_name}:'))
            logger.debug(f'--------------------')
            logger.debug(f'Payload: {payload}')
            logger.debug(f'Vector sum: {sum(vector)}')
            logger.debug(f'--------------------')
        # Error handling
        except (ValueError, ValidationError) as e:
            # Catch client-side errors
            logger.error(red(f'Could not parse point {uuid}:\n{str(e)}'))
            raise e
        except (ConnectionError, ApiException, UnexpectedResponse) as e:
            # Catch server-side errors
            logger.error(
                red(f'Encountered a server error when attempting to upsert point {uuid}:\n{str(e)}'))
            raise e
        except Exception as e:
            # Catch all
            logger.error(red(f'Failed to insert point {uuid}:\n{str(e)}'))
            raise e

        # Return the Document instance
        return Document(id=uuid, text=sentence, keywords=keywords if keywords else [], vector=vector, payload=payload)


    def search(
            self,
            sentence: str,
            collection_name: str,
            keywords: List[str] = None,
            metadata: Optional[dict] = {},
            num_results: int = 3,
            must_match_any: bool = True
    ) -> List[Document]:
        
        embedding = self.encoder(sentence).squeeze().tolist()

        query = {
            "collection_name": collection_name,
            "query_vector": embedding,
            "limit": num_results
        }

        # Construct filter conditions without using the Payload class
        filter_conditions = []
        
        # Create conditions for keywords
        if keywords:
            if must_match_any:
                match_condition = MatchAny(any=keywords)
                filter_conditions.append(FieldCondition(key="keywords", match=match_condition))
            else:
                keyword_conditions = [FieldCondition(key="keywords", match=MatchValue(value=keyword)) for keyword in keywords]
                filter_conditions.extend(keyword_conditions)
                
        # Create conditions for metadata
        if metadata:
            metadata_conditions = [FieldCondition(key=k, match=MatchValue(value=v)) for k, v in metadata.items()]
            filter_conditions.extend(metadata_conditions)

        # Adding filter conditions to the query
        if filter_conditions:
            query["query_filter"] = Filter(must=filter_conditions) if must_match_any else Filter(should=filter_conditions)

        try:
            results = self.client.search(**query, with_vectors=False, with_payload=True)
        except ApiException as e:
            logger.error(red(f'search error: {e}'))

        logger.debug(f'Search results ')
        logger.debug(bold(f'\n {results}'))

        documents = [Document(
            id=r.id,
            payload=r.payload,
            vector=r.vector if r.vector else []  # Use an empty list if vector is None
        ) for r in results]

        logger.info(cyan(f'{len(documents)} documents found.'))

        return documents


    def find_one(self, collection_name: str, metadata: dict = None, keywords: list = None) -> Optional[Document]:
        """
        Find a document in the collection that matches the provided metadata or keywords.

        Args:
            collection_name (str): Name of the Qdrant collection to search.
            metadata (dict): Metadata to match against. 
            keywords (list): List of keywords to match against.

        Returns:
            Document: Matching document or None if not found.
        """
        # Return None if neither metadata nor keywords are provided
        if not metadata and not keywords:
            return None

        results = self.search(sentence="", collection_name=collection_name, 
                              keywords=keywords, metadata=metadata, 
                              num_results=1, must_match_any=True)

        return results[0] if results else None


    def find_one_and_update(
            self, 
            collection_name: str, 
            new_sentence: str, 
            keywords: Optional[List[str]] = None,
            metadata: Optional[dict] = None
        ) -> Union[bool, Document]:
        """Updates a stored entity by its unique id.

        Args:
            collection_name (str): Name of the Qdrant collection to update.
            new_sentence (str): The new sentence value to update.
            keywords (Optional[List[str]]): Optional updated keywords related to the sentence.
            metadata (Optional[dict]): Optional updated metadata related to the document.

        Returns:
            Union[bool, Document]: The updated document if successful, or False otherwise.
        """
        vector = self.encoder(new_sentence).squeeze().tolist()

        # Locate the document first
        document = self.find_one(collection_name, metadata=metadata, keywords=keywords)

        # If the document isn't found, return False
        if not document:
            logger.error(red(f'Failed to find point with metadata {metadata} and keywords {keywords}.'))
            return False

        # Extract the ID of the found document
        id = document.id

        # Create the payload dictionary directly
        payload = {
            "text": new_sentence,
            "keywords": keywords if keywords else [],
            "updated": datetime_to_iso8061(datetime.now())  # Add "updated" timestamp to the payload
        }

        # Merge the metadata into the payload if provided
        if metadata:
            payload.update(metadata)

        try:
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )

            # Return the updated Document instance
            return Document(
                id=id,
                payload=payload,
                vector=vector
            )

        except (ValueError, ValidationError, ConnectionError, ApiException, UnexpectedResponse) as e:
            logger.error(red(f'Failed to update point {id}:\n{str(e)}'))
            return False

    def delete_collection(self, collection_name: str) -> None:
        """Deletes the collection from the Qdrant database.

        Args:
            collection_name (str): Name of the Qdrant collection to delete.
        """
        if self.collection_exists(collection_name):
            self.client.delete_collection(collection_name)
            logger.info(magenta(f'Deleted collection {collection_name}'))
        else:
            logger.warning(f'Collection {collection_name} does not exist, skipping deletion...')


    def fetch_by_id(self, collection_name: str, id: str) -> Optional[Document]:
        """Fetches a vector by its unique id.

        FIXME: This method doesn't work properly. This can't find by id.

        Args:
            collection_name (str): Name of the Qdrant collection to query.
            id (str): The unique id of the stored entity.

        Returns:
            Document: The document's content or None if not found.
        """
        try:
            # Setting up a filter to match the specific ID
            filter_condition = Filter(
                must=[
                    FieldCondition(
                        key="id",
                        match=MatchValue(value=id)
                    )
                ]
            )

            results = self.client.search(
                collection_name=collection_name,
                query_vector=[0.0] * self.embedding_dim,  # Using a dummy vector for the query. The filter will override the similarity based on this.
                query_filter=filter_condition,
                limit=1,  # Since ID is unique, expecting only one result
                with_payload=True
            )

        except ApiException as e:
            logger.error(red(f'{e}'))
            return None

        if results:
            r = results[0]
            text = list(r.payload.keys())[0]
            keywords = r.payload.get("keywords", [])
            metadata = r.payload.get("metadata", {})
            logger.info(cyan(f'successfully found by id:{r.id} text:{text} metadata: {metadata}'))
            return Document(
                id=r.id,
                text=text,
                keywords=keywords,
                metadata=metadata,
                vector=r.vector
            )
        else:
            logger.warning(f'not found by id: {id} in {collection_name}')
            return None

