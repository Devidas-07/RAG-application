from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.rag_routes import router as rag_router
from app.core.config import config

# Create FastAPI app
app = FastAPI(
    title="RAG-Based QA System",
    description="Retrieval Augmented Generation Question Answering System using Gemma, Elasticsearch, and BGE-M3",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rag_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "RAG-Based QA System",
        "version": "1.0.0",
        "description": "A learning project for Retrieval Augmented Generation",
        "endpoints": {
            "health": "/api/v1/health",
            "ingest": "/api/v1/ingest (POST)",
            "ask": "/api/v1/ask (POST)",
            "delete": "/api/v1/documents/{document_id} (DELETE)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        log_level="info"
    )
