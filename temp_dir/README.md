# elderly-assistant-bot
# Jarvis - Voice-Controlled AI Assistant for Elderly Care

An advanced Python-based voice assistant specifically designed for elderly care, combining speech recognition, AI capabilities, and a caring persona to create an interactive and supportive companion.

## 🌟 Key Features

- **Voice Interaction**: 
  - Natural speech recognition with "Jarvis" wake word
  - Clear UK English voice output
  - Adjusts for ambient noise automatically

- **AI-Powered Conversations**: 
  - Powered by Google's Gemini AI
  - Empathetic responses tailored for elderly care
  - Contextual memory for personal details

- **Daily Assistance**:
  - Time checking and announcements
  - Weather updates with location memory
  - Wikipedia information searches
  - Language translation support

- **Application Control**:
  - Chrome browser launch
  - Notepad access
  - YouTube navigation

- **Personal Customization**:
  - Remembers user's name
  - Stores location preferences
  - Weather information caching

## 🛠️ Technical Requirements

- Python 3.10 or higher
- Working microphone
- Internet connection
- Required API Keys:
  - Gemini API key
  - WeatherAPI key
  - MongoDB connection string

## 📦 Dependencies

```text
speech_recognition
pyttsx3
requests
wikipedia
pyautogui
googletrans==4.0.0rc1
pygame
python-dotenv
gTTS
pymongo
```

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/Adil-baby/elderly-assistant-bot.git
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:
```env
GEMINI_API_KEY=your_key_here
WEATHER_API_KEY=your_key_here
MONGODB_CONNECTION_STRING=your_connection_string
MONGODB_DATABASE_NAME=your_database_name
DEFAULT_USER_ID=default_user
```

## 🎯 Usage

1. Start Jarvis:
```bash
python jarvis/nepy.py
```

2. Wait for the greeting: "Hello, I am Jarvis. How can I help you?"

3. Use voice commands starting with "Jarvis":
   - "Jarvis what time is it?"
   - "Jarvis what's the weather in London?"
   - "Jarvis who is Albert Einstein?"
   - "Jarvis translate hello to Spanish"
   - "Jarvis open chrome"

## 🗣️ Voice Commands

| Category | Commands | Description |
|----------|----------|-------------|
| Time | "what time is it" | Gets current time |
| Weather | "weather in [city]" | Fetches weather information |
| Apps | "open [chrome/notepad/youtube]" | Launches applications |
| Information | "who is [person]", "what is [topic]" | Searches Wikipedia |
| Translation | "translate [text] to [language]" | Translates text |
| Personal | "my name is [name]" | Stores user's name |
| System | "exit", "stop", "quit" | Closes the assistant |

## 💡 Features in Detail

- **Ambient Noise Adjustment**: Automatically calibrates for background noise
- **Error Handling**: Graceful handling of network and API issues
- **Data Caching**: Stores weather and user preferences locally
- **Multiple Language Support**: Translation capabilities
- **Elderly-Focused AI**: Responses crafted for senior care

## 🔒 Security Note

- Keep your `.env` file secure and never commit it to version control
- Regularly update your API keys
- Use secure connections for MongoDB

## 📝 License

This project is licensed under the MIT License.
