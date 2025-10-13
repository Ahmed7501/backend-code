"""
Pydantic models for data validation and serialization.
These models define the structure of request/response data for the API.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., min_length=3, max_length=100, description="User's username")


class UserCreate(UserBase):
    """
    Schema for user registration.
    
    Attributes:
        email: User's email address (must be valid email format)
        username: User's username (3-100 characters)
        password: User's password (minimum 8 characters)
    """
    password: str = Field(..., min_length=8, description="User's password (minimum 8 characters)")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "securepassword123"
            }
        }


class User(UserBase):
    """
    Schema for user response data (without sensitive information).
    
    Attributes:
        id: User's unique identifier
        email: User's email address
        username: User's username
        is_active: Whether the user account is active
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
    """
    id: int = Field(..., description="User's unique identifier")
    is_active: bool = Field(..., description="Whether the user account is active")
    created_at: datetime = Field(..., description="Timestamp when user was created")
    updated_at: datetime = Field(..., description="Timestamp when user was last updated")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "username": "johndoe",
                "is_active": True,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            }
        }


class Token(BaseModel):
    """
    Schema for JWT token response.
    
    Attributes:
        access_token: JWT access token
        token_type: Type of token (typically "bearer")
    """
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Type of token")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class TokenData(BaseModel):
    """
    Schema for JWT token payload data.
    
    Attributes:
        email: User's email from the token payload
    """
    email: Optional[str] = None


class UserLogin(BaseModel):
    """
    Schema for user login request.
    
    Attributes:
        email: User's email address
        password: User's password
    """
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }
