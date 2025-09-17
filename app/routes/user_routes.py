from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from . import bp  # blueprint variable
from .. import db
from ..models.user import User
from ..models.survey import Survey, Question, QuestionOption
from ..forms import RegisterForm, LoginForm, SurveyForm, QuestionForm
from datetime import datetime, timedelta

# Word limits for each package
WORD_LIMITS = {
    'student': 800,
    'basic': 1500,
    'extended': 3000,
    'enterprise': 5000
}

# -----------------------------
# Home Page
# -----------------------------
@bp.route("/")
def index():
    return render_template("index.html")

# -----------------------------
# Register
# -----------------------------
@bp.route("/register", methods=["GET","POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter(
            (User.email == form.email.data) | (User.username == form.username.data)
        ).first()

        if existing_user:
            flash("User with that email or username already exists.")
            return render_template("register.html", form=form)

        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Account created successfully!")
        return redirect(url_for("main.dashboard"))

    return render_template("register.html", form=form)

# -----------------------------
# Login
# -----------------------------
@bp.route("/login", methods=["GET","POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)

                next_page = request.args.get("next")
                # Only redirect to a relative URL for safety
                if not next_page or not next_page.startswith("/"):
                    next_page = url_for("main.dashboard")
                return redirect(next_page)
            else:
                flash("Invalid email or password.", "danger")
        else:
            print("Form validation errors:", form.errors)

    return render_template("login.html", form=form)

# -----------------------------
# Logout
# -----------------------------
@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("main.index"))

# -----------------------------
# Dashboard
# -----------------------------
@bp.route("/dashboard")
@login_required
def dashboard():
    surveys = Survey.query.filter_by(user_id=current_user.id).all()
    total_responses = sum(getattr(survey, 'response_count', 0) for survey in surveys)
    return render_template("dashboard.html", surveys=surveys, total_responses=total_responses)

# -----------------------------
# Create Survey
# -----------------------------
@bp.route("/create_survey", methods=["GET","POST"])
@login_required
def create_survey():
    form = SurveyForm()

    if form.validate_on_submit():
        # Calculate word count for title and description
        title_words = len(form.title.data.split()) if form.title.data else 0
        description_words = len(form.description.data.split()) if form.description.data else 0
        total_words = title_words + description_words
        
        # Check if user has exceeded their word limit
        if total_words > current_user.word_limit and current_user.payment_status != 'unpaid':
            flash(f"Your survey exceeds your word limit of {current_user.word_limit} words. Please reduce content or upgrade your plan.")
            return render_template("survey_builder.html", form=form)
        
        # 1️⃣ Create the survey
        survey = Survey(
            title=form.title.data,
            description=form.description.data,
            user_id=current_user.id,
            word_count=total_words
        )
        db.session.add(survey)
        db.session.commit()  # commit first to get survey.id

        # 2️⃣ Handle dynamic questions from the frontend
        question_texts = request.form.getlist("question_text[]")
        question_types = request.form.getlist("question_type[]")

        for i, q_text in enumerate(question_texts):
            q_type = question_types[i]
            
            # Calculate word count for this question
            question_words = len(q_text.split()) if q_text else 0
            total_words += question_words
            
            # Check if adding this question would exceed the limit
            if total_words > current_user.word_limit and current_user.payment_status != 'unpaid':
                flash(f"Adding this question would exceed your word limit of {current_user.word_limit} words. Please reduce content or upgrade your plan.")
                db.session.delete(survey)
                db.session.commit()
                return render_template("survey_builder.html", form=form)
            
            question = Question(
                text=q_text,
                qtype=q_type,
                survey_id=survey.id,
                word_count=question_words
            )
            db.session.add(question)
            db.session.commit()  # commit to get question.id

            # Update survey word count
            survey.word_count = total_words
            db.session.commit()

            # Handle options for multiple choice, checkbox, dropdown
            if q_type in ["multiple_choice", "checkbox", "dropdown"]:
                option_names = request.form.getlist(f"question_option_{i}[]")
                for opt_text in option_names:
                    if opt_text.strip():
                        option = QuestionOption(
                            text=opt_text.strip(),
                            question_id=question.id
                        )
                        db.session.add(option)
        db.session.commit()

        flash("Survey created successfully! You can now manage your questions.")
        return redirect(url_for("main.survey_view", survey_id=survey.id))

    return render_template("survey_builder.html", form=form)

# -----------------------------
# Survey View (Add/Manage Questions)
# -----------------------------
@bp.route("/survey/<int:survey_id>", methods=["GET","POST"])
@login_required
def survey_view(survey_id):
    survey = Survey.query.get_or_404(survey_id)

    # Ensure current user owns the survey
    if survey.user_id != current_user.id:
        flash("You don't have permission to access this survey.")
        return redirect(url_for("main.dashboard"))

    form = QuestionForm()

    # Handle new questions submitted via POST
    if request.method == "POST":
        question_texts = request.form.getlist("question_text[]")
        question_types = request.form.getlist("question_type[]")

        for i, q_text in enumerate(question_texts):
            q_type = question_types[i]
            
            # Calculate word count for this question
            question_words = len(q_text.split()) if q_text else 0
            new_total_words = survey.word_count + question_words
            
            # Check if adding this question would exceed the limit
            if new_total_words > current_user.word_limit and current_user.payment_status != 'unpaid':
                flash(f"Adding this question would exceed your word limit of {current_user.word_limit} words. Please reduce content or upgrade your plan.")
                return redirect(url_for("main.survey_view", survey_id=survey.id))
            
            question = Question(text=q_text.strip(), qtype=q_type, survey_id=survey.id, word_count=question_words)
            db.session.add(question)
            db.session.commit()  # get question.id

            # Update survey word count
            survey.word_count = new_total_words
            db.session.commit()

            # Handle options
            if q_type in ["multiple_choice", "checkbox", "dropdown"]:
                option_names = request.form.getlist(f"question_option_{i}[]")
                for opt_text in option_names:
                    if opt_text.strip():
                        option = QuestionOption(text=opt_text.strip(), question_id=question.id)
                        db.session.add(option)
        db.session.commit()
        flash("Questions added successfully!")
        return redirect(url_for("main.survey_view", survey_id=survey.id))  # redirect after POST

    # 2️⃣ Get all questions for GET rendering
    questions = sorted(survey.questions, key=lambda q: q.id)  # avoid InstrumentedList error

    return render_template("survey_view.html", survey=survey, form=form, questions=questions)

# -----------------------------
# Delete Question
# -----------------------------
@bp.route("/question/<int:question_id>/delete", methods=["POST"])
@login_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    survey_id = question.survey_id
    survey = Survey.query.get(survey_id)
    
    if question.survey.user_id != current_user.id:
        flash("You don't have permission to delete this question.")
        return redirect(url_for("main.dashboard"))

    # Update survey word count before deleting the question
    survey.word_count -= question.word_count
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted successfully!")
    return redirect(url_for("main.survey_view", survey_id=survey_id))

# -----------------------------
# Delete Survey
# -----------------------------
@bp.route("/survey/<int:survey_id>/delete", methods=["POST"])
@login_required
def delete_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    if survey.user_id != current_user.id:
        flash("You don't have permission to delete this survey.")
        return redirect(url_for("main.dashboard"))

    Question.query.filter_by(survey_id=survey_id).delete()
    db.session.delete(survey)
    db.session.commit()
    flash("Survey deleted successfully!")
    return redirect(url_for("main.dashboard"))

# -----------------------------
# Publish Survey
# -----------------------------
@bp.route("/survey/<int:survey_id>/publish", methods=["POST"])
@login_required
def publish_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    
    # Check if user owns the survey
    if survey.user_id != current_user.id:
        flash("You don't have permission to publish this survey.")
        return redirect(url_for("main.dashboard"))
    
    # Check if user has paid
    if current_user.payment_status == 'unpaid':
        flash("You need to purchase a plan to publish surveys.")
        return redirect(url_for("main.payment_select"))
    
    # Check if survey exceeds word limit
    if survey.word_count > current_user.word_limit:
        flash("Survey exceeds your word limit. Please upgrade your plan or reduce content.")
        return redirect(url_for("main.survey_view", survey_id=survey.id))
    
    # Publish the survey
    survey.published = True
    survey.published_at = datetime.utcnow()
    db.session.commit()
    
    flash("Survey published successfully!")
    return redirect(url_for("main.dashboard"))

# -----------------------------
# Payment Selection
# -----------------------------
@bp.route("/payment_select")
@login_required
def payment_select():
    return render_template("payment_select.html")

# -----------------------------
# Process Payment
# -----------------------------
@bp.route("/process_payment/<package>", methods=["POST"])
@login_required
def process_payment(package):
    # Validate package type
    if package not in WORD_LIMITS:
        flash("Invalid package selected.")
        return redirect(url_for('main.payment_select'))
    
    # Update user payment status and word limit
    current_user.payment_status = package
    current_user.word_limit = WORD_LIMITS[package]
    db.session.commit()
    
    flash(f"Payment successful! Your {package} plan has been activated with a {WORD_LIMITS[package]} word limit.")
    return redirect(url_for('main.dashboard'))

# -----------------------------
# Payment page
# -----------------------------
@bp.route("/payment/<package>")
@login_required
def payment(package):
    # Define package details
    packages = {
        "student": {
            "name": "Student Plan", 
            "price": "$30", 
            "word_limit": "800 words",
            "features": ["1 survey", "Up to 200 responses", "10-day distribution", "CSV export"]
        },
        "basic": {
            "name": "Basic Plan", 
            "price": "$100", 
            "word_limit": "1,500 words",
            "features": ["1 survey", "Up to 1,000 responses", "14-day distribution", "Light demographic targeting"]
        },
        "extended": {
            "name": "Extended Plan", 
            "price": "$250", 
            "word_limit": "3,000 words",
            "features": ["1 survey", "Up to 5,000 responses", "30-day distribution", "Full demographic targeting"]
        },
        "enterprise": {
            "name": "Enterprise Plan", 
            "price": "Starting at $600", 
            "word_limit": "5,000+ words",
            "features": ["Custom surveys", "10,000+ responses", "60-day distribution", "Advanced targeting", "Full support"]
        }
    }

    plan = packages.get(package)
    if not plan:
        flash("Invalid package selected.", "danger")
        return redirect(url_for("main.index"))

    return render_template("payment.html", plan=plan, package=package)

@bp.route("/contact")
def contact():
    return render_template("contact.html")