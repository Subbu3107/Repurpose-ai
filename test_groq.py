import httpx
import os

# Load .env manually
with open(".env") as f:
    for line in f:
        line = line.strip()
        if "=" in line:
            key, val = line.split("=", 1)
            os.environ[key] = val

# Test Groq API
response = httpx.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
        "Content-Type": "application/json"
    },
    json={
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": "Say hello in 5 words"}]
    }
)

print(response.json()["choices"][0]["message"]["content"])
