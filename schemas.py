from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime

# User creation schema for input validation
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    father_name: str
    dob: Optional[date] = None
    gender: Optional[str] = None
    address: str
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pin_code: int
    role: Optional[str] = "user"
    picture: Optional[str] = None

# User login schema for validating login input
class UserLogin(BaseModel):
    username: str
    password: str

# User display schema for showing user information (e.g., when fetching a user profile)
class ShowUser(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str
    father_name: str
    dob: Optional[date]
    gender: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    address: str
    address_line_2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    pin_code: int
    role: str
    picture: Optional[str]

    class Config:
        orm_mode = True

# Book creation schema for input validation
class BookCreate(BaseModel):
    title: str
    author: str
    description: str
    price: int
    image: Optional[str] = None  # Image field for book cover (optional)
    is_available_for_purchase: Optional[bool] = True  # Whether the book is available for purchase
    add_to_cart: Optional[bool] = False  # Whether the book is marked to be added to cart

# Book schema for displaying book information (e.g., when fetching book details)
class ShowBook(BaseModel):
    id: int
    title: str
    author: str
    description: Optional[str] = None
    price: int
    image: Optional[str] = None
    is_available_for_purchase: bool
    add_to_cart: bool

    class Config:
        orm_mode = True

# Book output schema for showing book details without additional fields
class Book(BaseModel):
    id: int
    title: str
    author: str
    description: Optional[str] = None
    price: int
    image: Optional[str] = None
    is_available_for_purchase: bool
    add_to_cart: bool

    class Config:
        orm_mode = True
