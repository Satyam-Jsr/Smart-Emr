from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.models import Patient, Note, SummaryCache, MedicalDocument
from app.database import SessionLocal, init_db
import json
import os
import uuid
import tempfile
from datetime import datetime
from typing import List, Optional
from medical_ocr import MedicalOCR
import logging

logger = logging.getLogger(__name__)


def create_medical_note_from_ocr(patient_id: int, document_id: int, filename: str, 
                                 doc_type: str, ocr_text: str, confidence: float, db: Session) -> int:
    """
    Automatically create a structured medical note from OCR-extracted text.
    
    Args:
        patient_id: The patient's ID
        document_id: The medical document ID
        filename: The original filename
        doc_type: The detected document type
        ocr_text: The extracted OCR text
        confidence: The OCR confidence score
        db: Database session
        
    Returns:
        The created note ID, or None if note creation was skipped
    """
    # Skip creating notes for very low confidence or empty text
    if confidence < 10.0 or not ocr_text.strip() or len(ocr_text.strip()) < 20:
        return None
    
    # Generate structured note content based on document type and OCR text
    current_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    
    if doc_type == "lab_report":
        note_content = f"""Medical Document Analysis - Laboratory Report (Auto-Generated)

Document ID: {document_id} | Filename: {filename}
Date: {current_date} | OCR Confidence: {confidence:.1f}%

EXTRACTED LABORATORY RESULTS:
{ocr_text}

CLINICAL STATUS:
- Laboratory document processed automatically from uploaded image
- Results extracted using OCR technology
- Manual verification recommended for critical values

Note: This note was automatically generated from OCR analysis of uploaded medical document.
"""
    
    elif doc_type == "xray":
        note_content = f"""Medical Document Analysis - Imaging Report (Auto-Generated)

Document ID: {document_id} | Filename: {filename}
Date: {current_date} | OCR Confidence: {confidence:.1f}%

EXTRACTED IMAGING CONTENT:
{ocr_text}

IMAGING STATUS:
- Radiology document processed automatically from uploaded image
- Content extracted using OCR technology
- Professional radiologist review recommended

Note: This note was automatically generated from OCR analysis of uploaded medical document.
"""
    
    elif doc_type == "blood_test":
        note_content = f"""Medical Document Analysis - Blood Test Results (Auto-Generated)

Document ID: {document_id} | Filename: {filename}
Date: {current_date} | OCR Confidence: {confidence:.1f}%

EXTRACTED BLOOD TEST RESULTS:
{ocr_text}

HEMATOLOGY STATUS:
- Blood test document processed automatically from uploaded image
- Values extracted using OCR technology
- Clinical correlation and verification recommended

Note: This note was automatically generated from OCR analysis of uploaded medical document.
"""
    
    elif doc_type == "prescription":
        note_content = f"""Medical Document Analysis - Prescription (Auto-Generated)

Document ID: {document_id} | Filename: {filename}
Date: {current_date} | OCR Confidence: {confidence:.1f}%

EXTRACTED PRESCRIPTION CONTENT:
{ocr_text}

MEDICATION STATUS:
- Prescription document processed automatically from uploaded image
- Medication information extracted using OCR technology
- Pharmacy verification and clinical review recommended

Note: This note was automatically generated from OCR analysis of uploaded medical document.
"""
    
    else:
        # Generic medical document
        note_content = f"""Medical Document Analysis - {doc_type.title()} (Auto-Generated)

Document ID: {document_id} | Filename: {filename}
Date: {current_date} | OCR Confidence: {confidence:.1f}%

EXTRACTED MEDICAL CONTENT:
{ocr_text}

DOCUMENT STATUS:
- Medical document processed automatically from uploaded image
- Content extracted using OCR technology
- Healthcare provider review recommended for clinical decisions

Note: This note was automatically generated from OCR analysis of uploaded medical document.
"""
    
    # Create and save the note
    note = Note(
        patient_id=patient_id,
        text=note_content,
        note_date=datetime.utcnow()
    )
    
    db.add(note)
    db.commit()
    db.refresh(note)
    
    # Invalidate cached summaries for this patient since we added a new note
    try:
        db.query(SummaryCache).filter(SummaryCache.patient_id == patient_id).delete()
        db.commit()
    except Exception:
        db.rollback()
    
    return note.id


app = FastAPI()

# Allow CORS from the frontend dev server during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/patients")
async def create_patient(p: dict, db: Session = Depends(get_db)):
    patient = Patient(name=p['name'], age=p['age'])
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient

