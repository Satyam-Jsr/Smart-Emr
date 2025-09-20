# backend/app/api/notes.py
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db   # get_db helper (or define below)
from app.models import Note, Patient

router = APIRouter()

# If you don't already have get_db in database.py, uncomment this:
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

class NoteIn(BaseModel):
    text: str
    note_date: Optional[datetime] = None

class NoteOut(BaseModel):
    id: int
    patient_id: int
    note_date: datetime
    text: str

    class Config:
        orm_mode = True

@router.get("/{patient_id}/notes", response_model=List[NoteOut])
def list_notes(patient_id: int, db: Session = Depends(get_db)):
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    notes = db.query(Note).filter(Note.patient_id == patient_id).order_by(Note.note_date.desc()).all()
    return notes

@router.post("/{patient_id}/notes", response_model=NoteOut)
def create_note(patient_id: int, note_in: NoteIn, db: Session = Depends(get_db)):
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    note_date = note_in.note_date or datetime.utcnow()
    note = Note(patient_id=patient_id, note_date=note_date, text=note_in.text)
    db.add(note)
    db.commit()
    db.refresh(note)

    # TODO: trigger indexing (index_note(note.id, patient_id, note.text)) — can be async/worker later

    return note

class NoteUpdate(BaseModel):
    text: str

@router.put("/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: int, note_update: NoteUpdate, db: Session = Depends(get_db)):
    # Find the note
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Update the note text
    note.text = note_update.text
    db.commit()
    db.refresh(note)
    
    return note

@router.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    # Find the note
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Delete the note
    db.delete(note)
    db.commit()
    
    return {"message": "Note deleted successfully"}
