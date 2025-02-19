from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base, get_db
import schema, crud

from producer import send_user_created_message, send_book_borrowed
# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()


# Endpoint to Enroll new user
@app.post("/Enroll_User/", tags=["USER API"])
def enroll(user: schema.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    created_user = crud.add_user(db=db, user=user)

    # Publish user-created event to RabbitMQ
    send_user_created_message(created_user.id, created_user.firstname, created_user.lastname, created_user.email)

    
    return {"message": "Account created successfully","user": created_user}

# Endpoint to borrow a book
@app.post("/books/borrow", response_model=schema.BorrowedBookResponse, tags=["Books"])
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





@app.get("/")
def read_root():
    return {"Hello": "Welcome to the User end of the Library API"}