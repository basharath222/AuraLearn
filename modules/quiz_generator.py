from modules.llm_handler import _chat
import json
import re

def generate_quiz(context_text: str, num_questions=5):
    """
    Generates 'num_questions' MCQs. 
    """
    prompt = f"""
    Create exactly {num_questions} multiple-choice questions based on these notes.
    Return ONLY valid JSON array. 
    IMPORTANT: The 'answer' field must be the INTEGER INDEX (0, 1, 2, or 3).
    
    Example:
    [
        {{
            "question": "Question text?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": 0
        }}
    ]
    
    NOTES:
    {context_text[:3500]}
    """
    
    messages = [{"role": "user", "content": prompt}]
    response = _chat(messages, temperature=0.3)
    clean_response = re.sub(r'```json|```', '', response).strip()
    
    try:
        return json.loads(clean_response)
    except:
        return []