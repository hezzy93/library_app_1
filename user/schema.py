from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date

class UserBase(BaseModel):
    email: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Schema for book 
class BookBase(BaseModel):
    title: str
    publisher: str
    category: str
    available: bool = True

    model_config = ConfigDict(from_attributes=True)

class Book(BookBase):
    id: int
    borrower_id: Optional[int] = None  # ID of the user who borrowed the book
    borrow_date: Optional[date] = None
    return_date: Optional[date] = None

class BookCreate(BookBase):
    pass  # Inherits from BookBase

class BookBorrow(BaseModel):
    book_id: int  # Identify the book to borrow by ID
    borrow_duration: int

class BorrowedBookResponse(BaseModel):
    book_title: str
    borrow_date: date
    return_date: date
    user_email: str
    available: bool

    model_config = ConfigDict(from_attributes=True)