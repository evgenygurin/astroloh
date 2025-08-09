"""
Адаптер русификации астрологических данных Kerykeion.
Обеспечивает полную локализацию астрологической терминологии для русскоязычных пользователей.
"""

import logging
from datetime import date, datetime, time
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Try to import Kerykeion with graceful fallback
try:
    from kerykeion import AstrologicalSubject

    KERYKEION_AVAILABLE = True
    logger.info("RUSSIAN_ADAPTER_INIT: Kerykeion available for localization")
except ImportError as e:
    logger.warning(f"RUSSIAN_ADAPTER_INIT: Kerykeion not available - {e}")
    KERYKEION_AVAILABLE = False


class RussianZodiacSign(Enum):
    """Русские названия знаков зодиака с различными падежами"""

    ARIES = {
        "ru": "Овен",
        "genitive": "Овна",
        "dative": "Овну",
        "accusative": "Овна",
        "instrumental": "Овном",
        "prepositional": "Овне",
    }
    TAURUS = {
        "ru": "Телец",
        "genitive": "Тельца",
        "dative": "Тельцу",
        "accusative": "Тельца",
        "instrumental": "Тельцом",
        "prepositional": "Тельце",
    }
    GEMINI = {
        "ru": "Близнецы",
        "genitive": "Близнецов",
        "dative": "Близнецам",
        "accusative": "Близнецов",
        "instrumental": "Близнецами",
        "prepositional": "Близнецах",
    }
    CANCER = {
        "ru": "Рак",
        "genitive": "Рака",
        "dative": "Раку",
        "accusative": "Рака",
        "instrumental": "Раком",
        "prepositional": "Раке",
    }
    LEO = {
        "ru": "Лев",
        "genitive": "Льва",
        "dative": "Льву",
        "accusative": "Льва",
        "instrumental": "Львом",
        "prepositional": "Льве",
    }
    VIRGO = {
        "ru": "Дева",
        "genitive": "Девы",
        "dative": "Деве",
        "accusative": "Деву",
        "instrumental": "Девой",
        "prepositional": "Деве",
    }
    LIBRA = {
        "ru": "Весы",
        "genitive": "Весов",
        "dative": "Весам",
        "accusative": "Весы",
        "instrumental": "Весами",
        "prepositional": "Весах",
    }
    SCORPIO = {
        "ru": "Скорпион",
        "genitive": "Скорпиона",
        "dative": "Скорпиону",
        "accusative": "Скорпиона",
        "instrumental": "Скорпионом",
        "prepositional": "Скорпионе",
    }
    SAGITTARIUS = {
        "ru": "Стрелец",
        "genitive": "Стрельца",
        "dative": "Стрельцу",
        "accusative": "Стрельца",
        "instrumental": "Стрельцом",
        "prepositional": "Стрельце",
    }
    CAPRICORN = {
        "ru": "Козерог",
        "genitive": "Козерога",
        "dative": "Козерогу",
        "accusative": "Козерога",
        "instrumental": "Козерогом",
        "prepositional": "Козероге",
    }
    AQUARIUS = {
        "ru": "Водолей",
        "genitive": "Водолея",
        "dative": "Водолею",
        "accusative": "Водолея",
        "instrumental": "Водолеем",
        "prepositional": "Водолее",
    }
    PISCES = {
        "ru": "Рыбы",
        "genitive": "Рыб",
        "dative": "Рыбам",
        "accusative": "Рыб",
        "instrumental": "Рыбами",
        "prepositional": "Рыбах",
    }


