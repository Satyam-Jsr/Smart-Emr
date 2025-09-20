#!/usr/bin/env python
"""
Test script to verify AI configuration for EMR system.
This tests OpenRouter (primary) and Gemini (fallback) integration.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_openrouter():
    """Test OpenRouter wrapper"""
    print("🔄 Testing OpenRouter integration...")
    try:
        from openrouter_wrapper import generate_json_summary
        
        # Sample medical data for testing
        sample_retrieved = [
            {
                "note_id": 1,
                "patient_id": 1,
                "note_date": "2025-09-15",
                "snippet": "Patient presents with chest pain and shortness of breath. Vital signs stable.",
                "score": 0.9,
            },
            {
                "note_id": 2,
                "patient_id": 1,
                "note_date": "2025-09-10",
                "snippet": "Follow-up: Blood pressure controlled with medication. Patient reports feeling better.",
                "score": 0.7,
            }
        ]
        
        # Test summary generation
        summary = generate_json_summary(sample_retrieved)
        print("✅ OpenRouter summary generation successful!")
        print(f"   Source: {summary.get('source', 'openrouter')}")
        print(f"   One-line: {summary.get('one_line', 'N/A')}")
        print(f"   Bullets: {len(summary.get('bullets', []))} items")
        
        # Test Q&A generation
        qa_summary = generate_json_summary(sample_retrieved, question="What are the patient's main symptoms?")
        print("✅ OpenRouter Q&A generation successful!")
        print(f"   Q&A One-line: {qa_summary.get('one_line', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenRouter test failed: {e}")
        return False

def test_gemini():
    """Test Gemini wrapper"""
    print("\n🔄 Testing Gemini integration...")
    try:
        from gemini_wrapper import generate_json_summary
        
        # Sample medical data for testing
        sample_retrieved = [
            {
                "note_id": 3,
                "patient_id": 2,
                "note_date": "2025-09-12",
                "snippet": "Routine checkup. Blood work shows normal glucose levels. Patient healthy.",
                "score": 0.8,
            }
        ]
        
        # Test summary generation
        summary = generate_json_summary(sample_retrieved)
        print("✅ Gemini summary generation successful!")
        print(f"   One-line: {summary.get('one_line', 'N/A')}")
        print(f"   Bullets: {len(summary.get('bullets', []))} items")
        
        # Test Q&A generation
        qa_summary = generate_json_summary(sample_retrieved, question="What were the blood test results?")
        print("✅ Gemini Q&A generation successful!")
        print(f"   Q&A One-line: {qa_summary.get('one_line', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        return False

def test_fallback_order():
    """Test that the fallback order works correctly"""
    print("\n🔄 Testing AI service fallback order...")
    
    # This simulates what happens in the summarize endpoint
    sample_retrieved = [
        {
            "note_id": 4,
            "patient_id": 3,
            "note_date": "2025-09-18",
            "snippet": "Patient diagnosed with hypertension. Started on ACE inhibitor therapy.",
            "score": 0.9,
        }
    ]
    
    services_tried = []
    
    # Try OpenRouter first
    try:
        from openrouter_wrapper import generate_json_summary
        summary = generate_json_summary(sample_retrieved)
        services_tried.append("OpenRouter")
        print("✅ Primary service (OpenRouter) working correctly")
        return services_tried
    except Exception as e:
        print(f"⚠️ OpenRouter failed, trying fallback: {e}")
        services_tried.append("OpenRouter (failed)")
    
    # Try Gemini as fallback
    try:
        from gemini_wrapper import generate_json_summary as gemini_generate
        summary = gemini_generate(sample_retrieved)
        services_tried.append("Gemini")
        print("✅ Fallback service (Gemini) working correctly")
        return services_tried
    except Exception as e:
        print(f"❌ Gemini fallback also failed: {e}")
        services_tried.append("Gemini (failed)")
    
    return services_tried

if __name__ == "__main__":
    print("🏥 EMR AI Configuration Test")
    print("=" * 40)
    
    # Test individual services
    openrouter_ok = test_openrouter()
    gemini_ok = test_gemini()
    
    # Test fallback order
    services_tried = test_fallback_order()
    
    print("\n📊 Test Results Summary:")
    print("=" * 40)
    print(f"OpenRouter (Primary): {'✅ Working' if openrouter_ok else '❌ Failed'}")
    print(f"Gemini (Fallback): {'✅ Working' if gemini_ok else '❌ Failed'}")
    print(f"Service Priority: {' → '.join(services_tried)}")
    
    if openrouter_ok or gemini_ok:
        print("\n🎉 AI configuration is working! At least one service is available.")
        if openrouter_ok:
            print("   Primary service (OpenRouter) is operational.")
        if gemini_ok:
            print("   Fallback service (Gemini) is operational.")
    else:
        print("\n⚠️ Warning: No AI services are working. Check your API keys and configuration.")
    
    print("\nConfiguration details:")
    print(f"   OpenRouter Model: {os.environ.get('OPENROUTER_MODEL', 'Not set')}")
    print(f"   Gemini Model: {os.environ.get('GEMINI_MODEL', 'Not set')}")
    print(f"   OpenRouter API Key: {'Set' if os.environ.get('OPENROUTER_API_KEY') else 'Missing'}")
    print(f"   Gemini API Key: {'Set' if os.environ.get('GEMINI_API_KEY') else 'Missing'}")