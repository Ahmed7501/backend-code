"""
Team Management module for organization and role-based access control.
"""

from .permissions import (
    Permission,
    ROLES,
    require_permission,
    require_org_admin,
    require_org_owner,
    require_org_member,
    has_permission,
    is_org_admin,
    is_org_owner,
    get_user_permissions,
    check_permission_in_list,
    get_role_permissions,
    get_all_roles
)

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
    initialize_default_roles,
    get_organization_stats,
    get_user_organizations
)

from .invitations import (
    generate_invitation_token,
    create_invitation_link,
    send_invitation_email,
    validate_invitation_token,
    calculate_invitation_expiry,
    is_invitation_expired,
    format_invitation_email_template,
    create_invitation_qr_code,
    get_invitation_status_text,
    format_invitation_expiry
)

from .router import router

__all__ = [
    # Permissions
    "Permission",
    "ROLES",
    "require_permission",
    "require_org_admin",
    "require_org_owner",
    "require_org_member",
    "has_permission",
    "is_org_admin",
    "is_org_owner",
    "get_user_permissions",
    "check_permission_in_list",
    "get_role_permissions",
    "get_all_roles",
    
    # CRUD operations
    "create_organization",
    "get_organization",
    "update_organization",
    "delete_organization",
    "add_member_to_organization",
    "remove_member_from_organization",
    "update_member_role",
    "get_organization_members",
    "create_invitation",
    "get_invitation_by_token",
    "accept_invitation",
    "revoke_invitation",
    "get_pending_invitations",
    "initialize_default_roles",
    "get_organization_stats",
    "get_user_organizations",
    
    # Invitations
    "generate_invitation_token",
    "create_invitation_link",
    "send_invitation_email",
    "validate_invitation_token",
    "calculate_invitation_expiry",
    "is_invitation_expired",
    "format_invitation_email_template",
    "create_invitation_qr_code",
    "get_invitation_status_text",
    "format_invitation_expiry",
    
    # Router
    "router"
]
