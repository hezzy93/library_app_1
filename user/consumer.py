import pika
import json
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Book, User
from messaging.config import get_rabbitmq_connection

def book_created_callback(ch, method, properties, body):
    """Process book_created messages from Admin API."""
    data = json.loads(body)
    book_id = data["book_id"]
    title = data["title"]
    publisher = data["publisher"]
    category = data["category"]
    available = data["available"]

    db: Session = SessionLocal()

    # Check if book already exists
    existing_book = db.query(Book).filter(Book.id == book_id).first()
    if not existing_book:
        new_book = Book(id=book_id, title=title, publisher=publisher, category=category, available=available)
        db.add(new_book)
        db.commit()
        print(f"✅ User API: Book '{title}' added to Mysql")

    db.close()


def process_book_deleted(ch, method, properties, body):
    """Process messages from RabbitMQ for book deletion."""
    try:
        data = json.loads(body)

        if "book_id" not in data:
            print(f"⚠️ Invalid book delete message format: {data}")
            return

        book_id = data["book_id"]

        db: Session = SessionLocal()
        try:
            db_book = db.query(Book).filter(Book.id == book_id).first()
            if db_book:
                db.delete(db_book)  # ✅ Delete book from database
                db.commit()
                print(f"🗑️ Admin API: Book {book_id} deleted from PostgreSQL")
            else:
                print(f"⚠️ Admin API: Book {book_id} not found in database")
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error processing book delete message: {e}")







def process_user_deleted(ch, method, properties, body):
    """Process messages from RabbitMQ for user deletion."""
    try:
        data = json.loads(body)

        if "user_id" not in data:
            print(f"⚠️ Invalid book delete message format: {data}")
            return

        user_id = data["user_id"]

        db: Session = SessionLocal()
        try:
            db_user = db.query(User).filter(User.id == user_id).first()
            if db_user:
                db.delete(db_user)  # ✅ Delete user from database
                db.commit()
                print(f"🗑️ Admin API:User {user_id} deleted from PostgreSQL")
            else:
                print(f"⚠️ Admin API: User {user_id} not found in database")
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error processing book delete message: {e}")



def process_book_updated(ch, method, properties, body):
    """Process messages from RabbitMQ for book borrowing."""
    try:
        data = json.loads(body)

        if not all(k in data for k in ["book_id", "title", "publisher", "category","available"]):
            print(f"⚠️ Invalid user message format: {data}")
            return

        book_id = data["book_id"]
        title = data["title"]
        publisher = data["publisher"]
        category = data["category"]
        available = data["available"]


        db: Session = SessionLocal()
        try:
            db_book = db.query(Book).filter(Book.id == book_id).first()
            if db_book:
                # ✅ Update the existing book record
                db_book.title = title
                db_book.publisher = publisher
                db_book.category = category
                db_book.available = available

                db.commit()
                print(f"✅ Admin API: Book {book_id} marked as updated in PostgreSQL")
            else:
                print(f"⚠️ Admin API: Book {book_id} not found in database")
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error processing book borrow message: {e}")


   # Setup RabbitMQ Consumer
connection = get_rabbitmq_connection()
channel = connection.channel()

# Declare queues
channel.queue_declare(queue="book_created")
channel.queue_declare(queue="book_deleted", durable=False)
channel.queue_declare(queue="user_deleted", durable=False)

channel.queue_declare(queue="book_updated", durable=False)
# Bind consumers to queues
channel.basic_consume(queue="book_created", on_message_callback=book_created_callback, auto_ack=True)
channel.basic_consume(queue="book_deleted", on_message_callback=process_book_deleted, auto_ack=True)  # ✅ Listen for delete messages
channel.basic_consume(queue="user_deleted", on_message_callback=process_user_deleted, auto_ack=True)

channel.basic_consume(queue="book_updated", on_message_callback=process_book_updated, auto_ack=True)


print("🎧 User API is listening for book updates...")
channel.start_consuming()
