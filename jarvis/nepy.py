import speech_recognition as sr
import pyttsx3
import requests
import wikipedia
import os
from dotenv import load_dotenv
import datetime
import pyautogui
import webbrowser
from googletrans import Translator
import time
import json # Import json for parsing API responses
import db_utils
import sounddevice as sd
import numpy as np
import random
import pywhatkit

from local_llm import ask_ollama

from process_command import process_command

# Load environment variables from temp_dir/.env
dotenv_path = os.path.join(os.path.dirname(__file__), '../temp_dir/.env')
load_dotenv(dotenv_path)

import socket

def is_internet_available():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False


# Initialize Translator
translator = Translator()

# Initialize pyttsx3 engine once for efficiency
# This avoids re-initializing the engine for every speak call, which can cause delays.
try:
    engine = pyttsx3.init()
    engine.setProperty("rate", 170)
except Exception as e:
    print(f"Error initializing TTS engine: {e}")
    engine = None # Set engine to None if initialization fails

# Speak function
from gtts import gTTS
import pygame
import time
import os
import re

MILD_HEALTH = [
    "tired", "weak", "headache", "cold",
    "not feeling well", "fever", "body pain"
]

WARNING_HEALTH = [
    "dizzy", "lightheaded", "vomiting",
    "very weak", "cannot stand"
]

EMERGENCY_HEALTH = [
    "chest pain",
    "can't breathe",
    "not breathing",
    "severe pain",
    "heart pain",
    "collapsed"
]

HEALTH_KEYWORDS = [
    "not feeling well", "feeling sick", "i am sick",
    "headache", "fever", "pain", "dizzy", "weak",
    "can't breathe", "chest pain"
]

EMOTION_KEYWORDS = [
    "sad", "lonely", "tired", "depressed",
    "anxious", "scared", "worried", "upset"
]

def handle_emergency():

    responses = [
        "This sounds serious. Please try to stay calm. Should I call someone for you?",
        "I am concerned about you. Please seek immediate help. Do you want me to alert a family member?",
        "Please do not stay alone. Try to contact someone nearby right now."
    ]

    return random.choice(responses)

def handle_warning():

    responses = [
        "You may be feeling dizzy. Please sit down slowly and avoid sudden movement.",
        "Try to drink some water and rest for a moment.",
        "If the dizziness continues, it may be best to call someone."
    ]

    return random.choice(responses)

def handle_mild():

    responses = [
        "Please get some rest. Your body may need it.",
        "A little water and relaxation could help you feel better.",
        "Take things slowly. I am right here with you."
    ]

    return random.choice(responses)


def clean_text(text):
    return re.sub(r'[^A-Za-z0-9\s]', '', text)

def speak(text):
    print("Jarvis:", text)
    try:
        cleaned = clean_text(text)
        tts = gTTS(text=cleaned, lang='en', tld='co.uk')  # UK voice for smoother tone
        filename = "temp_voice.mp3"
        tts.save(filename)

        pygame.mixer.init()
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.3)

        pygame.mixer.music.unload()
        os.remove(filename)

    except Exception as e:
        print(f"Voice error: {e}")


def listen(show_error=True):
    r = sr.Recognizer()
    fs = 44100
    duration = 5

    if show_error:
        print("Listening... 🎤")

    try:
        audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()

        if show_error:
            print("Recognizing...")

        audio = sr.AudioData(audio_data.tobytes(), fs, 2)
        query = r.recognize_google(audio)

        print("You:", query)
        return query

    except sr.UnknownValueError:
        if show_error:
            speak("Sorry, I couldn’t understand what you said.")
        return ""

    except sr.RequestError:
        if show_error:
            speak("Speech recognition service is unavailable.")
        return ""

    except Exception as e:
        print(f"Listening error: {e}")
        if show_error:
            speak("There was a problem listening.")
        return ""


# Call Gemini API
def get_gemini_response(prompt):
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "I cannot reach my online assistant right now."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    caretaker_prompt = (
        "You are a kind British caretaker speaking to an elderly person. "
        "Use calm, short sentences. Be reassuring. Less than 50 words.\n"
        f"User: {prompt}"
    )

    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": caretaker_prompt}]}
        ]
    }

    try:
        res = requests.post(url, json=payload, timeout=15)
        res.raise_for_status()
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            return "I'm getting too many questions at once. Please give me a moment."
        return "I am having trouble reaching my intelligence service."

    except Exception as e:
        print("GEMINI ERROR:", e)
        return "I am having trouble reaching my intelligence service."



