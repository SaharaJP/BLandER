from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./blander.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True)
    password_hash = Column(String(200))
    subscription = Column(String(20), default="free")
    created_at = Column(DateTime, default=datetime.utcnow)
    stripe_id = Column(String(100), default="None")

class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    lesson_id = Column(Integer, primary_key=True)
    completed = Column(Boolean, default=False)
    score = Column(Integer)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Функция для подключения к базе
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()