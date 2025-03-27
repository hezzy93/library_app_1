from fastapi import HTTPException
from sqlalchemy.orm import Session
import schema, models
from datetime import date, timedelta
from datetime import timedelta
from auth import hash_password


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

