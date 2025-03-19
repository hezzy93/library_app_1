import sys
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Base, get_db
from main import app
import schema

SQLALCHEMY_DATABASE_URL = "sqlite:///"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_book(client, setup_database):
    book_data = {"title": "Test Book", "publisher": "Test Publisher", "category": "Fiction", "available": True}
    response = client.post("/books/", json=book_data)
    assert response.status_code == 200
    assert response.json()["message"] == "Book added successfully"

def test_get_books(client, setup_database):
    books = [
        {"title": "Book One", "publisher": "Pub A", "category": "Fiction", "available": True},
        {"title": "Book Two", "publisher": "Pub B", "category": "Science", "available": False},
    ]
    for book in books:
        client.post("/books/", json=book)
    
    response = client.get("/books/")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_get_book_by_id(client, setup_database):
    book_data = {"title": "Test Book", "publisher": "Test Publisher", "category": "Fiction", "available": True}
    client.post("/books/", json=book_data)
    response = client.get("/books/1/")
    assert response.status_code == 200
    assert response.json()["title"] == "Test Book"

def test_get_books_by_category(client, setup_database):
    client.post("/books/", json={"title": "Book A", "publisher": "Pub A", "category": "Fiction", "available": True})
    response = client.get("/books/category/Fiction/")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_get_books_by_publisher(client, setup_database):
    client.post("/books/", json={"title": "Book A", "publisher": "Pub A", "category": "Fiction", "available": True})
    response = client.get("/books/publisher/Pub A/")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_update_book(client, setup_database):
    client.post("/books/", json={"title": "Book A", "publisher": "Pub A", "category": "Fiction", "available": True})
    update_data = {"title": "Updated Book A", "publisher": "Updated Pub", "category": "Science", "available": False}
    response = client.put("/books/1", json=update_data)
    assert response.status_code == 200
    assert response.json()["message"] == "success"

def test_delete_book(client, setup_database):
    client.post("/books/", json={"title": "Book A", "publisher": "Pub A", "category": "Fiction", "available": True})
    response = client.delete("/books/1/delete")
    assert response.status_code == 200

def test_get_users(client, setup_database):
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_delete_user(client, setup_database):
    response = client.delete("/users/1/delete")
    assert response.status_code in [200, 404]  # It may return 404 if user doesn't exist

def test_get_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "Welcome to the Admin end of the Library API"}
