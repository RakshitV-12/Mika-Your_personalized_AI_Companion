# Mika - AI Companion
import os
import sys
import json
import speech_recognition as sr
import simpleaudio as sa
import together
import torch
import pyautogui
import time
from dotenv import load_dotenv
from pydub import AudioSegment
from transformers import pipeline
from TTS.api import TTS

sys.stdout.reconfigure(encoding='utf-8')  # Enable emoji support

# Load environment variables
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
FFMPEG_PATH = os.getenv("FFMPEG_PATH")

if not TOGETHER_API_KEY:
    print("Error: Together AI API Key is missing! Set it in the .env file.")
    exit()
together.api_key = TOGETHER_API_KEY

if not FFMPEG_PATH or not os.path.isdir(FFMPEG_PATH):
    print("Error: FFmpeg path is invalid! Set the correct directory in .env.")
    exit()

AudioSegment.converter = os.path.join(FFMPEG_PATH, "ffmpeg.exe")
AudioSegment.ffprobe = os.path.join(FFMPEG_PATH, "ffprobe.exe")

MEMORY_FILE = "memory.json"

# Load and Save Memory
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as file:
            return json.load(file)
    return {"chat_history": [], "nicknames": ["Gentleman"], "mood": "happy"}

def save_memory(memory):
    with open(MEMORY_FILE, "w") as file:
        json.dump(memory, file, indent=4)

memory = load_memory()

# Load Emotion Model
emotion_analyzer = pipeline("text-classification", model="bhadresh-savani/bert-base-uncased-emotion")

def detect_emotion(text):
    emotions = emotion_analyzer(text)
    return emotions[0]["label"]

# Load Coqui TTS
tts = TTS(model_name="tts_models/en/jenny/jenny", progress_bar=False)

def speak_text(text, emotion="happy"):
    emoji_dict = {
        "😊": "smiling happily", "😢": "crying softly", "😡": "angrily growling",
        "🎉": "cheering excitedly", "😘": "blowing a kiss", "💖": "sending love"
    }
    for emoji, description in emoji_dict.items():
        text = text.replace(emoji, f" {description} ")

    if emotion == "joy":
        text = "Aww! " + text + " 💖"
    elif emotion == "anger":
        text = "Hmph! " + text + " 😡"
    elif emotion == "sadness":
        text = "Oh no... " + text + " 😢"
    
    try:
        tts.tts_to_file(text=text, file_path="response.wav", speed=1.1)
        wave_obj = sa.WaveObject.from_wave_file("response.wav")
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except Exception as e:
        print(f"Error in speech synthesis: {e}")

# Speech Recognition
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)
            text = recognizer.recognize_google(audio).lower()
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            return None
        except sr.RequestError:
            print("Speech recognition error.")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

# AI Chat Function
def chat_with_ai(user_input):
    global memory
    emotion = detect_emotion(user_input)
    memory["mood"] = emotion  # Adjust Mika's mood based on conversation
    
    memory["chat_history"].append({"role": "user", "content": user_input})

    personality = (
        f"You are Mika, a professional AI companion created by our group. "
        f"You respond in a short, warm, and respectful manner. "
        f"Always address the user as 'Sir'. "
        f"DO NOT add extra 'User:' or 'Mika:' text. "
        f"DO NOT generate anything except Mika's direct reply. "
        f"Keep responses under 3 sentences. "
        f"When Gentleman says 'Introduce yourself, Mika,' respond with: "
        f"'I'm Mika, your personal AI companion. You created me, and I'm here to assist, support, and engage with you in every way possible.'"
    )

    try:
        response = together.Complete.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            prompt=(
                personality + "\n"
                "### User Input:\n"
                f"{user_input}\n"
                "### Mika's Response:\n"
            ),
            temperature=0.6,
            max_tokens=50,
            stop=["### User Input:", "User:", "Mika:"]
        )

        ai_response = response["choices"][0]["text"].strip()
        ai_response = ai_response.replace("User:", "").replace("Mika:", "").strip()

        memory["chat_history"].append({"role": "assistant", "content": ai_response})
        save_memory(memory)

        return ai_response, emotion
    except Exception as e:
        print(f"Error: {e}")
        return "I'm sorry, I couldn't process that request.", "neutral"

# Animation Commands
ANIMATIONS = {
    "hello": "q",
    "good girl": "w",
    "dance": "y",
    "jump": "u",
    "no": "k"
}

def trigger_animation(command):
    for keyword, key in ANIMATIONS.items():
        if keyword in command:
            print(f"Triggering animation: {keyword} (Pressing {key})")
            pyautogui.press(key)
            time.sleep(1)
            return True
    return False

# Main Loop
while True:
    print("Waiting for 'Hello Mika' to wake Mika... 💤")
    wake_word = recognize_speech()

    if wake_word and isinstance(wake_word, str) and "hello mika" in wake_word:
        print("Wake Word Heard: Hello Mika 💻")
        speak_text("Hello, Sir. How can I assist you today?", "happy")

        while True:
            user_input = recognize_speech()
            if user_input:
                if "goodbye" in user_input:
                    speak_text("Goodbye, Sir. Have a great day ahead!", "happy")
                    break
                
                if trigger_animation(user_input):
                    continue
                
                ai_response, emotion = chat_with_ai(user_input)
                print(f"Mika: {ai_response}")
                speak_text(ai_response, emotion)