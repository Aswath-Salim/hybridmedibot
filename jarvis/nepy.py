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
import speech_recognition as sr
import random

# Load environment variables from temp_dir/.env
dotenv_path = os.path.join(os.path.dirname(__file__), '../temp_dir/.env')
load_dotenv(dotenv_path)

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

# Listen to mic
# def listen():
#     r = sr.Recognizer()
#     with sr.Microphone() as source:
#         print("Available audio devices:")
#         for i, name in enumerate(sr.Microphone.list_microphone_names()):
#         print(f"Log: {i}: {name}")
#         print("Listening...")
#         # Corrected: Removed space in adjust_for_ambient_noise
#         r.adjust_for_ambient_noise(source, duration=1)  # Increased duration
#         try:
#             audio = r.listen(source, timeout=7, phrase_time_limit=10)  # Increased timeout and phrase_time_limit
#             print("Recognizing...")
#             # Add this line to check if audio is None
#             if audio is None:
#                 print("Log: Audio data is None")
#                 return ""
#             query = r.recognize_google(audio)
#             print("You:", query)
#             return query
#         except sr.WaitTimeoutError:
#             speak("I didn't hear anything. Please try again.")
#             return ""
#         except sr.UnknownValueError:
#             speak("Sorry, I couldn't understand what you said.")
#             return ""
#         except sr.RequestError as e:
#             speak(f"Could not request results from Google Speech Recognition service; {e}")
#             return ""
#         except Exception as e:
#             print(f"An unexpected error occurred during listening: {e}")
#             return ""

def listen():
    r = sr.Recognizer()
    fs = 44100  # Sample rate
    duration = 5  # seconds of listening time

    print("Listening... 🎤")
    try:
        # Record audio for a few seconds
        audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()  # Wait until recording is finished
        print("Recognizing...")

        # Convert recorded data into recognizer-compatible format
        audio = sr.AudioData(audio_data.tobytes(), fs, 2)
        query = r.recognize_google(audio)

        print("You:", query)
        return query

    except sr.UnknownValueError:
        speak("Sorry, I couldn’t understand what you said.")
        return ""
    except sr.RequestError:
        speak("Speech recognition service is unavailable.")
        return ""
    except Exception as e:
        print(f"Listening error: {e}")
        speak("There was a problem listening. Please try again.")
        return ""
    
# Call Gemini API
def get_gemini_response(prompt: str) -> str:
    # IMPORTANT: Replace "YOUR_GEMINI_API_KEY_HERE" with your actual Gemini API key.
    # You can get one from Google AI Studio: https://aistudio.google.com/
    apiKey = os.getenv("GEMINI_API_KEY")
    if apiKey is None:
        print("Log: Gemini API key not found in .env file.")
        return "Gemini API key not found in .env file."
    apiUrl = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={apiKey}"

    persona_prompt = "Act as a kind and caring British caretaker for an elderly person. Speak in short, gentle sentences with a warm, supportive tone. Use language a traditional British caretaker would use. If the user seems sad or tired, offer emotional support like a friend or nurse would. Your response should be less than 50 words."
    prompt = f"{persona_prompt} {prompt}"
    chatHistory = []
    # Corrected: Use .append() for Python lists instead of .push()
    chatHistory.append({ "role": "user", "parts": [{ "text": prompt }] })

    payload = {
        "contents": chatHistory
    }

    try:
        # Make the fetch call using requests library for Python
        response = requests.post(apiUrl, headers={'Content-Type': 'application/json'}, json=payload, timeout=60)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

        result = response.json()

        if result.get("candidates") and len(result["candidates"]) > 0 and \
           result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts") and \
           len(result["candidates"][0]["content"]["parts"]) > 0:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            return text
        else:
            print(f"Gemini API response structure unexpected: {result}")
            return "I received an unexpected response from the AI."
    except requests.exceptions.Timeout:
        return "The AI took too long to respond. Please try again."
    except requests.exceptions.ConnectionError:
        return "I couldn't connect to the AI service. Please check your internet connection."
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Response: {response.text}")
        return f"An HTTP error occurred while contacting the AI: {http_err}. Please check the API key and service status."
    except json.JSONDecodeError:
        print(f"Failed to decode JSON from response: {response.text}")
        return "I received an unreadable response from the AI."
    except Exception as e:
        print(f"An unexpected error occurred while getting Gemini response: {e}")
        return "I encountered an error while processing your request with the AI."


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

# Handle commands
def process_command(command):
    command = command.lower()

    if "time" in command:
        now = datetime.datetime.now().strftime("%H:%M:%S")
        response = f"The time is {now}"
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
        # Use Gemini for general queries
        response = "Let me think about that."
        speak(response)
        response = get_gemini_response(command)
        response = adjust_response(response)
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

if __name__ == "__main__":
    if engine is None:
        print("TTS engine failed to initialize. Exiting.")
        exit()

    speak("Hello, I am Jarvis. How can I help you?")
    while True:
        command = listen()
        if command and command.lower().startswith("jarvis"): # Only process if a command was recognized and starts with "jarvis"
            command = command[6:].strip() # Remove "jarvis" from the command
            response = process_command(command)

            # Get user feedback and update reward
            helpful = get_feedback()
            update_reward(response, helpful)
            print(f"New reward score: {get_reward_score()}")