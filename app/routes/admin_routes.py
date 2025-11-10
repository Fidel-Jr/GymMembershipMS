from flask import Blueprint, render_template, redirect, url_for, flash, request , session
from app.models import User
from flask_login import login_required
from app.utils.decorators import role_required

admin_bp = Blueprint('admin', __name__, template_folder='templates')


@admin_bp.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    return render_template('admin/dashboard.html')

@admin_bp.route('/admin/membership')
@login_required
@role_required('admin')
def membership():
    return render_template('admin/membership.html')

@admin_bp.route('/admin/manage/members')
@login_required
@role_required('admin')
def manage_members():
    return render_template('admin/manage/manage-member.html')

@admin_bp.route('/admin/manage/memberships')
@login_required
@role_required('admin')
def manage_memberships():
    return render_template('admin/manage/manage-membership.html')


@admin_bp.route('/admin/manage/plans')
@login_required
@role_required('admin')
def manage_plans():
    return render_template('admin/manage/manage-plan.html')

