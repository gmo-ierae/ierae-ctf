import os, base64
from functools import wraps
from flask import request, render_template, redirect, url_for, session
from app import app, db, bcrypt, login_manager
from app.models import User
from flask_login import login_user, current_user, logout_user, login_required

def admin_required(f):
    @wraps(f)
    def _wrapper(*args, **keywords):
        if not current_user.is_admin:
            return redirect(url_for('home', message='Required is_admin=True'))
        v = f(*args, **keywords)
        return v
    return _wrapper

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.jinja2')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or len(username) < 8 or len(username) > 20:
            return redirect(url_for('register', message='Username should be between 8 and 20 characters long'))
        if not password or len(password) < 8:
            return redirect(url_for('register', message='Password should be least 8 characters long'))

        user = User.query.filter_by(username=username).first()
        if user:
            return redirect(url_for('register', message='Duplicate username'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login', message='Your account has been created!'))
    return render_template('register.jinja2')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or len(username) < 8 or len(username) > 20:
            return redirect(url_for('login', message='Username should be between 8 and 20 characters long'))
        if not password or len(password) < 8:
            return redirect(url_for('login', message='Password should be least 8 characters long'))

        user = User.query.filter_by(username=username).first()
        if not user or not bcrypt.check_password_hash(user.password, password):
            return redirect(url_for('login', message='Failed login'))

        login_user(user)
        session["csrf_token"] = os.urandom(16).hex()
        return redirect(url_for('home'))
    return render_template('login.jinja2')

@app.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin():
    if request.method == 'POST':
        username = request.form.get('username')
        csrf_token = request.form.get('csrf_token')

        if not username or len(username) < 8 or len(username) > 20:
            return redirect(url_for('admin', message='Username should be between 8 and 20 characters long'))

        if not csrf_token or csrf_token != session.get('csrf_token'):
            return redirect(url_for('admin', message='Invalid csrf_token'))

        user = User.query.filter_by(username=username).first()
        if not user:
            return redirect(url_for('admin', message='Not found username'))

        user.is_admin = True
        db.session.commit()
        return redirect(url_for('admin', message='Success make admin!'))
    return render_template('admin.jinja2', csrf_token=session.get('csrf_token'))

@app.route('/admin/flag')
@login_required
@admin_required
def admin_flag():
    return app.config['FLAG']

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))
