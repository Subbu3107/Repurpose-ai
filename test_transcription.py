import os
import httpx
from dotenv import load_dotenv

load_dotenv()

def transcribe_audio(file_path: str) -> str:
    with open(file_path, "rb") as f:
        response = httpx.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
            files={"file": f},
            data={"model": "whisper-large-v3"}
        )
    return response.json()["text"]

# Test it
print(transcribe_audio("test_audio.mp3"))
