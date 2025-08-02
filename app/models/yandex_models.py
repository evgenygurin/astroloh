"""
Модели данных для интеграции с Яндекс.Диалогами.
"""
from enum import Enum
from typing import Dict, Any, Optional, List
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
    ADVICE = "advice"
    HELP = "help"
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


class YandexCard(BaseModel):
    """Карточка в интерфейсе Алисы."""
    type: str = "BigImage"
    image_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    button: Optional[YandexButton] = None


class YandexRequestMeta(BaseModel):
    """Метаданные запроса."""
    locale: str
    timezone: str
    client_id: str
    interfaces: Dict[str, Any] = Field(default_factory=dict)


class YandexRequestData(BaseModel):
    """Данные запроса пользователя."""
    command: str
    original_utterance: str
    type: YandexRequestType
    markup: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None
    nlu: Optional[Dict[str, Any]] = None


class YandexSession(BaseModel):
    """Данные сессии."""
    message_id: int
    session_id: str
    skill_id: str
    user_id: str
    user: Optional[Dict[str, Any]] = None
    application: Optional[Dict[str, Any]] = None
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


class YandexResponseModel(BaseModel):
    """Полная модель ответа для Яндекс.Диалогов."""
    response: YandexResponse
    session: YandexSession
    version: str = "1.0"


class UserContext(BaseModel):
    """Контекст пользователя в сессии."""
    intent: Optional[YandexIntent] = None
    awaiting_data: Optional[str] = None  # Ожидаемые данные (дата рождения, знак и т.д.)
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