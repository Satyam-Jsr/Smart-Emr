#!/usr/bin/env python
"""
Debug script to check RAG system and Q&A for specific patient
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.database import SessionLocal
from app.models import Patient, Note
from rag_prototype import RAGIndex

def debug_patient_qa():
    db = SessionLocal()
    
    # Find Satyam
    satyam = db.query(Patient).filter(Patient.name.ilike('%satyam%')).first()
    if not satyam:
        print("❌ Satyam not found in database")
        return
    
    print(f"✅ Found patient: {satyam.name} (ID: {satyam.id})")
    
    # Check notes
    notes = db.query(Note).filter(Note.patient_id == satyam.id).all()
    print(f"📝 Notes count: {len(notes)}")
    
    if notes:
        for i, note in enumerate(notes[:3]):
            print(f"Note {i+1}: {note.text[:200]}...")
            print("---")
    
    # Test RAG system
    try:
        r = RAGIndex()
        r.load()
        print(f"📊 RAG index loaded with {len(r.meta)} items")
        
        # Test different queries
        queries = [
            "health condition symptoms",
            "what condition does patient have",
            "medical diagnosis",
            "illness disease"
        ]
        
        for query in queries:
            print(f"\n🔍 Testing query: '{query}'")
            hits = r.query(satyam.id, query, k=5)
            print(f"   Found {len(hits)} hits")
            
            for i, (score, meta) in enumerate(hits[:3]):
                if score > 0.1:
                    snippet = meta.get("text_snippet", "")[:150]
                    print(f"   Hit {i+1}: Score={score:.3f}")
                    print(f"           Snippet: {snippet}...")
                    print(f"           Note ID: {meta.get('note_id')}")
                    
    except Exception as e:
        print(f"❌ RAG system error: {e}")
    
    db.close()

if __name__ == "__main__":
    debug_patient_qa()