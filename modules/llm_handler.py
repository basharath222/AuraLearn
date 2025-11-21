import os
from groq import Groq
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Read key from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    # Fallback for testing if .env fails, but try to use .env!
    print("⚠️ Warning: GROQ_API_KEY not found.")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)
DEFAULT_MODEL = "llama-3.3-70b-versatile"

def _chat(messages, temperature=0.3, max_tokens=1024):
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ LLM error: {str(e)}"

def explain_with_emotion(context_text: str, question: str, emotion: str) -> str:
    """
    Explains a concept based on the user's mood.
    """
    # 1. Define how the AI should behave for each mood
    emotion_prompts = {
        "confused": "Explain this step-by-step using simple analogies. Avoid jargon.",
        "sleepy": "Keep the answer extremely short. Use max 3 bullet points.",
        "stressed": "Be encouraging and calm. Focus only on the most important fact.",
        "happy": "Give a detailed explanation with an advanced example.",
        "neutral": "Provide a standard, clear academic explanation."
    }
    
    # Select the style (default to neutral if emotion not found)
    style_instruction = emotion_prompts.get(emotion, emotion_prompts["neutral"])

    messages = [
        {
            "role": "system",
            "content": (
                f"You are AuraLearn, a helpful AI tutor. {style_instruction} "
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