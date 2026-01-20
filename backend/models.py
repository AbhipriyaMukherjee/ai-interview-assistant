from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """Stores user authentication data."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Hashed
    results = db.relationship('InterviewResult', backref='user', lazy=True)

class InterviewResult(db.Model):
    """Stores every interview attempt for account history."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(100))
    score = db.Column(db.Integer)
    video_score = db.Column(db.Float)
    transcript = db.Column(db.Text)
    feedback = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)