"""Test script for GPT4All wrapper.

This will test local model generation for EMR summarization.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_gpt4all():
    try:
        from gpt4all_wrapper import generate_json_summary, model_info, list_available_models
        
        print("GPT4All Model Info:")
        info = model_info()
        for key, value in info.items():
            print(f"  {key}: {value}")
        print()
        
        # Test with sample medical data
        sample_retrieved = [
            {
                "note_id": 1,
                "patient_id": 1,
                "note_date": "2025-01-15",
                "snippet": "Patient reports persistent headaches and elevated blood pressure readings at home.",
                "score": 0.95
            },
            {
                "note_id": 2,
                "patient_id": 1,
                "note_date": "2025-01-10",
                "snippet": "Blood pressure 150/90, patient complains of morning headaches, prescribed medication.",
                "score": 0.88
            }
        ]
        
        print("Testing GPT4All generation...")
        print("Input snippets:")
        for r in sample_retrieved:
            print(f"  Note {r['note_id']}: {r['snippet']}")
        print()
        
        summary = generate_json_summary(sample_retrieved)
        
        print("Generated Summary:")
        print(f"  One-line: {summary.get('one_line')}")
        print(f"  Bullets:")
        for bullet in summary.get('bullets', []):
            print(f"    • {bullet}")
        print(f"  Sources: {len(summary.get('sources', []))} notes referenced")
        print(f"  Source: {summary.get('source', 'gpt4all')}")
        
        return True
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("\nTo install GPT4All:")
        print("  pip install gpt4all")
        return False
        
    except Exception as e:
        print(f"Test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Show available models if model loading failed
        try:
            print("\nAvailable models for download:")
            models = list_available_models()
            for i, model in enumerate(models[:10]):  # Show first 10
                print(f"  {i+1}. {model}")
            if len(models) > 10:
                print(f"  ... and {len(models)-10} more")
        except Exception:
            pass
            
        return False


if __name__ == "__main__":
    print("GPT4All EMR Test")
    print("=" * 50)
    
    success = test_gpt4all()
    
    if success:
        print("\n✅ GPT4All test successful!")
        print("\nNow the EMR app will use this priority:")
        print("  1. Cohere (if generation key works)")
        print("  2. Hugging Face (if API access available)")
        print("  3. GPT4All (local, private)")
        print("  4. Mock summary (fallback)")
    else:
        print("\n❌ GPT4All test failed")
        print("\nInstall with: pip install gpt4all")
        print("First run will download ~4GB model file")