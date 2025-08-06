"""
Astrology API endpoints for horoscopes, natal charts, and compatibility.
"""

from datetime import datetime
from typing import Dict, Optional, Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from loguru import logger
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
    latitude: float  # Latitude in degrees
    longitude: float  # Longitude in degrees
    timezone: Optional[str] = "Europe/Moscow"  # Timezone string


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
    lucky_numbers: Optional[List[int]] = None
    lucky_color: Optional[str] = None


class CompatibilityRequest(BaseModel):
    person1: BirthData
    person2: BirthData


class CompatibilityResponse(BaseModel):
    compatibility_score: int
    aspects: Dict[str, Any]
    strengths: List[str]
    challenges: List[str]
    advice: str


@router.post("/natal-chart", response_model=NatalChartResponse)
async def get_natal_chart(
    birth_data: BirthData,
    current_user: User = Depends(get_current_user)
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
            birth_place={"latitude": birth_data.latitude, "longitude": birth_data.longitude},
            timezone_str=birth_data.timezone or "Europe/Moscow"
        )
        
        # Generate interpretation (use existing interpretation from chart data)
        interpretation = chart_data.get("interpretation", "Натальная карта рассчитана успешно.")
        
        # Log the request
        logger.info("Natal chart calculated for authenticated user")
        
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
    type: str  # daily, weekly, monthly
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
    current_user: User = Depends(get_current_user)
):
    """Calculate compatibility between two people."""
    try:
        # Log compatibility request
        logger.info("Compatibility calculation requested for authenticated user")
        
        # Generate interpretation (dummy implementation for now)
        # TODO: Implement actual compatibility calculation using birth data  
        interpretation = {
            "strengths": ["Совместимость между партнерами хорошая"],
            "challenges": ["Необходимо работать над общением"],
            "advice": "Рекомендуется больше времени проводить вместе"
        }
        
        # Ensure proper types for response
        strengths = interpretation.get("strengths", [])
        if not isinstance(strengths, list):
            strengths = [str(strengths)] if strengths else []
            
        challenges = interpretation.get("challenges", [])
        if not isinstance(challenges, list):
            challenges = [str(challenges)] if challenges else []
        
        return CompatibilityResponse(
            compatibility_score=70,  # Default compatibility score for now
            aspects={},  # Default empty aspects for now
            strengths=strengths,
            challenges=challenges,
            advice=str(interpretation.get("advice", ""))
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