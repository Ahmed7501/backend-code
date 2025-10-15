"""
Invitation system for team member invitations.
"""

import secrets
import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def generate_invitation_token() -> str:
    """
    Generate secure invitation token.
    
    Returns:
        str: URL-safe random token
    """
    return secrets.token_urlsafe(32)


def create_invitation_link(token: str, base_url: str) -> str:
    """
    Create invitation link.
    
    Args:
        token: Invitation token
        base_url: Base URL of the application
        
    Returns:
        str: Complete invitation link
    """
    return f"{base_url}/invite/accept?token={token}"


async def send_invitation_email(email: str, invitation_link: str, org_name: str, role_name: str) -> bool:
    """
    Send invitation email.
    
    Args:
        email: Recipient email
        invitation_link: Invitation link
        org_name: Organization name
        role_name: Role name
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = f"You've been invited to join {org_name}"
        body = f"""
        Hello,
        
        You have been invited to join {org_name} as a {role_name}.
        
        Click the link below to accept the invitation:
        {invitation_link}
        
        This invitation will expire in 7 days.
        
        If you didn't expect this invitation, you can safely ignore this email.
        
        Best regards,
        The {org_name} Team
        """
        
        # TODO: Integrate with actual email service (SendGrid, AWS SES, etc.)
        logger.info(f"Would send invitation email to {email} for {org_name} as {role_name}")
        logger.info(f"Invitation link: {invitation_link}")
        
        # For now, just log the email content
        logger.info(f"Email subject: {subject}")
        logger.info(f"Email body: {body}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send invitation email: {e}")
        return False


def validate_invitation_token(token: str) -> bool:
    """
    Validate invitation token format.
    
    Args:
        token: Token to validate
        
    Returns:
        bool: True if token format is valid, False otherwise
    """
    try:
        # Basic validation - token should be URL-safe and reasonable length
        if not token or len(token) < 20:
            return False
        
        # Check if token contains only URL-safe characters
        import string
        allowed_chars = string.ascii_letters + string.digits + '-_'
        return all(c in allowed_chars for c in token)
        
    except Exception:
        return False


def calculate_invitation_expiry(days: int = 7) -> datetime:
    """
    Calculate invitation expiry date.
    
    Args:
        days: Number of days until expiry
        
    Returns:
        datetime: Expiry datetime
    """
    return datetime.utcnow() + timedelta(days=days)


def is_invitation_expired(expires_at: datetime) -> bool:
    """
    Check if invitation is expired.
    
    Args:
        expires_at: Expiry datetime
        
    Returns:
        bool: True if expired, False otherwise
    """
    return datetime.utcnow() > expires_at


def format_invitation_email_template(
    org_name: str,
    role_name: str,
    invitation_link: str,
    invited_by_name: str,
    expires_days: int = 7
) -> tuple[str, str]:
    """
    Format invitation email template.
    
    Args:
        org_name: Organization name
        role_name: Role name
        invitation_link: Invitation link
        invited_by_name: Name of person who sent invitation
        expires_days: Days until expiry
        
    Returns:
        tuple: (subject, body) strings
    """
    subject = f"You've been invited to join {org_name}"
    
    body = f"""
    <html>
    <body>
        <h2>You've been invited to join {org_name}</h2>
        
        <p>Hello,</p>
        
        <p>{invited_by_name} has invited you to join <strong>{org_name}</strong> as a <strong>{role_name}</strong>.</p>
        
        <p>Click the button below to accept the invitation:</p>
        
        <p>
            <a href="{invitation_link}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                Accept Invitation
            </a>
        </p>
        
        <p>Or copy and paste this link into your browser:</p>
        <p><a href="{invitation_link}">{invitation_link}</a></p>
        
        <p><strong>Important:</strong> This invitation will expire in {expires_days} days.</p>
        
        <p>If you didn't expect this invitation, you can safely ignore this email.</p>
        
        <hr>
        <p>Best regards,<br>The {org_name} Team</p>
    </body>
    </html>
    """
    
    return subject, body


def create_invitation_qr_code(token: str, base_url: str) -> Optional[str]:
    """
    Create QR code for invitation (optional feature).
    
    Args:
        token: Invitation token
        base_url: Base URL
        
    Returns:
        str: QR code data URL or None if not implemented
    """
    try:
        # TODO: Implement QR code generation using qrcode library
        invitation_link = create_invitation_link(token, base_url)
        logger.info(f"Would generate QR code for: {invitation_link}")
        return None
        
    except Exception as e:
        logger.error(f"Failed to create QR code: {e}")
        return None


def get_invitation_status_text(status: str) -> str:
    """
    Get human-readable status text.
    
    Args:
        status: Invitation status
        
    Returns:
        str: Human-readable status
    """
    status_map = {
        "pending": "Pending",
        "accepted": "Accepted",
        "expired": "Expired",
        "revoked": "Revoked"
    }
    
    return status_map.get(status, "Unknown")


def format_invitation_expiry(expires_at: datetime) -> str:
    """
    Format invitation expiry for display.
    
    Args:
        expires_at: Expiry datetime
        
    Returns:
        str: Formatted expiry string
    """
    now = datetime.utcnow()
    time_diff = expires_at - now
    
    if time_diff.total_seconds() < 0:
        return "Expired"
    
    days = time_diff.days
    hours = time_diff.seconds // 3600
    
    if days > 0:
        return f"{days} day{'s' if days != 1 else ''} remaining"
    elif hours > 0:
        return f"{hours} hour{'s' if hours != 1 else ''} remaining"
    else:
        return "Less than 1 hour remaining"
