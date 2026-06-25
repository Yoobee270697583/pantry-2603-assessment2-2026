from flask import Blueprint, redirect, render_template, flash, url_for
from flask_login import login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db
from forms import LoginForm, RegisterForm

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('kitchen.kitchen'))
        flash('Invalid email or password.', 'error')

    return render_template("login.html", form=form)


@auth_bp.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(first_name=form.first_name.data, last_name=form.last_name.data, email=form.email.data, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Something went wrong creating your account. Please try again.', 'error')
            return render_template("register.html", form=form)

        flash('Account created! ✅ Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template("register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
