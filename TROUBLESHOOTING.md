# 🔧 TROUBLESHOOTING GUIDE

Solutions for common issues with the RAG Q&A System.

## Connection Issues

### APIError: Cannot connect to FastAPI at `http://localhost:8000`

**Problem**: The API is not responding

**Solutions**:
```bash
# 1. Check if FastAPI is running
curl http://localhost:8000/

# 2. If not running, start it
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 3. Check if port 8000 is in use
# On Windows:
netstat -ano | findstr :8000

# 4. Use a different port if needed
uvicorn main:app --port 8001

# 5. Update .env with new port
# MINIO_ENDPOINT=localhost:8001
```

---

### Error: Could not connect to Elasticsearch

**Problem**: Elasticsearch is not running or not accessible

**Solutions**:
```bash
# 1. Check if Docker services are running
docker-compose ps

# 2. If services are down, start them
docker-compose up -d elasticsearch minio

# 3. Verify Elasticsearch is responding
curl http://localhost:9200

# 4. Check logs for errors
docker-compose logs elasticsearch

# 5. If stuck, restart service
docker-compose restart elasticsearch

# 6. Verify in .env that host matches
# ELASTICSEARCH_HOST=http://localhost:9200
```

**Advanced**:
```bash
# Check index exists
curl http://localhost:9200/_cat/indices

# Check documents are indexed
curl http://localhost:9200/rag_documents/_count

# Delete index to reset (WARNING: deletes all data)
curl -X DELETE http://localhost:9200/rag_documents
```

---

### Error: Could not connect to Ollama at `http://localhost:11434`

**Problem**: Ollama service is not running

**Solutions**:
```bash
# 1. Check if Ollama is running
curl http://localhost:11434/api/tags

# 2. If error, start Ollama in a new terminal
ollama serve

# 3. Verify on Windows (service might be running as background process)
tasklist | findstr ollama

# 4. If multiple Ollama instances, kill existing ones
taskkill /IM ollama.exe /F

# 5. Restart Ollama
ollama serve

# 6. Check configuration
# OLLAMA_HOST=http://localhost:11434
```

---

### MinIO Connection Error

**Problem**: MinIO is not accessible

**Solutions**:
```bash
# 1. Check if MinIO is running
docker-compose ps | grep minio

# 2. Start MinIO
docker-compose up -d minio

# 3. Verify it's responding
curl http://localhost:9000/minio/health/live

# 4. Check logs
docker-compose logs minio

# 5. Access MinIO Console
# URL: http://localhost:9001
# Username: minioadmin
# Password: minioadmin

# 6. Verify .env settings
# MINIO_ENDPOINT=localhost:9000
# MINIO_ACCESS_KEY=minioadmin
# MINIO_SECRET_KEY=minioadmin
# MINIO_BUCKET=documents
```

---

## Model & Embedding Issues

### Error: Model 'gemma:4b' not found

**Problem**: Ollama doesn't have the required model

**Solutions**:
```bash
# 1. Check available models
ollama list

# 2. Pull the model
ollama pull gemma:4b

# 3. Verify it was pulled
ollama list | grep gemma

# 4. If stuck or slow, increase timeout and try again
ollama pull gemma:4b

# 5. Alternative: Use a different model
# Edit .env: OLLAMA_MODEL=mistral or OLLAMA_MODEL=llama2
ollama pull mistral
```

---

### Error: Embedding model failed to load

**Problem**: BGE-M3 embedding model not loading

**Solutions**:
```bash
# 1. Check internet connection (model downloads from Hugging Face)

# 2. Try manually downloading the model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"

# 3. If slow or fails, use a smaller model
# Edit .env: EMBEDDING_MODEL=all-MiniLM-L6-v2
pip install sentence-transformers

# 4. Check pip is up to date
pip install --upgrade sentence-transformers

# 5. Check available disk space (model is ~2GB)
```

---

## Document Processing Issues

### Error: Failed to ingest document

**Problem**: Document upload fails

**Solutions**:
```bash
# 1. Check file format
# Supported: PDF, TXT, text/plain, application/pdf

# 2. Check file size
# If very large, split into smaller files

# 3. Check file permissions
# Ensure file is readable

# 4. Try with sample document first
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -F "file=@sample_docs/python_guide.txt"

# 5. Check API logs for detailed error
# Look in terminal where you ran uvicorn

# 6. Verify MinIO bucket exists
# Check MinIO console: http://localhost:9001
```

**Python debugging**:
```python
# Test document processing directly
from app.services.document_chunker import DocumentChunker

chunker = DocumentChunker()
with open("sample_docs/python_guide.txt", "r") as f:
    text = f.read()
chunks = chunker.chunk_text(text)
print(f"Created {len(chunks)} chunks")
```

---

### No results returned for query

**Problem**: Asked a question but got no context

**Solutions**:
```bash
# 1. Verify documents were ingested
curl http://localhost:9200/rag_documents/_count

# 2. Wait a moment for indexing
# (Elasticsearch sometimes needs time to index)
sleep 5

# 3. Try a simpler question with exact keywords

# 4. Increase k (number of results)
# Try k=10 instead of k=5

# 5. Check if documents contain relevant content
curl "http://localhost:9200/rag_documents/_search?q=python" -H "Content-Type: application/json"

# 6. Verify embedding service is working
python -c "from app.services.embedding_service import embedding_service; print(embedding_service.embed_text('test'))"
```

---

## Performance Issues

### System is slow / taking too long

