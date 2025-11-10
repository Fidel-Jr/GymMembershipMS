from flask import Blueprint, render_template, redirect, url_for, flash, request , session
from app.models import User
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
    return render_template('about.html', users=users)