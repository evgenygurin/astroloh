"""
Astrology API endpoints for horoscopes, natal charts, and compatibility.
"""

from datetime import datetime
from typing import Dict, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db_session
from app.services.astrology_calculator import AstrologyCalculator
from app.services.horoscope_generator import HoroscopeGenerator, HoroscopePeriod
from app.models.yandex_models import YandexZodiacSign
from app.services.natal_chart import NatalChartCalculator
from app.models.database import User
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/astrology", tags=["Astrology"])


# Pydantic models
class BirthData(BaseModel):
    date: str  # Format: YYYY-MM-DD
    time: str  # Format: HH:MM
    location: str  # City name or coordinates


class NatalChartResponse(BaseModel):
    chart_data: Dict[str, Any]
    aspects: Dict[str, Any]
    houses: Dict[str, Any]
    interpretation: str


class HoroscopeResponse(BaseModel):
    sign: str
    period: str
    date: str
    horoscope: str
    lucky_numbers: Optional[list] = None
    lucky_color: Optional[str] = None


class CompatibilityRequest(BaseModel):
    person1: BirthData
    person2: BirthData


class CompatibilityResponse(BaseModel):
    compatibility_score: int
    aspects: Dict[str, Any]
    strengths: list[str]
    challenges: list[str]
    advice: str


@router.post("/natal-chart", response_model=NatalChartResponse)
async def get_natal_chart(
    birth_data: BirthData,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Calculate natal chart for given birth data."""
    try:
        # Parse birth date and time
        birth_datetime = datetime.strptime(
            f"{birth_data.date} {birth_data.time}",
            "%Y-%m-%d %H:%M"
        )
        
        # Initialize services
        natal_service = NatalChartCalculator()
        
        # Calculate natal chart
        chart_data = natal_service.calculate_natal_chart(
            birth_date=birth_datetime.date(),
            birth_time=birth_datetime.time(),
            birth_place={"location_string": birth_data.location}
        )
        
        # Generate interpretation (use existing interpretation from chart data)
        interpretation = chart_data.get("interpretation", "Натальная карта рассчитана успешно.")
        
        # Log the request
        logger.info(f"Natal chart calculated for user {current_user.id}")
        
        return NatalChartResponse(
            chart_data=chart_data.get("planets", {}),
            aspects=chart_data.get("aspects", {}),
            houses=chart_data.get("houses", {}),
            interpretation=interpretation
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date/time format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error calculating natal chart: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate natal chart"
        )


@router.get("/horoscope/{sign}/{type}", response_model=HoroscopeResponse)
async def get_horoscope(
    sign: str,
    type: str,  # daily, weekly, monthly
    db: AsyncSession = Depends(get_db_session)
):
    """Get horoscope for a specific zodiac sign and period."""
    # Validate sign
    valid_signs = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
    ]
    
    if sign.lower() not in valid_signs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid zodiac sign. Must be one of: {', '.join(valid_signs)}"
        )
    
    # Validate type
    if type not in ["daily", "weekly", "monthly"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Type must be 'daily', 'weekly', or 'monthly'"
        )
    
    try:
        # Initialize horoscope generator
        horoscope_generator = HoroscopeGenerator()
        
        # Map English sign names to Russian YandexZodiacSign enum values
        sign_mapping = {
            "aries": YandexZodiacSign.ARIES,
            "taurus": YandexZodiacSign.TAURUS,
            "gemini": YandexZodiacSign.GEMINI,
            "cancer": YandexZodiacSign.CANCER,
            "leo": YandexZodiacSign.LEO,
            "virgo": YandexZodiacSign.VIRGO,
            "libra": YandexZodiacSign.LIBRA,
            "scorpio": YandexZodiacSign.SCORPIO,
            "sagittarius": YandexZodiacSign.SAGITTARIUS,
            "capricorn": YandexZodiacSign.CAPRICORN,
            "aquarius": YandexZodiacSign.AQUARIUS,
            "pisces": YandexZodiacSign.PISCES,
        }
        
        # Map period types
        period_mapping = {
            "daily": HoroscopePeriod.DAILY,
            "weekly": HoroscopePeriod.WEEKLY,
            "monthly": HoroscopePeriod.MONTHLY,
        }
        
        zodiac_sign_enum = sign_mapping.get(sign.lower())
        period_enum = period_mapping.get(type.lower(), HoroscopePeriod.DAILY)
        
        if not zodiac_sign_enum:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid zodiac sign: {sign}"
            )
            
        # Generate horoscope using correct method name
        horoscope_data = horoscope_generator.generate_personalized_horoscope(
            zodiac_sign=zodiac_sign_enum,
            period=period_enum
        )
        
        return HoroscopeResponse(
            sign=sign.lower(),
            period=type,
            date=datetime.now().strftime("%Y-%m-%d"),
            horoscope=horoscope_data.get("general_forecast", horoscope_data.get("forecast", "Гороскоп недоступен")),
            lucky_numbers=horoscope_data.get("lucky_numbers", []),
            lucky_color=horoscope_data.get("lucky_colors", ["белый"])[0] if horoscope_data.get("lucky_colors") else "белый"
        )
        
    except Exception as e:
        logger.error(f"Error generating horoscope: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate horoscope"
        )


@router.post("/compatibility", response_model=CompatibilityResponse)
async def get_compatibility(
    request: CompatibilityRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Calculate compatibility between two people."""
    try:
        # Parse birth data for both people
        person1_datetime = datetime.strptime(
            f"{request.person1.date} {request.person1.time}",
            "%Y-%m-%d %H:%M"
        )
        person2_datetime = datetime.strptime(
            f"{request.person2.date} {request.person2.time}",
            "%Y-%m-%d %H:%M"
        )
        
        # Initialize services
        astro_calculator = AstrologyCalculator()
        natal_service = NatalChartCalculator()
        
        # Calculate natal charts for both people
        person1_chart = natal_service.calculate_natal_chart(
            birth_date=person1_datetime.date(),
            birth_time=person1_datetime.time(),
            birth_place={"location_string": request.person1.location}
        )
        person2_chart = natal_service.calculate_natal_chart(
            birth_date=person2_datetime.date(),
            birth_time=person2_datetime.time(),
            birth_place={"location_string": request.person2.location}
        )
        
        # Calculate compatibility
        compatibility_data = astro_calculator.calculate_synastry(
            person1_chart, person2_chart
        )
        
        # Generate interpretation (dummy implementation for now)
        interpretation = {
            "strengths": ["Совместимость между партнерами хорошая"],
            "challenges": ["Необходимо работать над общением"],
            "advice": "Рекомендуется больше времени проводить вместе"
        }
        
        return CompatibilityResponse(
            compatibility_score=compatibility_data.get("overall_score", 70),
            aspects=compatibility_data.get("aspects", {}),
            strengths=interpretation.get("strengths", []),
            challenges=interpretation.get("challenges", []),
            advice=interpretation.get("advice", "")
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date/time format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error calculating compatibility: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate compatibility"
        )