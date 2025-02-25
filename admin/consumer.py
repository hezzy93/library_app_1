import pika
import json
import time
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Book
from messaging.config import get_rabbitmq_connection


def process_user_created(ch, method, properties, body):
    """Process messages from RabbitMQ and add users to Admin API database."""
    try:
        data = json.loads(body)

        if not all(k in data for k in ["user_id", "firstname", "lastname", "email"]):
            print(f"⚠️ Invalid user message format: {data}")
            return

        user_id = data["user_id"]
        firstname = data["firstname"]
        lastname = data["lastname"]
        email = data["email"]

        db: Session = SessionLocal()
        try:
            existing_user = db.query(User).filter(User.id == user_id).first()
            if not existing_user:
                new_user = User(id=user_id, firstname=firstname, lastname=lastname, email=email)
                db.add(new_user)
                db.commit()
                print(f"✅ Admin API: User {email} added to PostgreSQL")
            else:
                print(f"ℹ️ User {email} already exists in PostgreSQL")
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error processing user message: {e}")


def process_book_borrowed(ch, method, properties, body):
    """Process messages from RabbitMQ for book borrowing."""
    try:
        data = json.loads(body)

        if not all(k in data for k in ["book_id", "available", "borrower_id", "borrow_date","return_date"]):
            print(f"⚠️ Invalid user message format: {data}")
            return

        book_id = data["book_id"]
        available = data["available"]
        borrower_id = data["borrower_id"]
        borrow_date = data["borrow_date"]
        return_date = data["return_date"]

        db: Session = SessionLocal()
        try:
            db_book = db.query(Book).filter(Book.id == book_id).first()
            if db_book:
                # ✅ Update the existing book record
                db_book.available = available
                db_book.borrower_id = borrower_id
                db_book.borrow_date = borrow_date
                db_book.return_date = return_date

                db.commit()
                print(f"✅ Admin API: Book {book_id} marked as borrowed in PostgreSQL")
            else:
                print(f"⚠️ Admin API: Book {book_id} not found in database")
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error processing book borrow message: {e}")



def process_book_returned(ch, method, properties, body):
    """Process messages from RabbitMQ for book return."""
    try:
        data = json.loads(body)

        if not all(k in data for k in ["book_id", "available", "borrower_id", "borrow_date", "return_date"]):
            print(f"⚠️ Invalid book return message format: {data}")
            return

        book_id = data["book_id"]
        available = data["available"]
        borrower_id = data["borrower_id"]
        borrow_date = data["borrow_date"]
        return_date = data["return_date"]

        db: Session = SessionLocal()
        try:
            db_book = db.query(Book).filter(Book.id == book_id).first()
            if db_book:
                db_book.available = available
                db_book.borrower_id = borrower_id
                db_book.borrow_date = borrow_date
                db_book.return_date = return_date

                db.commit()
                print(f"✅ Admin API: Book {book_id} marked as returned in PostgreSQL")
            else:
                print(f"⚠️ Admin API: Book {book_id} not found in database")
        except Exception as db_error:
            db.rollback()  # ✅ Rollback in case of failure
            print(f"❌ Database error: {db_error}")
        finally:
            db.close()  # ✅ Ensure DB session is closed
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON format in message: {body}")
    except Exception as e:
        print(f"❌ Unexpected error processing book return message: {e}")





def start_consumer():
    """Start RabbitMQ consumer with automatic reconnection."""
    while True:
        try:
            connection = get_rabbitmq_connection()
            channel = connection.channel()

            # Declare queues
            channel.queue_declare(queue="user_created", durable=False)
            channel.queue_declare(queue="book_borrowed", durable=False)
            channel.queue_declare(queue="book_returned", durable=False)
            



            # Consume messages from both queues
            channel.basic_consume(queue="user_created", on_message_callback=process_user_created, auto_ack=True)
            channel.basic_consume(queue="book_borrowed", on_message_callback=process_book_borrowed, auto_ack=True)
            channel.basic_consume(queue="book_returned", on_message_callback=process_book_returned, auto_ack=True)
            
            print("🎧 Admin API is listening for user creation events...")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as e:
            print(f"🔴 RabbitMQ Connection Error: {e}. Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    start_consumer()
