import os
import sys

# Ensures backend modules are discoverable in the project structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Industrial Backend Imports
from backend.models import db, User, InterviewResult
from backend.ai_service import ai_service  
from backend.resume_parser import extract_skills_and_roles
from latex_export.generate import generate_latex, compile_pdf
from backend.audio_analysis import analyze_speech
from backend.video_analysis import analyze_video_file

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'career_ai.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "career_ai_role_lock_final_2026"

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Dashboard ---
@app.route("/")
@login_required
def index():
    """Main dashboard showing performance history."""
    past_results = InterviewResult.query.filter_by(user_id=current_user.id).order_by(InterviewResult.id.desc()).all()
    return render_template("home.html", results=past_results)

# --- Resume Analysis ---
@app.route("/resume", methods=["GET", "POST"])
@login_required
def resume_module():
    """Extracts skills and recommends roles from PDF."""
    if request.method == "POST":
        file = request.files.get('resume')
        if file and file.filename.endswith('.pdf'):
            path = os.path.join(app.config["UPLOAD_FOLDER"], "user_resume.pdf")
            file.save(path)
            skills, roles = extract_skills_and_roles(path)
            session['user_skills'] = skills
            return render_template("job_recommendations.html", roles=roles, skills=skills)
    return render_template("resume_upload.html")

# --- LaTeX Resume Generation ---
@app.route("/generate_resume", methods=["POST"])
@login_required
def generate_resume():
    """Generates a PDF resume from structured resume data."""

    data = request.get_json() or {}

    tex_path = generate_latex(data)
    pdf_path = compile_pdf(tex_path)

    return jsonify({
        "status": "success",
        "pdf_path": pdf_path
    })

# --- 2-Question Interview Loop ---
@app.route("/interview/live")
@login_required
def live_interview():
    """Generates 2 role-locked technical questions."""
    role = request.args.get("role", "General Candidate")
    skills = session.get('user_skills', [])
    
    # Request exactly 2 questions from the AI service
    questions = ai_service.generate_questions(role, skills, n=2)
    
    # Safety Check: Fallback if AI fails or drifts
    if not questions or len(questions) < 2:
        questions = [
            {"question": f"Explain a core technical principle relevant to a {role}."},
            {"question": f"Describe how you handle professional challenges in the field of {role}."}
        ]
        
    return render_template("interview_live.html", role=role, questions=questions)

@app.route("/submit_interview", methods=["POST"])
@login_required
def submit_interview():
    """Strict AI audit of each recorded answer."""
    video_file = request.files.get("video")
    video_path = os.path.join(app.config["UPLOAD_FOLDER"], "last_interview.webm")
    video_file.save(video_path)
    
    # AI Audit: Transcription and Strict Scoring
    audio_data = analyze_speech(video_path, request.form.get("question_text"))
    eval_result = ai_service.evaluate_answer(request.form.get("question_text"), audio_data['transcript'])
    video_data = analyze_video_file(video_path, app.config["UPLOAD_FOLDER"])
    
    new_result = InterviewResult(
        user_id=current_user.id,
        role=request.form.get("role"),
        score=eval_result['score'], # Harsh AI rating
        video_score=video_data['final_score_percent'],
        transcript=audio_data['transcript'],
        feedback=eval_result['feedback']
    )
    db.session.add(new_result)
    db.session.commit()
    return jsonify({"status": "success", "id": new_result.id})

# --- Audit Feedback ---
@app.route("/feedback")
@login_required
def feedback():
    """Displays the final audit results and AI feedback."""
    res_id = request.args.get('id')
    result = InterviewResult.query.get(res_id) if res_id else InterviewResult.query.filter_by(user_id=current_user.id).order_by(InterviewResult.id.desc()).first()
    return render_template("feedback.html", result=result)

# --- Auth Routes ---
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        hashed_pw = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        new_user = User(username=request.form['username'], email=request.form['email'], password=hashed_pw)
        try:
            db.session.add(new_user); db.session.commit()
            return redirect(url_for('login'))
        except:
            flash("Signup failed. User may already exist.", "danger")
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # Host '0.0.0.0' allows the tunnel to access your local port
    app.run(host='0.0.0.0', port=5000, debug=False)