def get_response(command):
    if interaction_count % 5 == 0:
        speak("Just checking in. Are you comfortable?")

    intent = detect_health_or_emotion(command)

    # 1️⃣ HEALTH FIRST (OFFLINE)
    if intent == "health":
        return handle_health_issue()

    # 2️⃣ EMOTIONAL SUPPORT (OFFLINE)
    if intent == "emotion":
        return handle_emotional_support()

    # 3️⃣ ONLINE AI IF AVAILABLE
    if is_internet_available():
        return get_gemini_response(command)

    # 4️⃣ FINAL OFFLINE FALLBACK
    return "I may not have all the answers, but I am here with you."


# Function to get user's name
def get_user_name(user_id):
    user_data = db_utils.get_user_data(user_id)
    if user_data and "name" in user_data:
        return user_data["name"]
    else:
        return None

# Function to set user's name
def set_user_name(user_id, name):
    user_data = {"name": name}
    return db_utils.store_user_data(user_id, user_data)

# Load reward data from JSON file
def load_reward_data():
    try:
        with open("reward_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"reward_score": 0}

# Save reward data to JSON file
def save_reward_data(data):
    with open("reward_data.json", "w") as f:
        json.dump(data, f, indent=2)

# Get the current reward score
def get_reward_score():
    data = load_reward_data()
    return data["reward_score"]

# Update the reward score based on feedback
def update_reward(response, positive_feedback):
    data = load_reward_data()
    reward = 0.1 if positive_feedback else -0.05  # Adjust reward values as needed
    data["reward_score"] += reward
    data["reward_score"] = max(0, data["reward_score"])  # Ensure reward score doesn't go below zero
    save_reward_data(data)

# Adjust bot behavior based on reward score
def adjust_response(response):
    reward_score = get_reward_score()
    if reward_score > 5:
        # Example: Add a positive affirmation
        response = f"{response} I'm glad I could help!"
    elif reward_score < -2:
        # Example: Apologize and offer alternative
        response = f"I'm sorry I couldn't help. Perhaps I can try a different approach?"
    return response

def get_feedback():
    speak("Was that helpful?")
    feedback = listen().lower()
    if "yes" in feedback:
        return True
    elif "no" in feedback:
        return False
    else:
        speak("Sorry, I didn't understand. Please say yes or no.")
        return get_feedback()
    
global assistant_awake

def detect_health_or_emotion(command):

    cmd = command.lower()

    # 🚨 EMERGENCY FIRST (highest priority)
    for word in EMERGENCY_HEALTH:
        if word in cmd:
            return "emergency"

    # ⚠️ WARNING
    for word in WARNING_HEALTH:
        if word in cmd:
            return "warning"

    # 🙂 MILD
    for word in MILD_HEALTH:
        if word in cmd:
            return "mild"

    # ❤️ EMOTION
    for word in EMOTION_KEYWORDS:
        if word in cmd:
            return "emotion"

    # 🧓 CARE
    for word in CARE_KEYWORDS:
        if word in cmd:
            return "care"

    return None


def handle_health_issue():
    return random.choice([
        "I'm sorry you're not feeling well. Please sit down and take slow breaths.",
        "That sounds uncomfortable. Please drink some water and rest.",
        "I'm here with you. If this gets worse, we should ask for help."
    ])

def handle_emotional_support():
    return random.choice([
        "I'm here with you. You are not alone.",
        "It's alright to feel this way. Take your time.",
        "Would you like me to stay and talk for a bit?"
    ])

def get_natural_time():
    now = datetime.datetime.now()

    hour = now.strftime("%I").lstrip("0")  # removes leading zero
    minute = now.strftime("%M")

    if minute == "00":
        minute_speech = "o clock"
    elif minute.startswith("0"):
        minute_speech = "oh " + minute[1]
    else:
        minute_speech = minute

    period = now.strftime("%p").lower()

    if period == "am":
        period_speech = "in the morning"
    elif int(hour) < 6:
        period_speech = "in the afternoon"
    else:
        period_speech = "in the evening"

    return f"It is {hour} {minute_speech} {period_speech}"

CARE_KEYWORDS = [
    "tired",
    "weak",
    "not okay",
    "bad day",
    "no energy",
    "exhausted"
]

interaction_count = 0


def handle_care_mode():
    return random.choice([
        "You sound tired. Please try to sit down and rest for a moment.",
        "Let us slow things down. Would you like some calming music?",
        "Please remember to take care of yourself. I am right here with you.",
        "Would you like me to remind you to drink some water?"
    ])


# Handle commands
def process_command(command):

    global assistant_awake
    command = command.lower()

    # ---------- STOP ----------
    if "stop listening" in command or "go to sleep" in command:
        assistant_awake = False
        speak("Alright. Call me if you need me.")
        return


    # ---------- TIME ----------
    if "time" in command:
        response = get_natural_time()
        speak(response)
        return

    # ---------- PLAY ON YOUTUBE ----------
# ---------- PLAY MUSIC ----------
    if command.startswith("play"):

        song = command.replace("play", "").strip()

        if song:
            speak(f"Alright. Playing {song} for you.")

            try:
                pywhatkit.playonyt(song)

            except Exception as e:
                print("YouTube error:", e)
                speak("I could not play that right now.")

            return


    # ---------- OPEN APPS ----------
    if "open chrome" in command:
        speak("Opening Chrome")
        pyautogui.press("win")
        pyautogui.write("chrome")
        pyautogui.press("enter")
        return

    if "open notepad" in command:
        speak("Opening Notepad")
        pyautogui.press("win")
        pyautogui.write("notepad")
        pyautogui.press("enter")
        return

    if "open youtube" in command:
        webbrowser.open("https://youtube.com")
        speak("Opening YouTube")
        return


    # ---------- CARE DETECTION ----------
    # ✅ HEALTH / EMOTION FIRST
    intent = detect_health_or_emotion(command)

    if intent == "emergency":
        speak(handle_emergency())
        return

    elif intent == "warning":
        speak(handle_warning())
        return

    elif intent == "mild":
        speak(handle_mild())
        return

    elif intent == "emotion":
        speak(handle_emotional_support())
        return

    elif intent == "care":
        speak(handle_care_mode())
        return


    # ✅ THEN TRY LOCAL LLM
    print("Trying LOCAL LLM...")
    local_reply = ask_ollama(command)

    if local_reply and len(local_reply.strip()) > 5:
        speak(local_reply)
        return


    # ---------- CLOUD BACKUP ----------
    if is_internet_available():

        print("Falling back to GEMINI...")

        response = get_gemini_response(command)

        speak(response)
        


    # ---------- FINAL FALLBACK ----------
    response = "I am here with you."
    speak(response)
    return response



    # ---------- FINAL FALLBACK ----------
    speak("I am here with you.")


# Load reward data from JSON file
def load_reward_data():
    try:
        with open("reward_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"reward_score": 0}

# Save reward data to JSON file
def save_reward_data(data):
    with open("reward_data.json", "w") as f:
        json.dump(data, f, indent=2)

def get_greeting():
    hour = datetime.datetime.now().hour

    if hour < 12:
        return "Good morning. How are you feeling today?"
    elif hour < 18:
        return "Good afternoon. I hope you are comfortable."
    else:
        return "Good evening. How has your day been?"

def wake_response():
    return random.choice([
        "Yes?",
        "I'm listening.",
        "How can I help?",
        "Tell me."
    ])
assistant_awake = False


assistant_awake = True   # Awake only at startup


if __name__ == "__main__":

    speak(get_greeting())

    while True:

        # -------- SLEEP MODE --------
        if not assistant_awake:

            print("Waiting for wake word...")

            wake = listen(show_error=False)

            if not wake:
                continue

            wake = wake.lower()

            if "jarvis" in wake:
                assistant_awake = True
                speak(wake_response())

            continue


        # -------- ACTIVE MODE --------
        command = listen(show_error=True)

        if not command:
            continue

        command = command.lower()


        # ⭐ STOP COMMAND
        if "stop" in command or "go to sleep" in command:

            speak("Alright. Call me if you need me.")
            assistant_awake = False
            continue


        process_command(command)

