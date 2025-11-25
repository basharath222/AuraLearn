# modules/llm_handler.py
import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

# Load .env file (for local development)
load_dotenv()

# --- ROBUST KEY LOADING ---
GROQ_API_KEY = None

# 1. Try Environment Variable (Render/Local)
if os.getenv("GROQ_API_KEY"):
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 2. Try Streamlit Secrets (Cloud)
if not GROQ_API_KEY:
    try:
        if "GROQ_API_KEY" in st.secrets:
            GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    except: pass

# Initialize Client
client = None
if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)

DEFAULT_MODEL = "llama-3.3-70b-versatile"

def _chat(messages, temperature=0.3, max_tokens=1024, timeout=30.0):
    if not client:
        return "⚠️ System Error: Groq API Key not found. Please configure secrets/env variables."
        
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ LLM error: {str(e)}"

# ==========================================
# 🧠 EXPORTED FUNCTIONS (Used by app.py)
# ==========================================

def explain_with_emotion(context_text: str, question: str, emotion: str) -> str:
    """Normal Chat Explanation"""
    emotion_prompts = {
        "confused": "Use a very simple analogy from daily life. Keep it under 3 sentences.",
        "sleepy": "Be extremely punchy and exciting. Use short bullet points.",
        "happy": "Go a bit deeper. You can use technical terms but explain them.",
        "neutral": "Be clear and concise."
    }
    style = emotion_prompts.get(emotion, emotion_prompts["neutral"])
    messages = [
        {"role": "system", "content": f"You are AuraLearn, a helpful AI tutor. {style} Use the provided notes context to answer."},
        {"role": "user", "content": f"Context: {context_text}\n\nQuestion: {question}"},
    ]
    return _chat(messages, temperature=0.5)

def simplify_concept(context_text: str):
    """Confused Mode: Summarize notes simply"""
    prompt = f"The student is CONFUSED. Explain the main idea as if talking to a 10-year-old. Use ONE clear analogy. Keep it under 60 words.\nNOTES: {context_text[:2500]}"
    messages = [{"role": "user", "content": prompt}]
    return _chat(messages, temperature=0.6)

def simplify_previous_answer(previous_answer: str, question: str):
    """Confused Mode: Simplify last answer"""
    prompt = f"The student is CONFUSED by your last answer.\nQuestion: '{question}'\nYour Answer: '{previous_answer}'\nRe-explain simply (ELI5). Use a metaphor. Keep it under 50 words."
    messages = [{"role": "user", "content": prompt}]
    return _chat(messages, temperature=0.6)

def generate_quick_activity(context_text: str):
    """Sleepy Mode: Wake up call"""
    prompt = "The student is SLEEPY. Generate a 15-second PHYSICAL wake-up call (e.g. 'Stand up and stretch'). Do NOT ask a study question."
    messages = [{"role": "user", "content": prompt}]
    return _chat(messages, temperature=0.9)