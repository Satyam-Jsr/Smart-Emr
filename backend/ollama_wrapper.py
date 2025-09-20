"""Ollama wrapper for EMR summarization using LLaMA-7B quantized models.

Ollama provides easy access to quantized LLaMA models optimized for local CPU inference.
This should give better quality than GPT4All for clinical summarization.

Requirements:
    1. Download Ollama: https://ollama.ai
    2. Run: ollama pull llama2:7b-chat
    3. Ensure Ollama service is running

Usage:
    from ollama_wrapper import generate_json_summary
"""
from __future__ import annotations

import json
import os
import requests
from typing import Any, Dict, List, Optional

# Configuration
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama2:7b-chat")
OLLAMA_MAX_TOKENS = int(os.environ.get("OLLAMA_MAX_TOKENS", "200"))
OLLAMA_TEMPERATURE = float(os.environ.get("OLLAMA_TEMPERATURE", "0.1"))


def _check_ollama_running() -> bool:
    """Check if Ollama service is running."""
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def _call_ollama(prompt: str) -> str:
    """Call Ollama API for text generation."""
    if not _check_ollama_running():
        raise RuntimeError(f"Ollama not running. Start with: ollama serve")
    
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": OLLAMA_TEMPERATURE,
            "num_predict": OLLAMA_MAX_TOKENS,
            "top_k": 10,
            "top_p": 0.3,
            "repeat_penalty": 1.1
        }
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        return result.get("response", "").strip()
    except Exception as e:
        raise RuntimeError(f"Ollama generation failed: {e}")


def generate_json_summary(retrieved: List[Dict[str, Any]], question: Optional[str] = None) -> Dict[str, Any]:
    """Generate a JSON summary using Ollama LLaMA model.
    
    Optimized for clinical accuracy and factual grounding.
    
    Args:
        retrieved: List of retrieved note snippets with metadata
        question: Optional question to focus the summary
        
    Returns:
        Dict with keys: one_line, bullets, sources
    """
    # Build context from retrieved snippets (limit for memory)
    context_lines = []
    sources = []
    
    for i, r in enumerate(retrieved[:5]):  # Limit to top 5 for memory
        note_id = r.get("note_id")
        date = r.get("note_date", "")
        snippet = (r.get("snippet") or "").strip()
        score = r.get("score", 0.0)
        
        context_lines.append(f"[Note {note_id}, {date}]: {snippet}")
        sources.append({"note_id": note_id, "score": float(score)})
    
    context = "\n".join(context_lines)
    question_text = f"\nSpecific question: {question}" if question else ""
    
    # Clinical-focused prompt optimized for LLaMA instruction format
    prompt = f"""<s>[INST] You are a medical assistant. Analyze these clinical note excerpts and create a factual summary. Do NOT invent or assume information not present in the notes.

Clinical Note Excerpts:
{context}{question_text}

Create a JSON response with exactly these fields:
- "one_line": Single factual sentence (max 15 words)
- "bullets": Array of 2-4 key clinical facts (each max 12 words)  
- "sources": Array of {{"note_id": int, "score": float}}

Rules:
- Only include facts explicitly stated in the notes
- If insufficient information, state "Limited information available"
- Use medical terminology appropriately
- Be concise and precise

Respond with ONLY the JSON object: [/INST]"""

    try:
        response = _call_ollama(prompt)
        
        # Extract JSON from response
        start = response.find("{")
        end = response.rfind("}")
        
        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"No JSON found in response: {response[:200]}")
        
        json_text = response[start:end+1]
        parsed = json.loads(json_text)
        
        # Validate and clean response
        if not isinstance(parsed, dict):
            raise ValueError("Response is not a JSON object")
        
        # Ensure required keys and reasonable content
        one_line = str(parsed.get("one_line", "")).strip()
        bullets = parsed.get("bullets", [])
        
        if not one_line or len(one_line) < 5:
            one_line = "Clinical summary requires more detailed notes"
        
        if not isinstance(bullets, list):
            bullets = [str(bullets)] if bullets else []
        
        # Clean and limit bullets
        bullets = [str(b).strip() for b in bullets[:4]]
        bullets = [b for b in bullets if b and len(b) > 3]  # Remove very short/empty
        
        if not bullets:
            bullets = ["Detailed clinical information not available in provided notes"]
        
        return {
            "one_line": one_line[:150],  # Reasonable limit
            "bullets": bullets,
            "sources": sources
        }
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from Ollama: {e}\nResponse: {response[:300]}")
    except Exception as e:
        raise RuntimeError(f"Ollama generation failed: {e}")


def list_available_models() -> List[str]:
    """List models available in Ollama."""
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return [model["name"] for model in data.get("models", [])]
        return []
    except Exception:
        return ["Ollama not available"]


def model_info() -> Dict[str, Any]:
    """Get info about the current model configuration."""
    return {
        "host": OLLAMA_HOST,
        "model": OLLAMA_MODEL,
        "max_tokens": OLLAMA_MAX_TOKENS,
        "temperature": OLLAMA_TEMPERATURE,
        "running": _check_ollama_running(),
        "available_models": list_available_models()
    }


if __name__ == "__main__":
    # Test with clinical data
    test_data = [
        {
            "note_id": 1,
            "note_date": "2025-01-15",
            "snippet": "Patient reports persistent headaches, BP 150/90, started on lisinopril 10mg daily.",
            "score": 0.95
        },
        {
            "note_id": 2,
            "note_date": "2025-01-10", 
            "snippet": "Morning headaches continue, patient compliance good with new medication regimen.",
            "score": 0.88
        }
    ]
    
    try:
        print("Ollama Model Info:")
        info = model_info()
        for key, value in info.items():
            print(f"  {key}: {value}")
        print()
        
        if not info["running"]:
            print("❌ Ollama not running. Please:")
            print("  1. Download from https://ollama.ai")
            print("  2. Run: ollama serve")
            print("  3. Run: ollama pull llama2:7b-chat")
        else:
            print("Testing Ollama generation...")
            result = generate_json_summary(test_data)
            print("✅ Success!")
            print(json.dumps(result, indent=2))
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("\nSetup instructions:")
        print("  1. Install Ollama: https://ollama.ai")
        print("  2. Start service: ollama serve")
        print("  3. Download model: ollama pull llama2:7b-chat")