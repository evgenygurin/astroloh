"""
Lunar calendar API endpoints for moon phases and recommendations.
"""

from datetime import timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db_session
from app.services.lunar_calendar import LunarCalendar

router = APIRouter(prefix="/api/lunar", tags=["Lunar Calendar"])


# Pydantic models
class MoonPhase(BaseModel):
    date: str
    phase: str
    illumination: float
    phase_name: str
    recommendations: Optional[List[str]] = None


class LunarCalendarResponse(BaseModel):
    month: int
    year: int
    phases: List[MoonPhase]
    new_moons: List[str]
    full_moons: List[str]
    first_quarters: List[str]
    last_quarters: List[str]


class CurrentPhaseResponse(BaseModel):
    current_phase: MoonPhase
    next_phase: MoonPhase
    lunar_day: int
    recommendations: List[str]
    energy_level: str
    best_activities: List[str]


@router.get("/calendar/{year}/{month}", response_model=LunarCalendarResponse)
async def get_lunar_calendar(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get lunar calendar for a specific month and year."""
    # Validate year and month
    if year < 1900 or year > 2100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Year must be between 1900 and 2100"
        )
    
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12"
        )
    
    try:
        # Initialize lunar service
        lunar_service = LunarCalendar()
        
        # Get calendar data for the month
        calendar_data = lunar_service.get_monthly_lunar_calendar(year, month)
        
        # Process phases
        phases = []
        new_moons = []
        full_moons = []
        first_quarters = []
        last_quarters = []
        
        for day_data in calendar_data.get("days", []):
            moon_phase = MoonPhase(
                date=day_data["date"],
                phase=day_data["phase"],
                illumination=day_data["illumination"],
                phase_name=day_data["phase_name"],
                recommendations=day_data.get("recommendations", [])
            )
            phases.append(moon_phase)
            
            # Categorize major phases
            if day_data["phase_name"].lower() == "new moon":
                new_moons.append(day_data["date"])
            elif day_data["phase_name"].lower() == "full moon":
                full_moons.append(day_data["date"])
            elif day_data["phase_name"].lower() == "first quarter":
                first_quarters.append(day_data["date"])
            elif day_data["phase_name"].lower() == "last quarter":
                last_quarters.append(day_data["date"])
        
        return LunarCalendarResponse(
            month=month,
            year=year,
            phases=phases,
            new_moons=new_moons,
            full_moons=full_moons,
            first_quarters=first_quarters,
            last_quarters=last_quarters
        )
        
    except Exception as e:
        logger.error(f"Error generating lunar calendar: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate lunar calendar"
        )


@router.get("/current-phase", response_model=CurrentPhaseResponse)
async def get_current_phase(
    db: AsyncSession = Depends(get_db_session)
):
    """Get current moon phase and recommendations."""
    try:
        # Initialize lunar service
        lunar_service = LunarCalendar()
        
        # Get current phase data (dummy implementation)
        from datetime import datetime
        today = datetime.now()
        
        current_data = {
            "date": today.strftime("%Y-%m-%d"),
            "phase": "waxing_crescent",
            "illumination": 0.3,
            "phase_name": "Растущая Луна",
            "lunar_day": 7
        }
        next_data = {
            "date": (today + timedelta(days=7)).strftime("%Y-%m-%d"),
            "phase": "full",
            "illumination": 1.0,
            "phase_name": "Полнолуние"
        }
        
        # Get general recommendations (no authentication required)
        recommendations = lunar_service.get_lunar_recommendations(
            activity_type="general",
            target_date=today
        )
        
        # Get lunar day and energy information
        lunar_day = current_data.get("lunar_day", 7)
        lunar_service.get_lunar_day_info(today)
        energy_data = {"energy_level": "medium", "best_activities": ["meditation", "planning"]}
        
        current_phase = MoonPhase(
            date=current_data["date"],
            phase=current_data["phase"],
            illumination=current_data["illumination"],
            phase_name=current_data["phase_name"],
            recommendations=recommendations.get("general", [])
        )
        
        next_phase = MoonPhase(
            date=next_data["date"],
            phase=next_data["phase"],
            illumination=next_data["illumination"],
            phase_name=next_data["phase_name"]
        )
        
        return CurrentPhaseResponse(
            current_phase=current_phase,
            next_phase=next_phase,
            lunar_day=lunar_day,
            recommendations=recommendations.get("general_advice", ["Следуйте интуиции"]),
            energy_level=energy_data.get("energy_level", "medium"),
            best_activities=energy_data.get("best_activities", ["meditation", "planning"])
        )
        
    except Exception as e:
        logger.error(f"Error getting current phase: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get current moon phase"
        )


@router.get("/phase/{phase_name}/recommendations")
async def get_phase_recommendations(
    phase_name: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get recommendations for a specific moon phase."""
    # Validate phase name
    valid_phases = ["new", "waxing_crescent", "first_quarter", "waxing_gibbous", 
                   "full", "waning_gibbous", "last_quarter", "waning_crescent"]
    
    if phase_name.lower() not in valid_phases:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid phase name. Must be one of: {', '.join(valid_phases)}"
        )
    
    try:
        # Initialize lunar service
        lunar_service = LunarCalendar()
        
        # Get recommendations for the phase (simplified)
        from datetime import datetime
        recommendations = lunar_service.get_lunar_recommendations(
            activity_type=phase_name,
            target_date=datetime.now()
        )
        
        return {
            "phase": phase_name,
            "general_recommendations": recommendations.get("general", []),
            "specific_recommendations": recommendations.get("specific", []),
            "activities": recommendations.get("activities", []),
            "avoid": recommendations.get("avoid", [])
        }
        
    except Exception as e:
        logger.error(f"Error getting phase recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get phase recommendations"
        )


@router.get("/lunar-day/{day}")
async def get_lunar_day_info(
    day: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get information about a specific lunar day (1-30)."""
    if day < 1 or day > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lunar day must be between 1 and 30"
        )
    
    try:
        # Initialize lunar service
        lunar_service = LunarCalendar()
        
        # Get lunar day information (simplified)
        from datetime import datetime
        day_info = lunar_service.get_lunar_day_info(datetime.now())
        
        return {
            "lunar_day": day,
            "energy_level": day_info.get("energy_level", "medium"),
            "characteristics": day_info.get("characteristics", []),
            "best_activities": day_info.get("best_activities", []),
            "avoid_activities": day_info.get("avoid_activities", []),
            "color": day_info.get("color"),
            "stone": day_info.get("stone"),
            "keywords": day_info.get("keywords", [])
        }
        
    except Exception as e:
        logger.error(f"Error getting lunar day info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get lunar day information"
        )