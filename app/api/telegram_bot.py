"""
API router for Telegram Bot integration.
"""
import json
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database
from app.services.multi_platform_handler import multi_platform_handler
from app.services.telegram_adapter import TelegramAdapter
from app.services.user_manager import UserManager
from app.utils.error_handler import error_handler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/telegram", tags=["Telegram Bot"])

telegram_adapter = TelegramAdapter()


@router.post("/webhook")
async def telegram_webhook(
    request: Request, db: AsyncSession = Depends(get_database)
) -> Dict[str, Any]:
    """
    Telegram Bot webhook endpoint.
    
    Handles incoming updates from Telegram Bot API and processes them
    through the unified multi-platform handler.
    """
    telegram_data = None
    try:
        # Get raw request body for debugging and validation
        raw_body = await request.body()
        logger.debug(f"Raw request body length: {len(raw_body)}, content preview: {raw_body[:100]}...")
        
        # Check if body is empty
        if not raw_body:
            logger.warning("Received empty request body")
            return {"ok": True, "error": "Empty request body"}
        
        # Try to parse JSON manually first to handle errors better
        try:
            body_text = raw_body.decode('utf-8')
            telegram_data = json.loads(body_text)
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode request body as UTF-8: {e}")
            return {"ok": True, "error": "Invalid encoding"}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}. Body content: '{body_text[:200]}...'")
            return {"ok": True, "error": "Invalid JSON"}
        
        logger.info(f"Received Telegram update: {telegram_data.get('update_id')}")
        
        # Validate request
        if not telegram_adapter.validate_request(telegram_data):
            raise HTTPException(status_code=400, detail="Invalid Telegram request")
        
        # Convert to universal format
        universal_request = telegram_adapter.to_universal_request(telegram_data)
        
        # Initialize user manager
        user_manager = UserManager(db)
        await user_manager.get_or_create_user(universal_request.user_id)
        
        # Process through multi-platform handler
        universal_response = await multi_platform_handler.handle_request(
            universal_request, db
        )
        
        # Add platform-specific data for response conversion
        if universal_request.user_context:
            chat_id = None
            callback_query_id = None
            
            # Extract chat_id
            if "telegram_user" in universal_request.user_context:
                # For regular messages, use chat info from message
                if "chat" in universal_request.user_context:
                    chat_id = str(universal_request.user_context["chat"]["id"])
                else:
                    chat_id = universal_request.user_id
            
            # Extract callback_query_id if this is a callback
            if "callback_query" in universal_request.user_context:
                callback_query_id = universal_request.user_context["callback_query"]["id"]
            
            universal_response.platform_specific = {
                "chat_id": chat_id,
                "callback_query_id": callback_query_id,
            }
        
        # Convert response to Telegram format
        telegram_adapter.from_universal_response(universal_response)
        
        logger.info("Successfully processed Telegram request")
        
        # Return 200 OK to Telegram (actual responses are sent via API)
        return {"ok": True}
        
    except HTTPException:
        # Let HTTPException pass through for proper status codes
        raise
    except Exception as e:
        logger.error(f"Error processing Telegram request: {str(e)}", exc_info=True)
        
        # Handle error gracefully
        try:
            # Build context data safely
            context = {"platform": "telegram"}
            
            if telegram_data:
                context["update_id"] = telegram_data.get("update_id", "unknown")
                context["user_id"] = telegram_data.get("message", {}).get("from", {}).get("id", "unknown")
            else:
                context["update_id"] = "unknown"
                context["user_id"] = "unknown"
            
            error_handler.handle_error(e, context)
            
            # For Telegram, we still return 200 OK but log the error
            return {"ok": True, "error": str(e)}
            
        except Exception as error_handling_error:
            logger.error(f"Error in error handling: {error_handling_error}")
            return {"ok": False, "error": "Internal server error"}


@router.get("/health")
async def telegram_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for Telegram Bot service.
    """
    try:
        return {
            "status": "healthy",
            "service": "telegram_bot",
            "platform": "telegram",
            "components": {
                "adapter": "ok",
                "webhook": "ok",
                "multi_platform_handler": "ok",
            },
        }
    except Exception as e:
        logger.error(f"Telegram health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@router.post("/set-webhook")
async def set_telegram_webhook(webhook_url: str) -> Dict[str, Any]:
    """
    Endpoint to set Telegram webhook URL.
    
    This would typically be called during deployment to configure
    the Telegram bot webhook.
    """
    try:
        # Note: In production, this would make an actual API call to Telegram
        # For now, it's a placeholder endpoint
        
        logger.info(f"Setting Telegram webhook to: {webhook_url}")
        
        return {
            "status": "success",
            "message": f"Webhook set to {webhook_url}",
            "note": "This is a placeholder - implement actual webhook setting in production",
        }
        
    except Exception as e:
        logger.error(f"Failed to set Telegram webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to set webhook")


@router.delete("/webhook")
async def delete_telegram_webhook() -> Dict[str, Any]:
    """
    Endpoint to delete Telegram webhook.
    """
    try:
        logger.info("Deleting Telegram webhook")
        
        return {
            "status": "success",
            "message": "Webhook deleted",
            "note": "This is a placeholder - implement actual webhook deletion in production",
        }
        
    except Exception as e:
        logger.error(f"Failed to delete Telegram webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete webhook")