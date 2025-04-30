from fastapi import HTTPException, Request, Depends
from sqlalchemy.orm import Session
from jose import JWTError, jwt, ExpiredSignatureError
from datetime import datetime, timedelta
from typing import Optional
from database import get_db
from models import User
import logging

# Constants
SECRET_KEY = "your_secret_key" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10

# Create JWT token with expiration
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire, "sub": data.get("sub")})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Get current user from cookie and validate token
def get_current_user(request: Request, db: Session = Depends(get_db)):
    try:
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated (No token)")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token: No username")

        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        # Successful authentication, return user info
        return {
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "picture": user.picture
        }

    except ExpiredSignatureError:
        logging.error("Token expired")
        raise HTTPException(status_code=401, detail="Token has expired")

    except JWTError as e:
        logging.error(f"JWT error: {e}")
        raise HTTPException(status_code=401, detail="Invalid or malformed token")

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
