from flask import Flask, request, jsonify
import httpx
import os
import requests

with open(".env") as f:
    for line in f:
        line = line.strip()
        if "=" in line:
            key, val = line.split("=", 1)
            os.environ[key] = val

app = Flask(__name__)

# ---- Supabase ----
def save_job(email, content, voice, outputs):
    url = f"{os.environ['SUPABASE_URL']}/rest/v1/jobs"
    headers = {
        "apikey": os.environ["SUPABASE_KEY"],
        "Authorization": f"Bearer {os.environ['SUPABASE_KEY']}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    requests.post(url, headers=headers, json={
        "user_email": email,
        "content": content,
        "voice_profile": voice,
        "outputs": outputs
    })

# ---- Groq ----
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

# ---- Voice ----
def build_voice_profile(samples):
    if not samples:
        return "Write in a clear, engaging style."
    combined = "\n---\n".join(samples)
    return call_groq(f"""
Analyze these writing samples and build a style guide under 200 words.
Cover: sentence length, tone, phrases, openings, endings, punctuation.
Samples: {combined}
""")

# ---- Platforms ----
PLATFORM_RULES = {
    "twitter": "5 tweet thread, numbered 1/5 to 5/5, max 280 chars each",
    "linkedin": "150-200 words, end with a question",
    "instagram": "3-4 paragraphs + 10 hashtags",
    "newsletter": "subject line + 3 paragraphs + one action item",
    "youtube_shorts": "60 second script: hook 5s, content 45s, CTA 10s"
}

# ---- Routes ----
@app.route("/")
def root():
    return jsonify({"status": "Repurpose AI is running 🚀"})

@app.route("/voice", methods=["POST"])
def create_voice():
    data = request.json
    profile = build_voice_profile(data.get("samples", []))
    return jsonify({"voice_profile": profile})

@app.route("/repurpose", methods=["POST"])
def repurpose_content():
    data = request.json
    content = data.get("content", "")
    platforms = data.get("platforms", [])
    voice_samples = data.get("voice_samples", [])
    email = data.get("email", "anonymous")

    if not content:
        return jsonify({"error": "content is required"}), 400

    voice = build_voice_profile(voice_samples)
    outputs = {}

    for platform in platforms:
        if platform not in PLATFORM_RULES:
            outputs[platform] = "Platform not supported"
        else:
            outputs[platform] = call_groq(f"""
Repurpose this content for {platform}.
Voice guide: {voice}
Format: {PLATFORM_RULES[platform]}
Content: {content}
Output only the final content.
""")

    # Save to Supabase
    save_job(email, content, voice, outputs)

    return jsonify({"voice_profile": voice, "outputs": outputs})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