class RussianPlanet(Enum):
    """Русские названия планет с различными падежами и символикой"""

    SUN = {
        "ru": "Солнце",
        "genitive": "Солнца",
        "dative": "Солнцу",
        "accusative": "Солнце",
        "instrumental": "Солнцем",
        "prepositional": "Солнце",
        "keywords": ["личность", "воля", "творчество", "лидерство", "отец"],
        "description": "Центр личности, воля к жизни, творческая энергия",
    }
    MOON = {
        "ru": "Луна",
        "genitive": "Луны",
        "dative": "Луне",
        "accusative": "Луну",
        "instrumental": "Луной",
        "prepositional": "Луне",
        "keywords": ["эмоции", "интуиция", "дом", "семья", "мать"],
        "description": "Эмоциональный мир, подсознание, инстинкты",
    }
    MERCURY = {
        "ru": "Меркурий",
        "genitive": "Меркурия",
        "dative": "Меркурию",
        "accusative": "Меркурий",
        "instrumental": "Меркурием",
        "prepositional": "Меркурии",
        "keywords": [
            "общение",
            "мышление",
            "информация",
            "обучение",
            "торговля",
        ],
        "description": "Ум, коммуникация, способность к обучению",
    }
    VENUS = {
        "ru": "Венера",
        "genitive": "Венеры",
        "dative": "Венере",
        "accusative": "Венеру",
        "instrumental": "Венерой",
        "prepositional": "Венере",
        "keywords": ["любовь", "красота", "гармония", "искусство", "деньги"],
        "description": "Любовь, красота, эстетика, материальные ценности",
    }
    MARS = {
        "ru": "Марс",
        "genitive": "Марса",
        "dative": "Марсу",
        "accusative": "Марс",
        "instrumental": "Марсом",
        "prepositional": "Марсе",
        "keywords": ["энергия", "действие", "борьба", "конкуренция", "спорт"],
        "description": "Энергия действия, напористость, борьба",
    }
    JUPITER = {
        "ru": "Юпитер",
        "genitive": "Юпитера",
        "dative": "Юпитеру",
        "accusative": "Юпитер",
        "instrumental": "Юпитером",
        "prepositional": "Юпитере",
        "keywords": [
            "расширение",
            "философия",
            "удача",
            "закон",
            "путешествия",
        ],
        "description": "Расширение сознания, мудрость, удача",
    }
    SATURN = {
        "ru": "Сатурн",
        "genitive": "Сатурна",
        "dative": "Сатурну",
        "accusative": "Сатурн",
        "instrumental": "Сатурном",
        "prepositional": "Сатурне",
        "keywords": [
            "дисциплина",
            "ограничения",
            "структура",
            "ответственность",
            "время",
        ],
        "description": "Дисциплина, структура, долг, ограничения",
    }
    URANUS = {
        "ru": "Уран",
        "genitive": "Урана",
        "dative": "Урану",
        "accusative": "Уран",
        "instrumental": "Ураном",
        "prepositional": "Уране",
        "keywords": [
            "революция",
            "свобода",
            "новаторство",
            "технологии",
            "неожиданность",
        ],
        "description": "Революционные изменения, свобода, новаторство",
    }
    NEPTUNE = {
        "ru": "Нептун",
        "genitive": "Нептуна",
        "dative": "Нептуну",
        "accusative": "Нептун",
        "instrumental": "Нептуном",
        "prepositional": "Нептуне",
        "keywords": [
            "мистика",
            "иллюзии",
            "творчество",
            "духовность",
            "жертвенность",
        ],
        "description": "Мистика, иллюзии, высшие идеалы",
    }
    PLUTO = {
        "ru": "Плутон",
        "genitive": "Плутона",
        "dative": "Плутону",
        "accusative": "Плутон",
        "instrumental": "Плутоном",
        "prepositional": "Плутоне",
        "keywords": [
            "трансформация",
            "смерть",
            "возрождение",
            "власть",
            "тайны",
        ],
        "description": "Глубинные трансформации, возрождение",
    }
    CHIRON = {
        "ru": "Хирон",
        "genitive": "Хирона",
        "dative": "Хирону",
        "accusative": "Хирона",
        "instrumental": "Хироном",
        "prepositional": "Хироне",
        "keywords": [
            "исцеление",
            "раны",
            "мудрость",
            "учительство",
            "служение",
        ],
        "description": "Раненый целитель, мудрость через боль",
    }
    LILITH = {
        "ru": "Лилит",
        "genitive": "Лилит",
        "dative": "Лилит",
        "accusative": "Лилит",
        "instrumental": "Лилит",
        "prepositional": "Лилит",
        "keywords": [
            "темная сторона",
            "подавленное",
            "инстинкты",
            "табу",
            "бунт",
        ],
        "description": "Темная Луна, подавленные инстинкты",
    }
    TRUE_NODE = {
        "ru": "Северный Узел",
        "genitive": "Северного Узла",
        "dative": "Северному Узлу",
        "accusative": "Северный Узел",
        "instrumental": "Северным Узлом",
        "prepositional": "Северном Узле",
        "keywords": [
            "предназначение",
            "развитие",
            "будущее",
            "кармические задачи",
            "рост",
        ],
        "description": "Кармическая задача, путь развития души",
    }
    MEAN_NODE = {
        "ru": "Лунный Узел",
        "genitive": "Лунного Узла",
        "dative": "Лунному Узлу",
        "accusative": "Лунный Узел",
        "instrumental": "Лунным Узлом",
        "prepositional": "Лунном Узле",
        "keywords": ["карма", "прошлое", "будущее", "судьба", "эволюция"],
        "description": "Кармическое направление, эволюция души",
    }


class RussianHouse(Enum):
    """Русские названия астрологических домов"""

    FIRST = {
        "ru": "I дом",
        "name": "Дом Личности",
        "description": "Личность, внешность, первое впечатление",
        "keywords": ["я", "личность", "внешность", "инициатива", "начало"],
    }
    SECOND = {
        "ru": "II дом",
        "name": "Дом Ресурсов",
        "description": "Деньги, материальные ценности, таланты",
        "keywords": [
            "деньги",
            "ценности",
            "таланты",
            "собственность",
            "стабильность",
        ],
    }
    THIRD = {
        "ru": "III дом",
        "name": "Дом Общения",
        "description": "Общение, обучение, братья и сестры",
        "keywords": ["общение", "информация", "поездки", "обучение", "связи"],
    }
    FOURTH = {
        "ru": "IV дом",
        "name": "Дом Семьи",
        "description": "Дом, семья, корни, основа",
        "keywords": ["дом", "семья", "корни", "основа", "безопасность"],
    }
    FIFTH = {
        "ru": "V дом",
        "name": "Дом Творчества",
        "description": "Творчество, дети, любовь, развлечения",
        "keywords": ["творчество", "дети", "любовь", "игры", "самовыражение"],
    }
    SIXTH = {
        "ru": "VI дом",
        "name": "Дом Здоровья",
        "description": "Здоровье, работа, служение, рутина",
        "keywords": ["здоровье", "работа", "служение", "привычки", "порядок"],
    }
    SEVENTH = {
        "ru": "VII дом",
        "name": "Дом Партнерства",
        "description": "Брак, партнерство, отношения",
        "keywords": [
            "брак",
            "партнерство",
            "другие",
            "равновесие",
            "договоры",
        ],
    }
    EIGHTH = {
        "ru": "VIII дом",
        "name": "Дом Трансформации",
        "description": "Смерть, возрождение, тайны, оккультизм",
        "keywords": [
            "трансформация",
            "тайны",
            "кризисы",
            "ресурсы других",
            "глубина",
        ],
    }
    NINTH = {
        "ru": "IX дом",
        "name": "Дом Философии",
        "description": "Философия, высшее образование, путешествия",
        "keywords": [
            "философия",
            "религия",
            "путешествия",
            "высшее образование",
            "мудрость",
        ],
    }
    TENTH = {
        "ru": "X дом",
        "name": "Дом Карьеры",
        "description": "Карьера, репутация, цель в жизни",
        "keywords": ["карьера", "репутация", "цель", "достижения", "власть"],
    }
    ELEVENTH = {
        "ru": "XI дом",
        "name": "Дом Дружбы",
        "description": "Друзья, надежды, мечты, группы",
        "keywords": ["друзья", "группы", "мечты", "надежды", "будущее"],
    }
    TWELFTH = {
        "ru": "XII дом",
        "name": "Дом Подсознания",
        "description": "Подсознание, жертвенность, тайны, карма",
        "keywords": [
            "подсознание",
            "тайны",
            "жертвенность",
            "карма",
            "духовность",
        ],
    }


