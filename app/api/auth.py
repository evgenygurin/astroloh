"""
Authentication API endpoints for the frontend.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db_session
from app.core.config import settings
from app.models.database import User
from app.utils.validators import PasswordValidator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Security settings
SECRET_KEY = settings.SECRET_KEY if hasattr(settings, "SECRET_KEY") else "dev-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# Pydantic models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password meets security requirements."""
        return PasswordValidator.validate_password(v)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    zodiac_sign: Optional[str] = None
    created_at: datetime


class UserInDB(BaseModel):
    id: str
    email: str
    hashed_password: str
    name: str


# Extend User model with email and password
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    return user


@router.post("/register", response_model=Token)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db_session)
):
    """Register a new user."""
    # Check if user already exists (by email in yandex_user_id field)
    result = await db.execute(
        select(User).where(User.yandex_user_id == user_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    # Store email in yandex_user_id field and hashed password in encrypted_name field
    user = User(
        yandex_user_id=user_data.email,  # Using yandex_user_id to store email
        encrypted_name=get_password_hash(user_data.password).encode(),  # Store hashed password
        preferences={"name": user_data.name, "email": user_data.email},  # Store actual name in preferences
        data_consent=True,
        created_at=datetime.utcnow()
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"New user registered: {user_data.email}")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session)
):
    """Login user and return access token."""
    # Find user by email
    result = await db.execute(
        select(User).where(User.yandex_user_id == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.encrypted_name:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password (stored in encrypted_name field)
    if not verify_password(form_data.password, user.encrypted_name.decode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last accessed
    user.last_accessed = datetime.utcnow()
    await db.commit()
    
    logger.info(f"User logged in: {form_data.username}")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    # Extract name from preferences
    name = current_user.preferences.get("name", "Unknown") if current_user.preferences else "Unknown"
    email = current_user.preferences.get("email", current_user.yandex_user_id) if current_user.preferences else current_user.yandex_user_id
    
    return UserResponse(
        id=str(current_user.id),
        email=email,
        name=name,
        zodiac_sign=current_user.zodiac_sign,
        created_at=current_user.created_at
    )