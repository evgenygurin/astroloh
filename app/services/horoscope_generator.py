"""
Сервис генерации персональных гороскопов.
"""
import random
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.models.yandex_models import YandexZodiacSign
from app.services.astrology_calculator import AstrologyCalculator


class HoroscopePeriod(Enum):
    DAILY = "день"
    WEEKLY = "неделя"
    MONTHLY = "месяц"


class HoroscopeGenerator:
    """Генератор персональных гороскопов."""

    def __init__(self):
        self.astro_calc = AstrologyCalculator()

        # Базовые характеристики знаков зодиака
        self.sign_characteristics = {
            YandexZodiacSign.ARIES: {
                "element": "fire",
                "quality": "cardinal",
                "ruling_planet": "Mars",
                "keywords": [
                    "энергия",
                    "инициатива",
                    "лидерство",
                    "импульсивность",
                ],
                "lucky_numbers": [1, 8, 17, 26],
                "lucky_colors": ["красный", "оранжевый"],
            },
            YandexZodiacSign.TAURUS: {
                "element": "earth",
                "quality": "fixed",
                "ruling_planet": "Venus",
                "keywords": [
                    "стабильность",
                    "упорство",
                    "красота",
                    "материальность",
                ],
                "lucky_numbers": [2, 6, 9, 12, 24],
                "lucky_colors": ["зеленый", "розовый"],
            },
            YandexZodiacSign.GEMINI: {
                "element": "air",
                "quality": "mutable",
                "ruling_planet": "Mercury",
                "keywords": [
                    "общение",
                    "любознательность",
                    "гибкость",
                    "многозадачность",
                ],
                "lucky_numbers": [3, 12, 21, 30],
                "lucky_colors": ["желтый", "серебряный"],
            },
            YandexZodiacSign.CANCER: {
                "element": "water",
                "quality": "cardinal",
                "ruling_planet": "Moon",
                "keywords": ["эмоции", "семья", "интуиция", "забота"],
                "lucky_numbers": [2, 7, 11, 16, 20, 25],
                "lucky_colors": ["белый", "серебряный", "синий"],
            },
            YandexZodiacSign.LEO: {
                "element": "fire",
                "quality": "fixed",
                "ruling_planet": "Sun",
                "keywords": [
                    "творчество",
                    "гордость",
                    "великодушие",
                    "драматизм",
                ],
                "lucky_numbers": [1, 3, 10, 19],
                "lucky_colors": ["золотой", "оранжевый"],
            },
            YandexZodiacSign.VIRGO: {
                "element": "earth",
                "quality": "mutable",
                "ruling_planet": "Mercury",
                "keywords": [
                    "аналитичность",
                    "практичность",
                    "перфекционизм",
                    "служение",
                ],
                "lucky_numbers": [3, 27, 35, 80],
                "lucky_colors": ["синий", "зеленый"],
            },
            YandexZodiacSign.LIBRA: {
                "element": "air",
                "quality": "cardinal",
                "ruling_planet": "Venus",
                "keywords": [
                    "гармония",
                    "справедливость",
                    "партнерство",
                    "красота",
                ],
                "lucky_numbers": [6, 15, 24, 33, 42, 51],
                "lucky_colors": ["розовый", "голубой"],
            },
            YandexZodiacSign.SCORPIO: {
                "element": "water",
                "quality": "fixed",
                "ruling_planet": "Pluto",
                "keywords": ["трансформация", "глубина", "страсть", "тайны"],
                "lucky_numbers": [8, 11, 18, 22],
                "lucky_colors": ["красный", "черный"],
            },
            YandexZodiacSign.SAGITTARIUS: {
                "element": "fire",
                "quality": "mutable",
                "ruling_planet": "Jupiter",
                "keywords": [
                    "философия",
                    "путешествия",
                    "оптимизм",
                    "свобода",
                ],
                "lucky_numbers": [3, 9, 21, 22, 30],
                "lucky_colors": ["фиолетовый", "бирюзовый"],
            },
            YandexZodiacSign.CAPRICORN: {
                "element": "earth",
                "quality": "cardinal",
                "ruling_planet": "Saturn",
                "keywords": [
                    "амбиции",
                    "дисциплина",
                    "ответственность",
                    "традиции",
                ],
                "lucky_numbers": [6, 8, 26, 35],
                "lucky_colors": ["черный", "коричневый"],
            },
            YandexZodiacSign.AQUARIUS: {
                "element": "air",
                "quality": "fixed",
                "ruling_planet": "Uranus",
                "keywords": [
                    "инновации",
                    "независимость",
                    "гуманизм",
                    "оригинальность",
                ],
                "lucky_numbers": [4, 7, 11, 22, 29],
                "lucky_colors": ["синий", "серебряный"],
            },
            YandexZodiacSign.PISCES: {
                "element": "water",
                "quality": "mutable",
                "ruling_planet": "Neptune",
                "keywords": [
                    "интуиция",
                    "сострадание",
                    "творчество",
                    "мистичность",
                ],
                "lucky_numbers": [3, 9, 12, 15, 18, 24],
                "lucky_colors": ["морской волны", "лавандовый"],
            },
        }

        # Шаблоны для гороскопов
        self.horoscope_templates = {
            "love": [
                "В любовных делах {period} будет особенно благоприятным временем.",
                "Венера дарует вам особую привлекательность {period}.",
                "Отношения могут выйти на новый уровень {period}.",
                "{period} принесет романтические сюрпризы.",
                "Время для открытых разговоров о чувствах наступает {period}.",
            ],
            "career": [
                "В профессиональной сфере {period} открываются новые возможности.",
                "Ваши усилия на работе {period} будут вознаграждены.",
                "Благоприятное время для карьерного роста наступает {period}.",
                "{period} принесет важные деловые контакты.",
                "Проекты, начатые {period}, имеют все шансы на успех.",
            ],
            "health": [
                "Обратите внимание на свое здоровье {period}.",
                "Энергетический потенциал {period} находится на высоком уровне.",
                "{period} благоприятно для начала новых оздоровительных практик.",
                "Слушайте сигналы своего тела {period}.",
                "Гармония души и тела особенно важна {period}.",
            ],
            "finances": [
                "Финансовое положение {period} стабилизируется.",
                "{period} благоприятно для инвестиций и крупных покупок.",
                "Будьте осторожны с тратами {period}.",
                "Новые источники дохода могут появиться {period}.",
                "{period} принесет финансовую ясность.",
            ],
        }

    def generate_personalized_horoscope(
        self,
        zodiac_sign: YandexZodiacSign,
        birth_date: Optional[date] = None,
        birth_time: Optional[datetime] = None,
        period: HoroscopePeriod = HoroscopePeriod.DAILY,
        target_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Генерирует персональный гороскоп."""

        if target_date is None:
            target_date = datetime.now()

        # Базовые характеристики знака
        sign_info = self.sign_characteristics.get(zodiac_sign, {})

        # Получаем текущие астрологические влияния
        astrological_influences = self._get_current_influences(
            target_date, zodiac_sign
        )

        # Генерируем прогноз по сферам
        spheres_forecast = self._generate_spheres_forecast(
            zodiac_sign, astrological_influences, period
        )

        # Вычисляем уровень энергии
        energy_level = self._calculate_energy_level(
            zodiac_sign, target_date, astrological_influences
        )

        # Генерируем счастливые числа и цвета
        lucky_elements = self._generate_lucky_elements(sign_info, target_date)

        general_forecast = self._generate_general_forecast(
            zodiac_sign, astrological_influences, period
        )

        return {
            "zodiac_sign": zodiac_sign.value,
            "period": period.value,
            "date": target_date.strftime("%Y-%m-%d"),
            "prediction": general_forecast,  # For backward compatibility with tests
            "general_forecast": general_forecast,
            "spheres": spheres_forecast,
            "energy_level": energy_level,
            "lucky_numbers": lucky_elements["numbers"],
            "lucky_colors": lucky_elements["colors"],
            "advice": self._generate_advice(
                zodiac_sign, astrological_influences
            ),
            "astrological_influences": astrological_influences,
        }

    def _get_current_influences(
        self, target_date: datetime, zodiac_sign: YandexZodiacSign
    ) -> Dict[str, Any]:
        """Получает текущие астрологические влияния."""

        # Получаем фазу Луны
        moon_phase = self.astro_calc.calculate_moon_phase(target_date)

        # Получаем планетные часы
        planetary_hours = self.astro_calc.get_planetary_hours(target_date)

        # Упрощенное определение важных транзитов
        important_transits = self._get_simplified_transits(
            target_date, zodiac_sign
        )

        return {
            "moon_phase": moon_phase,
            "planetary_hours": planetary_hours,
            "transits": important_transits,
            "season_influence": self._get_seasonal_influence(target_date),
        }

    def _get_simplified_transits(
        self, target_date: datetime, zodiac_sign: YandexZodiacSign
    ) -> List[Dict[str, str]]:
        """Упрощенное определение транзитов."""
        transits = []

        # Примерные циклы планет для упрощения
        day_of_year = target_date.timetuple().tm_yday

        # Меркурий (цикл ~88 дней)
        mercury_phase = (day_of_year % 88) / 88
        if mercury_phase < 0.33:
            transits.append(
                {
                    "planet": "Меркурий",
                    "aspect": "благоприятный",
                    "description": "Отличное время для общения и обучения",
                }
            )

        # Венера (цикл ~225 дней)
        venus_phase = (day_of_year % 225) / 225
        if venus_phase < 0.4:
            transits.append(
                {
                    "planet": "Венера",
                    "aspect": "гармоничный",
                    "description": "Благоприятно для любви и творчества",
                }
            )

        # Марс (цикл ~687 дней, упрощаем до 365)
        mars_phase = (day_of_year % 365) / 365
        if 0.2 < mars_phase < 0.6:
            transits.append(
                {
                    "planet": "Марс",
                    "aspect": "энергичный",
                    "description": "Время активных действий и инициатив",
                }
            )

        return transits

    def _get_seasonal_influence(self, target_date: datetime) -> Dict[str, str]:
        """Определяет сезонное влияние."""
        month = target_date.month

        if 3 <= month <= 5:
            return {"season": "весна", "influence": "обновление и рост"}
        elif 6 <= month <= 8:
            return {
                "season": "лето",
                "influence": "активность и самовыражение",
            }
        elif 9 <= month <= 11:
            return {"season": "осень", "influence": "сбор урожая и рефлексия"}
        else:
            return {
                "season": "зима",
                "influence": "внутреннее развитие и планирование",
            }

    def _generate_spheres_forecast(
        self,
        zodiac_sign: YandexZodiacSign,
        influences: Dict[str, Any],
        period: HoroscopePeriod,
    ) -> Dict[str, Dict[str, Any]]:
        """Генерирует прогноз по жизненным сферам."""

        period_str = period.value
        moon_influence = influences["moon_phase"]["phase_name"]

        spheres = {}

        for sphere in ["love", "career", "health", "finances"]:
            sphere_templates = self.horoscope_templates[sphere]
            base_text = random.choice(sphere_templates).format(
                period=period_str
            )

            # Добавляем влияние Луны
            moon_modifier = self._get_moon_modifier(sphere, moon_influence)
            if moon_modifier:
                base_text += f" {moon_modifier}"

            # Рассчитываем рейтинг сферы (1-5 звезд)
            rating = self._calculate_sphere_rating(
                sphere, zodiac_sign, influences
            )

            spheres[sphere] = {
                "forecast": base_text,
                "rating": rating,
                "advice": self._get_sphere_advice(sphere, rating, zodiac_sign),
            }

        return spheres

    def _get_moon_modifier(
        self, sphere: str, moon_phase: str
    ) -> Optional[str]:
        """Получает модификатор влияния Луны на сферу."""
        moon_modifiers = {
            "Новолуние": {
                "love": "Идеальное время для новых знакомств.",
                "career": "Начинайте новые проекты.",
                "health": "Время детоксикации и очищения.",
                "finances": "Планируйте бюджет на месяц вперед.",
            },
            "Полнолуние": {
                "love": "Эмоции достигают пика.",
                "career": "Результаты ваших усилий станут видны.",
                "health": "Будьте внимательны к переутомлению.",
                "finances": "Избегайте импульсивных трат.",
            },
            "Растущая Луна": {
                "love": "Отношения развиваются и крепнут.",
                "career": "Наращивайте усилия для достижения целей.",
                "health": "Организм хорошо усваивает питательные вещества.",
                "finances": "Благоприятное время для инвестиций.",
            },
            "Убывающая Луна": {
                "love": "Время для работы над отношениями.",
                "career": "Завершайте начатые дела.",
                "health": "Организм легче избавляется от токсинов.",
                "finances": "Сократите ненужные расходы.",
            },
        }

        return moon_modifiers.get(moon_phase, {}).get(sphere)

    def _calculate_sphere_rating(
        self,
        sphere: str,
        zodiac_sign: YandexZodiacSign,
        influences: Dict[str, Any],
    ) -> int:
        """Рассчитывает рейтинг сферы (1-5 звезд)."""

        base_rating = 3  # Нейтральная оценка

        # Влияние фазы Луны
        moon_phase = influences["moon_phase"]["phase_name"]
        moon_bonus = self._get_moon_sphere_bonus(sphere, moon_phase)

        # Влияние элемента знака
        sign_info = self.sign_characteristics.get(zodiac_sign, {})
        element = sign_info.get("element", "earth")
        element_bonus = self._get_element_sphere_bonus(sphere, element)

        # Влияние транзитов
        transit_bonus = 0
        for transit in influences.get("transits", []):
            if transit["aspect"] in ["благоприятный", "гармоничный"]:
                transit_bonus += 0.5
            elif transit["aspect"] == "энергичный" and sphere == "career":
                transit_bonus += 1

        # Рассчитываем итоговый рейтинг
        final_rating = base_rating + moon_bonus + element_bonus + transit_bonus

        # Ограничиваем диапазон 1-5
        return max(1, min(5, round(final_rating)))

    def _get_moon_sphere_bonus(self, sphere: str, moon_phase: str) -> float:
        """Получает бонус от фазы Луны для сферы."""
        moon_sphere_bonuses = {
            "Новолуние": {
                "career": 1,
                "health": 0.5,
                "finances": 0.5,
                "love": 0,
            },
            "Растущая Луна": {
                "love": 1,
                "career": 0.5,
                "finances": 1,
                "health": 0.5,
            },
            "Полнолуние": {
                "love": 1,
                "health": -0.5,
                "career": 0.5,
                "finances": -0.5,
            },
            "Убывающая Луна": {
                "health": 1,
                "finances": 0.5,
                "love": 0,
                "career": 0,
            },
        }

        return moon_sphere_bonuses.get(moon_phase, {}).get(sphere, 0)

    def _get_element_sphere_bonus(self, sphere: str, element: str) -> float:
        """Получает бонус от элемента знака для сферы."""
        element_sphere_bonuses = {
            "fire": {"career": 1, "love": 0.5, "health": 0.5, "finances": 0},
            "earth": {"finances": 1, "health": 0.5, "career": 0.5, "love": 0},
            "air": {"love": 0.5, "career": 0.5, "finances": 0.5, "health": 0},
            "water": {"love": 1, "health": 0.5, "finances": 0, "career": 0},
        }

        return element_sphere_bonuses.get(element, {}).get(sphere, 0)

    def _get_sphere_advice(
        self, sphere: str, rating: int, zodiac_sign: YandexZodiacSign
    ) -> str:
        """Получает совет для сферы жизни."""

        sphere_advice = {
            "love": {
                1: "Будьте терпеливы в отношениях, избегайте конфликтов.",
                2: "Время для работы над собой и своими чувствами.",
                3: "Поддерживайте открытое общение с партнером.",
                4: "Отличное время для романтических жестов.",
                5: "Любовь окружает вас, наслаждайтесь моментом!",
            },
            "career": {
                1: "Сосредоточьтесь на текущих задачах, избегайте новых инициатив.",
                2: "Время для обучения и развития профессиональных навыков.",
                3: "Работайте стабильно, результаты придут постепенно.",
                4: "Проявляйте инициативу, начальство это оценит.",
                5: "Смело беритесь за амбициозные проекты!",
            },
            "health": {
                1: "Обратите особое внимание на самочувствие.",
                2: "Введите здоровые привычки в свой распорядок дня.",
                3: "Поддерживайте баланс между работой и отдыхом.",
                4: "Отличное время для спорта и активного образа жизни.",
                5: "Ваша энергия на пике, используйте ее мудро!",
            },
            "finances": {
                1: "Будьте осторожны с тратами, ведите строгий учет.",
                2: "Время для планирования бюджета и экономии.",
                3: "Поддерживайте финансовую стабильность.",
                4: "Рассмотрите возможности для дополнительного дохода.",
                5: "Благоприятное время для инвестиций и крупных покупок!",
            },
        }

        return sphere_advice.get(sphere, {}).get(
            rating, "Следуйте своей интуиции."
        )

    def _generate_general_forecast(
        self,
        zodiac_sign: YandexZodiacSign,
        influences: Dict[str, Any],
        period: HoroscopePeriod,
    ) -> str:
        """Генерирует общий прогноз."""

        sign_info = self.sign_characteristics.get(zodiac_sign, {})
        ruling_planet = sign_info.get("ruling_planet", "Солнце")
        keywords = sign_info.get("keywords", ["гармония", "развитие"])

        # Базовый прогноз на основе характеристик знака
        keyword = random.choice(keywords)

        general_forecasts = [
            f"{period.value.capitalize()} подходит для развития вашей {keyword}.",
            f"Влияние {ruling_planet} поможет вам в вопросах {keyword}.",
            f"Звезды благоволят проявлению вашей природной {keyword}.",
            f"{period.value.capitalize()} принесет возможности для реализации {keyword}.",
        ]

        base_forecast = random.choice(general_forecasts)

        # Добавляем влияние текущих аспектов
        if influences.get("transits"):
            transit = random.choice(influences["transits"])
            base_forecast += f" {transit['description']}."

        return base_forecast

    def _calculate_energy_level(
        self,
        zodiac_sign: YandexZodiacSign,
        target_date: datetime,
        influences: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Рассчитывает уровень энергии."""

        base_energy = 60  # Базовый уровень энергии

        # Влияние фазы Луны
        moon_illumination = influences["moon_phase"]["illumination_percent"]
        moon_bonus = (moon_illumination - 50) / 5  # От -10 до +10

        # Влияние сезона
        month = target_date.month
        if 3 <= month <= 5:  # Весна
            seasonal_bonus = 15
        elif 6 <= month <= 8:  # Лето
            seasonal_bonus = 20
        elif 9 <= month <= 11:  # Осень
            seasonal_bonus = 5
        else:  # Зима
            seasonal_bonus = -5

        # Влияние элемента знака
        sign_info = self.sign_characteristics.get(zodiac_sign, {})
        element = sign_info.get("element", "earth")
        element_bonuses = {"fire": 15, "air": 10, "earth": 5, "water": 0}
        element_bonus = element_bonuses.get(element, 5)

        # Рассчитываем итоговый уровень
        total_energy = (
            base_energy + moon_bonus + seasonal_bonus + element_bonus
        )
        total_energy = max(10, min(100, total_energy))  # Ограничиваем 10-100%

        # Определяем описание уровня энергии
        if total_energy >= 80:
            description = "Очень высокий уровень энергии"
        elif total_energy >= 60:
            description = "Хороший уровень энергии"
        elif total_energy >= 40:
            description = "Умеренный уровень энергии"
        else:
            description = "Низкий уровень энергии"

        return {
            "level": round(total_energy),
            "description": description,
            "advice": self._get_energy_advice(total_energy),
        }

    def _get_energy_advice(self, energy_level: float) -> str:
        """Получает совет по уровню энергии."""
        if energy_level >= 80:
            return (
                "Используйте высокую энергию для достижения амбициозных целей."
            )
        elif energy_level >= 60:
            return (
                "Отличное время для активной деятельности и новых начинаний."
            )
        elif energy_level >= 40:
            return "Поддерживайте умеренную активность, не перегружайте себя."
        else:
            return "Время для отдыха и восстановления сил."

    def _generate_lucky_elements(
        self, sign_info: Dict[str, Any], target_date: datetime
    ) -> Dict[str, List]:
        """Генерирует счастливые числа и цвета."""

        base_numbers = sign_info.get("lucky_numbers", [7, 14, 21])
        base_colors = sign_info.get("lucky_colors", ["синий", "зеленый"])

        # Модифицируем числа на основе даты
        day_modifier = target_date.day % 10
        modified_numbers = [
            (num + day_modifier) % 50 + 1 for num in base_numbers[:3]
        ]

        # Добавляем дополнительное число на основе дня недели
        weekday_number = target_date.weekday() * 7 + day_modifier
        modified_numbers.append(weekday_number % 99 + 1)

        return {
            "numbers": sorted(list(set(modified_numbers))),
            "colors": base_colors,
        }

    def _generate_advice(
        self, zodiac_sign: YandexZodiacSign, influences: Dict[str, Any]
    ) -> str:
        """Генерирует персональный совет."""

        sign_info = self.sign_characteristics.get(zodiac_sign, {})
        keywords = sign_info.get("keywords", ["гармония"])

        advice_templates = [
            f"Сегодня особенно важно проявить вашу природную {random.choice(keywords)}.",
            f"Звезды советуют использовать вашу способность к {random.choice(keywords)}.",
            f"Доверьтесь своей интуиции в вопросах {random.choice(keywords)}.",
            f"Время активизировать вашу {random.choice(keywords)}.",
        ]

        base_advice = random.choice(advice_templates)

        # Добавляем совет на основе фазы Луны
        moon_phase = influences["moon_phase"]["phase_name"]
        moon_advice = {
            "Новолуние": "Загадайте желание и начните воплощать его в жизнь.",
            "Растущая Луна": "Наращивайте усилия для достижения целей.",
            "Полнолуние": "Время для завершения важных дел.",
            "Убывающая Луна": "Освободитесь от того, что больше не служит вам.",
        }

        additional_advice = moon_advice.get(moon_phase, "")
        if additional_advice:
            base_advice += f" {additional_advice}"

        return base_advice