class RussianAspect(Enum):
    """Русские названия аспектов с интерпретацией"""

    CONJUNCTION = {
        "ru": "Соединение",
        "symbol": "☌",
        "orb": 8,
        "nature": "нейтральный",
        "description": "Слияние энергий планет, усиление качеств",
    }
    OPPOSITION = {
        "ru": "Оппозиция",
        "symbol": "☍",
        "orb": 8,
        "nature": "напряженный",
        "description": "Противостояние, необходимость баланса",
    }
    TRINE = {
        "ru": "Тригон",
        "symbol": "△",
        "orb": 8,
        "nature": "гармоничный",
        "description": "Гармоничный аспект, легкое проявление энергий",
    }
    SQUARE = {
        "ru": "Квадрат",
        "symbol": "□",
        "orb": 8,
        "nature": "напряженный",
        "description": "Внутреннее напряжение, стимул к действию",
    }
    SEXTILE = {
        "ru": "Секстиль",
        "symbol": "⚹",
        "orb": 6,
        "nature": "гармоничный",
        "description": "Возможности, сотрудничество",
    }
    QUINCUNX = {
        "ru": "Квинконс",
        "symbol": "⚻",
        "orb": 3,
        "nature": "корректирующий",
        "description": "Необходимость корректировки, адаптация",
    }
    SEMISQUARE = {
        "ru": "Полуквадрат",
        "symbol": "∠",
        "orb": 2,
        "nature": "слабо напряженный",
        "description": "Легкое раздражение, мотивация к изменениям",
    }
    SESQUISQUARE = {
        "ru": "Полутораквадрат",
        "symbol": "⚼",
        "orb": 2,
        "nature": "слабо напряженный",
        "description": "Внутреннее беспокойство, стремление к совершенству",
    }
    SEMISEXTILE = {
        "ru": "Полусекстиль",
        "symbol": "⚺",
        "orb": 2,
        "nature": "слабо гармоничный",
        "description": "Скрытые возможности, постепенное развитие",
    }
    QUINTILE = {
        "ru": "Квинтиль",
        "symbol": "Q",
        "orb": 2,
        "nature": "творческий",
        "description": "Творческий талант, особые способности",
    }
    BIQUINTILE = {
        "ru": "Биквинтиль",
        "symbol": "bQ",
        "orb": 2,
        "nature": "творческий",
        "description": "Развитый творческий талант, мастерство",
    }


class RussianTimezone(Enum):
    """Российские часовые пояса с полной информацией"""

    KALININGRAD = {
        "zone": "Europe/Kaliningrad",
        "offset": "+02:00",
        "name": "Калининградское время",
    }
    MOSCOW = {
        "zone": "Europe/Moscow",
        "offset": "+03:00",
        "name": "Московское время",
    }
    SAMARA = {
        "zone": "Europe/Samara",
        "offset": "+04:00",
        "name": "Самарское время",
    }
    YEKATERINBURG = {
        "zone": "Asia/Yekaterinburg",
        "offset": "+05:00",
        "name": "Екатеринбургское время",
    }
    OMSK = {"zone": "Asia/Omsk", "offset": "+06:00", "name": "Омское время"}
    KRASNOYARSK = {
        "zone": "Asia/Krasnoyarsk",
        "offset": "+07:00",
        "name": "Красноярское время",
    }
    NOVOSIBIRSK = {
        "zone": "Asia/Novosibirsk",
        "offset": "+07:00",
        "name": "Новосибирское время",
    }
    IRKUTSK = {
        "zone": "Asia/Irkutsk",
        "offset": "+08:00",
        "name": "Иркутское время",
    }
    YAKUTSK = {
        "zone": "Asia/Yakutsk",
        "offset": "+09:00",
        "name": "Якутское время",
    }
    VLADIVOSTOK = {
        "zone": "Asia/Vladivostok",
        "offset": "+10:00",
        "name": "Владивостокское время",
    }
    MAGADAN = {
        "zone": "Asia/Magadan",
        "offset": "+11:00",
        "name": "Магаданское время",
    }
    KAMCHATKA = {
        "zone": "Asia/Kamchatka",
        "offset": "+12:00",
        "name": "Камчатское время",
    }


