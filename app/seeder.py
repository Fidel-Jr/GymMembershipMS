from app.models import db, User
from werkzeug.security import generate_password_hash
import sqlite3
import os

def add_image_column_if_missing(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Check if 'image' column exists
    cur.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cur.fetchall()]
    if 'image' not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN image VARCHAR(200)")
        conn.commit()
    # Set all images to NULL
    cur.execute("UPDATE users SET image=NULL")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Adjust path if needed
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'gym_system.db')
    add_image_column_if_missing(db_path)

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
