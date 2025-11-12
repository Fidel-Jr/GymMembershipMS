from .auth_routes import auth_bp
from .admin_routes import admin_bp
from .main_routes import main_bp
from .member_routes import member_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(member_bp)
    from .profile_routes import profile_bp
    app.register_blueprint(profile_bp)