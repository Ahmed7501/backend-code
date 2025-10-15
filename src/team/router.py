"""
API router for team management and organization features.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..shared.database import get_db
from ..shared.models.auth import User
from ..shared.schemas.team import (
    OrganizationSchema,
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationMemberSchema,
    MemberAddRequest,
    MemberRoleUpdate,
    InvitationCreate,
    InvitationSchema,
    InvitationAcceptRequest,
    InvitationResponse,
    OrganizationStats,
    UserOrganizationInfo,
    PermissionCheck
)
from ..auth.auth import get_current_active_user
from .crud import (
    create_organization,
    get_organization,
    update_organization,
    delete_organization,
    add_member_to_organization,
    remove_member_from_organization,
    update_member_role,
    get_organization_members,
    create_invitation,
    get_invitation_by_token,
    accept_invitation,
    revoke_invitation,
    get_pending_invitations,
    get_organization_stats,
    get_user_organizations
)
from .permissions import (
    require_permission,
    require_org_admin,
    require_org_owner,
    require_org_member,
    Permission,
    has_permission,
    get_user_permissions
)
from .invitations import (
    create_invitation_link,
    send_invitation_email,
    format_invitation_email_template
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/team", tags=["Team Management"])


@router.post("/organizations", response_model=OrganizationSchema, status_code=status.HTTP_201_CREATED)
async def create_organization_endpoint(
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new organization."""
    try:
        # Check if user already has an organization
        if current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already belongs to an organization"
            )
        
        organization = await create_organization(
            db=db,
            name=org_data.name,
            description=org_data.description,
            owner_id=current_user.id
        )
        
        return OrganizationSchema.from_orm(organization)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization"
        )


@router.get("/organizations/{org_id}", response_model=OrganizationSchema)
async def get_organization_endpoint(
    org_id: int,
    current_user: User = Depends(require_org_member()),
    db: Session = Depends(get_db)
):
    """Get organization details."""
    try:
        # Check if user belongs to this organization
        if current_user.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
        
        organization = await get_organization(db, org_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        return OrganizationSchema.from_orm(organization)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get organization"
        )


@router.put("/organizations/{org_id}", response_model=OrganizationSchema)
async def update_organization_endpoint(
    org_id: int,
    org_data: OrganizationUpdate,
    current_user: User = Depends(require_org_owner()),
    db: Session = Depends(get_db)
):
    """Update organization."""
    try:
        # Check if user owns this organization
        if current_user.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organization owner can update organization"
            )
        
        organization = await update_organization(db, org_id, org_data)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        return OrganizationSchema.from_orm(organization)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization"
        )


@router.delete("/organizations/{org_id}")
async def delete_organization_endpoint(
    org_id: int,
    current_user: User = Depends(require_org_owner()),
    db: Session = Depends(get_db)
):
    """Delete organization."""
    try:
        # Check if user owns this organization
        if current_user.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organization owner can delete organization"
            )
        
        success = await delete_organization(db, org_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        return {"message": "Organization deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete organization"
        )


@router.get("/organizations/{org_id}/members", response_model=List[OrganizationMemberSchema])
async def get_organization_members_endpoint(
    org_id: int,
    current_user: User = Depends(require_org_member()),
    db: Session = Depends(get_db)
):
    """Get organization members."""
    try:
        # Check if user belongs to this organization
        if current_user.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
        
        members = await get_organization_members(db, org_id)
        return [OrganizationMemberSchema(**member) for member in members]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get organization members: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get organization members"
        )


@router.post("/organizations/{org_id}/members", response_model=OrganizationMemberSchema)
async def add_organization_member_endpoint(
    org_id: int,
    member_data: MemberAddRequest,
    current_user: User = Depends(require_org_admin()),
    db: Session = Depends(get_db)
):
    """Add member to organization."""
    try:
        # Check if user belongs to this organization
        if current_user.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
        
        member = await add_member_to_organization(
            db=db,
            org_id=org_id,
            user_id=member_data.user_id,
            role_name=member_data.role_name
        )
        
        # Get member details for response
        members = await get_organization_members(db, org_id)
        member_info = next((m for m in members if m["user_id"] == member_data.user_id), None)
        
        if not member_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve member information"
            )
        
        return OrganizationMemberSchema(**member_info)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add organization member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add organization member"
        )


@router.put("/organizations/{org_id}/members/{user_id}", response_model=OrganizationMemberSchema)
async def update_member_role_endpoint(
    org_id: int,
    user_id: int,
    role_data: MemberRoleUpdate,
    current_user: User = Depends(require_org_admin()),
    db: Session = Depends(get_db)
):
    """Update member role."""
    try:
        # Check if user belongs to this organization
        if current_user.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
        
        member = await update_member_role(
            db=db,
            org_id=org_id,
            user_id=user_id,
            role_name=role_data.role_name
        )
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        # Get updated member details
        members = await get_organization_members(db, org_id)
        member_info = next((m for m in members if m["user_id"] == user_id), None)
        
        if not member_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve member information"
            )
        
        return OrganizationMemberSchema(**member_info)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update member role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update member role"
        )


