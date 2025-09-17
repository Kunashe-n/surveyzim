from . import db
from datetime import datetime

class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey("survey.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    answers = db.Column(db.JSON)  # store answers in JSON format
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
