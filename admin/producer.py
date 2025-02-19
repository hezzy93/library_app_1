import pika
import json
from messaging.config import get_rabbitmq_connection


def send_book_created(book_id, title, publisher, category, available):
    """Send a message when a new book is created."""
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    
    # Declare queue for book messages
    channel.queue_declare(queue="book_created")

    # Create message data
    message = {"book_id": book_id, "title": title, "publisher": publisher, "category": category, "available": available}
    channel.basic_publish(exchange="", routing_key="book_created", body=json.dumps(message))

    print(f"📨 Sent book_created message: {message}")
    connection.close()

def send_book_deleted(book_id):
    """Send a message when a book is deleted."""
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    # Declare queue for book deleted event
    channel.queue_declare(queue="book_deleted")

    # Create delete message
    message = {"book_id": book_id}

    channel.basic_publish(exchange="", routing_key="book_deleted", body=json.dumps(message))

    print(f"📨 Sent book deleted message: {message}")
    connection.close()
