import requests


def ask_ollama(prompt):

    print("USING LOCAL LLM")

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "tinyllama",   # change if using another model
                "prompt": prompt,
                "stream": False        # ⭐ CRITICAL
            },
            timeout=60
        )

        data = response.json()

        reply = data.get("response", "").strip()

        print("OLLAMA RAW:", reply)

        if reply:
            return reply

        return None

    except Exception as e:
        print("OLLAMA ERROR:", e)
        return None
