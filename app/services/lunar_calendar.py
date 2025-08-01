"""
Сервис лунного календаря и лунных рекомендаций.
"""
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
import calendar
import math

from app.services.astrology_calculator import AstrologyCalculator


class LunarCalendar:
    """Калькулятор лунного календаря."""
    
    def __init__(self):
        self.astro_calc = AstrologyCalculator()
        
        # Описания лунных дней (1-30)
        self.lunar_day_descriptions = {
            1: {
                "name": "День символа",
                "description": "День новых начинаний и планирования",
                "energy": "низкая",
                "recommendations": [
                    "Планируйте новые проекты",
                    "Медитируйте и ставьте цели",
                    "Избегайте активных действий"
                ]
            },
            2: {
                "name": "День роста", 
                "description": "Энергия начинает набирать силу",
                "energy": "растущая",
                "recommendations": [
                    "Начинайте осуществлять планы",
                    "Полезны дыхательные упражнения",
                    "Хорошее время для изучения нового"
                ]
            },
            3: {
                "name": "День борьбы",
                "description": "День активности и преодоления препятствий", 
                "energy": "активная",
                "recommendations": [
                    "Проявляйте инициативу",
                    "Занимайтесь спортом",
                    "Решайте сложные задачи"
                ]
            },
            4: {
                "name": "День выбора",
                "description": "Время принятия важных решений",
                "energy": "умеренная",
                "recommendations": [
                    "Анализируйте ситуацию",
                    "Принимайте взвешенные решения",
                    "Избегайте импульсивности"
                ]
            },
            5: {
                "name": "День единения",
                "description": "День работы с энергией и питанием",
                "energy": "стабильная",
                "recommendations": [
                    "Следите за питанием",
                    "Практикуйте йогу",
                    "Работайте с энергетическими центрами"
                ]
            },
            6: {
                "name": "День слова",
                "description": "День общения и передачи знаний",
                "energy": "коммуникативная",
                "recommendations": [
                    "Активно общайтесь",
                    "Передавайте знания",
                    "Изучайте языки"
                ]
            },
            7: {
                "name": "День ветра",
                "description": "День движения и перемен",
                "energy": "переменчивая",
                "recommendations": [
                    "Будьте гибкими",
                    "Практикуйте дыхательные техники",
                    "Избегайте жестких планов"
                ]
            },
            8: {
                "name": "День преображения",
                "description": "День трансформации и очищения",
                "energy": "трансформирующая",
                "recommendations": [
                    "Очищайте тело и разум",
                    "Практикуйте детокс",
                    "Освобождайтесь от ненужного"
                ]
            },
            9: {
                "name": "День обмана",
                "description": "День осторожности и внимательности",
                "energy": "нестабильная",
                "recommendations": [
                    "Будьте осторожны",
                    "Проверяйте информацию",
                    "Избегайте важных решений"
                ]
            },
            10: {
                "name": "День традиций",
                "description": "День связи с корнями и семьей",
                "energy": "традиционная",
                "recommendations": [
                    "Общайтесь с семьей",
                    "Изучайте родословную",
                    "Следуйте традициям"
                ]
            },
            11: {
                "name": "День силы",
                "description": "День активности и физической силы",
                "energy": "высокая",
                "recommendations": [
                    "Занимайтесь спортом",
                    "Проявляйте силу воли",
                    "Принимайте активные решения"
                ]
            },
            12: {
                "name": "День сердца",
                "description": "День любви и сострадания",
                "energy": "эмоциональная",
                "recommendations": [
                    "Проявляйте сострадание",
                    "Работайте с сердечной чакрой",
                    "Практикуйте прощение"
                ]
            },
            13: {
                "name": "День колеса",
                "description": "День движения и развития",
                "energy": "динамичная",
                "recommendations": [
                    "Развивайте навыки",
                    "Изучайте новое",
                    "Двигайтесь к целям"
                ]
            },
            14: {
                "name": "День призыва",
                "description": "День связи с высшими силами",
                "energy": "духовная",
                "recommendations": [
                    "Медитируйте",
                    "Практикуйте духовные техники",
                    "Слушайте интуицию"
                ]
            },
            15: {
                "name": "День искушения",
                "description": "День проверки на прочность",
                "energy": "испытательная",
                "recommendations": [
                    "Контролируйте желания",
                    "Укрепляйте силу воли",
                    "Избегайте излишеств"
                ]
            },
            16: {
                "name": "День гармонии",
                "description": "День равновесия и покоя",
                "energy": "гармоничная",
                "recommendations": [
                    "Ищите баланс",
                    "Практикуйте умеренность",
                    "Наслаждайтесь красотой"
                ]
            },
            17: {
                "name": "День радости",
                "description": "День веселья и праздника",
                "energy": "радостная",
                "recommendations": [
                    "Веселитесь и радуйтесь",
                    "Общайтесь с друзьями",
                    "Празднуйте жизнь"
                ]
            },
            18: {
                "name": "День зеркала",
                "description": "День самопознания и рефлексии",
                "energy": "рефлективная",
                "recommendations": [
                    "Изучайте себя",
                    "Анализируйте поступки",
                    "Работайте над собой"
                ]
            },
            19: {
                "name": "День паука",
                "description": "День терпения и планирования",
                "energy": "терпеливая",
                "recommendations": [
                    "Планируйте долгосрочно",
                    "Проявляйте терпение",
                    "Плетите свою судьбу"
                ]
            },
            20: {
                "name": "День орла",
                "description": "День высоких целей и перспектив",
                "energy": "возвышенная",
                "recommendations": [
                    "Ставьте высокие цели",
                    "Смотрите широко",
                    "Развивайте духовность"
                ]
            },
            21: {
                "name": "День коня",
                "description": "День движения и активности",
                "energy": "активная",
                "recommendations": [
                    "Будьте активны",
                    "Путешествуйте",
                    "Проявляйте независимость"
                ]
            },
            22: {
                "name": "День мудрости",
                "description": "День познания и учения",
                "energy": "мудрая",
                "recommendations": [
                    "Изучайте мудрость",
                    "Передавайте знания",
                    "Развивайте интеллект"
                ]
            },
            23: {
                "name": "День крокодила",
                "description": "День защиты и осторожности",
                "energy": "защитная",
                "recommendations": [
                    "Защищайте близких",
                    "Будьте осторожны",
                    "Укрепляйте безопасность"
                ]
            },
            24: {
                "name": "День медведя",
                "description": "День силы и пробуждения",
                "energy": "пробуждающая",
                "recommendations": [
                    "Пробуждайте силы",
                    "Активизируйте энергию",
                    "Выходите из спячки"
                ]
            },
            25: {
                "name": "День черепахи",
                "description": "День медленного и устойчивого прогресса",
                "energy": "устойчивая",
                "recommendations": [
                    "Двигайтесь медленно но верно",
                    "Проявляйте устойчивость",
                    "Накапливайте опыт"
                ]
            },
            26: {
                "name": "День жабы",
                "description": "День очищения и обновления",
                "energy": "очищающая",
                "recommendations": [
                    "Очищайте организм",
                    "Обновляйте энергию",
                    "Освобождайтесь от токсинов"
                ]
            },
            27: {
                "name": "День трезубца",
                "description": "День силы и власти",
                "energy": "властная",
                "recommendations": [
                    "Проявляйте лидерство",
                    "Используйте власть мудро",
                    "Направляйте энергию правильно"
                ]
            },
            28: {
                "name": "День лотоса",
                "description": "День духовного раскрытия",
                "energy": "духовная",
                "recommendations": [
                    "Раскрывайте духовность",
                    "Практикуйте медитацию",
                    "Стремитесь к просветлению"
                ]
            },
            29: {
                "name": "День осьминога",
                "description": "День сложностей и запутанности",
                "energy": "сложная",
                "recommendations": [
                    "Избегайте сложностей",
                    "Будьте осторожны",
                    "Не принимайте важных решений"
                ]
            },
            30: {
                "name": "День лебедя",
                "description": "День красоты и завершения",
                "energy": "завершающая",
                "recommendations": [
                    "Завершайте дела",
                    "Наслаждайтесь красотой",
                    "Готовьтесь к новому циклу"
                ]
            }
        }
        
        # Активности по фазам Луны
        self.lunar_phase_activities = {
            "Новолуние": {
                "business": "Планирование новых проектов, постановка целей",
                "health": "Детоксикация, начало диет, очищение",
                "relationships": "Знакомства, новые контакты",
                "creativity": "Зарождение идей, планирование творческих проектов",
                "spiritual": "Медитация, постановка намерений"
            },
            "Растущая Луна": {
                "business": "Активное развитие проектов, привлечение ресурсов",
                "health": "Укрепление организма, набор мышечной массы",
                "relationships": "Развитие отношений, укрепление связей",
                "creativity": "Активное творчество, воплощение идей",
                "spiritual": "Изучение, накопление знаний"
            },
            "Полнолуние": {
                "business": "Завершение проектов, подведение итогов",
                "health": "Максимальная активность, но осторожность с переутомлением",
                "relationships": "Пик эмоций, важные разговоры",
                "creativity": "Максимальное самовыражение, презентации",
                "spiritual": "Мощные практики, энергетическая работа"
            },
            "Убывающая Луна": {
                "business": "Анализ результатов, оптимизация процессов",
                "health": "Избавление от вредных привычек, снижение веса",
                "relationships": "Работа над проблемами, прощение",
                "creativity": "Редактирование, совершенствование работ",
                "spiritual": "Освобождение, отпускание старого"
            }
        }

    def get_lunar_day_info(self, target_date: datetime) -> Dict[str, Any]:
        """Получает информацию о лунном дне."""
        
        # Упрощенный расчет лунного дня
        # В реальности требуется точный расчет лунного календаря
        moon_phase = self.astro_calc.calculate_moon_phase(target_date)
        
        # Приблизительный расчет лунного дня на основе фазы
        lunar_day = self._calculate_approximate_lunar_day(moon_phase["angle"])
        
        lunar_info = self.lunar_day_descriptions.get(lunar_day, self.lunar_day_descriptions[1])
        
        return {
            "lunar_day": lunar_day,
            "name": lunar_info["name"],
            "description": lunar_info["description"],
            "energy_level": lunar_info["energy"],
            "recommendations": lunar_info["recommendations"],
            "moon_phase": moon_phase,
            "activities": self.lunar_phase_activities.get(
                moon_phase["phase_name"], 
                self.lunar_phase_activities["Новолуние"]
            )
        }

    def _calculate_approximate_lunar_day(self, moon_angle: float) -> int:
        """Приблизительно вычисляет лунный день по углу Луны."""
        # Упрощенный расчет: 360 градусов / 29.5 дней ≈ 12.2 градуса на день
        lunar_day = int(moon_angle / 12.2) + 1
        return max(1, min(30, lunar_day))

    def get_monthly_lunar_calendar(
        self, 
        year: int, 
        month: int
    ) -> Dict[str, Any]:
        """Получает лунный календарь на месяц."""
        
        # Получаем все дни месяца
        days_in_month = calendar.monthrange(year, month)[1]
        lunar_month = {}
        
        for day in range(1, days_in_month + 1):
            target_date = datetime(year, month, day)
            lunar_info = self.get_lunar_day_info(target_date)
            
            lunar_month[day] = {
                "date": target_date.strftime("%Y-%m-%d"),
                "lunar_day": lunar_info["lunar_day"],
                "name": lunar_info["name"],
                "energy": lunar_info["energy_level"],
                "phase": lunar_info["moon_phase"]["phase_name"],
                "recommendations": lunar_info["recommendations"][:2]  # Первые 2 рекомендации
            }
        
        # Находим ключевые дни месяца
        key_dates = self._find_key_lunar_dates(year, month)
        
        return {
            "year": year,
            "month": month,
            "month_name": calendar.month_name[month],
            "lunar_days": lunar_month,
            "key_dates": key_dates,
            "monthly_advice": self._get_monthly_advice(year, month)
        }

    def _find_key_lunar_dates(self, year: int, month: int) -> Dict[str, List[int]]:
        """Находит ключевые лунные даты в месяце."""
        
        days_in_month = calendar.monthrange(year, month)[1]
        key_dates = {
            "new_moon": [],
            "full_moon": [],
            "first_quarter": [],
            "last_quarter": []
        }
        
        for day in range(1, days_in_month + 1):
            target_date = datetime(year, month, day)
            moon_phase = self.astro_calc.calculate_moon_phase(target_date)
            phase_name = moon_phase["phase_name"]
            
            if "Новолуние" in phase_name:
                key_dates["new_moon"].append(day)
            elif "Полнолуние" in phase_name:
                key_dates["full_moon"].append(day)
            elif "Первая четверть" in phase_name:
                key_dates["first_quarter"].append(day)
            elif "Последняя четверть" in phase_name:
                key_dates["last_quarter"].append(day)
        
        return key_dates

    def _get_monthly_advice(self, year: int, month: int) -> Dict[str, str]:
        """Получает советы на месяц."""
        
        # Определяем сезон и даем соответствующие советы
        if month in [12, 1, 2]:
            season = "winter"
            season_advice = "Время внутреннего развития и планирования"
        elif month in [3, 4, 5]:
            season = "spring"
            season_advice = "Время новых начинаний и роста"
        elif month in [6, 7, 8]:
            season = "summer"
            season_advice = "Время активности и самовыражения"
        else:
            season = "autumn"
            season_advice = "Время сбора урожая и подготовки"
        
        return {
            "general": season_advice,
            "health": "Следуйте лунным ритмам для поддержания здоровья",
            "relationships": "Используйте лунные фазы для гармонизации отношений",
            "business": "Планируйте важные дела в соответствии с лунным календарем"
        }

    def get_lunar_recommendations(
        self, 
        activity_type: str,
        target_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Получает рекомендации для конкретной деятельности."""
        
        if target_date is None:
            target_date = datetime.now()
        
        lunar_info = self.get_lunar_day_info(target_date)
        phase_name = lunar_info["moon_phase"]["phase_name"]
        
        # Получаем рекомендации по типу активности
        activities = lunar_info["activities"]
        
        if activity_type in activities:
            specific_recommendation = activities[activity_type]
        else:
            specific_recommendation = "Следуйте общим лунным рекомендациям"
        
        # Определяем благоприятность
        energy_level = lunar_info["energy_level"]
        favorability = self._determine_favorability(activity_type, energy_level, phase_name)
        
        return {
            "date": target_date.strftime("%Y-%m-%d"),
            "lunar_day": lunar_info["lunar_day"],
            "lunar_day_name": lunar_info["name"],
            "moon_phase": phase_name,
            "activity_type": activity_type,
            "recommendation": specific_recommendation,
            "favorability": favorability,
            "energy_level": energy_level,
            "additional_advice": self._get_additional_advice(activity_type, lunar_info)
        }

    def _determine_favorability(
        self, 
        activity_type: str, 
        energy_level: str, 
        phase_name: str
    ) -> Dict[str, Any]:
        """Определяет благоприятность для деятельности."""
        
        # Базовая благоприятность по типу активности и фазе Луны
        favorability_matrix = {
            "business": {
                "Новолуние": 4,
                "Растущая Луна": 5,
                "Полнолуние": 3,
                "Убывающая Луна": 2
            },
            "health": {
                "Новолуние": 5,
                "Растущая Луна": 4,
                "Полнолуние": 2,
                "Убывающая Луна": 5
            },
            "relationships": {
                "Новолуние": 4,
                "Растущая Луна": 5,
                "Полнолуние": 5,
                "Убывающая Луна": 3
            },
            "creativity": {
                "Новолуние": 3,
                "Растущая Луна": 5,
                "Полнолуние": 5,
                "Убывающая Луна": 2
            },
            "spiritual": {
                "Новолуние": 5,
                "Растущая Луна": 4,
                "Полнолуние": 5,
                "Убывающая Луна": 4
            }
        }
        
        base_score = favorability_matrix.get(activity_type, {}).get(phase_name, 3)
        
        # Корректируем по уровню энергии
        energy_modifiers = {
            "низкая": -1,
            "растущая": 0,
            "умеренная": 0,
            "активная": 1,
            "высокая": 1,
            "духовная": 0
        }
        
        modifier = energy_modifiers.get(energy_level, 0)
        final_score = max(1, min(5, base_score + modifier))
        
        favorability_descriptions = {
            1: "Неблагоприятное время",
            2: "Малоблагоприятное время", 
            3: "Нейтральное время",
            4: "Благоприятное время",
            5: "Очень благоприятное время"
        }
        
        return {
            "score": final_score,
            "description": favorability_descriptions[final_score],
            "recommendation": "Действуйте" if final_score >= 4 else "Подождите лучшего времени"
        }

    def _get_additional_advice(
        self, 
        activity_type: str, 
        lunar_info: Dict[str, Any]
    ) -> str:
        """Получает дополнительные советы."""
        
        lunar_day = lunar_info["lunar_day"]
        energy_level = lunar_info["energy_level"]
        
        # Специфические советы по дням
        special_advice = {
            1: "Идеальный день для планирования",
            7: "Будьте гибкими в планах",
            11: "Используйте высокую энергию",
            14: "Доверьтесь интуиции",
            15: "Избегайте излишеств",
            19: "Проявите терпение",
            29: "Избегайте сложных дел"
        }
        
        if lunar_day in special_advice:
            return special_advice[lunar_day]
        
        # Общие советы по уровню энергии
        energy_advice = {
            "низкая": "Время для отдыха и планирования",
            "растущая": "Постепенно увеличивайте активность",
            "активная": "Время для решительных действий",
            "высокая": "Используйте энергию максимально",
            "духовная": "Сосредоточьтесь на внутреннем развитии"
        }
        
        return energy_advice.get(energy_level, "Следуйте своей интуиции")

    def get_best_days_for_activity(
        self, 
        activity_type: str,
        year: int,
        month: int
    ) -> List[Dict[str, Any]]:
        """Находит лучшие дни месяца для определенной деятельности."""
        
        days_in_month = calendar.monthrange(year, month)[1]
        best_days = []
        
        for day in range(1, days_in_month + 1):
            target_date = datetime(year, month, day)
            recommendations = self.get_lunar_recommendations(activity_type, target_date)
            
            if recommendations["favorability"]["score"] >= 4:
                best_days.append({
                    "date": target_date.strftime("%Y-%m-%d"),
                    "day": day,
                    "score": recommendations["favorability"]["score"],
                    "description": recommendations["favorability"]["description"],
                    "lunar_day": recommendations["lunar_day"],
                    "moon_phase": recommendations["moon_phase"]
                })
        
        # Сортируем по убыванию благоприятности
        best_days.sort(key=lambda x: x["score"], reverse=True)
        
        return best_days[:10]  # Возвращаем топ-10 дней