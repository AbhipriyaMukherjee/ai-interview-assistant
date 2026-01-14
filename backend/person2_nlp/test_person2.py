from question_generation import generate_questions
from answer_evaluation import evaluate_answer

print("=== PERSON 2 MODULE TEST ===")

# Test 1: Generate Questions
print("\n1. TESTING QUESTION GENERATION")
profile = {
    "skills": ["Python", "Django", "REST APIs", "PostgreSQL"],
    "summary": "2 years backend developer experience building web apps"
}

questions = generate_questions(profile, "backend-developer", n=2)
print(f"Generated {len(questions)} questions:")
for i, q in enumerate(questions, 1):
    print(f"  Q{i}: {q.get('question', 'N/A')} ({q.get('type')}, {q.get('difficulty')})")

# Test 2: Evaluate Answer
print("\n2. TESTING ANSWER EVALUATION")
if questions:
    sample_question = questions[0]["question"]
    sample_answer = """Django is a full-stack web framework while Flask is a micro-framework. 
Django has ORM, admin panel, and batteries included. Flask is lightweight, you add what you need. 
I used Django for my e-commerce project with PostgreSQL database."""

    result = evaluate_answer(sample_question, sample_answer)
    print("Evaluation result:")
    print(f"  Scores: {result.get('scores', {})}")
    print(f"  Feedback: {result.get('feedback', 'N/A')}")
    print(f"  Keywords: {result.get('extracted_keywords', [])}")
else:
    print("No questions to evaluate")

print("\n=== TEST COMPLETE ===")
