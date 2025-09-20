"""Cohere helper: embeddings + generation with retries and JSON parsing.

Usage:
    from cohere_wrapper import embed_texts, generate_json_summary

Requires COHERE_API_KEY set in environment or backend/.env
"""
from __future__ import annotations

import importlib
import json
import os
from typing import Any, Dict, List, Optional
import traceback

# Optional dependencies: cohere, tenacity, python-dotenv
_cohere_mod = None
try:
    _cohere_mod = importlib.import_module("cohere")
except Exception:
    _cohere_mod = None

# tenacity (retry) — provide a safe no-op fallback if not installed
_tenacity = None
try:
    _tenacity = importlib.import_module("tenacity")
    retry = getattr(_tenacity, "retry")
    wait_exponential = getattr(_tenacity, "wait_exponential")
    stop_after_attempt = getattr(_tenacity, "stop_after_attempt")
    retry_if_exception_type = getattr(_tenacity, "retry_if_exception_type")
except Exception:
    def retry(*args, **kwargs):
        def _decorator(fn):
            return fn
        return _decorator

    def wait_exponential(*_args, **_kwargs):
        return None

    def stop_after_attempt(*_args, **_kwargs):
        return None

    def retry_if_exception_type(*_args, **_kwargs):
        return None

# requests exceptions fallback
try:
    _req_ex = importlib.import_module("requests.exceptions")
    HTTPError = getattr(_req_ex, "HTTPError")
    RequestException = getattr(_req_ex, "RequestException")
except Exception:
    HTTPError = Exception
    RequestException = Exception

# dotenv (optional)
try:
    dotenv = importlib.import_module("dotenv")
    load_dotenv = getattr(dotenv, "load_dotenv", None)
    if callable(load_dotenv):
        load_dotenv()
except Exception:
    pass

COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
EMBED_MODEL = os.environ.get("COHERE_EMBED_MODEL", "embed-english-small")
GEN_MODEL = os.environ.get("COHERE_GEN_MODEL", "command-r-08-2024")
# sensible fallback candidates in case the configured model isn't available to the account
GEN_MODEL_FALLBACKS = [
    "command-r-plus-08-2024",
    "command-r7b-12-2024",
    "command-r-08-2024",
    "command-a-03-2025",
    "command-xlarge",
    "xlarge",
    "command",
]
MAX_TOKENS = int(os.environ.get("COHERE_MAX_TOKENS", "250"))
TIMEOUT_S = int(os.environ.get("COHERE_TIMEOUT_S", "60"))
COHERE_DEBUG = os.environ.get("COHERE_DEBUG", "0") in ("1", "true", "True")

_client = None
if COHERE_API_KEY and _cohere_mod is not None:
    try:
        _client = _cohere_mod.Client(COHERE_API_KEY)
    except Exception:
        _client = None


