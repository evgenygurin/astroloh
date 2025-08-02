"""
Валидаторы данных для навыка Яндекс.Диалогов.
"""
import re
from datetime import date
from typing import Optional, Tuple

from app.models.yandex_models import YandexZodiacSign
from app.utils.error_handler import ValidationSkillError


class DateValidator:
    """Валидатор дат."""

    @staticmethod
    def parse_date_string(date_str: str) -> Optional[date]:
        """Парсит строку даты в объект date."""
        date_str = date_str.strip().lower()

        # Удаляем лишние символы
        date_str = re.sub(r"[^\d\.\-\/\s]", "", date_str)

        patterns = [
            (r"^(\d{1,2})[\.\/\-\s](\d{1,2})[\.\/\-\s](\d{4})$", "%d.%m.%Y"),
            (r"^(\d{1,2})[\.\/\-\s](\d{1,2})[\.\/\-\s](\d{2})$", "%d.%m.%y"),
            (r"^(\d{4})[\.\/\-\s](\d{1,2})[\.\/\-\s](\d{1,2})$", "%Y.%m.%d"),
            (r"^(\d{1,2})\s(\d{1,2})\s(\d{4})$", "%d %m %Y"),
        ]

        for pattern, date_format in patterns:
            match = re.match(pattern, date_str)
            if match:
                try:
                    if date_format in ["%d.%m.%Y", "%d %m %Y"]:
                        day, month, year = match.groups()
                        return date(int(year), int(month), int(day))
                    elif date_format == "%d.%m.%y":
                        day, month, year = match.groups()
                        year = int(year)
                        if year < 50:
                            year += 2000
                        else:
                            year += 1900
                        return date(year, int(month), int(day))
                    elif date_format == "%Y.%m.%d":
                        year, month, day = match.groups()
                        return date(int(year), int(month), int(day))
                except ValueError:
                    continue

        return None

    @staticmethod
    def validate_birth_date(birth_date: date) -> bool:
        """Валидирует дату рождения."""
        today = date.today()

        # Проверяем, что дата не в будущем
        if birth_date > today:
            raise ValidationSkillError(
                "Дата рождения не может быть в будущем", "birth_date"
            )

        # Проверяем разумные границы (не старше 150 лет)
        min_date = date(today.year - 150, today.month, today.day)
        if birth_date < min_date:
            raise ValidationSkillError(
                "Дата рождения слишком давняя", "birth_date"
            )

        return True

    @staticmethod
    def get_zodiac_sign_by_date(birth_date: date) -> YandexZodiacSign:
        """Определяет знак зодиака по дате рождения."""
        month = birth_date.month
        day = birth_date.day

        if (month == 3 and day >= 21) or (month == 4 and day <= 19):
            return YandexZodiacSign.ARIES
        elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
            return YandexZodiacSign.TAURUS
        elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
            return YandexZodiacSign.GEMINI
        elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
            return YandexZodiacSign.CANCER
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
            return YandexZodiacSign.LEO
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
            return YandexZodiacSign.VIRGO
        elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
            return YandexZodiacSign.LIBRA
        elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
            return YandexZodiacSign.SCORPIO
        elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
            return YandexZodiacSign.SAGITTARIUS
        elif (month == 12 and day >= 22) or (month == 1 and day <= 19):
            return YandexZodiacSign.CAPRICORN
        elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
            return YandexZodiacSign.AQUARIUS
        else:  # (month == 2 and day >= 19) or (month == 3 and day <= 20)
            return YandexZodiacSign.PISCES


