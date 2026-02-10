#!/usr/bin/env python3
"""
Test script for RAG-based Q&A System
This script demonstrates how to use the RAG system programmatically
"""

import requests
import time
import os
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"
SAMPLE_DOCS_DIR = Path(__file__).parent / "sample_docs"

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")

def check_health():
    """Check if the system is healthy"""
    print_header("System Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✓ System is running")
            print(f"✓ Ollama connected: {data.get('ollama_connected')}")
            return True
        else:
            print("✗ System health check failed")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot connect to API: {e}")
        print(f"  Make sure FastAPI is running at {BASE_URL}")
        return False

def ingest_sample_documents():
    """Ingest sample documents"""
    print_header("Ingesting Sample Documents")
    
    ingested_docs = []
    txt_files = list(SAMPLE_DOCS_DIR.glob("*.txt"))
    
    if not txt_files:
        print(f"✗ No sample documents found in {SAMPLE_DOCS_DIR}")
        return ingested_docs
    
    for file_path in txt_files:
        print(f"Ingesting: {file_path.name}")
        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f, "text/plain")}
                response = requests.post(f"{BASE_URL}/ingest", files=files, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                doc_id = data.get("document_id")
                chunks = data.get("chunks_created")
                print(f"  ✓ Document ID: {doc_id}")
                print(f"  ✓ Chunks created: {chunks}\n")
                ingested_docs.append({
                    "id": doc_id,
                    "name": file_path.name,
                    "chunks": chunks
                })
            else:
                print(f"  ✗ Failed: {response.status_code}\n")
        
        except Exception as e:
            print(f"  ✗ Error: {e}\n")
        
        time.sleep(2)  # Delay between requests
    
    return ingested_docs

def ask_questions():
    """Ask sample questions"""
    print_header("Asking Questions (RAG Pipeline)")
    
    sample_questions = [
        "What are the key features of Python?",
        "How does FastAPI work?",
        "What is Retrieval Augmented Generation?",
        "What is Elasticsearch used for?",
        "How do embeddings work in RAG?",
    ]
    
    for i, question in enumerate(sample_questions, 1):
        print(f"Question {i}: {question}")
        print("-" * 60)
        
        try:
            response = requests.post(
                f"{BASE_URL}/ask",
                json={
                    "question": question,
                    "k": 3,
                    "temperature": 0.7
                },
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "No answer generated")
                context = data.get("context_used", [])
                
                print(f"Answer: {answer}\n")
                
                if context:
                    print("Context used:")
                    for j, ctx in enumerate(context, 1):
                        print(f"  [{j}] From '{ctx.get('document', 'Unknown')}' (Score: {ctx.get('score', 0):.2f})")
                        print(f"      {ctx.get('text', '')[:100]}...\n")
            else:
                print(f"✗ Error: {response.status_code}")
                print(f"  {response.text}\n")
        
        except requests.exceptions.Timeout:
            print("✗ Request timed out - LLM might be slow or not responding\n")
        except Exception as e:
            print(f"✗ Error: {e}\n")
        
        time.sleep(3)  # Delay between requests

def test_ingest_through_url():
    """Test ingesting a document from URL"""
    print_header("Testing Document Ingestion")
    
    # Create a simple test file
    test_file = Path("test_document.txt")
    test_content = """
    Machine Learning is a subset of artificial intelligence that enables systems 
    to learn and improve from experience without being explicitly programmed.
    
    Deep Learning using neural networks has revolutionized fields like computer vision 
    and natural language processing.
    
    Transfer learning allows models trained on one task to be adapted for another task,
    reducing training time and data requirements.
    """
    
    try:
        # Write test file
        test_file.write_text(test_content)
        print(f"Created test file: {test_file.name}")
        
        # Ingest it
        with open(test_file, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{BASE_URL}/ingest", files=files, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Successfully ingested test document")
            print(f"  Document ID: {data.get('document_id')}")
            print(f"  Chunks: {data.get('chunks_created')}")
            
            doc_id = data.get('document_id')
            return doc_id
        else:
            print(f"✗ Failed to ingest: {response.status_code}")
            return None
    
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()
            print(f"Cleaned up test file")

def query_about_ml():
    """Query about machine learning"""
    print_header("Testing ML Document Query")
    
    question = "What is machine learning?"
    print(f"Question: {question}")
    print("-" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/ask",
            json={
                "question": question,
                "k": 5,
                "temperature": 0.5
            },
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Answer: {data.get('answer')}\n")
        else:
            print(f"✗ Error: {response.status_code}")
    
    except Exception as e:
        print(f"✗ Error: {e}")

def main():
    """Main test execution"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  RAG-Based Q&A System - Test Suite".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    
    # Check system health
    if not check_health():
        print("\n✗ System is not ready. Please ensure:")
        print("  1. FastAPI app is running: uvicorn main:app --port 8000")
        print("  2. Elasticsearch is running")
        print("  3. MinIO is running")
        print("  4. Ollama is running locally")
        return
    
    # Ingest documents
    print("\n")
    docs = ingest_sample_documents()
    
    if not docs:
        print("✗ No documents were ingested. Cannot proceed with testing.")
        return
    
    # Wait a bit for indexing
    print("\nWaiting for document indexing...\n")
    time.sleep(5)
    
    # Ask questions
    ask_questions()
    
    # Test creating and querying custom document
    print("\n")
    doc_id = test_ingest_through_url()
    if doc_id:
        time.sleep(3)
        query_about_ml()
    
    print_header("Test Complete!")
    print("✓ All tests completed successfully\n")
    print("Next steps:")
    print("  - Open http://localhost:8000/docs for interactive API")
    print("  - Try ingesting your own documents")
    print("  - Explore the Elasticsearch index at http://localhost:9200")
    print("  - Access MinIO console at http://localhost:9001")

if __name__ == "__main__":
    main()
