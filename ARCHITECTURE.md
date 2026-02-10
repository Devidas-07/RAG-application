# 🏗️ System Architecture & Design

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER/CLIENT                                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                    HTTP/REST API (FastAPI)
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
    ┌────────────┐    ┌──────────────┐    ┌────────────┐
    │   INGEST   │    │   ASK (RAG)  │    │  RETRIEVE  │
    │     API    │    │   PIPELINE   │    │   CONTEXT  │
    └──────┬─────┘    └──────┬───────┘    └─────┬──────┘
           │                 │                   │
           │                 └───────┬───────────┘
           │                         │
        ┌──▼─────────────────────────▼──────────┐
        │  PROCESSING LAYER                      │
        │                                        │
        │  1. Document Chunker                   │
        │     • Split PDF/text into chunks      │
        │     • Add overlap for context         │
        │                                        │
        │  2. Embedding Service (BGE-M3)        │
        │     • Convert text → vectors          │
        │     • 1024-dim embeddings             │
        │                                        │
        │  3. RAG Pipeline                       │
        │     • Orchestrate flow                │
        │     • Combine context + question       │
        │                                        │
        │  4. LLM Service (Ollama + Gemma)      │
        │     • Generate responses              │
        │     • Context-aware answers           │
        └──┬──────────────────────────────┬──────┘
           │                              │
        ┌──▼──────────────┐    ┌──────────▼──────┐
        │ STORAGE LAYER   │    │  SEARCH LAYER   │
        │                 │    │                 │
        │  MinIO          │    │ Elasticsearch   │
        │  ────────       │    │ ───────────────│
        │  • Store PDFs   │    │ • Index chunks │
        │  • Store docs   │    │ • Hybrid search│
        │  • Object store │    │ • Vector DB    │
        │  • Versioning   │    │ • BM25 + KNN   │
        └─────────────────┘    └────────────────┘
```

## Data Flow: Document Ingestion

```
User uploads PDF/Text
        │
        ▼
   ┌─────────────────────┐
   │ Receive Upload File │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │ Extract Text        │
   │ (from PDF or read   │
   │  text file)         │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────────────────────┐
   │ Document Chunker                    │
   │ • Split by words                    │
   │ • Size: 500 words/chunk             │
   │ • Overlap: 50 words                 │
   └──────────┬────────────────────────┐
              │ Chunks                   │
              ▼                          │
   ┌─────────────────────────────────────┐
   │ Embedding Service (BGE-M3)          │ (Process in batch)
   │ Convert each chunk to 1024-dim vec  │
   └──────────┬────────────────────────┐
              │ (Chunks + Embeddings)    │
              ▼                          │
        ┌─────────────┐          ┌──────────┐
        │   MinIO     │ ◄────────┤          │
        │ Store orig  │          │ Store in │
        │   PDF file  │          │ ES Index │
        └─────────────┘          └──────────┘
                                     │
                                 ElasticSearch
                                 • Document
                                 • Embedding
                                 • Metadata
```

## Data Flow: Question Answering (RAG)

```
User asks: "What is Python?"
        │
        ▼
   ┌──────────────────────┐
   │ Receive Question     │
   └──────────┬───────────┘
              │
              ▼
   ┌──────────────────────────────────┐
   │ Embedding Service                │
   │ Convert question to 1024-dim vec │
   └──────────┬───────────────────────┘
              │ Query Vector
              ▼
   ┌──────────────────────────────────────────┐
   │ Elasticsearch Hybrid Search              │
   │                                          │
   │ 1. BM25 Search (keyword match)           │
   │    • Find chunks with "Python"           │
   │                                          │
   │ 2. Vector Search (semantic similarity)   │
   │    • Find similar embeddings (K=5)       │
   │                                          │
   │ 3. Combine and rank results              │
   └──────────┬───────────────────────────────┘
              │ Top 5 Matching Chunks
              ▼
   ┌──────────────────────────────────────────┐
   │ Build RAG Prompt                         │
   │                                          │
   │ "Based on context, answer question:     │
   │  [1] Python is a programming lang...    │
   │  [2] Python is used for data analysis..│
   │  [3] Python has extensive libraries...  │
   │                                          │
   │  Question: What is Python?"             │
   └──────────┬───────────────────────────────┘
              │ Prompt
              ▼
   ┌──────────────────────────────────────────┐
   │ Ollama + Gemma 3:4b                      │
   │ Generate response based on context      │
   └──────────┬───────────────────────────────┘
              │ Generated Answer
              ▼
   ┌──────────────────────────────────────────┐
   │ Return Response + Context                │
   │                                          │
   │ {                                        │
   │   "question": "What is Python?",        │
   │   "answer": "Python is a high-level...  │
   │   "context_used": [                     │
   │     {text: "...", document: "...", ...}│
   │   ]                                      │
   │ }                                        │
   └──────────────────────────────────────────┘
