from flask import Blueprint, render_template, redirect, url_for, flash, request , session
from app.models import User, MembershipPlan, Membership, MembershipRenewal, db
from flask_login import login_required
from app.forms import LoginForm

main_bp = Blueprint('main', __name__, template_folder='templates')

@main_bp.route('/')
def home():
    form = LoginForm()
    return render_template('login.html', form=form)
    
@main_bp.route('/about')
@login_required
def about():
    users = User.query.all()
    renewals = (
        db.session.query(
            MembershipRenewal,
            Membership,
            User,
            MembershipPlan
        )
        .join(Membership, MembershipRenewal.membership_id == Membership.id)
        .join(User, Membership.member_id == User.id)
        .join(MembershipPlan, Membership.plan_id == MembershipPlan.id)
        .order_by(MembershipRenewal.renewal_date.desc())
        .all()
    )
    return render_template('about.html', users=users, renewals=renewals)