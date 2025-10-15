
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..shared.models.auth import User
from ..shared.schemas.auth import TokenData
from ..shared.database import get_async_session, get_db

# Configuration
SECRET_KEY = "your-secret-key-change-this-in-production"  # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer scheme for JWT token authentication
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password to verify against
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        str: The hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        str: The encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Add organization context if available
    if "user" in data:
        user = data["user"]
        to_encode.update({
            "org_id": user.organization_id,
            "role": user.current_role.name if user.current_role else None
        })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def authenticate_user(email: str, password: str, db: AsyncSession) -> Optional[User]:
    """
    Authenticate a user by email and password.
    
    Args:
        email: User's email address
        password: User's plain text password
        db: Database session
        
    Returns:
        Optional[User]: User object if authentication successful, None otherwise
    """
    # Get user by email
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    Get the current authenticated user from JWT token.
    This is a FastAPI dependency that can be used to protect routes.
    
    Args:
        credentials: HTTPAuthorizationCredentials containing the Bearer token
        db: Database session
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from credentials
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    result = await db.execute(select(User).where(User.email == token_data.email))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user.
    This dependency ensures the user is not only authenticated but also active.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        User: The active authenticated user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


# Sync versions for routes that use sync database sessions
def get_current_user_sync(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token (sync version).
    This is a FastAPI dependency for routes that use sync database sessions.
    
    Args:
        credentials: HTTPAuthorizationCredentials containing the Bearer token
        db: Sync database session
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from credentials
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    # Get user from database (sync version)
    user = db.query(User).filter(User.email == token_data.email).first()
    
    if user is None:
        raise credentials_exception
    
    return user


def get_current_active_user_sync(current_user: User = Depends(get_current_user_sync)) -> User:
    """
    Get the current active user (sync version).
    This dependency ensures the user is not only authenticated but also active.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        User: The active authenticated user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user
