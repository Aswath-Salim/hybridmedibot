from caretaker import detect_intent, caretaker_response
from rl_engine import choose_style, reward_style
from gemini_brain import get_gemini_response
from utils import is_internet_available, natural_time


POSITIVE = ["thank","good","nice","helpful","great"]
NEGATIVE = ["wrong","bad","stop","annoying"]


def process_command(command):

    command = command.lower()

    # OFFLINE TIME
    if "time" in command:
        return natural_time()

    # CARETAKER OVERRIDE
    intent = detect_intent(command)

    if intent:
        return caretaker_response(intent)

    # RL STYLE
    style = choose_style()

    persona = {
        "caring":"Speak like a warm elderly caretaker.",
        "neutral":"Speak clearly and briefly.",
        "cheerful":"Be positive and uplifting."
    }

    prompt = persona[style] + "\nUser: " + command

    if is_internet_available():
        response = get_gemini_response(prompt)
    else:
        response = "I may not know everything, but I am here with you."

    # PASSIVE RL REWARD
    if any(p in command for p in POSITIVE):
        reward_style(style,0.3)

    if any(n in command for n in NEGATIVE):
        reward_style(style,-0.2)

    return response
