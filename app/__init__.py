from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from .config import Config

# Only one instance of each extension
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "main.login"  # route name for login page

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)

    # Import models here AFTER db.init_app to avoid circular imports
    from .models.user import User
    from .models.survey import Survey, Question

    # Register the user_loader inside create_app
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from .routes import bp
    app.register_blueprint(bp)

    return app
