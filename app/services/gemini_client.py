import os
import requests


def ask_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-2.5-flash:generateContent"
        f"?key={api_key}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    response = requests.post(url, json=payload, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(f"Gemini HTTP {response.status_code}: {response.text}")

    data = response.json()

    candidates = data.get("candidates")
    if not candidates:
        raise RuntimeError(f"No candidates in Gemini response: {data}")

    content = candidates[0].get("content", {})
    parts = content.get("parts", [])
    if not parts:
        raise RuntimeError(f"No parts in Gemini response: {data}")

    text = parts[0].get("text")
    if not text:
        raise RuntimeError(f"No text in Gemini response: {data}")

    return text.strip()