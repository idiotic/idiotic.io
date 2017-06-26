from sqlalchemy import Column, Integer, String
from . import Base

class User(Base):
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password = Column(String)
    name = Column(String)
    
