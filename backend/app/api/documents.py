"""
Document upload API for medical images and OCR processing.
"""

import os
import uuid
import asyncio
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Patient, MedicalDocument, Note
from medical_ocr import MedicalOCR
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Create uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf', '.tiff', '.bmp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

ocr_processor = MedicalOCR()

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and \
           '.' + filename.rsplit('.', 1)[1].lower() in {ext[1:] for ext in ALLOWED_EXTENSIONS}

@router.post("/{patient_id}/upload-document")
async def upload_medical_document(
    patient_id: int,
    file: UploadFile = File(...),
    doc_type: str = Form("default"),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    """
    Upload medical document image and process with OCR.
    
    Args:
        patient_id: ID of the patient
        file: Uploaded image file
        doc_type: Type of document (lab_report, xray, prescription, blood_test, default)
        description: Optional description of the document
    """
    try:
        # Verify patient exists
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        if not allowed_file(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large. Maximum size: 10MB")
        
        # Generate unique filename
        file_extension = '.' + file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{patient_id}_{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Create database record
        doc_record = MedicalDocument(
            patient_id=patient_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_type=doc_type,
            processing_status='pending'
        )
        
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)
        
        # Process OCR asynchronously
        try:
            doc_record.processing_status = 'processing'
            db.commit()
            
            # Extract text using OCR
            ocr_result = ocr_processor.extract_text(file_path, doc_type)
            
            if ocr_result['success']:
                # Update document with OCR results
                doc_record.ocr_text = ocr_result['text']
                doc_record.ocr_confidence = ocr_result['confidence']
                doc_record.processing_status = 'completed'
                doc_record.processed_at = datetime.utcnow()
                
                # Auto-detect document type if not specified
                if doc_type == 'default' and ocr_result['text']:
                    detected_type = ocr_processor.detect_document_type(ocr_result['text'])
                    doc_record.file_type = detected_type
                
                # Create a note with the extracted text
                if ocr_result['text']:
                    note_text = f"[Uploaded Document: {file.filename}]\n"
                    if description:
                        note_text += f"Description: {description}\n"
                    note_text += f"Document Type: {doc_record.file_type}\n"
                    note_text += f"OCR Confidence: {ocr_result['confidence']:.1f}%\n\n"
                    note_text += ocr_result['text']
                    
                    note = Note(
                        patient_id=patient_id,
                        text=note_text
                    )
                    db.add(note)
                
                db.commit()
                
                return {
                    "success": True,
                    "document_id": doc_record.id,
                    "filename": file.filename,
                    "doc_type": doc_record.file_type,
                    "ocr_text": ocr_result['text'][:500] + "..." if len(ocr_result['text']) > 500 else ocr_result['text'],
                    "full_text": ocr_result['text'],
                    "confidence": ocr_result['confidence'],
                    "word_count": ocr_result.get('word_count', 0),
                    "processing_status": "completed",
                    "message": "Document uploaded and processed successfully"
                }
            
            else:
                # OCR failed
                doc_record.processing_status = 'failed'
                doc_record.processed_at = datetime.utcnow()
                db.commit()
                
                return {
                    "success": False,
                    "document_id": doc_record.id,
                    "filename": file.filename,
                    "processing_status": "failed",
                    "error": ocr_result.get('error', 'OCR processing failed'),
                    "message": "Document uploaded but OCR processing failed"
                }
        
        except Exception as ocr_error:
            logger.error(f"OCR processing error: {ocr_error}")
            doc_record.processing_status = 'failed'
            doc_record.processed_at = datetime.utcnow()
            db.commit()
            
            return {
                "success": False,
                "document_id": doc_record.id,
                "filename": file.filename,
                "processing_status": "failed",
                "error": str(ocr_error),
                "message": "Document uploaded but processing failed"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/{patient_id}/documents")
async def get_patient_documents(patient_id: int, db: Session = Depends(get_db)):
    """Get all uploaded documents for a patient."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    documents = db.query(MedicalDocument).filter(
        MedicalDocument.patient_id == patient_id
    ).order_by(MedicalDocument.uploaded_at.desc()).all()
    
    return [
        {
            "id": doc.id,
            "original_filename": doc.original_filename,
            "file_type": doc.file_type,
            "processing_status": doc.processing_status,
            "ocr_confidence": doc.ocr_confidence,
            "uploaded_at": doc.uploaded_at.isoformat(),
            "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
            "has_text": bool(doc.ocr_text),
            "text_preview": doc.ocr_text[:200] + "..." if doc.ocr_text and len(doc.ocr_text) > 200 else doc.ocr_text
        }
        for doc in documents
    ]

@router.get("/{patient_id}/documents/{document_id}")
async def get_document_details(patient_id: int, document_id: int, db: Session = Depends(get_db)):
    """Get full details of a specific document."""
    document = db.query(MedicalDocument).filter(
        MedicalDocument.id == document_id,
        MedicalDocument.patient_id == patient_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": document.id,
        "patient_id": document.patient_id,
        "original_filename": document.original_filename,
        "file_type": document.file_type,
        "processing_status": document.processing_status,
        "ocr_text": document.ocr_text,
        "ocr_confidence": document.ocr_confidence,
        "uploaded_at": document.uploaded_at.isoformat(),
        "processed_at": document.processed_at.isoformat() if document.processed_at else None
    }

@router.post("/{patient_id}/documents/{document_id}/summarize")
async def summarize_document(patient_id: int, document_id: int, db: Session = Depends(get_db)):
    """Generate AI summary of a specific document."""
    document = db.query(MedicalDocument).filter(
        MedicalDocument.id == document_id,
        MedicalDocument.patient_id == patient_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not document.ocr_text:
        raise HTTPException(status_code=400, detail="No text available for summarization")
    
    try:
        # Prepare data for AI summarization (using existing infrastructure)
        from app.api.summarize import _try_generate_summary_with_providers
        
        retrieved = [{
            "note_id": f"doc_{document.id}",
            "note_date": document.uploaded_at.isoformat() if document.uploaded_at else "",
            "snippet": document.ocr_text,
            "score": document.ocr_confidence / 100.0 if document.ocr_confidence else 0.8
        }]
        
        summary, provider = _try_generate_summary_with_providers(retrieved)
        
        return {
            "success": True,
            "document_id": document.id,
            "summary": summary,
            "ai_provider": provider,
            "source_confidence": document.ocr_confidence
        }
    
    except Exception as e:
        logger.error(f"Document summarization error: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

@router.delete("/{patient_id}/documents/{document_id}")
async def delete_document(patient_id: int, document_id: int, db: Session = Depends(get_db)):
    """Delete a document and its associated file."""
    document = db.query(MedicalDocument).filter(
        MedicalDocument.id == document_id,
        MedicalDocument.patient_id == patient_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Delete file from filesystem
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete from database
        db.delete(document)
        db.commit()
        
        return {"success": True, "message": "Document deleted successfully"}
    
    except Exception as e:
        logger.error(f"Document deletion error: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")