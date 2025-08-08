"""
Security and GDPR compliance API endpoints.
"""

import uuid
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database
from app.services.gdpr_compliance import GDPRComplianceService
from app.services.user_manager import UserManager

router = APIRouter(prefix="/security", tags=["Security & GDPR"])


class ConsentUpdateRequest(BaseModel):
    """Request model for updating data consent."""

    consent: bool
    retention_days: int = 365
    consent_details: Optional[Dict[str, bool]] = None


class DataRectificationRequest(BaseModel):
    """Request model for data rectification."""

    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    birth_location: Optional[str] = None
    zodiac_sign: Optional[str] = None
    gender: Optional[str] = None


class ProcessingRestrictionRequest(BaseModel):
    """Request model for processing restriction."""

    restrict: bool
    reason: Optional[str] = None


@router.get("/user/{user_id}/data-summary")
async def get_user_data_summary(
    user_id: str, db: AsyncSession = Depends(get_database)
):
    """
    Get user data summary (GDPR Article 15 - Right of access).

    Args:
        user_id: Yandex user ID
        db: Database session

    Returns:
        Complete summary of user's personal data
    """
    try:
        # Find user by Yandex ID
        users = await db.execute(
            "SELECT id FROM users WHERE yandex_user_id = :yandex_id",
            {"yandex_id": user_id},
        )
        user_record = users.fetchone()

        if not user_record:
            raise HTTPException(status_code=404, detail="User not found")

        gdpr_service = GDPRComplianceService(db)
        summary = await gdpr_service.get_user_data_summary(
            uuid.UUID(user_record[0])
        )

        if not summary:
            raise HTTPException(status_code=404, detail="User data not found")

        return summary

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get user data: {str(e)}"
        )


@router.get("/user/{user_id}/export")
async def export_user_data(
    user_id: str,
    format_type: str = "json",
    db: AsyncSession = Depends(get_database),
):
    """
    Export all user data (GDPR Article 20 - Right to data portability).

    Args:
        user_id: Yandex user ID
        format_type: Export format (json, csv)
        db: Database session

    Returns:
        Complete export of user's data
    """
    try:
        # Find user by Yandex ID
        users = await db.execute(
            "SELECT id FROM users WHERE yandex_user_id = :yandex_id",
            {"yandex_id": user_id},
        )
        user_record = users.fetchone()

        if not user_record:
            raise HTTPException(status_code=404, detail="User not found")

        gdpr_service = GDPRComplianceService(db)
        export_data = await gdpr_service.export_user_data(
            uuid.UUID(user_record[0]), format_type
        )

        if not export_data:
            raise HTTPException(status_code=404, detail="No data to export")

        return export_data

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export data: {str(e)}"
        )


@router.post("/user/{user_id}/consent")
async def update_consent(
    user_id: str,
    consent_data: ConsentUpdateRequest,
    db: AsyncSession = Depends(get_database),
):
    """
    Update data processing consent (GDPR Article 7 - Consent).

    Args:
        user_id: Yandex user ID
        consent_data: Consent update data
        db: Database session

    Returns:
        Success confirmation
    """
    try:
        # Find user by Yandex ID
        users = await db.execute(
            "SELECT id FROM users WHERE yandex_user_id = :yandex_id",
            {"yandex_id": user_id},
        )
        user_record = users.fetchone()

        if not user_record:
            raise HTTPException(status_code=404, detail="User not found")

        gdpr_service = GDPRComplianceService(db)
        success = await gdpr_service.update_consent(
            uuid.UUID(user_record[0]),
            consent_data.consent,
            consent_data.retention_days,
            consent_data.consent_details,
        )

        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to update consent"
            )

        return {
            "status": "success",
            "message": "Consent updated successfully",
            "consent": consent_data.consent,
            "retention_days": consent_data.retention_days,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update consent: {str(e)}"
        )


@router.post("/user/{user_id}/rectify")
async def rectify_user_data(
    user_id: str,
    rectification_data: DataRectificationRequest,
    db: AsyncSession = Depends(get_database),
):
    """
    Rectify user data (GDPR Article 16 - Right to rectification).

    Args:
        user_id: Yandex user ID
        rectification_data: Data to be corrected
        db: Database session

    Returns:
        Success confirmation
    """
    try:
        # Find user by Yandex ID
        users = await db.execute(
            "SELECT id FROM users WHERE yandex_user_id = :yandex_id",
            {"yandex_id": user_id},
        )
        user_record = users.fetchone()

        if not user_record:
            raise HTTPException(status_code=404, detail="User not found")

        # Convert to dict for processing
        correction_data = rectification_data.dict(exclude_unset=True)

        gdpr_service = GDPRComplianceService(db)
        success = await gdpr_service.rectify_user_data(
            uuid.UUID(user_record[0]), correction_data
        )

        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to rectify data"
            )

        return {
            "status": "success",
            "message": "Data rectified successfully",
            "updated_fields": list(correction_data.keys()),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to rectify data: {str(e)}"
        )


