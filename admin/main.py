from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base, get_db
import schema, crud
from producer import send_book_created, send_book_deleted

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()



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

@app.get("/")
def read_root():
    return {"Hello": "Welcome to the Admin end of the Library API"}