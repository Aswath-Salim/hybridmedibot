import requests


def ask_ollama(prompt):

    print("USING LOCAL LLM")

    # ⭐ Force short answers at the prompt level (MOST IMPORTANT)
    short_prompt = f"""
You are a helpful elderly care assistant.

Reply in ONLY 2 to 3 short sentences.
Keep it simple.
Avoid lists.
Avoid steps unless necessary.
Be calm and clear.

User: {prompt}
Assistant:
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "tinyllama",

                # ⭐ Prompt
                "prompt": short_prompt,

                # ⭐ VERY IMPORTANT for Raspberry Pi
                "stream": False,
                "options": {
                    "num_predict": 120,   # HARD token limit (~2–3 sentences)
                    "temperature": 0.4,   # Less randomness → faster
                    "top_k": 20,          # Smaller compute
                    "top_p": 0.8
                }
            },
            timeout=60
        )

        data = response.json()
        reply = data.get("response", "").strip()

        if reply:
            print("LOCAL LLM USED")
            return reply

        return None

    except Exception as e:
        print("OLLAMA ERROR:", e)
        return None
