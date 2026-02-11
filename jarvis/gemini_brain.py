import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_gemini_response(prompt):

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return "I cannot reach my online assistant right now."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    payload = {
        "contents":[{"parts":[{"text":prompt}]}]
    }

    try:
        res = requests.post(url, json=payload, timeout=15)
        data = res.json()

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except:
        return "I'm here with you."