**Solutions**:
```bash
# 1. Check resource usage
# CPU, memory should be reasonable
# Watch -n 1 command (Linux/Mac)
# Task Manager (Windows)

# 2. Reduce chunk size (less processing)
# In app/services/document_chunker.py:
# self.chunk_size = 300  # was 500

# 3. Reduce k value (fewer results to process)
# In API call: "k": 3  # was 5

# 4. Use smaller embedding model
# In .env: EMBEDDING_MODEL=all-MiniLM-L6-v2

# 5. Use smaller LLM
# In .env: OLLAMA_MODEL=orca-mini

# 6. Allocate more memory to Docker
# Docker Desktop Settings -> Resources -> Memory

# 7. Check database size
du -sh ./data/
```

---

### Out of Memory (OOM) errors

**Solutions**:
```bash
# 1. Increase Docker memory allocation
# Docker Desktop -> Settings -> Resources -> Memory (increase to 4GB or more)

# 2. Reduce batch size for embeddings
# In embedding_service.py:
# Process fewer documents at once

# 3. Use CPU-optimized settings
# Disable GPU if using CUDA:
# export CUDA_VISIBLE_DEVICES=""

# 4. Clear unnecessary data
docker-compose down -v  # Remove volumes
docker system prune      # Clean up Docker

# 5. Monitor memory usage
docker stats

# 6. Use a lighter embedding model
# Edit .env: EMBEDDING_MODEL=all-MiniLM-L6-v2
```

---

## Docker Issues

### Docker containers won't start

**Solutions**:
```bash
# 1. Check Docker is running
docker ps

# 2. Check docker-compose logs
docker-compose logs

# 3. Try rebuilding
docker-compose up -d --build

# 4. Check for port conflicts
netstat -ano | findstr :9200  # Elasticsearch
netstat -ano | findstr :9000  # MinIO

# 5. Reset Docker (careful!)
docker-compose down -v
docker-compose up -d

# 6. Check disk space
docker system df

# 7. Prune unused images/containers
docker system prune
```

---

### Permission denied errors

**Problem**: Cannot read/write files

**Solutions**:
```bash
# Check file permissions
ls -la sample_docs/

# Make files readable
chmod 644 sample_docs/*

# Reset directory permissions
chmod 755 sample_docs/

# On Windows (PowerShell as Admin):
Get-ChildItem sample_docs -Recurse | % {
  $acl = Get-Acl $_.FullName
  $acl.SetAccessRuleProtection($false, $false)
  Set-Acl $_.FullName $acl
}
```

---

## Python/Dependencies Issues

### ModuleNotFoundError: No module named 'xxx'

**Solutions**:
```bash
# 1. Activate virtual environment
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# 2. Reinstall all dependencies
pip install -r requirements.txt

# 3. Check pip version
pip --version

# 4. Upgrade pip
pip install --upgrade pip

# 5. Check for conflicting packages
pip check

# 6. Fresh install (if still issues)
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

---

### Version conflicts

**Solutions**:
```bash
# Check installed versions
pip list

# Check specific package version
pip show sentence-transformers

# Upgrade specific package
pip install --upgrade sentence-transformers

# Install exact version from requirements
pip install sentence-transformers==2.2.2
```

---

## Debugging Tips

### Enable verbose logging

```python
# In main.py, add before running:
import logging
logging.basicConfig(level=logging.DEBUG)

# Or run with:
uvicorn main:app --log-level debug
```

### Check service health

```bash
# Full health check script
python3 << 'EOF'
import requests

services = {
    "FastAPI": "http://localhost:8000/api/v1/health",
    "Elasticsearch": "http://localhost:9200",
    "MinIO": "http://localhost:9000/minio/health/live",
    "Ollama": "http://localhost:11434/api/tags"
}

for name, url in services.items():
    try:
        r = requests.get(url, timeout=2)
        status = "✓ OK" if r.status_code == 200 else f"✗ {r.status_code}"
    except:
        status = "✗ NOT RESPONDING"
    print(f"{name:15} {status}")
EOF
```

### Test individual components

```python
# Test embedding
from app.services.embedding_service import embedding_service
emb = embedding_service.embed_text("test")
print(f"Embedding size: {len(emb)}")

# Test Ollama
from app.services.ollama_service import ollama_service
if ollama_service.check_connection():
    response = ollama_service.generate("Hello, how are you?")
    print(f"LLM Response: {response}")

# Test Elasticsearch
from app.core.elasticsearch_client import es_client
print(f"Elasticsearch connected: {es_client.client.ping()}")

# Test MinIO
from app.core.minio_client import minio_client
objects = minio_client.list_objects()
print(f"MinIO objects: {objects}")
```

---

## Getting Help

If issue persists:

1. **Check logs**: `docker-compose logs | grep ERROR`
2. **Check .env**: Verify all configuration values
3. **Check versions**: `pip list` for Python packages
4. **Check ports**: `netstat -ano` (Windows) or `lsof -i` (Mac/Linux)
5. **Try fresh install**: Delete venv and start over
6. **Ask for help**: Include error messages and system info

---

**Last Resort**: Fresh start

```bash
# Stop everything
docker-compose down -v
deactivate
Ctrl+C  # Stop FastAPI and Ollama

# Clean up
rm -rf venv __pycache__ .pytest_cache

# Start fresh
python -m venv venv
venv\Scripts\activate  # or source venv/bin/activate
pip install -r requirements.txt
docker-compose up -d elasticsearch minio
ollama serve  # in another terminal

# Run again
uvicorn main:app --port 8000
```

---

**Good luck! 🍀**
