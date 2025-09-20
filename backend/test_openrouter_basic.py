#!/usr/bin/env python3
"""Quick OpenRouter connectivity test"""

import sys
sys.path.append('.')
from openrouter_wrapper import _chat

print('🧪 Testing basic OpenRouter API call...')
try:
    # Simple test prompt
    prompt = 'Return only this JSON object: {"test": "success", "status": "working"}'
    response = _chat(prompt, max_tokens=50)
    print('✅ API Response received')
    print(f'📤 Response: {repr(response)}')
    print(f'📊 Response length: {len(response)} characters')
    print('🔍 Testing JSON parsing...')
    
    import json
    try:
        parsed = json.loads(response.strip())
        print('✅ JSON parsing successful')
        print(f'📋 Parsed data: {parsed}')
    except:
        print('❌ JSON parsing failed - checking for JSON in response')
        start = response.find('{')
        end = response.rfind('}')
        if start != -1 and end != -1:
            json_part = response[start:end+1]
            try:
                parsed = json.loads(json_part)
                print('✅ Found and parsed JSON successfully')
                print(f'📋 Parsed data: {parsed}')
            except:
                print(f'❌ Could not parse extracted JSON: {json_part}')
        else:
            print('❌ No JSON found in response')
            
except Exception as e:
    print(f'❌ API call failed: {e}')
    import traceback
    traceback.print_exc()