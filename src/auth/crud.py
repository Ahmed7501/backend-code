"""
CRUD (Create, Read, Update, Delete) operations for database interactions.
Contains async functions for user-related database operations.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..shared.models.auth import User
from ..shared.schemas.auth import UserCreate
from .auth import get_password_hash


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get a user by their email address.
    
    Args:
        db: Database session
        email: User's email address
        
    Returns:
        Optional[User]: User object if found, None otherwise
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """
    Get a user by their username.
    
    Args:
        db: Database session
        username: User's username
        
    Returns:
        Optional[User]: User object if found, None otherwise
    """
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Get a user by their ID.
    
    Args:
        db: Database session
        user_id: User's ID
        
    Returns:
        Optional[User]: User object if found, None otherwise
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """
    Create a new user in the database.
    
    Args:
        db: Database session
        user: User creation data
        
    Returns:
        User: The created user object
        
    Raises:
        ValueError: If email or username already exists
    """
    # Check if user with email already exists
    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        raise ValueError("Email already registered")
    
    # Check if user with username already exists
    existing_user = await get_user_by_username(db, user.username)
    if existing_user:
        raise ValueError("Username already taken")
    
    # Hash the password
    hashed_password = get_password_hash(user.password)
    
    # Create new user
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    
    try:
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except IntegrityError as e:
        await db.rollback()
        raise ValueError("User creation failed due to database constraint violation")


async def update_user(db: AsyncSession, user_id: int, user_update: dict) -> Optional[User]:
    """
    Update a user's information.
    
    Args:
        db: Database session
        user_id: ID of the user to update
        user_update: Dictionary containing fields to update
        
    Returns:
        Optional[User]: Updated user object if found, None otherwise
    """
    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()
    
    if not db_user:
        return None
    
    # Update fields
    for field, value in user_update.items():
        if hasattr(db_user, field):
            setattr(db_user, field, value)
    
    try:
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except IntegrityError:
        await db.rollback()
        raise ValueError("User update failed due to database constraint violation")


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """
    Delete a user from the database.
    
    Args:
        db: Database session
        user_id: ID of the user to delete
        
    Returns:
        bool: True if user was deleted, False if user not found
    """
    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()
    
    if not db_user:
        return False
    
    await db.delete(db_user)
    await db.commit()
    return True


async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[User]:
    """
    Get a list of all users with pagination.
    
    Args:
        db: Database session
        skip: Number of users to skip
        limit: Maximum number of users to return
        
    Returns:
        list[User]: List of user objects
    """
    result = await db.execute(
        select(User)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()
