from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo

# -----------------------------
# User Authentication Forms
# -----------------------------
class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

# -----------------------------
# Survey Forms
# -----------------------------
class SurveyForm(FlaskForm):
    title = StringField("Survey Title", validators=[DataRequired()])
    description = TextAreaField("Description")
    submit = SubmitField("Create Survey")

class QuestionForm(FlaskForm):
    text = StringField("Question", validators=[DataRequired()])
    qtype = SelectField("Type", choices=[("short","Short Answer"),("paragraph","Paragraph")])
    submit = SubmitField("Add Question")
