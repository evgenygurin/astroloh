"""
Тесты для моделей транзитов.
"""
import pytest
from datetime import date, time
from pydantic import ValidationError

from app.models.transit_models import (
    AspectType,
    BirthInfo,
    CurrentTransits,
    LunarReturn,
    PlanetPosition,
    Progressions,
    ProgressionMovement,
    SolarReturn,
    TimingPhase,
    TransitAnalysisResult,
    TransitAspect,
    TransitRequest,
    TransitResponse,
    TransitSummary,
    TransitType,
)


class TestTransitModels:
    """Тесты для моделей транзитов."""

    def test_planet_position_model(self):
        """Тест модели позиции планеты."""
        position = PlanetPosition(
            longitude=123.45,
            sign="Лев",
            degree_in_sign=3.45,
            sign_number=4,
        )

        assert position.longitude == 123.45
        assert position.sign == "Лев"
        assert position.degree_in_sign == 3.45
        assert position.sign_number == 4

    def test_planet_position_validation(self):
        """Тест валидации модели позиции планеты."""
        # Корректные данные
        position = PlanetPosition(
            longitude=0.0,
            sign="Овен",
            degree_in_sign=0.0,
            sign_number=0,
        )
        assert position.longitude == 0.0

        # Отрицательные значения должны работать
        position = PlanetPosition(
            longitude=-10.0,
            sign="Рыбы",
            degree_in_sign=20.0,
            sign_number=11,
        )
        assert position.longitude == -10.0

    def test_transit_aspect_model(self):
        """Тест модели транзитного аспекта."""
        transit_pos = PlanetPosition(
            longitude=90.0, sign="Рак", degree_in_sign=0.0, sign_number=3
        )
        natal_pos = PlanetPosition(
            longitude=0.0, sign="Овен", degree_in_sign=0.0, sign_number=0
        )

        aspect = TransitAspect(
            transit_planet="Mars",
            natal_planet="Sun",
            aspect=AspectType.SQUARE,
            aspect_angle=90.0,
            exact_angle=90.0,
            orb=0.0,
            strength=8.5,
            transit_position=transit_pos,
            natal_position=natal_pos,
        )

        assert aspect.transit_planet == "Mars"
        assert aspect.natal_planet == "Sun"
        assert aspect.aspect == AspectType.SQUARE
        assert aspect.strength == 8.5

    def test_birth_info_model(self):
        """Тест модели информации о рождении."""
        birth_info = BirthInfo(
            date="1990-03-15",
            time="12:00",
            place={"latitude": 55.7558, "longitude": 37.6176},
            timezone="Europe/Moscow",
        )

        assert birth_info.date == "1990-03-15"
        assert birth_info.time == "12:00"
        assert birth_info.timezone == "Europe/Moscow"

    def test_birth_info_default_timezone(self):
        """Тест timezone по умолчанию."""
        birth_info = BirthInfo(
            date="1990-03-15",
            time="12:00",
            place={"latitude": 55.7558, "longitude": 37.6176},
        )

        assert birth_info.timezone == "UTC"

    def test_transit_summary_model(self):
        """Тест модели резюме транзитов."""
        summary = TransitSummary(
            overall_influence="благоприятный",
            dominant_planet="Jupiter",
            main_themes=["удача", "рост", "путешествия"],
            transit_count=5,
            advice="Используйте возможности для роста",
        )

        assert summary.overall_influence == "благоприятный"
        assert summary.dominant_planet == "Jupiter"
        assert len(summary.main_themes) == 3
        assert summary.transit_count == 5

    def test_progression_movement_model(self):
        """Тест модели движения в прогрессии."""
        natal_pos = PlanetPosition(
            longitude=0.0, sign="Овен", degree_in_sign=0.0, sign_number=0
        )
        progressed_pos = PlanetPosition(
            longitude=15.0, sign="Овен", degree_in_sign=15.0, sign_number=0
        )

        movement = ProgressionMovement(
            planet="Sun",
            natal_position=natal_pos,
            progressed_position=progressed_pos,
            movement_degrees=15.0,
            interpretation={
                "phase": "активная",
                "description": "Значительное развитие личности",
            },
        )

        assert movement.planet == "Sun"
        assert movement.movement_degrees == 15.0
        assert movement.interpretation["phase"] == "активная"

    def test_current_transits_model(self):
        """Тест модели текущих транзитов."""
        birth_info = BirthInfo(
            date="1990-03-15",
            time="12:00",
            place={"latitude": 55.7558, "longitude": 37.6176},
        )

        position = PlanetPosition(
            longitude=0.0, sign="Овен", degree_in_sign=0.0, sign_number=0
        )

        summary = TransitSummary(
            overall_influence="смешанный",
            main_themes=["изменения"],
            transit_count=0,
            advice="Будьте внимательны",
        )

        transits = CurrentTransits(
            calculation_date="2024-03-15T12:00:00Z",
            birth_info=birth_info,
            natal_positions={"Sun": position},
            current_positions={"Sun": position},
            all_transits=[],
            significant_transits=[],
            interpretation={"summary": "Спокойный период"},
            summary=summary,
        )

        assert transits.calculation_date == "2024-03-15T12:00:00Z"
        assert "Sun" in transits.natal_positions
        assert len(transits.all_transits) == 0

    def test_solar_return_model(self):
        """Тест модели соляра."""
        birth_info = BirthInfo(
            date="1990-03-15",
            time="12:00",
            place={"latitude": 55.7558, "longitude": 37.6176},
        )

        position = PlanetPosition(
            longitude=0.0, sign="Овен", degree_in_sign=0.0, sign_number=0
        )

        solar_return = SolarReturn(
            solar_year=2024,
            solar_date="2024-03-15",
            birth_info=birth_info,
            solar_positions={"Sun": position},
            solar_houses={"ascendant": {"sign": "Лев"}},
            interpretation={
                "year_theme": "личностное развитие",
                "summary": "Год роста",
            },
        )

        assert solar_return.solar_year == 2024
        assert solar_return.interpretation["year_theme"] == "личностное развитие"

    def test_lunar_return_model(self):
        """Тест модели лунара."""
        birth_info = BirthInfo(
            date="1990-03-15",
            time="12:00",
            place={"latitude": 55.7558, "longitude": 37.6176},
        )

        position = PlanetPosition(
            longitude=0.0, sign="Рак", degree_in_sign=0.0, sign_number=3
        )

        lunar_return = LunarReturn(
            lunar_date="2024-03-15",
            target_date="2024-03-15",
            birth_info=birth_info,
            lunar_positions={"Moon": position},
            interpretation={
                "monthly_theme": "семейные вопросы",
                "summary": "Эмоциональный месяц",
            },
        )

        assert lunar_return.lunar_date == "2024-03-15"
        assert lunar_return.interpretation["monthly_theme"] == "семейные вопросы"

    def test_transit_request_model(self):
        """Тест модели запроса транзитов."""
        request = TransitRequest(
            birth_date=date(1990, 3, 15),
            birth_time=time(12, 0),
            birth_place={"latitude": 55.7558, "longitude": 37.6176},
            transit_type=TransitType.CURRENT,
        )

        assert request.birth_date == date(1990, 3, 15)
        assert request.transit_type == TransitType.CURRENT

    def test_transit_request_defaults(self):
        """Тест значений по умолчанию в запросе транзитов."""
        request = TransitRequest(birth_date=date(1990, 3, 15))

        assert request.birth_time is None
        assert request.birth_place is None
        assert request.transit_type == TransitType.CURRENT

    def test_transit_response_model(self):
        """Тест модели ответа с транзитами."""
        birth_info = BirthInfo(
            date="1990-03-15",
            time="12:00",
            place={"latitude": 55.7558, "longitude": 37.6176},
        )

        position = PlanetPosition(
            longitude=0.0, sign="Овен", degree_in_sign=0.0, sign_number=0
        )

        summary = TransitSummary(
            overall_influence="спокойный",
            main_themes=["стабильность"],
            transit_count=0,
            advice="Наслаждайтесь покоем",
        )

        current_transits = CurrentTransits(
            calculation_date="2024-03-15T12:00:00Z",
            birth_info=birth_info,
            natal_positions={"Sun": position},
            current_positions={"Sun": position},
            all_transits=[],
            significant_transits=[],
            interpretation={"summary": "Спокойный период"},
            summary=summary,
        )

        response = TransitResponse(
            success=True,
            transit_type=TransitType.CURRENT,
            current_transits=current_transits,
        )

        assert response.success is True
        assert response.transit_type == TransitType.CURRENT
        assert response.current_transits is not None
        assert response.error is None

    def test_transit_response_error(self):
        """Тест модели ответа с ошибкой."""
        response = TransitResponse(
            success=False,
            transit_type=TransitType.CURRENT,
            error="Calculation failed",
            details="Invalid birth date",
        )

        assert response.success is False
        assert response.error == "Calculation failed"
        assert response.details == "Invalid birth date"

    def test_transit_analysis_result_model(self):
        """Тест модели результата анализа транзитов."""
        result = TransitAnalysisResult(
            has_significant_transits=True,
            dominant_themes=["трансформация", "рост"],
            period_influence="интенсивный",
            recommendations=["Будьте готовы к изменениям", "Доверьтесь процессу"],
            voice_summary="Период активных изменений и роста",
            detailed_explanation="Это время глубоких трансформаций...",
        )

        assert result.has_significant_transits is True
        assert len(result.dominant_themes) == 2
        assert result.period_influence == "интенсивный"
        assert len(result.recommendations) == 2

    def test_enums(self):
        """Тест перечислений."""
        # TransitType
        assert TransitType.CURRENT == "current"
        assert TransitType.PROGRESSIONS == "progressions"
        assert TransitType.SOLAR_RETURN == "solar_return"
        assert TransitType.LUNAR_RETURN == "lunar_return"

        # AspectType
        assert AspectType.CONJUNCTION == "Соединение"
        assert AspectType.SQUARE == "Квадрат"
        assert AspectType.TRINE == "Трин"

        # TimingPhase
        assert TimingPhase.EXACT == "точный"
        assert TimingPhase.APPROACHING == "приближающийся"

    def test_progressions_model(self):
        """Тест модели прогрессий."""
        birth_info = BirthInfo(
            date="1990-03-15",
            time="12:00",
            place={"latitude": 55.7558, "longitude": 37.6176},
        )

        natal_pos = PlanetPosition(
            longitude=0.0, sign="Овен", degree_in_sign=0.0, sign_number=0
        )

        progressed_pos = PlanetPosition(
            longitude=10.0, sign="Овен", degree_in_sign=10.0, sign_number=0
        )

        movement = ProgressionMovement(
            planet="Sun",
            natal_position=natal_pos,
            progressed_position=progressed_pos,
            movement_degrees=10.0,
            interpretation={"phase": "умеренная", "description": "Развитие"},
        )

        progressions = Progressions(
            calculation_date="2024-03-15",
            birth_info=birth_info,
            progression_date="2024-03-15",
            years_lived=34.0,
            natal_positions={"Sun": natal_pos},
            progressed_positions={"Sun": progressed_pos},
            progressions=[movement],
            interpretation={"life_phase": "период развития"},
        )

        assert progressions.years_lived == 34.0
        assert len(progressions.progressions) == 1
        assert progressions.progressions[0].movement_degrees == 10.0

    def test_model_serialization(self):
        """Тест сериализации моделей."""
        position = PlanetPosition(
            longitude=123.45,
            sign="Лев",
            degree_in_sign=3.45,
            sign_number=4,
        )

        # Сериализация в словарь
        data = position.dict()
        assert data["longitude"] == 123.45
        assert data["sign"] == "Лев"

        # Создание из словаря
        new_position = PlanetPosition(**data)
        assert new_position.longitude == position.longitude
        assert new_position.sign == position.sign

    def test_optional_fields(self):
        """Тест опциональных полей."""
        # TransitAspect с минимальными полями
        transit_pos = PlanetPosition(
            longitude=90.0, sign="Рак", degree_in_sign=0.0, sign_number=3
        )
        natal_pos = PlanetPosition(
            longitude=0.0, sign="Овен", degree_in_sign=0.0, sign_number=0
        )

        aspect = TransitAspect(
            transit_planet="Mars",
            natal_planet="Sun",
            aspect=AspectType.SQUARE,
            aspect_angle=90.0,
            exact_angle=90.0,
            orb=0.0,
            strength=8.5,
            transit_position=transit_pos,
            natal_position=natal_pos,
            # timing и interpretation опциональны
        )

        assert aspect.timing is None
        assert aspect.interpretation is None

    @pytest.mark.parametrize(
        "aspect_type,expected_value",
        [
            (AspectType.CONJUNCTION, "Соединение"),
            (AspectType.SEXTILE, "Секстиль"),
            (AspectType.SQUARE, "Квадрат"),
            (AspectType.TRINE, "Трин"),
            (AspectType.OPPOSITION, "Оппозиция"),
        ],
    )
    def test_aspect_types(self, aspect_type, expected_value):
        """Тест типов аспектов."""
        assert aspect_type.value == expected_value

    def test_constants(self):
        """Тест констант из модуля."""
        from app.models.transit_models import (
            ASPECT_WEIGHTS,
            PLANET_WEIGHTS,
            TRANSIT_ORBS,
        )

        # Проверяем, что константы определены
        assert isinstance(PLANET_WEIGHTS, dict)
        assert isinstance(ASPECT_WEIGHTS, dict)
        assert isinstance(TRANSIT_ORBS, dict)

        # Проверяем некоторые значения
        assert PLANET_WEIGHTS["Sun"] == 10
        assert ASPECT_WEIGHTS[0] == 10  # Соединение
        assert TRANSIT_ORBS[90] == 3  # Квадрат

    def test_planet_themes_constant(self):
        """Тест константы тем планет."""
        from app.models.transit_models import PLANET_THEMES

        assert isinstance(PLANET_THEMES, dict)
        assert "Sun" in PLANET_THEMES
        assert "личность" in PLANET_THEMES["Sun"]
        assert "Moon" in PLANET_THEMES
        assert "эмоции" in PLANET_THEMES["Moon"]

    def test_aspect_natures_constant(self):
        """Тест константы характеров аспектов."""
        from app.models.transit_models import ASPECT_NATURES

        assert isinstance(ASPECT_NATURES, dict)
        assert "Соединение" in ASPECT_NATURES
        assert "интенсивное" in ASPECT_NATURES["Соединение"]
        assert "Трин" in ASPECT_NATURES
        assert "благоприятное" in ASPECT_NATURES["Трин"]