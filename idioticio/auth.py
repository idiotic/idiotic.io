from .models.user import User
from passlib.hash import bcrypt_sha256


class LoginFailed(Exception):
    pass


class AccountExists(Exception):
    pass


class InvalidPassword(Exception):
    pass


def authenticate(session, email, password):
    user = session.query(User).filter_by(email=email).first()

    if user and bcrypt_sha256.verify(password, user.password):
        return user

    raise LoginFailed()


def register_user(session, name, email, password):
    user = session.query(User).filter_by(email=email).first()

    if user:
        raise AccountExists('That email is already registered')

    if len(password) < 8:
        raise InvalidPassword('Password must be at least 8 characters long')

    user = User(name=name, email=email, password=bcrypt_sha256.hash(password))
    session.add(user)
    session.commit()

    return user