from flask import Blueprint, render_template, redirect, url_for, flash, request , session, jsonify, current_app
from app.models import User
from flask_login import login_required
from app.utils.decorators import role_required
from app.forms import MembershipPlanForm, AssignMembershipForm, EditMembershipForm
from app.models import db, MembershipPlan, Membership, MembershipRenewal
from flask_login import current_user
from dateutil.relativedelta import relativedelta
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from sqlalchemy.orm import aliased

admin_bp = Blueprint('admin', __name__, template_folder='templates')


# Helper: Expire memberships past end_date
def expire_past_memberships():
    today = datetime.today().date()
    expired_memberships = Membership.query.filter(
        Membership.end_date < today,
        Membership.status != 'Expired'
    ).all()
    for m in expired_memberships:
        m.status = 'Expired'
    if expired_memberships:
        db.session.commit()

@admin_bp.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    expire_past_memberships()
    today = datetime.today().date()
    upcoming = today + timedelta(days=3)

    # 🔸 Query memberships expiring within the next 3 days
    expiring_members = (
        db.session.query(Membership)
        .join(User, Membership.member_id == User.id)
        .join(MembershipPlan, Membership.plan_id == MembershipPlan.id)
        .filter(Membership.end_date.between(today, upcoming), Membership.status != 'Expired')
        .order_by(Membership.end_date.asc())
        .all()
    )

    # 🔸 Get 5 most recent memberships
    recent_memberships = (
        db.session.query(Membership, User, MembershipPlan)
        .join(User, Membership.member_id == User.id)
        .join(MembershipPlan, Membership.plan_id == MembershipPlan.id)
        .filter(Membership.status == 'active' and User.role == 'member') # ✅ Only active memberships
        .order_by(Membership.start_date.desc())
        .limit(5)
        .all()
    )

    # 🔸 Get latest 5 expired memberships
    expired_members = (
        db.session.query(Membership, User, MembershipPlan)
        .join(User, Membership.member_id == User.id)
        .join(MembershipPlan, Membership.plan_id == MembershipPlan.id)
        .filter(Membership.status == 'Expired')
        .order_by(Membership.end_date.desc())
        .limit(5)
        .all()
    )

    # 🔸 Get counts and total payments
    active_count = db.session.query(Membership).filter(Membership.status == 'active').count()
    expired_count = db.session.query(Membership).filter(Membership.status == 'Expired').count()
    total_payment = db.session.query(db.func.sum(MembershipPlan.price)).join(Membership, Membership.plan_id == MembershipPlan.id).scalar() or 0

    return render_template(
        'admin/dashboard.html',
        recent_memberships=recent_memberships,
        expiring_members=expiring_members,
        expired_members=expired_members,
        active_count=active_count,
        expired_count=expired_count,
        total_payment=total_payment,
        current_date=today
    )



# MANAGEMENT OF MEMBERSHIPS AND PLANS

