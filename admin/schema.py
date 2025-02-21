from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date

class UserBase(BaseModel):
    email: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None

class UserCreate(UserBase):
    pass




    model_config = ConfigDict(from_attributes=True)


# Schema for book response including borrow information
class Book(BaseModel):
    id: int
    title: str
    publisher: str
    category: str
    available: bool
    borrower_id: Optional[int] = None  # ID of the user who borrowed the book
    borrow_date: Optional[date] = None  # Date when the book was borrowed
    return_date: Optional[date] = None  # Date when the book is due to be returned

    model_config = ConfigDict(from_attributes=True)

class Book1(Book):
    id:int
    user: Optional[UserBase] = None

# Schema for creating new books
class BookCreate(BaseModel):
    title: str
    publisher: str
    category: str
    available: bool = True

    model_config = ConfigDict(from_attributes=True)

class User(UserBase):
    id: int
    books: List[Book] = [] 