# RAG-Based Q&A System

A complete learning project implementing Retrieval Augmented Generation (RAG) for question-answering using modern technologies.

## 🎯 Project Overview

This system demonstrates a full RAG pipeline:
1. **Ingest**: Upload PDF/text documents
2. **Chunk**: Split documents into manageable pieces
3. **Embed**: Convert chunks to vectors using BGE-M3
4. **Store**: Index vectors and text in Elasticsearch with hybrid search
5. **Retrieve**: Find relevant context for user queries
6. **Generate**: Produce answers using Gemma 3:4b LLM via Ollama

## 🛠 Tech Stack

- **FastAPI**: Modern, fast web framework
- **Ollama + Gemma 3:4b**: Local LLM for generation
- **Elasticsearch**: Vector + hybrid search capabilities
- **MinIO**: Object storage for documents
- **BGE-M3**: Multilingual embedding model
- **Docker**: Containerization and orchestration
- **Python 3.10**: Programming language

## 📋 Prerequisites

- Docker Desktop (running)
- Ollama (installed and running locally)
- 8GB+ RAM recommended
- Port availability: 8000 (FastAPI), 9200 (Elasticsearch), 9000 (MinIO), 11434 (Ollama)

### Verify Prerequisites

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Check Docker Desktop is running
docker --version
```

## 🚀 Quick Start

### 1. Clone/Navigate to Project

```bash
cd rag-qa-system
```

### 2. Set Up Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env if needed (defaults should work for local setup)
```

### 3. Prepare Ollama

```bash
# Pull Gemma 3:4b model (if not already pulled)
ollama pull gemma:4b

# Verify it's running
ollama list  # Should show gemma:4b
```

### 4. Start Elasticsearch and MinIO

**Option A: Using Docker Compose (Recommended)**

```bash
# Start Elasticsearch and MinIO containers
docker-compose up -d elasticsearch minio

# Verify services are running
docker-compose ps
```

**Option B: Manual Services**

If you have these services running locally on different ports, update `.env` accordingly.

### 5. Install Python Dependencies

```bash
# Create virtual environment (optional but recommended)
python -m venv venv
source venv/Scripts/activate  # On Windows
# or
source venv/bin/activate  # On Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 6. Start FastAPI Application

```bash
# Run the FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 7. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

## 📚 API Endpoints

### Health Check

```bash
GET /api/v1/health

# Response
{
  "status": "healthy",
  "ollama_connected": true,
  "message": "RAG system is running"
}
```

### Ingest Document

```bash
POST /api/v1/ingest

# Request (form-data)
- file: [PDF or text file]

# Response
{
  "status": "success",
  "document_id": "uuid-here",
  "file_name": "example.pdf",
  "chunks_created": 10,
  "message": "Document ingested successfully with 10 chunks"
}
```

### Ask Question (RAG Pipeline)

```bash
POST /api/v1/ask

# Request (JSON)
{
  "question": "What is Python used for?",
  "k": 5,
  "temperature": 0.7
}

# Response
{
  "question": "What is Python used for?",
  "answer": "Python is a versatile programming language used for...",
  "context_used": [
    {
      "text": "Python chunk text here...",
      "document": "python_guide.txt",
      "chunk_index": 2,
      "score": 0.85
    }
  ],
  "status": "success"
}
```

### Delete Document

```bash
DELETE /api/v1/documents/{document_id}

# Response
{
  "status": "success",
  "message": "Document {document_id} deleted successfully"
}
```

## 📖 Usage Examples

### Using curl

```bash
# Ingest a document
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -F "file=@sample_docs/python_guide.txt"

# Ask a question
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the key features of Python?",
    "k": 5,
    "temperature": 0.7
  }'
```

### Using Python

```python
import requests

# Ingest document
with open("sample_docs/python_guide.txt", "rb") as f:
    files = {"file": f}
    response = requests.post("http://localhost:8000/api/v1/ingest", files=files)
    doc_id = response.json()["document_id"]

# Ask question
response = requests.post(
    "http://localhost:8000/api/v1/ask",
    json={
        "question": "What is Python used for?",
        "k": 5,
        "temperature": 0.7
    }
)
print(response.json()["answer"])
```

### Using FastAPI Docs

1. Open http://localhost:8000/docs
2. Try the endpoints directly from the interactive UI
3. Upload sample documents from `sample_docs/` folder

## 🔄 Pipeline Workflow

```
User Question
    ↓
Embed Question (BGE-M3)
    ↓
Search in Elasticsearch (Hybrid Search)
    ↓
Retrieve Context Chunks
    ↓
Build Prompt with Context
    ↓
Send to Ollama (Gemma 3:4b)
    ↓
Generate Answer
    ↓
Return Response with Context
```

