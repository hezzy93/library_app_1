from sqlalchemy.orm import Session
import schema, models

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
    return db.query(models.Book).offset(offset).limit(limit).all()

