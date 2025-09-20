from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    age = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    note_date = Column(DateTime, default=datetime.utcnow)
    text = Column(Text)

class MedicalDocument(Base):
    __tablename__ = "medical_documents"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    filename = Column(String)
    original_filename = Column(String)
    file_path = Column(String)
    file_type = Column(String)  # 'lab_report', 'xray', 'blood_test', 'prescription', etc.
    ocr_text = Column(Text)
    ocr_confidence = Column(Float)
    processing_status = Column(String, default='pending')  # 'pending', 'processing', 'completed', 'failed'
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)

class AIOutput(Base):
    __tablename__ = "ai_outputs"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer)
    endpoint = Column(String)
    prompt = Column(Text)
    response = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class SummaryCache(Base):
    __tablename__ = "summary_cache"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, index=True)
    source = Column(String)  # e.g., 'cohere' or 'huggingface' or 'mock'
    summary_json = Column(Text)  # stored as JSON text
    updated_at = Column(DateTime, default=datetime.utcnow)

class Vital(Base):
    __tablename__ = "vitals"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    date = Column(DateTime, default=datetime.utcnow)
    systolic = Column(Integer)  # Blood pressure systolic
    diastolic = Column(Integer)  # Blood pressure diastolic
    heart_rate = Column(Integer)
    temperature = Column(Float)  # In Celsius
    weight = Column(Float)  # In kg
    height = Column(Float)  # In cm
