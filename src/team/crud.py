"""
CRUD operations for team management and organization features.
"""

import logging
import secrets
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from ..shared.models.auth import (
    Organization, 
    Role, 
    OrganizationMember, 
    Invitation, 
    User
)
from ..shared.schemas.team import (
    OrganizationCreate,
    OrganizationUpdate,
    RoleCreate,
    MemberAddRequest,
    MemberRoleUpdate,
    InvitationCreate
)
from .permissions import ROLES

logger = logging.getLogger(__name__)


async def create_organization(db: Session, name: str, description: Optional[str], owner_id: int) -> Organization:
    """Create a new organization."""
    try:
        # Check if organization name already exists
        existing_org = db.execute(select(Organization).where(Organization.name == name)).scalar_one_or_none()
        if existing_org:
            raise ValueError("Organization name already exists")
        
        # Create organization
        organization = Organization(
            name=name,
            description=description,
            owner_id=owner_id
        )
        
        db.add(organization)
        db.commit()
        db.refresh(organization)
        
        # Add owner as admin member
        admin_role = db.execute(select(Role).where(Role.name == "admin")).scalar_one_or_none()
        if admin_role:
            member = OrganizationMember(
                organization_id=organization.id,
                user_id=owner_id,
                role_id=admin_role.id
            )
            db.add(member)
            
            # Update user's organization and role
            user = db.execute(select(User).where(User.id == owner_id)).scalar_one_or_none()
            if user:
                user.organization_id = organization.id
                user.current_role_id = admin_role.id
            
            db.commit()
        
        logger.info(f"Created organization '{name}' with owner {owner_id}")
        return organization
        
    except Exception as e:
        logger.error(f"Failed to create organization: {e}")
        db.rollback()
        raise


async def get_organization(db: Session, org_id: int) -> Optional[Organization]:
    """Get organization by ID."""
    try:
        result = db.execute(select(Organization).where(Organization.id == org_id))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Failed to get organization {org_id}: {e}")
        return None


async def update_organization(db: Session, org_id: int, updates: OrganizationUpdate) -> Optional[Organization]:
    """Update organization."""
    try:
        organization = await get_organization(db, org_id)
        if not organization:
            return None
        
        # Update fields
        if updates.name is not None:
            organization.name = updates.name
        if updates.description is not None:
            organization.description = updates.description
        if updates.is_active is not None:
            organization.is_active = updates.is_active
        
        db.commit()
        db.refresh(organization)
        
        logger.info(f"Updated organization {org_id}")
        return organization
        
    except Exception as e:
        logger.error(f"Failed to update organization {org_id}: {e}")
        db.rollback()
        return None


async def delete_organization(db: Session, org_id: int) -> bool:
    """Delete organization."""
    try:
        organization = await get_organization(db, org_id)
        if not organization:
            return False
        
        db.delete(organization)
        db.commit()
        
        logger.info(f"Deleted organization {org_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete organization {org_id}: {e}")
        db.rollback()
        return False


async def add_member_to_organization(db: Session, org_id: int, user_id: int, role_name: str) -> Optional[OrganizationMember]:
    """Add member to organization."""
    try:
        # Check if user is already a member
        existing_member = db.execute(
            select(OrganizationMember).where(
                and_(
                    OrganizationMember.organization_id == org_id,
                    OrganizationMember.user_id == user_id
                )
            )
        ).scalar_one_or_none()
        
        if existing_member:
            raise ValueError("User is already a member of this organization")
        
        # Get role
        role = db.execute(select(Role).where(Role.name == role_name)).scalar_one_or_none()
        if not role:
            raise ValueError(f"Role '{role_name}' not found")
        
        # Create member
        member = OrganizationMember(
            organization_id=org_id,
            user_id=user_id,
            role_id=role.id
        )
        
        db.add(member)
        
        # Update user's organization and role if they don't have one
        user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if user and not user.organization_id:
            user.organization_id = org_id
            user.current_role_id = role.id
        
        db.commit()
        db.refresh(member)
        
        logger.info(f"Added user {user_id} to organization {org_id} as {role_name}")
        return member
        
    except Exception as e:
        logger.error(f"Failed to add member to organization: {e}")
        db.rollback()
        raise


