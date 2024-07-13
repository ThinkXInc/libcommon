# vector_database.py
from pydantic import BaseModel
from typing import Dict, List, Union, Optional
from uuid import uuid4
from datetime import datetime
import torch

from pydantic import ValidationError
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import ApiException, UnexpectedResponse
from qdrant_client.models import Distance, PointStruct, VectorParams, FieldCondition, Filter, MatchValue, MatchAny

from libcommon.vector_database.sentence_encoder import SentenceEncoder

# Logger
from libcommon.logger import Logger
logger = Logger('VectorDatabase')
logger_ = Logger('VectorDatabase_', simple=True)
logLevel = logger.DEBUG
logger.setLevel(logLevel)
logger_.setLevel(logLevel)
from libcommon.color import *

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
    vector: Optional[List[float]]
    payload: Dict


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
        if exists:
            logger.debug(f'Collection {collection_name} exist in the database')
        else:
            logger.debug(f'[WARNING] Collection {collection_name} does not exist in the database')
        return exists

    def chat_history_collection_name(self, user_id):
        return f'{user_id}_chats'

    def documents_collection_name(self, user_id):
        return f'{user_id}_documents'

    def create_collection(
            self,
            collection_name: str,
            collection_config: Dict = None,
            should_reset_if_already_exist: bool = False
    ) -> None:
        """Creates the collection in the Qdrant database.

        Args:
            collection_name (str): Name of the Qdrant collection to which to connect.
            collection_config (dict): Dictionary specifying collection configuration, including the vector
                configuration. For more information, refer to https://qdrant.tech/documentation/concepts/collections/
                for a detailed explanation of options.
            should_reset_if_already_exist (bool, optional): Whether to delete and re-create the collection if it already exists.
                (Default = False)
        """
        if not should_reset_if_already_exist:
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
        if should_reset_if_already_exist:
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
            text: str,
            metadata: Optional[dict] = None,
            id: Optional[str] = None
        ) -> Document:
        """Inserts or updates an item to the Qdrant store.

        Args:
            text (str): String to put to the Qdrant collection.
            collection_name (str): Name of the Qdrant collection to which to connect.
            metadata (Optional[dict]): Additional metadata for the payload.
            id (Optional[str]): must be UUID. uuid4().hex (32-character hexadecimal) is used if not set.

        Returns:
            Document: Document instance with id, text, keywords, and vector.
        """

        vector = self.encoder(text).squeeze().tolist()

        # Creating the payload
        payload = {
            "text": text,
            "updated": datetime.now().isoformat()  # Add "updated" timestamp to the payload
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
        return Document(id=uuid, text=text, vector=vector, payload=payload)

    def filter_condition(self, find_key: str, must_match_any: bool, metadata: dict) -> List[FieldCondition]:
        """Generates filter conditions for searching in the Qdrant store.

        Args:
            find_key (str): Key by which to search a document.
            must_match_any (bool): Whether to match any keyword or all keywords.
            metadata (dict): Metadata to match against.

        Returns:
            List[FieldCondition]: A list of field conditions for searching.
        """
        filter_conditions = []

        # Handling for keywords
        if find_key == "keywords" and "keywords" in metadata:
            keywords = metadata.pop("keywords", [])
            if must_match_any:
                match_condition = MatchAny(any=keywords)
                filter_conditions.append(FieldCondition(key="keywords", match=match_condition))
            else:
                keyword_conditions = [FieldCondition(key="keywords", match=MatchValue(value=keyword)) for keyword in keywords]
                filter_conditions.extend(keyword_conditions)

        # Handling for other metadata
        logger.debug(f'filter condition: metadata={metadata} find_key={find_key}')
        if find_key in metadata:
            condition = FieldCondition(key=find_key, match=MatchValue(value=metadata[find_key]))
            logger.debug(f'append to filter condition {condition}')
            filter_conditions.append(condition)
        if find_key not in metadata and find_key:
            logger.warning(yellow(f'[WARNING] find_key is set as {find_key} but filter is not created. this doesnt happen.'))

        logger.debug(f'filter conditions generated => {filter_conditions}')
        return filter_conditions

    def search(
            self,
            text: str,
            collection_name: str,
            find_key: Optional[str] = None,  # Added find_key argument
            metadata: Optional[dict] = {},
            num_results: int = 3,
            must_match_any: bool = True
    ) -> List[Document]:
        """
        Search for documents in a collection based on a text, optional keywords, and optional metadata.

        Args:
            text (str): String to search in the Qdrant collection.
            collection_name (str): Name of the Qdrant collection to search.
            find_key (str, optional): Key by which to search a document. If None, only vector search is conducted.
                If set to 'keywords', search will be filtered based on the `keywords` list. If set to a key in `metadata`,
                the filter will apply only to the value of that key.
            keywords (List[str], optional): Keywords related to the text.
            metadata (dict, optional): Additional metadata for the payload.
            num_results (int, optional): Number of results to return.
            must_match_any (bool, optional): Whether to match any keyword or all keywords.

        Returns:
            List[Document]: List of matching documents.
        """
        try:
            logger.debug(f"Starting encoding for text: {text[:30]}...")  # Log the start of an operation
            embedding = self.encoder(text).squeeze()
            logger.debug(f"Generated embedding of size {embedding.size()} for text.")  # Confirm the size of the output

            if embedding.size(0) == 0:
                raise ValueError("Empty embedding generated, check input text and model behavior.")

            embedding_list = embedding.tolist()
            logger.debug(f"Embedding converted to list with length {len(embedding_list)}.")  # Check final list size

            # Further operations...
        except Exception as e:
            logger.error(f"Failed during search operation: {e}")
            raise

        logger.debug(green(f'Text: "{text}" converted to embedding with size {len(embedding)}.'))

        if logger.getEffectiveLevel() == logger.DEBUG:
            try:
                total_docs = self.count(collection_name)
                logger.debug(yellow(f'Total documents in collection "{collection_name}": {total_docs}'))
            except ApiException as e:
                logger.error(red(f'Error fetching document count from collection "{collection_name}": {e}'))
                raise

        query = {
            "collection_name": collection_name,
            "query_vector": embedding,
            "limit": num_results
        }
        if 'query_vector' in query and isinstance(query['query_vector'], list):
            query_for_logging = query.copy()
            query_for_logging['query_vector'] = f"{query['query_vector'][:5]}.."
            logger.debug(f'trying to run search in vector db by query {query_for_logging}..')
        elif 'query_vector' in query and isinstance(query['query_vector'], torch.Tensor):
            query_for_logging = query.copy()
            query_for_logging['query_vector'] = f"{query['query_vector'].tolist()[:5]}.."
            logger.debug(f'trying to run search in vector db by query {query_for_logging}..')
        else:
            logger.debug(f'trying to run search in vector db by query {query}..')

        if not isinstance(metadata, dict):
            raise TypeError(f'metadata must be type of dict but {type(metadata)}')

        filter_conditions = self.filter_condition(find_key, must_match_any, metadata)
    
        if filter_conditions:
            query["query_filter"] = Filter(must=filter_conditions) if must_match_any else Filter(should=filter_conditions)

        try:
            results = self.client.search(**query, with_vectors=False, with_payload=True)
            documents = [Document(
                id=r.id,
                payload=r.payload,
                vector=r.vector if r.vector else []  # Use an empty list if vector is None
            ) for r in results]

            logger.info(cyan(f'{len(documents)} documents found by query: {text}'))
            return documents

        except UnexpectedResponse as e:
            if e.status_code == 404:
                logger.info(yellow("No documents found matching the criteria."))
                return []
            else:
                logger.error(red(f'Search error with status {e.status_code}: {e.reason_phrase}'))
                raise  # Re-raise the exception for other unexpected statuses

        except ApiException as e:
            logger.error(red(f'Search error: {e}'))
            raise  # Re-raise other API exceptions

        logger.debug(f'Search results ')
        logger.debug(f'query {query}')
        logger.debug(bold(f'\n {results}'))

        documents = [Document(
            id=r.id,
            payload=r.payload,
            vector=r.vector if r.vector else []  # Use an empty list if vector is None
        ) for r in results]

        logger.info(cyan(f'{len(documents)} documents found in collection {collection_name} by query:{text}'))

        return documents

    def count(self, collection_name: str) -> int:
        """
        Count the total number of documents in a specified collection.

        Args:
            collection_name (str): The name of the collection to count documents in.

        Returns:
            int: The total number of documents in the collection.
        """
        try:
            count_result = self.client.count(collection_name=collection_name, exact=True)
            logger.debug(f'count (all) result for collection {collection_name} -> {count_result}')
            return count_result.count
        except ApiException as e:
            logger.error(red(f'Error fetching document count from collection "{collection_name}": {e}'))
            raise

    def find_one(
            self,
            collection_name: str,
            find_key: str,  # Added find_key as required argument
            metadata: dict = None) -> Optional[Document]:
        """
        Find a document in the collection that matches the provided find_key, metadata, or keywords.

        Args:
            collection_name (str): Name of the Qdrant collection to search.
            find_key (str): Key by which to search a document.
            metadata (dict, optional): Metadata to match against. 

        Returns:
            Document: Matching document or None if not found.
        """

        results = self.search(
            text="",
            collection_name=collection_name, 
            find_key=find_key, 
            metadata=metadata,
            num_results=1, 
            must_match_any=True)

        return results[0] if results else None


    def find_one_and_update(
            self, 
            collection_name: str, 
            find_key: str,  # Added find_key as required argument
            find_value,
            text: str, 
            metadata: Optional[dict] = None) -> Union[bool, Document]:
        """
        Updates a stored entity by its unique id.

        Args:
            collection_name (str): Name of the Qdrant collection to update.
            find_key (str): Key by which to search a document.
            find_value (str): Value associated with the find_key for searching.
            text (str): The new sentence value to update.
            metadata (Optional[dict]): Optional updated metadata related to the document.

        Returns:
            Union[bool, Document]: The updated document if successful, or False otherwise.
        """
        vector = self.encoder(text).squeeze().tolist()

        # Locate the document first
        document = self.find_one(collection_name, find_key, {find_key: find_value})

        # If the document isn't found, return False
        if not document:
            logger.error(red(f'Failed to find document with find_key {find_key} and find_value {find_value}.'))
            return False

        # Extract the ID of the found document
        id = document.id

        # Create the payload dictionary directly
        payload = {
            "text": text,
            "updated": datetime.now().isoformat()  # Add "updated" timestamp to the payload
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
            logger.info(bold(f'Successfully updated point id:{id} in collection {collection_name}:'))
            return Document(
                id=id,
                payload=payload,
                vector=vector
            )

        except (ValueError, ValidationError, ConnectionError, ApiException, UnexpectedResponse) as e:
            logger.error(red(f'Failed to update point {id}:\n{str(e)}'))
            return False

    def delete(self, collection_name: str, find_key: str, find_value: str) -> bool:
        """
        Deletes a document from the collection based on a find_key and find_value.

        Args:
            collection_name (str): Name of the Qdrant collection to delete from.
            find_key (str): Key by which to find a document.
            find_value (str): Value of the key to match against.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        
        # First, find the document using the find_one method
        document = self.find_one(collection_name, find_key, {find_key: find_value})

        # If the document exists, proceed to delete
        if document:
            try:
                self.client.delete(collection_name=collection_name, points_selector=[document.id]) 
                logger.info(f'Successfully deleted document with id {document.id} from collection {collection_name}')
                return True
            except (ConnectionError, ApiException, UnexpectedResponse) as e:
                logger.error(red(f'Failed to delete document with id {document.id}:\n{str(e)}'))
                return False
        else:
            logger.warning(yellow(f'Document with {find_key}={find_value} not found in collection {collection_name}'))
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
            logger.warning(yellow(f'Collection {collection_name} does not exist, skipping deletion...'))

    def list_all_in_collection(self, collection_name: str, limit=1000000, with_payload=False, with_vectors=False) -> List[str]:
        """List all document IDs from a specific collection."""
        try:
            # Use a neutral query vector. Depending on the vector dimensions and norm, adjust accordingly.
            neutral_vector = [0.0] * self.embedding_dim  # Assuming vectors are normalized and same dimension
            logger.debug(f"Using neutral vector for listing IDs: {neutral_vector[:10]}..")
            
            # Perform the search
            results = self.client.search(
                collection_name=collection_name,
                query_vector=neutral_vector,
                limit=limit,  # Set a high limit; adjust based on your dataset size and expected results
                with_payload=with_payload,  # Do not retrieve any payload data
                with_vectors=with_vectors # Do not retrieve vector data
            )
            logger.debug(f"Search completed. Number of results: {len(results)}")
            logger.debug(f"Documents retrieved: {results}")
            return results
        except Exception as e:
            logger.error(red(f"Failed to list documents: {e}"))
            raise