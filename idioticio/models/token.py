from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from datetime import datetime

from . import Base


class Token(Base):
    __tablename__ = 'tokens'

    id = Column(Integer, primary_key=True)
    service = Column(String)

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='tokens')

    value = Column(String)
    type = Column(String)
    expiration = Column(DateTime)
    scopes = relationship('Scope')

    @property
    def scope_names(self):
        return (scope.name for scope in self.scopes)

    def to_oauthlib_token(self):
        return {
            'access_token': self.value,
            'token_type': self.type,
            'expires_at': self.expiration.timestamp(),
        }


class Scope(Base):
    __tablename__ = 'scopes'

    id = Column(Integer, primary_key=True)

    token_id = Column(Integer, ForeignKey('tokens.id'))
    token = relationship('Token', back_populates='scopes')

    name = Column(String)
