"""
Сервис генерации персональных гороскопов.
"""

import logging
import random
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.models.yandex_models import YandexZodiacSign
from app.services.astrology_calculator import AstrologyCalculator
from app.services.transit_calculator import TransitCalculator

logger = logging.getLogger(__name__)


class HoroscopePeriod(Enum):
    DAILY = "день"
    WEEKLY = "неделя"
    MONTHLY = "месяц"


class HoroscopeGenerator:
    """Генератор персональных гороскопов."""

    def __init__(self):
        self.astro_calc = AstrologyCalculator()
        self.transit_calc = TransitCalculator()

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
        logger.info(
            f"HOROSCOPE_GENERATION_START: sign={zodiac_sign.value}, period={period.value}, birth_date={birth_date}"
        )

        if target_date is None:
            target_date = datetime.now()
            logger.debug(
                f"HOROSCOPE_TARGET_DATE_DEFAULT: using_current_date={target_date.strftime('%Y-%m-%d')}"
            )
        else:
            logger.debug(
                f"HOROSCOPE_TARGET_DATE_PROVIDED: target_date={target_date.strftime('%Y-%m-%d')}"
            )

        # Базовые характеристики знака
        sign_info = self.sign_characteristics.get(zodiac_sign, {})
        logger.debug(
            f"HOROSCOPE_SIGN_INFO: element={sign_info.get('element')}, ruling_planet={sign_info.get('ruling_planet')}"
        )

        # Получаем текущие астрологические влияния
        logger.debug(
            "HOROSCOPE_INFLUENCES_START: calculating_astrological_influences"
        )
        astrological_influences = self._get_current_influences(
            target_date, zodiac_sign
        )
        logger.info(
            f"HOROSCOPE_INFLUENCES_CALCULATED: moon_phase={astrological_influences.get('moon_phase', {}).get('phase_name')}"
        )

        # Генерируем прогноз по сферам
        logger.debug("HOROSCOPE_SPHERES_START: generating_forecast_by_spheres")
        spheres_forecast = self._generate_spheres_forecast(
            zodiac_sign, astrological_influences, period
        )
        logger.info(
            f"HOROSCOPE_SPHERES_GENERATED: spheres_count={len(spheres_forecast)}"
        )

        # Вычисляем уровень энергии
        logger.debug("HOROSCOPE_ENERGY_START: calculating_energy_level")
        energy_level = self._calculate_energy_level(
            zodiac_sign, target_date, astrological_influences
        )
        logger.info(
            f"HOROSCOPE_ENERGY_CALCULATED: level={energy_level.get('level')}%, description='{energy_level.get('description')}'"
        )

        # Генерируем счастливые числа и цвета
        logger.debug("HOROSCOPE_LUCKY_START: generating_lucky_elements")
        lucky_elements = self._generate_lucky_elements(sign_info, target_date)
        logger.debug(
            f"HOROSCOPE_LUCKY_GENERATED: numbers={lucky_elements['numbers']}, colors={lucky_elements['colors']}"
        )

        logger.debug("HOROSCOPE_GENERAL_START: generating_general_forecast")
        general_forecast = self._generate_general_forecast(
            zodiac_sign, astrological_influences, period
        )
        logger.debug(
            f"HOROSCOPE_GENERAL_GENERATED: forecast_length={len(general_forecast)}"
        )

        result = {
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

        logger.info(
            f"HOROSCOPE_GENERATION_SUCCESS: sign={zodiac_sign.value}, total_fields={len(result)}"
        )
        return result

    def _get_current_influences(
        self, target_date: datetime, zodiac_sign: YandexZodiacSign
    ) -> Dict[str, Any]:
        """Получает текущие астрологические влияния."""
        logger.debug(
            f"INFLUENCES_CALCULATION_START: date={target_date.strftime('%Y-%m-%d')}, sign={zodiac_sign.value}"
        )

        # Получаем фазу Луны
        logger.debug("INFLUENCES_MOON_PHASE_START: calculating_moon_phase")
        moon_phase = self.astro_calc.calculate_moon_phase(target_date)
        logger.debug(
            f"INFLUENCES_MOON_PHASE_RESULT: phase={moon_phase.get('phase_name')}, illumination={moon_phase.get('illumination_percent')}%"
        )

        # Получаем планетные часы
        logger.debug(
            "INFLUENCES_PLANETARY_HOURS_START: calculating_planetary_hours"
        )
        planetary_hours = self.astro_calc.get_planetary_hours(target_date)
        logger.debug(
            f"INFLUENCES_PLANETARY_HOURS_RESULT: current_ruler={planetary_hours.get('current_ruler')}"
        )

        # Упрощенное определение важных транзитов
        logger.debug(
            "INFLUENCES_TRANSITS_START: calculating_simplified_transits"
        )
        important_transits = self._get_simplified_transits(
            target_date, zodiac_sign
        )
        logger.debug(
            f"INFLUENCES_TRANSITS_RESULT: transits_count={len(important_transits)}"
        )

        # Сезонные влияния
        logger.debug(
            "INFLUENCES_SEASONAL_START: calculating_seasonal_influence"
        )
        season_influence = self._get_seasonal_influence(target_date)
        logger.debug(
            f"INFLUENCES_SEASONAL_RESULT: season={season_influence.get('season')}"
        )

        result = {
            "moon_phase": moon_phase,
            "planetary_hours": planetary_hours,
            "transits": important_transits,
            "season_influence": season_influence,
        }

        logger.info(
            f"INFLUENCES_CALCULATION_SUCCESS: calculated_all_influences for {zodiac_sign.value}"
        )
        return result

    def _get_simplified_transits(
        self, target_date: datetime, zodiac_sign: YandexZodiacSign
    ) -> List[Dict[str, str]]:
        """Упрощенное определение транзитов."""
        logger.debug(
            f"TRANSITS_CALCULATION_START: date={target_date.strftime('%Y-%m-%d')}"
        )
        transits = []

        # Примерные циклы планет для упрощения
        day_of_year = target_date.timetuple().tm_yday
        logger.debug(f"TRANSITS_DAY_OF_YEAR: day={day_of_year}")

        # Меркурий (цикл ~88 дней)
        mercury_phase = (day_of_year % 88) / 88
        logger.debug(f"TRANSITS_MERCURY_PHASE: phase={mercury_phase:.2f}")
        if mercury_phase < 0.33:
            transits.append(
                {
                    "planet": "Меркурий",
                    "aspect": "благоприятный",
                    "description": "Отличное время для общения и обучения",
                }
            )
            logger.debug("TRANSITS_MERCURY_FAVORABLE: added_to_transits")

        # Венера (цикл ~225 дней)
        venus_phase = (day_of_year % 225) / 225
        logger.debug(f"TRANSITS_VENUS_PHASE: phase={venus_phase:.2f}")
        if venus_phase < 0.4:
            transits.append(
                {
                    "planet": "Венера",
                    "aspect": "гармоничный",
                    "description": "Благоприятно для любви и творчества",
                }
            )
            logger.debug("TRANSITS_VENUS_HARMONIOUS: added_to_transits")

        # Марс (цикл ~687 дней, упрощаем до 365)
        mars_phase = (day_of_year % 365) / 365
        logger.debug(f"TRANSITS_MARS_PHASE: phase={mars_phase:.2f}")
        if 0.2 < mars_phase < 0.6:
            transits.append(
                {
                    "planet": "Марс",
                    "aspect": "энергичный",
                    "description": "Время активных действий и инициатив",
                }
            )
            logger.debug("TRANSITS_MARS_ENERGETIC: added_to_transits")

        logger.debug(
            f"TRANSITS_CALCULATION_RESULT: found_transits={len(transits)}"
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
        logger.debug(
            f"SPHERES_FORECAST_START: sign={zodiac_sign.value}, period={period.value}"
        )

        period_str = period.value
        moon_influence = influences["moon_phase"]["phase_name"]
        logger.debug(f"SPHERES_MOON_INFLUENCE: phase={moon_influence}")

        spheres = {}

        for sphere in ["love", "career", "health", "finances"]:
            logger.debug(f"SPHERES_PROCESSING: sphere={sphere}")

            sphere_templates = self.horoscope_templates[sphere]
            base_text = random.choice(sphere_templates).format(
                period=period_str
            )
            logger.debug(
                f"SPHERES_BASE_TEXT: sphere={sphere}, text_length={len(base_text)}"
            )

            # Добавляем влияние Луны
            moon_modifier = self._get_moon_modifier(sphere, moon_influence)
            if moon_modifier:
                base_text += f" {moon_modifier}"
                logger.debug(
                    f"SPHERES_MOON_MODIFIER: sphere={sphere}, added_modifier"
                )
            else:
                logger.debug(
                    f"SPHERES_MOON_MODIFIER: sphere={sphere}, no_modifier_applied"
                )

            # Рассчитываем рейтинг сферы (1-5 звезд)
            rating = self._calculate_sphere_rating(
                sphere, zodiac_sign, influences
            )
            logger.debug(f"SPHERES_RATING: sphere={sphere}, rating={rating}")

            # Получаем совет для сферы
            advice = self._get_sphere_advice(sphere, rating, zodiac_sign)
            logger.debug(
                f"SPHERES_ADVICE: sphere={sphere}, advice_length={len(advice)}"
            )

            spheres[sphere] = {
                "forecast": base_text,
                "rating": rating,
                "advice": advice,
            }

        logger.info(
            f"SPHERES_FORECAST_SUCCESS: generated_spheres={list(spheres.keys())}"
        )
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
        logger.debug(
            f"ENERGY_CALCULATION_START: sign={zodiac_sign.value}, date={target_date.strftime('%Y-%m-%d')}"
        )

        base_energy = 60  # Базовый уровень энергии
        logger.debug(f"ENERGY_BASE: level={base_energy}")

        # Влияние фазы Луны
        moon_illumination = influences["moon_phase"]["illumination_percent"]
        moon_bonus = (moon_illumination - 50) / 5  # От -10 до +10
        logger.debug(
            f"ENERGY_MOON_BONUS: illumination={moon_illumination}%, bonus={moon_bonus:.1f}"
        )

        # Влияние сезона
        month = target_date.month
        if 3 <= month <= 5:  # Весна
            seasonal_bonus = 15
            season = "spring"
        elif 6 <= month <= 8:  # Лето
            seasonal_bonus = 20
            season = "summer"
        elif 9 <= month <= 11:  # Осень
            seasonal_bonus = 5
            season = "autumn"
        else:  # Зима
            seasonal_bonus = -5
            season = "winter"
        logger.debug(
            f"ENERGY_SEASONAL_BONUS: season={season}, bonus={seasonal_bonus}"
        )

        # Влияние элемента знака
        sign_info = self.sign_characteristics.get(zodiac_sign, {})
        element = sign_info.get("element", "earth")
        element_bonuses = {"fire": 15, "air": 10, "earth": 5, "water": 0}
        element_bonus = element_bonuses.get(element, 5)
        logger.debug(
            f"ENERGY_ELEMENT_BONUS: element={element}, bonus={element_bonus}"
        )

        # Рассчитываем итоговый уровень
        total_energy = (
            base_energy + moon_bonus + seasonal_bonus + element_bonus
        )
        raw_energy = total_energy
        total_energy = max(10, min(100, total_energy))  # Ограничиваем 10-100%
        logger.debug(
            f"ENERGY_CALCULATION: raw={raw_energy:.1f}, clamped={total_energy}"
        )

        # Определяем описание уровня энергии
        if total_energy >= 80:
            description = "Очень высокий уровень энергии"
        elif total_energy >= 60:
            description = "Хороший уровень энергии"
        elif total_energy >= 40:
            description = "Умеренный уровень энергии"
        else:
            description = "Низкий уровень энергии"

        logger.debug(
            f"ENERGY_DESCRIPTION: level={total_energy}, description='{description}'"
        )

        result = {
            "level": round(total_energy),
            "description": description,
            "advice": self._get_energy_advice(total_energy),
        }

        logger.info(
            f"ENERGY_CALCULATION_SUCCESS: final_level={result['level']}%"
        )
        return result

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
        logger.debug(f"ADVICE_GENERATION_START: sign={zodiac_sign.value}")

        sign_info = self.sign_characteristics.get(zodiac_sign, {})
        keywords = sign_info.get("keywords", ["гармония"])
        logger.debug(
            f"ADVICE_KEYWORDS: sign={zodiac_sign.value}, keywords={keywords}"
        )

        advice_templates = [
            f"Сегодня особенно важно проявить вашу природную {random.choice(keywords)}.",
            f"Звезды советуют использовать вашу способность к {random.choice(keywords)}.",
            f"Доверьтесь своей интуиции в вопросах {random.choice(keywords)}.",
            f"Время активизировать вашу {random.choice(keywords)}.",
        ]

        base_advice = random.choice(advice_templates)
        logger.debug(f"ADVICE_BASE_TEMPLATE: length={len(base_advice)}")

        # Добавляем совет на основе фазы Луны
        moon_phase = influences["moon_phase"]["phase_name"]
        logger.debug(f"ADVICE_MOON_PHASE: phase={moon_phase}")

        moon_advice = {
            "Новолуние": "Загадайте желание и начните воплощать его в жизнь.",
            "Растущая Луна": "Наращивайте усилия для достижения целей.",
            "Полнолуние": "Время для завершения важных дел.",
            "Убывающая Луна": "Освободитесь от того, что больше не служит вам.",
        }

        additional_advice = moon_advice.get(moon_phase, "")
        if additional_advice:
            base_advice += f" {additional_advice}"
            logger.debug(
                f"ADVICE_MOON_ADDED: moon_advice='{additional_advice}'"
            )
        else:
            logger.debug("ADVICE_MOON_SKIPPED: no_specific_advice_for_phase")

        logger.info(
            f"ADVICE_GENERATION_SUCCESS: final_length={len(base_advice)}"
        )
        return base_advice

    # Enhanced methods with transit integration

    def generate_enhanced_horoscope(
        self,
        sign: YandexZodiacSign,
        period: HoroscopePeriod = HoroscopePeriod.DAILY,
        natal_chart_data: Optional[Dict[str, Any]] = None,
        include_transits: bool = True,
        target_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Генерирует улучшенный гороскоп с интеграцией транзитов.

        Args:
            sign: Знак зодиака
            period: Период гороскопа
            natal_chart_data: Данные натальной карты (опционально)
            include_transits: Включать анализ транзитов
            target_date: Дата для гороскопа
        """
        logger.info(
            f"HOROSCOPE_ENHANCED_START: sign={sign.value}, period={period.value}, transits={include_transits}"
        )

        if target_date is None:
            target_date = date.today()

        # Генерируем базовый гороскоп
        base_horoscope = self.generate_horoscope(sign, period, target_date)

        enhanced_horoscope = {
            "sign": sign.value,
            "period": period.value,
            "date": target_date.isoformat(),
            "base_horoscope": base_horoscope,
        }

        # Добавляем анализ транзитов, если доступны данные натальной карты
        if (
            include_transits
            and natal_chart_data
            and self.transit_calc.is_enhanced_features_available().get(
                "enhanced_analysis", False
            )
        ):
            try:
                transit_analysis = self._get_transit_enhanced_content(
                    natal_chart_data, period, target_date
                )
                enhanced_horoscope["transit_influences"] = transit_analysis

                # Объединяем базовый гороскоп с транзитным анализом
                enhanced_horoscope[
                    "integrated_forecast"
                ] = self._integrate_base_and_transit_content(
                    base_horoscope, transit_analysis
                )

                logger.info(
                    "HOROSCOPE_ENHANCED_TRANSIT_SUCCESS: Transit analysis integrated"
                )
            except Exception as e:
                logger.error(f"HOROSCOPE_ENHANCED_TRANSIT_ERROR: {e}")
                enhanced_horoscope["transit_influences"] = {
                    "error": "Transit analysis unavailable"
                }
        else:
            logger.info(
                "HOROSCOPE_ENHANCED_TRANSIT_SKIPPED: No natal chart data or transits disabled"
            )

        # Добавляем улучшенные рекомендации
        enhanced_horoscope[
            "enhanced_recommendations"
        ] = self._generate_enhanced_recommendations(
            sign,
            period,
            target_date,
            enhanced_horoscope.get("transit_influences", {}),
        )

        # Добавляем энергетический анализ
        enhanced_horoscope["energy_analysis"] = self._generate_energy_analysis(
            sign, target_date, enhanced_horoscope.get("transit_influences", {})
        )

        logger.info("HOROSCOPE_ENHANCED_SUCCESS: Enhanced horoscope generated")
        return enhanced_horoscope

    def generate_transit_forecast(
        self, natal_chart_data: Dict[str, Any], forecast_days: int = 7
    ) -> Dict[str, Any]:
        """
        Генерирует прогноз на основе транзитов.

        Args:
            natal_chart_data: Данные натальной карты
            forecast_days: Количество дней для прогноза
        """
        logger.info(f"HOROSCOPE_TRANSIT_FORECAST_START: {forecast_days} days")

        try:
            # Получаем период прогноза транзитов
            period_forecast = self.transit_calc.get_period_forecast(
                natal_chart_data, forecast_days
            )

            # Получаем важные транзиты
            important_transits = self.transit_calc.get_important_transits(
                natal_chart_data, lookback_days=7, lookahead_days=forecast_days
            )

            # Создаем прогноз
            forecast = {
                "forecast_period": f"{forecast_days} дней",
                "generated_date": date.today().isoformat(),
                "period_forecast": period_forecast,
                "important_transits": important_transits,
                "daily_guidance": self._create_daily_guidance_from_transits(
                    period_forecast
                ),
                "key_themes": self._extract_key_themes_from_transits(
                    period_forecast, important_transits
                ),
                "timing_advice": self._create_timing_advice_from_transits(
                    period_forecast, important_transits
                ),
            }

            logger.info("HOROSCOPE_TRANSIT_FORECAST_SUCCESS")
            return forecast

        except Exception as e:
            logger.error(f"HOROSCOPE_TRANSIT_FORECAST_ERROR: {e}")
            return {
                "error": "Не удалось создать прогноз на основе транзитов",
                "forecast_period": f"{forecast_days} дней",
                "generated_date": date.today().isoformat(),
            }

    def generate_comprehensive_analysis(
        self, natal_chart_data: Dict[str, Any], analysis_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Генерирует комплексный астрологический анализ.

        Args:
            natal_chart_data: Данные натальной карты
            analysis_period_days: Период анализа в днях
        """
        logger.info(
            f"HOROSCOPE_COMPREHENSIVE_START: {analysis_period_days} days analysis"
        )

        try:
            # Получаем комплексный анализ транзитов
            comprehensive_transit_analysis = (
                self.transit_calc.get_comprehensive_transit_analysis(
                    natal_chart_data, analysis_period_days
                )
            )

            # Добавляем гороскопную интерпретацию
            analysis = {
                "analysis_type": "comprehensive",
                "analysis_period": f"{analysis_period_days} дней",
                "generated_date": date.today().isoformat(),
                # Основной анализ транзитов
                "transit_analysis": comprehensive_transit_analysis,
                # Интерпретация для пользователя
                "user_interpretation": self._create_user_friendly_interpretation(
                    comprehensive_transit_analysis
                ),
                # Практические рекомендации
                "practical_guidance": self._create_practical_guidance(
                    comprehensive_transit_analysis
                ),
                # Духовные инсайты
                "spiritual_insights": self._create_spiritual_insights(
                    comprehensive_transit_analysis
                ),
            }

            logger.info("HOROSCOPE_COMPREHENSIVE_SUCCESS")
            return analysis

        except Exception as e:
            logger.error(f"HOROSCOPE_COMPREHENSIVE_ERROR: {e}")
            return {
                "error": "Не удалось создать комплексный анализ",
                "analysis_type": "comprehensive",
                "analysis_period": f"{analysis_period_days} дней",
                "generated_date": date.today().isoformat(),
            }

    # Helper methods for enhanced functionality

    def _get_transit_enhanced_content(
        self,
        natal_chart_data: Dict[str, Any],
        period: HoroscopePeriod,
        target_date: date,
    ) -> Dict[str, Any]:
        """Получает контент на основе анализа транзитов."""

        if period == HoroscopePeriod.DAILY:
            # Для ежедневного гороскопа - текущие транзиты
            current_transits = self.transit_calc.get_enhanced_current_transits(
                natal_chart_data,
                datetime.combine(target_date, datetime.min.time()),
            )

            return {
                "type": "daily_transits",
                "current_transits": current_transits,
                "daily_influences": current_transits.get(
                    "daily_influences", []
                ),
                "energy_level": current_transits.get(
                    "energy_assessment", {}
                ).get("description", "умеренная энергия"),
                "timing_recommendations": current_transits.get(
                    "timing_recommendations", []
                ),
            }

        elif period == HoroscopePeriod.WEEKLY:
            # Для недельного гороскопа - прогноз на 7 дней
            period_forecast = self.transit_calc.get_period_forecast(
                natal_chart_data,
                days=7,
                start_date=datetime.combine(target_date, datetime.min.time()),
            )

            return {
                "type": "weekly_forecast",
                "period_forecast": period_forecast,
                "weekly_themes": period_forecast.get("overall_themes", []),
                "important_dates": period_forecast.get("important_dates", []),
                "general_advice": period_forecast.get("general_advice", ""),
            }

        elif period == HoroscopePeriod.MONTHLY:
            # Для месячного гороскопа - прогноз на 30 дней + лунар
            period_forecast = self.transit_calc.get_period_forecast(
                natal_chart_data,
                days=30,
                start_date=datetime.combine(target_date, datetime.min.time()),
            )

            # Добавляем лунар для месяца
            lunar_return = self.transit_calc.get_enhanced_lunar_return(
                natal_chart_data, target_date.month, target_date.year
            )

            return {
                "type": "monthly_forecast",
                "period_forecast": period_forecast,
                "lunar_return": lunar_return,
                "monthly_themes": period_forecast.get("overall_themes", []),
                "lunar_guidance": lunar_return.get("emotional_guidance", []),
                "important_dates": period_forecast.get("important_dates", []),
            }

        return {"type": "basic", "message": "Транзитный анализ недоступен"}

    def _integrate_base_and_transit_content(
        self, base_horoscope: Dict[str, Any], transit_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Интегрирует базовый гороскоп с транзитным анализом."""

        integrated = {
            "base_forecast": base_horoscope.get("forecast", ""),
            "transit_overlay": "",
            "combined_advice": [],
            "energy_synthesis": "",
            "timing_guidance": [],
        }

        # Объединяем прогнозы
        base_forecast = base_horoscope.get("forecast", "")
        transit_influences = transit_analysis.get("daily_influences", [])

        if transit_influences:
            transit_overlay = f"Астрологические влияния: {'. '.join(transit_influences[:2])}."
            integrated["transit_overlay"] = transit_overlay
            integrated["base_forecast"] = f"{base_forecast} {transit_overlay}"

        # Объединяем советы
        base_advice = base_horoscope.get("advice", "")
        transit_timing = transit_analysis.get("timing_recommendations", [])

        combined_advice = [base_advice] if base_advice else []
        combined_advice.extend(transit_timing[:2])
        integrated["combined_advice"] = combined_advice

        # Синтезируем энергию
        base_energy = base_horoscope.get("energy_level", 50)
        transit_energy = transit_analysis.get(
            "energy_level", "умеренная энергия"
        )

        integrated[
            "energy_synthesis"
        ] = f"Базовая энергия: {base_energy}%. Транзитное влияние: {transit_energy}"

        return integrated

    def _generate_enhanced_recommendations(
        self,
        sign: YandexZodiacSign,
        period: HoroscopePeriod,
        target_date: date,
        transit_influences: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Генерирует улучшенные рекомендации."""

        recommendations = {
            "general": [],
            "relationships": [],
            "career": [],
            "health": [],
            "spiritual": [],
        }

        # Базовые рекомендации по знаку
        sign_keywords = self.sign_characteristics.get(sign, {}).get(
            "keywords", []
        )

        if "лидерство" in sign_keywords:
            recommendations["career"].append(
                "Проявите инициативу в профессиональных делах"
            )
        if "стабильность" in sign_keywords:
            recommendations["general"].append(
                "Сосредоточьтесь на создании устойчивых основ"
            )
        if "общение" in sign_keywords:
            recommendations["relationships"].append(
                "Активно взаимодействуйте с окружающими"
            )

        # Рекомендации на основе транзитов
        if transit_influences and not transit_influences.get("error"):
            transit_timing = transit_influences.get(
                "timing_recommendations", []
            )
            for rec in transit_timing[:2]:
                recommendations["general"].append(rec)

            # Анализируем темы транзитов
            if "weekly_themes" in transit_influences:
                for theme in transit_influences["weekly_themes"][:2]:
                    if "отношения" in theme.lower():
                        recommendations["relationships"].append(
                            f"Фокус на теме: {theme}"
                        )
                    elif "карьера" in theme.lower():
                        recommendations["career"].append(
                            f"Фокус на теме: {theme}"
                        )

            # Эмоциональное руководство из лунара
            if "lunar_guidance" in transit_influences:
                recommendations["spiritual"].extend(
                    transit_influences["lunar_guidance"][:2]
                )

        # Заполняем пустые категории базовыми советами
        if not recommendations["relationships"]:
            recommendations["relationships"] = [
                "Уделите внимание близким отношениям"
            ]
        if not recommendations["career"]:
            recommendations["career"] = [
                "Сосредоточьтесь на текущих профессиональных задачах"
            ]
        if not recommendations["health"]:
            recommendations["health"] = [
                "Поддерживайте баланс между активностью и отдыхом"
            ]
        if not recommendations["spiritual"]:
            recommendations["spiritual"] = [
                "Найдите время для внутренней рефлексии"
            ]

        return recommendations

    def _generate_energy_analysis(
        self,
        sign: YandexZodiacSign,
        target_date: date,
        transit_influences: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Генерирует анализ энергетических влияний."""

        energy_analysis = {
            "overall_level": 50,  # Базовый уровень
            "description": "умеренная",
            "sources": [],
            "recommendations": [],
            "peak_times": [],
            "rest_times": [],
        }

        # Базовая энергия знака
        element = self.sign_characteristics.get(sign, {}).get("element", "")

        if element == "fire":
            energy_analysis["overall_level"] += 15
            energy_analysis["sources"].append("Огненная энергия знака")
        elif element == "air":
            energy_analysis["overall_level"] += 10
            energy_analysis["sources"].append("Воздушная активность знака")
        elif element == "earth":
            energy_analysis["overall_level"] += 5
            energy_analysis["sources"].append("Земная стабильность знака")
        elif element == "water":
            energy_analysis["overall_level"] -= 5
            energy_analysis["sources"].append("Водная интуитивность знака")

        # Влияние транзитов на энергию
        if transit_influences and not transit_influences.get("error"):
            if "energy_level" in transit_influences:
                energy_desc = transit_influences["energy_level"]
                if "высокая" in energy_desc:
                    energy_analysis["overall_level"] += 20
                    energy_analysis["sources"].append("Активирующие транзиты")
                elif "низкая" in energy_desc:
                    energy_analysis["overall_level"] -= 15
                    energy_analysis["sources"].append("Замедляющие транзиты")

        # Лунное влияние
        current_moon_phase = self.astro_calc.calculate_moon_phase(
            datetime.combine(target_date, datetime.min.time())
        )
        moon_phase_name = current_moon_phase.get("phase_name", "")

        if moon_phase_name in ["Новолуние", "Растущая Луна"]:
            energy_analysis["overall_level"] += 10
            energy_analysis["sources"].append(f"Поддержка {moon_phase_name}")
        elif moon_phase_name == "Полнолуние":
            energy_analysis["overall_level"] += 15
            energy_analysis["sources"].append("Энергия Полнолуния")

        # Нормализуем уровень энергии
        energy_analysis["overall_level"] = max(
            0, min(100, energy_analysis["overall_level"])
        )

        # Определяем описание
        level = energy_analysis["overall_level"]
        if level >= 80:
            energy_analysis["description"] = "очень высокая"
            energy_analysis["recommendations"] = [
                "Используйте пик энергии",
                "Не перенапрягайтесь",
            ]
        elif level >= 60:
            energy_analysis["description"] = "повышенная"
            energy_analysis["recommendations"] = [
                "Время для активных действий",
                "Планируйте важные дела",
            ]
        elif level >= 40:
            energy_analysis["description"] = "умеренная"
            energy_analysis["recommendations"] = [
                "Сохраняйте баланс",
                "Следуйте естественным ритмам",
            ]
        elif level >= 20:
            energy_analysis["description"] = "пониженная"
            energy_analysis["recommendations"] = [
                "Больше отдыхайте",
                "Избегайте стресса",
            ]
        else:
            energy_analysis["description"] = "низкая"
            energy_analysis["recommendations"] = [
                "Необходим полноценный отдых",
                "Восстановите силы",
            ]

        return energy_analysis

    def _create_daily_guidance_from_transits(
        self, period_forecast: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Создает ежедневные рекомендации из прогноза транзитов."""
        guidance = []

        daily_forecasts = period_forecast.get("daily_forecasts", [])

        for day_data in daily_forecasts:
            day_guidance = {
                "date": day_data.get("date", ""),
                "energy": day_data.get("energy_level", "умеренная"),
                "main_themes": ", ".join(day_data.get("main_influences", [])),
                "recommendations": "; ".join(
                    day_data.get("recommendations", [])
                ),
            }
            guidance.append(day_guidance)

        return guidance[:7]  # Ограничиваем неделей

    def _extract_key_themes_from_transits(
        self,
        period_forecast: Dict[str, Any],
        important_transits: Dict[str, Any],
    ) -> List[str]:
        """Извлекает ключевые темы из транзитов."""
        themes = set()

        # Из периодного прогноза
        themes.update(period_forecast.get("overall_themes", []))

        # Из важных транзитов
        themes.update(important_transits.get("life_themes", []))

        return list(themes)[:5]

    def _create_timing_advice_from_transits(
        self,
        period_forecast: Dict[str, Any],
        important_transits: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """Создает советы по таймингу из транзитов."""
        timing_advice = []

        # Из важных дат
        important_dates = period_forecast.get("important_dates", [])
        for date_info in important_dates[:3]:
            timing_advice.append(
                {
                    "date": date_info.get("date", ""),
                    "event": date_info.get("event", ""),
                    "advice": date_info.get("significance", ""),
                }
            )

        # Из подготовки к транзитам
        prep_advice = important_transits.get("preparation_advice", [])
        for advice in prep_advice[:2]:
            timing_advice.append(
                {
                    "period": "долгосрочно",
                    "advice": advice,
                    "category": "подготовка",
                }
            )

        return timing_advice

    def _create_user_friendly_interpretation(
        self, comprehensive_analysis: Dict[str, Any]
    ) -> Dict[str, str]:
        """Создает пользовательскую интерпретацию комплексного анализа."""

        # Извлекаем основные компоненты
        current_transits = comprehensive_analysis.get("current_transits", {})
        life_phase = comprehensive_analysis.get("life_phase_analysis", {})
        integrated_themes = comprehensive_analysis.get("integrated_themes", [])
        executive_summary = comprehensive_analysis.get("executive_summary", "")

        interpretation = {
            "current_moment": current_transits.get(
                "summary", "Спокойный период развития"
            ),
            "life_phase": f"Вы находитесь в фазе: {life_phase.get('life_stage', 'развития')}",
            "main_themes": f"Основные темы периода: {', '.join(integrated_themes[:3])}"
            if integrated_themes
            else "Время для общего развития",
            "overall_message": executive_summary
            or "Период стабильного роста с возможностями для развития",
        }

        return interpretation

    def _create_practical_guidance(
        self, comprehensive_analysis: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Создает практические рекомендации из комплексного анализа."""

        timing_recs = comprehensive_analysis.get("timing_recommendations", [])
        integrated_themes = comprehensive_analysis.get("integrated_themes", [])

        guidance = {
            "immediate_actions": [],
            "weekly_focus": [],
            "monthly_planning": [],
        }

        # Немедленные действия
        for rec in timing_recs:
            if rec.get("period") == "сейчас":
                guidance["immediate_actions"].append(
                    rec.get("recommendation", "")
                )

        # Недельный фокус на основе тем
        for theme in integrated_themes[:2]:
            if theme == "отношения":
                guidance["weekly_focus"].append(
                    "Уделите время укреплению отношений"
                )
            elif theme == "карьера":
                guidance["weekly_focus"].append(
                    "Сосредоточьтесь на профессиональных задачах"
                )
            elif theme == "здоровье":
                guidance["weekly_focus"].append(
                    "Позаботьтесь о физическом и эмоциональном здоровье"
                )

        # Месячное планирование
        for rec in timing_recs:
            if rec.get("period") == "долгосрочно":
                guidance["monthly_planning"].append(
                    rec.get("recommendation", "")
                )

        # Заполняем пустые категории базовыми советами
        if not guidance["immediate_actions"]:
            guidance["immediate_actions"] = [
                "Начните день с осознанности и ясного намерения"
            ]
        if not guidance["weekly_focus"]:
            guidance["weekly_focus"] = [
                "Поддерживайте баланс между работой и отдыхом"
            ]
        if not guidance["monthly_planning"]:
            guidance["monthly_planning"] = [
                "Планируйте будущее с учетом текущих возможностей"
            ]

        return guidance

    def _create_spiritual_insights(
        self, comprehensive_analysis: Dict[str, Any]
    ) -> Dict[str, str]:
        """Создает духовные инсайты из комплексного анализа."""

        spiritual_guidance = comprehensive_analysis.get(
            "spiritual_guidance", ""
        )
        life_phase = comprehensive_analysis.get("life_phase_analysis", {})
        progressions = comprehensive_analysis.get("progressions", {})

        insights = {
            "soul_purpose": "Ваша душа стремится к развитию через текущие жизненные обстоятельства",
            "growth_opportunity": spiritual_guidance
            or "Каждый момент несет возможности для осознанного роста",
            "life_lesson": life_phase.get(
                "key_lessons", "Принятие и интеграция жизненного опыта"
            ),
            "spiritual_evolution": progressions.get(
                "spiritual_evolution",
                "Постепенное развитие сознания через опыт",
            ),
        }

        return insights