@router.delete("/organizations/{org_id}/members/{user_id}")
async def remove_organization_member_endpoint(
    org_id: int,
    user_id: int,
    current_user: User = Depends(require_org_admin()),
    db: Session = Depends(get_db)
):
    """Remove member from organization."""
    try:
        # Check if user belongs to this organization
        if current_user.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
        
        # Prevent removing organization owner
        organization = await get_organization(db, org_id)
        if organization and organization.owner_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove organization owner"
            )
        
        success = await remove_member_from_organization(
            db=db,
            org_id=org_id,
            user_id=user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        return {"message": "Member removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove organization member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove organization member"
        )


@router.post("/organizations/{org_id}/invitations", response_model=InvitationResponse)
async def create_invitation_endpoint(
    org_id: int,
    invitation_data: InvitationCreate,
    current_user: User = Depends(require_org_admin()),
    db: Session = Depends(get_db)
):
    """Create invitation."""
    try:
        # Check if user belongs to this organization
        if current_user.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
        
        invitation = await create_invitation(
            db=db,
            org_id=org_id,
            email=invitation_data.email,
            role_name=invitation_data.role_name,
            invited_by_id=current_user.id
        )
        
        # Create invitation link
        base_url = "http://localhost:8000"  # TODO: Get from settings
        invitation_link = create_invitation_link(invitation.token, base_url)
        
        # Send invitation email
        organization = await get_organization(db, org_id)
        org_name = organization.name if organization else "Unknown Organization"
        
        email_sent = await send_invitation_email(
            email=invitation_data.email,
            invitation_link=invitation_link,
            org_name=org_name,
            role_name=invitation_data.role_name
        )
        
        return InvitationResponse(
            success=True,
            message=f"Invitation sent to {invitation_data.email}",
            invitation_link=invitation_link,
            expires_at=invitation.expires_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create invitation"
        )


@router.get("/organizations/{org_id}/invitations", response_model=List[InvitationSchema])
async def get_organization_invitations_endpoint(
    org_id: int,
    current_user: User = Depends(require_org_admin()),
    db: Session = Depends(get_db)
):
    """Get organization invitations."""
    try:
        # Check if user belongs to this organization
        if current_user.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
        
        invitations = await get_pending_invitations(db, org_id)
        return [InvitationSchema(**invitation) for invitation in invitations]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get organization invitations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get organization invitations"
        )


@router.post("/invitations/{token}/accept")
async def accept_invitation_endpoint(
    token: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Accept invitation."""
    try:
        success = await accept_invitation(db, token, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invitation"
            )
        
        return {"message": "Invitation accepted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to accept invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to accept invitation"
        )


@router.delete("/invitations/{invitation_id}/revoke")
async def revoke_invitation_endpoint(
    invitation_id: int,
    current_user: User = Depends(require_org_admin()),
    db: Session = Depends(get_db)
):
    """Revoke invitation."""
    try:
        success = await revoke_invitation(db, invitation_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )
        
        return {"message": "Invitation revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke invitation"
        )


@router.get("/organizations/{org_id}/stats", response_model=OrganizationStats)
async def get_organization_stats_endpoint(
    org_id: int,
    current_user: User = Depends(require_org_member()),
    db: Session = Depends(get_db)
):
    """Get organization statistics."""
    try:
        # Check if user belongs to this organization
        if current_user.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
        
        stats = await get_organization_stats(db, org_id)
        return OrganizationStats(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get organization stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get organization stats"
        )


@router.get("/my-organizations", response_model=List[UserOrganizationInfo])
async def get_my_organizations_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's organizations."""
    try:
        organizations = await get_user_organizations(db, current_user.id)
        return [UserOrganizationInfo(**org) for org in organizations]
        
    except Exception as e:
        logger.error(f"Failed to get user organizations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user organizations"
        )


@router.get("/permissions/check", response_model=PermissionCheck)
async def check_permission_endpoint(
    permission: str = Query(..., description="Permission to check"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Check if user has specific permission."""
    try:
        # Validate permission
        try:
            perm = Permission(permission)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid permission: {permission}"
            )
        
        has_perm = await has_permission(current_user, perm, db)
        user_permissions = get_user_permissions(current_user, db)
        
        return PermissionCheck(
            has_permission=has_perm,
            permission=permission,
            user_role=current_user.current_role.name if current_user.current_role else None,
            organization_id=current_user.organization_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check permission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check permission"
        )


@router.get("/roles")
async def get_roles_endpoint():
    """Get available roles."""
    try:
        from .permissions import get_all_roles
        roles = get_all_roles()
        return {"roles": roles}
        
    except Exception as e:
        logger.error(f"Failed to get roles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get roles"
        )
