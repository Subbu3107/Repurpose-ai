from flask import Flask, request, jsonify, render_template
import httpx
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

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
        timeout=60
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
def home():
    return render_template("index.html")

@app.route("/voice", methods=["POST"])
def create_voice():
    data = request.json
    profile = build_voice_profile(data.get("samples", []))
    return jsonify({"voice_profile": profile})

@app.route("/score", methods=["POST"])
def score_content():
    data = request.json
    content = data.get("content", "")
    prompt = f"""
Analyze this content and score it out of 10 for each:
1. Hook strength (how grabbing is the opening)
2. Engagement potential (will people interact)
3. Viral probability (will people share)
4. Clarity (is it easy to understand)

Also give 2 short suggestions to improve it.

Content: {content}

Respond ONLY in this exact JSON format:
{{"hook": 7, "engagement": 8, "viral": 6, "clarity": 9, "suggestions": "your suggestions here"}}
"""
    result = call_groq(prompt)
    try:
        clean = result.strip().replace("```json","").replace("```","")
        score = json.loads(clean)
    except:
        score = {"hook":7,"engagement":7,"viral":6,"clarity":8,"suggestions":"Add a stronger opening hook and use more specific numbers."}
    return jsonify({"score": score})

@app.route("/hooks", methods=["POST"])
def generate_hooks():
    data = request.json
    content = data.get("content", "")
    if not content:
        return jsonify({"error": "content is required"}), 400
    prompt = f"""
Generate 5 different hooks for this content.

Content: {content}

Generate exactly these 5 types:
1. CURIOSITY: Makes reader curious
2. CONTROVERSY: Bold/surprising take
3. STORY: Opens with a scene
4. DATA: Starts with a number/stat
5. QUESTION: Thought provoking question

Format exactly like this:
CURIOSITY: [hook]
CONTROVERSY: [hook]
STORY: [hook]
DATA: [hook]
QUESTION: [hook]
"""
    result = call_groq(prompt)
    hooks = {}
    for line in result.strip().split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            hooks[key.strip()] = val.strip()
    return jsonify({"hooks": hooks})

@app.route("/analyze", methods=["POST"])
def analyze_viral():
    data = request.json
    url = data.get("url", "")
    if not url:
        return jsonify({"error": "URL required"}), 400
    try:
        content_data = {}

        # ---- YouTube ----
        if "youtube.com" in url or "youtu.be" in url:
            import yt_dlp
            ydl_opts = {'quiet': True, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                content_data = {
                    "platform": "YouTube",
                    "title": info.get("title", ""),
                    "description": info.get("description", "")[:500],
                    "tags": info.get("tags", [])[:10],
                    "views": info.get("view_count", 0),
                    "likes": info.get("like_count", 0),
                    "duration": info.get("duration", 0),
                    "channel": info.get("uploader", "")
                }

        # ---- Instagram ----
        elif "instagram.com" in url:
            from bs4 import BeautifulSoup
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            title = ""
            description = ""
            for tag in soup.find_all("meta"):
                if tag.get("property") == "og:title":
                    title = tag.get("content", "")
                if tag.get("property") == "og:description":
                    description = tag.get("content", "")
            content_data = {
                "platform": "Instagram",
                "title": title,
                "description": description,
                "url": url
            }
        else:
            return jsonify({"error": "Only YouTube and Instagram URLs supported"}), 400

        platform = content_data.get("platform")
        title = content_data.get("title", "")
        description = content_data.get("description", "")
        views = content_data.get("views", "unknown")
        likes = content_data.get("likes", "unknown")
        tags = content_data.get("tags", [])

        prompt = f"""
You are a viral content expert. Analyze this {platform} content.

Platform: {platform}
Title/Caption: {title}
Description: {description}
Views: {views}
Likes: {likes}
Tags: {tags}

Respond ONLY in this exact JSON format:
{{
  "viral_score": 72,
  "verdict": "Good content but weak hook is limiting reach",
  "whats_working": ["point 1", "point 2", "point 3"],
  "killing_reach": ["problem 1", "problem 2", "problem 3"],
  "rewritten_title": "viral version of the title",
  "rewritten_caption": "viral version of caption in 3 lines",
  "hashtags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10"],
  "best_time": {{
    "day": "Tuesday",
    "time": "7PM IST",
    "reason": "highest engagement window for Indian creators"
  }},
  "viral_tips": ["tip 1", "tip 2", "tip 3"]
}}
"""
        result = call_groq(prompt)
        clean = result.strip().replace("```json","").replace("```","").strip()
        analysis = json.loads(clean)

        return jsonify({
            "platform": platform,
            "original": content_data,
            "analysis": analysis
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/youtube", methods=["POST"])
def youtube_repurpose():
    data = request.json
    url = data.get("url", "")
    platforms = data.get("platforms", ["twitter", "linkedin"])
    voice_samples = data.get("voice_samples", [])
    if not url:
        return jsonify({"error": "YouTube URL required"}), 400
    try:
        import yt_dlp
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{tmpdir}/audio.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'quiet': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Video')
                duration = info.get('duration', 0)
            if duration > 1800:
                return jsonify({"error": "Video too long. Max 30 minutes."}), 400
            audio_path = f'{tmpdir}/audio.mp3'
            with open(audio_path, "rb") as f:
                transcript_response = httpx.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
                    files={"file": ("audio.mp3", f, "audio/mpeg")},
                    data={"model": "whisper-large-v3"},
                    timeout=120
                )
            transcript = transcript_response.json().get("text", "")
            if not transcript:
                return jsonify({"error": "Could not transcribe video"}), 400
            voice = build_voice_profile(voice_samples)
            outputs = {}
            for platform in platforms:
                if platform in PLATFORM_RULES:
                    outputs[platform] = call_groq(f"""
Repurpose this video transcript for {platform}.
Voice guide: {voice}
Format: {PLATFORM_RULES[platform]}
Transcript: {transcript[:3000]}
Output only the final content.
""")
            return jsonify({
                "title": title,
                "transcript": transcript[:500] + "...",
                "voice_profile": voice,
                "outputs": outputs
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/repurpose", methods=["POST"])
def repurpose_content():
    data = request.json
    content = data.get("content", "")
    platforms = data.get("platforms", [])
    voice_samples = data.get("voice_samples", [])
    email = data.get("email", "anonymous")
    tone = data.get("tone", "viral")
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
Tone: {tone}
Voice guide: {voice}
Format: {PLATFORM_RULES[platform]}
Content: {content}
Output only the final content.
""")
    save_job(email, content, voice, outputs)
    return jsonify({"voice_profile": voice, "outputs": outputs})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
