from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base, get_db
import schema, crud
from typing import List
from producer import send_book_created, send_book_deleted

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()



@app.post("/books/", tags=["Book"])
def create_book(book: schema.BookCreate, db: Session = Depends(get_db)):
    added_book = crud.add_book(db=db, book=book)

    # Publish book-created event to RabbitMQ
    send_book_created(added_book.id, added_book.title, added_book.publisher, added_book.category, added_book.available)

    return {
        "message": "Book added successfully",
        "book": added_book
    }


# Endpoint to DELETE a book by Id
@app.delete("/books/{book_id}/delete", response_model=dict, tags=["Book"])
def delete_book(book_id: int, db: Session = Depends(get_db)):
    result = crud.delete_book(db, book_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    # Send RabbitMQ message **only if the book was deleted successfully**
    send_book_deleted(book_id)
    
    return result

# Endpoint to GET all users
@app.get("/users/", response_model=List[schema.User], tags=["User"])
def get_users(db: Session = Depends(get_db), offset: int = 0, limit: int = 10):
    users = crud.get_users(db, offset=offset, limit=limit)
    return users

# Endpoint to GET all books
@app.get("/books/", response_model=List[schema.Book], tags=["Book"])
def get_books(db: Session = Depends(get_db), offset: int = 0, limit: int = 10):
    books = crud.get_books(db, offset=offset, limit=limit)
    return books

@app.get("/")
def read_root():
    return {"Hello": "Welcome to the Admin end of the Library API"}