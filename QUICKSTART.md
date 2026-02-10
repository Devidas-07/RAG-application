# 🚀 QUICKSTART GUIDE

Get the RAG Q&A System running in 5 minutes!

## Prerequisites

Before you start, ensure you have:
- ✅ Docker Desktop (running)
- ✅ Ollama (installed)
- ✅ Python 3.10+
- ✅ Ports available: 8000, 9000, 9200, 11434

## Step 1: Prepare Ollama (1 min)

```bash
# In a terminal, start Ollama
ollama serve

# In another terminal, pull Gemma 3:4b model
ollama pull gemma:4b

# Verify it's ready
ollama list  # Should show gemma:4b
```

## Step 2: Install Dependencies (2 min)

```bash
# Navigate to project directory
cd rag-qa-system

# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

## Step 3: Start Services (1 min)

```bash
# In a new terminal, start Elasticsearch and MinIO
docker-compose up -d elasticsearch minio

# Wait for services to be ready (watch the logs)
docker-compose logs -f
# Ctrl+C when you see "started" messages for both services
```

## Step 4: Start FastAPI (1 min)

```bash
# In your main terminal (with venv activated)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

✅ **System is now running!**

## Access the System

- 🌐 **API Dashboard**: http://localhost:8000/docs
- 📊 **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- 🔍 **Elasticsearch**: http://localhost:9200

## First Test (1 min)

### Option A: Using FastAPI Docs UI (Easiest)

1. Open http://localhost:8000/docs
2. Click "Ingest" endpoint → "Try it out"
3. Choose a file from `sample_docs/` folder
4. Click "Execute"
5. Wait for success, then go to "Ask" endpoint
6. Enter: `"What is Python used for?"`
7. Click "Execute" and see the answer!

### Option B: Using Python Script

```bash
# In a new terminal (with venv activated)
python test_rag.py
```

### Option C: Using curl

```bash
# Ingest a document
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -F "file=@sample_docs/python_guide.txt"

# Ask a question
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Python used for?"}'
```

## Sample Documents

The `sample_docs/` folder contains:
- `python_guide.txt` - Python programming
- `fastapi_guide.txt` - FastAPI basics
- `rag_guide.txt` - RAG concepts
- `elasticsearch_guide.txt` - Elasticsearch guide

Ingest any of these and ask questions about them!

## Common Issues & Quick Fixes

### "Cannot connect to Ollama"
```bash
# Make sure Ollama is running in another terminal
ollama serve
```

### "Elasticsearch not available"
```bash
# Check if Docker services are running
docker-compose ps

# If not, start them
docker-compose up -d elasticsearch minio
```

### "Model not found"
```bash
# Pull the model
ollama pull gemma:4b
```

### Port already in use
- 8000: Change FastAPI port: `uvicorn main:app --port 8001`
- 9200: Change `ELASTICSEARCH_HOST` in `.env`
- 9000: Change `MINIO_ENDPOINT` in `.env`
- 11434: Change `OLLAMA_HOST` in `.env`

## Next Steps

1. **Explore the API**: Read [API Documentation](README.md#-api-endpoints)
2. **Learn the Architecture**: Check [Pipeline Workflow](README.md#-pipeline-workflow)
3. **Understand the Code**: Review the project structure in [README.md](README.md#-project-structure)
4. **Add Your Documents**: Ingest your own PDFs/text files
5. **Customize**: Modify chunk sizes, temperature, embedding model in code

## Stopping the System

```bash
# Stop FastAPI (Ctrl+C in that terminal)

# Stop Docker services
docker-compose down

# Deactivate Python environment
deactivate

# Stop Ollama (Ctrl+C in that terminal)
```

## Full Documentation

See [README.md](README.md) for complete documentation, architecture details, and advanced usage.

---

**Happy Learning! 🎓**
