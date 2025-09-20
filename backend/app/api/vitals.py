# backend/app/api/vitals.py
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Vital, Patient

router = APIRouter()

class VitalIn(BaseModel):
    date: Optional[datetime] = None
    systolic: Optional[int] = None
    diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    temperature: Optional[float] = None
    weight: Optional[float] = None
    height: Optional[float] = None

class VitalOut(BaseModel):
    id: int
    patient_id: int
    date: datetime
    systolic: Optional[int] = None
    diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    temperature: Optional[float] = None
    weight: Optional[float] = None
    height: Optional[float] = None

    class Config:
        orm_mode = True

@router.get("/vitals", response_model=List[VitalOut])
def get_vitals(
    patient_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get vitals, optionally filtered by patient_id"""
    query = db.query(Vital)
    if patient_id:
        query = query.filter(Vital.patient_id == patient_id)
    vitals = query.order_by(Vital.date.asc()).all()
    return vitals

@router.post("/{patient_id}/vitals", response_model=VitalOut)
def create_vital(patient_id: int, vital_in: VitalIn, db: Session = Depends(get_db)):
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    vital_date = vital_in.date or datetime.utcnow()
    vital = Vital(
        patient_id=patient_id,
        date=vital_date,
        systolic=vital_in.systolic,
        diastolic=vital_in.diastolic,
        heart_rate=vital_in.heart_rate,
        temperature=vital_in.temperature,
        weight=vital_in.weight,
        height=vital_in.height
    )
    db.add(vital)
    db.commit()
    db.refresh(vital)

    return vital

@router.get("/{patient_id}/vitals", response_model=List[VitalOut])
def get_patient_vitals(patient_id: int, db: Session = Depends(get_db)):
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    vitals = db.query(Vital).filter(Vital.patient_id == patient_id).order_by(Vital.date.asc()).all()
    return vitals