from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from ..services.rag_service import rag_assistant
from ..services.auth_service import get_current_user
from ..models.auth import User

router = APIRouter(prefix="/api/assistant", tags=["Approved Knowledge Base RAG Assistant"])

class QueryRequest(BaseModel):
    query: str

@router.post("/query")
def ask_assistant(req: QueryRequest, current_user: User = Depends(get_current_user)):
    result = rag_assistant.answer_query(req.query)
    return result

@router.get("/documents")
def list_approved_documents(current_user: User = Depends(get_current_user)):
    return {
        "total_documents": len(rag_assistant.documents),
        "total_indexed_passages": len(rag_assistant.passages),
        "documents": rag_assistant.documents
    }

