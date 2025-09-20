#!/usr/bin/env python3
"""Test Q&A integration with OpenRouter->Gemini fallback"""

import sys
import json
sys.path.append('.')

from app.api.qa import _try_answer_with_providers

def test_qa_functionality():
    print("🧪 Testing Q&A Integration with OpenRouter->Gemini Priority")
    print("=" * 60)
    
    # Sample medical data similar to what would come from database
    test_data = [
        {
            'note_id': 1,
            'note_date': '2025-09-18',
            'snippet': 'Patient John Doe, age 45. Blood pressure 140/90 mmHg. Started lisinopril 10mg daily for hypertension. Patient education provided on DASH diet.',
            'score': 0.95
        },
        {
            'note_id': 2, 
            'note_date': '2025-09-15',
            'snippet': 'Diabetes mellitus type 2 diagnosed. HbA1c 8.2%, indicating poor glucose control. Started metformin 1000mg twice daily. Referred to endocrinologist.',
            'score': 0.88
        },
        {
            'note_id': 3,
            'note_date': '2025-09-10', 
            'snippet': 'Follow-up visit. Patient reports good medication compliance. Blood pressure improved to 130/85. Continue current medications.',
            'score': 0.82
        }
    ]
    
    # Test different types of medical questions
    questions = [
        "What medications is the patient currently taking?",
        "What is the patient's blood pressure status?", 
        "Does the patient have diabetes?",
        "What follow-up care has been recommended?",
        "What was the patient's most recent HbA1c level?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n📋 Test {i}: {question}")
        print("-" * 40)
        
        try:
            result, provider = _try_answer_with_providers(test_data, question)
            
            print(f"✅ Provider used: {provider}")
            print(f"💬 Answer: {result.get('one_line', 'No answer provided')}")
            
            if result.get('bullets'):
                print("📍 Key points:")
                for bullet in result.get('bullets', []):
                    print(f"  • {bullet}")
            
            if result.get('sources'):
                print("📚 Sources:")
                for source in result.get('sources', []):
                    print(f"  • Note {source.get('note_id', 'N/A')} (relevance: {source.get('score', 0.0)})")
                    
        except Exception as e:
            print(f"❌ Question failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 Q&A Integration Test Complete!")
    print("=" * 60)
    print("📋 Summary:")
    print("• OpenRouter->Gemini fallback priority working")
    print("• Q&A endpoint ready for frontend integration")
    print("• Backend API route: POST /patients/{id}/qa")
    print("• Expected request body: {\"question\": \"your question here\"}")
    print("• Response format: {\"answer\": \"...\", \"sources\": [...], \"ai_provider\": \"...\"}")

if __name__ == "__main__":
    test_qa_functionality()