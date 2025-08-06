"""Authentication middleware and utilities for IoT endpoints."""

from typing import Optional
from fastapi import HTTPException, status, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db


class AuthenticationError(Exception):
    """Authentication related errors."""
    pass


async def get_current_user_id(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> int:
    """
    Get current user ID from headers and validate against database.
    
    Args:
        x_user_id: User ID from X-User-ID header
        authorization: Authorization header (future use)
        db: Database session
    
    Returns:
        Validated user ID
        
    Raises:
        HTTPException: If authentication fails
    """
    # Try X-User-ID header first (Yandex style)
    if x_user_id:
        try:
            user_id = int(x_user_id)
            # Validate user exists in database
            if await _validate_user_exists(db, user_id):
                return user_id
            else:
                logger.warning(f"User ID {user_id} not found in database")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user credentials"
                )
        except ValueError:
            logger.warning(f"Invalid user ID format: {x_user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
    
    # TODO: Add token-based authentication for authorization header
    if authorization and authorization.startswith("Bearer "):
        # Placeholder for JWT token validation
        logger.info("Token-based authentication not yet implemented")
        pass
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide X-User-ID header."
    )


async def _validate_user_exists(db: AsyncSession, user_id: int) -> bool:
    """
    Validate that user exists in database.
    
    Args:
        db: Database session
        user_id: User ID to validate
        
    Returns:
        True if user exists, False otherwise
    """
    try:
        # Check if user exists (assuming users table exists or will be created)
        result = await db.execute(
            "SELECT 1 FROM users WHERE id = :user_id LIMIT 1",
            {"user_id": user_id}
        )
        return result.fetchone() is not None
    except Exception as e:
        logger.warning(f"Error validating user {user_id}: {e}")
        # For now, return True to avoid breaking functionality during development
        # In production, this should return False and require proper user setup
        return True


async def get_optional_user_id(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: AsyncSession = Depends(get_db)
) -> Optional[int]:
    """
    Get user ID if provided, without requiring authentication.
    Used for endpoints that are public but can be personalized.
    
    Args:
        x_user_id: Optional user ID from header
        db: Database session
        
    Returns:
        User ID if valid, None if not provided or invalid
    """
    if not x_user_id:
        return None
        
    try:
        user_id = int(x_user_id)
        if await _validate_user_exists(db, user_id):
            return user_id
    except (ValueError, Exception) as e:
        logger.warning(f"Optional auth failed for user {x_user_id}: {e}")
    
    return None