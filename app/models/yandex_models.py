"""
Модели данных для интеграции с Яндекс.Диалогами.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class YandexRequestType(str, Enum):
    """Типы запросов от Яндекс.Диалогов."""

    SIMPLE_UTTERANCE = "SimpleUtterance"
    BUTTON_PRESSED = "ButtonPressed"


class YandexIntent(str, Enum):
    """Поддерживаемые интенты навыка."""

    GREET = "greet"
    HOROSCOPE = "horoscope"
    COMPATIBILITY = "compatibility"
    NATAL_CHART = "natal_chart"
    LUNAR_CALENDAR = "lunar_calendar"
    TRANSITS = "transits"
    PROGRESSIONS = "progressions"
    SOLAR_RETURN = "solar_return"
    LUNAR_RETURN = "lunar_return"
    ADVICE = "advice"
    HELP = "help"
    EXIT = "exit"
    UNKNOWN = "unknown"


class YandexZodiacSign(str, Enum):
    """Знаки зодиака."""

    ARIES = "овен"
    TAURUS = "телец"
    GEMINI = "близнецы"
    CANCER = "рак"
    LEO = "лев"
    VIRGO = "дева"
    LIBRA = "весы"
    SCORPIO = "скорпион"
    SAGITTARIUS = "стрелец"
    CAPRICORN = "козерог"
    AQUARIUS = "водолей"
    PISCES = "рыбы"


class YandexButton(BaseModel):
    """Кнопка в интерфейсе Алисы."""

    title: str
    payload: Optional[Dict[str, Any]] = None
    url: Optional[str] = None
    hide: bool = True

    def __init__(self, **data):
        super().__init__(**data)
        # Ensure button title length complies with Alice limits (max 64 chars)
        if len(self.title) > 64:
            self.title = self.title[:61] + "..."


class YandexCard(BaseModel):
    """Карточка в интерфейсе Алисы."""

    type: str = "BigImage"
    image_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    button: Optional[YandexButton] = None

    def __init__(self, **data):
        super().__init__(**data)
        # Ensure title and description length comply with Alice limits
        if self.title and len(self.title) > 128:
            self.title = self.title[:125] + "..."
        if self.description and len(self.description) > 256:
            self.description = self.description[:253] + "..."


class YandexRequestMeta(BaseModel):
    """Метаданные запроса."""

    locale: str
    timezone: str
    client_id: str
    interfaces: Dict[str, Any] = Field(default_factory=dict)


class YandexApplication(BaseModel):
    """Данные приложения."""

    application_id: str


class YandexRequestData(BaseModel):
    """Данные запроса пользователя."""

    command: Optional[str] = ""
    original_utterance: Optional[str] = ""
    type: YandexRequestType
    markup: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None
    nlu: Optional[Dict[str, Any]] = None


# Alias for backward compatibility
YandexRequest = YandexRequestData


class YandexSession(BaseModel):
    """Данные сессии."""

    message_id: int
    session_id: str
    skill_id: str
    user_id: str
    user: Optional[Dict[str, Any]] = None
    application: Optional[YandexApplication] = None
    new: bool = True


class YandexRequestModel(BaseModel):
    """Полная модель запроса от Яндекс.Диалогов."""

    meta: YandexRequestMeta
    request: YandexRequestData
    session: YandexSession
    version: str = "1.0"


class YandexResponse(BaseModel):
    """Ответ для Яндекс.Диалогов."""

    text: str
    tts: Optional[str] = None
    card: Optional[YandexCard] = None
    buttons: Optional[List[YandexButton]] = None
    end_session: bool = False
    directives: Optional[Dict[str, Any]] = None

    def __init__(self, **data):
        super().__init__(**data)
        # Ensure Alice button limit compliance (max 5 buttons)
        if self.buttons and len(self.buttons) > 5:
            self.buttons = self.buttons[:5]
        # Ensure text is not empty for Alice compatibility
        if not self.text or len(self.text.strip()) == 0:
            self.text = "Извините, произошла ошибка. Попробуйте еще раз."
        # Ensure text length is reasonable for voice interface
        if len(self.text) > 1024:
            self.text = self.text[:1020] + "..."


class YandexResponseModel(BaseModel):
    """Полная модель ответа для Яндекс.Диалогов."""

    response: YandexResponse
    session: YandexSession
    version: str = "1.0"


class UserContext(BaseModel):
    """Контекст пользователя в сессии."""

    user_id: Optional[str] = None
    intent: Optional[YandexIntent] = None
    awaiting_data: Optional[
        str
    ] = None  # Ожидаемые данные (дата рождения, знак и т.д.)
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    birth_place: Optional[str] = None
    zodiac_sign: Optional[YandexZodiacSign] = None
    partner_sign: Optional[YandexZodiacSign] = None
    conversation_step: int = 0
    last_request: Optional[str] = None


class ProcessedRequest(BaseModel):
    """Обработанный запрос с извлеченными данными."""

    intent: YandexIntent
    entities: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    raw_text: str
    user_context: UserContext