class TimeValidator:
    """Валидатор времени."""

    @staticmethod
    def parse_time_string(time_str: str) -> Optional[Tuple[int, int]]:
        """Парсит строку времени в часы и минуты."""
        time_str = time_str.strip().lower()

        patterns = [
            r"^(\d{1,2}):(\d{2})$",  # HH:MM
            r"^(\d{1,2})\s*час(?:а|ов)?\s*(\d{1,2})?\s*мин(?:ут|уты?)?",  # X час Y минут
            r"^(\d{1,2})\s*час(?:а|ов)?$",  # X час
        ]

        for pattern in patterns:
            match = re.search(pattern, time_str)
            if match:
                try:
                    hours = int(match.group(1))
                    minutes = int(match.group(2)) if match.group(2) else 0

                    if 0 <= hours <= 23 and 0 <= minutes <= 59:
                        return hours, minutes
                except (ValueError, IndexError):
                    continue

        return None

    @staticmethod
    def validate_time(hours: int, minutes: int) -> bool:
        """Валидирует время."""
        if not (0 <= hours <= 23):
            raise ValidationSkillError("Часы должны быть от 0 до 23", "time")

        if not (0 <= minutes <= 59):
            raise ValidationSkillError("Минуты должны быть от 0 до 59", "time")

        return True


class ZodiacValidator:
    """Валидатор знаков зодиака."""

    @staticmethod
    def parse_zodiac_sign(sign_str: str) -> Optional[YandexZodiacSign]:
        """Парсит строку знака зодиака."""
        sign_str = sign_str.strip().lower()

        sign_mappings = {
            "овен": YandexZodiacSign.ARIES,
            "aries": YandexZodiacSign.ARIES,
            "телец": YandexZodiacSign.TAURUS,
            "taurus": YandexZodiacSign.TAURUS,
            "близнецы": YandexZodiacSign.GEMINI,
            "gemini": YandexZodiacSign.GEMINI,
            "рак": YandexZodiacSign.CANCER,
            "cancer": YandexZodiacSign.CANCER,
            "лев": YandexZodiacSign.LEO,
            "leo": YandexZodiacSign.LEO,
            "дева": YandexZodiacSign.VIRGO,
            "virgo": YandexZodiacSign.VIRGO,
            "весы": YandexZodiacSign.LIBRA,
            "libra": YandexZodiacSign.LIBRA,
            "скорпион": YandexZodiacSign.SCORPIO,
            "scorpio": YandexZodiacSign.SCORPIO,
            "стрелец": YandexZodiacSign.SAGITTARIUS,
            "sagittarius": YandexZodiacSign.SAGITTARIUS,
            "козерог": YandexZodiacSign.CAPRICORN,
            "capricorn": YandexZodiacSign.CAPRICORN,
            "водолей": YandexZodiacSign.AQUARIUS,
            "aquarius": YandexZodiacSign.AQUARIUS,
            "рыбы": YandexZodiacSign.PISCES,
            "pisces": YandexZodiacSign.PISCES,
        }

        return sign_mappings.get(sign_str)

    @staticmethod
    def validate_zodiac_sign(sign: YandexZodiacSign) -> bool:
        """Валидирует знак зодиака."""
        if not isinstance(sign, YandexZodiacSign):
            raise ValidationSkillError("Неверный знак зодиака", "zodiac_sign")

        return True


class YandexRequestValidator:
    """Валидатор запросов от Яндекс.Диалогов."""

    @staticmethod
    def validate_request_structure(request_data: dict) -> bool:
        """Валидирует структуру запроса."""
        required_fields = ["meta", "request", "session", "version"]

        for field in required_fields:
            if field not in request_data:
                raise ValidationSkillError(
                    f"Отсутствует обязательное поле: {field}", field
                )

        # Проверяем подполя
        if "command" not in request_data["request"]:
            raise ValidationSkillError(
                "Отсутствует команда в запросе", "command"
            )

        if "session_id" not in request_data["session"]:
            raise ValidationSkillError(
                "Отсутствует идентификатор сессии", "session_id"
            )

        return True

    @staticmethod
    def sanitize_user_input(text: str) -> str:
        """Очищает пользовательский ввод."""
        if not text:
            return ""

        # Удаляем потенциально опасные символы
        text = re.sub(r"[<>\"\'&]", "", text)

        # Ограничиваем длину
        max_length = 1000
        if len(text) > max_length:
            text = text[:max_length]

        return text.strip()
