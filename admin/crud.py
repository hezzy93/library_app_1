from sqlalchemy.orm import Session
import schema, models
from sqlalchemy.orm import joinedload


# Function to ADD book
def add_book(db: Session, book: schema.BookCreate):
    # Create and add the book
    db_book = models.Book(
        title=book.title,
        publisher=book.publisher,
        category=book.category,
        available=True
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

# Funtion to DELETE book
def delete_book(db: Session, book_id: int):
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()

    if not db_book:
        print(f" [!] Book with ID {book_id} not found in the frontend database")
        return {"error": "Book not found"}
    
    db.delete(db_book)
    db.commit()
    
    print(f" [x] Deleted book with ID {book_id} from the frontend database")
    return {"message": f"Book {book_id} deleted successfully"}

#Get all users
def get_users(db: Session, offset: int = 0, limit: int = 10):
    return db.query(models.User).offset(offset).limit(limit).all()

#Get all books
def get_books(db: Session, offset: int = 0, limit: int = 10):
    return (
        db.query(models.Book)
        .options(joinedload(models.Book.user))  # ✅ Now correctly loads borrower
        .offset(offset)
        .limit(limit)
        .all()
    )

# Function to DELETE User
def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()

    if not db_user:
        print(f" [!] User with ID {user_id} not found in the frontend database")
        return {"error": "User not found"}
    
    db.delete(db_user)
    db.commit()
    
    print(f" [x] Deleted user with ID {user_id} from the frontend database")
    return {"message": f"User {user_id} deleted successfully"}


#Function to Update Book
def update_book(db:Session, book_id: int, book_update: schema.BookUpdate):
    db_book =db.query(models.Book).filter(models.Book.id == book_id).first()
    if not db_book:
        return None
    
    for key, value in book_update.model_dump(exclude_unset=True).items():
            setattr(db_book, key, value)
            
    db.commit()
    db.refresh(db_book)
    return db_book

# Function to UPDATE book Availabilty
def update_book_availability(db: Session, book_id: int, available: bool):
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not db_book:
        return None

    db_book.available = available
    db.commit()
    db.refresh(db_book)
    return db_book


# GET USER BY id
def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id ==user_id).first()

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