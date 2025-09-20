from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Patient, Note, SummaryCache
import json
from datetime import datetime, timedelta

# We'll prefer real providers with graceful fallbacks to mock
def _try_generate_summary_with_providers(retrieved):
    # Try OpenRouter first (our best working provider)
    try:
        from openrouter_wrapper import generate_json_summary as openrouter_generate
        return openrouter_generate(retrieved), "openrouter"
    except Exception:
        pass
    # Try Cohere
    try:
        from cohere_wrapper import generate_json_summary as cohere_generate
        return cohere_generate(retrieved), "cohere"
    except Exception:
        pass
    # Try Hugging Face
    try:
        from hf_wrapper import generate_json_summary as hf_generate
        return hf_generate(retrieved), "huggingface"
    except Exception:
        pass
    # Try Ollama
    try:
        from ollama_wrapper import generate_json_summary as ollama_generate
        return ollama_generate(retrieved), "ollama"
    except Exception:
        pass
    # Try GPT4All
    try:
        from gpt4all_wrapper import generate_json_summary as gpt4all_generate
        return gpt4all_generate(retrieved), "gpt4all"
    except Exception:
        pass
    # Fallback to mock
    from mock_ai_wrapper import generate_json_summary as mock_generate
    return mock_generate(retrieved), "mock_ai"

router = APIRouter()

@router.post("/{patient_id}/summarize")
async def summarize(patient_id: int, db: Session = Depends(get_db)):
    # Get patient notes from database
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Check for cached summary (valid for 1 hour)
    cache_cutoff = datetime.utcnow() - timedelta(hours=1)
    cached_summary = db.query(SummaryCache).filter(
        SummaryCache.patient_id == patient_id,
        SummaryCache.updated_at >= cache_cutoff
    ).order_by(SummaryCache.updated_at.desc()).first()
    
    if cached_summary:
        try:
            cached_data = json.loads(cached_summary.summary_json)
            cached_data["from_cache"] = True
            cached_data["cache_source"] = cached_summary.source
            return cached_data
        except (json.JSONDecodeError, Exception):
            # Invalid cache, continue to generate new summary
            pass
    
    notes = db.query(Note).filter(Note.patient_id == patient_id).all()
    if not notes:
        return {
            "one_line": f"No notes available for {patient.name}",
            "bullets": ["No clinical data to analyze"],
            "sources": []
        }
    
    # Prepare notes for AI analysis
    # Build retrieval items expected by wrappers (id/date/snippet/score optional)
    retrieved = []
    for note in notes:
        retrieved.append({
            "note_id": note.id,
            "note_date": getattr(note, "note_date", None),
            "snippet": (note.text or "").strip(),
            "score": 1.0,
        })
    
    # Try providers with graceful fallback
    try:
        # Prefer OpenRouter if available
        try:
            from openrouter_wrapper import generate_json_summary as or_generate
            ai_result = or_generate(retrieved)
            provider = "openrouter"
        except Exception:
            # Try Gemini next
            try:
                from gemini_wrapper import generate_json_summary as gem_generate
                ai_result = gem_generate(retrieved)
                provider = "gemini"
            except Exception:
                ai_result, provider = _try_generate_summary_with_providers(retrieved)
        
        # Prepare final result
        if isinstance(ai_result, dict) and {"one_line", "bullets"}.issubset(ai_result.keys()):
            ai_result.setdefault("sources", [{"note_id": r.get("note_id"), "score": r.get("score", 0)} for r in retrieved[:5]])
            ai_result["ai_provider"] = ai_result.get("ai_provider", provider)
            final_result = ai_result
        else:
            # Translate mock/other shapes
            final_result = {
                "one_line": ai_result.get("summary", "AI summary not available"),
                "bullets": ai_result.get("key_points", ["No key points available"]),
                "sources": [{"note_id": r.get("note_id"), "snippet": r.get("snippet", "")[:200]} for r in retrieved],
                "ai_provider": ai_result.get("provider", provider),
                "confidence": ai_result.get("confidence", 0.0),
            }
        
        # Cache the successful result
        try:
            # Clear old cache entries for this patient
            db.query(SummaryCache).filter(SummaryCache.patient_id == patient_id).delete()
            
            # Add new cache entry
            cache_entry = SummaryCache(
                patient_id=patient_id,
                source=provider,
                summary_json=json.dumps(final_result),
                updated_at=datetime.utcnow()
            )
            db.add(cache_entry)
            db.commit()
        except Exception as cache_error:
            # Log cache error but don't fail the request
            print(f"Cache save error: {cache_error}")
        
        final_result["from_cache"] = False
        return final_result
        
    except Exception as e:
        # Fallback to basic summary if AI fails entirely
        return {
            "one_line": f"Summary for {patient.name} - {len(notes)} clinical notes available",
            "bullets": [f"Note {i+1}: {n.text[:50]}..." for i, n in enumerate(notes[:3])],
            "sources": [{"note_id": n.id, "snippet": (n.text or "")[:200]} for n in notes],
            "error": f"AI processing failed: {str(e)}",
            "from_cache": False
        }
