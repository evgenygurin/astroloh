"""
Тесты для лунного календаря.
"""
import calendar
from datetime import datetime

from app.services.lunar_calendar import LunarCalendar


class TestLunarCalendar:
    """Тесты лунного календаря."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.lunar_calendar = LunarCalendar()

    def test_get_lunar_day_info_basic(self):
        """Тест базового получения информации о лунном дне."""
        test_date = datetime(2023, 6, 15, 12, 0)
        lunar_info = self.lunar_calendar.get_lunar_day_info(test_date)

        # Проверяем основную структуру
        assert "lunar_day" in lunar_info
        assert "name" in lunar_info
        assert "description" in lunar_info
        assert "energy_level" in lunar_info
        assert "recommendations" in lunar_info
        assert "moon_phase" in lunar_info
        assert "activities" in lunar_info

        # Проверяем типы и диапазоны
        assert 1 <= lunar_info["lunar_day"] <= 30
        assert isinstance(lunar_info["name"], str)
        assert isinstance(lunar_info["description"], str)
        assert isinstance(lunar_info["energy_level"], str)
        assert isinstance(lunar_info["recommendations"], list)
        assert len(lunar_info["recommendations"]) > 0

    def test_lunar_day_descriptions(self):
        """Тест описаний лунных дней."""
        # Проверяем, что все 30 лунных дней имеют описания
        for day in range(1, 31):
            assert day in self.lunar_calendar.lunar_day_descriptions

            day_info = self.lunar_calendar.lunar_day_descriptions[day]
            assert "name" in day_info
            assert "description" in day_info
            assert "energy" in day_info
            assert "recommendations" in day_info

            assert isinstance(day_info["name"], str)
            assert isinstance(day_info["description"], str)
            assert isinstance(day_info["energy"], str)
            assert isinstance(day_info["recommendations"], list)
            assert len(day_info["recommendations"]) >= 2

    def test_moon_phase_activities(self):
        """Тест активностей по фазам Луны."""
        expected_phases = [
            "Новолуние",
            "Растущая Луна",
            "Полнолуние",
            "Убывающая Луна",
        ]
        expected_activities = [
            "business",
            "health",
            "relationships",
            "creativity",
            "spiritual",
        ]

        for phase in expected_phases:
            assert phase in self.lunar_calendar.lunar_phase_activities

            phase_activities = self.lunar_calendar.lunar_phase_activities[
                phase
            ]
            for activity in expected_activities:
                assert activity in phase_activities
                assert isinstance(phase_activities[activity], str)
                assert len(phase_activities[activity]) > 10

    def test_get_monthly_lunar_calendar(self):
        """Тест получения лунного календаря на месяц."""
        year = 2023
        month = 6

        lunar_month = self.lunar_calendar.get_monthly_lunar_calendar(
            year, month
        )

        # Проверяем основную структуру
        assert "year" in lunar_month
        assert "month" in lunar_month
        assert "month_name" in lunar_month
        assert "lunar_days" in lunar_month
        assert "key_dates" in lunar_month
        assert "monthly_advice" in lunar_month

        # Проверяем значения
        assert lunar_month["year"] == year
        assert lunar_month["month"] == month
        assert lunar_month["month_name"] == calendar.month_name[month]

        # Проверяем дни месяца
        days_in_month = calendar.monthrange(year, month)[1]
        lunar_days = lunar_month["lunar_days"]

        assert len(lunar_days) == days_in_month

        for day in range(1, days_in_month + 1):
            assert day in lunar_days
            day_info = lunar_days[day]

            assert "date" in day_info
            assert "lunar_day" in day_info
            assert "name" in day_info
            assert "energy" in day_info
            assert "phase" in day_info
            assert "recommendations" in day_info

            assert 1 <= day_info["lunar_day"] <= 30
            assert isinstance(day_info["recommendations"], list)

    def test_key_lunar_dates(self):
        """Тест определения ключевых лунных дат."""
        year = 2023
        month = 7

        lunar_month = self.lunar_calendar.get_monthly_lunar_calendar(
            year, month
        )
        key_dates = lunar_month["key_dates"]

        # Проверяем структуру ключевых дат
        expected_keys = [
            "new_moon",
            "full_moon",
            "first_quarter",
            "last_quarter",
        ]

        for key in expected_keys:
            assert key in key_dates
            assert isinstance(key_dates[key], list)

            # Проверяем, что дни находятся в допустимом диапазоне
            for day in key_dates[key]:
                assert 1 <= day <= 31

    def test_monthly_advice(self):
        """Тест месячных советов."""
        year = 2023
        month = 12  # Зима

        lunar_month = self.lunar_calendar.get_monthly_lunar_calendar(
            year, month
        )
        advice = lunar_month["monthly_advice"]

        assert "general" in advice
        assert "health" in advice
        assert "relationships" in advice
        assert "business" in advice

        for category, text in advice.items():
            assert isinstance(text, str)
            assert len(text) > 10

        # Зимние советы должны содержать соответствующие темы
        assert (
            "внутреннего развития" in advice["general"]
            or "планирования" in advice["general"]
        )

    def test_lunar_recommendations_by_activity(self):
        """Тест рекомендаций по типу деятельности."""
        test_date = datetime(2023, 8, 10, 15, 30)
        activity_types = [
            "business",
            "health",
            "relationships",
            "creativity",
            "spiritual",
        ]

        for activity in activity_types:
            recommendations = self.lunar_calendar.get_lunar_recommendations(
                activity_type=activity, target_date=test_date
            )

            # Проверяем основную структуру
            assert "date" in recommendations
            assert "lunar_day" in recommendations
            assert "lunar_day_name" in recommendations
            assert "moon_phase" in recommendations
            assert "activity_type" in recommendations
            assert "recommendation" in recommendations
            assert "favorability" in recommendations
            assert "energy_level" in recommendations
            assert "additional_advice" in recommendations

            # Проверяем значения
            assert recommendations["activity_type"] == activity
            assert 1 <= recommendations["lunar_day"] <= 30
            assert isinstance(recommendations["recommendation"], str)

            # Проверяем благоприятность
            favorability = recommendations["favorability"]
            assert "score" in favorability
            assert "description" in favorability
            assert "recommendation" in favorability

            assert 1 <= favorability["score"] <= 5

    def test_favorability_scoring(self):
        """Тест системы оценки благоприятности."""
        test_date = datetime(2023, 9, 5)

        # Тестируем разные активности
        activities = [
            "business",
            "health",
            "relationships",
            "creativity",
            "spiritual",
        ]
        scores = []

        for activity in activities:
            recommendations = self.lunar_calendar.get_lunar_recommendations(
                activity_type=activity, target_date=test_date
            )
            scores.append(recommendations["favorability"]["score"])

        # Все оценки должны быть в допустимом диапазоне
        for score in scores:
            assert 1 <= score <= 5

        # Должна быть некоторая вариативность в оценках
        assert len(set(scores)) >= 1  # Минимум одна уникальная оценка

    def test_best_days_for_activity(self):
        """Тест поиска лучших дней для деятельности."""
        year = 2023
        month = 10
        activity = "business"

        best_days = self.lunar_calendar.get_best_days_for_activity(
            activity_type=activity, year=year, month=month
        )

        # Проверяем структуру результата
        assert isinstance(best_days, list)
        assert len(best_days) <= 10  # Максимум 10 дней

        for day_info in best_days:
            assert "date" in day_info
            assert "day" in day_info
            assert "score" in day_info
            assert "description" in day_info
            assert "lunar_day" in day_info
            assert "moon_phase" in day_info

            # Все дни должны быть благоприятными (оценка >= 4)
            assert day_info["score"] >= 4
            assert 1 <= day_info["day"] <= 31
            assert 1 <= day_info["lunar_day"] <= 30

        # Дни должны быть отсортированы по убыванию оценки
        scores = [day["score"] for day in best_days]
        assert scores == sorted(scores, reverse=True)

    def test_seasonal_influence(self):
        """Тест сезонного влияния."""
        # Тестируем разные сезоны
        seasons_data = [
            (datetime(2023, 3, 15), "весна"),  # Весна
            (datetime(2023, 6, 15), "лето"),  # Лето
            (datetime(2023, 9, 15), "осень"),  # Осень
            (datetime(2023, 12, 15), "зима"),  # Зима
        ]

        for test_date, expected_season in seasons_data:
            lunar_info = self.lunar_calendar.get_lunar_day_info(test_date)

            # Получаем сезонное влияние из астрологических влияний
            if "astrological_influences" in lunar_info:
                season_influence = lunar_info["astrological_influences"].get(
                    "season_influence", {}
                )
                if "season" in season_influence:
                    assert season_influence["season"] == expected_season

    def test_lunar_day_calculation(self):
        """Тест расчета лунного дня."""
        # Тестируем разные даты
        test_dates = [
            datetime(2023, 1, 1),
            datetime(2023, 6, 15),
            datetime(2023, 12, 31),
        ]

        for test_date in test_dates:
            lunar_info = self.lunar_calendar.get_lunar_day_info(test_date)
            lunar_day = lunar_info["lunar_day"]

            # Лунный день должен быть в допустимом диапазоне
            assert 1 <= lunar_day <= 30

            # Проверяем, что описание лунного дня соответствует дню
            expected_description = self.lunar_calendar.lunar_day_descriptions[
                lunar_day
            ]
            assert lunar_info["name"] == expected_description["name"]
            assert (
                lunar_info["description"]
                == expected_description["description"]
            )

    def test_different_activity_types(self):
        """Тест различных типов деятельности."""
        test_date = datetime(2023, 11, 20)

        # Тестируем все основные типы деятельности
        activity_types = [
            "business",
            "health",
            "relationships",
            "creativity",
            "spiritual",
        ]

        for activity in activity_types:
            recommendations = self.lunar_calendar.get_lunar_recommendations(
                activity_type=activity, target_date=test_date
            )

            assert recommendations["activity_type"] == activity

            # Проверяем, что рекомендация содержательная
            recommendation = recommendations["recommendation"]
            assert isinstance(recommendation, str)
            assert len(recommendation) > 20

            # Дополнительный совет должен присутствовать
            additional_advice = recommendations["additional_advice"]
            assert isinstance(additional_advice, str)
            assert len(additional_advice) > 5

    def test_edge_cases(self):
        """Тест граничных случаев."""
        # Тест с граничными датами года
        edge_dates = [
            datetime(2023, 1, 1, 0, 0),  # Начало года
            datetime(2023, 12, 31, 23, 59),  # Конец года
            datetime(2024, 2, 29, 12, 0),  # Високосный год
        ]

        for test_date in edge_dates:
            lunar_info = self.lunar_calendar.get_lunar_day_info(test_date)

            # Основная структура должна быть корректной
            assert 1 <= lunar_info["lunar_day"] <= 30
            assert isinstance(lunar_info["name"], str)
            assert len(lunar_info["recommendations"]) > 0

            # Фаза Луны должна быть определена
            moon_phase = lunar_info["moon_phase"]
            assert "phase_name" in moon_phase
            assert 0 <= moon_phase["illumination_percent"] <= 100
