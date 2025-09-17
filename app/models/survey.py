from datetime import datetime
from .. import db  # import the same db instance from app/__init__.py

class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    word_count = db.Column(db.Integer, default=0)  # Total words in survey
    published = db.Column(db.Boolean, default=False)  # Whether the survey is published

    questions = db.relationship("Question", backref="survey", lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    qtype = db.Column(db.String(50), nullable=False)  # short, paragraph, multiple_choice, checkbox, dropdown
    survey_id = db.Column(db.Integer, db.ForeignKey("survey.id"))
    word_count = db.Column(db.Integer, default=0)  # Word count of the question
    
    options = db.relationship("QuestionOption", backref="question", lazy=True)

class QuestionOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"))