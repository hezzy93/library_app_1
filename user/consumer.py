import pika
import json
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Book
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


   # Setup RabbitMQ Consumer
connection = get_rabbitmq_connection()
channel = connection.channel()

# Declare queues
channel.queue_declare(queue="book_created")
channel.queue_declare(queue="book_deleted", durable=False)

# Bind consumers to queues
channel.basic_consume(queue="book_created", on_message_callback=book_created_callback, auto_ack=True)
channel.basic_consume(queue="book_deleted", on_message_callback=process_book_deleted, auto_ack=True)  # ✅ Listen for delete messages

print("🎧 User API is listening for book updates...")
channel.start_consuming()