def _require_client():
    if _client is None:
        raise RuntimeError("COHERE_API_KEY is not set or Cohere client not available; set COHERE_API_KEY and install cohere SDK")


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Return embeddings for input texts using Cohere embed API."""
    _require_client()
    try:
        resp = _client.embed(model=EMBED_MODEL, texts=texts)
        return resp.embeddings
    except Exception as e:
        # If the configured model isn't found, try a sensible fallback model
        msg = str(e)
        fallback_models = ["embed-english-v2.0", "embed-english-small"]
        # avoid retrying the same model
        fallback_models = [m for m in fallback_models if m != EMBED_MODEL]
        for fm in fallback_models:
            try:
                resp = _client.embed(model=fm, texts=texts)
                if COHERE_DEBUG:
                    print(f"embed_texts: primary model {EMBED_MODEL} failed, succeeded with fallback {fm}")
                return resp.embeddings
            except Exception:
                continue
        # re-raise with more context
        raise RuntimeError(f"Embedding failed for models [{EMBED_MODEL}]+fallbacks; last error: {msg}") from e


@retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(4), retry=retry_if_exception_type((HTTPError, RequestException)))
def _call_generate(prompt: str, max_tokens: int = MAX_TOKENS, temperature: float = 0.2) -> str:
    _require_client()
    last_err = None
    # Prefer modern Responses/Chat APIs (Generate API removed Sep 15, 2025)
    try:
        if hasattr(_client, "responses") and hasattr(_client.responses, "create"):
            resp = _client.responses.create(model=GEN_MODEL, input=prompt, max_tokens=max_tokens, temperature=temperature)
            # Try common extraction points
            if hasattr(resp, "output_text") and resp.output_text:
                return resp.output_text
            if hasattr(resp, "output"):
                try:
                    out = []
                    for item in resp.output:
                        out.append(str(item))
                    if out:
                        return "\n".join(out)
                except Exception:
                    pass
            return str(resp)
    except Exception as e:
        last_err = e
        if COHERE_DEBUG:
            print(f"responses.create with primary model '{GEN_MODEL}' failed: {repr(e)}")

    # Try chat.create with both modern (messages=[...]) and legacy (message=...) signatures
    try:
        if hasattr(_client, "chat") and hasattr(_client.chat, "create"):
            try:
                resp = _client.chat.create(model=GEN_MODEL, messages=[{"role": "user", "content": prompt}], max_tokens=max_tokens, temperature=temperature)
            except TypeError:
                # legacy SDK signature
                resp = _client.chat.create(model=GEN_MODEL, message=prompt, max_tokens=max_tokens)
            if hasattr(resp, "output_text") and resp.output_text:
                return resp.output_text
            if hasattr(resp, "generations") and resp.generations:
                return resp.generations[0].text
            return str(resp)
    except Exception as e:
        last_err = e
        if COHERE_DEBUG:
            print(f"chat.create with primary model '{GEN_MODEL}' failed: {repr(e)}")

    # If model not found or primary failed, try fallbacks across several APIs
    for fm in GEN_MODEL_FALLBACKS:
        if fm == GEN_MODEL:
            continue
        try:
            if COHERE_DEBUG:
                print(f"Trying fallback model: {fm}")
            # Try responses API
            if hasattr(_client, "responses") and hasattr(_client.responses, "create"):
                resp = _client.responses.create(model=fm, input=prompt, max_tokens=max_tokens, temperature=temperature)
                if hasattr(resp, "output_text") and resp.output_text:
                    return resp.output_text
                return str(resp)

            

            # Try v2.responses.create if available (SDK v5+)
            if hasattr(_client, "v2") and hasattr(_client.v2, "responses") and hasattr(_client.v2.responses, "create"):
                if COHERE_DEBUG:
                    print(f"Trying v2.responses.create with model: {fm}")
                resp = _client.v2.responses.create(model=fm, input=prompt, max_tokens=max_tokens, temperature=temperature)
                if COHERE_DEBUG:
                    print("v2.responses.create returned, extracting text")
                # try common fields
                if hasattr(resp, "output_text") and resp.output_text:
                    return resp.output_text
                if hasattr(resp, "output"):
                    try:
                        out = []
                        for item in resp.output:
                            out.append(str(item))
                        if out:
                            return "\n".join(out)
                    except Exception:
                        pass
                return str(resp)

            # Try chat endpoints (client.chat.create or v2.chat.create)
            if hasattr(_client, "chat") and hasattr(_client.chat, "create"):
                if COHERE_DEBUG:
                    print(f"Trying chat.create with model: {fm}")
                resp = _client.chat.create(model=fm, messages=[{"role":"user","content":prompt}], max_tokens=max_tokens)
                # extract reply
                try:
                    if hasattr(resp, "generations"):
                        return resp.generations[0].text
                    if hasattr(resp, "output_text"):
                        return resp.output_text
                except Exception:
                    pass
                return str(resp)

            if hasattr(_client, "v2") and hasattr(_client.v2, "chat") and hasattr(_client.v2.chat, "create"):
                if COHERE_DEBUG:
                    print(f"Trying v2.chat.create with model: {fm}")
                resp = _client.v2.chat.create(model=fm, messages=[{"role":"user","content":prompt}], max_tokens=max_tokens)
                if hasattr(resp, "output_text") and resp.output_text:
                    return resp.output_text
                return str(resp)

            # If no supported interface, raise
            raise AttributeError("No supported generation interface available on Cohere client")
        except Exception as e:
            last_err = e
            if COHERE_DEBUG:
                print(f"Fallback model {fm} failed: {repr(e)}")
                try:
                    print("Exception args:", getattr(e, 'args', None))
                    print("Traceback:\n", traceback.format_exc())
                except Exception:
                    pass
            continue

    # No model worked — provide a helpful error including configured models
    cfg_models = [GEN_MODEL] + [m for m in GEN_MODEL_FALLBACKS if m != GEN_MODEL]
    raise RuntimeError(
        f"Cohere generation failed for configured models {cfg_models}. "
        f"Last error: {repr(last_err)}.\n"
        f"Cohere Generate API was sunset. The wrapper now uses Responses/Chat. If issues persist, set COHERE_GEN_MODEL to a model available on your account and with chat/responses support."
    ) from last_err


def generate_json_summary(retrieved: List[Dict[str, Any]], question: Optional[str] = None) -> Dict[str, Any]:
    """Build a prompt from retrieved snippets and ask Cohere to return JSON.

    Returns a dict with keys 'one_line', 'bullets', 'sources'. Raises ValueError on parse failure.
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
        "You are a helpful assistant that reads clinical note snippets and returns a structured JSON summary.\n"
        "Return ONLY valid JSON (no extra text) with keys: one_line (string), bullets (array of short strings), "
        "sources (array of objects {note_id:int, score:float}).\n\n"
        f"{qline}"
        "Snippets:\n"
        f"{snippets_block}\n\n"
        "Produce the JSON now."
    )

    out = _call_generate(prompt)
    text = out.strip()
    if COHERE_DEBUG:
        try:
            print("COHERE RAW OUTPUT:\n", text[:8000])
        except Exception:
            print("COHERE RAW OUTPUT (unable to slice)")

    # Try to parse JSON directly, otherwise try to extract the first JSON object
    try:
        parsed = json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(text[start:end+1])
            except Exception as e:
                raise ValueError(f"Failed to parse JSON summary: {e}\nModel output: {text[:1000]}")
        else:
            raise ValueError(f"Failed to parse JSON summary. Model output: {text[:1000]}")

    # Basic schema validation
    if not isinstance(parsed, dict) or "one_line" not in parsed or "bullets" not in parsed:
        raise ValueError(f"Summary JSON missing required keys. Parsed: {parsed}")

    # Normalize sources
    if "sources" in parsed:
        normalized: List[Dict[str, Any]] = []
        for s in parsed.get("sources", []):
            try:
                normalized.append({"note_id": int(s.get("note_id")), "score": float(s.get("score", 0))})
            except Exception:
                continue
        parsed["sources"] = normalized

    return parsed


