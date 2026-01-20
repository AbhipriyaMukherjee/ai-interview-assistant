import PyPDF2
import re

def extract_skills_and_roles(pdf_path):
    """
    Parses a PDF to extract technical keywords and recommend job paths.
    """
    text = ""
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
        text = text.lower()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return [], []

    # Industrial Keyword Libraries
    skill_library = {
        "Python": ["python", "flask", "django", "pandas", "numpy"],
        "Web Development": ["html", "css", "javascript", "react", "vue", "node"],
        "Data Science": ["machine learning", "ml", "ai", "sql", "tableau", "powerbi"],
        "Cloud": ["aws", "azure", "docker", "kubernetes", "cloud"],
        "Finance": ["excel", "accounting", "auditing", "financial modeling"]
    }

    detected_skills = []
    for category, keywords in skill_library.items():
        for word in keywords:
            if re.search(rf"\b{word}\b", text):
                detected_skills.append(word.title())
    
    # Remove duplicates
    detected_skills = list(set(detected_skills))

    # Recommendation Logic based on detected expertise
    recommendations = []
    if any(s.lower() in text for s in ["python", "flask", "javascript", "react"]):
        recommendations.append("Web Developer")
    if any(s.lower() in text for s in ["sql", "machine learning", "pandas", "excel"]):
        recommendations.append("Data Analyst")
    if any(s.lower() in text for s in ["aws", "docker", "cloud"]):
        recommendations.append("DevOps Engineer")
    
    # Fallback if no specific skills found
    if not recommendations:
        recommendations = ["Software Engineer", "Business Analyst"]

    return detected_skills, recommendations