from fastapi import HTTPException
from sqlalchemy.orm import Session
import schema, models
from datetime import date, timedelta

# Create User
def add_user(db: Session, user: schema.UserCreate):
    db_user = models.User(
        email=user.email,
        lastname=user.lastname,
        firstname=user.firstname
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