@app.get("/patients/")
async def list_patients(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    return patients

@app.get("/patients/{pid}")
async def get_patient(pid: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == pid).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@app.delete("/patients/{patient_id}")
async def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Delete all associated notes first
    db.query(Note).filter(Note.patient_id == patient_id).delete()
    
    # Delete all associated documents
    db.query(MedicalDocument).filter(MedicalDocument.patient_id == patient_id).delete()
    
    # Delete the patient
    db.delete(patient)
    db.commit()
    
    return {"status": "deleted"}

@app.post("/patients/{pid}/notes")
async def add_note(pid: int, note: dict, db: Session = Depends(get_db)):
    # persist a new note for the patient
    patient = db.query(Patient).filter(Patient.id == pid).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    n = Note(patient_id=pid, text=note.get('text', ''))
    db.add(n)
    db.commit()
    db.refresh(n)
    # Invalidate cached summaries for this patient
    try:
        db.query(SummaryCache).filter(SummaryCache.patient_id == pid).delete()
        db.commit()
    except Exception:
        db.rollback()

    return {
        "id": n.id,
        "patient_id": n.patient_id,
        "note_date": n.note_date.isoformat(),
        "text": n.text,
    }


@app.get("/patients/{pid}/notes")
async def get_patient_notes(pid: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == pid).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    notes = db.query(Note).filter(Note.patient_id == pid).order_by(Note.note_date.desc()).all()
    return [
        {"id": n.id, "patient_id": n.patient_id, "note_date": n.note_date.isoformat(), "text": n.text}
        for n in notes
    ]


@app.get("/notes")
async def get_notes(patient_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Note)
    if patient_id is not None:
        query = query.filter(Note.patient_id == patient_id)
    notes = query.order_by(Note.note_date.desc()).all()
    return [
        {"id": n.id, "patient_id": n.patient_id, "note_date": n.note_date.isoformat(), "text": n.text}
        for n in notes
    ]


@app.get("/notes/{pid}")
async def get_notes_by_pid(pid: int, db: Session = Depends(get_db)):
    notes = db.query(Note).filter(Note.patient_id == pid).order_by(Note.note_date.desc()).all()
    return [
        {"id": n.id, "patient_id": n.patient_id, "note_date": n.note_date.isoformat(), "text": n.text}
        for n in notes
    ]


@app.delete("/notes/{note_id}")
async def delete_note(note_id: int, db: Session = Depends(get_db)):
    n = db.query(Note).filter(Note.id == note_id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Note not found")
    patient_id = n.patient_id
    db.delete(n)
    db.commit()
    # Invalidate cache for this patient
    try:
        db.query(SummaryCache).filter(SummaryCache.patient_id == patient_id).delete()
        db.commit()
    except Exception:
        db.rollback()
    return {"status": "ok"}

@app.post("/patients/{pid}/summarize")
async def summarize(pid: int, k: int = 5, db: Session = Depends(get_db)):
    """Summarize a patient's notes using RAG retrieval. Prefer Cohere generator when available,
    fall back to a simple mock summary otherwise.
    """
    try:
        # local import to avoid startup errors when dependencies aren't present
        from rag_prototype import RAGIndex
    except Exception:
        return {"one_line": "(summarization unavailable) please install dependencies", "bullets": [], "sources": []}

    # Check for cached summary first
    try:
        cached = db.query(SummaryCache).filter(SummaryCache.patient_id == pid).order_by(SummaryCache.updated_at.desc()).first()
        if cached:
            try:
                payload = json.loads(cached.summary_json)
                # ensure source is present
                if isinstance(payload, dict):
                    payload.setdefault('source', cached.source or 'cache')
                return payload
            except Exception:
                # if cached content is malformed, fall through and regenerate
                pass
    except Exception:
        # DB/cache check failed; continue to generate
        pass

    r = RAGIndex()
    r.load()
    hits = r.query(pid, f"summarize patient {pid}", k=k)

    # convert hits to retrieval format expected by cohere_wrapper
    retrieved = []
    for score, meta in hits:
        retrieved.append({
            "note_id": meta.get("note_id"),
            "patient_id": meta.get("patient_id"),
            "note_date": meta.get("note_date"),
            "snippet": meta.get("text_snippet"),
            "score": float(score),
        })

    # Try to use OpenRouter wrapper as primary AI service
    try:
        from openrouter_wrapper import generate_json_summary
        try:
            summary = generate_json_summary(retrieved)
            # mark source for debugging / UI
            if isinstance(summary, dict):
                summary["source"] = "openrouter"
            # persist to cache
            try:
                sc = SummaryCache(patient_id=pid, source="openrouter", summary_json=json.dumps(summary))
                db.add(sc)
                db.commit()
            except Exception:
                db.rollback()
            return summary
        except Exception as e:
            # generation/parsing error — fall back to next option
            print("OpenRouter generation failed:", e)
            
            # Try Gemini as fallback
            try:
                from gemini_wrapper import generate_json_summary as gemini_generate
                try:
                    summary = gemini_generate(retrieved)
                    if isinstance(summary, dict):
                        summary["source"] = "gemini"
                    # persist to cache
                    try:
                        sc = SummaryCache(patient_id=pid, source="gemini", summary_json=json.dumps(summary))
                        db.add(sc)
                        db.commit()
                    except Exception:
                        db.rollback()
                    return summary
                except Exception as ge:
                    print("Gemini generation failed:", ge)
            except Exception:
                pass
            
            # Try Cohere as secondary fallback if available
            try:
                from cohere_wrapper import generate_json_summary as cohere_generate
                try:
                    summary = cohere_generate(retrieved)
                    if isinstance(summary, dict):
                        summary["source"] = "cohere"
                    # persist to cache
                    try:
                        sc = SummaryCache(patient_id=pid, source="cohere", summary_json=json.dumps(summary))
                        db.add(sc)
                        db.commit()
                    except Exception:
                        db.rollback()
                    return summary
                except Exception as ce:
                    print("Cohere generation failed:", ce)
            except Exception:
                pass
    except Exception:
        # openrouter_wrapper not available or not configured — will fall back
        pass

    # Fallback mock summary (Stage A)
    bullets = []
    sources = []
    for rscore, meta in hits:
        text = meta.get("text_snippet")
        bullets.append(text[:200])
        sources.append({"note_id": meta.get("note_id"), "patient_id": meta.get("patient_id"), "score": float(rscore)})

    one_line = (bullets[0][:140] + "...") if bullets else "No notes available"
    return {"one_line": one_line, "bullets": bullets, "sources": sources}


@app.post("/patients/{pid}/qa")
async def ask_question_about_patient(pid: int, question_data: dict, db: Session = Depends(get_db)):
    """
    Q&A endpoint for asking questions about a specific patient.
    This integrates with the RAG system to provide contextual answers based on patient data.
    """
    try:
        # Get patient info
        patient = db.query(Patient).filter(Patient.id == pid).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        question = question_data.get('question', '').strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        # Try to use AI services for more intelligent Q&A responses
        try:
            from rag_prototype import RAGIndex
            r = RAGIndex()
            r.load()
            # Use the question as query to find relevant patient information
            hits = r.query(pid, question, k=5)
            
            # Convert hits to retrieval format for AI processing
            retrieved = []
            print(f"DEBUG Q&A: Found {len(hits)} RAG hits for patient {pid}, question: {question}")
            for score, meta in hits:
                print(f"DEBUG Q&A: Hit score={score:.3f}, snippet={meta.get('text_snippet', '')[:100]}...")
                if score > 0.05:  # Lower threshold to catch more relevant matches
                    retrieved.append({
                        "note_id": meta.get("note_id"),
                        "patient_id": meta.get("patient_id"),
                        "note_date": meta.get("note_date"),
                        "snippet": meta.get("text_snippet"),
                        "score": float(score),
                    })
            print(f"DEBUG Q&A: {len(retrieved)} hits passed threshold")
            
            if retrieved:
                # Try OpenRouter first for AI-powered Q&A with timeout protection
                try:
                    from openrouter_wrapper import generate_json_summary
                    print(f"DEBUG Q&A: Attempting OpenRouter API call with {len(retrieved)} items")
                    
                    # For complex questions like lab results, use faster processing
                    if any(word in question.lower() for word in ['lab', 'test', 'result', 'blood', 'analysis']):
                        print(f"DEBUG Q&A: Detected lab results question - using optimized processing")
                        # Use only top 3 most relevant items for lab results to speed up processing
                        limited_retrieved = retrieved[:3]
                    else:
                        limited_retrieved = retrieved
                    
                    ai_response = generate_json_summary(limited_retrieved, question=question)
                    print(f"DEBUG Q&A: OpenRouter response: {ai_response}")
                    
                    # Extract answer from AI response
                    if isinstance(ai_response, dict) and "one_line" in ai_response:
                        answer = ai_response["one_line"]
                        if "bullets" in ai_response and ai_response["bullets"]:
                            # Limit bullets to prevent overly long responses
                            limited_bullets = ai_response["bullets"][:5]  # Max 5 bullet points
                            answer += " Key points: " + "; ".join(limited_bullets)
                        print(f"DEBUG Q&A: OpenRouter success - final answer length: {len(answer)}")
                    else:
                        answer = f"Based on {patient.name}'s medical records, I found relevant information but had trouble formatting the response."
                        print(f"DEBUG Q&A: OpenRouter response format issue")
                        
                except Exception as or_error:
                    print(f"DEBUG Q&A: OpenRouter Q&A failed: {or_error}")
                    
                    # Try Gemini as fallback
                    try:
                        from gemini_wrapper import generate_json_summary as gemini_generate
                        print(f"DEBUG Q&A: Attempting Gemini API call with {len(retrieved)} items")
                        ai_response = gemini_generate(retrieved[:3], question=question)  # Limit to top 3 for speed
                        print(f"DEBUG Q&A: Gemini response: {ai_response}")
                        # Extract answer from AI response
                        if isinstance(ai_response, dict) and "one_line" in ai_response:
                            answer = ai_response["one_line"]
                            if "bullets" in ai_response and ai_response["bullets"]:
                                # Limit bullets for Gemini too
                                limited_bullets = ai_response["bullets"][:5]
                                answer += " Key points: " + "; ".join(limited_bullets)
                            print(f"DEBUG Q&A: Gemini success - final answer: {answer}")
                        else:
                            answer = f"Based on {patient.name}'s medical records, I found relevant information but had trouble formatting the response."
                            print(f"DEBUG Q&A: Gemini response format issue")
                    except Exception as g_error:
                        print(f"DEBUG Q&A: Gemini Q&A failed: {g_error}")
                        
                        # Fast fallback to simple context extraction
                        print(f"DEBUG Q&A: Using fast fallback - simple context extraction")
                        context_snippets = []
                        for score, meta in hits:
                            if score > 0.2:  # Higher threshold for faster response
                                snippet = meta.get("text_snippet", "")[:200]  # Limit snippet length
                                context_snippets.append(snippet)
                        
                        if context_snippets:
                            context = " ".join(context_snippets[:2])  # Use only top 2 snippets
                            answer = f"Based on {patient.name}'s medical records: {context[:400]}..." if len(context) > 400 else f"Based on {patient.name}'s medical records: {context}"
                            print(f"DEBUG Q&A: Using fallback context answer")
                        else:
                            answer = f"I couldn't find specific information about '{question}' in {patient.name}'s current medical records."
                            print(f"DEBUG Q&A: No context available for fallback")
            else:
                answer = f"I couldn't find specific information about '{question}' in {patient.name}'s current medical records. You may want to add more notes or ask a different question."
                
        except Exception as e:
            # Fallback if RAG system is not available
            print(f"DEBUG Q&A: RAG system error: {e}")
            import traceback
            print(f"DEBUG Q&A: RAG traceback: {traceback.format_exc()}")
            logger.warning(f"RAG system unavailable for Q&A: {e}")
            answer = f"Q&A system is currently unavailable. For questions about {patient.name} (Age: {patient.age}), please review the patient's notes manually or contact the medical team."
        
        print(f"DEBUG Q&A: Final answer being returned: {answer}")
        
        # Ensure we return a valid response structure
        response_data = {
            "question": question,
            "answer": answer if answer else "Unable to process question at this time.",
            "patient_id": pid,
            "patient_name": patient.name
        }
        print(f"DEBUG Q&A: Response structure: {response_data}")
        print(f"DEBUG Q&A: Response size: {len(str(response_data))} characters")
        
        # Truncate extremely long responses to prevent timeout issues
        if len(answer) > 2000:
            truncated_answer = answer[:1800] + "... [Response truncated for performance]"
            response_data["answer"] = truncated_answer
            print(f"DEBUG Q&A: Answer truncated from {len(answer)} to {len(truncated_answer)} characters")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG Q&A: Unexpected error in Q&A endpoint: {e}")
        import traceback
        print(f"DEBUG Q&A: Full traceback: {traceback.format_exc()}")
        logger.error(f"Q&A error for patient {pid}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process question")


# Document Upload and Management Routes
@app.post("/patients/{patient_id}/upload-document")
async def upload_document(
    patient_id: int,
    file: UploadFile = File(...),
    doc_type: Optional[str] = Form("default"),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload and process a medical document with OCR."""
    
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file.content_type} not supported. Allowed: JPEG, PNG, PDF"
        )
    
    try:
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # For now, we'll process the file in memory and store the OCR results
        # In production, you'd want to save files to disk or cloud storage
        file_content = await file.read()
        
        # Create document record
        document = MedicalDocument(
            patient_id=patient_id,
            filename=file.filename,
            original_filename=file.filename,
            file_path=unique_filename,  # This would be actual path in production
            file_type="uploaded_image",  # Document type category
            uploaded_at=datetime.utcnow(),
            processing_status="processing"
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Initialize OCR processor and process the uploaded file
        try:
            ocr_processor = MedicalOCR()
            
            # Save file temporarily for OCR processing (the MedicalOCR expects a file path)
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            # Extract text using OCR
            ocr_result = ocr_processor.extract_text(temp_file_path)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            # Update document with OCR results
            document.processing_status = "completed"
            document.ocr_text = ocr_result['text']
            document.ocr_confidence = ocr_result['confidence']
            document.processed_at = datetime.utcnow()
            
            # Detect document type based on OCR content
            detected_type = ocr_processor.detect_document_type(ocr_result['text'])
            document.file_type = detected_type
            
            # Automatically create a medical note from the OCR text
            try:
                note_id = create_medical_note_from_ocr(
                    patient_id=patient_id,
                    document_id=document.id,
                    filename=file.filename,
                    doc_type=detected_type,
                    ocr_text=ocr_result['text'],
                    confidence=ocr_result['confidence'],
                    db=db
                )
                logger.info(f"Auto-created note {note_id} for document {document.id}")
            except Exception as note_error:
                logger.warning(f"Failed to auto-create note for document {document.id}: {str(note_error)}")
                # Don't fail the upload if note creation fails
            
        except Exception as ocr_error:
            logger.warning(f"OCR processing failed: {str(ocr_error)}")
            # Fallback to basic processing
            document.processing_status = "completed"
            document.ocr_text = f"OCR processing encountered an error: {str(ocr_error)}. Please ensure Tesseract is installed."
            document.ocr_confidence = 0.0
        
        db.commit()
        
        return JSONResponse(content={
            "success": True,
            "message": "Document uploaded successfully",
            "document_id": document.id,
            "status": "completed",
            "ocr_text": document.ocr_text,
            "confidence": document.ocr_confidence,
            "doc_type": document.file_type,
            "processing_status": document.processing_status
        })
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/patients/{patient_id}/documents")
async def list_patient_documents(patient_id: int, db: Session = Depends(get_db)):
    """Get all documents for a patient."""
    
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    documents = db.query(MedicalDocument).filter(MedicalDocument.patient_id == patient_id).all()
    
    return [{
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "original_filename": doc.original_filename,
        "upload_date": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
        "processing_status": doc.processing_status,
        "confidence_score": doc.ocr_confidence
    } for doc in documents]


@app.get("/patients/{patient_id}/documents/{document_id}")
async def get_document_details(patient_id: int, document_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific document."""
    
    document = db.query(MedicalDocument).filter(
        MedicalDocument.id == document_id,
        MedicalDocument.patient_id == patient_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": document.id,
        "filename": document.filename,
        "file_type": document.file_type,
        "original_filename": document.original_filename,
        "upload_date": document.uploaded_at.isoformat() if document.uploaded_at else None,
        "processing_status": document.processing_status,
        "confidence_score": document.ocr_confidence,
        "ocr_text": document.ocr_text,
        "ai_summary": getattr(document, 'ai_summary', None)
    }


@app.post("/patients/{patient_id}/documents/{document_id}/summarize")
async def summarize_document(patient_id: int, document_id: int, db: Session = Depends(get_db)):
    """Generate AI summary for a document."""
    
    document = db.query(MedicalDocument).filter(
        MedicalDocument.id == document_id,
        MedicalDocument.patient_id == patient_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not document.ocr_text:
        raise HTTPException(status_code=400, detail="No OCR text available for summarization")
    
    # For now, return a simple summary
    # In production, you'd use your AI wrapper here
    summary_text = f"AI Summary of {document.filename}: This document contains medical information extracted via OCR."
    
    # Store summary in a note or separate table - for now just return it
    # document.ai_summary = summary_text  # Field doesn't exist in model
    
    return {
        "summary": summary_text,
        "document_id": document.id
    }


@app.delete("/patients/{patient_id}/documents/{document_id}")
async def delete_document(patient_id: int, document_id: int, db: Session = Depends(get_db)):
    """Delete a document."""
    
    document = db.query(MedicalDocument).filter(
        MedicalDocument.id == document_id,
        MedicalDocument.patient_id == patient_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # In production, you'd also delete the actual file from storage
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