def list_models() -> List[str]:
    """Return a list of model ids available to the configured Cohere client.

    Useful for debugging which generation models an account can access.
    """
    _require_client()
    import re

    def _extract_name(obj_str: str) -> Optional[str]:
        # try to find name='model-id' or name="model-id"
        m = re.search(r"name=['\"]([^'\"]+)['\"]", obj_str)
        if m:
            return m.group(1)
        # try id=(...)
        m = re.search(r"id=['\"]([^'\"]+)['\"]", obj_str)
        if m:
            return m.group(1)
        return None

    # Try client.list_models() if present
    if hasattr(_client, "list_models"):
        try:
            resp = _client.list_models()
            if isinstance(resp, list):
                out = []
                for m in resp:
                    sid = getattr(m, "id", None) or getattr(m, "name", None) or _extract_name(str(m))
                    out.append(sid or str(m))
                return out
            if hasattr(resp, "models"):
                out = []
                for m in resp.models:
                    sid = getattr(m, "id", None) or getattr(m, "name", None) or _extract_name(str(m))
                    out.append(sid or str(m))
                return out
            # try to extract names from string
            s = str(resp)
            nm = _extract_name(s)
            if nm:
                return [nm]
            return [s]
        except Exception:
            # fall through to other strategies
            pass

    # Try client.models.list() (ModelsClient)
    if hasattr(_client, "models"):
        models_attr = getattr(_client, "models")
        # If it's callable, try calling it
        try:
            if callable(models_attr):
                resp = models_attr()
                out = []
                if isinstance(resp, list):
                    for m in resp:
                        sid = getattr(m, "id", None) or getattr(m, "name", None) or _extract_name(str(m))
                        out.append(sid or str(m))
                    return out
                if hasattr(resp, "models"):
                    for m in resp.models:
                        sid = getattr(m, "id", None) or getattr(m, "name", None) or _extract_name(str(m))
                        out.append(sid or str(m))
                    return out
                nm = _extract_name(str(resp))
                if nm:
                    return [nm]
                return [str(resp)]
        except Exception:
            pass

        # If it exposes .list(), call that
        if hasattr(models_attr, "list"):
            try:
                resp = models_attr.list()
                out = []
                if isinstance(resp, list):
                    for m in resp:
                        sid = getattr(m, "id", None) or getattr(m, "name", None) or _extract_name(str(m))
                        out.append(sid or str(m))
                    return out
                if hasattr(resp, "models"):
                    for m in resp.models:
                        sid = getattr(m, "id", None) or getattr(m, "name", None) or _extract_name(str(m))
                        out.append(sid or str(m))
                    return out
                nm = _extract_name(str(resp))
                if nm:
                    return [nm]
                return [str(resp)]
            except Exception:
                pass

    # Try common alternative names
    for alt in ("list_models", "available_models", "get_models"):
        if hasattr(_client, alt):
            try:
                fn = getattr(_client, alt)
                resp = fn()
                if isinstance(resp, list):
                    return [getattr(m, "id", str(m)) for m in resp]
                if hasattr(resp, "models"):
                    return [getattr(m, "id", str(m)) for m in resp.models]
                return [str(resp)]
            except Exception:
                continue

    # Last resort: inspect attributes of client for model-like ids
    try:
        attrs = dir(_client)
        candidates = [a for a in attrs if "model" in a.lower() or "models" in a.lower()]
        return candidates[:50]
    except Exception as e:
        raise RuntimeError(f"Unable to enumerate models: {e}") from e


