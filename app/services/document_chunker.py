import PyPDF2
import io
from typing import List

class DocumentChunker:
    """Chunks documents into smaller pieces"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def extract_pdf_text(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes"""
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk = " ".join(chunk_words)
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def chunk_pdf(self, pdf_bytes: bytes) -> List[str]:
        """Extract and chunk PDF"""
        text = self.extract_pdf_text(pdf_bytes)
        return self.chunk_text(text)
    
    def chunk_text_file(self, text_content: str) -> List[str]:
        """Chunk plain text content"""
        return self.chunk_text(text_content)
