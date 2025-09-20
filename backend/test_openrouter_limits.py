#!/usr/bin/env python3
"""Check OpenRouter API limits and pricing."""

import requests
import json
import os

# Load API key from environment
API_KEY = "OPENROUTER_API_KEY_REMOVED"
headers = {'Authorization': f'Bearer {API_KEY}'}

print("=== OpenRouter Account & Rate Limits ===\n")

# Get account information
try:
    auth_resp = requests.get('https://openrouter.ai/api/v1/auth/key', headers=headers)
    auth_data = auth_resp.json()['data']
    
    print("📊 Account Information:")
    print(f"   Account Type: {'Free Tier' if auth_data.get('is_free_tier') else 'Paid'}")
    print(f"   Current Usage: ${auth_data.get('usage', 0):.6f}")
    print(f"   Spending Limit: {auth_data.get('limit') or 'No limit set'}")
    print(f"   Remaining: {auth_data.get('limit_remaining') or 'N/A'}")
    
    rate_limit = auth_data.get('rate_limit', {})
    print(f"   Rate Limit: {rate_limit.get('requests', 'N/A')} requests per {rate_limit.get('interval', 'N/A')}")
    
except Exception as e:
    print(f"❌ Error getting account info: {e}")

print("\n" + "="*50)

# Get model information
try:
    models_resp = requests.get('https://openrouter.ai/api/v1/models', headers=headers)
    models = models_resp.json()['data']
    
    # Find LLaMA 3.1 8B model
    llama_model = next((m for m in models if 'llama-3.1-8b-instruct' in m.get('id', '')), None)
    
    if llama_model:
        print("🤖 LLaMA 3.1 8B Instruct Model Info:")
        print(f"   Model ID: {llama_model.get('id')}")
        print(f"   Context Length: {llama_model.get('context_length'):,} tokens")
        
        pricing = llama_model.get('pricing', {})
        prompt_cost = float(pricing.get('prompt', 0))
        completion_cost = float(pricing.get('completion', 0))
        
        print(f"   Prompt Cost: ${prompt_cost:.8f} per token")
        print(f"   Completion Cost: ${completion_cost:.8f} per token")
        
        # Calculate costs for typical EMR usage
        print("\n💰 Cost Estimates for EMR Usage:")
        
        # Typical summarization: 500 prompt tokens + 100 completion tokens
        summary_cost = (500 * prompt_cost) + (100 * completion_cost)
        print(f"   Per Summary (500+100 tokens): ${summary_cost:.6f}")
        
        # Typical Q&A: 300 prompt tokens + 50 completion tokens  
        qa_cost = (300 * prompt_cost) + (50 * completion_cost)
        print(f"   Per Q&A (300+50 tokens): ${qa_cost:.6f}")
        
        # Daily estimates
        daily_summaries = 50  # 50 summaries per day
        daily_qa = 20         # 20 Q&A interactions per day
        
        daily_cost = (daily_summaries * summary_cost) + (daily_qa * qa_cost)
        print(f"   Daily Cost (50 summaries + 20 Q&As): ${daily_cost:.4f}")
        print(f"   Monthly Cost (30 days): ${daily_cost * 30:.2f}")
        
    else:
        print("❌ LLaMA 3.1 8B model not found")
        
except Exception as e:
    print(f"❌ Error getting model info: {e}")

print("\n" + "="*50)
print("📋 OpenRouter Free Tier Limits (General):")
print("   • Free tier has rate limits but no hard daily call limits")
print("   • Rate limits are per model and provider")  
print("   • Costs are pay-per-use (very small amounts)")
print("   • No subscription required for basic usage")
print("\n🔗 For detailed limits: https://openrouter.ai/docs")