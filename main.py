from pathlib import Path  
from fastapi import FastAPI, Depends, Request, Form, UploadFile, File, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import shutil, os, logging

from database import SessionLocal, engine
from database_models import Base
from models import User, Book
from schemas import BookCreate, Book as BookSchema, ShowUser
from utils import hash_password, verify_password
from auth import create_access_token, get_current_user

app = FastAPI()

# Setup
templates = Jinja2Templates(directory="templates")
app.mount("/media", StaticFiles(directory="media"), name="media")
app.mount("/static", StaticFiles(directory="static"), name="static")

Base.metadata.create_all(bind=engine)

MEDIA_DIR = "media"
ALLOWED_EXTENSIONS = ["image/jpeg", "image/png"]
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

logging.basicConfig(level=logging.INFO)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def validate_image(picture: UploadFile):
    if picture.content_type not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid image format")
    picture.file.seek(0)
    size = len(picture.file.read())
    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Image size exceeds 5MB")
    picture.file.seek(0)

# Routes for user authentication
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def show_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})
from datetime import datetime
@app.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    full_name: str = Form(...),
    username: str = Form(...),
    father_name: str = Form(...),
    dob: str = Form(...),
    gender: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirmation: str = Form(...),
    address: str = Form(...),
    address_line_2: str = Form(None),
    city: str = Form(...),
    state: str = Form(...),
    country: str = Form(...),
    pin_code: int = Form(...),
    role: str = Form("user"),
    picture: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Password confirmation check
    if password != password_confirmation:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Passwords do not match"})

    # Unique username check
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username already exists"})

    # Unique email check
    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email already exists"})

    # Validate image
    validate_image(picture)

    # Save image
    user_dir = os.path.join(MEDIA_DIR, username)
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, picture.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(picture.file, f)

    # Convert DOB to date
    try:
        dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
    except Exception as e:
        return templates.TemplateResponse("register.html", {"request": request, "error": f"Invalid date format: {str(e)}"})

    # Create user
    hashed = hash_password(password)
    user = User(
        full_name=full_name,
        username=username,
        father_name=father_name,
        dob=dob_date,
        gender=gender,
        email=email,
        password=hashed,
        address=address,
        address_line_2=address_line_2,
        city=city,
        state=state,
        country=country,
        pin_code=pin_code,
        role=role,
        picture=f"/media/{username}/{picture.filename}",
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    return RedirectResponse(url="/login?msg=registered", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def show_login(request: Request):
    msg = request.query_params.get("msg")
    return templates.TemplateResponse("login.html", {"request": request, "msg": msg})

@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

    token = create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=token)
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, current_user: ShowUser = Depends(get_current_user)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": current_user})

# ------------------------ BOOK ROUTES ------------------------

@app.get("/books")
async def get_books(request: Request, db: Session = Depends(get_db), current_user: ShowUser = Depends(get_current_user)):
    books = db.query(Book).all()
    return templates.TemplateResponse("books/list_books.html", {"request": request, "books": books})

@app.get("/books/list-view", response_class=HTMLResponse)
async def list_books_view(request: Request, search: str = '', db: Session = Depends(get_db), current_user: ShowUser = Depends(get_current_user)):
    # Query the books from the database with search functionality
    query = db.query(Book)
    if search:
        query = query.filter(
            (Book.title.ilike(f"%{search}%")) | 
            (Book.author.ilike(f"%{search}%"))
        )
    
    # Fetch all books matching the search criteria
    books = query.all()

    # Return the response with the books data
    return templates.TemplateResponse(
        "books/list_books.html", 
        {"request": request, "books": books, "search_query": search}
    )

@app.get("/books/add", response_class=HTMLResponse)
def add_book_page(request: Request, current_user: ShowUser = Depends(get_current_user)):
    return templates.TemplateResponse("books/add_book.html", {"request": request})

@app.post("/books/add")
async def add_book(
    title: str = Form(...),
    author: str = Form(...),
    description: str = Form(...),
    price: int = Form(...),
    image: UploadFile = File(None),  # Handle the image file
   
  
    current_user: ShowUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Save the image if it exists
    image_url = None
    if image:
        # Define the image folder path
        image_folder = Path("static/images/")
        image_folder.mkdir(parents=True, exist_ok=True)
        
        # Create the file path
        image_filename = image.filename
        image_path = image_folder / image_filename
        
        # Save the image file to disk
        with open(image_path, "wb") as buffer:
            buffer.write(await image.read())
        
        # Use the relative path for the image (FastAPI will handle serving this from static)
        image_url = f"/static/images/{image_filename}"

    # Create a new book record
    book = Book(
        title=title,
        author=author,
        description=description,
        price=price,

       
        image=image_url  # Save the image URL in the database
    )
    
    db.add(book)
    db.commit()
    
    # Redirect to the books listing page after adding the book
    return RedirectResponse(url="/books", status_code=302)

@app.get("/books/edit/{book_id}", response_class=HTMLResponse)
def edit_book_form(request: Request, book_id: int, db: Session = Depends(get_db), current_user: ShowUser = Depends(get_current_user)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")
    return templates.TemplateResponse("books/edit_book.html", {"request": request, "book": book})

@app.post("/books/edit/{book_id}")
async def update_book(
    book_id: int,
    title: str = Form(...),
    author: str = Form(...),
    description: str = Form(...),
    price: int = Form(...),
    image: UploadFile = File(None),
    current_user: ShowUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    book.title = title
    book.author = author
    book.description = description
    book.price = price

    if image:
        validate_image(image)
        user_dir = os.path.join(MEDIA_DIR, str(book.id))
        os.makedirs(user_dir, exist_ok=True)
        file_path = os.path.join(user_dir, image.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(image.file, f)
        book.image = f"/media/{book.id}/{image.filename}"

    db.commit()
    return RedirectResponse(url="/books", status_code=302)

@app.get("/books/delete/{book_id}", response_class=HTMLResponse)
def delete_book(request: Request, book_id: int, db: Session = Depends(get_db), current_user: ShowUser = Depends(get_current_user)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")
    db.delete(book)
    db.commit()
    return RedirectResponse(url="/books", status_code=302)

@app.post("/books/delete/{book_id}")
def confirm_delete(book_id: int, db: Session = Depends(get_db), current_user: ShowUser = Depends(get_current_user)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")
    
    db.delete(book)
    db.commit()
    return RedirectResponse(url="/books", status_code=302)

