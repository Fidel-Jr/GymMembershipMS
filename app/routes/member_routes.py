from flask import Blueprint, render_template, redirect, url_for, flash, request , session
from app.models import User
from flask_login import login_required
from app.utils.decorators import role_required

member_bp = Blueprint('member', __name__, template_folder='templates')

@member_bp.route('/member/dashboard')
@login_required
@role_required('member')
def member_dashboard():
    from flask_login import current_user
    from app.models import Membership, MembershipPlan, MembershipRenewal, db

    # Get all memberships for current user
    memberships = Membership.query.filter_by(member_id=current_user.id).order_by(Membership.start_date.desc()).all()
    membership_history = []
    total_payment = 0
    expired_count = 0
    renewed_count = 0
    current_membership = None
    current_plan = None

    renewal_history = []
    for m in memberships:
        plan = MembershipPlan.query.get(m.plan_id)
        membership_history.append((m, plan))
        total_payment += plan.price if plan else 0
        if m.status == 'expired':
            expired_count += 1
        renewals = MembershipRenewal.query.filter_by(membership_id=m.id).order_by(MembershipRenewal.renewal_date.desc()).all()
        if renewals:
            renewed_count += 1
            for r in renewals:
                renewal_history.append({
                    'plan': plan,
                    'renewal': r,
                    'membership': m
                })
        if m.status == 'active' and not current_membership:
            current_membership = m
            current_plan = plan

    return render_template(
        'member/dashboard.html',
        renewed_count=renewed_count,
        total_payment=total_payment,
        expired_count=expired_count,
        current_membership=current_membership,
        current_plan=current_plan,
        membership_history=membership_history,
        renewal_history=renewal_history
    )