## 📁 Project Structure

```
rag-qa-system/
├── app/
│   ├── core/
│   │   ├── config.py              # Configuration management
│   │   ├── elasticsearch_client.py # Elasticsearch integration
│   │   └── minio_client.py        # MinIO integration
│   ├── services/
│   │   ├── document_chunker.py    # Document splitting
│   │   ├── embedding_service.py   # BGE-M3 embeddings
│   │   ├── ollama_service.py      # Ollama LLM integration
│   │   └── rag_pipeline.py        # Main RAG logic
│   ├── routes/
│   │   └── rag_routes.py          # API endpoints
│   └── __init__.py
├── sample_docs/                    # Sample documents
├── data/                           # Local data storage
├── main.py                         # FastAPI application entry
├── requirements.txt                # Python dependencies
├── docker-compose.yml              # Docker services
├── Dockerfile                      # FastAPI container
├── .env.example                    # Example environment variables
└── README.md                       # This file
```

## 🔧 Configuration

Edit `.env` to customize:

```
# Elasticsearch
ELASTICSEARCH_HOST=http://localhost:9200
ELASTICSEARCH_INDEX=rag_documents

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=documents

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma:4b

# Embedding
EMBEDDING_MODEL=BAAI/bge-m3

# FastAPI
API_HOST=0.0.0.0
API_PORT=8000
```

## 🐛 Troubleshooting

### Ollama Connection Error

```
Error: Could not connect to Ollama at http://localhost:11434
```

**Solution:**
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running (varies by OS)
ollama serve
```

### Elasticsearch Connection Error

```
Error: Failed to connect to Elasticsearch
```

**Solution:**
```bash
# Check if Elasticsearch is running
docker-compose ps

# Restart Elasticsearch
docker-compose restart elasticsearch
```

### Model Not Found

**Solution:**
```bash
# Pull the required model
ollama pull gemma:4b

# Verify
ollama list
```

### Memory Issues

If experiencing OOM (Out of Memory):
- Reduce chunk size in `document_chunker.py`
- Reduce batch size for embeddings
- Use a smaller embedding model
- Allocate more memory to Docker

### No Results in Search

```
# Check Elasticsearch index
curl http://localhost:9200/_cat/indices

# Verify documents are indexed
curl http://localhost:9200/rag_documents/_count
```

## 📊 Performance Tips

1. **Chunk Size**: Larger chunks retain more context but increase compute
2. **K Value**: 3-5 usually sufficient; more increases LLM processing time
3. **Temperature**: 0.7 balanced; lower (0.1-0.3) for factual answers, higher (0.9+) for creative
4. **Batch Processing**: Process multiple documents at once for efficiency

## 🎓 Learning Points

This project covers:

- **RAG Architecture**: Understanding retrieval + generation pipeline
- **Vector Search**: Implementing semantic search with embeddings
- **Hybrid Search**: Combining keyword + semantic search
- **Document Processing**: Chunking and embedding strategies
- **FastAPI**: Building modern REST APIs
- **Docker**: Containerizing multi-service applications
- **Integration**: Coordinating multiple services (Elasticsearch, MinIO, Ollama)

## 📝 Sample Documents

The `sample_docs/` folder contains learning materials on:
- Python Programming
- FastAPI Web Development
- Retrieval Augmented Generation
- Elasticsearch and Vector Search

Use these to test the system or add your own documents!

## 🔐 Security Notes

**⚠️ For Learning Only**

This project uses default credentials. Do NOT use in production:
- MinIO: minioadmin/minioadmin
- Elasticsearch: No authentication
- Add authentication, enable TLS, and use strong passwords in production

## 🚀 Next Steps & Enhancements

- [ ] Add user authentication
- [ ] Implement document metadata and filtering
- [ ] Add support for multiple languages
- [ ] Implement caching layer (Redis)
- [ ] Add monitoring and logging (ELK stack)
- [ ] Deploy to cloud (AWS, GCP, Azure)
- [ ] Implement reranking for better relevance
- [ ] Add support for structured data (CSV, JSON)
- [ ] Implement semantic caching
- [ ] Add feedback loop for continuous improvement

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Sentence Transformers](https://www.sbert.net/)
- [Ollama](https://ollama.ai/)
- [MinIO Documentation](https://docs.min.io/)

## 📄 License

This is a learning project. Use freely for educational purposes.

## 🤝 Contributing

This is a personal learning project. Feel free to fork, modify, and learn from it!

## 📞 Support

For issues or questions:
1. Check the Troubleshooting section
2. Verify all services are running (`docker-compose ps`)
3. Check logs: `docker-compose logs service_name`
4. Ensure ports are not in use

---

**Happy Learning! 🚀**
