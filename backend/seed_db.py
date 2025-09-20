# backend/seed_db.py
from datetime import datetime, timedelta
from app.database import SessionLocal, init_db
from app.models import Patient, Note

def seed():
    init_db()  # create tables if missing
    db = SessionLocal()
    try:
        # clear existing (optional for dev)
        db.query(Note).delete()
        db.query(Patient).delete()
        db.commit()

        # Create a demo patient
        patient = Patient(name="Aisha Kumar", age=52)
        db.add(patient)
        db.commit()
        db.refresh(patient)

        # Create several notes with dates that show a trend
        base_date = datetime(2025, 8, 1)
        notes_texts = [
            "2025-08-01: BP 130/80. No complaints.",
            "2025-08-15: BP 138/84. Mild headache reported.",
            "2025-09-01: BP 145/88. Patient reports medication missed once a week.",
            "2025-09-10: BP 150/92. Recommend care review; possible med escalation.",
            "2025-09-14: CXR shows small right lower lobe infiltrate. Start azithromycin.",
            "2025-09-20: Cough improving, still short of breath on exertion."
        ]

        for i, txt in enumerate(notes_texts):
            note_date = base_date + timedelta(days=15 * i)
            n = Note(patient_id=patient.id, note_date=note_date, text=txt)
            db.add(n)

        db.commit()
        print(f"Seeded patient id={patient.id} with {len(notes_texts)} notes.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
