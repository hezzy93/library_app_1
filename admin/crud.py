from sqlalchemy.orm import Session
import schema, models
from sqlalchemy.orm import joinedload

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
def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()

    if not db_user:
        print(f" [!] Book with ID {user_id} not found in the frontend database")
        return {"error": "Book not found"}
    
    db.delete(db_user)
    db.commit()
    
    print(f" [x] Deleted book with ID {user_id} from the frontend database")
    return {"message": f"Book {user_id} deleted successfully"}