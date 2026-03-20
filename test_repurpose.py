import httpx
import os

with open(".env") as f:
    for line in f:
        line = line.strip()
        if "=" in line:
            key, val = line.split("=", 1)
            os.environ[key] = val

PLATFORMS = {
    "twitter": """
Write a 5 tweet thread. Each tweet max 280 chars.
Start with a hook. End with a CTA. Number each tweet 1/5, 2/5 etc.
""",
    "linkedin": """
Write a LinkedIn post, 150-200 words.
Professional but human. Start with a bold first line. End with a question.
""",
    "instagram": """
Write an Instagram caption. 
Conversational, fun, 3-4 short paragraphs. Add 10 relevant hashtags at the end.
""",
    "newsletter": """
Write a short email newsletter section.
Subject line first, then 3 short paragraphs. Friendly tone. End with one action item.
""",
    "youtube_shorts": """
Write a 60-second YouTube Shorts script.
Format: Hook (5 sec) → Main point (45 sec) → CTA (10 sec).
Conversational, energetic, spoken word style.
"""
}

def repurpose(text, platform):
    prompt = f"""
You are an expert content repurposer.
Take this content and rewrite it for {platform}.

Instructions: {PLATFORMS[platform]}

Original Content:
{text}

Output only the final content. No explanations.
"""
    response = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        },
        timeout=30
    )
    return response.json()["choices"][0]["message"]["content"]

# ---- Test ----
sample = """
I woke up at 5am for 30 days straight.
Here is what happened to my productivity, mental health, and income.
It was the hardest and best thing I ever did.
"""

for platform in PLATFORMS:
    print(f"\n{'='*40}")
    print(f"  {platform.upper()}")
    print(f"{'='*40}")
    print(repurpose(sample, platform))
    print()
