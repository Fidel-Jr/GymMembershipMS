from app.models import db, User
from werkzeug.security import generate_password_hash

def seed_admin():
    """Seed the database with a default admin account if not exists."""
    admin_email = "admin@gym.com"
    admin_user = User.query.filter_by(email=admin_email).first()

    if not admin_user:
        admin = User(
            full_name="Admin User",
            username="admin",
            email=admin_email,
            contact_number="09123456789",
            address="System Office",
            role="admin",
            password_hash=generate_password_hash("admin123")  # Default password
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Default admin account created: admin@gym.com / admin123")
    else:
        print("ℹ️ Admin account already exists.")
