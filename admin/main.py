from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base, get_db
import schema, crud
from typing import List
from producer import send_book_created, send_book_deleted, send_user_deleted, send_book_updated

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()


# Endpoint to CREATE book
@app.post("/books/", tags=["Admin"])
def create_book(book: schema.BookCreate, db: Session = Depends(get_db)):
    added_book = crud.add_book(db=db, book=book)

    # Publish book-created event to RabbitMQ
    send_book_created(added_book.id, added_book.title, added_book.publisher, added_book.category, added_book.available)

    return {
        "message": "Book added successfully",
        "book": added_book
    }


# Endpoint to DELETE a book by Id
@app.delete("/books/{book_id}/delete", response_model=dict, tags=["Admin"])
def delete_book(book_id: int, db: Session = Depends(get_db)):
    result = crud.delete_book(db, book_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    # Send RabbitMQ message **only if the book was deleted successfully**
    send_book_deleted(book_id)
    
    return result

# Endpoint to DELETE a user by Id
@app.delete("/users/{user_id}/delete", response_model=dict, tags=["Admin"])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    result = crud.delete_user(db, user_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    # Send RabbitMQ message **only if the user was deleted successfully**
    send_user_deleted(user_id)
    
    return result

# Endpoint to GET all users
@app.get("/users/", response_model=List[schema.User], tags=["Admin"])
def get_users(db: Session = Depends(get_db), offset: int = 0, limit: int = 10):
    users = crud.get_users(db, offset=offset, limit=limit)
    return users

# Endpoint to GET all books
@app.get("/books/", response_model=List[schema.Book1], tags=["Admin"])
def get_books(db: Session = Depends(get_db), offset: int = 0, limit: int = 10):
    books = crud.get_books(db, offset=offset, limit=limit)
    return books

# Endpoint to UPDATE books
@app.put("/books/{book_id}", tags=["Admin"])
def update_book(book_id: int, payload: schema.BookUpdate, db: Session = Depends(get_db)):
    updated_book =crud.update_book(
        db=db,
        book_id=book_id,
        book_update=payload
    )
    if updated_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Publish book-created event to RabbitMQ
    send_book_updated(updated_book.id, updated_book.title, updated_book.publisher, updated_book.category, updated_book.available)
    
    return {'message': 'success', 'data':updated_book}

# Endpoint to UPDATE Book Availability
@app.patch("/books/{book_id}/availability", tags=["Admin"])
def update_book_availability(
    book_id: int,
    payload: schema.BookAvailabilityUpdate,
    db: Session = Depends(get_db)
):
    updated_book = crud.update_book_availability(db, book_id, payload.available)
    if updated_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    # Publish book-availability-changed event to RabbitMQ
    send_book_updated(
        updated_book.id,
        updated_book.title,
        updated_book.publisher,
        updated_book.category,
        updated_book.available
    )

    return {"message": "Availability updated", "data": updated_book}

# Endpoint to GET User by id
@app.get("/users/{user_id}/get/", response_model=schema.User, tags=["Admin"])
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
   user= crud.get_user_by_id(db=db, user_id=user_id) 
   if user is None:
       raise HTTPException(status_code=404, detail="User not found")
   return user   

# Endpoint to GET Book by title
@app.get("/books/title/{title}/", response_model=List[schema.Book], tags=["Admin"] )
def get_book_by_title(title: str, db:Session = Depends(get_db)):
    books=crud.get_book_by_title(db=db, title=title)
    if not books:
        raise HTTPException(status_code=404, detail="Book not found")
    # Convert each SQLAlchemy model instance to a Pydantic schema
    return [schema.Book.model_validate(book) for book in books]

# Endpoint to GET Books by category
@app.get("/books/category/{category}/", response_model=List[schema.Book], tags=["Admin"])
def get_books_by_category(category: str, db: Session = Depends(get_db)):
    books = crud.get_books_by_category(db=db, category=category)
    if not books:
        raise HTTPException(status_code=404, detail="No books found in this category")
    return books

# Endpoint to GET Books by publisher
@app.get("/books/publisher/{publisher}/", response_model=List[schema.Book], tags=["Admin"])
def get_books_by_publisher(publisher: str, db: Session = Depends(get_db)):
    print(f"checking")
    books = crud.get_books_by_publisher(db=db, publisher=publisher)
    if not books:
        raise HTTPException(status_code=404, detail="No books found for this publisher")
    return books

# Endpoint to GET Book by id
@app.get("/books/{book_id}/", response_model=schema.Book, tags=["Admin"])
def get_Book_by_id(book_id: int, db: Session = Depends(get_db)):
   book= crud.get_book_by_id(db=db, book_id=book_id) 
   if book is None:
       raise HTTPException(status_code=404, detail="Book not found")
   return book


# Endpoint to Get borrowed books
@app.get("/borrowed/books/", response_model=List[schema.Book1], tags=["Admin"])
def get_borrowed_books(db: Session = Depends(get_db), offset: int = 0, limit: int = 10):
    books = crud.get_borrowed_books(db, offset=offset, limit=limit)
    return books


@app.get("/")
def read_root():
    return {"Hello": "Welcome to the Admin end of the Library API"}