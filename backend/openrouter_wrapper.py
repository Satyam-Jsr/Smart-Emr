"""OpenRouter helper: chat generation with JSON parsing.

Requires OPENROUTER_API_KEY in env or backend/.env.
Optionally set OPENROUTER_MODEL (e.g., 'meta-llama/llama-3.1-8b-instruct').
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import requests

# dotenv (optional)
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OR_MODEL = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")
OR_TIMEOUT_S = int(os.environ.get("OPENROUTER_TIMEOUT_S", "20"))  # Reduced from 60 to 20 seconds
OR_TEMPERATURE = float(os.environ.get("OPENROUTER_TEMPERATURE", "0.2"))
OR_MAX_TOKENS = int(os.environ.get("OPENROUTER_MAX_TOKENS", "300"))
OR_DEBUG = os.environ.get("OPENROUTER_DEBUG", "0") in ("1", "true", "True")

API_URL = "https://openrouter.ai/api/v1/chat/completions"


def _require_key() -> None:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not set; add it to backend/.env")


def _chat(prompt: str, max_tokens: int = OR_MAX_TOKENS, temperature: float = OR_TEMPERATURE) -> str:
    _require_key()
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        # Optional, but recommended by OpenRouter for analytics/rate fairness
        "HTTP-Referer": os.environ.get("OPENROUTER_REFERER", "http://localhost"),
        "X-Title": os.environ.get("OPENROUTER_TITLE", "EMR App"),
    }
    payload = {
        "model": OR_MODEL,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "user", "content": prompt},
        ],
    }
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=OR_TIMEOUT_S)
    if OR_DEBUG:
        try:
            print("OpenRouter status:", resp.status_code)
            print("OpenRouter body (first 2000):", resp.text[:2000])
        except Exception:
            pass
    resp.raise_for_status()
    data = resp.json()
    # Expected structure: { choices: [ { message: { content: "..." } } ] }
    try:
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        raise ValueError(f"OpenRouter: unexpected response shape: {data}") from e


def generate_json_summary(retrieved: List[Dict[str, Any]], question: Optional[str] = None) -> Dict[str, Any]:
    """Ask model to produce a strict JSON summary.

    Returns dict with keys: one_line, bullets, sources.
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
    prompt = (
        "Return ONLY one JSON object. No prose, no code fences.\n"
        "Keys: one_line (<=12 words), bullets (2-4 short items), "
        "sources (array of {note_id:int, score:float}).\n\n"
        f"{qline}"
        "SNIPPETS:\n"
        f"{snippets_block}\n\n"
        "Produce the JSON now."
    )

    text = _chat(prompt)
    # Try parse JSON directly, otherwise extract first {...}
    try:
        parsed = json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(text[start:end+1])
        else:
            raise ValueError(f"OpenRouter: failed to parse JSON. Output (trunc): {text[:1000]}")

    if not isinstance(parsed, dict) or "one_line" not in parsed or "bullets" not in parsed:
        raise ValueError(f"OpenRouter: Summary JSON missing required keys. Parsed: {parsed}")

    return parsed




