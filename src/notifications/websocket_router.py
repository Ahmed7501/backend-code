"""
WebSocket router for real-time notifications.
"""

import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from jose import JWTError, jwt

from ..shared.database import get_sync_session
from ..shared.models.auth import User
from ..auth.auth import SECRET_KEY, ALGORITHM
from .websocket_manager import manager
from .crud import mark_as_read

logger = logging.getLogger(__name__)

router = APIRouter()


async def authenticate_websocket_user(token: str, db: Session) -> Optional[User]:
    """Authenticate user from JWT token for WebSocket connection."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        
        # Get user from database
        user = db.query(User).filter(User.email == email).first()
        if user is None or not user.is_active:
            return None
        
        return user
        
    except JWTError:
        return None
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_sync_session)
):
    """WebSocket endpoint for real-time notifications."""
    user = await authenticate_websocket_user(token, db)
    if not user:
        logger.warning("WebSocket connection rejected: Invalid token")
        await websocket.close(code=1008, reason="Unauthorized")
        return
    
    # Connect user
    await manager.connect(websocket, user.id, user.organization_id)
    
    try:
        # Send initial connection success message
        await websocket.send_json({
            "type": "connected",
            "data": {
                "user_id": user.id,
                "organization_id": user.organization_id,
                "username": user.username
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"WebSocket connected for user {user.id} ({user.username})")
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                
                # Handle ping/pong
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # Handle mark as read
                elif data.get("type") == "mark_read":
                    notification_id = data.get("notification_id")
                    if notification_id:
                        mark_as_read(db, notification_id, user.id)
                        await websocket.send_json({
                            "type": "mark_read_success",
                            "data": {"notification_id": notification_id},
                            "timestamp": datetime.utcnow().isoformat()
                        })
                
                # Handle bulk mark as read
                elif data.get("type") == "mark_all_read":
                    from .crud import mark_all_as_read
                    updated_count = mark_all_as_read(db, user.id)
                    await websocket.send_json({
                        "type": "mark_all_read_success",
                        "data": {"updated_count": updated_count},
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # Handle get unread count
                elif data.get("type") == "get_unread_count":
                    from .crud import get_unread_count
                    count = get_unread_count(db, user.id)
                    await websocket.send_json({
                        "type": "unread_count",
                        "data": {"count": count},
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # Handle unknown message types
                else:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": f"Unknown message type: {data.get('type')}"},
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Internal server error"},
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.id}")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        manager.disconnect(websocket, user.id, user.organization_id)


@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status."""
    try:
        return {
            "active_connections": manager.get_connection_count(),
            "connected_users": len(manager.get_connected_users()),
            "connected_organizations": len(manager.get_connected_organizations()),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get WebSocket status: {e}")
        return {
            "error": "Failed to get status",
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/ws/users/{user_id}/status")
async def user_websocket_status(user_id: int):
    """Get WebSocket status for a specific user."""
    try:
        is_connected = manager.is_user_connected(user_id)
        connection_count = manager.get_user_connection_count(user_id)
        
        return {
            "user_id": user_id,
            "is_connected": is_connected,
            "connection_count": connection_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get user WebSocket status: {e}")
        return {
            "error": "Failed to get user status",
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/ws/organizations/{organization_id}/status")
async def organization_websocket_status(organization_id: int):
    """Get WebSocket status for an organization."""
    try:
        connection_count = manager.get_organization_connection_count(organization_id)
        
        return {
            "organization_id": organization_id,
            "connection_count": connection_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get organization WebSocket status: {e}")
        return {
            "error": "Failed to get organization status",
            "timestamp": datetime.utcnow().isoformat()
        }
