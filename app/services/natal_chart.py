"""
Сервис расчета и интерпретации натальной карты.
"""
from datetime import date, datetime, time
from typing import Any, Dict, List, Optional

import pytz

from app.services.astrology_calculator import AstrologyCalculator


class NatalChartCalculator:
    """Калькулятор натальной карты."""

    def __init__(self):
        self.astro_calc = AstrologyCalculator()

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
