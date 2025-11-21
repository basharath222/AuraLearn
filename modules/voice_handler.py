# modules/voice_handler.py
import speech_recognition as sr
from gtts import gTTS
import os
import tempfile

def listen_to_user():
    """
    Listens to the microphone and returns text.
    """
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            # Adjust for ambient noise
            r.adjust_for_ambient_noise(source, duration=1)
            audio = r.listen(source, timeout=5)
            text = r.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return None
        except sr.RequestError:
            return "API Error"
        except Exception as e:
            return None

def text_to_speech(text):
    """
    Converts text to audio file path.
    """
    try:
        tts = gTTS(text=text, lang='en')
        # Create a temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp_file.name)
        return temp_file.name
    except Exception as e:
        print(f"TTS Error: {e}")
        return None