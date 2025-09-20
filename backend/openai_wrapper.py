"""
OpenAI API wrapper for EMR summarization
Requires paid OpenAI account with API access
"""

import openai
import json
from typing import Dict, Any, Optional

class OpenAIWrapper:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        
    def generate_json_summary(self, patient_notes: str) -> Optional[Dict[str, Any]]:
        """Generate a JSON summary using OpenAI's GPT models"""
        try:
            prompt = f"""You are a medical AI assistant. Based on these patient notes, create a brief JSON summary.

Patient Notes:
{patient_notes}

Return ONLY a JSON object with this exact structure:
{{
    "one_line": "Brief one-sentence summary",
    "bullets": ["Key point 1", "Key point 2", "Key point 3"]
}}

Keep it concise and medically accurate."""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Cheapest option
                messages=[
                    {"role": "system", "content": "You are a medical summarization assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            return json.loads(content)
            
        except Exception as e:
            print(f"OpenAI generation failed: {e}")
            return None

# Test function
def test_openai():
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("No OPENAI_API_KEY found in .env")
        return
        
    wrapper = OpenAIWrapper(api_key)
    
    test_notes = """
    Patient: John Doe, Age: 45
    Chief Complaint: Chest pain and shortness of breath
    
    Visit 1 (2024-01-15):
    Patient reports chest pain that started 2 days ago. Pain is described as sharp, 
    located in the center of chest. Associated with mild shortness of breath.
    Vital signs stable. ECG shows normal sinus rhythm.
    
    Visit 2 (2024-01-20):
    Follow-up for chest pain. Patient reports improvement with prescribed medication.
    Still experiencing occasional shortness of breath with exertion.
    """
    
    print("Testing OpenAI generation...")
    result = wrapper.generate_json_summary(test_notes)
    
    if result:
        print("✅ OpenAI generation successful:")
        print(json.dumps(result, indent=2))
    else:
        print("❌ OpenAI generation failed")

if __name__ == "__main__":
    test_openai()