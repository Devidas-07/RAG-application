from app.core.elasticsearch_client import es_client
from app.core.minio_client import minio_client
from app.services.document_chunker import DocumentChunker
from app.services.embedding_service import embedding_service
from app.services.ollama_service import ollama_service
import uuid
import io
import traceback

class RAGPipeline:
    """Main RAG (Retrieval Augmented Generation) Pipeline"""
    
    def __init__(self):
        self.chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)
    
    def ingest_document(self, file_bytes: bytes, file_name: str, document_type: str = "pdf") -> dict:
        """
        Ingest a document: chunk it, embed chunks, and store in Elasticsearch
        """
        doc_id = str(uuid.uuid4())
        
        try:
            # 1. Chunk the document
            if document_type == "pdf":
                chunks = self.chunker.chunk_pdf(file_bytes)
            else:
                text = file_bytes.decode('utf-8')
                chunks = self.chunker.chunk_text(text)
            
            # 2. Upload original file to MinIO
            file_stream = io.BytesIO(file_bytes)
            minio_client.client.put_object(
                minio_client.bucket,
                f"{doc_id}/{file_name}",
                file_stream,
                len(file_bytes)
            )
            
            # 3. Embed and index chunks
            chunk_embeddings = embedding_service.embed_batch(chunks)
            
            for idx, (chunk, embedding) in enumerate(zip(chunks, chunk_embeddings)):
                es_client.index_document(
                    doc_id=doc_id,
                    text=chunk,
                    embedding=embedding,
                    document_name=file_name,
                    chunk_index=idx,
                    metadata={"document_type": document_type, "total_chunks": len(chunks)}
                )
            
            return {
                "status": "success",
                "document_id": doc_id,
                "file_name": file_name,
                "chunks_created": len(chunks),
                "message": f"Document ingested successfully with {len(chunks)} chunks"
            }
        
        except Exception as e:
            # Log full traceback for debugging
            tb = traceback.format_exc()
            print("Error during ingest_document:\n", tb)
            return {
                "status": "error",
                "message": f"Error ingesting document: {str(e)}"
            }
    
    def retrieve_context(self, query: str, k: int = 5) -> list:
        """
        Retrieve relevant context chunks for a query
        """
        try:
            # 1. Embed the query
            query_embedding = embedding_service.embed_query(query)
            
            # 2. Search in Elasticsearch (hybrid search)
            search_results = es_client.hybrid_search(query, query_embedding, k=k)
            
            # 3. Format results
            context_chunks = []
            for result in search_results:
                source = result["_source"]
                context_chunks.append({
                    "text": source["text"],
                    "document": source["document_name"],
                    "chunk_index": source["chunk_index"],
                    "score": result.get("_score", 0)
                })
            
            return context_chunks
        
        except Exception as e:
            print(f"Error retrieving context: {str(e)}")
            return []
    
    def answer_question(self, question: str, k: int = 5, temperature: float = 0.7) -> dict:
        """
        Complete RAG pipeline: retrieve context and generate answer
        """
        try:
            # 1. Retrieve context
            context_chunks = self.retrieve_context(question, k=k)
            
            if not context_chunks:
                return {
                    "question": question,
                    "answer": "I couldn't find relevant information in the documents to answer your question.",
                    "context_used": [],
                    "error": "No relevant context found"
                }
            
            # 2. Build prompt with context
            context_text = "\n\n".join([f"[{i+1}] {chunk['text']}" for i, chunk in enumerate(context_chunks)])
            
            prompt = f"""Based on the following context, please answer the question accurately and concisely.

CONTEXT:
{context_text}

QUESTION: {question}

ANSWER:"""
            
            # 3. Generate answer using Ollama
            answer = ollama_service.generate(prompt, temperature=temperature, max_tokens=500)
            
            return {
                "question": question,
                "answer": answer,
                "context_used": context_chunks,
                "status": "success"
            }
        
        except Exception as e:
            return {
                "question": question,
                "answer": f"Error generating answer: {str(e)}",
                "context_used": [],
                "status": "error",
                "error": str(e)
            }
    
    def answer_question_stream(self, question: str, k: int = 5, temperature: float = 0.7):
        """
        RAG pipeline with streaming: retrieve context then stream tokens.
        First yields a JSON metadata line with context, then streams answer tokens.
        """
        import json
        context_chunks = self.retrieve_context(question, k=k)

        if not context_chunks:
            yield json.dumps({"type": "context", "context_used": []}) + "\n"
            yield json.dumps({"type": "token", "token": "I couldn't find relevant information in the documents to answer your question."}) + "\n"
            return

        yield json.dumps({"type": "context", "context_used": context_chunks}) + "\n"

        context_text = "\n\n".join([f"[{i+1}] {chunk['text']}" for i, chunk in enumerate(context_chunks)])
        prompt = f"""Based on the following context, please answer the question accurately and concisely.

CONTEXT:
{context_text}

QUESTION: {question}

ANSWER:"""

        for token in ollama_service.generate_stream(prompt, temperature=temperature):
            yield json.dumps({"type": "token", "token": token}) + "\n"

    def delete_document(self, document_id: str) -> dict:
        """Delete a document and its chunks"""
        try:
            es_client.delete_document(document_id)
            # MinIO cleanup would be done here if needed
            return {
                "status": "success",
                "message": f"Document {document_id} deleted successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error deleting document: {str(e)}"
            }

# Global RAG pipeline instance
rag_pipeline = RAGPipeline()
