#!/usr/bin/env python3

import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()

# Test if we can import the library correctly
try:
    from openai import OpenAI
    print("✅ OpenAI library imported successfully")
except ImportError as e:
    print(f"❌ Failed to import OpenAI: {e}")
    sys.exit(1)

# Get API key
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("❌ No OpenAI API key found")
    sys.exit(1)

print(f"✅ API key found: {api_key[:20]}...")

# Try to unset any proxy-related environment variables
proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'NO_PROXY', 'no_proxy']
for var in proxy_vars:
    if var in os.environ:
        print(f"Removing proxy env var: {var}")
        del os.environ[var]

# Test with minimal configuration
try:
    client = OpenAI(
        api_key=api_key,
        timeout=30.0,
        max_retries=2
    )
    print("✅ OpenAI client created successfully")
    
    # Test a simple completion
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "Generate exactly 4 notes in this format: C4(quarter,80) D4(quarter,75)"}
        ],
        max_tokens=50,
        temperature=0.7
    )
    
    print("✅ API call successful!")
    print("Response:", response.choices[0].message.content)
    
except Exception as e:
    print(f"❌ Error: {e}")
    # Try alternative approach with requests directly
    print("Trying alternative approach...")
    
    try:
        import requests
        import json
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-4',
            'messages': [
                {'role': 'user', 'content': 'Generate exactly 4 notes in this format: C4(quarter,80) D4(quarter,75)'}
            ],
            'max_tokens': 50
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Direct API call successful!")
            print("Response:", result['choices'][0]['message']['content'])
        else:
            print(f"❌ API error: {response.status_code} - {response.text}")
            
    except Exception as e2:
        print(f"❌ Alternative approach failed: {e2}")