class RussianAstrologyAdapter:
    """
    Адаптер русификации астрологических данных Kerykeion.

    Обеспечивает:
    - Полную локализацию астрологических терминов
    - Поддержку российских часовых поясов
    - Культурную адаптацию интерпретаций
    - Грамматические склонения для голосового интерфейса
    """

    def __init__(self, kerykeion_subject: Optional[Any] = None):
        """
        Инициализация адаптера русификации.

        Args:
            kerykeion_subject: Объект AstrologicalSubject из Kerykeion (опционально)
        """
        self.subject = kerykeion_subject
        self.available = KERYKEION_AVAILABLE

        if not self.available:
            logger.warning(
                "RUSSIAN_ADAPTER: Kerykeion not available, using fallback mode"
            )

        # Кеш локализованных данных для производительности
        self._localized_cache: Dict[str, Any] = {}

        # Инициализация локализованных данных
        self.localized_data = self._initialize_localization()

        logger.info(
            "RUSSIAN_ADAPTER_INIT: Russian astrology adapter initialized"
        )

    def _initialize_localization(self) -> Dict[str, Any]:
        """Инициализация локализованных астрологических данных"""
        return {
            "signs": {
                sign.name.lower(): sign.value for sign in RussianZodiacSign
            },
            "planets": {
                planet.name.lower(): planet.value for planet in RussianPlanet
            },
            "houses": {
                house.name.lower(): house.value for house in RussianHouse
            },
            "aspects": {
                aspect.name.lower(): aspect.value for aspect in RussianAspect
            },
            "timezones": {tz.name.lower(): tz.value for tz in RussianTimezone},
        }

    def get_russian_planet_description(
        self, planet_name: str, case: str = "nominative"
    ) -> Dict[str, Any]:
        """
        Получить русское описание планеты с склонением.

        Args:
            planet_name: Название планеты (английское или русское)
            case: Падеж (nominative, genitive, dative, accusative, instrumental, prepositional)

        Returns:
            Словарь с русским описанием планеты
        """
        try:
            # Попытка найти планету по английскому названию
            planet_key = planet_name.upper()
            if hasattr(RussianPlanet, planet_key):
                planet_data = getattr(RussianPlanet, planet_key).value
            else:
                # Поиск по русскому названию
                for planet in RussianPlanet:
                    if planet.value["ru"].lower() == planet_name.lower():
                        planet_data = planet.value
                        break
                else:
                    logger.warning(
                        f"RUSSIAN_ADAPTER_PLANET: Unknown planet {planet_name}"
                    )
                    return {"error": f"Unknown planet: {planet_name}"}

            # Получение названия в нужном падеже
            if case == "nominative":
                name = planet_data["ru"]
            else:
                name = planet_data.get(case, planet_data["ru"])

            result = {
                "name": name,
                "base_name": planet_data["ru"],
                "keywords": planet_data["keywords"],
                "description": planet_data["description"],
                "case": case,
            }

            logger.debug(
                f"RUSSIAN_ADAPTER_PLANET: Generated description for {planet_name} in {case}"
            )
            return result

        except Exception as e:
            logger.error(f"RUSSIAN_ADAPTER_PLANET_ERROR: {e}")
            return {"error": f"Error getting planet description: {e}"}

    def get_russian_sign_description(
        self, sign_name: str, case: str = "nominative"
    ) -> Dict[str, Any]:
        """
        Получить русское описание знака зодиака с склонением.

        Args:
            sign_name: Название знака (английское или русское)
            case: Падеж

        Returns:
            Словарь с русским описанием знака
        """
        try:
            # Попытка найти знак по английскому названию
            sign_key = sign_name.upper()
            if hasattr(RussianZodiacSign, sign_key):
                sign_data = getattr(RussianZodiacSign, sign_key).value
            else:
                # Поиск по русскому названию
                for sign in RussianZodiacSign:
                    if sign.value["ru"].lower() == sign_name.lower():
                        sign_data = sign.value
                        break
                else:
                    logger.warning(
                        f"RUSSIAN_ADAPTER_SIGN: Unknown sign {sign_name}"
                    )
                    return {}

            # Получение названия в нужном падеже
            if case == "nominative":
                name = sign_data["ru"]
            else:
                name = sign_data.get(case, sign_data["ru"])

            result = {
                "name": name,
                "base_name": sign_data["ru"],
                "case": case,
                "characteristics": f"Знак зодиака {sign_data['ru']} с основными качествами и свойствами.",
            }

            logger.debug(
                f"RUSSIAN_ADAPTER_SIGN: Generated description for {sign_name} in {case}"
            )
            return result

        except Exception as e:
            logger.error(f"RUSSIAN_ADAPTER_SIGN_ERROR: {e}")
            return {"error": f"Error getting sign description: {e}"}

    def get_russian_house_description(
        self, house_number: int
    ) -> Dict[str, Any]:
        """
        Получить русское описание астрологического дома.

        Args:
            house_number: Номер дома (1-12)

        Returns:
            Словарь с русским описанием дома
        """
        try:
            house_names = [
                "FIRST",
                "SECOND",
                "THIRD",
                "FOURTH",
                "FIFTH",
                "SIXTH",
                "SEVENTH",
                "EIGHTH",
                "NINTH",
                "TENTH",
                "ELEVENTH",
                "TWELFTH",
            ]

            if not 1 <= house_number <= 12:
                logger.warning(
                    f"RUSSIAN_ADAPTER_HOUSE: Invalid house number {house_number}"
                )
                return {"error": f"Invalid house number: {house_number}"}

            house_key = house_names[house_number - 1]
            house_data = getattr(RussianHouse, house_key).value

            result = {
                "number": house_number,
                "roman": house_data["ru"],
                "name": house_data["name"],
                "description": house_data["description"],
                "keywords": house_data["keywords"],
            }

            logger.debug(
                f"RUSSIAN_ADAPTER_HOUSE: Generated description for house {house_number}"
            )
            return result

        except Exception as e:
            logger.error(f"RUSSIAN_ADAPTER_HOUSE_ERROR: {e}")
            return {"error": f"Error getting house description: {e}"}

    def get_russian_aspect_description(self, aspect: Dict[str, Any]) -> str:
        """
        Получить русское описание аспекта.

        Args:
            aspect: Словарь с данными об аспекте

        Returns:
            Русское описание аспекта
        """
        try:
            aspect_type = aspect.get("aspect", "").upper()
            planet1 = aspect.get("p1_name", "")
            planet2 = aspect.get("p2_name", "")
            orb = aspect.get("orbit", 0)

            if hasattr(RussianAspect, aspect_type):
                aspect_data = getattr(RussianAspect, aspect_type).value
                aspect_name = aspect_data["ru"]
                aspect_description = aspect_data["description"]
            else:
                aspect_name = aspect_type
                aspect_description = "Неизвестный аспект"

            # Получение русских названий планет
            planet1_ru = self.get_russian_planet_description(planet1)["name"]
            planet2_ru = self.get_russian_planet_description(planet2)["name"]

            # Форматирование описания
            description = f"{planet1_ru} {aspect_name.lower()} {planet2_ru}"
            if orb > 0:
                description += f" (орб {orb:.1f}°)"

            if aspect_description != "Неизвестный аспект":
                description += f" - {aspect_description}"

            logger.debug(
                f"RUSSIAN_ADAPTER_ASPECT: Generated description for {aspect_type}"
            )
            return description

        except Exception as e:
            logger.error(f"RUSSIAN_ADAPTER_ASPECT_ERROR: {e}")
            return f"Ошибка в описании аспекта: {e}"

    def detect_russian_timezone(
        self, city_name: str
    ) -> Optional[Dict[str, str]]:
        """
        Определить часовой пояс по названию российского города.

        Args:
            city_name: Название города

        Returns:
            Информация о часовом поясе или None
        """
        # Упрощенная база городов по часовым поясам
        city_timezone_map = {
            # Калининградское время
            "калининград": RussianTimezone.KALININGRAD.value,
            # Московское время
            "москва": RussianTimezone.MOSCOW.value,
            "санкт-петербург": RussianTimezone.MOSCOW.value,
            "спб": RussianTimezone.MOSCOW.value,
            "питер": RussianTimezone.MOSCOW.value,
            "воронеж": RussianTimezone.MOSCOW.value,
            "нижний новгород": RussianTimezone.MOSCOW.value,
            "ростов-на-дону": RussianTimezone.MOSCOW.value,
            "краснодар": RussianTimezone.MOSCOW.value,
            "сочи": RussianTimezone.MOSCOW.value,
            # Самарское время
            "самара": RussianTimezone.SAMARA.value,
            "тольятти": RussianTimezone.SAMARA.value,
            "ульяновск": RussianTimezone.SAMARA.value,
            "саратов": RussianTimezone.SAMARA.value,
            # Екатеринбургское время
            "екатеринбург": RussianTimezone.YEKATERINBURG.value,
            "челябинск": RussianTimezone.YEKATERINBURG.value,
            "уфа": RussianTimezone.YEKATERINBURG.value,
            "пермь": RussianTimezone.YEKATERINBURG.value,
            "тюмень": RussianTimezone.YEKATERINBURG.value,
            # Омское время
            "омск": RussianTimezone.OMSK.value,
            # Красноярское время
            "красноярск": RussianTimezone.KRASNOYARSK.value,
            "новосибирск": RussianTimezone.NOVOSIBIRSK.value,
            "кемерово": RussianTimezone.KRASNOYARSK.value,
            "барнаул": RussianTimezone.KRASNOYARSK.value,
            "томск": RussianTimezone.KRASNOYARSK.value,
            # Иркутское время
            "иркутск": RussianTimezone.IRKUTSK.value,
            "улан-удэ": RussianTimezone.IRKUTSK.value,
            "чита": RussianTimezone.IRKUTSK.value,
            # Якутское время
            "якутск": RussianTimezone.YAKUTSK.value,
            "благовещенск": RussianTimezone.YAKUTSK.value,
            "комсомольск-на-амуре": RussianTimezone.YAKUTSK.value,
            # Владивостокское время
            "владивосток": RussianTimezone.VLADIVOSTOK.value,
            "хабаровск": RussianTimezone.VLADIVOSTOK.value,
            "уссурийск": RussianTimezone.VLADIVOSTOK.value,
            # Магаданское время
            "магадан": RussianTimezone.MAGADAN.value,
            "южно-сахалинск": RussianTimezone.MAGADAN.value,
            # Камчатское время
            "петропавловск-камчатский": RussianTimezone.KAMCHATKA.value,
            "анадырь": RussianTimezone.KAMCHATKA.value,
        }

        city_lower = city_name.lower().strip()
        timezone_info = city_timezone_map.get(city_lower)

        if timezone_info:
            logger.info(
                f"RUSSIAN_ADAPTER_TIMEZONE: Found timezone for {city_name}: {timezone_info['name']}"
            )
            return timezone_info
        else:
            logger.warning(
                f"RUSSIAN_ADAPTER_TIMEZONE: Unknown city {city_name}, using Moscow time"
            )
            return RussianTimezone.MOSCOW.value

    def format_for_voice(
        self,
        text: str,
        add_stress_marks: bool = True,
        insert_pauses: bool = False,
        max_length: int = None,
    ) -> str:
        """
        Форматирование текста для голосового вывода с правильными ударениями.

        Args:
            text: Исходный текст
            add_stress_marks: Добавлять ли знаки ударения
            insert_pauses: Вставлять ли паузы между предложениями
            max_length: Максимальная длина текста

        Returns:
            Отформатированный текст для голосового синтеза
        """
        # Словарь ударений для астрологических терминов
        stress_map = {
            "овен": "овéн",
            "телец": "телéц",
            "близнецы": "близнецы́",
            "рак": "рак",
            "лев": "лев",
            "дева": "дéва",
            "весы": "весы́",
            "скорпион": "скорпио́н",
            "стрелец": "стрелéц",
            "козерог": "козеро́г",
            "водолей": "водолéй",
            "рыбы": "ры́бы",
            "солнце": "со́лнце",
            "луна": "луна́",
            "меркурий": "мерку́рий",
            "венера": "венéра",
            "марс": "марс",
            "юпитер": "юпи́тер",
            "сатурн": "сату́рн",
            "уран": "ура́н",
            "нептун": "непту́н",
            "плутон": "плуто́н",
            "хирон": "хиро́н",
            "лилит": "лили́т",
        }

        result = text

        # Apply stress marks if requested
        if add_stress_marks:
            # Store the original case pattern
            result.lower()
            for word, stressed in stress_map.items():
                # Find case-insensitive occurrences and replace them
                import re

                pattern = re.compile(re.escape(word), re.IGNORECASE)

                def replace_with_case(match):
                    original = match.group()
                    if original[0].isupper():
                        # If original was capitalized, capitalize the stressed version
                        return stressed.capitalize()
                    return stressed

                result = pattern.sub(replace_with_case, result)

        # Insert pauses if requested
        if insert_pauses:
            result = (
                result.replace(".", ". - ")
                .replace("!", "! - ")
                .replace("?", "? - ")
            )

        # Limit length if specified
        if max_length and len(result) > max_length:
            result = result[: max_length - 3] + "..."

        # Sanitize for voice output (remove script tags and dangerous content)
        import re

        # Remove script tags
        result = result.replace("<script>", "").replace("</script>", "")
        # Remove JavaScript functions that could be dangerous
        result = re.sub(r"alert\s*\([^)]*\)", "", result)
        result = re.sub(r"eval\s*\([^)]*\)", "", result)
        result = re.sub(r"document\.[^;\s]*", "", result)
        # Remove any remaining HTML tags
        result = re.sub(r"<[^>]*>", "", result)

        return result

    def get_localized_chart_data(self) -> Dict[str, Any]:
        """
        Получить полную локализованную информацию о натальной карте.

        Returns:
            Словарь с русскими астрологическими данными
        """
        if not self.available or not self.subject:
            logger.warning(
                "RUSSIAN_ADAPTER_CHART: Kerykeion or subject not available"
            )
            return {"error": "Kerykeion not available or no subject"}

        try:
            result = {
                "planets": {},
                "houses": {},
                "aspects": [],
                "general_info": {},
            }

            # Информация о планетах
            if hasattr(self.subject, "planets_list"):
                for planet in self.subject.planets_list:
                    planet_name = planet.get("name", "")
                    planet_ru = self.get_russian_planet_description(
                        planet_name
                    )
                    sign_name = planet.get("sign", "")
                    sign_ru = self.get_russian_sign_description(sign_name)

                    result["planets"][planet_name] = {
                        "russian_name": planet_ru.get("name", planet_name),
                        "sign": sign_ru.get("name", sign_name),
                        "degree": planet.get("pos", 0),
                        "house": planet.get("house", 0),
                        "keywords": planet_ru.get("keywords", []),
                        "description": planet_ru.get("description", ""),
                    }

            # Информация о домах
            if hasattr(self.subject, "houses_list"):
                for i, house in enumerate(self.subject.houses_list, 1):
                    house_ru = self.get_russian_house_description(i)
                    sign_name = house.get("sign", "")
                    sign_ru = self.get_russian_sign_description(sign_name)

                    result["houses"][f"house_{i}"] = {
                        "number": i,
                        "name": house_ru.get("name", f"Дом {i}"),
                        "sign": sign_ru.get("name", sign_name),
                        "degree": house.get("pos", 0),
                        "keywords": house_ru.get("keywords", []),
                        "description": house_ru.get("description", ""),
                    }

            # Информация об аспектах
            if hasattr(self.subject, "aspects_list"):
                for aspect in self.subject.aspects_list:
                    aspect_description = self.get_russian_aspect_description(
                        aspect
                    )
                    result["aspects"].append(
                        {
                            "description": aspect_description,
                            "type": aspect.get("aspect", ""),
                            "orb": aspect.get("orbit", 0),
                            "planets": [
                                aspect.get("p1_name", ""),
                                aspect.get("p2_name", ""),
                            ],
                        }
                    )

            # Общая информация
            result["general_info"] = {
                "name": getattr(self.subject, "name", "Неизвестно"),
                "birth_date": getattr(self.subject, "day", "?")
                + "."
                + str(getattr(self.subject, "month", "?"))
                + "."
                + str(getattr(self.subject, "year", "?")),
                "birth_time": str(getattr(self.subject, "hour", "?"))
                + ":"
                + str(getattr(self.subject, "minute", "?")),
                "birth_place": f"{getattr(self.subject, 'city', 'Неизвестно')}, {getattr(self.subject, 'nation', '')}",
            }

            logger.info(
                "RUSSIAN_ADAPTER_CHART: Successfully generated localized chart data"
            )
            return result

        except Exception as e:
            logger.error(f"RUSSIAN_ADAPTER_CHART_ERROR: {e}")
            return {"error": f"Error getting localized chart data: {e}"}

    def create_localized_subject(
        self,
        name: str,
        birth_date: date,
        birth_time: time,
        birth_place: Dict[str, Any],
        city_name: str = "",
        timezone_str: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Создать AstrologicalSubject с автоматическим определением российского часового пояса.

        Args:
            name: Имя
            birth_date: Дата рождения
            birth_time: Время рождения
            birth_place: Координаты места рождения
            city_name: Название города для определения часового пояса
            timezone_str: Явно указанный часовой пояс

        Returns:
            AstrologicalSubject или None при ошибке
        """
        if not self.available:
            logger.error("RUSSIAN_ADAPTER_CREATE: Kerykeion not available")
            return None

        try:
            # Определение часового пояса
            if not timezone_str and city_name:
                timezone_info = self.detect_russian_timezone(city_name)
                if timezone_info:
                    timezone_str = timezone_info["zone"]
                else:
                    timezone_str = "Europe/Moscow"
            elif not timezone_str:
                timezone_str = "Europe/Moscow"

            # Создание datetime объекта
            datetime.combine(birth_date, birth_time)

            # Создание AstrologicalSubject
            subject = AstrologicalSubject(
                name=name,
                year=birth_date.year,
                month=birth_date.month,
                day=birth_date.day,
                hour=birth_time.hour,
                minute=birth_time.minute,
                lat=birth_place.get("latitude", 55.7558),
                lng=birth_place.get("longitude", 37.6176),
                tz_str=timezone_str,
            )

            self.subject = subject
            logger.info(
                f"RUSSIAN_ADAPTER_CREATE: Created subject for {name} in {timezone_str}"
            )
            return subject

        except Exception as e:
            logger.error(f"RUSSIAN_ADAPTER_CREATE_ERROR: {e}")
            return None

    def generate_russian_interpretation(self, focus: str = "general") -> str:
        """
        Генерация культурно-адаптированной интерпретации на русском языке.

        Args:
            focus: Фокус интерпретации (general, career, love, health, spiritual)

        Returns:
            Русская интерпретация
        """
        if not self.subject:
            return "Для интерпретации необходимы астрологические данные"

        try:
            chart_data = self.get_localized_chart_data()
            if "error" in chart_data:
                return f"Ошибка получения данных: {chart_data['error']}"

            interpretation_parts = []

            # Солнце - основа личности
            if "Sun" in chart_data["planets"]:
                sun_data = chart_data["planets"]["Sun"]
                sun_sign = sun_data["sign"]
                interpretation_parts.append(
                    f"Ваше Солнце в знаке {sun_sign} определяет основные черты личности. "
                    f"Это влияет на вашу волю, творческие способности и жизненные цели."
                )

            # Луна - эмоциональная сфера
            if "Moon" in chart_data["planets"]:
                moon_data = chart_data["planets"]["Moon"]
                moon_sign = moon_data["sign"]
                interpretation_parts.append(
                    f"Луна в {moon_sign} показывает ваш эмоциональный мир и интуицию. "
                    f"Это влияет на отношения с семьей и подсознательные реакции."
                )

            # Асцендент (если есть)
            if "house_1" in chart_data["houses"]:
                asc_data = chart_data["houses"]["house_1"]
                asc_sign = asc_data["sign"]
                interpretation_parts.append(
                    f"Ваш Асцендент в {asc_sign} определяет первое впечатление, которое вы производите, "
                    f"и способ взаимодействия с окружающим миром."
                )

            # Специализированный фокус
            if focus == "career":
                if "house_10" in chart_data["houses"]:
                    mc_data = chart_data["houses"]["house_10"]
                    mc_sign = mc_data["sign"]
                    interpretation_parts.append(
                        f"Десятый дом в {mc_sign} указывает на ваши карьерные устремления "
                        f"и способы достижения профессиональных целей."
                    )

            elif focus == "love":
                if "Venus" in chart_data["planets"]:
                    venus_data = chart_data["planets"]["Venus"]
                    venus_sign = venus_data["sign"]
                    interpretation_parts.append(
                        f"Венера в {venus_sign} показывает ваш подход к любви, красоте и отношениям. "
                        f"Это влияет на ваши романтические предпочтения и способность к гармонии."
                    )

            result = " ".join(interpretation_parts)

            if not result:
                result = "Астрологические данные получены, но интерпретация временно недоступна."

            logger.info(
                f"RUSSIAN_ADAPTER_INTERPRETATION: Generated {focus} interpretation"
            )
            return result

        except Exception as e:
            logger.error(f"RUSSIAN_ADAPTER_INTERPRETATION_ERROR: {e}")
            return f"Ошибка генерации интерпретации: {e}"

    def localize_kerykeion_planet_data(
        self, planet_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Localize Kerykeion planet data to Russian."""
        try:
            localized_data = planet_data.copy()

            # Check if this is a dictionary of planets or a single planet's data
            # If it has planet names as keys (sun, moon, etc.)
            if any(
                key in localized_data
                for key in [
                    "sun",
                    "moon",
                    "mercury",
                    "venus",
                    "mars",
                    "jupiter",
                    "saturn",
                ]
            ):
                # Process each planet
                for planet_key, planet_info in localized_data.items():
                    if isinstance(planet_info, dict):
                        # Translate planet name if exists
                        if "name" in planet_info:
                            planet_name = planet_info["name"].lower()
                            russian_planet = (
                                self.get_russian_planet_description(
                                    planet_name
                                )
                            )
                            planet_info["name"] = russian_planet.get(
                                "name", planet_info["name"]
                            )

                        # Translate zodiac sign if exists
                        if "sign" in planet_info:
                            sign_name = planet_info["sign"].lower()
                            russian_sign = self.get_russian_sign_description(
                                sign_name
                            )
                            planet_info["sign"] = russian_sign.get(
                                "name", planet_info["sign"]
                            )
            else:
                # Handle single planet data
                # Translate planet name
                if "name" in localized_data:
                    planet_name = localized_data["name"].lower()
                    russian_planet = self.get_russian_planet_description(
                        planet_name
                    )
                    localized_data["name"] = russian_planet.get(
                        "name", localized_data["name"]
                    )

                # Translate zodiac sign
                if "sign" in localized_data:
                    sign_name = localized_data["sign"].lower()
                    russian_sign = self.get_russian_sign_description(sign_name)
                    localized_data["sign"] = russian_sign.get(
                        "name", localized_data["sign"]
                    )

            return localized_data
        except Exception as e:
            logger.error(f"RUSSIAN_ADAPTER_PLANET_LOCALIZE_ERROR: {e}")
            return planet_data

    def localize_kerykeion_aspect_data(
        self, aspect_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Localize Kerykeion aspect data to Russian."""
        try:
            localized_aspects = []

            # Russian aspect translations
            aspect_translations = {
                "conjunction": "Соединение",
                "sextile": "Секстиль",
                "square": "Квадрат",
                "trine": "Тригон",
                "opposition": "Оппозиция",
                "quincunx": "Квинконс",
                "semisextile": "Полусекстиль",
                "semisquare": "Полуквадрат",
                "sesquiquadrate": "Полутораквадрат",
            }

            for aspect in aspect_data:
                localized_aspect = aspect.copy()

                # Translate planet names
                if "planet1" in aspect:
                    planet1_desc = self.get_russian_planet_description(
                        aspect["planet1"]
                    )
                    if planet1_desc:
                        localized_aspect["planet1"] = planet1_desc["name"]

                if "planet2" in aspect:
                    planet2_desc = self.get_russian_planet_description(
                        aspect["planet2"]
                    )
                    if planet2_desc:
                        localized_aspect["planet2"] = planet2_desc["name"]

                # Translate aspect type
                if "aspect" in aspect:
                    aspect_name = aspect["aspect"].lower()
                    if aspect_name in aspect_translations:
                        localized_aspect["aspect"] = aspect_translations[
                            aspect_name
                        ]

                localized_aspects.append(localized_aspect)

            return localized_aspects
        except Exception as e:
            logger.error(f"RUSSIAN_ADAPTER_ASPECT_LOCALIZE_ERROR: {e}")
            return aspect_data

    def localize_complete_astrological_data(
        self, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Localize complete astrological data to Russian."""
        try:
            localized_data = data.copy()

            # Handle nested chart structure
            if "natal_chart" in data:
                natal_chart = data["natal_chart"].copy()

                # Localize planets
                if "planets" in natal_chart:
                    natal_chart[
                        "planets"
                    ] = self.localize_kerykeion_planet_data(
                        natal_chart["planets"]
                    )

                # Localize aspects
                if "aspects" in natal_chart:
                    natal_chart[
                        "aspects"
                    ] = self.localize_kerykeion_aspect_data(
                        natal_chart["aspects"]
                    )

                localized_data["natal_chart"] = natal_chart

            # Handle transit data
            if (
                "transit_data" in data
                and "current_transits" in data["transit_data"]
            ):
                transit_data = data["transit_data"].copy()
                current_transits = []

                for transit in data["transit_data"]["current_transits"]:
                    localized_transit = transit.copy()

                    # Translate transit planet
                    if "transit_planet" in transit:
                        planet_desc = self.get_russian_planet_description(
                            transit["transit_planet"]
                        )
                        if planet_desc:
                            localized_transit["transit_planet"] = planet_desc[
                                "name"
                            ]

                    # Translate natal planet
                    if "natal_planet" in transit:
                        planet_desc = self.get_russian_planet_description(
                            transit["natal_planet"]
                        )
                        if planet_desc:
                            localized_transit["natal_planet"] = planet_desc[
                                "name"
                            ]

                    # Translate aspect
                    if "aspect" in transit:
                        aspect_translations = {
                            "conjunction": "Соединение",
                            "sextile": "Секстиль",
                            "square": "Квадрат",
                            "trine": "Тригон",
                            "opposition": "Оппозиция",
                        }
                        aspect_name = transit["aspect"].lower()
                        if aspect_name in aspect_translations:
                            localized_transit["aspect"] = aspect_translations[
                                aspect_name
                            ]

                    current_transits.append(localized_transit)

                transit_data["current_transits"] = current_transits
                localized_data["transit_data"] = transit_data

            # Direct planets localization for simpler structures
            elif "planets" in data:
                localized_data[
                    "planets"
                ] = self.localize_kerykeion_planet_data(data["planets"])

            return localized_data
        except Exception as e:
            logger.error(f"RUSSIAN_ADAPTER_COMPLETE_LOCALIZE_ERROR: {e}")
            return data

    def generate_voice_optimized_interpretation(
        self, data: Dict[str, Any]
    ) -> str:
        """Generate voice-optimized interpretation."""
        try:
            # Generate basic interpretation based on provided data
            if "name" in data and "sign" in data:
                # Planet interpretation
                planet_desc = self.get_russian_planet_description(data["name"])
                sign_desc = self.get_russian_sign_description(data["sign"])

                if planet_desc and sign_desc:
                    base_interpretation = (
                        f"{planet_desc['name']} в знаке {sign_desc['name']}"
                    )
                    if planet_desc.get("description"):
                        base_interpretation += (
                            f". {planet_desc['description'][:100]}..."
                        )
                else:
                    base_interpretation = f"{data.get('name', 'планета')} в знаке {data.get('sign', 'неизвестном')}"
            else:
                # Fallback interpretation
                base_interpretation = self.generate_russian_interpretation()

            return self.format_for_voice(
                base_interpretation, add_stress_marks=True
            )
        except Exception as e:
            logger.error(f"RUSSIAN_ADAPTER_VOICE_INTERPRETATION_ERROR: {e}")
            return "Для интерпретации необходимы астрологические данные"

    def get_stress_marks_dictionary(self) -> Dict[str, str]:
        """Get stress marks dictionary for astrological terms."""
        return {
            "овен": "ове́н",
            "телец": "теле́ц",
            "близнецы": "близнецы́",
            "рак": "рак",
            "лев": "лев",
            "дева": "де́ва",
            "весы": "весы́",
            "скорпион": "скорпио́н",
            "стрелец": "стреле́ц",
            "козерог": "козеро́г",
            "водолей": "водоле́й",
            "рыбы": "ры́бы",
            "солнце": "со́лнце",
            "луна": "луна́",
            "меркурий": "мерку́рий",
            "венера": "вене́ра",
            "марс": "марс",
            "юпитер": "юпи́тер",
            "сатурн": "сату́рн",
            "уран": "ура́н",
            "нептун": "непту́н",
            "плутон": "плуто́н",
        }


# Глобальный экземпляр адаптера
russian_adapter = RussianAstrologyAdapter()
