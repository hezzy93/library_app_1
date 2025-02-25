import pika
import json
from messaging.config import get_rabbitmq_connection

def send_user_created_message(user_id, lastname, firstname, email):
    """Send a message when a new user is created in the User API."""
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    # Declare the queue
    channel.queue_declare(queue="user_created")

    # Create the message data
    message = {
        "user_id": user_id,
        "firstname": firstname,
        "lastname": lastname,
        "email": email,
    }
    
    # Send the message
    channel.basic_publish(exchange="", routing_key="user_created", body=json.dumps(message))

    print(f"📨 Sent user_created message: {message}")
    channel.close()
    connection.close()


def send_book_borrowed(book_id, available, borrower_id, borrow_date, return_date):
    """Send a message when a book is borrowed."""
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    # Declare queue for book borrowed event
    channel.queue_declare(queue="book_borrowed")

    # Create message data
    message = {
        "book_id": book_id,
        "available": available,
        "borrower_id": borrower_id,
        "borrow_date": borrow_date,
        "return_date": return_date
    }
    
    channel.basic_publish(exchange="", routing_key="book_borrowed", body=json.dumps(message, default=str))

    print(f"📨 Sent borrowed book message: {message}")
    channel.close()
    connection.close()


def return_book_borrowed(book_id, available, borrower_id, borrow_date, return_date):
    """Send a message when a book is returned."""
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    # Declare queue for book return event
    channel.queue_declare(queue="book_returned")

    # Create message data
    message = {
        "book_id": book_id,
        "available": available,
        "borrower_id": borrower_id,
        "borrow_date": borrow_date,
        "return_date": return_date
    }
    
    channel.basic_publish(exchange="", routing_key="book_returned", body=json.dumps(message, default=str))

    print(f"📨 Sent returned book message: {message}")
    channel.close()
    connection.close()