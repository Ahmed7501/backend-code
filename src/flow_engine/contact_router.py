"""
API router for contact attributes management.
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..shared.database import get_db
from ..shared.models.auth import User
from ..shared.schemas.contact import (
    SetAttributeRequest,
    GetAttributeResponse,
    ContactAttributesResponse,
    BulkSetAttributesRequest,
    DeleteAttributeRequest,
    SearchContactsByAttributeRequest,
    SearchContactsByAttributeResponse
)
from ..shared.schemas.flow_engine import ContactResponse
from ..auth.auth import get_current_active_user_sync
from ..team.permissions import require_permission, Permission
from .contact_crud import (
    set_contact_attribute,
    get_contact_attribute,
    get_all_contact_attributes,
    delete_contact_attribute,
    bulk_set_contact_attributes,
    search_contacts_by_attribute,
    get_contact_by_id,
    get_contact_attributes_dict
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contacts", tags=["Contact Attributes"])


@router.post("/{contact_id}/attributes", response_model=GetAttributeResponse)
async def set_contact_attribute_endpoint(
    contact_id: int,
    request: SetAttributeRequest,
    current_user: User = Depends(require_permission(Permission.CONTACT_MANAGE)),
    db: Session = Depends(get_db)
):
    """Set a single contact attribute."""
    # Check if contact exists
    contact = get_contact_by_id(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    try:
        attr = set_contact_attribute(
            db, 
            contact_id, 
            request.key, 
            request.value, 
            request.value_type
        )
        
        return GetAttributeResponse(
            key=attr.key,
            value=attr.value,
            value_type=attr.value_type,
            created_at=attr.created_at,
            updated_at=attr.updated_at
        )
    except Exception as e:
        logger.error(f"Failed to set attribute for contact {contact_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{contact_id}/attributes/bulk", response_model=List[GetAttributeResponse])
async def bulk_set_contact_attributes_endpoint(
    contact_id: int,
    request: BulkSetAttributesRequest,
    current_user: User = Depends(require_permission(Permission.CONTACT_MANAGE)),
    db: Session = Depends(get_db)
):
    """Set multiple contact attributes at once."""
    # Check if contact exists
    contact = get_contact_by_id(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    try:
        attributes_data = [attr.dict() for attr in request.attributes]
        attrs = bulk_set_contact_attributes(db, contact_id, attributes_data)
        
        return [
            GetAttributeResponse(
                key=attr.key,
                value=attr.value,
                value_type=attr.value_type,
                created_at=attr.created_at,
                updated_at=attr.updated_at
            )
            for attr in attrs
        ]
    except Exception as e:
        logger.error(f"Failed to bulk set attributes for contact {contact_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{contact_id}/attributes", response_model=ContactAttributesResponse)
async def get_contact_attributes_endpoint(
    contact_id: int,
    db: Session = Depends(get_db)
):
    """Get all attributes for a contact."""
    # Check if contact exists
    contact = get_contact_by_id(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    try:
        attributes_dict = get_contact_attributes_dict(db, contact_id)
        return ContactAttributesResponse(
            contact_id=contact_id,
            attributes=attributes_dict,
            total_count=len(attributes_dict)
        )
    except Exception as e:
        logger.error(f"Failed to get attributes for contact {contact_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{contact_id}/attributes/{key}", response_model=GetAttributeResponse)
async def get_contact_attribute_endpoint(
    contact_id: int,
    key: str,
    db: Session = Depends(get_db)
):
    """Get a single contact attribute."""
    # Check if contact exists
    contact = get_contact_by_id(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    attr = get_contact_attribute(db, contact_id, key)
    if not attr:
        raise HTTPException(status_code=404, detail=f"Attribute '{key}' not found")
    
    return GetAttributeResponse(
        key=attr.key,
        value=attr.value,
        value_type=attr.value_type,
        created_at=attr.created_at,
        updated_at=attr.updated_at
    )


@router.delete("/{contact_id}/attributes/{key}")
async def delete_contact_attribute_endpoint(
    contact_id: int,
    key: str,
    db: Session = Depends(get_db)
):
    """Delete a contact attribute."""
    # Check if contact exists
    contact = get_contact_by_id(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    success = delete_contact_attribute(db, contact_id, key)
    if not success:
        raise HTTPException(status_code=404, detail=f"Attribute '{key}' not found")
    
    return {"message": f"Attribute '{key}' deleted successfully"}


@router.get("/search/by-attribute", response_model=SearchContactsByAttributeResponse)
async def search_contacts_by_attribute_endpoint(
    key: str = Query(..., description="Attribute key to search by"),
    value: str = Query(..., description="Attribute value to search for"),
    value_type: str = Query(default="string", description="Value type for comparison"),
    db: Session = Depends(get_db)
):
    """Search contacts by attribute value."""
    try:
        contacts = search_contacts_by_attribute(db, key, value, value_type)
        
        # Convert contacts to response format
        contact_list = []
        for contact in contacts:
            contact_dict = {
                "id": contact.id,
                "phone_number": contact.phone_number,
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "meta_data": contact.meta_data,
                "created_at": contact.created_at,
                "updated_at": contact.updated_at
            }
            contact_list.append(contact_dict)
        
        return SearchContactsByAttributeResponse(
            contacts=contact_list,
            total_count=len(contact_list),
            search_key=key,
            search_value=value
        )
    except Exception as e:
        logger.error(f"Failed to search contacts by attribute: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact_with_attributes_endpoint(
    contact_id: int,
    include_attributes: bool = Query(default=False, description="Include contact attributes"),
    db: Session = Depends(get_db)
):
    """Get contact with optional attributes."""
    contact = get_contact_by_id(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    response_data = {
        "id": contact.id,
        "phone_number": contact.phone_number,
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "meta_data": contact.meta_data,
        "created_at": contact.created_at,
        "updated_at": contact.updated_at
    }
    
    if include_attributes:
        try:
            attributes_dict = get_contact_attributes_dict(db, contact_id)
            response_data["attributes"] = attributes_dict
        except Exception as e:
            logger.error(f"Failed to get attributes for contact {contact_id}: {e}")
            response_data["attributes"] = {}
    
    return ContactResponse(**response_data)