```

## Component Details

### 1. FastAPI Application (`main.py`)
- **Role**: HTTP API server
- **Endpoints**:
  - `POST /api/v1/ingest` - Upload documents
  - `POST /api/v1/ask` - Ask questions
  - `GET /api/v1/health` - Health check

### 2. Document Chunker (`app/services/document_chunker.py`)
- **Purpose**: Split documents into manageable pieces
- **Process**:
  - Extracts text from PDF using PyPDF2
  - Splits by words with overlap
  - Creates overlapping 500-word chunks
  - Preserves context between chunks

### 3. Embedding Service (`app/services/embedding_service.py`)
- **Model**: BGE-M3 (1024-dimensional)
- **Purpose**: Convert text to vectors
- **Features**:
  - Multilingual support
  - Batch processing
  - Efficient similarity calculations

### 4. Elasticsearch Client (`app/core/elasticsearch_client.py`)
- **Capabilities**:
  - BM25 full-text search
  - Dense vector similarity search
  - Hybrid search (BM25 + Vector)
  - Automatic index creation
  - Document management

### 5. MinIO Client (`app/core/minio_client.py`)
- **Storage**: Object storage for original documents
- **Features**:
  - Auto bucket creation
  - File upload/download
  - Organize by document_id

### 6. Ollama Service (`app/services/ollama_service.py`)
- **LLM**: Gemma 3:4b
- **Function**: Generate responses
- **Local**: Runs on user's machine via Ollama
- **No API keys**: Fully local processing

### 7. RAG Pipeline (`app/services/rag_pipeline.py`)
- **Orchestrates**:
  1. Document ingestion workflow
  2. Query processing & retrieval
  3. Context injection
  4. LLM generation
- **Handles** end-to-end flow

## Why This Architecture?

### Separation of Concerns
- Each service has single responsibility
- Easy to test and modify independently
- Clear interfaces between components

### Scalability
- FastAPI is async and fast
- Can handle multiple concurrent requests
- Elasticsearch scales horizontally
- MinIO scales for large documents

### Privacy
- All processing local (except maybe embeddings initial download)
- No API keys needed
- No cloud dependency

### Flexibility
- Easy to swap components:
  - Different embedding model
  - Different LLM
  - Different storage backend
  - Different search engine

### Learning-Friendly
- Clear pipeline stages
- Modular components
- Easy to debug each step
- Good for understanding RAG

## Key Design Decisions

### 1. Hybrid Search (Not Pure Vector Search)
**Why**: 
- Vector search alone misses exact keywords
- BM25 alone misses semantic meaning
- Hybrid combines both strengths

### 2. Document Chunking with Overlap
**Why**:
- Preserves context between chunks
- Prevents information loss at boundaries
- Better semantic understanding

### 3. BGE-M3 Embedding Model
**Why**:
- Multilingual (good for diverse documents)
- High quality embeddings
- Good balance of performance/size
- 1024-dim is good for quality

### 4. Local LLM (Ollama)
**Why**:
- No internet required
- No API costs
- Privacy-friendly
- Fast responses
- Good for learning

### 5. Elasticsearch for Search
**Why**:
- Supports both keyword and vector search
- Production-ready
- Good performance
- Rich query DSL
- Easy to understand

## Performance Characteristics

### Document Ingestion
- Time: ~1s per chunk (includes embedding)
- Memory: ~500MB for large PDFs
- Can process in parallel with threading

### Question Answering
- Search time: ~200-500ms
- Embedding time: ~100-200ms
- LLM generation: ~3-10s (depends on model)
- Total: ~5-15s per question

### Scaling Recommendations
- **Documents**: 1000+ with Elasticsearch
- **Chunks**: 100,000+ feasible
- **Concurrent Users**: 5-10 with single Ollama instance
- **Memory**: 4GB minimum recommended

## Technology Stack Justification

| Component | Choice | Why |
|-----------|--------|-----|
| Web Framework | FastAPI | Fast, modern, async support |
| Vector DB | Elasticsearch | Hybrid search, production-ready |
| Embeddings | BGE-M3 | Quality, multilingual, efficient |
| LLM | Ollama + Gemma | Local, private, easy setup |
| Storage | MinIO | S3-compatible, self-hosted |
| Language | Python | Rich ML ecosystem, rapid development |
| Containerization | Docker | Reproducible environment |

## Future Enhancement Opportunities

1. **Caching Layer**: Redis for frequently asked questions
2. **Reranking**: Use cross-encoder for better relevance
3. **User Feedback**: Track answer quality and improve
4. **Multi-modal**: Support images and tables
5. **Streaming**: Real-time LLM response streaming
6. **Metrics**: Track usage patterns and performance
7. **Load Balancing**: Scale to multiple instances
8. **Fine-tuning**: Train on domain-specific data

---

**This architecture is designed for learning and production readiness! 🚀**
