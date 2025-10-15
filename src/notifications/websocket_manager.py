"""
WebSocket connection manager for real-time notifications.
"""

import logging
from typing import Dict, List, Set, Optional
from fastapi import WebSocket
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time notifications."""
    
    def __init__(self):
        # Map user_id -> list of WebSocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Map organization_id -> set of user_ids
        self.organization_members: Dict[int, Set[int]] = {}
        # Track connection meta_data
        self.connection_meta_data: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int, organization_id: int):
        """Accept WebSocket connection and track user."""
        try:
            await websocket.accept()
            
            # Add to user connections
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            self.active_connections[user_id].append(websocket)
            
            # Track organization membership
            if organization_id not in self.organization_members:
                self.organization_members[organization_id] = set()
            self.organization_members[organization_id].add(user_id)
            
            # Store connection meta_data
            self.connection_meta_data[websocket] = {
                "user_id": user_id,
                "organization_id": organization_id,
                "connected_at": datetime.utcnow()
            }
            
            logger.info(f"User {user_id} connected to WebSocket (org: {organization_id})")
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket for user {user_id}: {e}")
            raise
    
    def disconnect(self, websocket: WebSocket, user_id: Optional[int] = None, organization_id: Optional[int] = None):
        """Remove WebSocket connection and clean up tracking."""
        try:
            # Get meta_data if not provided
            if not user_id or not organization_id:
                meta_data = self.connection_metadata.get(websocket, {})
                user_id = user_id or meta_data.get("user_id")
                organization_id = organization_id or meta_data.get("organization_id")
            
            # Remove from user connections
            if user_id and user_id in self.active_connections:
                if websocket in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(websocket)
                
                # Clean up empty user connection list
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Remove from organization tracking
            if organization_id and organization_id in self.organization_members:
                self.organization_members[organization_id].discard(user_id)
                
                # Clean up empty organization
                if not self.organization_members[organization_id]:
                    del self.organization_members[organization_id]
            
            # Remove meta_data
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]
            
            logger.info(f"User {user_id} disconnected from WebSocket (org: {organization_id})")
            
        except Exception as e:
            logger.error(f"Failed to disconnect WebSocket: {e}")
    
    async def send_to_user(self, user_id: int, message: dict):
        """Send message to all connections of a specific user."""
        if user_id not in self.active_connections:
            logger.debug(f"No active connections for user {user_id}")
            return
        
        failed_connections = []
        
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                failed_connections.append(connection)
        
        # Clean up failed connections
        for connection in failed_connections:
            self.disconnect(connection, user_id)
    
    async def send_to_organization(self, organization_id: int, message: dict):
        """Send message to all users in an organization."""
        if organization_id not in self.organization_members:
            logger.debug(f"No active members for organization {organization_id}")
            return
        
        for user_id in self.organization_members[organization_id]:
            await self.send_to_user(user_id, message)
    
    async def broadcast(self, message: dict):
        """Send message to all connected users."""
        failed_connections = []
        
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to broadcast to user {user_id}: {e}")
                    failed_connections.append((connection, user_id))
        
        # Clean up failed connections
        for connection, user_id in failed_connections:
            self.disconnect(connection, user_id)
    
    async def send_ping(self, websocket: WebSocket):
        """Send ping message to keep connection alive."""
        try:
            await websocket.send_json({
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to send ping: {e}")
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_user_connection_count(self, user_id: int) -> int:
        """Get number of connections for a specific user."""
        return len(self.active_connections.get(user_id, []))
    
    def get_organization_connection_count(self, organization_id: int) -> int:
        """Get number of connected users in an organization."""
        if organization_id not in self.organization_members:
            return 0
        
        total_connections = 0
        for user_id in self.organization_members[organization_id]:
            total_connections += self.get_user_connection_count(user_id)
        
        return total_connections
    
    def get_connected_users(self) -> List[int]:
        """Get list of all connected user IDs."""
        return list(self.active_connections.keys())
    
    def get_connected_organizations(self) -> List[int]:
        """Get list of all organizations with connected users."""
        return list(self.organization_members.keys())
    
    def is_user_connected(self, user_id: int) -> bool:
        """Check if a user has active connections."""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0
    
    def get_connection_info(self, websocket: WebSocket) -> Optional[Dict]:
        """Get connection meta_data."""
        return self.connection_metadata.get(websocket)
    
    async def cleanup_stale_connections(self):
        """Clean up stale connections by sending ping and removing failed ones."""
        stale_connections = []
        
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await self.send_ping(connection)
                except Exception:
                    stale_connections.append((connection, user_id))
        
        # Remove stale connections
        for connection, user_id in stale_connections:
            self.disconnect(connection, user_id)
        
        if stale_connections:
            logger.info(f"Cleaned up {len(stale_connections)} stale connections")


# Global connection manager instance
manager = ConnectionManager()
