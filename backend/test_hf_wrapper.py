from hf_wrapper import generate_json_summary

retrieved = [
    {"note_id": 1, "note_date": "2025-09-18", "snippet": "Patient has cough and elevated BP.", "score": 0.95}
]

print("Calling HF generate_json_summary()")
try:
    out = generate_json_summary(retrieved)
    print("HF Parsed JSON:", out)
except Exception as e:
    print("HF generate failed:", repr(e))