@admin_bp.route('/admin/membership', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def membership():
    form = AssignMembershipForm()
    # Load plans for display
    plans = MembershipPlan.query.order_by(MembershipPlan.price.asc()).all()
    # ✅ Dynamically allow the selected member_id to be valid
    if request.method == 'POST':
        member_id = request.form.get('member_id', type=int)
        if member_id:
            member = User.query.get(member_id)
            if member and member.role == 'member':
                form.member_id.choices = [(member.id, member.full_name)]
    if form.validate_on_submit():
        plan = MembershipPlan.query.get(form.plan_id.data)
        if not plan:
            flash('Selected membership plan not found.', 'danger')
            return redirect(url_for('admin.membership'))
        start_date = form.start_date.data

        end_date = start_date + relativedelta(months=plan.duration_months)

        membership = Membership(
            member_id=form.member_id.data,
            plan_id=form.plan_id.data,
            start_date=form.start_date.data,
            end_date = end_date,
            paymentMethod=form.payment_method.data,
            status='active'
        )
        db.session.add(membership)
        db.session.commit()
        flash('Membership assigned successfully!', 'success')
        return redirect(url_for('admin.manage_memberships'))

    
    return render_template('admin/membership.html', form=form, plans=plans)



@admin_bp.route('/admin/manage/memberships')
@login_required
@role_required('admin')
def manage_memberships():
    expire_past_memberships()
    memberships = (
        db.session.query(Membership, User, MembershipPlan)
        .join(User, Membership.member_id == User.id)
        .join(MembershipPlan, Membership.plan_id == MembershipPlan.id)
        .order_by(Membership.start_date.desc())
        .all()
    )
    return render_template('admin/manage/manage-membership.html', memberships=memberships)

@admin_bp.route('/admin/api/membership/<int:membership_id>')
@login_required
@role_required('admin')
def api_get_membership(membership_id):
    membership = Membership.query.get_or_404(membership_id)
    user = User.query.get(membership.member_id)
    plan = MembershipPlan.query.get(membership.plan_id)
    
    if not user or not plan:
        return jsonify({'error': 'Membership data not found'}), 404
    
    return jsonify({
        'id': membership.id,
        'member': user.full_name,
        'plan': plan.name,
        'duration': f"{plan.duration_months} Month{'s' if plan.duration_months > 1 else ''}",
        'start_date': membership.start_date.strftime('%Y-%m-%d'),
        'end_date': membership.end_date.strftime('%Y-%m-%d'),
        'status': membership.status,
        'payment_method': membership.paymentMethod
    })


@admin_bp.route('/admin/api/users')
def api_users():
    """Return a small JSON list of users for Select2 AJAX search.

    Query param: q (search term)
    Returns JSON with shape: { results: [ {id, text, email, phone}, ... ] }
    This endpoint intentionally returns JSON error codes instead of redirects so AJAX callers
    can handle auth/permission issues gracefully.
    """
    # If not authenticated or not admin, return 401/403 JSON instead of redirecting
    if not current_user.is_authenticated:
        return jsonify({'results': [], 'error': 'authentication_required'}), 401
    if getattr(current_user, 'role', None) != 'admin':
        return jsonify({'results': [], 'error': 'insufficient_permission'}), 403

    q = request.args.get('q', '').strip()
    query = User.query
    if q:
        like = f"%{q}%"
        query = query.filter((User.full_name.ilike(like)) | (User.email.ilike(like)) | (User.username.ilike(like)))

    users = (
    query.filter_by(role='member')
    .order_by(User.full_name.asc())
    .limit(20)
    .all()
)
    results = []
    for u in users:
        results.append({
            'id': u.id,
            'text': f"{u.full_name} - #{u.id:03d}",
            'email': u.email,
            'phone': u.contact_number or ''
        })

    return jsonify({'results': results})

# PLAN MANAGEMENT

@admin_bp.route('/admin/manage/plans', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_plans():
    form = MembershipPlanForm()
    plans = MembershipPlan.query.order_by(MembershipPlan.id.asc()).all()
    if form.validate_on_submit():
        # Check if plan name already exists
        existing_plan = MembershipPlan.query.filter_by(name=form.name.data).first()
        if existing_plan:
            flash('A plan with this name already exists.', 'danger')
            return render_template('admin/manage/manage-plan.html', form=form, plans=plans)

        # Create and save new plan
        new_plan = MembershipPlan(
            name=form.name.data,
            features=form.features.data,
            price=form.price.data,
            duration_months=form.duration_months.data,  # e.g. duration in months
            status=form.status.data if form.status.data else 'available'
        )
        db.session.add(new_plan)
        db.session.commit()

        flash('New plan created successfully!', 'success')
        return redirect(url_for('admin.manage_plans'))  # adjust this to your view route

    return render_template('admin/manage/manage-plan.html', form=form, plans=plans)


@admin_bp.route('/admin/manage/plans/edit/<int:plan_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_plan(plan_id):
    plan = MembershipPlan.query.get_or_404(plan_id)
    form = MembershipPlanForm(obj=plan)  # Pre-fill form with existing data

    if form.validate_on_submit():
        plan.name = form.name.data
        plan.features = form.features.data
        plan.price = form.price.data
        plan.duration_months = form.duration_months.data
        plan.status = form.status.data
        
        db.session.commit()
        flash('Membership plan updated successfully!', 'success')
        return redirect(url_for('admin.manage_plans'))

    return render_template('admin/manage/edit-plan.html', form=form, plan=plan)

    
@admin_bp.route('/admin/manage/plans/delete/<int:plan_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_plan(plan_id):
    plan = MembershipPlan.query.get_or_404(plan_id)

    try:
        db.session.delete(plan)
        db.session.commit()
        flash('Membership plan deleted successfully!', 'success')
    except IntegrityError:
        db.session.rollback()
        flash("❌ Cannot delete this plan because it is still assigned to one or more memberships.", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"An unexpected error occurred: {str(e)}", "danger")

    return redirect(url_for('admin.manage_plans'))





# MEMBERSHIP MANAGEMENT 

@admin_bp.route('/admin/manage/memberships/view/<int:membership_id>', methods=['GET'])
@login_required
@role_required('admin')
def view_membership(membership_id):
    expire_past_memberships()
    membership = Membership.query.get_or_404(membership_id)
    user = User.query.get(membership.member_id)
    plan = MembershipPlan.query.get(membership.plan_id)
    return render_template('admin/manage/view-membership.html', membership=membership, user=user, plan=plan)

@admin_bp.route('/admin/manage/memberships/edit/<int:membership_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_membership(membership_id):
    expire_past_memberships()
    membership = Membership.query.get_or_404(membership_id)
    user = User.query.get(membership.member_id)
    plan = MembershipPlan.query.get(membership.plan_id)
    form = EditMembershipForm(obj=membership)

    if form.validate_on_submit():
        membership.plan_id = form.plan_id.data
        membership.start_date = form.start_date.data
        membership.end_date = form.end_date.data
        membership.status = form.status.data
        membership.paymentMethod = form.paymentMethod.data
        db.session.commit()
        flash('Membership updated successfully!', 'success')
        return redirect(url_for('admin.manage_memberships'))

    return render_template('admin/manage/edit-membership.html', form=form, membership=membership, user=user, plan=plan)

@admin_bp.route('/admin/manage/memberships/delete/<int:membership_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_membership(membership_id):
    membership = Membership.query.get_or_404(membership_id)
    db.session.delete(membership)
    db.session.commit()
    flash('Membership deleted successfully!', 'warning')
    return redirect(url_for('admin.manage_memberships'))



# MEMBER MANAGEMENT

# List Members
@admin_bp.route('/admin/manage/members')
@login_required
@role_required('admin')
def manage_members():
    members = User.query.order_by(User.id.asc()).all()
    return render_template('admin/manage/manage-member.html', members=members)

# View Member
@admin_bp.route('/admin/manage/members/view/<int:member_id>')
@login_required
@role_required('admin')
def view_member(member_id):
    member = User.query.get_or_404(member_id)
    return render_template('admin/manage/view-member.html', member=member)

# Edit Member
from app.forms import MemberEditForm
@admin_bp.route('/admin/manage/members/edit/<int:member_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_member(member_id):
    member = User.query.get_or_404(member_id)
    form = MemberEditForm(obj=member)
    if form.validate_on_submit():
        member.full_name = form.full_name.data
        member.email = form.email.data
        member.contact_number = form.contact_number.data
        member.is_active = True if form.is_active.data == '1' else False
        member.role = form.role.data
        # Handle profile image upload (admin)
        if form.image.data and hasattr(form.image.data, "filename"):
            file = form.image.data
            filename = secure_filename(file.filename)
            # create directory if not exists
            upload_folder = os.path.join(current_app.root_path, 'static', 'img', 'users')
            os.makedirs(upload_folder, exist_ok=True)
            # prefix with member id and timestamp to avoid clashes
            prefixed = f"u{member.id}_{int(datetime.utcnow().timestamp())}_{filename}"
            filepath = os.path.join(upload_folder, prefixed)
            file.save(filepath)
            member.image = prefixed
        db.session.commit()
        flash('Member updated successfully!', 'success')
        return redirect(url_for('admin.manage_members'))
    return render_template('admin/manage/edit-member.html', form=form, member=member)

# Delete Member
@admin_bp.route('/admin/manage/members/delete/<int:member_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_member(member_id):
    member = User.query.get_or_404(member_id)
    db.session.delete(member)
    db.session.commit()
    flash('Member deleted successfully!', 'warning')
    return redirect(url_for('admin.manage_members'))





# MEMBERSHIP RENEWAL MANAGEMENT

@admin_bp.route('/admin/manage/memberships/renew/<int:membership_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def renew_membership(membership_id):
    
    membership = Membership.query.get_or_404(membership_id)
    member = User.query.get(membership.member_id)
    plans = MembershipPlan.query.all()
    today = datetime.today().date() 
    
     # Prevent renewing if membership is still active
    if membership.end_date and membership.end_date.date() > today:
        flash(f'Membership for {member.full_name} is already active until {membership.end_date.strftime('%Y-%m-%d') }.', 'warning')
        return redirect(url_for('admin.manage_memberships'))

    if request.method == 'POST':
        plan_id = request.form.get('plan_id', membership.plan_id)
        plan = MembershipPlan.query.get(plan_id)

        # ✅ Set start_date to today if membership has expired, otherwise use end_date
        if membership.end_date and membership.end_date.date() > today:  
            start_date = membership.end_date
        else:
            start_date = today

        end_date = start_date + relativedelta(months=plan.duration_months)

        try:
            # 1️⃣ Update existing Membership
            last_start_date = membership.start_date
            last_end_date = membership.end_date
            membership.plan_id = plan.id
            membership.start_date = start_date
            membership.end_date = end_date
            membership.status = 'active'
            db.session.add(membership)

            # 2️⃣ Add record to MembershipRenewal
            renewal = MembershipRenewal(
                membership_id=membership.id,
                processed_by=current_user.id,
                last_start_date=last_start_date,
                last_end_date=last_end_date,
                renewal_date=today,
            )
            db.session.add(renewal)

            db.session.commit()
            flash(f'Membership for {member.full_name} renewed successfully.', 'success')
            return redirect(url_for('admin.manage_memberships'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error renewing membership: {str(e)}', 'danger')
            return redirect(url_for('admin.admin_dashboard'))

    return render_template('admin/dashboard.html', member=member, membership=membership, plans=plans, today=today)



# VIEW EXPIRING & EXPIRED MEMBERSHIPS 

@admin_bp.route('/admin/manage/expiring-expired')
@login_required
@role_required('admin')
def manage_renewal():
    today = datetime.today().date()
    upcoming = today + timedelta(days=3)
    # Get memberships expiring in next 3 days
    expiring = (
        db.session.query(Membership, User, MembershipPlan)
        .join(User, Membership.member_id == User.id)
        .join(MembershipPlan, Membership.plan_id == MembershipPlan.id)
        .filter(Membership.end_date.between(today, upcoming), Membership.status != 'Expired')
        .order_by(Membership.end_date.asc())
        .all()
    )
    # Get all expired memberships
    expired = (
        db.session.query(Membership, User, MembershipPlan)
        .join(User, Membership.member_id == User.id)
        .join(MembershipPlan, Membership.plan_id == MembershipPlan.id)
        .filter(Membership.status == 'Expired')
        .order_by(Membership.end_date.desc())
        .all()
    )
    # Combine both lists for the table (expiring first, then expired)
    memberships = expiring + expired
    return render_template('admin/manage/manage-renewal.html', memberships=memberships, current_date=today)