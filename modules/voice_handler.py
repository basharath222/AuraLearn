# modules/voice_handler.py
import speech_recognition as sr
from gtts import gTTS
import tempfile
import os

def listen_to_user():
    """Listens to microphone input."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            print("Adjusting for noise...")
            r.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening...")
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
            text = r.recognize_google(audio)
            return text
        except Exception as e:
            print(f"Mic Error: {e}")
            return None

def text_to_audio_file(text):
    """
    Generates MP3 using Google TTS (Reliable).
    """
    try:
        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_path = temp_file.name
        temp_file.close() 

        # Generate Audio (Lang='en', tld='com' is standard US accent)
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(temp_path)
        
        return temp_path
    except Exception as e:
        print(f"TTS Error: {e}")
        return None