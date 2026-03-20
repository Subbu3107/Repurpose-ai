import httpx
import os

with open(".env") as f:
    for line in f:
        line = line.strip()
        if "=" in line:
            key, val = line.split("=", 1)
            os.environ[key] = val

def call_groq(prompt):
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

def build_voice_profile(writing_samples: list) -> str:
    combined = "\n---\n".join(writing_samples)
    prompt = f"""
Analyze these writing samples from a content creator and build a detailed style guide.

Writing Samples:
{combined}

Extract and describe:
1. Sentence length (short/long/mixed)
2. Tone (casual/formal/humorous/motivational)
3. Common phrases or words they use
4. How they open posts
5. How they end posts
6. Use of punctuation, caps, emojis
7. Overall personality in writing

Return a STYLE GUIDE that can be given to an AI to copy this person's voice exactly.
Keep it under 200 words. Be specific.
"""
    return call_groq(prompt)

def repurpose_with_voice(content, platform, voice_profile):
    prompt = f"""
You are a content repurposer. Rewrite the content below for {platform}.

IMPORTANT - Write in this exact voice and style:
{voice_profile}

Content to repurpose:
{content}

Rules by platform:
- twitter: 5 tweet thread, numbered 1/5 to 5/5
- linkedin: 150-200 words, end with a question
- instagram: 3-4 paragraphs + 10 hashtags

Match the creator's voice EXACTLY. Output only the content.
"""
    return call_groq(prompt)


# ---- TEST ----

# These are sample posts from a creator (their past writing)
my_writing_samples = [
    "honestly didn't think i'd make it past day 3. but here we are. consistency is weird like that.",
    "nobody talks about the nights when nothing works and you just stare at the screen. that's the real hustle.",
    "shipped my first product today. it's ugly. it barely works. i love it.",
    "stop waiting to feel ready. readiness is a myth we tell ourselves to avoid starting."
]

print("Building your voice profile...")
profile = build_voice_profile(my_writing_samples)

print("\n=== YOUR VOICE PROFILE ===")
print(profile)

# Now repurpose WITH the voice
content = """
I woke up at 5am for 30 days straight.
Here is what happened to my productivity, mental health, and income.
It was the hardest and best thing I ever did.
"""

print("\n\n=== TWITTER (in YOUR voice) ===")
print(repurpose_with_voice(content, "twitter", profile))

print("\n\n=== LINKEDIN (in YOUR voice) ===")
print(repurpose_with_voice(content, "linkedin", profile))
