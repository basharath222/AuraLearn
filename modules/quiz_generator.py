from modules.llm_handler import _chat
import json
import re

def generate_quiz(context_text: str, num_questions=5, difficulty="Medium"):
    """
    Generates specific number of MCQs at a specific difficulty.
    """
    prompt = f"""
    Create exactly {num_questions} multiple-choice questions based on these notes.
    Difficulty Level: {difficulty}.
    
    Return ONLY valid JSON array. 
    IMPORTANT: The 'answer' field must be the INTEGER INDEX (0, 1, 2, or 3) of the correct option.
    
    Example format:
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
    response = _chat(messages, temperature=0.3, max_tokens=4096)
    
    # Clean up markdown if present
    clean_response = re.sub(r'```json|```', '', response).strip()
    
    try:
        quiz_data = json.loads(clean_response)
        return quiz_data
    except json.JSONDecodeError:
        print("JSON Error. Raw response:", response[:100])
        return []