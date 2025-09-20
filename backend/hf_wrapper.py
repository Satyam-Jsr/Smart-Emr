"""Minimal Hugging Face inference adapter for generation + JSON parsing.

Usage:
    from hf_wrapper import generate_json_summary

Requires HF_API_KEY in environment and an HF model id in HF_GEN_MODEL.
"""
from __future__ import annotations

import json
import os
import requests
try:
    from huggingface_hub import InferenceClient
except Exception:
    InferenceClient = None
from typing import Any, Dict, List, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, skip loading .env file
    pass

HF_API_KEY = os.environ.get("HF_TOKEN")  # Fixed to match .env file
# Default to flan-t5-small for compact instruction-tuned generation
HF_GEN_MODEL = os.environ.get("HF_GEN_MODEL", "google/flan-t5-small")
HF_TIMEOUT = int(os.environ.get("HF_TIMEOUT_S", "60"))
# Use very low temperature and small max tokens by default to reduce token costs and enforce concise JSON
HF_TEMPERATURE = float(os.environ.get("HF_TEMPERATURE", "0.0"))
HF_MAX_TOKENS = int(os.environ.get("HF_MAX_TOKENS", "60"))
HF_BULLET_WORD_LIMIT = int(os.environ.get("HF_BULLET_WORD_LIMIT", "12"))


def _require_key():
    if not HF_API_KEY:
        raise RuntimeError("HF_API_KEY not set; export your Hugging Face token")


def _call_hf_inference(prompt: str, max_tokens: int = 250) -> str:
    _require_key()
    # Prefer huggingface_hub InferenceClient if available
    if InferenceClient is not None:
        try:
            client = InferenceClient(model=HF_GEN_MODEL, token=HF_API_KEY, timeout=HF_TIMEOUT)
            out = client.text_generation(prompt, max_new_tokens=max_tokens, temperature=HF_TEMPERATURE, return_full_text=False)
            return out
        except Exception:
            pass
    # Fallback to REST
    url = f"https://api-inference.huggingface.co/models/{HF_GEN_MODEL}"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_tokens,
            "temperature": HF_TEMPERATURE,
            "do_sample": False,
            "return_full_text": False,
        },
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=HF_TIMEOUT)
    resp.raise_for_status()
    return resp.text


def generate_json_summary(retrieved: List[Dict[str, Any]], question: Optional[str] = None) -> Dict[str, Any]:
    """Very small wrapper that asks the HF model to return JSON.

    The HF API returns different shapes depending on model; this function tries to parse JSON out of the text.
    """
    snippet_lines: List[str] = []
    for r in retrieved:
        nid = r.get("note_id")
        date = r.get("note_date", "")
        snippet = (r.get("snippet") or "").strip().replace("\n", " ")
        score = r.get("score", None)
        snippet_lines.append(f"NOTE_ID={nid} DATE={date} SCORE={score}\n{snippet}\n")

    snippets_block = "\n---\n".join(snippet_lines)
    qline = f"Question: {question}\n\n" if question else ""
    # Very tight prompt: force exactly one JSON object only, minimal text
    prompt = (
        "RETURN EXACTLY ONE JSON OBJECT AND NOTHING ELSE. No explanation, no code fences.\n"
        "Keys:\n"
        "- one_line: one short sentence, max 12 words.\n"
        "- bullets: array of 2-4 short sentences, each <= " + str(HF_BULLET_WORD_LIMIT) + " words.\n"
        "- sources: array of objects {note_id:int, score:float}.\n\n"
        f"{qline}"
        "SNIPPETS:\n"
        f"{snippets_block}\n\n"
        "Produce the JSON now."
    )

    # Call HF inference - many models return application/json or plain text
    full_text = _call_hf_inference(prompt)
    # The response body might be JSON text already, or a plain string like [{"generated_text": "..."}]
    try:
        parsed = json.loads(full_text)
        # if it's a list with generated_text
        if isinstance(parsed, list) and isinstance(parsed[0], dict) and "generated_text" in parsed[0]:
            text = parsed[0]["generated_text"]
        elif isinstance(parsed, dict) and "generated_text" in parsed:
            text = parsed["generated_text"]
        else:
            # if the model returned JSON already, try to interpret it as summary
            if isinstance(parsed, dict) and "one_line" in parsed:
                return parsed
            # otherwise, if it's a list, join textual elements
            text = json.dumps(parsed)
    except Exception:
        # Not JSON: treat full_text as plain string and try to extract JSON
        text = full_text

    # try to find JSON object in text
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            parsed = json.loads(text[start:end+1])
        except Exception as e:
            raise ValueError(f"HF: failed to parse JSON summary: {e}\nModel output: {text[:1000]}")
    else:
        raise ValueError(f"HF: failed to find JSON in model output. Output (truncated): {text[:1000]}")

    # basic schema check and post-process to enforce brevity
    if not isinstance(parsed, dict) or "one_line" not in parsed or "bullets" not in parsed:
        raise ValueError(f"HF: Summary JSON missing required keys. Parsed: {parsed}")

    # enforce one_line brevity
    def _shorten_sentence(s: str, max_words: int = 12) -> str:
        words = s.strip().split()
        if len(words) <= max_words:
            return " ".join(words)
        return " ".join(words[:max_words]) + "..."

    parsed["one_line"] = _shorten_sentence(str(parsed.get("one_line", "")), 12)

    # enforce bullets array length and word limits
    bullets = parsed.get("bullets", [])
    if not isinstance(bullets, list):
        bullets = [str(bullets)]
    # limit to 4 bullets
    bullets = bullets[:4]
    bullets = [_shorten_sentence(str(b), HF_BULLET_WORD_LIMIT) for b in bullets]
    parsed["bullets"] = bullets

    return parsed
