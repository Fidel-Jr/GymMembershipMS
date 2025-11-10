from flask import Blueprint, render_template, redirect, url_for, flash, request , session
from app.models import User
from flask_login import login_required
from app.utils.decorators import role_required

member_bp = Blueprint('member', __name__, template_folder='templates')

@member_bp.route('/member/dashboard')
@login_required
@role_required('member')
def member_dashboard():
    return render_template('member/dashboard.html')