def client_info() -> Dict[str, Any]:
    """Return basic introspection about the Cohere client for debugging."""
    if _client is None:
        return {"available": False}
    info = {"available": True, "type": str(type(_client)), "dir": dir(_client)}
    # Try to report SDK version if present
    try:
        info["version"] = getattr(_cohere_mod, "__version__", None)
    except Exception:
        pass
    return info


def try_generate_with_model(model: str, prompt: str, max_tokens: int = 60, temperature: float = 0.2) -> str:
    """Attempt a single generation call using the provided model name.

    Tries generate(), responses.create(), v2.responses.create(), chat.create() and returns the text on success.
    Raises the last exception on failure.
    """
    _require_client()
    last_err = None
    # Try generate() if present
    try:
        if hasattr(_client, "generate"):
            if COHERE_DEBUG:
                print(f"try_generate_with_model: calling generate() with model={model}")
            resp = _client.generate(model=model, prompt=prompt, max_tokens=max_tokens, temperature=temperature)
            if hasattr(resp, "generations"):
                return resp.generations[0].text
            return str(resp)
    except Exception as e:
        last_err = e
        if COHERE_DEBUG:
            print("generate() failed:", repr(e))

    # Try client.responses.create
    try:
        if hasattr(_client, "responses") and hasattr(_client.responses, "create"):
            if COHERE_DEBUG:
                print(f"try_generate_with_model: calling responses.create with model={model}")
            resp = _client.responses.create(model=model, input=prompt, max_tokens=max_tokens, temperature=temperature)
            # try to extract text
            if hasattr(resp, "output_text") and resp.output_text:
                return resp.output_text
            if hasattr(resp, "output"):
                try:
                    out = []
                    for item in resp.output:
                        out.append(str(item))
                    if out:
                        return "\n".join(out)
                except Exception:
                    pass
            return str(resp)
    except Exception as e:
        last_err = e
        if COHERE_DEBUG:
            print("responses.create failed:", repr(e))

    # Try v2.responses.create
    try:
        if hasattr(_client, "v2") and hasattr(_client.v2, "responses") and hasattr(_client.v2.responses, "create"):
            if COHERE_DEBUG:
                print(f"try_generate_with_model: calling v2.responses.create with model={model}")
            resp = _client.v2.responses.create(model=model, input=prompt, max_tokens=max_tokens, temperature=temperature)
            if hasattr(resp, "output_text") and resp.output_text:
                return resp.output_text
            return str(resp)
    except Exception as e:
        last_err = e
        if COHERE_DEBUG:
            print("v2.responses.create failed:", repr(e))

    # Try chat endpoints
    try:
        if hasattr(_client, "chat") and hasattr(_client.chat, "create"):
            if COHERE_DEBUG:
                print(f"try_generate_with_model: calling chat.create with model={model}")
            resp = _client.chat.create(model=model, messages=[{"role": "user", "content": prompt}], max_tokens=max_tokens)
            if hasattr(resp, "generations"):
                return resp.generations[0].text
            if hasattr(resp, "output_text"):
                return resp.output_text
            return str(resp)
    except Exception as e:
        last_err = e
        if COHERE_DEBUG:
            print("chat.create failed:", repr(e))

    # Try v2.chat.create
    try:
        if hasattr(_client, "v2") and hasattr(_client.v2, "chat") and hasattr(_client.v2.chat, "create"):
            if COHERE_DEBUG:
                print(f"try_generate_with_model: calling v2.chat.create with model={model}")
            resp = _client.v2.chat.create(model=model, messages=[{"role": "user", "content": prompt}], max_tokens=max_tokens)
            if hasattr(resp, "output_text") and resp.output_text:
                return resp.output_text
            return str(resp)
    except Exception as e:
        last_err = e
        if COHERE_DEBUG:
            print("v2.chat.create failed:", repr(e))

    # All attempts failed
    raise last_err or RuntimeError("All generation attempts failed for model {model}")


def check_api_key_info() -> Dict[str, Any]:
    """Invoke client's check_api_key() if available and return result for diagnostics."""
    if _client is None:
        return {"available": False}
    if hasattr(_client, "check_api_key"):
        try:
            resp = _client.check_api_key()
            # try to convert to dict safely
            try:
                return dict(resp)
            except Exception:
                return {"raw": str(resp)}
        except Exception as e:
            return {"error": repr(e)}
    return {"check_api_key": "not_supported"}
