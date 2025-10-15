"""
CRUD operations for contact attributes.
"""

import json
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..shared.models.bot_builder import ContactAttribute, Contact
from ..shared.schemas.contact import ContactAttributeSchema

logger = logging.getLogger(__name__)


def _convert_value_by_type(value: str, value_type: str) -> Any:
    """Convert string value to appropriate type based on value_type."""
    try:
        if value_type == "string":
            return value
        elif value_type == "number":
            # Try int first, then float
            try:
                return int(value)
            except ValueError:
                return float(value)
        elif value_type == "boolean":
            return value.lower() in ("true", "1", "yes", "on")
        elif value_type == "json":
            return json.loads(value)
        else:
            logger.warning(f"Unknown value_type '{value_type}', treating as string")
            return value
    except (ValueError, json.JSONDecodeError) as e:
        logger.error(f"Failed to convert value '{value}' to type '{value_type}': {e}")
        return value  # Return as string if conversion fails


def _convert_value_to_string(value: Any, value_type: str) -> str:
    """Convert value to string for storage."""
    try:
        if value_type == "json":
            return json.dumps(value)
        else:
            return str(value)
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to convert value to string: {e}")
        return str(value)


def set_contact_attribute(
    db: Session, 
    contact_id: int, 
    key: str, 
    value: str, 
    value_type: str = "string"
) -> ContactAttribute:
    """Set or update a contact attribute."""
    # Convert value to appropriate type for validation
    converted_value = _convert_value_by_type(value, value_type)
    string_value = _convert_value_to_string(converted_value, value_type)
    
    # Check if attribute already exists
    existing_attr = db.query(ContactAttribute).filter(
        and_(ContactAttribute.contact_id == contact_id, ContactAttribute.key == key)
    ).first()
    
    if existing_attr:
        # Update existing attribute
        existing_attr.value = string_value
        existing_attr.value_type = value_type
        db.commit()
        db.refresh(existing_attr)
        logger.info(f"Updated attribute '{key}' for contact {contact_id}")
        return existing_attr
    else:
        # Create new attribute
        new_attr = ContactAttribute(
            contact_id=contact_id,
            key=key,
            value=string_value,
            value_type=value_type
        )
        db.add(new_attr)
        db.commit()
        db.refresh(new_attr)
        logger.info(f"Created attribute '{key}' for contact {contact_id}")
        return new_attr


def get_contact_attribute(db: Session, contact_id: int, key: str) -> Optional[ContactAttribute]:
    """Get a single contact attribute."""
    attr = db.query(ContactAttribute).filter(
        and_(ContactAttribute.contact_id == contact_id, ContactAttribute.key == key)
    ).first()
    
    if attr:
        # Convert value back to appropriate type
        attr.converted_value = _convert_value_by_type(attr.value, attr.value_type)
    
    return attr


def get_all_contact_attributes(db: Session, contact_id: int) -> List[ContactAttribute]:
    """Get all attributes for a contact."""
    attributes = db.query(ContactAttribute).filter(
        ContactAttribute.contact_id == contact_id
    ).all()
    
    # Convert values back to appropriate types
    for attr in attributes:
        attr.converted_value = _convert_value_by_type(attr.value, attr.value_type)
    
    return attributes


def get_contact_attributes_dict(db: Session, contact_id: int) -> Dict[str, Any]:
    """Get all contact attributes as a dictionary."""
    attributes = get_all_contact_attributes(db, contact_id)
    return {attr.key: _convert_value_by_type(attr.value, attr.value_type) for attr in attributes}


def delete_contact_attribute(db: Session, contact_id: int, key: str) -> bool:
    """Delete a contact attribute."""
    attr = db.query(ContactAttribute).filter(
        and_(ContactAttribute.contact_id == contact_id, ContactAttribute.key == key)
    ).first()
    
    if attr:
        db.delete(attr)
        db.commit()
        logger.info(f"Deleted attribute '{key}' for contact {contact_id}")
        return True
    else:
        logger.warning(f"Attribute '{key}' not found for contact {contact_id}")
        return False


def bulk_set_contact_attributes(
    db: Session, 
    contact_id: int, 
    attributes: List[Dict[str, Any]]
) -> List[ContactAttribute]:
    """Set multiple contact attributes at once."""
    results = []
    
    for attr_data in attributes:
        key = attr_data.get("key")
        value = attr_data.get("value")
        value_type = attr_data.get("value_type", "string")
        
        if not key or value is None:
            logger.warning(f"Skipping invalid attribute data: {attr_data}")
            continue
            
        attr = set_contact_attribute(db, contact_id, key, str(value), value_type)
        results.append(attr)
    
    logger.info(f"Bulk set {len(results)} attributes for contact {contact_id}")
    return results


def search_contacts_by_attribute(
    db: Session, 
    key: str, 
    value: str, 
    value_type: str = "string"
) -> List[Contact]:
    """Find contacts by attribute value."""
    # Convert search value to string for database comparison
    search_value = _convert_value_to_string(value, value_type)
    
    # Query contacts that have the specified attribute with the given value
    contacts = db.query(Contact).join(ContactAttribute).filter(
        and_(
            ContactAttribute.key == key,
            ContactAttribute.value == search_value,
            ContactAttribute.value_type == value_type
        )
    ).all()
    
    logger.info(f"Found {len(contacts)} contacts with attribute '{key}' = '{value}'")
    return contacts


def get_contact_by_id(db: Session, contact_id: int) -> Optional[Contact]:
    """Get contact by ID."""
    return db.query(Contact).filter(Contact.id == contact_id).first()


def create_contact_attribute_schema(attr: ContactAttribute) -> ContactAttributeSchema:
    """Convert ContactAttribute model to schema."""
    return ContactAttributeSchema(
        id=attr.id,
        contact_id=attr.contact_id,
        key=attr.key,
        value=attr.value,
        value_type=attr.value_type,
        created_at=attr.created_at,
        updated_at=attr.updated_at
    )
