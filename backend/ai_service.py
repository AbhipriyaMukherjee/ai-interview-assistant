import requests
import json

class AIService:
    def __init__(self):
        self.url = "http://localhost:11434/api/generate"

    def generate_questions(self, role, skills, n=2):
        """Generates exactly 2 technical questions locked to the specific role."""
        prompt = f"""
        System: You are an expert interviewer for the position of {role}.
        Candidate Skills: {skills}.
        Task: Generate exactly {n} technical interview questions.
        
        CRITICAL RULE: The questions must be 100% relevant to {role}. 
        Do NOT drift into unrelated fields like Computer Science unless the role specifically requires it.
        For example, if the role is Finance Analyst, questions must focus on financial modeling, valuation, or accounting.
        
        Output: Strictly return ONLY a JSON array of objects: [{{ "question": "text" }}]
        """
        try:
            r = requests.post(self.url, json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
                "format": "json"
            })
            response_text = r.json().get('response', '[]')
            return json.loads(response_text)
        except Exception:
            # Context-aware fallback questions
            return [
                {"question": f"Explain a core technical concept essential for a {role}."},
                {"question": f"Describe a complex problem-solving scenario in {role}."}
            ]

    def evaluate_answer(self, question, answer):
        """Strict technical audit penalizing vague or generic answers."""
        prompt = f"""
        System: Strict Technical Auditor.
        Question: {question}
        Answer: {answer}
        
        Task: Rate technical depth. If the answer lacks specific terminology for this field, score below 30.
        Output: Strictly return JSON: {{ "score": 0-100, "feedback": "text" }}
        """
        try:
            r = requests.post(self.url, json={"model": "llama3", "prompt": prompt, "stream": False, "format": "json"})
            return json.loads(r.json()['response'])
        except Exception:
            return {"score": 0, "feedback": "Evaluation failed."}

ai_service = AIService()