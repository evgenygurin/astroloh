"""
Модели данных для транзитов, прогрессий и других продвинутых астрологических техник.
"""
from datetime import date, datetime, time
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TransitType(str, Enum):
    """Типы транзитов."""
    CURRENT = "current"
    PROGRESSIONS = "progressions"
    SOLAR_RETURN = "solar_return"
    LUNAR_RETURN = "lunar_return"


class AspectType(str, Enum):
    """Типы аспектов."""
    CONJUNCTION = "Соединение"
    SEXTILE = "Секстиль"
    SQUARE = "Квадрат"
    TRINE = "Трин"
    OPPOSITION = "Оппозиция"


class TimingPhase(str, Enum):
    """Фазы тайминга транзитов."""
    EXACT = "точный"
    CLOSE = "близкий"
    APPROACHING = "приближающийся"
    WEAK = "слабый"


class PlanetPosition(BaseModel):
    """Позиция планеты."""
    longitude: float = Field(..., description="Эклиптическая долгота в градусах")
    sign: str = Field(..., description="Знак зодиака")
    degree_in_sign: float = Field(..., description="Градус в знаке")
    sign_number: int = Field(..., description="Номер знака (0-11)")


class TransitAspect(BaseModel):
    """Транзитный аспект между планетами."""
    transit_planet: str = Field(..., description="Транзитная планета")
    natal_planet: str = Field(..., description="Натальная планета")
    aspect: AspectType = Field(..., description="Тип аспекта")
    aspect_angle: float = Field(..., description="Угол аспекта")
    exact_angle: float = Field(..., description="Точный угол между планетами")
    orb: float = Field(..., description="Орб аспекта")
    strength: float = Field(..., description="Сила аспекта (0-10)")
    
    transit_position: PlanetPosition = Field(..., description="Позиция транзитной планеты")
    natal_position: PlanetPosition = Field(..., description="Позиция натальной планеты")
    
    timing: Optional[Dict[str, str]] = Field(None, description="Информация о тайминге")
    interpretation: Optional[Dict[str, str]] = Field(None, description="Интерпретация аспекта")


class TransitTiming(BaseModel):
    """Информация о тайминге транзита."""
    phase: TimingPhase = Field(..., description="Фаза транзита")
    description: str = Field(..., description="Описание фазы")


class TransitInterpretation(BaseModel):
    """Интерпретация транзитного аспекта."""
    summary: str = Field(..., description="Краткое описание")
    influence: str = Field(..., description="Влияние на жизнь")
    nature: str = Field(..., description="Характер аспекта")
    advice: str = Field(..., description="Совет по аспекту")


class TransitSummary(BaseModel):
    """Краткое резюме транзитов."""
    overall_influence: str = Field(..., description="Общее влияние периода")
    dominant_planet: Optional[str] = Field(None, description="Доминирующая планета")
    main_themes: List[str] = Field(..., description="Основные темы периода")
    transit_count: int = Field(..., description="Количество значимых транзитов")
    advice: str = Field(..., description="Общий совет")


class BirthInfo(BaseModel):
    """Информация о рождении."""
    date: str = Field(..., description="Дата рождения (ISO format)")
    time: str = Field(..., description="Время рождения (HH:MM)")
    place: Dict[str, float] = Field(..., description="Место рождения (latitude, longitude)")
    timezone: Optional[str] = Field("UTC", description="Временная зона")


class CurrentTransits(BaseModel):
    """Модель для текущих транзитов."""
    calculation_date: str = Field(..., description="Дата расчета")
    birth_info: BirthInfo = Field(..., description="Информация о рождении")
    
    natal_positions: Dict[str, PlanetPosition] = Field(..., description="Натальные позиции планет")
    current_positions: Dict[str, PlanetPosition] = Field(..., description="Текущие позиции планет")
    
    all_transits: List[TransitAspect] = Field(..., description="Все транзитные аспекты")
    significant_transits: List[TransitAspect] = Field(..., description="Значимые транзиты")
    
    interpretation: Dict[str, str] = Field(..., description="Общая интерпретация")
    summary: TransitSummary = Field(..., description="Краткое резюме")


class ProgressionMovement(BaseModel):
    """Движение планеты в прогрессии."""
    planet: str = Field(..., description="Планета")
    natal_position: PlanetPosition = Field(..., description="Натальная позиция")
    progressed_position: PlanetPosition = Field(..., description="Прогрессивная позиция")
    movement_degrees: float = Field(..., description="Движение в градусах")
    interpretation: Dict[str, str] = Field(..., description="Интерпретация движения")


class Progressions(BaseModel):
    """Модель для прогрессий."""
    calculation_date: str = Field(..., description="Дата расчета")
    birth_info: BirthInfo = Field(..., description="Информация о рождении")
    progression_date: str = Field(..., description="Прогрессивная дата")
    years_lived: float = Field(..., description="Прожитые годы")
    
    natal_positions: Dict[str, PlanetPosition] = Field(..., description="Натальные позиции")
    progressed_positions: Dict[str, PlanetPosition] = Field(..., description="Прогрессивные позиции")
    
    progressions: List[ProgressionMovement] = Field(..., description="Прогрессивные движения")
    interpretation: Dict[str, str] = Field(..., description="Общая интерпретация")


