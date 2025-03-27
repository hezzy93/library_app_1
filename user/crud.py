from fastapi import HTTPException
from sqlalchemy.orm import Session
import schema, models
from datetime import date, timedelta
import bcrypt
from models import User
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from schema import TokenData
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    SECRET_KEY: str  # Ensure this is set in the .env file
    ALGORITHM: str = "HS256"  # Set a default algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Default expiration time if not set

# Initialize settings
settings = Settings()


# Create User
def add_user(db: Session, user: schema.UserCreate):
    hashed_password = hash_password(user.password)
    db_user = models.User(
        email=user.email,
        lastname=user.lastname,
        firstname=user.firstname,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Get User by email
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email.ilike(email)).first()


# Borrow Book
def borrow_book(db: Session, book_borrow: schema.BookBorrow, user_id: int):
    db_book = db.query(models.Book).filter(models.Book.id == book_borrow.book_id).first()

    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")

    if not db_book.available:
        raise HTTPException(status_code=400, detail="Book is not available")

    # Update the book's availability and borrow details in the frontend database
    db_book.available = False
    db_book.borrower_id = user_id
    db_book.borrow_date = date.today()
    db_book.return_date = date.today() + timedelta(days=book_borrow.borrow_duration)

    db.commit()
    db.refresh(db_book)

    return db_book


#Get all books
def get_books(db: Session, offset: int = 0, limit: int = 10):
    return db.query(models.Book).offset(offset).limit(limit).all()

# Function to return borrowed books
def return_book(db: Session, book_id: int, user_id: int):
    """Marks a book as returned and updates availability if the user is the borrower."""
    book = db.query(models.Book).filter(
        models.Book.id == book_id
    ).first()

    if not book:
        return None, "Book not found"

    if book.available:
        return None, "Book is already available"

    if book.borrower_id != user_id:
        return None, "You are not the borrower of this book"

    # Update book availability
    book.available = True
    book.borrower_id = None
    book.borrow_date = None
    book.return_date = None

    db.commit()
    db.refresh(book)
    return book, None




# GET BOOK BY title
def get_book_by_title(db: Session, title: str):
    return db.query(models.Book).filter(models.Book.title.ilike(f"%{title}%")).all()

# GET BOOKS BY CATEGORY
def get_books_by_category(db: Session, category: str):
    return db.query(models.Book).filter(models.Book.category.ilike(f"%{category}%")).all()



# GET BOOK BY publisher
def get_books_by_publisher(db: Session, publisher: str):
    return db.query(models.Book).filter(models.Book.publisher.ilike(f"%{publisher}%")).all()


# GET Book BY id
def get_book_by_id(db: Session, book_id: int):
    return db.query(models.Book).filter(models.Book.id ==book_id).first()


#Hash Password
def hash_password(password: str) -> str:
    # Hash a password
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

#verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Ensure hashed_password is not None before verification
    if not hashed_password:
        return False
    # Verify a hashed password
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

#Authenticate for login
def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None



# Create Access Token
# Create Access Token
def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=30)):
    to_encode = data.copy()

    if "id" not in to_encode or to_encode["id"] is None:
        raise ValueError("User ID must be provided when generating the token")  

    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt  # Ensure token is returned


# Verify Token
def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print(f"Decoded Token: {payload}")  # Debugging

        user_email: str = payload.get("sub")
        user_id: str = payload.get("id")  # Extract ID

        if user_email is None or user_id is None:
            raise credentials_exception

        return TokenData(email=user_email, id=user_id)  # Ensure ID is returned
    except JWTError:
        raise credentials_exception

