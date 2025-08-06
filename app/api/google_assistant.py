"""
API router for Google Assistant integration.
"""
import json
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database
from app.services.google_adapter import GoogleAssistantAdapter
from app.services.multi_platform_handler import multi_platform_handler
from app.services.user_manager import UserManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/google", tags=["Google Assistant"])

google_adapter = GoogleAssistantAdapter()


@router.post("/webhook")
async def google_assistant_webhook(
    request: Request, db: AsyncSession = Depends(get_database)
) -> Dict[str, Any]:
    """
    Google Assistant webhook endpoint.

    Handles incoming requests from Google Actions and Dialogflow
    and processes them through the unified multi-platform handler.
    """
    google_data = None
    body_text = ""
    try:
        # Get raw request body for debugging and validation
        raw_body = await request.body()
        logger.debug(
            "Raw request body length: %d, content preview: %s...",
            len(raw_body),
            raw_body[:100].decode("utf-8", errors="replace"),
        )

        # Check if body is empty
        if not raw_body:
            logger.warning("Received empty request body")
            return {"fulfillmentText": "Empty request received"}

        # Try to parse JSON manually first to handle errors better
        try:
            body_text = raw_body.decode("utf-8")
            google_data = json.loads(body_text)
        except UnicodeDecodeError as e:
            logger.error("Failed to decode request body as UTF-8: %s", e)
            return {"fulfillmentText": "Invalid request encoding"}
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse JSON: %s. Body content: '%s...'", e, body_text[:200]
            )
            return {"fulfillmentText": "Invalid request format"}

        logger.info("Received Google Assistant request")

        # Validate request
        if not google_adapter.validate_request(google_data):
            raise HTTPException(
                status_code=400, detail="Invalid Google Assistant request"
            )

        # Convert to universal format
        universal_request = google_adapter.to_universal_request(google_data)

        # Initialize user manager
        user_manager = UserManager(db)
        await user_manager.get_or_create_user(universal_request.user_id)

        # Process through multi-platform handler
        universal_response = await multi_platform_handler.handle_request(
            universal_request, db
        )

        # Add platform-specific data for response conversion
        platform_specific = {}

        # Check if this is a Dialogflow request
        if "queryResult" in google_data:
            platform_specific["use_dialogflow"] = True

        # Preserve conversation token
        if (
            universal_request.user_context
            and "conversation_token" in universal_request.user_context
        ):
            platform_specific["conversation_token"] = universal_request.user_context[
                "conversation_token"
            ]

        if platform_specific:
            universal_response.platform_specific = platform_specific

        # Convert response to Google format
        google_response = google_adapter.from_universal_response(universal_response)

        logger.info("Successfully processed Google Assistant request")

        return google_response

    except HTTPException:
        # Let HTTP exceptions propagate to return proper status codes
        raise
    except Exception as e:
        logger.error(
            "Error processing Google Assistant request: %s", str(e), exc_info=True
        )

        # Handle error gracefully with proper Google response format
        try:
            error_text = (
                "Извините, произошла ошибка. "
                "Попробуйте еще раз или скажите 'помощь'."
            )

            # Return proper error response based on request format
            if (
                google_data
                and isinstance(google_data, dict)
                and "queryResult" in google_data
            ):
                # Dialogflow format
                return {"fulfillmentText": error_text, "source": "astroloh"}

            # Google Actions format
            from app.models.google_models import (
                GoogleResponse,
                GoogleRichResponse,
                GoogleSimpleResponse,
            )

            simple_response = GoogleSimpleResponse(
                text_to_speech=error_text, display_text=error_text
            )

            rich_response = GoogleRichResponse(
                items=[{"simpleResponse": simple_response.model_dump()}]
            )

            error_response = GoogleResponse(
                expect_user_response=False, rich_response=rich_response
            )

            return error_response.model_dump(exclude_none=True)

        except Exception as error_handling_error:
            logger.error("Error in error handling: %s", error_handling_error)
            return {"fulfillmentText": "Internal server error"}


@router.get("/health")
async def google_assistant_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for Google Assistant service.
    """
    try:
        return {
            "status": "healthy",
            "service": "google_assistant",
            "platform": "google_assistant",
            "supported_formats": ["google_actions", "dialogflow_v2"],
            "components": {
                "adapter": "ok",
                "webhook": "ok",
                "multi_platform_handler": "ok",
            },
        }
    except Exception as e:
        logger.error("Google Assistant health check failed: %s", str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy") from e


@router.post("/actions")
async def google_actions_endpoint(
    request: Request, db: AsyncSession = Depends(get_database)
) -> Dict[str, Any]:
    """
    Dedicated endpoint for Google Actions (non-Dialogflow) requests.
    """
    # This is the same as the main webhook but with explicit Google Actions handling
    return await google_assistant_webhook(request, db)


@router.post("/dialogflow")
async def dialogflow_endpoint(
    request: Request, db: AsyncSession = Depends(get_database)
) -> Dict[str, Any]:
    """
    Dedicated endpoint for Dialogflow v2 fulfillment requests.
    """
    # This is the same as the main webhook but with explicit Dialogflow handling
    return await google_assistant_webhook(request, db)
