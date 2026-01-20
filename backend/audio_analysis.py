import whisper
import librosa
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load model once at startup
model = whisper.load_model("base")

# Model answers for better scoring realism
MODEL_ANSWERS = {
    "Explain supervised vs unsupervised learning.": "Supervised learning uses labeled data to train algorithms, while unsupervised learning finds hidden patterns in unlabeled data.",
    "What is overfitting?": "Overfitting occurs when a statistical model fits exactly against its training data, capturing noise instead of the underlying pattern.",
    "Explain REST APIs.": "REST APIs are architectural styles for providing interoperability between computer systems on the internet using HTTP methods."
}

def relevance_score(answer, question):
    if not answer.strip():
        return 0.0
    
    # We compare the user answer to the MODEL answer, not just the question
    reference = MODEL_ANSWERS.get(question, question) 
    
    vec = TfidfVectorizer(stop_words="english")
    tfidf = vec.fit_transform([reference, answer])
    return round(cosine_similarity(tfidf[0], tfidf[1])[0][0] * 100, 1)

def analyze_speech(audio_path, question_text):
    # Load audio - force 16k for Whisper consistency
    audio, sr = librosa.load(audio_path, sr=16000)
    duration = librosa.get_duration(y=audio, sr=sr)

    # Transcribe
    result = model.transcribe(audio_path)
    text = result["text"]

    # Metrics
    words = len(text.split())
    wpm = (words / duration) * 60 if duration > 0 else 0

    # Improved Pause Detection
    pauses = librosa.effects.split(audio, top_db=30)
    voiced_duration = sum(e - s for s, e in pauses) / sr
    pause_ratio = 1 - (voiced_duration / duration) if duration > 0 else 0

    relevance = relevance_score(text, question_text)
    
    # Final Score Logic (Weighted)
    # 60% Relevance, 20% Fluency (WPM), 20% Technical (Pause Ratio)
    # Target WPM for interviews is ~120-150
    wpm_score = 100 - abs(130 - wpm) if wpm > 0 else 0
    fluency_score = max(0, min(100, wpm_score))
    
    final_score = (relevance * 0.6) + (fluency_score * 0.2) + ((1 - pause_ratio) * 20)
    
    return {
        "transcript": text,
        "wpm": round(wpm, 1),
        "pause_ratio": round(pause_ratio, 2),
        "relevance": relevance,
        "score": round(max(0, min(final_score, 100)), 1)
    }
