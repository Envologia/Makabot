# db.py

from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")
Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(Integer, unique=True, index=True)
    name = Column(String)
    university = Column(String)
    age = Column(Integer)
    gender = Column(String)
    interests = Column(String)
    looking_for = Column(String)
    registered = Column(Boolean, default=False)
    photo_file_id = Column(String, nullable=True)
    bio = Column(String, default="")
    match_universities = Column(String, default="")  # Comma-separated
    chatting_with = Column(Integer, nullable=True)   # tg_id of chat partner

class Like(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey('users.id'))
    to_user_id = Column(Integer, ForeignKey('users.id'))
    matched = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
