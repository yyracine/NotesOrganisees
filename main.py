"""Minimal example using DeepSeek's API (OpenAI-compatible)."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
API_KEY = os.getenv("DEEPSEEK_API_KEY")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def chat(prompt: str) -> tuple[str, str]:
    """Send a chat completion request. Returns (reply_text, request_id)."""
    url = f"{BASE_URL}/chat/completions"
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
    }
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    reply = data["choices"][0]["message"]["content"]
    request_id = data.get("id") or resp.headers.get("x-request-id")
    return reply, request_id


if __name__ == "__main__":
    prompt = 'Reponds en JSON avec une cle "message" disant bonjour en une phrase.'
    reply, request_id = chat(prompt)
    print(f"Model: {MODEL}")
    print(f"Reply: {reply}")
    print(f"Request ID: {request_id}")