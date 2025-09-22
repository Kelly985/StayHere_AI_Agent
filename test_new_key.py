#!/usr/bin/env python3
"""
Quick test for new OpenRouter API key
Usage: python test_new_key.py YOUR_NEW_API_KEY
"""
import sys
import asyncio
import httpx

async def test_key(api_key):
    """Test if the API key works"""
    print(f"Testing API key: {api_key[:20]}...")
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "x-ai/grok-4-fast:free",
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 5
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data, timeout=10.0)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                print("✅ API KEY IS VALID!")
                return True
            else:
                print("❌ API KEY IS INVALID!")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_new_key.py YOUR_NEW_API_KEY")
        sys.exit(1)
    
    asyncio.run(test_key(sys.argv[1]))
