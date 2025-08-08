"""
Сервис расчета и интерпретации натальной карты.
Расширен поддержкой полного функционала Kerykeion.
"""

import logging
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional

import pytz

from app.services.astrology_calculator import AstrologyCalculator
from app.services.kerykeion_service import KerykeionService, HouseSystem, ZodiacType

logger = logging.getLogger(__name__)


class NatalChartCalculator:
    """Калькулятор натальной карты."""

    def __init__(self):
        self.astro_calc = AstrologyCalculator()
        self.kerykeion_service = KerykeionService()
        logger.info(f"NATAL_CHART_CALCULATOR_INIT: Kerykeion available = {self.kerykeion_service.is_available()}")

        # Интерпретации планет в знаках
        self.planet_sign_interpretations = {
            "Sun": {
                "description": "Ваша основная сущность, эго, жизненная сила",
                "keywords": [
                    "индивидуальность",
                    "творчество",
                    "лидерство",
                    "самовыражение",
                ],
            },
            "Moon": {
                "description": "Эмоциональная природа, потребности, инстинкты",
                "keywords": ["эмоции", "интуиция", "семья", "подсознание"],
            },
            "Mercury": {
                "description": "Мышление, общение, обучение",
                "keywords": [
                    "коммуникация",
                    "логика",
                    "анализ",
                    "любознательность",
                ],
            },
            "Venus": {
                "description": "Любовь, красота, ценности, отношения",
                "keywords": [
                    "любовь",
                    "гармония",
                    "искусство",
                    "привлекательность",
                ],
            },
            "Mars": {
                "description": "Энергия, действие, желания, агрессия",
                "keywords": [
                    "энергия",
                    "инициатива",
                    "страсть",
                    "соперничество",
                ],
            },
            "Jupiter": {
                "description": "Рост, расширение, мудрость, удача",
                "keywords": [
                    "оптимизм",
                    "философия",
                    "путешествия",
                    "изобилие",
                ],
            },
            "Saturn": {
                "description": "Дисциплина, ограничения, ответственность",
                "keywords": [
                    "дисциплина",
                    "терпение",
                    "структура",
                    "мудрость",
                ],
            },
            "Uranus": {
                "description": "Оригинальность, инновации, свобода",
                "keywords": [
                    "независимость",
                    "инновации",
                    "бунтарство",
                    "интуиция",
                ],
            },
            "Neptune": {
                "description": "Духовность, иллюзии, творчество",
                "keywords": [
                    "мистицизм",
                    "сострадание",
                    "творчество",
                    "иллюзии",
                ],
            },
            "Pluto": {
                "description": "Трансформация, власть, регенерация",
                "keywords": [
                    "трансформация",
                    "сила воли",
                    "глубина",
                    "возрождение",
                ],
            },
        }

        # Значения домов
        self.house_meanings = {
            1: {
                "name": "Дом личности",
                "description": "Ваша внешность, первое впечатление, подход к жизни",
                "keywords": ["личность", "внешность", "начинания", "энергия"],
            },
            2: {
                "name": "Дом ценностей",
                "description": "Деньги, материальные ценности, самооценка",
                "keywords": ["деньги", "ценности", "таланты", "ресурсы"],
            },
            3: {
                "name": "Дом общения",
                "description": "Общение, обучение, близкие родственники, короткие поездки",
                "keywords": [
                    "общение",
                    "обучение",
                    "братья/сестры",
                    "поездки",
                ],
            },
            4: {
                "name": "Дом дома и семьи",
                "description": "Семья, дом, корни, эмоциональная безопасность",
                "keywords": ["семья", "дом", "корни", "традиции"],
            },
            5: {
                "name": "Дом творчества",
                "description": "Творчество, дети, романтика, хобби, самовыражение",
                "keywords": ["творчество", "дети", "романтика", "развлечения"],
            },
            6: {
                "name": "Дом здоровья и служения",
                "description": "Здоровье, работа, рутина, служение другим",
                "keywords": ["здоровье", "работа", "служение", "привычки"],
            },
            7: {
                "name": "Дом партнерства",
                "description": "Брак, партнерство, открытые враги, договоры",
                "keywords": [
                    "партнерство",
                    "брак",
                    "сотрудничество",
                    "контракты",
                ],
            },
            8: {
                "name": "Дом трансформации",
                "description": "Смерть и возрождение, общие ресурсы, оккультизм",
                "keywords": [
                    "трансформация",
                    "тайны",
                    "общие ресурсы",
                    "кризисы",
                ],
            },
            9: {
                "name": "Дом философии",
                "description": "Высшее образование, философия, религия, дальние путешествия",
                "keywords": [
                    "философия",
                    "религия",
                    "путешествия",
                    "высшее образование",
                ],
            },
            10: {
                "name": "Дом карьеры",
                "description": "Карьера, репутация, социальный статус, призвание",
                "keywords": ["карьера", "репутация", "статус", "призвание"],
            },
            11: {
                "name": "Дом дружбы и надежд",
                "description": "Друзья, группы, надежды, мечты, социальные сети",
                "keywords": ["друзья", "группы", "надежды", "социальные сети"],
            },
            12: {
                "name": "Дом подсознания",
                "description": "Подсознание, тайны, изоляция, духовность, карма",
                "keywords": ["подсознание", "духовность", "карма", "изоляция"],
            },
        }

        # Аспекты и их значения
        self.aspect_interpretations = {
            "Соединение": {
                "angle": 0,
                "description": "Слияние энергий планет",
                "nature": "нейтральный",
                "strength": "очень сильный",
            },
            "Секстиль": {
                "angle": 60,
                "description": "Гармоничное взаимодействие",
                "nature": "позитивный",
                "strength": "умеренный",
            },
            "Квадрат": {
                "angle": 90,
                "description": "Напряжение и вызовы",
                "nature": "напряженный",
                "strength": "сильный",
            },
            "Трин": {
                "angle": 120,
                "description": "Естественная гармония",
                "nature": "позитивный",
                "strength": "сильный",
            },
            "Оппозиция": {
                "angle": 180,
                "description": "Противоположности и баланс",
                "nature": "напряженный",
                "strength": "очень сильный",
            },
        }

    def calculate_natal_chart(
        self,
        birth_date: date,
        birth_time: Optional[time] = None,
        birth_place: Optional[Dict[str, float]] = None,
        timezone_str: str = "Europe/Moscow",
    ) -> Dict[str, Any]:
        """Вычисляет натальную карту."""

        # Создаем datetime объект
        if birth_time is None:
            birth_time = time(12, 0)  # Полдень по умолчанию

        birth_datetime = datetime.combine(birth_date, birth_time)

        # Устанавливаем временную зону
        try:
            timezone = pytz.timezone(timezone_str)
            birth_datetime = timezone.localize(birth_datetime)
        except Exception:
            # Если временная зона некорректна, используем UTC
            birth_datetime = pytz.UTC.localize(birth_datetime)

        # Координаты места рождения (по умолчанию Москва)
        if birth_place is None:
            birth_place = {"latitude": 55.7558, "longitude": 37.6176}

        # Вычисляем позиции планет
        planet_positions = self.astro_calc.calculate_planet_positions(
            birth_datetime, birth_place["latitude"], birth_place["longitude"]
        )

        # Вычисляем дома
        houses = self.astro_calc.calculate_houses(
            birth_datetime, birth_place["latitude"], birth_place["longitude"]
        )

        # Вычисляем аспекты
        aspects = self.astro_calc.calculate_aspects(planet_positions)

        # Создаем интерпретацию карты
        interpretation = self._create_chart_interpretation(
            planet_positions, houses, aspects
        )

        return {
            "birth_info": {
                "date": birth_date.isoformat(),
                "time": birth_time.strftime("%H:%M")
                if birth_time
                else "12:00",
                "place": birth_place,
                "timezone": timezone_str,
            },
            "planets": planet_positions,
            "houses": houses,
            "aspects": aspects,
            "interpretation": interpretation,
            "chart_signature": self._calculate_chart_signature(
                planet_positions
            ),
            "dominant_elements": self._calculate_dominant_elements(
                planet_positions
            ),
            "chart_shape": self._determine_chart_shape(planet_positions),
        }

    def _create_chart_interpretation(
        self,
        planets: Dict[str, Dict[str, Any]],
        houses: Dict[int, Dict[str, Any]],
        aspects: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Создает интерпретацию натальной карты."""

        interpretation = {
            "personality": self._interpret_personality(planets),
            "relationships": self._interpret_relationships(planets, aspects),
            "career": self._interpret_career(planets, houses),
            "challenges": self._interpret_challenges(aspects),
            "strengths": self._interpret_strengths(planets, aspects),
            "life_purpose": self._interpret_life_purpose(planets, houses),
            "spiritual_path": self._interpret_spiritual_path(planets, houses),
        }

        return interpretation

    def _interpret_personality(
        self, planets: Dict[str, Dict[str, Any]]
    ) -> Dict[str, str]:
        """Интерпретирует личность на основе Солнца, Луны и Асцендента."""

        sun_sign = planets.get("Sun", {}).get("sign", "Овен")
        moon_sign = planets.get("Moon", {}).get("sign", "Овен")

        personality = {
            "core_self": f"Ваше солнце в {sun_sign} говорит о том, что вы по природе активный и энергичный человек.",
            "emotional_nature": f"Луна в {moon_sign} указывает на вашу эмоциональную природу и потребности.",
            "general_description": self._get_personality_description(
                sun_sign, moon_sign
            ),
        }

        return personality

    def _get_personality_description(
        self, sun_sign: str, moon_sign: str
    ) -> str:
        """Генерирует описание личности."""

        sun_descriptions = {
            "Овен": "динамичный лидер",
            "Телец": "стабильный практик",
            "Близнецы": "любознательный коммуникатор",
            "Рак": "заботливый эмпат",
            "Лев": "творческий вдохновитель",
            "Дева": "аналитический перфекционист",
            "Весы": "гармоничный дипломат",
            "Скорпион": "интенсивный трансформатор",
            "Стрелец": "свободолюбивый философ",
            "Козерог": "амбициозный строитель",
            "Водолей": "оригинальный реформатор",
            "Рыбы": "чувствительный мечтатель",
        }

        moon_traits = {
            "Овен": "импульсивные эмоции",
            "Телец": "устойчивые чувства",
            "Близнецы": "переменчивые настроения",
            "Рак": "глубокие эмоции",
            "Лев": "драматичные переживания",
            "Дева": "практичный подход к чувствам",
            "Весы": "потребность в гармонии",
            "Скорпион": "интенсивные эмоции",
            "Стрелец": "оптимистичный настрой",
            "Козерог": "сдержанные чувства",
            "Водолей": "независимые эмоции",
            "Рыбы": "чувствительная душа",
        }

        sun_trait = sun_descriptions.get(sun_sign, "уникальная личность")
        moon_trait = moon_traits.get(moon_sign, "особые эмоции")

        return f"Вы {sun_trait} с {moon_trait}. Эта комбинация делает вас особенным и многогранным человеком."

    def _interpret_relationships(
        self, planets: Dict[str, Dict[str, Any]], aspects: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Интерпретирует отношения на основе Венеры и Марса."""

        venus_sign = planets.get("Venus", {}).get("sign", "Телец")
        mars_sign = planets.get("Mars", {}).get("sign", "Овен")

        # Ищем аспекты между Венерой и Марсом
        venus_mars_aspect = None
        for aspect in aspects:
            if (
                aspect["planet1"] == "Venus" and aspect["planet2"] == "Mars"
            ) or (
                aspect["planet1"] == "Mars" and aspect["planet2"] == "Venus"
            ):
                venus_mars_aspect = aspect["aspect"]
                break

        relationships = {
            "love_style": f"Ваша Венера в {venus_sign} указывает на романтичный и гармоничный подход к любви.",
            "passion_style": f"Марс в {mars_sign} говорит о том, как вы выражаете страсть и желания.",
            "compatibility_advice": self._get_relationship_advice(
                venus_sign, mars_sign, venus_mars_aspect
            ),
        }

        return relationships

    def _get_relationship_advice(
        self, venus_sign: str, mars_sign: str, venus_mars_aspect: Optional[str]
    ) -> str:
        """Дает советы по отношениям."""

        base_advice = (
            "В отношениях важно найти баланс между чувствами и страстью."
        )

        if venus_mars_aspect:
            aspect_advice = {
                "Соединение": "У вас естественная гармония между любовью и страстью.",
                "Трин": "Ваши чувства и желания прекрасно дополняют друг друга.",
                "Секстиль": "У вас хорошие возможности для гармоничных отношений.",
                "Квадрат": "Важно работать над балансом между эмоциями и действиями.",
                "Оппозиция": "Учитесь интегрировать противоположные потребности в отношениях.",
            }
            base_advice = aspect_advice.get(venus_mars_aspect, base_advice)

        return base_advice

    def _interpret_career(
        self,
        planets: Dict[str, Dict[str, Any]],
        houses: Dict[int, Dict[str, Any]],
    ) -> Dict[str, str]:
        """Интерпретирует карьерные возможности."""

        # Смотрим на 10-й дом (карьера) и Марс (действие)
        midheaven_sign = houses.get("midheaven", {}).get("sign", "Козерог")
        mars_sign = planets.get("Mars", {}).get("sign", "Овен")

        career_suggestions = {
            "Овен": "лидерство, спорт, военное дело",
            "Телец": "финансы, искусство, сельское хозяйство",
            "Близнецы": "журналистика, преподавание, торговля",
            "Рак": "медицина, забота о детях, недвижимость",
            "Лев": "развлечения, творчество, управление",
            "Дева": "медицина, аналитика, служба",
            "Весы": "право, дипломатия, искусство",
            "Скорпион": "исследования, психология, медицина",
            "Стрелец": "образование, путешествия, философия",
            "Козерог": "бизнес, управление, архитектура",
            "Водолей": "технологии, изобретения, гуманитарная деятельность",
            "Рыбы": "искусство, духовность, помощь людям",
        }

        career_field = career_suggestions.get(
            midheaven_sign, "разнообразные области"
        )

        return {
            "career_direction": f"Ваш средний небесный в {midheaven_sign} указывает на склонность к {career_field}.",
            "work_style": f"Марс в {mars_sign} показывает ваш стиль работы и подход к достижению целей.",
            "success_factors": "Используйте свои природные таланты и следуйте своему призванию.",
        }

    def _interpret_challenges(
        self, aspects: List[Dict[str, Any]]
    ) -> List[str]:
        """Интерпретирует вызовы на основе напряженных аспектов."""

        challenges = []

        for aspect in aspects:
            if aspect["aspect"] in ["Квадрат", "Оппозиция"]:
                planet1 = aspect["planet1"]
                planet2 = aspect["planet2"]
                aspect_name = aspect["aspect"]

                challenge_text = f"{aspect_name} между {planet1} и {planet2} может создавать внутреннее напряжение."
                challenges.append(challenge_text)

        if not challenges:
            challenges.append("В вашей карте преобладают гармоничные аспекты.")

        return challenges[:3]  # Ограничиваем тремя основными вызовами

    def _interpret_strengths(
        self, planets: Dict[str, Dict[str, Any]], aspects: List[Dict[str, Any]]
    ) -> List[str]:
        """Интерпретирует сильные стороны."""

        strengths = []

        # Ищем гармоничные аспекты
        for aspect in aspects:
            if aspect["aspect"] in ["Трин", "Секстиль"]:
                planet1 = aspect["planet1"]
                planet2 = aspect["planet2"]
                aspect_name = aspect["aspect"]

                strength_text = f"{aspect_name} между {planet1} и {planet2} дает вам естественные таланты."
                strengths.append(strength_text)

        if not strengths:
            strengths.append(
                "У вас есть уникальные таланты, которые стоит развивать."
            )

        return strengths[:3]  # Ограничиваем тремя основными сильными сторонами

    def _interpret_life_purpose(
        self,
        planets: Dict[str, Dict[str, Any]],
        houses: Dict[int, Dict[str, Any]],
    ) -> str:
        """Интерпретирует жизненное предназначение."""

        sun_sign = planets.get("Sun", {}).get("sign", "Овен")

        life_purposes = {
            "Овен": "вести и вдохновлять других, быть первопроходцем",
            "Телец": "создавать красоту и стабильность в мире",
            "Близнецы": "соединять людей через общение и знания",
            "Рак": "заботиться и защищать тех, кто в этом нуждается",
            "Лев": "творить и выражать свою уникальность",
            "Дева": "служить и помогать совершенствовать мир",
            "Весы": "создавать гармонию и справедливость",
            "Скорпион": "трансформировать и исцелять",
            "Стрелец": "искать истину и делиться мудростью",
            "Козерог": "строить и достигать значимых целей",
            "Водолей": "изменять мир к лучшему, быть новатором",
            "Рыбы": "исцелять и вдохновлять через сострадание",
        }

        purpose = life_purposes.get(sun_sign, "найти свой уникальный путь")

        return f"Ваше жизненное предназначение - {purpose}."

    def _interpret_spiritual_path(
        self,
        planets: Dict[str, Dict[str, Any]],
        houses: Dict[int, Dict[str, Any]],
    ) -> str:
        """Интерпретирует духовный путь."""

        # Смотрим на Нептун и 12-й дом
        neptune_sign = planets.get("Neptune", {}).get("sign", "Рыбы")

        spiritual_paths = {
            "Овен": "активные духовные практики",
            "Телец": "связь с природой и землей",
            "Близнецы": "изучение различных учений",
            "Рак": "эмоциональное и интуитивное развитие",
            "Лев": "творческое самовыражение как путь",
            "Дева": "служение как духовная практика",
            "Весы": "поиск гармонии и красоты",
            "Скорпион": "глубокая трансформация души",
            "Стрелец": "философские и религиозные поиски",
            "Козерог": "практический мистицизм",
            "Водолей": "инновационные духовные подходы",
            "Рыбы": "мистицизм и сострадание",
        }

        path = spiritual_paths.get(neptune_sign, "уникальный духовный путь")

        return f"Ваш духовный путь связан с {path}."

    def _calculate_chart_signature(
        self, planets: Dict[str, Dict[str, Any]]
    ) -> Dict[str, str]:
        """Вычисляет подпись карты (доминирующий элемент и качество)."""

        elements = {"fire": 0, "earth": 0, "air": 0, "water": 0}
        qualities = {"cardinal": 0, "fixed": 0, "mutable": 0}

        # Подсчитываем элементы и качества
        for planet, data in planets.items():
            sign = data.get("sign", "Овен")
            element = self.astro_calc.elements.get(sign, "fire")
            quality = self.astro_calc.qualities.get(sign, "cardinal")

            elements[element] += 1
            qualities[quality] += 1

        # Находим доминирующие
        dominant_element = max(elements, key=elements.get)
        dominant_quality = max(qualities, key=qualities.get)

        return {
            "dominant_element": dominant_element,
            "dominant_quality": dominant_quality,
            "description": f"У вас преобладает {dominant_element} элемент с {dominant_quality} качеством.",
        }

    def _calculate_dominant_elements(
        self, planets: Dict[str, Dict[str, Any]]
    ) -> Dict[str, int]:
        """Вычисляет распределение элементов в карте."""

        elements = {"fire": 0, "earth": 0, "air": 0, "water": 0}

        for planet, data in planets.items():
            sign = data.get("sign", "Овен")
            element = self.astro_calc.elements.get(sign, "fire")
            elements[element] += 1

        return elements

    def _determine_chart_shape(
        self, planets: Dict[str, Dict[str, Any]]
    ) -> Dict[str, str]:
        """Определяет форму карты (распределение планет)."""

        # Упрощенное определение формы карты
        longitudes = [data.get("longitude", 0) for data in planets.values()]

        min_long = min(longitudes)
        max_long = max(longitudes)
        spread = max_long - min_long

        if spread < 120:
            shape = "Bundle"
            description = "Концентрированная энергия в одной области жизни"
        elif spread < 180:
            shape = "Bowl"
            description = "Односторонняя концентрация с пустой половиной"
        elif spread < 240:
            shape = "Locomotive"
            description = "Последовательное развертывание энергии"
        else:
            shape = "Splash"
            description = "Разнообразные интересы и таланты"

        return {"shape": shape, "description": description}

    def calculate_progressions(
        self,
        birth_date: date,
        birth_time: Optional[time] = None,
        progression_date: Optional[date] = None,
        birth_place: Optional[Dict[str, float]] = None,
        timezone_str: str = "Europe/Moscow",
    ) -> Dict[str, Any]:
        """Вычисляет прогрессии натальной карты."""

        if progression_date is None:
            progression_date = date.today()

        if birth_time is None:
            birth_time = time(12, 0)

        if birth_place is None:
            birth_place = {"latitude": 55.7558, "longitude": 37.6176}

        # Вычисляем количество дней от рождения до даты прогрессии
        days_since_birth = (progression_date - birth_date).days

        # В символических прогрессиях 1 день = 1 год
        # Поэтому прогрессированная дата = дата рождения + количество лет в днях
        progressed_birth_date = birth_date + timedelta(days=days_since_birth)
        progressed_datetime = datetime.combine(
            progressed_birth_date, birth_time
        )

        # Устанавливаем временную зону
        try:
            timezone = pytz.timezone(timezone_str)
            progressed_datetime = timezone.localize(progressed_datetime)
        except Exception:
            progressed_datetime = pytz.UTC.localize(progressed_datetime)

        # Вычисляем прогрессированные позиции планет
        progressed_positions = self.astro_calc.calculate_planet_positions(
            progressed_datetime,
            birth_place["latitude"],
            birth_place["longitude"],
        )

        # Вычисляем прогрессированные дома (только для быстро движущихся точек)
        progressed_houses = self.astro_calc.calculate_houses(
            progressed_datetime,
            birth_place["latitude"],
            birth_place["longitude"],
        )

        # Создаем интерпретацию прогрессий
        progression_interpretation = self._interpret_progressions(
            progressed_positions, progression_date, birth_date
        )

        return {
            "birth_date": birth_date.isoformat(),
            "progression_date": progression_date.isoformat(),
            "days_progressed": days_since_birth,
            "progressed_planets": progressed_positions,
            "progressed_houses": progressed_houses,
            "interpretation": progression_interpretation,
            "key_changes": self._analyze_progression_changes(
                progressed_positions
            ),
        }

    def _interpret_progressions(
        self,
        progressed_positions: Dict[str, Dict[str, Any]],
        progression_date: date,
        birth_date: date,
    ) -> Dict[str, Any]:
        """Интерпретирует прогрессии."""

        age = (progression_date - birth_date).days // 365

        # Анализируем прогрессированное Солнце
        prog_sun_sign = progressed_positions.get("Sun", {}).get("sign", "Овен")

        # Анализируем прогрессированную Луну
        prog_moon_sign = progressed_positions.get("Moon", {}).get(
            "sign", "Рак"
        )

        interpretation = {
            "current_age": age,
            "life_stage": self._get_life_stage_description(age),
            "progressed_sun": {
                "sign": prog_sun_sign,
                "meaning": self._get_progressed_sun_meaning(prog_sun_sign),
            },
            "progressed_moon": {
                "sign": prog_moon_sign,
                "meaning": self._get_progressed_moon_meaning(prog_moon_sign),
            },
            "general_trends": self._get_progression_trends(
                age, progressed_positions
            ),
        }

        return interpretation

    def _get_life_stage_description(self, age: int) -> str:
        """Возвращает описание жизненного этапа."""

        if age < 7:
            return "Раннее детство - формирование базовой личности"
        elif age < 14:
            return "Детство - развитие социальных навыков"
        elif age < 21:
            return "Юность - поиск идентичности"
        elif age < 30:
            return "Молодость - становление в мире"
        elif age < 42:
            return "Зрелость - активная самореализация"
        elif age < 56:
            return "Средний возраст - переосмысление ценностей"
        elif age < 70:
            return "Зрелый возраст - мудрость и наставничество"
        else:
            return "Старшие годы - интеграция жизненного опыта"

    def _get_progressed_sun_meaning(self, sun_sign: str) -> str:
        """Возвращает значение прогрессированного Солнца."""

        meanings = {
            "Овен": "Период активности и новых начинаний",
            "Телец": "Время стабилизации и материального роста",
            "Близнецы": "Фокус на общении и обучении",
            "Рак": "Внимание к семье и эмоциональной безопасности",
            "Лев": "Творческое самовыражение и лидерство",
            "Дева": "Совершенствование навыков и служение",
            "Весы": "Гармонизация отношений и партнерство",
            "Скорпион": "Глубокая трансформация и возрождение",
            "Стрелец": "Расширение горизонтов и философские поиски",
            "Козерог": "Построение структуры и достижение целей",
            "Водолей": "Инновации и социальная активность",
            "Рыбы": "Духовное развитие и сострадание",
        }

        return meanings.get(sun_sign, "Период личностного развития")

    def _get_progressed_moon_meaning(self, moon_sign: str) -> str:
        """Возвращает значение прогрессированной Луны."""

        meanings = {
            "Овен": "Эмоциональная независимость и спонтанность",
            "Телец": "Потребность в стабильности и комфорте",
            "Близнецы": "Любознательность и социальная активность",
            "Рак": "Глубокая эмоциональная связь с близкими",
            "Лев": "Потребность в признании и творческом выражении",
            "Дева": "Аналитический подход к эмоциям",
            "Весы": "Стремление к гармонии в отношениях",
            "Скорпион": "Интенсивные эмоциональные переживания",
            "Стрелец": "Оптимизм и стремление к свободе",
            "Козерог": "Серьезный подход к эмоциональным вопросам",
            "Водолей": "Необычный взгляд на чувства и отношения",
            "Рыбы": "Повышенная чувствительность и интуиция",
        }

        return meanings.get(moon_sign, "Эмоциональное развитие")

    def _get_progression_trends(
        self, age: int, progressed_positions: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Определяет основные тенденции прогрессий."""

        trends = []

        # Анализируем ключевые возрастные периоды
        if 28 <= age <= 30:
            trends.append(
                "Возвращение Сатурна - время важных жизненных решений"
            )
        elif 35 <= age <= 45:
            trends.append(
                "Кризис среднего возраста - переосмысление жизненных целей"
            )
        elif 56 <= age <= 60:
            trends.append("Второе возвращение Сатурна - мудрость и авторитет")

        # Анализируем прогрессированные аспекты (упрощенно)
        prog_sun = progressed_positions.get("Sun", {}).get("longitude", 0)
        prog_moon = progressed_positions.get("Moon", {}).get("longitude", 0)

        sun_moon_angle = abs(prog_sun - prog_moon)
        if sun_moon_angle > 180:
            sun_moon_angle = 360 - sun_moon_angle

        if sun_moon_angle <= 10:
            trends.append("Гармония между сознанием и эмоциями")
        elif 170 <= sun_moon_angle <= 190:
            trends.append("Необходимость баланса между разумом и чувствами")

        return trends

    def _analyze_progression_changes(
        self, progressed_positions: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Анализирует ключевые изменения в прогрессиях."""

        changes = []

        # Анализируем быстро движущиеся планеты
        fast_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars"]

        for planet in fast_planets:
            if planet in progressed_positions:
                sign = progressed_positions[planet]["sign"]
                changes.append(f"Прогрессированный {planet} в {sign}")

        return changes[:3]  # Ограничиваем тремя основными изменениями
    
    def calculate_enhanced_natal_chart(
        self,
        name: str,
        birth_date: date,
        birth_time: Optional[time] = None,
        birth_place: Optional[Dict[str, float]] = None,
        timezone_str: str = "Europe/Moscow",
        house_system: str = "Placidus",
        zodiac_type: str = "Tropical",
        include_arabic_parts: bool = True,
        include_fixed_stars: bool = True,
        generate_svg: bool = False,
    ) -> Dict[str, Any]:
        """
        Вычисляет расширенную натальную карту с полным функционалом Kerykeion.
        
        Args:
            name: Имя владельца карты
            birth_date: Дата рождения
            birth_time: Время рождения (опционально)
            birth_place: Координаты места рождения
            timezone_str: Временная зона
            house_system: Система домов
            zodiac_type: Тип зодиака (Tropical/Sidereal)
            include_arabic_parts: Включить арабские части
            include_fixed_stars: Включить фиксированные звезды
            generate_svg: Генерировать SVG карту
        
        Returns:
            Полные данные натальной карты
        """
        logger.info(f"NATAL_CHART_ENHANCED_START: {name}")
        
        # Создаем datetime объект
        if birth_time is None:
            birth_time = time(12, 0)  # Полдень по умолчанию
        
        birth_datetime = datetime.combine(birth_date, birth_time)
        
        # Координаты места рождения (по умолчанию Москва)
        if birth_place is None:
            birth_place = {"latitude": 55.7558, "longitude": 37.6176}
        
        # Конвертируем строковые параметры в enums
        try:
            house_sys_enum = HouseSystem(house_system)
        except ValueError:
            logger.warning(f"NATAL_CHART_ENHANCED: Unknown house system {house_system}, using Placidus")
            house_sys_enum = HouseSystem.PLACIDUS
        
        try:
            zodiac_enum = ZodiacType(zodiac_type)
        except ValueError:
            logger.warning(f"NATAL_CHART_ENHANCED: Unknown zodiac type {zodiac_type}, using Tropical")
            zodiac_enum = ZodiacType.TROPICAL
        
        result = {
            "basic_info": {
                "name": name,
                "birth_date": birth_date.isoformat(),
                "birth_time": birth_time.strftime("%H:%M"),
                "birth_place": birth_place,
                "timezone": timezone_str,
                "house_system": house_system,
                "zodiac_type": zodiac_type,
            },
            "calculation_backend": "fallback",
            "enhanced_features_available": False,
        }
        
        # Попробуем использовать Kerykeion если доступен
        if self.kerykeion_service.is_available():
            logger.info("NATAL_CHART_ENHANCED: Using Kerykeion for advanced calculation")
            
            kerykeion_data = self.kerykeion_service.get_full_natal_chart_data(
                name=name,
                birth_datetime=birth_datetime,
                latitude=birth_place["latitude"],
                longitude=birth_place["longitude"],
                timezone=timezone_str,
                house_system=house_sys_enum,
                zodiac_type=zodiac_enum,
            )
            
            if "error" not in kerykeion_data:
                result.update({
                    "calculation_backend": "kerykeion",
                    "enhanced_features_available": True,
                    "planets": kerykeion_data.get("planets", {}),
                    "houses": kerykeion_data.get("houses", {}),
                    "angles": kerykeion_data.get("angles", {}),
                    "aspects": kerykeion_data.get("aspects", []),
                    "chart_shape": kerykeion_data.get("chart_shape", {}),
                    "element_distribution": kerykeion_data.get("element_distribution", {}),
                    "quality_distribution": kerykeion_data.get("quality_distribution", {}),
                    "dominant_planets": kerykeion_data.get("dominant_planets", []),
                })
                
                # Добавляем арабские части если запрошены
                if include_arabic_parts:
                    # Создаем subject для арабских частей
                    subject = self.kerykeion_service.create_astrological_subject(
                        name, birth_datetime, birth_place["latitude"],
                        birth_place["longitude"], timezone_str, house_sys_enum, zodiac_enum
                    )
                    if subject:
                        result["arabic_parts"] = self.kerykeion_service.calculate_arabic_parts_extended(subject)
                
                # Генерируем SVG если запрошено
                if generate_svg:
                    svg_chart = self.kerykeion_service.generate_chart_svg(
                        name, birth_datetime, birth_place["latitude"],
                        birth_place["longitude"], timezone_str, house_sys_enum
                    )
                    if svg_chart:
                        result["svg_chart"] = svg_chart
                
                # Добавляем расширенную интерпретацию
                result["enhanced_interpretation"] = self._create_enhanced_interpretation(result)
                
                logger.info("NATAL_CHART_ENHANCED_SUCCESS: Kerykeion calculation completed")
            else:
                logger.warning(f"NATAL_CHART_ENHANCED: Kerykeion failed - {kerykeion_data['error']}")
                # Fallback to basic calculation
                result.update(self._calculate_fallback_chart(
                    birth_date, birth_time, birth_place, timezone_str
                ))
        else:
            logger.info("NATAL_CHART_ENHANCED: Kerykeion not available, using fallback")
            # Используем базовый калькулятор
            result.update(self._calculate_fallback_chart(
                birth_date, birth_time, birth_place, timezone_str
            ))
        
        # Добавляем фиксированные звезды если запрошены (используем базовый калькулятор)
        if include_fixed_stars:
            result["fixed_stars"] = self.astro_calc.calculate_fixed_stars(
                birth_datetime, birth_place["latitude"], birth_place["longitude"]
            )
        
        logger.info(f"NATAL_CHART_ENHANCED_COMPLETE: {name} - backend: {result['calculation_backend']}")
        return result
    
    def _calculate_fallback_chart(
        self, birth_date: date, birth_time: Optional[time], 
        birth_place: Dict[str, float], timezone_str: str
    ) -> Dict[str, Any]:
        """Fallback calculation using the basic astrology calculator"""
        basic_chart = self.calculate_natal_chart(birth_date, birth_time, birth_place, timezone_str)
        
        return {
            "planets": basic_chart.get("planets", {}),
            "houses": basic_chart.get("houses", {}),
            "aspects": basic_chart.get("aspects", []),
            "interpretation": basic_chart.get("interpretation", {}),
            "chart_signature": basic_chart.get("chart_signature", {}),
            "dominant_elements": basic_chart.get("dominant_elements", {}),
            "chart_shape": basic_chart.get("chart_shape", {}),
        }
    
    def _create_enhanced_interpretation(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создает расширенную интерпретацию на основе Kerykeion данных"""
        interpretation = {
            "personality_analysis": {},
            "life_themes": [],
            "karmic_indicators": [],
            "psychological_patterns": [],
            "spiritual_path": {},
            "relationship_potential": {},
            "career_guidance": {},
            "health_indications": {},
            "timing_cycles": {},
        }
        
        planets = chart_data.get("planets", {})
        aspects = chart_data.get("aspects", [])
        dominant_planets = chart_data.get("dominant_planets", [])
        
        # Анализ доминирующих планет
        if dominant_planets:
            interpretation["personality_analysis"]["dominant_influences"] = []
            for planet in dominant_planets[:3]:  # Топ 3 планеты
                planet_meaning = self._get_planet_psychological_meaning(planet)
                interpretation["personality_analysis"]["dominant_influences"].append({
                    "planet": planet,
                    "influence": planet_meaning,
                })
        
        # Анализ жизненных тем на основе сильных аспектов
        strong_aspects = [asp for asp in aspects if asp.get("strength") in ["Very Strong", "Strong"]]
        life_themes = []
        
        for aspect in strong_aspects[:5]:  # Топ 5 аспектов
            theme = self._interpret_aspect_life_theme(aspect)
            if theme:
                life_themes.append(theme)
        
        interpretation["life_themes"] = life_themes
        
        # Карьерное руководство на основе MC и 10 дома
        angles = chart_data.get("angles", {})
        if "midheaven" in angles:
            mc_sign = angles["midheaven"].get("sign")
            if mc_sign:
                interpretation["career_guidance"] = self._get_career_guidance_by_mc(mc_sign)
        
        # Духовный путь на основе распределения элементов
        element_dist = chart_data.get("element_distribution", {})
        interpretation["spiritual_path"] = self._analyze_spiritual_path(element_dist)
        
        return interpretation
    
    def _get_planet_psychological_meaning(self, planet: str) -> str:
        """Получает психологическое значение планеты"""
        meanings = {
            "Sun": "Основная идентичность, эго, жизненная сила и самовыражение",
            "Moon": "Эмоциональная природа, подсознание, потребности и инстинкты",
            "Mercury": "Мышление, коммуникация, обучение и адаптивность",
            "Venus": "Ценности, отношения, красота и гармония",
            "Mars": "Энергия, действие, желания и способность к инициативе", 
            "Jupiter": "Рост, мудрость, оптимизм и поиск смысла",
            "Saturn": "Дисциплина, ответственность, ограничения и структура",
            "Uranus": "Инновации, независимость, оригинальность и революционность",
            "Neptune": "Интуиция, духовность, иллюзии и сострадание",
            "Pluto": "Трансформация, власть, глубинная психология и возрождение",
        }
        return meanings.get(planet, f"Влияние планеты {planet}")
    
    def _interpret_aspect_life_theme(self, aspect: Dict[str, Any]) -> Optional[str]:
        """Интерпретирует аспект как жизненную тему"""
        planet1 = aspect.get("planet1", "").lower()
        planet2 = aspect.get("planet2", "").lower()
        aspect_type = aspect.get("aspect", "")
        
        # Ключевые аспекты и их жизненные темы
        key_combinations = {
            ("sun", "moon"): {
                "Conjunction": "Интеграция сознательного и бессознательного",
                "Opposition": "Баланс между волей и эмоциями",
                "Square": "Внутренний конфликт личности",
                "Trine": "Гармоничное самовыражение",
            },
            ("sun", "saturn"): {
                "Conjunction": "Серьезность и ответственность в жизни",
                "Square": "Преодоление ограничений и авторитета", 
                "Trine": "Дисциплинированная самореализация",
            },
            ("moon", "pluto"): {
                "Conjunction": "Глубокие эмоциональные трансформации",
                "Square": "Интенсивные психологические процессы",
                "Trine": "Интуитивная связь с подсознанием",
            },
            ("venus", "mars"): {
                "Conjunction": "Гармония между любовью и страстью",
                "Square": "Динамика в отношениях",
                "Trine": "Естественная привлекательность",
            },
        }
        
        combination = (planet1, planet2) if (planet1, planet2) in key_combinations else (planet2, planet1)
        
        if combination in key_combinations:
            theme_dict = key_combinations[combination]
            return theme_dict.get(aspect_type)
        
        return None
    
    def _get_career_guidance_by_mc(self, mc_sign: str) -> Dict[str, Any]:
        """Дает карьерные рекомендации по знаку MC"""
        career_guidance = {
            "Овен": {
                "fields": ["лидерство", "спорт", "военное дело", "предпринимательство"],
                "style": "Динамичный, инициативный, конкурентный",
                "advice": "Стремитесь к позициям лидера, не бойтесь рисков",
            },
            "Телец": {
                "fields": ["финансы", "искусство", "недвижимость", "кулинария"],
                "style": "Стабильный, практичный, надежный",
                "advice": "Развивайте практические навыки, стройте долгосрочную карьеру",
            },
            "Близнецы": {
                "fields": ["журналистика", "образование", "торговля", "IT"],
                "style": "Коммуникативный, разносторонний, адаптивный",
                "advice": "Используйте свои коммуникативные способности",
            },
            # Добавьте остальные знаки аналогично...
        }
        
        return career_guidance.get(mc_sign, {
            "fields": ["разнообразные области"],
            "style": "Индивидуальный подход",
            "advice": "Следуйте своим уникальным талантам",
        })
    
    def _analyze_spiritual_path(self, element_distribution: Dict[str, int]) -> Dict[str, Any]:
        """Анализирует духовный путь по распределению элементов"""
        total_planets = sum(element_distribution.values()) or 1
        
        # Определяем доминирующий элемент
        dominant_element = max(element_distribution, key=element_distribution.get)
        dominant_percentage = (element_distribution[dominant_element] / total_planets) * 100
        
        spiritual_paths = {
            "Fire": {
                "path": "Путь действия и вдохновения",
                "practices": ["динамическая медитация", "спорт как духовная практика", "творческое самовыражение"],
                "qualities": ["энтузиазм", "лидерство", "воодушевление"],
            },
            "Earth": {
                "path": "Путь практической мудрости",
                "practices": ["работа с телом", "садоводство", "рукоделие", "служение"],
                "qualities": ["терпение", "заземленность", "практичность"],
            },
            "Air": {
                "path": "Путь знания и общения",
                "practices": ["изучение философии", "преподавание", "письменность"],
                "qualities": ["любознательность", "объективность", "социальность"],
            },
            "Water": {
                "path": "Путь интуиции и сострадания",
                "practices": ["медитация", "целительство", "искусство", "помощь людям"],
                "qualities": ["эмпатия", "интуиция", "глубина чувств"],
            },
        }
        
        path_info = spiritual_paths.get(dominant_element, {})
        path_info["dominant_percentage"] = round(dominant_percentage, 1)
        path_info["element_balance"] = element_distribution
        
        return path_info
    
    def calculate_compatibility_enhanced(
        self,
        person1_chart: Dict[str, Any],
        person2_chart: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Расширенная совместимость с использованием Kerykeion данных"""
        if not self.kerykeion_service.is_available():
            logger.warning("COMPATIBILITY_ENHANCED: Kerykeion not available, using basic compatibility")
            # Fallback to basic compatibility calculation
            return {"error": "Enhanced compatibility requires Kerykeion"}
        
        logger.info("COMPATIBILITY_ENHANCED_START")
        
        compatibility = self.kerykeion_service.calculate_compatibility_detailed(
            person1_chart, person2_chart
        )
        
        if "error" not in compatibility:
            # Добавляем дополнительную интерпретацию
            compatibility["relationship_advice"] = self._generate_relationship_advice(compatibility)
            compatibility["growth_areas"] = self._identify_growth_areas(compatibility)
            compatibility["strength_areas"] = self._identify_strength_areas(compatibility)
            
            logger.info("COMPATIBILITY_ENHANCED_SUCCESS")
        
        return compatibility
    
    def _generate_relationship_advice(self, compatibility: Dict[str, Any]) -> List[str]:
        """Генерирует советы для отношений на основе совместимости"""
        advice = []
        overall_score = compatibility.get("overall_score", 50)
        
        if overall_score >= 80:
            advice.append("У вас очень высокая совместимость! Цените эту гармонию.")
            advice.append("Поддерживайте открытое общение и взаимное уважение.")
        elif overall_score >= 60:
            advice.append("Ваша совместимость хорошая, но требует работы.")
            advice.append("Фокусируйтесь на сильных сторонах отношений.")
        else:
            advice.append("Отношения требуют значительных усилий с обеих сторон.")
            advice.append("Работайте над пониманием различий друг друга.")
        
        # Добавляем советы на основе Sun-Moon связей
        sun_moon_connections = compatibility.get("sun_moon_connections", [])
        for connection in sun_moon_connections[:2]:  # Топ 2
            if connection.get("harmony_score", 0) < 0:
                advice.append(f"Работайте над балансом в области {connection['connection']}")
        
        return advice[:5]  # Максимум 5 советов
    
    def _identify_growth_areas(self, compatibility: Dict[str, Any]) -> List[str]:
        """Определяет области для роста в отношениях"""
        growth_areas = []
        
        # Анализируем проблемные аспекты
        sun_moon_connections = compatibility.get("sun_moon_connections", [])
        for connection in sun_moon_connections:
            if connection.get("harmony_score", 0) < 0:
                growth_areas.append(f"Развитие понимания в {connection['connection']}")
        
        venus_mars_connections = compatibility.get("venus_mars_connections", [])
        for connection in venus_mars_connections:
            if connection.get("passion_score", 0) < 3:
                growth_areas.append(f"Углубление близости через {connection['connection']}")
        
        return growth_areas[:3]  # Максимум 3 области
    
    def _identify_strength_areas(self, compatibility: Dict[str, Any]) -> List[str]:
        """Определяет сильные стороны отношений"""
        strengths = []
        
        # Анализируем позитивные аспекты
        sun_moon_connections = compatibility.get("sun_moon_connections", [])
        for connection in sun_moon_connections:
            if connection.get("harmony_score", 0) > 5:
                strengths.append(f"Естественная гармония в {connection['connection']}")
        
        venus_mars_connections = compatibility.get("venus_mars_connections", [])
        for connection in venus_mars_connections:
            if connection.get("passion_score", 0) > 6:
                strengths.append(f"Сильное притяжение через {connection['connection']}")
        
        return strengths[:3]  # Максимум 3 силы
