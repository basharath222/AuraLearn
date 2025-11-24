import speech_recognition as sr
from gtts import gTTS
import tempfile
import os
import io

# Engine Setup (Same as before)
def text_to_audio_file(text):
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_path = temp_file.name
        temp_file.close() 
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(temp_path)
        return temp_path
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

# === NEW FUNCTION FOR CLOUD ===
def transcribe_audio_bytes(audio_bytes):
    """
    Transcribes audio from a byte stream (Browser recording)
    instead of a hardware microphone.
    """
    r = sr.Recognizer()
    try:
        # Create a temporary WAV file from the bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        # Process the file
        with sr.AudioFile(tmp_path) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data)
            
        # Clean up
        os.remove(tmp_path)
        return text
    except Exception as e:
        print(f"Transcribe Error: {e}")
        return None

# Keep this for local testing if needed, but cloud won't use it
def listen_to_user():
    return None