from cohere_wrapper import embed_texts, generate_json_summary
from cohere_wrapper import list_models
from cohere_wrapper import client_info, check_api_key_info

texts = ["Patient has cough and elevated BP, headache in morning."]
print("Embedding test (length):", len(embed_texts(texts)[0]))

retrieved = [
  {"note_id": 1, "note_date": "2025-09-18", "snippet": texts[0], "score": 0.95}
]

print("Calling generate_json_summary()")
try:
  models = list_models()
  print("Available Cohere models (sample):", models[:20])
except Exception as e:
  print("Could not list models:", repr(e))
info = client_info()
print("Cohere client info:", info)
try:
  cak = client_info()
  print("check_api_key (basic):", cak)
except Exception as e:
  print("check_api_key failed:", repr(e))
try:
  cak2 = check_api_key_info()
  print("check_api_key_info():", cak2)
except Exception as e:
  print("check_api_key_info failed:", repr(e))

import os
print("Configured COHERE_GEN_MODEL env:", os.environ.get("COHERE_GEN_MODEL"))
print("COHERE_API_KEY present:", bool(os.environ.get("COHERE_API_KEY")))
try:
    out = generate_json_summary(retrieved)
    print("Parsed JSON:", out)
except Exception as e:
    print("Generate failed with:", repr(e))


print("\nNow attempting to auto-find a working generator model from list_models() candidates")
try:
  from cohere_wrapper import try_generate_with_model
  candidates = list_models()
  # prefer command-like generator models
  filtered = [m for m in candidates if m and any(x in m for x in ["command", "r7b", "r-", "a-", "command-r", "command-a"]) ]
  if not filtered:
    filtered = candidates
  print("Trying candidate models (sample):", filtered[:20])
  test_prompt = "Say JSON: {\"ok\": true, \"msg\": \"hi\"}"
  success = None
  for m in filtered:
    try:
      print("Trying model:", m)
      out = try_generate_with_model(m, test_prompt, max_tokens=40)
      print("Success with model:", m)
      print("Output (truncated):", str(out)[:400])
      success = m
      break
    except Exception as e:
      print("Model failed:", m, "error:", repr(e))
      continue
  if not success:
    print("No candidate models produced output. Check API key permissions or contact Cohere support.")
  else:
    print("Working model found:", success)
except Exception as e:
  print("Auto-find attempt failed:", repr(e))
