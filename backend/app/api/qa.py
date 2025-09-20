from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Patient, Note

def _try_answer_with_providers(retrieved, question: str):
    # Try OpenRouter first (our best working provider)
    try:
        from openrouter_wrapper import generate_json_summary as openrouter_generate
        out = openrouter_generate(retrieved, question=question)
        return out, "openrouter"
    except Exception:
        pass
    # Try Gemini as second option (reliable fallback)
    try:
        from gemini_wrapper import generate_json_summary as gemini_generate
        out = gemini_generate(retrieved, question=question)
        return out, "gemini"
    except Exception:
        pass
    try:
        from cohere_wrapper import generate_json_summary as cohere_generate
        out = cohere_generate(retrieved, question=question)
        return out, "cohere"
    except Exception:
        pass
    try:
        from hf_wrapper import generate_json_summary as hf_generate
        out = hf_generate(retrieved, question=question)
        return out, "huggingface"
    except Exception:
        pass
    try:
        from ollama_wrapper import generate_json_summary as ollama_generate
        out = ollama_generate(retrieved, question=question)
        return out, "ollama"
    except Exception:
        pass
    try:
        from gpt4all_wrapper import generate_json_summary as gpt4all_generate
        out = gpt4all_generate(retrieved, question=question)
        return out, "gpt4all"
    except Exception:
        pass
    from mock_ai_wrapper import generate_json_summary as mock_generate
    return mock_generate(retrieved, question=question), "mock_ai"

router = APIRouter()

class QAIn(BaseModel):
    question: str

@router.post("/{patient_id}/qa")
async def qa(patient_id: int, body: QAIn, db: Session = Depends(get_db)):
    # Get patient and notes from database
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    notes = db.query(Note).filter(Note.patient_id == patient_id).all()
    
    # Prepare retrieval items for AI
    retrieved = []
    for note in notes:
        retrieved.append({
            "note_id": note.id,
            "note_date": getattr(note, "note_date", None),
            "snippet": (note.text or "").strip(),
            "score": 1.0,
        })
    
    try:
        # Generate AI response with question context via providers (OpenRouter->Gemini priority)
        ai_result, provider = _try_answer_with_providers(retrieved, body.question)
        
        # Normalize outputs
        answer = ai_result.get("answer") or ai_result.get("one_line") or f"Answer to: {body.question}"
        return {
            "answer": answer,
            "sources": [{
                "note_id": r.get("note_id"),
                "snippet": (r.get("snippet") or "")[:200],
                "relevance": r.get("score", 0.8),
            } for r in retrieved[:3]],
            "confidence": ai_result.get("confidence", 0.7),
            "ai_provider": provider,
        }
    except Exception as e:
        return {
            "answer": f"I encountered an error while processing your question: {body.question}. Error: {str(e)}",
            "sources": [],
            "error": True
        }
