# backend/seed_vitals.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.database import SessionLocal, engine
from app.models import Base, Vital, Patient

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Get existing patients
patients = db.query(Patient).all()

if patients:
    # Add sample vitals for the first patient
    patient_id = patients[0].id
    
    # Add vitals over the last 30 days
    base_date = datetime.now() - timedelta(days=30)
    
    sample_vitals = [
        {"days_ago": 30, "systolic": 120, "diastolic": 80, "heart_rate": 72, "temperature": 36.5, "weight": 70.0},
        {"days_ago": 25, "systolic": 118, "diastolic": 78, "heart_rate": 75, "temperature": 36.7, "weight": 69.8},
        {"days_ago": 20, "systolic": 125, "diastolic": 82, "heart_rate": 68, "temperature": 36.4, "weight": 69.5},
        {"days_ago": 15, "systolic": 122, "diastolic": 79, "heart_rate": 74, "temperature": 36.6, "weight": 69.2},
        {"days_ago": 10, "systolic": 119, "diastolic": 77, "heart_rate": 71, "temperature": 36.5, "weight": 69.0},
        {"days_ago": 5, "systolic": 117, "diastolic": 75, "heart_rate": 73, "temperature": 36.8, "weight": 68.8},
        {"days_ago": 1, "systolic": 121, "diastolic": 78, "heart_rate": 70, "temperature": 36.6, "weight": 68.5},
    ]
    
    for vital_data in sample_vitals:
        vital_date = base_date + timedelta(days=vital_data["days_ago"])
        
        # Check if vital already exists for this date
        existing = db.query(Vital).filter(
            Vital.patient_id == patient_id,
            Vital.date.between(vital_date, vital_date + timedelta(hours=1))
        ).first()
        
        if not existing:
            vital = Vital(
                patient_id=patient_id,
                date=vital_date,
                systolic=vital_data["systolic"],
                diastolic=vital_data["diastolic"],
                heart_rate=vital_data["heart_rate"],
                temperature=vital_data["temperature"],
                weight=vital_data["weight"],
                height=175.0  # Static height
            )
            db.add(vital)
    
    db.commit()
    print(f"Added sample vitals for patient {patient_id}")
else:
    print("No patients found. Please create patients first.")

db.close()