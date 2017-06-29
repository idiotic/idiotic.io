from flask import Flask, request, session, redirect, url_for, flash, get_flashed_messages,\
    render_template
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
from functools import wraps

from .auth import authenticate, register_user, AccountExists, InvalidPassword, LoginFailed
from .models import Base
from .models.token import Token, Scope

from requests_oauthlib import OAuth2, OAuth2Session, OAuth1, OAuth1Session

from datetime import datetime

import os

APP = Flask(__name__)
DBSESSION = None
CONFIG = {
    'database': 'sqlite:///:memory:',
    'port': 5000,
    'secret_key': os.urandom(24),
}


class InvalidServiceConfig(Exception):
    pass


def validate_service_config(config):
    if not config.get('client_id', None):
        raise InvalidServiceConfig("Invalid value for 'client_id'")

    if not config.get('client_secret', None):
        raise InvalidServiceConfig("Invalid value for 'client_secret'")


def find_service(name):
    services = CONFIG.get('services', {})
    if name in services:
        service = dict(services[name])
        validate_service_config(service)
        service['name'] = name
        return service
    else:
        raise InvalidServiceConfig("Service not found")


def oauth_session_class(service):
    oauth = service.get('oauth', 'oauth2')

    if oauth == 'oauth2':
        return OAuth2Session
    elif oauth == 'oauth1':
        return OAuth1Session


def get_authorization_url(service, session):
    OAuthSession = oauth_session_class(service)
    res = OAuthSession(service['client_id'])

    if 'auth_scope' in service:
        res.scope = service['auth_scope']

    auth_url, state = res.authorization_url(service['auth_url'])

    session['oauth_state_' + service['name']] = state

    return auth_url


def get_token(service, session):
    OAuthSession = oauth_session_class(service)
    res = OAuthSession(service['client_id'], state=session['oauth_state_' + service['name']])
    token = res.fetch_token(service['token_url'],
                            client_secret=service['client_secret'],
                            authorization_response=request.url)

    return token


def get_tokens(db):
    user_id = session.get('user_id', None)
    if user_id:
        tokens = db.query(Token).filter_by(user_id=user_id)
        return tokens
    return []


def store_oauth_token(db, service, token):
    user_id = session.get('user_id', None)
    if user_id:
        store_token = Token(
            service=service['name'],
            user_id=user_id,
            value=token['access_token'],
            type=token.get('token_type', 'bearer'),
            expiration=datetime.fromtimestamp(token.get('expires_at', 4294967295)),
            scopes=[Scope(name=n) for n in token.scopes],
        )

        db.add(store_token)
        db.commit()
    else:
        raise ValueError("Not logged in!")


def requires_login(func):
    @wraps(func)
    def login_checker(*args, **kwargs):
        if session.get('user_id', None):
            return func(*args, **kwargs)
        else:
            return redirect(url_for('login', next=request.full_path))
    return login_checker


@APP.route('/')
def index():
    user_id = session.get('user_id', None)
    user_email = session.get('email', None)
    user_name = session.get('name', None)

    services = CONFIG.get('services', {})
    tokens = get_tokens(DBSESSION)

    return render_template(
        'index.html',
        services=services,
        tokens=tokens,
        authed=bool(user_id),
        user_email=user_email,
        user_name=user_name,
    )


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
            session['user_id'] = user.id
            session['email'] = user.email
            session['name'] = user.name

            flash('Login succeeded')
            return redirect(success_next)
        except LoginFailed:
            flash('Invalid credentials', 'error')
        except Exception as e:
            flash('Unknown error: ' + e.args[0], 'error')
        return render_template('login.html', email=email, next=success_next)
    elif request.method == 'GET':
        return render_template('login.html', next=success_next)


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

                session['user_id'] = user.id
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
@requires_login
def logout():
    if session.get('email', None):
        session.pop('user_id')
        session.pop('email')
        session.pop('name')
        flash('Successfully logged out')
        return redirect(url_for('index'))


@APP.route('/authorize/<service>')
@requires_login
def authorize(service):
    error = request.args.get('error', None)
    if error:
        desc = request.args.get('error_description', None)
        if desc:
            flash('Error authorizing {}: {} ({})'.format(service, desc, error), 'error')
        else:
            flash('Error authorizing {}: {}'.format(service, error), 'error')

        return redirect(url_for('index'))

    oauth = find_service(service)

    url = get_authorization_url(oauth, session)

    return redirect(url)


@APP.route('/callback/<service>')
@requires_login
def callback(service):
    oauth = find_service(service)

    state = session.get('oauth_state_' + oauth['name'], None)

    if not state:
        flash('Invalid request: no OAuth state', 'error')
        return redirect(url_for('index'))

    token = get_token(oauth, session)

    store_oauth_token(DBSESSION, oauth, token)

    flash('Successfully authorized to ' + oauth.get('desc', service))
    return redirect(url_for('index'))


def run(config):
    global DBSESSION
    engine = create_engine(config['database'])
    DBSESSION = sessionmaker(bind=engine)()

    CONFIG.update(config)

    Base.metadata.create_all(engine)

    APP.secret_key = config['secret_key']
    APP.run(port=CONFIG['port'], debug=False)