async def remove_member_from_organization(db: Session, org_id: int, user_id: int) -> bool:
    """Remove member from organization."""
    try:
        member = db.execute(
            select(OrganizationMember).where(
                and_(
                    OrganizationMember.organization_id == org_id,
                    OrganizationMember.user_id == user_id
                )
            )
        ).scalar_one_or_none()
        
        if not member:
            return False
        
        db.delete(member)
        
        # Update user's organization and role
        user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if user and user.organization_id == org_id:
            user.organization_id = None
            user.current_role_id = None
        
        db.commit()
        
        logger.info(f"Removed user {user_id} from organization {org_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to remove member from organization: {e}")
        db.rollback()
        return False


async def update_member_role(db: Session, org_id: int, user_id: int, role_name: str) -> Optional[OrganizationMember]:
    """Update member role."""
    try:
        member = db.execute(
            select(OrganizationMember).where(
                and_(
                    OrganizationMember.organization_id == org_id,
                    OrganizationMember.user_id == user_id
                )
            )
        ).scalar_one_or_none()
        
        if not member:
            return None
        
        # Get new role
        role = db.execute(select(Role).where(Role.name == role_name)).scalar_one_or_none()
        if not role:
            raise ValueError(f"Role '{role_name}' not found")
        
        # Update member role
        member.role_id = role.id
        
        # Update user's current role
        user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if user:
            user.current_role_id = role.id
        
        db.commit()
        db.refresh(member)
        
        logger.info(f"Updated user {user_id} role to {role_name} in organization {org_id}")
        return member
        
    except Exception as e:
        logger.error(f"Failed to update member role: {e}")
        db.rollback()
        raise


async def get_organization_members(db: Session, org_id: int) -> List[Dict[str, Any]]:
    """Get all organization members."""
    try:
        members = db.execute(
            select(OrganizationMember, User, Role)
            .join(User, OrganizationMember.user_id == User.id)
            .join(Role, OrganizationMember.role_id == Role.id)
            .where(OrganizationMember.organization_id == org_id)
        ).all()
        
        return [
            {
                "id": member.id,
                "user_id": member.user_id,
                "user_email": user.email,
                "user_name": user.username,
                "role_name": role.name,
                "is_active": member.is_active,
                "joined_at": member.joined_at
            }
            for member, user, role in members
        ]
        
    except Exception as e:
        logger.error(f"Failed to get organization members: {e}")
        return []


async def create_invitation(db: Session, org_id: int, email: str, role_name: str, invited_by_id: int) -> Invitation:
    """Create invitation."""
    try:
        # Check if user already exists
        existing_user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if existing_user and existing_user.organization_id == org_id:
            raise ValueError("User is already a member of this organization")
        
        # Check if invitation already exists
        existing_invitation = db.execute(
            select(Invitation).where(
                and_(
                    Invitation.organization_id == org_id,
                    Invitation.email == email,
                    Invitation.status == "pending"
                )
            )
        ).scalar_one_or_none()
        
        if existing_invitation:
            raise ValueError("Invitation already exists for this email")
        
        # Get role
        role = db.execute(select(Role).where(Role.name == role_name)).scalar_one_or_none()
        if not role:
            raise ValueError(f"Role '{role_name}' not found")
        
        # Generate token and expiration
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        # Create invitation
        invitation = Invitation(
            organization_id=org_id,
            email=email,
            role_id=role.id,
            token=token,
            invited_by_id=invited_by_id,
            status="pending",
            expires_at=expires_at
        )
        
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        
        logger.info(f"Created invitation for {email} to organization {org_id}")
        return invitation
        
    except Exception as e:
        logger.error(f"Failed to create invitation: {e}")
        db.rollback()
        raise


async def get_invitation_by_token(db: Session, token: str) -> Optional[Invitation]:
    """Get invitation by token."""
    try:
        result = db.execute(select(Invitation).where(Invitation.token == token))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Failed to get invitation by token: {e}")
        return None


async def accept_invitation(db: Session, token: str, user_id: int) -> bool:
    """Accept invitation."""
    try:
        invitation = await get_invitation_by_token(db, token)
        if not invitation:
            return False
        
        # Check if invitation is still valid
        if invitation.status != "pending" or invitation.expires_at < datetime.utcnow():
            return False
        
        # Check if user exists
        user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user:
            return False
        
        # Check if user email matches invitation email
        if user.email != invitation.email:
            return False
        
        # Add user to organization
        member = OrganizationMember(
            organization_id=invitation.organization_id,
            user_id=user_id,
            role_id=invitation.role_id
        )
        
        db.add(member)
        
        # Update user's organization and role
        user.organization_id = invitation.organization_id
        user.current_role_id = invitation.role_id
        
        # Update invitation status
        invitation.status = "accepted"
        invitation.accepted_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"User {user_id} accepted invitation to organization {invitation.organization_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to accept invitation: {e}")
        db.rollback()
        return False


