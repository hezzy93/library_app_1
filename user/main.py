from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base, get_db
import schema, crud, models
from typing import List
from schema import Token, TokenData
from crud import create_access_token, verify_password, verify_token, authenticate_user,settings
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from producer import send_user_created_message, send_book_borrowed, return_book_borrowed
# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users_Login")

@app.post("/users_Login")
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    print(f"Logging in User: {user.email}, ID: {user.id}")  # Debugging

    if not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.id is None:
        raise ValueError("User ID is missing from database!")  # Ensure user ID exists

    access_token = create_access_token(data={"sub": user.email, "id": user.id})  
    print(f"Generated Token: {access_token}")  # Debugging

    return {"access_token": access_token, "token_type": "bearer"}


# Dependency to get current user
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("id")

        if email is None or user_id is None:
            raise credentials_exception

        print(f"Decoded Token: {payload}")  # Debugging
        token_data = TokenData(sub=email, id=user_id)

    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == token_data.id).first()

    if user is None:
        raise credentials_exception

    return user

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
def borrow_book(
    book_borrow: schema.BookBorrow, 
    db: Session = Depends(get_db), 
    current_user: TokenData = Depends(get_current_user),  # Ensure we get user ID
):
    borrowed_book = crud.borrow_book(db=db, book_borrow=book_borrow, user_id=current_user.id)

    # Publish borrow book event to RabbitMQ
    send_book_borrowed(
        borrowed_book.id, 
        borrowed_book.available, 
        borrowed_book.borrower_id, 
        borrowed_book.borrow_date, 
        borrowed_book.return_date
    )
    
    return schema.BorrowedBookResponse(
        book_title=borrowed_book.title,
        borrow_date=borrowed_book.borrow_date,
        return_date=borrowed_book.return_date,
        user_email=current_user.email,  # Use authenticated user email
        available=borrowed_book.available
    )



# Endpoint to GET all books
@app.get("/books/", response_model=List[schema.Book], tags=["Book"])
def get_books(db: Session = Depends(get_db), offset: int = 0, limit: int = 10):
    books = crud.get_books(db, offset=offset, limit=limit)
    return books

@app.post("/return_book/", tags=["Book"])
def return_book(
    request: schema.ReturnRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Return a borrowed book if the user is the borrower."""
    book, error = crud.return_book(db, request.book_id, current_user.id)

    if error == "Book not found":
        raise HTTPException(status_code=404, detail=error)

    if error == "Book is already available":
        raise HTTPException(status_code=400, detail=error)

    if error == "You are not the borrower of this book":
        raise HTTPException(status_code=403, detail=error)

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