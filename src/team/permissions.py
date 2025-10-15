"""
Permission system for role-based access control.
"""

from enum import Enum
from typing import List, Dict, Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..shared.database import get_db
from ..shared.models.auth import User, Role, OrganizationMember
from ..auth.auth import get_current_active_user_sync


class Permission(str, Enum):
    """System permissions for role-based access control."""
    
    # Bot permissions
    BOT_CREATE = "bot:create"
    BOT_READ = "bot:read"
    BOT_UPDATE = "bot:update"
    BOT_DELETE = "bot:delete"
    
    # Flow permissions
    FLOW_CREATE = "flow:create"
    FLOW_READ = "flow:read"
    FLOW_UPDATE = "flow:update"
    FLOW_DELETE = "flow:delete"
    
    # Analytics permissions
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"
    
    # Team permissions
    TEAM_VIEW = "team:view"
    TEAM_INVITE = "team:invite"
    TEAM_MANAGE = "team:manage"
    TEAM_REMOVE = "team:remove"
    
    # Organization permissions
    ORG_MANAGE = "org:manage"
    ORG_DELETE = "org:delete"
    
    # Contact permissions
    CONTACT_VIEW = "contact:view"
    CONTACT_MANAGE = "contact:manage"
    
    # Trigger permissions
    TRIGGER_CREATE = "trigger:create"
    TRIGGER_READ = "trigger:read"
    TRIGGER_UPDATE = "trigger:update"
    TRIGGER_DELETE = "trigger:delete"


# Predefined roles with their permissions
ROLES = {
    "admin": {
        "name": "Admin",
        "description": "Full access to all resources",
        "permissions": [p.value for p in Permission]
    },
    "member": {
        "name": "Member",
        "description": "Can create and manage bots",
        "permissions": [
            Permission.BOT_CREATE,
            Permission.BOT_READ,
            Permission.BOT_UPDATE,
            Permission.FLOW_CREATE,
            Permission.FLOW_READ,
            Permission.FLOW_UPDATE,
            Permission.ANALYTICS_VIEW,
            Permission.TEAM_VIEW,
            Permission.CONTACT_VIEW,
            Permission.CONTACT_MANAGE,
            Permission.TRIGGER_CREATE,
            Permission.TRIGGER_READ,
            Permission.TRIGGER_UPDATE,
            Permission.TRIGGER_DELETE
        ]
    },
    "viewer": {
        "name": "Viewer",
        "description": "Read-only access",
        "permissions": [
            Permission.BOT_READ,
            Permission.FLOW_READ,
            Permission.ANALYTICS_VIEW,
            Permission.TEAM_VIEW,
            Permission.CONTACT_VIEW,
            Permission.TRIGGER_READ
        ]
    }
}


async def has_permission(user: User, permission: Permission, db: Session) -> bool:
    """
    Check if user has specific permission.
    
    Args:
        user: User object
        permission: Permission to check
        db: Database session
        
    Returns:
        bool: True if user has permission, False otherwise
    """
    try:
        # Special case: Allow any authenticated user to create bots
        if permission == Permission.BOT_CREATE:
            return True
        
        # If user has no organization, they have no permissions
        if not user.organization_id:
            return False
        
        # If user has no role, they have no permissions
        if not user.current_role_id:
            return False
        
        # Get user's role
        result = db.execute(select(Role).where(Role.id == user.current_role_id))
        role = result.scalar_one_or_none()
        
        if not role:
            return False
        
        # Check if role has the permission
        role_permissions = role.permissions or []
        return permission.value in role_permissions
        
    except Exception:
        return False


def is_admin(user: User, db: Session) -> bool:
    """
    Check if user is admin.
    
    Args:
        user: Current authenticated user
        db: Database session
        
    Returns:
        bool: True if user is admin, False otherwise
    """
    if user.current_role_id:
        role = db.query(Role).filter(Role.id == user.current_role_id).first()
        return role and role.name == "admin"
    return False


def check_ownership_or_admin(record, current_user: User, db: Session, ownership_field: str = "created_by_id") -> bool:
    """
    Universal ownership check function.
    Checks if user owns the record or is an admin.
    
    Args:
        record: Database record to check ownership for
        current_user: Current authenticated user
        db: Database session
        ownership_field: Field name that contains the owner ID (default: "created_by_id")
        
    Returns:
        bool: True if user can access record, False otherwise
    """
    # Admin users can access all records
    if is_admin(current_user, db):
        return True
    
    # Check ownership
    if hasattr(record, ownership_field):
        owner_id = getattr(record, ownership_field)
        return owner_id == current_user.id
    
    return False


