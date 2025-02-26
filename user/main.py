from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base, get_db
import schema, crud
from typing import List

from producer import send_user_created_message, send_book_borrowed, return_book_borrowed
# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()


# Endpoint to Enroll new user
@app.post("/Enroll_User/", tags=["USER"])
def enroll(user: schema.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    created_user = crud.add_user(db=db, user=user)

    # Publish user-created event to RabbitMQ
    send_user_created_message(created_user.id, created_user.firstname, created_user.lastname, created_user.email)

    
    return {"message": "Account created successfully","user": created_user}

# Endpoint to borrow a book
@app.post("/books/borrow", response_model=schema.BorrowedBookResponse, tags=["Book"])
def borrow_book(email: str, book_borrow: schema.BookBorrow, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=email)
    if not db_user:
        raise HTTPException(status_code=400, detail="Email not registered")

    borrowed_book = crud.borrow_book(db=db, book_borrow=book_borrow, user_id=db_user.id)

    # Publish borrow book event to RabbitMQ
    send_book_borrowed(borrowed_book.id, borrowed_book.available, borrowed_book.borrower_id, borrowed_book.borrow_date, borrowed_book.return_date)
    
    return schema.BorrowedBookResponse(
        book_title=borrowed_book.title,
        borrow_date=borrowed_book.borrow_date,
        return_date=borrowed_book.return_date,
        user_email=db_user.email,
        available=borrowed_book.available
    )


# Endpoint to GET all books
@app.get("/books/", response_model=List[schema.Book], tags=["Book"])
def get_books(db: Session = Depends(get_db), offset: int = 0, limit: int = 10):
    books = crud.get_books(db, offset=offset, limit=limit)
    return books

@app.post("/return_book/", tags=["Book"])
def return_book(request: schema.ReturnRequest, db: Session = Depends(get_db)):
    """Return a borrowed book."""
    book = crud.return_book(db, request.book_id)
    if not book:
        raise HTTPException(status_code=400, detail="Book not found or not borrowed")

    # Publish book returned event to RabbitMQ
    return_book_borrowed(book.id, book.available, book.borrower_id, book.borrow_date, book.return_date)

    return {"message": f"Book {book.id} returned successfully"}

# Endpoint to GET Book by id
@app.get("/books/{book_id}/", response_model=schema.Book, tags=["Book"])

def get_Book_by_id(book_id: int, db: Session = Depends(get_db)):
   print(f"Fetching book with ID: {book_id}")  # Debugging line
   book= crud.get_book_by_id(db=db, book_id=book_id) 
   if book is None:
       raise HTTPException(status_code=404, detail="Book not found")
   return book

# Endpoint to GET Book by title
@app.get("/books/title/{title}/", response_model=List[schema.Book], tags=["Book"] )
def get_book_by_title(title: str, db:Session = Depends(get_db)):
    print(f"checking")
    books=crud.get_book_by_title(db=db, title=title)
    if not books:
        raise HTTPException(status_code=404, detail="Book not found")
    # Convert each SQLAlchemy model instance to a Pydantic schema
    return [schema.Book.model_validate(book) for book in books]

# Endpoint to GET Books by category
@app.get("/books/category/{category}/", response_model=List[schema.Book], tags=["Book"])
def get_books_by_category(category: str, db: Session = Depends(get_db)):
    books = crud.get_books_by_category(db=db, category=category)
    if not books:
        raise HTTPException(status_code=404, detail="No books found in this category")
    return books

# Endpoint to GET Books by publisher
@app.get("/books/publisher/{publisher}/", response_model=List[schema.Book], tags=["Book"])
def get_books_by_publisher(publisher: str, db: Session = Depends(get_db)):
    books = crud.get_books_by_publisher(db=db, publisher=publisher)
    if not books:
        raise HTTPException(status_code=404, detail="No books found for this publisher")
    return books



@app.get("/")
def read_root():
    return {"Hello": "Welcome to the User end of the Library API"}