
import pika
import os

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")

def get_rabbitmq_connection():
    """Establish RabbitMQ connection."""
    return pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
