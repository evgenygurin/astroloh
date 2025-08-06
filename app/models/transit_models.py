"""
Модели данных для транзитов, прогрессий, соляров и лунаров.
"""
from datetime import date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TransitAspect(BaseModel):
    """Модель транзитного аспекта."""
    
    transit_planet: str = Field(..., description="Транзитная планета")
    natal_planet: str = Field(..., description="Натальная планета")
    aspect: str = Field(..., description="Название аспекта")
    angle: float = Field(..., description="Угол аспекта")
    orb: float = Field(..., description="Орб аспекта")
    exact_angle: float = Field(..., description="Точный угол между планетами")
    influence: str = Field(..., description="Описание влияния")
    strength: str = Field(..., description="Сила аспекта")
    nature: str = Field(..., description="Природа аспекта")


class TransitData(BaseModel):
    """Модель данных транзитов."""
    
    date: str = Field(..., description="Дата транзитов")
    active_transits: List[TransitAspect] = Field(default_factory=list, description="Активные транзиты")
    approaching_transits: List[TransitAspect] = Field(default_factory=list, description="Приближающиеся транзиты")
    summary: str = Field(..., description="Краткое резюме транзитов")
    daily_influences: List[str] = Field(default_factory=list, description="Ключевые влияния дня")


class ProgressedPlanet(BaseModel):
    """Модель прогрессированной планеты."""
    
    sign: str = Field(..., description="Знак прогрессированной планеты")
    meaning: str = Field(..., description="Значение позиции")


class ProgressionInterpretation(BaseModel):
    """Модель интерпретации прогрессий."""
    
    current_age: int = Field(..., description="Текущий возраст")
    life_stage: str = Field(..., description="Этап жизни")
    progressed_sun: ProgressedPlanet = Field(..., description="Прогрессированное Солнце")
    progressed_moon: ProgressedPlanet = Field(..., description="Прогрессированная Луна")
    general_trends: List[str] = Field(default_factory=list, description="Общие тенденции")


class ProgressionData(BaseModel):
    """Модель данных прогрессий."""
    
    birth_date: str = Field(..., description="Дата рождения")
    progression_date: str = Field(..., description="Дата прогрессии")
    days_progressed: int = Field(..., description="Количество прогрессированных дней")
    progressed_planets: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Прогрессированные планеты")
    progressed_houses: Dict[int, Dict[str, Any]] = Field(default_factory=dict, description="Прогрессированные дома")
    interpretation: ProgressionInterpretation = Field(..., description="Интерпретация прогрессий")
    key_changes: List[str] = Field(default_factory=list, description="Ключевые изменения")


class SolarReturnInterpretation(BaseModel):
    """Модель интерпретации соляра."""
    
    year_theme: str = Field(..., description="Тема года")
    key_areas: List[str] = Field(default_factory=list, description="Ключевые сферы жизни")
    challenges: List[str] = Field(default_factory=list, description="Вызовы года")
    opportunities: List[str] = Field(default_factory=list, description="Возможности года")


class SolarReturnData(BaseModel):
    """Модель данных соляра."""
    
    year: int = Field(..., description="Год соляра")
    date: str = Field(..., description="Дата соляра")
    planets: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Позиции планет в соляре")
    houses: Dict[int, Dict[str, Any]] = Field(default_factory=dict, description="Дома соляра") 
    interpretation: SolarReturnInterpretation = Field(..., description="Интерпретация соляра")
    themes: List[str] = Field(default_factory=list, description="Темы года")


class LunarReturnInterpretation(BaseModel):
    """Модель интерпретации лунара."""
    
    emotional_theme: str = Field(..., description="Эмоциональная тема месяца")
    action_theme: str = Field(..., description="Тема активности")
    general_advice: str = Field(..., description="Общий совет")


class LunarReturnData(BaseModel):
    """Модель данных лунара."""
    
    month: int = Field(..., description="Месяц лунара")
    year: int = Field(..., description="Год лунара")
    new_moon_date: str = Field(..., description="Дата новолуния")
    planets: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Позиции планет в лунаре")
    houses: Dict[int, Dict[str, Any]] = Field(default_factory=dict, description="Дома лунара")
    interpretation: LunarReturnInterpretation = Field(..., description="Интерпретация лунара")
    monthly_themes: List[str] = Field(default_factory=list, description="Темы месяца")


class TransitRequest(BaseModel):
    """Модель запроса на транзиты."""
    
    birth_date: date = Field(..., description="Дата рождения")
    birth_time: Optional[str] = Field(None, description="Время рождения")
    birth_place: Optional[Dict[str, float]] = Field(None, description="Место рождения")
    transit_date: Optional[date] = Field(None, description="Дата для расчета транзитов")


class ProgressionRequest(BaseModel):
    """Модель запроса на прогрессии."""
    
    birth_date: date = Field(..., description="Дата рождения")
    birth_time: Optional[str] = Field(None, description="Время рождения")
    birth_place: Optional[Dict[str, float]] = Field(None, description="Место рождения")
    progression_date: Optional[date] = Field(None, description="Дата для расчета прогрессий")


class SolarReturnRequest(BaseModel):
    """Модель запроса на соляр."""
    
    birth_date: date = Field(..., description="Дата рождения")
    year: int = Field(..., description="Год соляра")
    birth_place: Optional[Dict[str, float]] = Field(None, description="Место рождения")


class LunarReturnRequest(BaseModel):
    """Модель запроса на лунар."""
    
    birth_date: date = Field(..., description="Дата рождения")
    month: int = Field(..., ge=1, le=12, description="Месяц лунара")
    year: int = Field(..., description="Год лунара")
    birth_place: Optional[Dict[str, float]] = Field(None, description="Место рождения")


class TransitAnalysisResult(BaseModel):
    """Результат анализа транзитов."""
    
    transit_data: TransitData = Field(..., description="Данные транзитов")
    natal_planets: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Натальные планеты")
    recommendations: List[str] = Field(default_factory=list, description="Рекомендации")
    energy_level: str = Field(..., description="Уровень энергии периода")
    focus_areas: List[str] = Field(default_factory=list, description="Области фокуса")


class ProgressionAnalysisResult(BaseModel):
    """Результат анализа прогрессий."""
    
    progression_data: ProgressionData = Field(..., description="Данные прогрессий")
    life_phase_analysis: str = Field(..., description="Анализ жизненной фазы")
    development_areas: List[str] = Field(default_factory=list, description="Области развития")
    spiritual_guidance: str = Field(..., description="Духовное руководство")


class YearlyForecast(BaseModel):
    """Годовой прогноз на основе соляра."""
    
    solar_data: SolarReturnData = Field(..., description="Данные соляра")
    monthly_highlights: Dict[int, str] = Field(default_factory=dict, description="Ключевые моменты по месяцам")
    seasonal_themes: Dict[str, str] = Field(default_factory=dict, description="Сезонные темы")
    success_indicators: List[str] = Field(default_factory=list, description="Индикаторы успеха")
    caution_periods: List[str] = Field(default_factory=list, description="Периоды осторожности")


class MonthlyGuidance(BaseModel):
    """Месячное руководство на основе лунара."""
    
    lunar_data: LunarReturnData = Field(..., description="Данные лунара")
    weekly_rhythms: Dict[int, str] = Field(default_factory=dict, description="Недельные ритмы")
    emotional_cycles: List[str] = Field(default_factory=list, description="Эмоциональные циклы")
    optimal_actions: List[str] = Field(default_factory=list, description="Оптимальные действия")
    energy_management: str = Field(..., description="Управление энергией")