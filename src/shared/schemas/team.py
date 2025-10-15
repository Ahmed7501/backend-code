"""
Pydantic schemas for team management and organization features.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


class OrganizationSchema(BaseModel):
    """Schema for organization data."""
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    owner_id: int
    is_active: bool = True
    created_at: Optional[datetime] = None

    class Config:
       from_attributes = True


class OrganizationCreate(BaseModel):
    """Schema for creating an organization."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class RoleSchema(BaseModel):
    """Schema for role data."""
    id: Optional[int] = None
    name: str
    description: str
    permissions: List[str]

    class Config:
       from_attributes = True


class RoleCreate(BaseModel):
    """Schema for creating a custom role."""
    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., max_length=200)
    permissions: List[str]


class OrganizationMemberSchema(BaseModel):
    """Schema for organization member data."""
    id: Optional[int] = None
    user_id: int
    user_email: str
    user_name: str
    role_name: str
    is_active: bool
    joined_at: datetime

    class Config:
       from_attributes = True


class MemberAddRequest(BaseModel):
    """Schema for adding a member to organization."""
    user_id: int
    role_name: str = Field(..., pattern="^(admin|member|viewer)$")


class MemberRoleUpdate(BaseModel):
    """Schema for updating member role."""
    role_name: str = Field(..., pattern="^(admin|member|viewer)$")


class InvitationCreate(BaseModel):
    """Schema for creating an invitation."""
    email: EmailStr
    role_name: str = Field(..., pattern="^(admin|member|viewer)$")


class InvitationSchema(BaseModel):
    """Schema for invitation data."""
    id: Optional[int] = None
    email: str
    role_name: str
    status: str
    invited_by_email: str
    expires_at: datetime
    created_at: datetime

    class Config:
       from_attributes = True


class InvitationAcceptRequest(BaseModel):
    """Schema for accepting an invitation."""
    token: str


class InvitationResponse(BaseModel):
    """Schema for invitation response."""
    success: bool
    message: str
    invitation_link: Optional[str] = None
    expires_at: Optional[datetime] = None


class OrganizationStats(BaseModel):
    """Schema for organization statistics."""
    total_members: int
    active_members: int
    pending_invitations: int
    total_bots: int
    active_bots: int


class UserOrganizationInfo(BaseModel):
    """Schema for user's organization information."""
    organization_id: Optional[int] = None
    organization_name: Optional[str] = None
    role_name: Optional[str] = None
    is_owner: bool = False
    joined_at: Optional[datetime] = None


class PermissionCheck(BaseModel):
    """Schema for permission check response."""
    has_permission: bool
    permission: str
    user_role: Optional[str] = None
    organization_id: Optional[int] = None
