import ollama
import json
import re
from collections import Counter


def extract_keywords(text):
    """Simple keyword extraction"""
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    common = Counter(words).most_common(10)
    return [word for word, count in common]


def evaluate_answer(question: str, answer_text: str, features: dict = {}) -> dict:
    prompt = f"""Evaluate this interview answer:

Question: {question}
Answer: {answer_text}

Score 0.0-1.0:
- structure: logical flow?
- clarity: grammar, clear?
- relevance: answers question?
- keywords: technical terms?

Return ONLY JSON:
{{
  "scores": {{"structure": 0.8, "clarity": 0.9, "relevance": 0.7, "keywords": 0.8, "overall": 0.8}},
  "feedback": "Good technical depth, improve structure.",
  "keywords": ["django", "flask"]
}}"""

    try:
        response = ollama.chat(model='llama3.2:3b', messages=[
            {'role': 'user', 'content': prompt}
        ])
        raw = response['message']['content']

        # Extract JSON
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            result["extracted_keywords"] = extract_keywords(answer_text)
            return result
        return {}
    except Exception as e:
        print(f"Evaluation error: {e}")
        return {"scores": {"overall": 0}, "feedback": "Error"}


if __name__ == "__main__":
    result = evaluate_answer(
        "Explain Django vs Flask",
        "Django is full framework, Flask is micro..."
    )
    print(result)
