from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import Patient
from app.database import SessionLocal, init_db
from app.schemas import PatientSchema, PatientCreate
from typing import List

# Ensure DB tables exist when module is imported in dev
init_db()

router = APIRouter()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=PatientSchema)
@router.post("", response_model=PatientSchema)
def create_patient(patient_in: PatientCreate, db: Session = Depends(get_db)):
    patient = Patient(name=patient_in.name, age=patient_in.age)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient

# Get a patient by ID
@router.get("/{patient_id}")
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.get("/", response_model=List[PatientSchema])
@router.get("", response_model=List[PatientSchema])
def list_patients(db: Session = Depends(get_db)):
    return db.query(Patient).all()

@router.put("/{patient_id}", response_model=PatientSchema)
@router.put("/{patient_id}/", response_model=PatientSchema)
def update_patient(patient_id: int, patient_data: PatientCreate, db: Session = Depends(get_db)):
    db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Update fields
    # Support both pydantic v1 (.dict()) and v2 (.model_dump())
    try:
        data = patient_data.model_dump()
    except Exception:
        data = getattr(patient_data, "dict", lambda: {})()

    for key, value in data.items():
        setattr(db_patient, key, value)
    
    db.commit()
    db.refresh(db_patient)
    return db_patient

# Delete patient
@router.delete("/{patient_id}")
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(patient)
    db.commit()
    return {"status": "deleted"}