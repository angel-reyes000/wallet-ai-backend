from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Integer

class Base(DeclarativeBase):
    pass

class user(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String)
    email = Column(String)
    password = Column(String)