from fastapi import APIRouter, File, UploadFile, HTTPException
from app.services.rag_pipeline import rag_pipeline
from app.services.ollama_service import ollama_service
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["RAG"])

class QuestionRequest(BaseModel):
    question: str
    k: int = 5
    temperature: float = 0.7

class AnswerResponse(BaseModel):
    question: str
    answer: str
    context_used: list
    status: str

@router.get("/health")
async def health_check():
    """Check system health"""
    ollama_connected = ollama_service.check_connection()
    return {
        "status": "healthy",
        "ollama_connected": ollama_connected,
        "message": "RAG system is running"
    }

@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """Upload and ingest a PDF document"""
    try:
        if file.content_type not in ["application/pdf", "text/plain"]:
            raise HTTPException(status_code=400, detail="Only PDF and text files are supported")
        
        file_bytes = await file.read()
        file_type = "pdf" if file.filename.endswith(".pdf") else "text"
        
        result = rag_pipeline.ingest_document(file_bytes, file.filename, document_type=file_type)
        
        if result["status"] == "success":
            return result
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting document: {str(e)}")

@router.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question to the RAG system"""
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        result = rag_pipeline.answer_question(
            request.question,
            k=request.k,
            temperature=request.temperature
        )
        
        if result["status"] == "success":
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Error generating answer"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its chunks"""
    try:
        result = rag_pipeline.delete_document(document_id)
        
        if result["status"] == "success":
            return result
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")
