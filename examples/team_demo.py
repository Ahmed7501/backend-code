#!/usr/bin/env python3
"""
Team Management Demo Script

This script demonstrates the Team Management API endpoints for:
- Organization creation and management
- Team member invitations
- Role-based access control
- Permission checking

Usage:
    python examples/team_demo.py --help
    python examples/team_demo.py --quick
    python examples/team_demo.py --org-id 1 --user-id 2
"""

import argparse
import asyncio
import json
import logging
import sys
from typing import Dict, Any, Optional
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/team"

# Demo data
DEMO_ORGANIZATION = {
    "name": "Demo Company Inc",
    "description": "A demo organization for testing team management"
}

DEMO_INVITATION = {
    "email": "demo@example.com",
    "role_name": "member"
}

DEMO_MEMBER = {
    "user_id": 2,
    "role_name": "viewer"
}


class TeamManagementDemo:
    """Demo class for Team Management API."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.api_base = f"{base_url}/team"
        self.auth_base = f"{base_url}/auth"
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.organization_id: Optional[int] = None
    
    def authenticate(self, email: str = "admin@example.com", password: str = "admin123") -> bool:
        """Authenticate and get access token."""
        try:
            # Login
            login_data = {
                "username": email,  # FastAPI OAuth2 uses 'username' field for email
                "password": password
            }
            
            response = self.session.post(
                f"{self.auth_base}/token",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                
                # Set authorization header
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                
                # Get user info
                user_response = self.session.get(f"{self.auth_base}/me")
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    self.user_id = user_data["id"]
                    self.organization_id = user_data.get("organization_id")
                    logger.info(f"Authenticated as user {self.user_id}")
                    return True
                else:
                    logger.error("Failed to get user info")
                    return False
            else:
                logger.error(f"Authentication failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def create_organization(self, org_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new organization."""
        try:
            response = self.session.post(
                f"{self.api_base}/organizations",
                json=org_data
            )
            
            if response.status_code == 201:
                org = response.json()
                self.organization_id = org["id"]
                logger.info(f"Created organization: {org['name']} (ID: {org['id']})")
                return org
            else:
                logger.error(f"Failed to create organization: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            return None
    
    def get_organization(self, org_id: int) -> Optional[Dict[str, Any]]:
        """Get organization details."""
        try:
            response = self.session.get(f"{self.api_base}/organizations/{org_id}")
            
            if response.status_code == 200:
                org = response.json()
                logger.info(f"Retrieved organization: {org['name']}")
                return org
            else:
                logger.error(f"Failed to get organization: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting organization: {e}")
            return None
    
    def update_organization(self, org_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update organization."""
        try:
            response = self.session.put(
                f"{self.api_base}/organizations/{org_id}",
                json=updates
            )
            
            if response.status_code == 200:
                org = response.json()
                logger.info(f"Updated organization: {org['name']}")
                return org
            else:
                logger.error(f"Failed to update organization: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error updating organization: {e}")
            return None
    
    def get_organization_members(self, org_id: int) -> Optional[list]:
        """Get organization members."""
        try:
            response = self.session.get(f"{self.api_base}/organizations/{org_id}/members")
            
            if response.status_code == 200:
                members = response.json()
                logger.info(f"Retrieved {len(members)} organization members")
                return members
            else:
                logger.error(f"Failed to get organization members: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting organization members: {e}")
            return None
    
    def add_member(self, org_id: int, member_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add member to organization."""
        try:
            response = self.session.post(
                f"{self.api_base}/organizations/{org_id}/members",
                json=member_data
            )
            
            if response.status_code == 200:
                member = response.json()
                logger.info(f"Added member: {member['user_name']} as {member['role_name']}")
                return member
            else:
                logger.error(f"Failed to add member: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error adding member: {e}")
            return None
    
    def update_member_role(self, org_id: int, user_id: int, role_name: str) -> Optional[Dict[str, Any]]:
        """Update member role."""
        try:
            response = self.session.put(
                f"{self.api_base}/organizations/{org_id}/members/{user_id}",
                json={"role_name": role_name}
            )
            
            if response.status_code == 200:
                member = response.json()
                logger.info(f"Updated member role: {member['user_name']} -> {member['role_name']}")
                return member
            else:
                logger.error(f"Failed to update member role: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error updating member role: {e}")
            return None
    
    def create_invitation(self, org_id: int, invitation_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create invitation."""
        try:
            response = self.session.post(
                f"{self.api_base}/organizations/{org_id}/invitations",
                json=invitation_data
            )
            
            if response.status_code == 200:
                invitation = response.json()
                logger.info(f"Created invitation for {invitation_data['email']} as {invitation_data['role_name']}")
                logger.info(f"Invitation link: {invitation.get('invitation_link', 'N/A')}")
                return invitation
            else:
                logger.error(f"Failed to create invitation: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating invitation: {e}")
            return None
    
    def get_pending_invitations(self, org_id: int) -> Optional[list]:
        """Get pending invitations."""
        try:
            response = self.session.get(f"{self.api_base}/organizations/{org_id}/invitations")
            
            if response.status_code == 200:
                invitations = response.json()
                logger.info(f"Retrieved {len(invitations)} pending invitations")
                return invitations
            else:
                logger.error(f"Failed to get pending invitations: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting pending invitations: {e}")
            return None
    
    def check_permission(self, permission: str) -> Optional[Dict[str, Any]]:
        """Check user permission."""
        try:
            response = self.session.get(
                f"{self.api_base}/permissions/check",
                params={"permission": permission}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Permission '{permission}': {result['has_permission']}")
                return result
            else:
                logger.error(f"Failed to check permission: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return None
    
    def get_organization_stats(self, org_id: int) -> Optional[Dict[str, Any]]:
        """Get organization statistics."""
        try:
            response = self.session.get(f"{self.api_base}/organizations/{org_id}/stats")
            
            if response.status_code == 200:
                stats = response.json()
                logger.info(f"Organization stats: {stats}")
                return stats
            else:
                logger.error(f"Failed to get organization stats: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting organization stats: {e}")
            return None
    
    def get_roles(self) -> Optional[Dict[str, Any]]:
        """Get available roles."""
        try:
            response = self.session.get(f"{self.api_base}/roles")
            
            if response.status_code == 200:
                roles = response.json()
                logger.info(f"Available roles: {list(roles['roles'].keys())}")
                return roles
            else:
                logger.error(f"Failed to get roles: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting roles: {e}")
            return None
    
    def run_quick_demo(self):
        """Run a quick demonstration of team management features."""
        logger.info("🚀 Starting Team Management Quick Demo")
        
        # Authenticate
        if not self.authenticate():
            logger.error("❌ Authentication failed")
            return
        
        # Get available roles
        logger.info("\n📋 Getting available roles...")
        self.get_roles()
        
        # Create organization
        logger.info("\n🏢 Creating organization...")
        org = self.create_organization(DEMO_ORGANIZATION)
        if not org:
            logger.error("❌ Failed to create organization")
            return
        
        org_id = org["id"]
        
        # Get organization details
        logger.info("\n📊 Getting organization details...")
        self.get_organization(org_id)
        
        # Get organization members
        logger.info("\n👥 Getting organization members...")
        self.get_organization_members(org_id)
        
        # Check permissions
        logger.info("\n🔐 Checking permissions...")
        permissions_to_check = [
            "bot:create",
            "team:invite",
            "org:manage",
            "analytics:view"
        ]
        
        for permission in permissions_to_check:
            self.check_permission(permission)
        
        # Create invitation
        logger.info("\n📧 Creating invitation...")
        self.create_invitation(org_id, DEMO_INVITATION)
        
        # Get pending invitations
        logger.info("\n📬 Getting pending invitations...")
        self.get_pending_invitations(org_id)
        
        # Get organization statistics
        logger.info("\n📈 Getting organization statistics...")
        self.get_organization_stats(org_id)
        
        # Update organization
        logger.info("\n✏️ Updating organization...")
        updates = {
            "description": "Updated description for demo organization"
        }
        self.update_organization(org_id, updates)
        
        logger.info("\n✅ Quick demo completed successfully!")
    
    def run_comprehensive_demo(self, org_id: Optional[int] = None, user_id: Optional[int] = None):
        """Run a comprehensive demonstration."""
        logger.info("🚀 Starting Team Management Comprehensive Demo")
        
        # Authenticate
        if not self.authenticate():
            logger.error("❌ Authentication failed")
            return
        
        # Use provided org_id or create new organization
        if org_id:
            self.organization_id = org_id
            logger.info(f"Using existing organization ID: {org_id}")
        else:
            # Create organization
            logger.info("\n🏢 Creating organization...")
            org = self.create_organization(DEMO_ORGANIZATION)
            if not org:
                logger.error("❌ Failed to create organization")
                return
            org_id = org["id"]
        
        # Comprehensive organization management
        logger.info("\n📊 Comprehensive organization management...")
        
        # Get organization details
        org_details = self.get_organization(org_id)
        if org_details:
            logger.info(f"Organization: {org_details['name']}")
            logger.info(f"Description: {org_details['description']}")
            logger.info(f"Owner ID: {org_details['owner_id']}")
            logger.info(f"Active: {org_details['is_active']}")
        
        # Get organization members
        members = self.get_organization_members(org_id)
        if members:
            logger.info(f"\nOrganization has {len(members)} members:")
            for member in members:
                logger.info(f"  - {member['user_name']} ({member['user_email']}) - {member['role_name']}")
        
        # Add member if user_id provided
        if user_id:
            logger.info(f"\n👤 Adding user {user_id} as member...")
            member_data = {"user_id": user_id, "role_name": "member"}
            self.add_member(org_id, member_data)
            
            # Update member role
            logger.info(f"\n🔄 Updating user {user_id} role to viewer...")
            self.update_member_role(org_id, user_id, "viewer")
        
        # Create multiple invitations
        logger.info("\n📧 Creating multiple invitations...")
        invitations = [
            {"email": "admin@demo.com", "role_name": "admin"},
            {"email": "member@demo.com", "role_name": "member"},
            {"email": "viewer@demo.com", "role_name": "viewer"}
        ]
        
        for invitation in invitations:
            self.create_invitation(org_id, invitation)
        
        # Get pending invitations
        pending = self.get_pending_invitations(org_id)
        if pending:
            logger.info(f"\nPending invitations ({len(pending)}):")
            for invitation in pending:
                logger.info(f"  - {invitation['email']} as {invitation['role_name']}")
        
        # Check all permissions
        logger.info("\n🔐 Checking all permissions...")
        all_permissions = [
            "bot:create", "bot:read", "bot:update", "bot:delete",
            "flow:create", "flow:read", "flow:update", "flow:delete",
            "analytics:view", "analytics:export",
            "team:view", "team:invite", "team:manage", "team:remove",
            "org:manage", "org:delete",
            "contact:view", "contact:manage",
            "trigger:create", "trigger:read", "trigger:update", "trigger:delete"
        ]
        
        permission_results = {}
        for permission in all_permissions:
            result = self.check_permission(permission)
            if result:
                permission_results[permission] = result['has_permission']
        
        # Display permission summary
        logger.info("\n📋 Permission Summary:")
        for permission, has_perm in permission_results.items():
            status = "✅" if has_perm else "❌"
            logger.info(f"  {status} {permission}")
        
        # Get organization statistics
        stats = self.get_organization_stats(org_id)
        if stats:
            logger.info(f"\n📈 Organization Statistics:")
            logger.info(f"  Total Members: {stats['total_members']}")
            logger.info(f"  Active Members: {stats['active_members']}")
            logger.info(f"  Pending Invitations: {stats['pending_invitations']}")
            logger.info(f"  Total Bots: {stats['total_bots']}")
            logger.info(f"  Active Bots: {stats['active_bots']}")
        
        # Update organization
        logger.info("\n✏️ Updating organization...")
        updates = {
            "description": f"Updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        self.update_organization(org_id, updates)
        
        logger.info("\n✅ Comprehensive demo completed successfully!")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Team Management Demo")
    parser.add_argument("--quick", action="store_true", help="Run quick demo")
    parser.add_argument("--org-id", type=int, help="Organization ID for comprehensive demo")
    parser.add_argument("--user-id", type=int, help="User ID to add as member")
    parser.add_argument("--base-url", default=BASE_URL, help="Base URL for API")
    
    args = parser.parse_args()
    
    # Create demo instance
    demo = TeamManagementDemo(args.base_url)
    
    try:
        if args.quick:
            demo.run_quick_demo()
        else:
            demo.run_comprehensive_demo(args.org_id, args.user_id)
    except KeyboardInterrupt:
        logger.info("\n⏹️ Demo interrupted by user")
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