def check_bot_ownership_or_admin(record, current_user: User, db: Session) -> bool:
    """
    Check bot ownership with cascading logic.
    For records that don't have direct ownership but are related to bots.
    
    Args:
        record: Database record to check ownership for
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        bool: True if user can access record, False otherwise
    """
    # Admin users can access all records
    if is_admin(current_user, db):
        return True
    
    # Direct ownership check
    if hasattr(record, 'created_by_id'):
        return record.created_by_id == current_user.id
    
    # Bot-related ownership check
    if hasattr(record, 'bot_id'):
        from ..shared.models.bot_builder import Bot
        bot = db.query(Bot).filter(Bot.id == record.bot_id).first()
        if bot and bot.created_by_id == current_user.id:
            return True
    
    # User-specific records (notifications, preferences)
    if hasattr(record, 'user_id'):
        return record.user_id == current_user.id
    
    return False


async def is_org_admin(user: User, db: Session) -> bool:
    """
    Check if user is organization admin.
    
    Args:
        user: User object
        db: Database session
        
    Returns:
        bool: True if user is admin, False otherwise
    """
    try:
        if not user.organization_id or not user.current_role_id:
            return False
        
        # Get user's role
        result = db.execute(select(Role).where(Role.id == user.current_role_id))
        role = result.scalar_one_or_none()
        
        if not role:
            return False
        
        return role.name == "admin"
        
    except Exception:
        return False


async def is_org_owner(user: User, db: Session) -> bool:
    """
    Check if user is organization owner.
    
    Args:
        user: User object
        db: Database session
        
    Returns:
        bool: True if user is owner, False otherwise
    """
    try:
        if not user.organization_id:
            return False
        
        # Get organization
        from ..shared.models.auth import Organization
        result = db.execute(select(Organization).where(Organization.id == user.organization_id))
        org = result.scalar_one_or_none()
        
        if not org:
            return False
        
        return org.owner_id == user.id
        
    except Exception:
        return False


def require_permission(permission: Permission):
    """
    Decorator to require specific permission.
    
    Args:
        permission: Permission to require
        
    Returns:
        Dependency function for FastAPI
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user_sync),
        db: Session = Depends(get_db)
    ):
        # Check if user has permission
        if not await has_permission(current_user, permission, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value}"
            )
        return current_user
    
    return permission_checker


def require_org_admin():
    """
    Decorator to require organization admin role.
    
    Returns:
        Dependency function for FastAPI
    """
    async def org_admin_checker(
        current_user: User = Depends(get_current_active_user_sync),
        db: Session = Depends(get_db)
    ):
        if not await is_org_admin(current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization admin access required"
            )
        return current_user
    
    return org_admin_checker


def require_org_owner():
    """
    Decorator to require organization owner role.
    
    Returns:
        Dependency function for FastAPI
    """
    async def org_owner_checker(
        current_user: User = Depends(get_current_active_user_sync),
        db: Session = Depends(get_db)
    ):
        if not await is_org_owner(current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization owner access required"
            )
        return current_user
    
    return org_owner_checker


def require_org_member():
    """
    Decorator to require organization membership.
    
    Returns:
        Dependency function for FastAPI
    """
    async def org_member_checker(
        current_user: User = Depends(get_current_active_user_sync),
        db: Session = Depends(get_db)
    ):
        if not current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization membership required"
            )
        return current_user
    
    return org_member_checker


def get_user_permissions(user: User, db: Session) -> List[str]:
    """
    Get all permissions for a user.
    
    Args:
        user: User object
        db: Database session
        
    Returns:
        List of permission strings
    """
    try:
        if not user.organization_id or not user.current_role_id:
            return []
        
        # Get user's role
        result = db.execute(select(Role).where(Role.id == user.current_role_id))
        role = result.scalar_one_or_none()
        
        if not role:
            return []
        
        return role.permissions or []
        
    except Exception:
        return []


def check_permission_in_list(permissions: List[str], permission: Permission) -> bool:
    """
    Check if permission exists in permission list.
    
    Args:
        permissions: List of permission strings
        permission: Permission to check
        
    Returns:
        bool: True if permission exists, False otherwise
    """
    return permission.value in permissions


def get_role_permissions(role_name: str) -> List[str]:
    """
    Get permissions for a predefined role.
    
    Args:
        role_name: Name of the role
        
    Returns:
        List of permission strings
    """
    role_data = ROLES.get(role_name)
    if role_data:
        return role_data["permissions"]
    return []


def get_all_roles() -> Dict[str, Dict[str, Any]]:
    """
    Get all predefined roles.
    
    Returns:
        Dictionary of role definitions
    """
    return ROLES.copy()
