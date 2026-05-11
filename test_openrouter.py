import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("OPENROUTER_MODEL", "openrouter/auto")

print(f"Testing OpenRouter with model: {model}")
print(f"Key starts with: {key[:10]}...")

try:
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {key}",
            "HTTP-Referer": "http://localhost:5000", # Optional
            "X-Title": "SmartAvatar", # Optional
        },
        json={
            "model": model,
            "messages": [
                {"role": "user", "content": "Hello!"}
            ]
        },
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
