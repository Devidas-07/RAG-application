import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application Configuration"""
    
    # Elasticsearch
    ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200")
    ELASTICSEARCH_INDEX = os.getenv("ELASTICSEARCH_INDEX", "rag_documents")
    
    # MinIO
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET = os.getenv("MINIO_BUCKET", "documents")
    
    # Ollama
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:4b")
    
    # Embedding Model
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    
    # FastAPI
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))

config = Config()
