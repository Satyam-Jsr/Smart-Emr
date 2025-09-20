#!/usr/bin/env python3
"""Test OpenRouter medical summary functionality"""

import sys
import os
sys.path.append('.')

# Enable debug mode
os.environ['OPENROUTER_DEBUG'] = '1'

from openrouter_wrapper import generate_json_summary

print('🧪 Testing OpenRouter Medical Summary with DEBUG enabled...')

# Test data with medical notes
test_data = [
    {
        'note_id': 1,
        'note_date': '2025-09-18',
        'snippet': 'Patient John Doe, age 45. Blood pressure 140/90 mmHg. Started lisinopril 10mg daily for hypertension.',
        'score': 0.95
    },
    {
        'note_id': 2, 
        'note_date': '2025-09-15',
        'snippet': 'Diabetes mellitus type 2. HbA1c 8.2%. Started metformin 1000mg twice daily.',
        'score': 0.88
    }
]

try:
    print('📋 Testing summary generation...')
    result = generate_json_summary(test_data)
    print('✅ OpenRouter Medical Summary successful!')
    print('📍 One-line:', result.get('one_line', 'N/A'))
    print('📍 Bullets:')
    for bullet in result.get('bullets', []):
        print(f'  • {bullet}')
    print('📍 Sources:', result.get('sources', []))
    
    print('\n🧪 Testing Q&A functionality...')
    question = 'What medications is the patient taking?'
    qa_result = generate_json_summary(test_data, question=question)
    print('✅ OpenRouter Q&A successful!')
    print(f'❓ Question: {question}')
    print('📍 Answer:', qa_result.get('one_line', 'N/A'))
    print('📍 Details:')
    for bullet in qa_result.get('bullets', []):
        print(f'  • {bullet}')
    print('📍 Sources:', qa_result.get('sources', []))
        
except Exception as e:
    print(f'❌ Test failed: {e}')
    import traceback
    traceback.print_exc()