
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class User(Base):
    """
    User model representing the users table.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        email: Unique email address for the user
        username: Unique username for the user
        hashed_password: Bcrypt hashed password
        is_active: Boolean flag indicating if user is active
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    current_role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    organization = relationship("Organization", foreign_keys=[organization_id])
    current_role = relationship("Role", foreign_keys=[current_role_id])

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"


class Organization(Base):
    """Organization model for team management."""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("OrganizationMember", back_populates="organization")
    bots = relationship("Bot", back_populates="organization")


class Role(Base):
    """Role model for role-based access control."""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # 'admin', 'member', 'viewer'
    description = Column(String)
    permissions = Column(JSON)  # List of permissions
    created_at = Column(DateTime, default=datetime.utcnow)


class OrganizationMember(Base):
    """Organization member model linking users to organizations with roles."""
    __tablename__ = "organization_members"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role_id = Column(Integer, ForeignKey("roles.id"))
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="members")
    user = relationship("User")
    role = relationship("Role")
    
    __table_args__ = (UniqueConstraint('organization_id', 'user_id', name='_org_user_uc'),)


class Invitation(Base):
    """Invitation model for team member invitations."""
    __tablename__ = "invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    email = Column(String, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    token = Column(String, unique=True, index=True)
    invited_by_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String)  # 'pending', 'accepted', 'expired', 'revoked'
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    
    organization = relationship("Organization")
    invited_by = relationship("User")
    role = relationship("Role")
