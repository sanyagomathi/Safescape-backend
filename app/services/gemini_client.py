import os
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def ask_gemini(prompt: str) -> str:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-1.5-flash:generateContent"
        f"?key={GEMINI_API_KEY}"
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

    r = requests.post(url, json=payload, timeout=30)

    if r.status_code != 200:
        raise Exception(f"Gemini error: {r.text}")

    data = r.json()

    return data["candidates"][0]["content"]["parts"][0]["text"]