async def revoke_invitation(db: Session, invitation_id: int) -> bool:
    """Revoke invitation."""
    try:
        invitation = db.execute(select(Invitation).where(Invitation.id == invitation_id)).scalar_one_or_none()
        if not invitation:
            return False
        
        invitation.status = "revoked"
        db.commit()
        
        logger.info(f"Revoked invitation {invitation_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to revoke invitation: {e}")
        db.rollback()
        return False


async def get_pending_invitations(db: Session, org_id: int) -> List[Dict[str, Any]]:
    """Get pending invitations for organization."""
    try:
        invitations = db.execute(
            select(Invitation, User, Role)
            .join(User, Invitation.invited_by_id == User.id)
            .join(Role, Invitation.role_id == Role.id)
            .where(
                and_(
                    Invitation.organization_id == org_id,
                    Invitation.status == "pending"
                )
            )
        ).all()
        
        return [
            {
                "id": invitation.id,
                "email": invitation.email,
                "role_name": role.name,
                "invited_by_email": user.email,
                "expires_at": invitation.expires_at,
                "created_at": invitation.created_at
            }
            for invitation, user, role in invitations
        ]
        
    except Exception as e:
        logger.error(f"Failed to get pending invitations: {e}")
        return []


async def initialize_default_roles(db: Session) -> bool:
    """Initialize default roles."""
    try:
        for role_name, role_data in ROLES.items():
            # Check if role already exists
            existing_role = db.execute(select(Role).where(Role.name == role_name)).scalar_one_or_none()
            if existing_role:
                continue
            
            # Create role
            role = Role(
                name=role_name,
                description=role_data["description"],
                permissions=role_data["permissions"]
            )
            
            db.add(role)
        
        db.commit()
        logger.info("Initialized default roles")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize default roles: {e}")
        db.rollback()
        return False


async def get_organization_stats(db: Session, org_id: int) -> Dict[str, int]:
    """Get organization statistics."""
    try:
        # Count members
        total_members = db.execute(
            select(OrganizationMember).where(OrganizationMember.organization_id == org_id)
        ).count()
        
        active_members = db.execute(
            select(OrganizationMember).where(
                and_(
                    OrganizationMember.organization_id == org_id,
                    OrganizationMember.is_active == True
                )
            )
        ).count()
        
        # Count pending invitations
        pending_invitations = db.execute(
            select(Invitation).where(
                and_(
                    Invitation.organization_id == org_id,
                    Invitation.status == "pending"
                )
            )
        ).count()
        
        # Count bots (if Bot model is available)
        try:
            from ..shared.models.bot_builder import Bot
            total_bots = db.execute(
                select(Bot).where(Bot.organization_id == org_id)
            ).count()
            
            active_bots = db.execute(
                select(Bot).where(
                    and_(
                        Bot.organization_id == org_id,
                        Bot.is_whatsapp_enabled == True
                    )
                )
            ).count()
        except ImportError:
            total_bots = 0
            active_bots = 0
        
        return {
            "total_members": total_members,
            "active_members": active_members,
            "pending_invitations": pending_invitations,
            "total_bots": total_bots,
            "active_bots": active_bots
        }
        
    except Exception as e:
        logger.error(f"Failed to get organization stats: {e}")
        return {}


async def get_user_organizations(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """Get all organizations for a user."""
    try:
        memberships = db.execute(
            select(OrganizationMember, Organization, Role)
            .join(Organization, OrganizationMember.organization_id == Organization.id)
            .join(Role, OrganizationMember.role_id == Role.id)
            .where(OrganizationMember.user_id == user_id)
        ).all()
        
        return [
            {
                "organization_id": org.id,
                "organization_name": org.name,
                "role_name": role.name,
                "is_owner": org.owner_id == user_id,
                "joined_at": membership.joined_at
            }
            for membership, org, role in memberships
        ]
        
    except Exception as e:
        logger.error(f"Failed to get user organizations: {e}")
        return []
