from elasticsearch import Elasticsearch
from app.core.config import config
import traceback
import json

class ElasticsearchClient:
    """Elasticsearch client for managing documents and hybrid search"""
    
    def __init__(self):
        # Initialize Elasticsearch client with explicit API version for 8.x compatibility
        try:
            self.client = Elasticsearch(
                [config.ELASTICSEARCH_HOST],
                api_version="8.10"  # Specify compatible ES version
            )
        except Exception:
            # Fallback: try without api_version for older client versions
            self.client = Elasticsearch([config.ELASTICSEARCH_HOST])
        self.index_name = config.ELASTICSEARCH_INDEX
        self._create_index_if_not_exists()
    
    def _check_connection(self):
        """Verify Elasticsearch is reachable"""
        try:
            info = self.client.info()
            print(f"Connected to Elasticsearch: {info.get('version', {}).get('number', 'unknown')}")
            return True
        except Exception as e:
            print(f"Failed to connect to Elasticsearch at {config.ELASTICSEARCH_HOST}:")
            print(traceback.format_exc())
            return False
    
    def _create_index_if_not_exists(self):
        """Create index with proper mapping for hybrid search"""
        # First verify connection
        if not self._check_connection():
            print("WARNING: Elasticsearch connection failed. Index creation skipped. Will retry on next request.")
            return
        # Check index existence with defensive error handling to surface ES errors
        try:
            exists = self.client.indices.exists(index=self.index_name)
        except Exception as e:
            print("Elasticsearch indices.exists() raised an exception:")
            print(traceback.format_exc())
            # Try to fetch cluster info for diagnostics
            try:
                info = self.client.info()
                print("Elasticsearch cluster info:", json.dumps(info, indent=2, default=str))
            except Exception:
                print("Failed to get Elasticsearch info:")
                print(traceback.format_exc())
            # Assume index does not exist so we can attempt to create it
            exists = False

        if not exists:
            # Try to determine embedding dimensionality from the embedding model
            try:
                from app.services.embedding_service import embedding_service
                embedding_dim = getattr(embedding_service.model, "get_sentence_embedding_dimension", lambda: None)()
                if embedding_dim is None:
                    # Fallback: try attribute 'embedding_dimension' or default
                    embedding_dim = getattr(embedding_service.model, "embedding_dimension", None) or 1024
            except Exception:
                embedding_dim = 1024

            mapping = {
                "mappings": {
                    "properties": {
                        "text": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "embedding": {
                            "type": "dense_vector",
                            "dims": int(embedding_dim),
                            "index": True,
                            "similarity": "cosine"
                        },
                        "document_id": {
                            "type": "keyword"
                        },
                        "document_name": {
                            "type": "keyword"
                        },
                        "chunk_index": {
                            "type": "integer"
                        },
                        "metadata": {
                            "type": "object"
                        }
                    }
                }
            }
            try:
                self.client.indices.create(index=self.index_name, body=mapping)
                print(f"Index '{self.index_name}' created successfully")
            except Exception:
                print("Elasticsearch indices.create() raised an exception:")
                print(traceback.format_exc())
    
    def index_document(self, doc_id: str, text: str, embedding: list, document_name: str, chunk_index: int, metadata: dict = None):
        """Index a document chunk with embedding"""
        body = {
            "text": text,
            "embedding": embedding,
            "document_id": doc_id,
            "document_name": document_name,
            "chunk_index": chunk_index,
            "metadata": metadata or {}
        }
        self.client.index(index=self.index_name, id=f"{doc_id}_{chunk_index}", body=body)
    
    def hybrid_search(self, query_text: str, query_embedding: list, k: int = 5):
        """Perform hybrid search combining BM25 and vector search"""
        search_body = {
            "size": k,
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query_text,
                                "fields": ["text"],
                                "fuzziness": "AUTO"
                            }
                        }
                    ]
                }
            }
        }
        
        # Add vector search part
        search_body["knn"] = {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": k,
            "num_candidates": 100
        }
        
        results = self.client.search(index=self.index_name, body=search_body)
        return results["hits"]["hits"]
    
    def search_by_vector(self, embedding: list, k: int = 5):
        """Pure vector search"""
        results = self.client.search(
            index=self.index_name,
            body={
                "size": k,
                "knn": {
                    "field": "embedding",
                    "query_vector": embedding,
                    "k": k,
                    "num_candidates": 100
                }
            }
        )
        return results["hits"]["hits"]
    
    def delete_document(self, document_id: str):
        """Delete all chunks of a document"""
        self.client.delete_by_query(
            index=self.index_name,
            body={"query": {"match": {"document_id": document_id}}}
        )

# Lazy client proxy
_es_client_instance = None

class LazyElasticsearchClientProxy:
    """Lazy proxy that creates ElasticsearchClient only when first accessed"""
    
    def __init__(self):
        self._client = None
    
    def _get_client(self):
        global _es_client_instance
        if _es_client_instance is None:
            _es_client_instance = ElasticsearchClient()
        return _es_client_instance
    
    def __getattr__(self, name):
        return getattr(self._get_client(), name)

es_client = LazyElasticsearchClientProxy()
