import random

HEALTH = ["not feeling well","sick","fever","pain","dizzy","weak"]
EMOTION = ["sad","lonely","depressed","tired","worried"]
EMERGENCY = ["chest pain","cant breathe","collapse","severe pain"]

def detect_intent(command):

    cmd = command.lower()

    if any(e in cmd for e in EMERGENCY):
        return "emergency"

    if any(h in cmd for h in HEALTH):
        return "health"

    if any(e in cmd for e in EMOTION):
        return "emotion"

    return None


def caretaker_response(intent):

    if intent == "emergency":
        return "This sounds serious. Please call emergency services immediately or alert someone nearby."

    if intent == "health":
        return random.choice([
            "I'm sorry you're unwell. Please sit down and rest.",
            "Let us slow things down. Would you like me to call someone?",
            "Please drink some water and try to relax."
        ])

    if intent == "emotion":
        return random.choice([
            "I'm right here with you.",
            "You are not alone.",
            "Would you like to talk for a while?"
        ])
