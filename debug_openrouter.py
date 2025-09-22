#!/usr/bin/env python3
"""
Debug script to test OpenRouter API directly
"""
import asyncio
import httpx
from config.settings import settings

async def test_openrouter_direct():
    """Test OpenRouter API with exact same parameters as the application"""
    
    print(f"Testing OpenRouter API...")
    print(f"API Key: {settings.openrouter_api_key[:20]}...")
    print(f"Model: {settings.openrouter_model}")
    print("-" * 50)
    
    # Test 1: Minimal request
    print("🧪 Test 1: Minimal request")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json"
    }
    
    simple_data = {
        "model": settings.openrouter_model,
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 10
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=simple_data, timeout=30.0)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code}")
                return False
            else:
                print("✅ Minimal request successful!")
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    
    print("-" * 50)
    
    # Test 2: Exact same format as application
    print("🧪 Test 2: Same format as application")
    app_headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Kenyan Real Estate AI Agent"
    }
    
    app_data = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": "What are property prices in Nairobi?"}
        ],
        "max_tokens": 100,
        "temperature": 0.7,
        "top_p": 0.9,
        "stream": False
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=app_headers, json=app_data, timeout=30.0)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code}")
                return False
            else:
                print("✅ Application format successful!")
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    
    return True

# Test 3: Check model availability
async def test_model_availability():
    """Test if the model is available"""
    print("-" * 50)
    print("🧪 Test 3: Check model availability")
    
    url = "https://openrouter.ai/api/v1/models"
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                models_data = response.json()
                available_models = [model["id"] for model in models_data.get("data", [])]
                
                if settings.openrouter_model in available_models:
                    print(f"✅ Model '{settings.openrouter_model}' is available!")
                else:
                    print(f"❌ Model '{settings.openrouter_model}' is NOT available!")
                    print("Available models containing 'grok' or 'free':")
                    for model in available_models:
                        if 'grok' in model.lower() or 'free' in model.lower():
                            print(f"  - {model}")
                    return False
            else:
                print(f"❌ Could not fetch models: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    
    return True

async def main():
    print("🔍 OpenRouter API Debug Test")
    print("=" * 50)
    
    # Test API key and requests
    api_success = await test_openrouter_direct()
    
    # Test model availability 
    model_success = await test_model_availability()
    
    print("=" * 50)
    if api_success and model_success:
        print("✅ All tests passed! The API should work.")
    else:
        print("❌ Some tests failed. This explains the 401 error.")

if __name__ == "__main__":
    asyncio.run(main())
