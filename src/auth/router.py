"""
Authentication router for user registration and login endpoints.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ..shared.database import get_async_session, init_db
from ..shared.models.auth import User
from ..shared.schemas.auth import UserCreate, User as UserSchema, Token
from .crud import create_user, get_all_users
from .auth import authenticate_user, get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Register a new user.
    
    Args:
        user: User registration data
        db: Database session
        
    Returns:
        UserSchema: Created user data (without password)
        
    Raises:
        HTTPException: If email or username already exists
    """
    try:
        db_user = await create_user(db=db, user=user)
        return db_user
    except ValueError as e:
        if "Email already registered" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        elif "Username already taken" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Login and get access token.
    
    Args:
        form_data: OAuth2 password request form (username=email, password)
        db: Database session
        
    Returns:
        Token: JWT access token
        
    Raises:
        HTTPException: If authentication fails
    """
    # Authenticate user (form_data.username is actually the email)
    user = await authenticate_user(form_data.username, form_data.password, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user (from dependency)
        
    Returns:
        UserSchema: Current user data
    """
    return current_user


@router.get("/users", response_model=list[UserSchema])
async def get_all_users_endpoint(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all users (protected endpoint).
    
    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        list[UserSchema]: List of users
    """
    users = await get_all_users(db=db, skip=skip, limit=limit)
    return users
