from flask import Flask, request, session, redirect, url_for, flash, get_flashed_messages,\
    render_template
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
from functools import wraps

from .auth import authenticate, register_user, AccountExists, InvalidPassword, LoginFailed
from .models import Base

import os

APP = Flask(__name__)
DBSESSION = None
APP.secret_key = os.urandom(24)


def requires_login(func):
    @wraps(func)
    def login_checker(*args, **kwargs):
        if session.get('email', None):
            return func(*args, **kwargs)
        else:
            return redirect(url_for('login', next=request.full_path))
    return login_checker


@APP.route('/')
def index():
    return render_template('index.html')


@APP.route('/login', methods=['GET', 'POST'])
def login():
    success_next = request.args.get('next', url_for('index'))

    if session.get('email', None):
        flash('Already logged in')
        return redirect(success_next)

    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')

        try:
            user = authenticate(DBSESSION, email, password)
            session['email'] = user.email
            session['name'] = user.name

            flash('Login succeeded')
            return redirect(success_next)
        except LoginFailed:
            flash('Invalid credentials', 'error')
        except Exception as e:
            flash('Unknown error: ' + e.args[0], 'error')
        return render_template('login.html', email=email)
    elif request.method == 'GET':
        return render_template('login.html')


@APP.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('email', None):
        flash('Already registered')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        password1 = request.form.get('password1', '')
        password2 = request.form.get('password2', '')

        if password1 != password2:
            flash('Passwords do not match', 'error')
        else:
            try:
                user = register_user(DBSESSION, name, email, password1)

                session['email'] = user.email
                session['name'] = user.name

                flash('Account created')
                return redirect(url_for('index'))
            except AccountExists:
                flash('That email address is already in use', 'error')
            except InvalidPassword:
                flash('Password must be at least 8 characters long')
        return render_template('register.html', name=name, email=email)
    elif request.method == 'GET':
        return render_template('register.html')

@APP.route('/logout')
def logout():
    if session.get('email', None):
        session.pop('email')
        session.pop('name')
        flash('Successfully logged out')
        return redirect(url_for('index'))


@APP.route('/authorize', methods=['GET', 'POST'])
@requires_login
def authorize():
    if request.method == 'POST':
        print(request.postdata)
    else:
        return '''
    <!DOCTYPE html>
    <html>
    <head><title>idiotic.io</title></head>
    <body>
    <em>TODO</em>
    </body>
    </html>
    '''


def run(port, db, config):
    global DBSESSION
    engine = create_engine(db)
    DBSESSION = sessionmaker(bind=engine)()

    Base.metadata.create_all(engine)

    APP.run(debug=False)
