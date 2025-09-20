"""Quick comparison test between GPT4All and Ollama for clinical summarization.

Run this when you have adequate memory available (after closing apps/restarting).
"""
import time
import json

def test_clinical_comparison():
    # Sample clinical note for testing
    test_note = [
        {
            "note_id": 1,
            "note_date": "2025-01-15",
            "snippet": "Patient reports persistent chest pain, started on metoprolol 50mg daily. Blood pressure improved from 160/95 to 140/85 over 2 weeks. Patient tolerating medication well, no side effects reported.",
            "score": 0.95
        }
    ]
    
    print("=== Clinical AI Model Comparison ===")
    print("Test case: Hypertension management with chest pain")
    print(f"Input: {test_note[0]['snippet']}")
    print("\n" + "="*60)
    
    # Test GPT4All
    print("\n🔹 Testing GPT4All...")
    try:
        from gpt4all_wrapper import generate_json_summary as gpt4all_generate
        start_time = time.time()
        gpt4all_result = gpt4all_generate(test_note)
        gpt4all_time = time.time() - start_time
        
        print(f"⏱️  Time: {gpt4all_time:.1f} seconds")
        print(f"📋 One-line: {gpt4all_result.get('one_line')}")
        print("📝 Bullets:")
        for i, bullet in enumerate(gpt4all_result.get('bullets', []), 1):
            print(f"   {i}. {bullet}")
        print(f"🔧 Source: {gpt4all_result.get('source', 'gpt4all')}")
        
    except Exception as e:
        print(f"❌ GPT4All failed: {e}")
        gpt4all_result = None
        gpt4all_time = None
    
    print("\n" + "-"*60)
    
    # Test Ollama
    print("\n🔹 Testing Ollama (LLaMA-7B)...")
    try:
        from ollama_wrapper import generate_json_summary as ollama_generate
        start_time = time.time()
        ollama_result = ollama_generate(test_note)
        ollama_time = time.time() - start_time
        
        print(f"⏱️  Time: {ollama_time:.1f} seconds")
        print(f"📋 One-line: {ollama_result.get('one_line')}")
        print("📝 Bullets:")
        for i, bullet in enumerate(ollama_result.get('bullets', []), 1):
            print(f"   {i}. {bullet}")
        print(f"🔧 Source: {ollama_result.get('source', 'ollama')}")
        
    except Exception as e:
        print(f"❌ Ollama failed: {e}")
        ollama_result = None
        ollama_time = None
    
    print("\n" + "="*60)
    print("\n📊 COMPARISON SUMMARY:")
    
    if gpt4all_time and ollama_time:
        print(f"⏱️  Speed: GPT4All {gpt4all_time:.1f}s vs Ollama {ollama_time:.1f}s")
        print(f"🏃 Winner: {'GPT4All' if gpt4all_time < ollama_time else 'Ollama'} (faster)")
    
    print("\n🎯 Quality Assessment (Manual Review Needed):")
    print("   - Medical accuracy: Which captured the clinical details better?")
    print("   - Completeness: Which included more relevant information?")
    print("   - Professional tone: Which sounds more clinical?")
    print("   - Factual accuracy: Which avoided adding unsupported information?")
    
    print("\n💡 Recommendation:")
    if gpt4all_time and ollama_time:
        if ollama_time < 10:  # Acceptable speed
            print("   Use Ollama for better clinical quality (if memory allows)")
        else:
            print("   Use GPT4All for acceptable speed-quality balance")
    else:
        print("   Stick with mock summaries for reliable demo performance")

if __name__ == "__main__":
    print("Clinical AI Model Comparison")
    print("⚠️  Warning: This test requires 4-6GB free RAM")
    print("Close other applications before running.\n")
    
    # Check if we should proceed
    try:
        import psutil
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        print(f"Available RAM: {available_gb:.1f}GB")
        
        if available_gb < 3:
            print("❌ Insufficient memory. Close apps and try again.")
            exit(1)
        elif available_gb < 5:
            print("⚠️  Low memory. GPT4All only recommended.")
        else:
            print("✅ Sufficient memory for both tests.")
    except ImportError:
        print("⚠️  Cannot check memory. Proceed with caution.")
    
    print()
    test_clinical_comparison()