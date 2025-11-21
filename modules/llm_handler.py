# modules/llm_handler.py
import os
from groq import Groq
from dotenv import load_dotenv
import streamlit as st

# Load .env file
load_dotenv()

# Inside modules/llm_handler.py

# Try getting key from Streamlit Secrets first, then Environment variable
if "GROQ_API_KEY" in st.secrets:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
else:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq client
# If you are running locally and .env fails, you can paste your key string directly below:
# client = Groq(api_key="gsk_...")
client = Groq(api_key=GROQ_API_KEY)

# Using a fast model
DEFAULT_MODEL = "llama-3.3-70b-versatile"

def _chat(messages, temperature=0.3, max_tokens=1024):
    """
    Internal helper to call Groq API with a safety timeout.
    """
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=30.0  # <--- FIX: Wait up to 30 seconds before erroring
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ LLM error: {str(e)}"

# ==========================================
# 🧠 AI TUTOR FUNCTIONS
# ==========================================

def explain_with_emotion(context_text: str, question: str, emotion: str) -> str:
    """
    Explains a concept based on the user's mood.
    """
    emotion_prompts = {
        "confused": "Explain this step-by-step using simple analogies. Avoid jargon.",
        "sleepy": "Keep the answer extremely short, punchy, and exciting. Use max 3 bullet points.",
        "happy": "Give a detailed, enthusiastic explanation. Challenge the student slightly.",
        "neutral": "Provide a clear, concise, academic explanation."
    }
    
    style = emotion_prompts.get(emotion, emotion_prompts["neutral"])

    messages = [
        {
            "role": "system",
            "content": (
                f"You are AuraLearn, an empathetic AI tutor. {style} "
                "Use the provided notes context to answer."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Context from Notes: {context_text}\n\n"
                f"Student Question: {question}"
            ),
        },
    ]
    return _chat(messages, temperature=0.5)

def simplify_concept(context_text: str):
    """
    Called when user clicks 'Confused'. 
    Summarizes the notes simply without a specific question.
    """
    prompt = f"""
    The student is CONFUSED and stuck.
    Stop teaching normally. Instead:
    1. Summarize the core concept of these notes in 3 very simple sentences.
    2. Use a real-world analogy (like cars, cooking, or sports).
    3. Be encouraging.
    
    NOTES CONTEXT:
    {context_text[:2500]}
    """
    messages = [{"role": "user", "content": prompt}]
    return _chat(messages, temperature=0.6)

def simplify_previous_answer(previous_answer: str, question: str):
    """
    Called when user is CONFUSED about a specific answer given by the AI.
    """
    prompt = f"""
    The student didn't understand your last explanation.
    
    User Question: "{question}"
    Your Previous Answer: "{previous_answer}"
    
    Task:
    
    1. Re-explain the answer in a totally different, simpler way (EL15).
    2. Use an analogy.
    """
    messages = [{"role": "user", "content": prompt}]
    return _chat(messages, temperature=0.6)

def generate_quick_activity(context_text: str):
    """
    Called when user clicks 'Sleepy'.
    Generates a PHYSICAL wake-up call (ignoring context to focus on energy).
    """
    prompt = f"""
    The student is SLEEPY and bored.
    Do NOT generate a quiz. 
    Generate a 1-minute PHYSICAL or BREATHING challenge to wake them up.
    
    Examples:
    - "Stand up and do 5 jumping jacks!"
    - "Take a deep breath in for 4 seconds, hold for 4, out for 4."
    - "Find something RED in your room."
    
    Keep it under 30 words. Be high energy!
    """
    messages = [{"role": "user", "content": prompt}]
    return _chat(messages, temperature=0.9)