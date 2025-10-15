"""
Pydantic schemas for contact attribute management.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ContactAttributeSchema(BaseModel):
    """Schema for a single contact attribute."""
    id: Optional[int] = None
    contact_id: int
    key: str
    value: str
    value_type: str = Field(default="string", description="Type: string, number, boolean, json")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
       from_attributes = True


class SetAttributeRequest(BaseModel):
    """Request schema for setting a single attribute."""
    key: str = Field(..., description="Attribute key name")
    value: str = Field(..., description="Attribute value")
    value_type: str = Field(default="string", description="Value type: string, number, boolean, json")


class GetAttributeResponse(BaseModel):
    """Response schema for getting a single attribute."""
    key: str
    value: Any
    value_type: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class ContactAttributesResponse(BaseModel):
    """Response schema for getting all contact attributes."""
    contact_id: int
    attributes: Dict[str, Any]
    total_count: int


class BulkSetAttributesRequest(BaseModel):
    """Request schema for setting multiple attributes at once."""
    attributes: List[SetAttributeRequest] = Field(..., description="List of attributes to set")


class DeleteAttributeRequest(BaseModel):
    """Request schema for deleting an attribute."""
    key: str = Field(..., description="Attribute key to delete")


class SearchContactsByAttributeRequest(BaseModel):
    """Request schema for searching contacts by attribute."""
    key: str = Field(..., description="Attribute key to search by")
    value: str = Field(..., description="Attribute value to search for")
    value_type: Optional[str] = Field(default="string", description="Value type for comparison")


class SearchContactsByAttributeResponse(BaseModel):
    """Response schema for contact search results."""
    contacts: List[Dict[str, Any]]
    total_count: int
    search_key: str
    search_value: str
