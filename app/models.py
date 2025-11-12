from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()   

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    contact_number = db.Column(db.String(20))
    address = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')  # 'admin' or 'member'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    image = db.Column(db.String(255))  # stores filename of profile image

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class MembershipPlan(db.Model):
    __tablename__ = 'membership_plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    features = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    duration_months = db.Column(db.Integer, nullable=False)  # Duration in months
    status = db.Column(db.String(20), default='available')  # 'available' or 'unavailable'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Membership(db.Model):
    __tablename__ = 'memberships'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('membership_plans.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    paymentMethod = db.Column(db.String(100))  # e.g., 'credit_card', 'cash', etc.   
    status = db.Column(db.String(20), default='active')  # 'active', 'expired', 'cancelled'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('memberships', lazy=True))
    plan = db.relationship('MembershipPlan', backref=db.backref('memberships', lazy=True))
    
class MembershipRenewal(db.Model):
    __tablename__ = 'membership_renewals'
    
    id = db.Column(db.Integer, primary_key=True)
    membership_id = db.Column(db.Integer, db.ForeignKey('memberships.id'), nullable=False)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    last_start_date = db.Column(db.DateTime, nullable=True)
    last_end_date = db.Column(db.DateTime, nullable=True)
    renewal_date = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    
    # Relationships
    membership = db.relationship('Membership', backref='renewals', lazy=True)
    processed_user = db.relationship('User', backref='processed_renewals', lazy=True)
