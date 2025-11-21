# modules/quiz_generator.py
from modules.llm_handler import _chat
import json
import re

def generate_quiz(context_text: str):
    """
    Generates 3 MCQs. Returns JSON with 'answer_index' (0-3) to avoid text mismatch.
    """
    prompt = f"""
    Create 3 to 20 multiple-choice questions based on these notes.
    Return ONLY valid JSON array. 
    IMPORTANT: The 'answer' field must be the INTEGER INDEX (0, 1, 2, or 3) of the correct option.
    
    Example format:
    [
        {{
            "question": "What is the capital of France?",
            "options": ["Berlin", "Madrid", "Paris", "Rome"],
            "answer": 2
        }}
    ]
    
    NOTES:
    {context_text[:3000]}
    """
    
    messages = [{"role": "user", "content": prompt}]
    response = _chat(messages, temperature=0.3)
    
    # Clean up markdown if present
    clean_response = re.sub(r'```json|```', '', response).strip()
    
    try:
        quiz_data = json.loads(clean_response)
        return quiz_data
    except json.JSONDecodeError:
        print("JSON Error:", response)
        return []