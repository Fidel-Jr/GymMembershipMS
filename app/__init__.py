from flask import Flask
from app.routes import register_blueprints
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.models import db, User

# from flask_migrate import Migrate


# db = SQLAlchemy()
# bcrypt = Bcrypt()
login_manager = LoginManager()
# login_manager.login_view = 'login'

def create_app():
    app = Flask(__name__)
    register_blueprints(app)
    app.config['SECRET_KEY'] = 'mysecretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/gym.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    # migrate = Migrate(app, db)
    # Flask-Login
    login_manager.init_app(app)

    login_manager.login_view = 'auth.login'  # redirect if not logged in
    login_manager.login_message_category = 'info'
    
    
    
    return app
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))