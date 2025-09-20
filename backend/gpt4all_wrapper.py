"""GPT4All local model wrapper for EMR summarization.

This provides a local alternative to cloud-based generation services.
Keeps all medical data private and works offline.

Requirements:
    pip install gpt4all

Usage:
    from gpt4all_wrapper import generate_json_summary
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

# Configuration
GPT4ALL_MODEL = os.environ.get("GPT4ALL_MODEL", "mistral-7b-instruct-v0.1.Q4_0.gguf")
GPT4ALL_MAX_TOKENS = int(os.environ.get("GPT4ALL_MAX_TOKENS", "150"))
GPT4ALL_TEMPERATURE = float(os.environ.get("GPT4ALL_TEMPERATURE", "0.1"))
GPT4ALL_DEVICE = os.environ.get("GPT4ALL_DEVICE", "cpu")

# Global model instance for reuse
_model = None


def _get_model():
    """Get or initialize the GPT4All model."""
    global _model
    if _model is None:
        try:
            from gpt4all import GPT4All
            print(f"Loading GPT4All model: {GPT4ALL_MODEL}")
            _model = GPT4All(GPT4ALL_MODEL, device=GPT4ALL_DEVICE)
            print("Model loaded successfully")
        except ImportError:
            raise RuntimeError("GPT4All not installed. Run: pip install gpt4all")
        except Exception as e:
            raise RuntimeError(f"Failed to load GPT4All model {GPT4ALL_MODEL}: {e}")
    return _model


def generate_json_summary(retrieved: List[Dict[str, Any]], question: Optional[str] = None) -> Dict[str, Any]:
    """Generate a JSON summary using GPT4All local model.
    
    Args:
        retrieved: List of retrieved note snippets with metadata
        question: Optional question to focus the summary
        
    Returns:
        Dict with keys: one_line, bullets, sources
    """
    model = _get_model()
    
    # Build context from retrieved snippets
    snippet_lines = []
    sources = []
    
    for r in retrieved:
        note_id = r.get("note_id")
        date = r.get("note_date", "")
        snippet = (r.get("snippet") or "").strip().replace("\n", " ")
        score = r.get("score", 0.0)
        
        snippet_lines.append(f"Note {note_id} ({date}): {snippet}")
        sources.append({"note_id": note_id, "score": float(score)})
    
    context = "\n".join(snippet_lines[:5])  # Limit context for speed
    question_text = f"Question: {question}\n\n" if question else ""
    
    # Optimized prompt for medical summarization
    prompt = f"""You are a medical assistant. Read these clinical notes and create a JSON summary.

{question_text}Clinical Notes:
{context}

Create a JSON response with exactly these keys:
- "one_line": A single sentence summary (max 15 words)
- "bullets": Array of 2-4 key points (each max 10 words)
- "sources": Array of {{"note_id": int, "score": float}}

Respond with ONLY the JSON object, no other text:"""

    try:
        # Generate with conservative settings for consistent output
        with model.chat_session():
            response = model.generate(
                prompt=prompt,
                max_tokens=GPT4ALL_MAX_TOKENS,
                temp=GPT4ALL_TEMPERATURE,
                top_k=1,  # More deterministic
                top_p=0.1,  # More focused
                repeat_penalty=1.1
            )
        
        # Extract JSON from response
        response = response.strip()
        
        # Find JSON object boundaries
        start = response.find("{")
        end = response.rfind("}")
        
        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"No JSON found in response: {response[:200]}")
        
        json_text = response[start:end+1]
        parsed = json.loads(json_text)
        
        # Validate and clean response
        if not isinstance(parsed, dict):
            raise ValueError("Response is not a JSON object")
        
        # Ensure required keys
        one_line = str(parsed.get("one_line", "")).strip()
        bullets = parsed.get("bullets", [])
        
        if not one_line:
            one_line = "Clinical summary not available"
        
        if not isinstance(bullets, list):
            bullets = [str(bullets)] if bullets else []
        
        # Limit bullet points and length
        bullets = [str(b).strip()[:100] for b in bullets[:4]]
        bullets = [b for b in bullets if b]  # Remove empty
        
        if not bullets:
            bullets = ["No key findings identified"]
        
        return {
            "one_line": one_line[:200],  # Reasonable limit
            "bullets": bullets,
            "sources": sources
        }
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from GPT4All: {e}\nResponse: {response[:300]}")
    except Exception as e:
        raise RuntimeError(f"GPT4All generation failed: {e}")


def list_available_models() -> List[str]:
    """List models available for download."""
    try:
        from gpt4all import GPT4All
        return GPT4All.list_models()
    except ImportError:
        return ["GPT4All not installed"]


def model_info() -> Dict[str, Any]:
    """Get info about the current model configuration."""
    return {
        "model": GPT4ALL_MODEL,
        "max_tokens": GPT4ALL_MAX_TOKENS,
        "temperature": GPT4ALL_TEMPERATURE,
        "device": GPT4ALL_DEVICE,
        "loaded": _model is not None
    }


if __name__ == "__main__":
    # Simple test
    test_data = [
        {
            "note_id": 1,
            "note_date": "2025-01-01",
            "snippet": "Patient reports chest pain and shortness of breath. Vital signs stable.",
            "score": 0.9
        }
    ]
    
    try:
        result = generate_json_summary(test_data)
        print("Test successful!")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Test failed: {e}")
        print("\nAvailable models:")
        for model in list_available_models()[:5]:
            print(f"  - {model}")