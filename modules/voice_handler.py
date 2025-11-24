import speech_recognition as sr
from gtts import gTTS
import tempfile
import os
import io

# Text to Speech
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

# Cloud Transcriber (Fast)
def transcribe_audio_bytes(audio_bytes):
    r = sr.Recognizer()
    try:
        # Convert web audio bytes to WAV
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        with sr.AudioFile(tmp_path) as source:
            # Listen for a maximum of 5 seconds to keep it snappy
            audio_data = r.record(source, duration=5) 
            text = r.recognize_google(audio_data)
            
        os.remove(tmp_path)
        return text
    except:
        return None

# Local Transcriber (Fallback)
def listen_to_user():
    r = sr.Recognizer()
    r.energy_threshold = 300 
    r.dynamic_energy_threshold = True
    with sr.Microphone() as source:
        try:
            # Short timeout for faster response
            audio = r.listen(source, timeout=3, phrase_time_limit=4)
            text = r.recognize_google(audio)
            return text
        except: return None