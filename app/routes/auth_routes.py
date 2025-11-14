from flask import Blueprint, render_template, redirect, url_for, flash, session, request, current_app
from app.forms import RegisterForm, LoginForm, ProfileForm
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User
from flask_bcrypt import Bcrypt
from datetime import datetime

# Tell the blueprint where its templates are located (app/routes/templates)
auth_bp = Blueprint('auth', __name__, template_folder='../templates')
bcrypt = Bcrypt()

import os
from werkzeug.utils import secure_filename

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    # Check if the user just registered
    if session.pop('registered', None):  # remove it right after showing
        flash('Account created successfully! You can now log in.', 'success')

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            # flash(f'Welcome back, {user.full_name}!', 'success')

            # Redirect based on role
            if user.role == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            else:
                return redirect(url_for('member.member_dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        # Check if username or email already exist
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()

        if existing_user:
            flash("Username or email already exists.", "danger")
            return render_template("register.html", form=form)

        # Create new user
        new_user = User(
            full_name=form.fullname.data,
            username=form.username.data,
            email=form.email.data,
            role='member'
        )
        new_user.set_password(form.password.data)

        db.session.add(new_user)
        db.session.commit()
        
        # Store success message in session
        session['registered'] = True
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# @auth_bp.route('/profile', methods=['GET', 'POST'])
# @login_required
# def profile():
# 	user = User.query.get_or_404(current_user.id)
# 	form = ProfileForm(obj=user)
# 	if form.validate_on_submit():
# 		user.full_name = form.full_name.data
# 		user.email = form.email.data
# 		user.contact_number = form.contact_number.data
# 		# Password update (optional)
# 		if form.password.data:
# 			user.set_password(form.password.data)
# 		# Handle profile image upload
# 		if hasattr(form, 'image') and form.image.data:
# 			file = form.image.data
# 			filename = secure_filename(file.filename)
# 			upload_folder = os.path.join(current_app.root_path, 'static', 'img', 'users')
# 			os.makedirs(upload_folder, exist_ok=True)
# 			prefixed = f"u{user.id}_{int(datetime.today().date())}_{filename}"  
# 			filepath = os.path.join(upload_folder, prefixed)
# 			file.save(filepath)
# 			user.image = prefixed
# 		db.session.commit()
# 		flash('Profile updated successfully!', 'success')
# 		return redirect(url_for('profile.profile'))
# 	return render_template('profile/profile.html', form=form, user=user)