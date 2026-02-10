from sentence_transformers import SentenceTransformer
from app.core.config import config
import numpy as np
import traceback


class EmbeddingService:
    """Service for generating embeddings with robust loading and fallbacks."""

    def __init__(self):
        self.model = None
        self.dim = None
        requested = config.EMBEDDING_MODEL
        print(f"Loading embedding model: {requested}")
        try:
            self.model = SentenceTransformer(requested)
            print(f"Embedding model '{requested}' loaded successfully")
        except Exception:
            print(f"Failed to load embedding model '{requested}':")
            print(traceback.format_exc())
            # Fallback to a lightweight, widely-available model
            fallback = "all-MiniLM-L6-v2"
            try:
                print(f"Falling back to '{fallback}'")
                self.model = SentenceTransformer(fallback)
                print(f"Fallback model '{fallback}' loaded successfully")
            except Exception:
                print("Failed to load fallback embedding model:")
                print(traceback.format_exc())
                raise RuntimeError("No usable embedding model available. Check network or model name.")

        # Try to determine embedding dimensionality
        try:
            self.dim = getattr(self.model, "get_sentence_embedding_dimension", lambda: None)()
            if self.dim is None:
                # Run a quick encode to infer dimension
                sample = self.model.encode(["test"], convert_to_tensor=False)
                if hasattr(sample, "shape"):
                    self.dim = int(sample.shape[-1])
                else:
                    self.dim = len(sample[0])
        except Exception:
            print("Could not determine embedding dimension; defaulting to 1024")
            self.dim = 1024

    def embed_text(self, text: str) -> list:
        """Generate embedding for a single text"""
        if not text:
            return [0.0] * self.dim
        try:
            emb = self.model.encode(text, convert_to_tensor=False)
            # emb may be numpy array
            if hasattr(emb, "tolist"):
                return emb.tolist()
            return list(emb)
        except Exception:
            print("Error during embed_text:")
            print(traceback.format_exc())
            raise

    def embed_batch(self, texts: list) -> list:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            # embeddings may be numpy array or list of arrays
            result = []
            for emb in embeddings:
                if hasattr(emb, "tolist"):
                    result.append(emb.tolist())
                else:
                    result.append(list(emb))
            return result
        except Exception:
            print("Error during embed_batch:")
            print(traceback.format_exc())
            raise

    def embed_query(self, query: str) -> list:
        """Generate embedding for a query"""
        return self.embed_text(query)

    def similarity_search(self, query_embedding: list, embeddings_list: list, k: int = 5) -> list:
        """Find k most similar embeddings"""
        query_emb = np.array(query_embedding)
        similarities = []

        for i, emb in enumerate(embeddings_list):
            emb_array = np.array(emb)
            # Cosine similarity
            sim = np.dot(query_emb, emb_array) / (np.linalg.norm(query_emb) * np.linalg.norm(emb_array) + 1e-10)
            similarities.append((i, sim))

        # Sort by similarity and return top k indices
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [idx for idx, _ in similarities[:k]]


# Global embedding service instance
embedding_service = EmbeddingService()
