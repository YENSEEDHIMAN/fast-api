from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Text
from database import Base
from datetime import datetime
target_metadata = Base.metadata
# User Model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True)
    full_name = Column(String(255))
    father_name = Column(String(255))
    dob = Column(Date, nullable=True)
    gender = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255), nullable=False)  # Password should never be null
    address = Column(String(255))
    address_line_2 = Column(String(255), nullable=True)
    city = Column(String(255), nullable=True)
    state = Column(String(255), nullable=True)
    country = Column(String(255), nullable=True)
    pin_code = Column(Integer)
    role = Column(String(255), default="user")
    picture = Column(String(255), nullable=True)

# Book Model
class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    author = Column(String(255))
    description = Column(Text)
    price = Column(Integer)
    image = Column(String(255), nullable=True)  
   
