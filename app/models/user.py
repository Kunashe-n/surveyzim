from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .. import db  # import the same db instance from app/__init__.py

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512))
    payment_status = db.Column(db.String(20), default='unpaid')  # student, basic, extended, enterprise
    word_limit = db.Column(db.Integer, default=0)  # Will be set based on payment package

    surveys = db.relationship("Survey", backref="owner", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)