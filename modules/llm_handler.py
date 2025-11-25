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
    """
    Confused Mode: Summarize notes simply.
    ENHANCEMENT: Added persona, strict formatting constraints, and a "core truth" focus.
    """
    prompt = f"""
    You are AuraLearn, an expert tutor who specializes in explaining complex topics to beginners.
    The student is CONFUSED and struggling to understand the material.
    
    YOUR TASK:
    1. Ignore all jargon and technical fluff.
    2. Identify the ONE "core truth" or main idea from the notes below.
    3. Explain that single idea using a relatable real-world analogy (e.g., cooking, driving, sports, or nature).
    4. Speak directly to the student with empathy.
    
    CONSTRAINTS:
    - Maximum 3 sentences.
    - Maximum 60 words.
    - NO headers (like "Analogy:" or "Summary:"). Just the explanation.
    - Do NOT mention "the text says" or "the notes". Just teach the concept.
    
    NOTES CONTEXT:
    {context_text[:3000]}
    """
    messages = [{"role": "user", "content": prompt}]
    # Lower temp for focus, but high enough for good analogies
    return _chat(messages, temperature=0.5)

def simplify_previous_answer(previous_answer: str, question: str):
    """
    Confused Mode: Simplify last answer.
    ENHANCEMENT: Forces the LLM to analyze *why* the previous answer failed (too complex) and fix it.
    """
    prompt = f"""
    You are AuraLearn. The student is CONFUSED by your previous explanation because it was likely too technical or dry.
    
    User's Question: "{question}"
    Your Previous (Confusing) Answer: "{previous_answer}"
    
    YOUR TASK:
    1. Apologize briefly for the complexity (e.g., "That was a bit heavy, let me try again.").
    2. Re-explain the specific answer using the "ELI5" (Explain Like I'm 5) technique.
    3. Use a concrete metaphor to make it click.
    
    CONSTRAINTS:
    - Maximum 50 words.
    - Keep it conversational and warm.
    - No bullet points.
    """
    messages = [{"role": "user", "content": prompt}]
    return _chat(messages, temperature=0.6)

def generate_quick_activity(context_text: str):
    """
    Sleepy Mode: Wake up call.
    ENHANCEMENT: Forces variety (somatic, visual, breathing) and high energy to combat boredom.
    """
    prompt = f"""
    The student is SLEEPY and their attention is drifting. They need a "Pattern Break" to reset their brain.
    
    YOUR TASK:
    Generate ONE random, high-energy, 15-second physical or sensory challenge.
    
    Choose ONE of these types:
    1. Somatic: "Stand up and shake your hands out!"
    2. Visual: "Find 3 blue objects in your room right now."
    3. Breathing: "Inhale for 4 seconds... hold... exhale for 4."
    4. silly: "Try to touch your nose with your tongue."
    
    CONSTRAINTS:
    - Do NOT ask a study question.
    - Do NOT reference the notes context (unless to say "Let's take a break from [Topic]").
    - Be imperative and energetic (Use exclamation marks!).
    - Max 30 words.
    
    Context (Just for topic reference): "{context_text[:100]}..."
    """
    messages = [{"role": "user", "content": prompt}]
    return _chat(messages, temperature=0.9)