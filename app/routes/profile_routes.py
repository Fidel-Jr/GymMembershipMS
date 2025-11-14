from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models import User, db
from app.forms import ProfileForm
import os
from werkzeug.utils import secure_filename
from datetime import datetime

profile_bp = Blueprint('profile', __name__, template_folder='templates')

# Profile view and update (for logged-in user)
@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
	user = User.query.get_or_404(current_user.id)
	form = ProfileForm(obj=user)
	if form.validate_on_submit():
		user.full_name = form.full_name.data
		user.email = form.email.data
		user.contact_number = form.contact_number.data
		user.role = form.role.data
		# Password update (optional)
		if form.password.data:
			user.set_password(form.password.data)
		# Handle profile image upload
		if form.image.data and hasattr(form.image.data, "filename"):
			file = form.image.data
			filename = secure_filename(file.filename)

			upload_folder = os.path.join(current_app.root_path, 'static', 'img', 'users')
			os.makedirs(upload_folder, exist_ok=True)

			prefixed = f"u{user.id}_{int(datetime.utcnow().timestamp())}_{filename}"
			filepath = os.path.join(upload_folder, prefixed)

			file.save(filepath)
			user.image = prefixed

		db.session.commit()
		flash('Profile updated successfully!', 'success')
		return redirect(url_for('profile.profile'))
	return render_template('profile/profile.html', form=form, user=user)
