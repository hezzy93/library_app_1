
from sqlalchemy.orm import Session
from datetime import timedelta
import bcrypt
from models import User
from datetime import datetime, timedelta
from jose import JWTError, jwt
from schema import TokenData
from pydantic_settings import BaseSettings




class Settings(BaseSettings):
    SECRET_KEY: str  # Ensure this is set in the .env file
    ALGORITHM: str = "HS256"  # Set a default algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Default expiration time if not set

# Initialize settings
settings = Settings()



#Hash Password
def hash_password(password: str) -> str:
    # Hash a password
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

#verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Ensure hashed_password is not None before verification
    if not hashed_password:
        return False
    # Verify a hashed password
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

#Authenticate for login
def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None




# Create Access Token
def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=30)):
    to_encode = data.copy()

    if "id" not in to_encode or to_encode["id"] is None:
        raise ValueError("User ID must be provided when generating the token")  

    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt  # Ensure token is returned


# Verify Token
def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print(f"Decoded Token: {payload}")  # Debugging

        user_email: str = payload.get("sub")
        user_id: str = payload.get("id")  # Extract ID

        if user_email is None or user_id is None:
            raise credentials_exception

        return TokenData(email=user_email, id=user_id)  # Ensure ID is returned
    except JWTError:
        raise credentials_exception

