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

HEALTH_KEYWORDS = [
    "not feeling well", "feeling sick", "i am sick",
    "headache", "fever", "pain", "dizzy", "weak",
    "can't breathe", "chest pain"
]

EMOTION_KEYWORDS = [
    "sad", "lonely", "tired", "depressed",
    "anxious", "scared", "worried", "upset"
]



def handle_health_issue():
    responses = [
        "I'm sorry you're not feeling well. Please sit down and take slow breaths.",
        "That doesn't sound nice. Would you like me to call a family member?",
        "Please drink some water. If this continues, we should seek help."
    ]
    return random.choice(responses)


def handle_emotional_support():
    responses = [
        "I'm here with you. You are not alone.",
        "It's alright to feel this way. Take your time.",
        "Would you like me to stay and talk for a while?"
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
    for k in HEALTH_KEYWORDS:
        if k in command:
            return "health"
    for k in EMOTION_KEYWORDS:
        if k in command:
            return "emotion"
    for k in CARE_KEYWORDS:
        if k in command:
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
    global interaction_count
    interaction_count += 1

    command = command.lower()


    if "time" in command:
        response = get_natural_time()
        speak(response)
        return response

    if "stop listening" in command or "go to sleep" in command:
        global assistant_awake
        assistant_awake = False
        speak("Alright. Call me if you need me.")
        return


    intent = detect_health_or_emotion(command)

    if intent == "health":
        response = handle_health_issue()
        speak(response)
        return response

    if intent == "emotion":
        response = handle_emotional_support()
        speak(response)
        return response

    if intent == "care":
        response = handle_care_mode()
        speak(response)
        return response

        # -------- DEFAULT AI BRAIN --------

    if is_internet_available():

        print("Calling Gemini...")  # DEBUG LINE

        response = get_gemini_response(command)

        speak(response)
        return response
 
    elif "open" in command:
        if "chrome" in command:
            response = "Opening Chrome"
            speak(response)
            pyautogui.press("win")
            pyautogui.write("chrome")
            pyautogui.press("enter")
            return response
        elif "notepad" in command:
            response = "Opening Notepad"
            speak(response)
            pyautogui.press("win")
            pyautogui.write("notepad")
            pyautogui.press("enter")
            return response
        elif "youtube" in command:
            webbrowser.open("https://youtube.com")
            response = "Opening YouTube"
            speak(response)
            return response
        else:
            response = "I can open Chrome, Notepad, or YouTube. What would you like to open?"
            speak(response)
            
        # Add a return statement here
        

    elif "my name is" in command:
        name = command.replace("my name is", "").strip()
        if name:
            user_id = os.environ.get("DEFAULT_USER_ID", "default_user")  # Use environment variable for user ID, default to "default_user"
            if set_user_name(user_id, name):
                response = f"Okay, I'll remember your name is {name}."
                speak(response)
                return response
            else:
                response = "Sorry, I couldn't store your name."
                speak(response)
                return response
        else:
            response = "Please tell me your name."
            speak(response)
            return response

    elif "what is my name" in command:
        user_id = os.environ.get("DEFAULT_USER_ID", "default_user")  # Use environment variable for user ID, default to "default_user"
        name = get_user_name(user_id)
        if name:
            response = f"Your name is {name}."
            speak(response)
            return response
        else:
            response = "I don't know your name yet. You can tell me by saying 'My name is <your name>'."
            speak(response)
            return response

    elif "i live in" in command:
        location_parts = command.replace("i live in", "").strip().split()
        if len(location_parts) >= 2:
            city = location_parts[0]
            state = " ".join(location_parts[1:])  # Handles multi-word state names
            user_id = os.environ.get("DEFAULT_USER_ID", "default_user")  # Use environment variable for user ID, default to "default_user"
            if db_utils.store_user_location(user_id, city, state):
                response = f"Okay, I'll remember you live in {city}, {state}."
                speak(response)
                return response
            else:
                response = "Sorry, I couldn't store your location."
                speak(response)
                return response
        else:
            response = "Please tell me your city and state. For example, 'I live in London England'."
            speak(response)
            return response

    elif "water" in command or "hydrated" in command:
        response = "Please take a few sips of water. Staying hydrated is important."
        speak(response)
        return response

    elif "stop listening" in command or "go to sleep" in command:

        speak("Alright. Call me if you need me.")
        
     
        assistant_awake = False
        
        return

    elif "weather" in command:
        city_match = None
        # Simple parsing for "weather in <city>"
        if "weather in" in command:
            city_match = command.split("weather in", 1)[1].strip()
        elif "weather of" in command:
            city_match = command.split("weather of", 1)[1].strip()

        if city_match:
            city = city_match.replace("the", "").strip()
            weather_data = db_utils.get_weather_data(city)
            if weather_data:
                temp = weather_data["temperature"]
                cond = weather_data["condition"]
                response = f"The temperature in {city} is {temp}°C with {cond} (from cache)."
                speak(response)
                return response
            else:
                # IMPORTANT: The 'demo' key for weatherapi.com is for demonstration purposes only and will not work for real requests.
                # You need to sign up at weatherapi.com and get a free API key.
                weather_key = os.getenv("WEATHER_API_KEY")
                if weather_key is None:
                    print("Log: Weather API key not found in .env file.")
                    response = "Weather API key not found in .env file."
                    speak(response)
                    return response

                url = f"http://api.weatherapi.com/v1/current.json?key={weather_key}&q={city}"
                try:
                    print(f"Log: Requesting weather data from {url}")
                    res = requests.get(url, timeout=10)
                    res.raise_for_status() # Raise an exception for HTTP errors
                    data = res.json()
                    temp = data["current"]["temp_c"]
                    cond = data["current"]["condition"]["text"]
                    weather_data = {"temperature": temp, "condition": cond}
                    if db_utils.store_weather_data(city, weather_data):
                        speak(f"The temperature in {city} is {temp}°C with {cond}.")
                        return f"The temperature in {city} is {temp}°C with {cond}."
                    else:
                        speak(f"The temperature in {city} is {temp}°C with {cond}, but I couldn't save it to the cache.")
                        return f"The temperature in {city} is {temp}°C with {cond}, but I couldn't save it to the cache."
                except requests.exceptions.RequestException as e:
                    response = f"Could not fetch weather for {city}. Error: {e}"
                    speak(response)
                    return response
                except KeyError:
                    response = f"Could not find weather information for {city}. Please ensure the city name is correct."
                    speak(response)
                    return response

        # Add a return statement here
        

    elif "who is" in command or "what is" in command:
        topic = command.replace("who is", "").replace("what is", "").strip()
        if topic:
            try:
                response = f"Searching Wikipedia for {topic}..."
                speak(response)
                summary = wikipedia.summary(topic, sentences=2)
                response = summary
                speak(response)
                return response
            except wikipedia.exceptions.DisambiguationError as e:
                response = f"There are multiple results for {topic}. Can you be more specific? Options include: {', '.join(e.options[:3])}."
                speak(response)
                return response
            except wikipedia.exceptions.PageError:
                response = f"Sorry, I couldn't find any information on Wikipedia about {topic}."
                speak(response)
                return response
            except Exception as e:
                response = f"An error occurred while searching Wikipedia: {e}"
                speak(response)
                return response
        else:
            response = "Please tell me who or what you want to know about."
            speak(response)
            return response

    elif "translate" in command:
        parts = command.split("to")
        if len(parts) == 2:
            text_to_translate = parts[0].replace("translate", "").strip()
            dest_language = parts[1].strip()
            if text_to_translate and dest_language:
                try:
                    response = f"Translating '{text_to_translate}' to {dest_language}..."
                    speak(response)
                    translated = translator.translate(text_to_translate, dest=dest_language)
                    response = translated.text
                    speak(translated.text, lang=dest_language)
                    return response
                except Exception as e:
                    response = f"Sorry, I couldn't translate that. Error: {e}. Please ensure the language is valid (e.g., 'french', 'spanish')."
                    speak(response)
                    return response
            else:
                response = "Please say: translate <text> to <language>"
                speak(response)
                return response
            
        else:
            response = "Please say: translate <text> to <language>"
            speak(response)
            return response

    elif "exit" in command or "stop" in command or "quit" in command:
        response = "Goodbye! Have a great day."
        speak(response)
        exit()

    elif "terminate" in command:
        response = "Terminating program."
        speak(response)
        exit()

    else:
        # 🩺 Health & Emotion First (OFFLINE SAFE)
        intent = detect_health_or_emotion(command)

        if intent == "health":
            response = handle_health_issue()
            speak(response)
            return response

        if intent == "care":
            response = handle_care_mode()
            speak(response)
            return response


        if intent == "emotion":
            response = handle_emotional_support()
            speak(response)
            return response

        # 🌐 Online AI (Gemini) if Internet Available
        if is_internet_available():
            speak("Let me think about that.")
            response = get_gemini_response(command)
            response = adjust_response(response)
            speak(response)
            return response

        # 📴 Final Offline Fallback
        response = "I'm here with you. Let's take this slowly."
        speak(response)
        return response

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


if __name__ == "__main__":

    speak(get_greeting())

    # ⭐ ADD THIS LINE
    speak("Say Jarvis whenever you need me.")

    while True:

        # -------- SLEEP MODE --------
        if not assistant_awake:

            print("Waiting for wake word...")

            wake = listen(show_error=False).lower()

            if not wake:
                continue

            if "jarvis" in wake:
                assistant_awake = True
                speak(wake_response())

            continue


        # -------- ACTIVE MODE --------
        command = listen(show_error=True).lower()

        if not command:
            continue

        if "stop" in command or "go to sleep" in command:
            speak("Alright. Call me if you need me.")
            assistant_awake = False
            continue

        process_command(command)
