"""
Anthropic Claude API wrapper for EMR summarization
Requires paid Anthropic account
"""

import anthropic
import json
from typing import Dict, Any, Optional

class AnthropicWrapper:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        
    def generate_json_summary(self, patient_notes: str) -> Optional[Dict[str, Any]]:
        """Generate a JSON summary using Claude"""
        try:
            prompt = f"""Based on these patient notes, create a brief JSON summary.

Patient Notes:
{patient_notes}

Return ONLY a JSON object with this exact structure:
{{
    "one_line": "Brief one-sentence summary",
    "bullets": ["Key point 1", "Key point 2", "Key point 3"]
}}

Keep it concise and medically accurate."""

            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Most cost-effective
                max_tokens=200,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text.strip()
            return json.loads(content)
            
        except Exception as e:
            print(f"Anthropic generation failed: {e}")
            return None

# Test function
def test_anthropic():
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("No ANTHROPIC_API_KEY found in .env")
        return
        
    wrapper = AnthropicWrapper(api_key)
    
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
    
    print("Testing Anthropic generation...")
    result = wrapper.generate_json_summary(test_notes)
    
    if result:
        print("✅ Anthropic generation successful:")
        print(json.dumps(result, indent=2))
    else:
        print("❌ Anthropic generation failed")

if __name__ == "__main__":
    test_anthropic()