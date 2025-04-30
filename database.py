# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database_models import Base  # Assuming you have models defined
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL = "mysql://root:root@localhost/books_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ This is the correct way for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database tables
Base = declarative_base()
Base.metadata.create_all(bind=engine)
