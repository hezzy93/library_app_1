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

SQLALCHEMY_DATABASE_URL = "sqlite:///"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
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

def test_enroll_user(client, setup_database):
    user_data = {"firstname": "John", "lastname": "Doe", "email": "johndoe@example.com"}
    response = client.post("/users/enroll/", json=user_data)
    assert response.status_code == 201
    assert "id" in response.json()

def test_borrow_book(client, setup_database):
    user_data = {"firstname": "Jane", "lastname": "Doe", "email": "janedoe@example.com"}
    client.post("/users/enroll/", json=user_data)
    
    book_data = {"title": "Test Book", "publisher": "Test Publisher", "category": "Fiction", "available": True}
    book_response = client.post("/books/", json=book_data)
    assert book_response.status_code == 201
    book_id = book_response.json()["id"]
    
    borrow_request = {"borrow_duration": 7}
    response = client.post(f"/books/borrow/{book_id}?email=janedoe@example.com", json=borrow_request)
    assert response.status_code == 200
    assert response.json()["message"] == "Book borrowed successfully"

def test_return_book(client, setup_database):
    user_data = {"firstname": "Jane", "lastname": "Doe", "email": "janedoe@example.com"}
    client.post("/users/enroll/", json=user_data)
    
    book_data = {"title": "Test Book", "publisher": "Test Publisher", "category": "Fiction", "available": True}
    book_response = client.post("/books/", json=book_data)
    assert book_response.status_code == 201
    book_id = book_response.json()["id"]
    
    borrow_request = {"borrow_duration": 7}
    client.post(f"/books/borrow/{book_id}?email=janedoe@example.com", json=borrow_request)
    
    return_response = client.post(f"/books/return/{book_id}?email=janedoe@example.com")
    assert return_response.status_code == 200
    assert return_response.json()["message"] == "Book returned successfully"

def test_get_books(client, setup_database):
    response = client.get("/books/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_book_by_id(client, setup_database):
    book_data = {"title": "Test Book", "publisher": "Test Publisher", "category": "Fiction", "available": True}
    book_response = client.post("/books/", json=book_data)
    assert book_response.status_code == 201
    book_id = book_response.json()["id"]
    
    response = client.get(f"/books/{book_id}/")
    assert response.status_code == 200
    assert response.json()["title"] == "Test Book"

def test_get_books_by_category(client, setup_database):
    client.post("/books/", json={"title": "Book A", "publisher": "Pub A", "category": "Fiction", "available": True})
    response = client.get("/books/category/Fiction/")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_get_books_by_publisher(client, setup_database):
    client.post("/books/", json={"title": "Book A", "publisher": "Pub A", "category": "Fiction", "available": True})
    response = client.get("/books/publisher/{publisher}/")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_get_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "Welcome to the User end of the Library API"}