class SolarReturn(BaseModel):
    """Модель для соляра (солнечного возвращения)."""
    solar_year: int = Field(..., description="Год соляра")
    solar_date: str = Field(..., description="Дата солнечного возвращения")
    birth_info: BirthInfo = Field(..., description="Информация о рождении")
    
    solar_positions: Dict[str, PlanetPosition] = Field(..., description="Позиции планет в соляре")
    solar_houses: Dict[str, Any] = Field(..., description="Дома в соляре")
    
    interpretation: Dict[str, str] = Field(..., description="Интерпретация соляра")


class LunarReturn(BaseModel):
    """Модель для лунара (лунного возвращения)."""
    lunar_date: str = Field(..., description="Дата лунного возвращения")
    target_date: str = Field(..., description="Целевая дата")
    birth_info: BirthInfo = Field(..., description="Информация о рождении")
    
    lunar_positions: Dict[str, PlanetPosition] = Field(..., description="Позиции планет в лунаре")
    interpretation: Dict[str, str] = Field(..., description="Интерпретация лунара")


class TransitRequest(BaseModel):
    """Запрос на расчет транзитов."""
    birth_date: date = Field(..., description="Дата рождения")
    birth_time: Optional[time] = Field(None, description="Время рождения")
    birth_place: Optional[Dict[str, float]] = Field(None, description="Место рождения")
    
    transit_type: TransitType = Field(TransitType.CURRENT, description="Тип транзита")
    target_date: Optional[datetime] = Field(None, description="Целевая дата/время")
    target_year: Optional[int] = Field(None, description="Целевой год (для соляра)")


class TransitResponse(BaseModel):
    """Ответ с транзитами."""
    success: bool = Field(..., description="Успешность расчета")
    transit_type: TransitType = Field(..., description="Тип транзита")
    
    # Один из типов данных в зависимости от transit_type
    current_transits: Optional[CurrentTransits] = None
    progressions: Optional[Progressions] = None
    solar_return: Optional[SolarReturn] = None
    lunar_return: Optional[LunarReturn] = None
    
    error: Optional[str] = Field(None, description="Сообщение об ошибке")
    details: Optional[str] = Field(None, description="Детали ошибки")


class TransitAnalysisResult(BaseModel):
    """Результат анализа транзитов для интеграции с диалогами."""
    has_significant_transits: bool = Field(..., description="Есть ли значимые транзиты")
    dominant_themes: List[str] = Field(..., description="Доминирующие темы")
    period_influence: str = Field(..., description="Влияние периода")
    recommendations: List[str] = Field(..., description="Рекомендации")
    
    # Краткое описание для голосового ответа
    voice_summary: str = Field(..., description="Краткое описание для голоса")
    detailed_explanation: str = Field(..., description="Подробное объяснение")


# Константы для использования в сервисах
PLANET_WEIGHTS = {
    "Sun": 10, "Moon": 9, "Mercury": 6, "Venus": 7, "Mars": 7,
    "Jupiter": 8, "Saturn": 9, "Uranus": 6, "Neptune": 5, "Pluto": 7
}

ASPECT_WEIGHTS = {
    0: 10,    # Соединение
    90: 8,    # Квадрат
    180: 8,   # Оппозиция
    120: 6,   # Трин
    60: 4     # Секстиль
}

TRANSIT_ORBS = {
    0: 3,     # Соединение
    60: 2,    # Секстиль
    90: 3,    # Квадрат
    120: 3,   # Трин
    180: 3,   # Оппозиция
}

# Интерпретации для быстрого доступа
PLANET_THEMES = {
    "Sun": ["личность", "творчество", "лидерство", "самовыражение"],
    "Moon": ["эмоции", "семья", "интуиция", "настроение"],
    "Mercury": ["общение", "учеба", "решения", "информация"],
    "Venus": ["любовь", "деньги", "красота", "гармония"],
    "Mars": ["активность", "конфликты", "инициатива", "страсть"],
    "Jupiter": ["расширение", "путешествия", "удача", "философия"],
    "Saturn": ["дисциплина", "работа", "структура", "ограничения"],
    "Uranus": ["изменения", "свобода", "инновации", "неожиданность"],
    "Neptune": ["духовность", "иллюзии", "творчество", "мистика"],
    "Pluto": ["трансформация", "власть", "возрождение", "глубина"],
}

ASPECT_NATURES = {
    "Соединение": "интенсивное, концентрированное влияние",
    "Секстиль": "гармоничные возможности, легкие изменения",
    "Квадрат": "напряжение, вызовы, необходимость действий",
    "Трин": "благоприятное течение, естественные возможности",
    "Оппозиция": "поляризация, необходимость баланса",
}