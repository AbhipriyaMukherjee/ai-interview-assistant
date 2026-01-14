import ollama
import json
import re


def build_context(profile, domain):
    skills = ", ".join(profile.get("skills", []))
    exp = profile.get("summary", "No experience")
    return f"{domain} role. Skills: {skills}. Experience: {exp}"


def generate_questions(profile: dict, domain: str, n: int = 5) -> list[dict]:
    context = build_context(profile, domain)
    prompt = f"""Generate EXACTLY {n} interview questions.

Role: {domain}
Candidate: {context}

Respond with ONLY valid JSON array:
[{{"question": "Explain Python?", "type": "technical", "difficulty": "easy"}}]

No other text."""

    try:
        response = ollama.chat(model='llama3.2:3b', messages=[
            {'role': 'user', 'content': prompt}
        ])
        raw = response['message']['content']
        print("Raw:", raw)

        # Extract JSON
        json_match = re.search(r'\[.*\]', raw, re.DOTALL)
        if json_match:
            questions = json.loads(json_match.group())
            return questions
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []


if __name__ == "__main__":
    profile = {"skills": ["Python"], "summary": "Junior dev"}
    print(generate_questions(profile, "backend", 2))

