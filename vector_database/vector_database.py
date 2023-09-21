# llm/vector_database.py
#
from pydantic import BaseModel
from typing import Dict, List, Union, Optional
from uuid import uuid4

from pydantic import ValidationError
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import ApiException, UnexpectedResponse
from qdrant_client.models import Distance, PointStruct, VectorParams, FieldCondition

from libcommon.vector_database.sentence_encoder import SentenceEncoder

from libcommon.logger import Logger
logger = Logger('VectorDatabase')
logger.setLevel(logger.INFO)

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


class QueryFilter(BaseModel):
    """
    query_filter = QueryFilter(keywords=["Mountain", "Backpack"])

    # save
    client.upsert(
        points=[
            PointStruct(
                ...
                payload=query_filter.payload()
            )
        ]
    )

    # search
    client.search(
        ...
        query_filter=query_filter.to_filter(must_much=False)
    )
    """
    keywords: List[str]  # e.g. ['AfterEffects', 'Animation']

    def payload(self) -> dict:
        return {"keywords": self.keywords}

    def to_filter(self, must_match: bool = False) -> 'Filter':
        """
        Converts the QdrantFilterCondition to a Filter object.

        Args:
            must_match (bool): Determines the type of filtering. If True, uses MatchAny. If False, uses MatchValue.
        Returns:
            Qdrant Filter object
        """
        if must_match:
            match_condition = MatchAny(any=self.keywords)
            return Filter(
                must=[FieldCondition(key="keywords", match=match_condition)]
            )
        else:
            should_conditions = [FieldCondition(key="keywords", match=MatchValue(value=category)) for category in self.keywords]
            return Filter(
                should=should_conditions
            )


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
        """Generate id for the inserted point."""
        return uuid4().hex

    def save(
            self,
            sentence: str,
            collection_name: str,
            keywords: Optional[List[str]] = None
        ) -> str:
        """Inserts or updates an item to the Qdrant store.

        Args:
            sentence (str): String to put to the Qdrant collection.
            collection_name (str): Name of the Qdrant collection to which to connect.
            keywords (Optional[List[str]]): Optional keywords related to the sentence.

        Returns:
            uuid (str): UUID of the inserted item.
        """

        vector = self.encoder(sentence).squeeze().tolist()

        payload = {sentence: True}

        if keywords:
            query_filter = QueryFilter(keywords=keywords)
            payload.update(query_filter.payload()) 

        # Create a random UUID (should have extremely minimal collisions)
        uuid = self.uuid()
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
            logger.debug(f'Successfully inserted point {uuid} in collection {collection_name}:')
            logger.debug(f'--------------------')
            logger.debug(f'Payload: {sentence}')
            logger.debug(f'Vector sum: {sum(vector)}')
            logger.debug(f'--------------------')
        # Error handling
        except (ValueError, ValidationError) as e:
            # Catch client-side errors
            logger.error(f'Could not parse point {uuid}:\n{str(e)}')
            raise e
        except (ConnectionError, ApiException, UnexpectedResponse) as e:
            # Catch server-side errors
            logger.error(
                f'Encountered a server error when attempting to upsert point {uuid}:\n{str(e)}')
            raise e
        except Exception as e:
            # Catch all
            logger.error(f'Failed to insert point {uuid}:\n{str(e)}')
            raise e

        return uuid

    def search(
            self,
            sentence: str,
            collection_name: str,
            keywords: List[str] = None,
            num_results: int = 3
    ) -> List[str]:
        """Searches for similar items. Refer to the Qdrant documentation for more information about constructing
        queries: https://qdrant.tech/documentation/concepts/search/.

        Args:
            sentence (str): String for which to query the Qdrant database for similar entries.
            collection_name (str): Name of the Qdrant collection to which to connect.
            keywords (Optional[List[str]]): Optional keywords for filtering.
            num_results (int): Number of results to return from search queries.

        Returns:
            results (List[str]): top n sentences
        """
        embedding = self.encoder(sentence).squeeze().tolist()

        query = {
            "collection_name": collection_name,
            "query_vector": embedding,
            "limit": num_results
        }

        # Use keywords for filtering if provided
        if keywords:
            query_filter = QueryFilter(keywords=keywords)
            query["query_filter"] = query_filter.to_filter(must_match=True)

        results = self.client.search(**query, with_vectors=False, with_payload=True)

        logger.debug(f'Search results \n {results}')

        documents = [list(r.payload.keys())[0] for r in results]

        logger.debug(f'For query {sentence}, got the following search outputs: '
                     f'[{", ".join(documents)}]\n')
        return documents