@router.post("/user/{user_id}/delete-request")
async def request_data_deletion(
    user_id: str,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_database),
):
    """
    Request data deletion (GDPR Article 17 - Right to erasure).

    Args:
        user_id: Yandex user ID
        reason: Reason for deletion
        db: Database session

    Returns:
        Verification code for confirming deletion
    """
    try:
        # Find user by Yandex ID
        users = await db.execute(
            "SELECT id FROM users WHERE yandex_user_id = :yandex_id",
            {"yandex_id": user_id},
        )
        user_record = users.fetchone()

        if not user_record:
            raise HTTPException(status_code=404, detail="User not found")

        gdpr_service = GDPRComplianceService(db)
        verification_code = await gdpr_service.request_data_deletion(
            uuid.UUID(user_record[0]), reason
        )

        return {
            "status": "success",
            "message": "Deletion request created. Please confirm with verification code.",
            "verification_code": verification_code,
            "instructions": "Use the verification code to confirm deletion via /confirm-deletion endpoint",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create deletion request: {str(e)}",
        )


@router.post("/user/{user_id}/confirm-deletion")
async def confirm_data_deletion(
    user_id: str,
    verification_code: str,
    db: AsyncSession = Depends(get_database),
):
    """
    Confirm data deletion with verification code.

    Args:
        user_id: Yandex user ID
        verification_code: Verification code from deletion request
        db: Database session

    Returns:
        Deletion confirmation
    """
    try:
        # Find user by Yandex ID
        users = await db.execute(
            "SELECT id FROM users WHERE yandex_user_id = :yandex_id",
            {"yandex_id": user_id},
        )
        user_record = users.fetchone()

        if not user_record:
            raise HTTPException(status_code=404, detail="User not found")

        gdpr_service = GDPRComplianceService(db)
        success = await gdpr_service.confirm_data_deletion(
            uuid.UUID(user_record[0]), verification_code
        )

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Invalid verification code or deletion request not found",
            )

        return {
            "status": "success",
            "message": "User data has been permanently deleted",
            "deleted_at": "2024-01-01T00:00:00Z",  # Current timestamp would be added
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to confirm deletion: {str(e)}"
        )


@router.post("/user/{user_id}/restrict-processing")
async def restrict_processing(
    user_id: str,
    restriction_data: ProcessingRestrictionRequest,
    db: AsyncSession = Depends(get_database),
):
    """
    Restrict or unrestrict data processing (GDPR Article 18).

    Args:
        user_id: Yandex user ID
        restriction_data: Processing restriction data
        db: Database session

    Returns:
        Success confirmation
    """
    try:
        # Find user by Yandex ID
        users = await db.execute(
            "SELECT id FROM users WHERE yandex_user_id = :yandex_id",
            {"yandex_id": user_id},
        )
        user_record = users.fetchone()

        if not user_record:
            raise HTTPException(status_code=404, detail="User not found")

        gdpr_service = GDPRComplianceService(db)
        success = await gdpr_service.restrict_processing(
            uuid.UUID(user_record[0]),
            restriction_data.restrict,
            restriction_data.reason,
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update processing restriction",
            )

        return {
            "status": "success",
            "message": f"Processing {'restricted' if restriction_data.restrict else 'unrestricted'}",
            "restricted": restriction_data.restrict,
            "reason": restriction_data.reason,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to restrict processing: {str(e)}"
        )


@router.get("/compliance-report")
async def get_compliance_report(
    days: int = 30, db: AsyncSession = Depends(get_database)
):
    """
    Generate GDPR compliance report for administrators.

    Args:
        days: Number of days to include in report
        db: Database session

    Returns:
        Compliance report
    """
    try:
        from datetime import datetime, timedelta

        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()

        gdpr_service = GDPRComplianceService(db)
        report = await gdpr_service.generate_compliance_report(
            start_date, end_date
        )

        return report

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate report: {str(e)}"
        )


@router.post("/cleanup-expired-data")
async def cleanup_expired_data(db: AsyncSession = Depends(get_database)):
    """
    Clean up expired user data according to retention policies.

    Args:
        db: Database session

    Returns:
        Cleanup summary
    """
    try:
        user_manager = UserManager(db)
        deleted_count = await user_manager.cleanup_expired_data()

        return {
            "status": "success",
            "message": "Expired data cleanup completed",
            "deleted_users": deleted_count,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to cleanup data: {str(e)}"
        )
