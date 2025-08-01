"""
Тесты для валидаторов данных.
"""
import pytest
from datetime import date
from app.utils.validators import DateValidator, ZodiacValidator, YandexRequestValidator
from app.models.yandex_models import YandexZodiacSign
from app.utils.error_handler import ValidationSkillError


class TestDateValidator:
    """Тесты для валидатора дат."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.validator = DateValidator()

    def test_parse_date_string_valid_formats(self):
        """Тест парсинга различных форматов дат."""
        test_cases = [
            ("15.03.1990", date(1990, 3, 15)),
            ("15/03/1990", date(1990, 3, 15)),
            ("15-03-1990", date(1990, 3, 15)),
            ("15 03 1990", date(1990, 3, 15)),
            ("1990.03.15", date(1990, 3, 15)),
            ("15.03.90", date(1990, 3, 15)),  # Предполагаем 20 век
        ]
        
        for date_str, expected_date in test_cases:
            parsed_date = self.validator.parse_date_string(date_str)
            assert parsed_date == expected_date

    def test_parse_date_string_invalid_formats(self):
        """Тест парсинга неверных форматов дат."""
        invalid_dates = [
            "не дата",
            "32.13.1990",  # Неверный день и месяц
            "abc.def.ghij",
            ""
        ]
        
        for date_str in invalid_dates:
            parsed_date = self.validator.parse_date_string(date_str)
            assert parsed_date is None

    def test_validate_birth_date_valid(self):
        """Тест валидации корректных дат рождения."""
        valid_dates = [
            date(1990, 3, 15),
            date(1980, 12, 31),
            date(2000, 1, 1)
        ]
        
        for birth_date in valid_dates:
            assert self.validator.validate_birth_date(birth_date) is True

    def test_validate_birth_date_future(self):
        """Тест валидации будущих дат рождения."""
        from datetime import date, timedelta
        future_date = date.today() + timedelta(days=1)
        
        with pytest.raises(ValidationSkillError):
            self.validator.validate_birth_date(future_date)

    def test_get_zodiac_sign_by_date(self):
        """Тест определения знака зодиака по дате."""
        test_cases = [
            (date(1990, 3, 21), YandexZodiacSign.ARIES),    # Начало Овна
            (date(1990, 4, 19), YandexZodiacSign.ARIES),    # Конец Овна
            (date(1990, 4, 20), YandexZodiacSign.TAURUS),   # Начало Тельца
            (date(1990, 5, 20), YandexZodiacSign.TAURUS),   # Конец Тельца
            (date(1990, 12, 22), YandexZodiacSign.CAPRICORN), # Начало Козерога
            (date(1990, 1, 19), YandexZodiacSign.CAPRICORN),  # Конец Козерога
        ]
        
        for birth_date, expected_sign in test_cases:
            zodiac_sign = self.validator.get_zodiac_sign_by_date(birth_date)
            assert zodiac_sign == expected_sign


class TestZodiacValidator:
    """Тесты для валидатора знаков зодиака."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.validator = ZodiacValidator()

    def test_parse_zodiac_sign_russian(self):
        """Тест парсинга русских названий знаков."""
        test_cases = [
            ("овен", YandexZodiacSign.ARIES),
            ("телец", YandexZodiacSign.TAURUS),
            ("близнецы", YandexZodiacSign.GEMINI),
            ("рак", YandexZodiacSign.CANCER),
            ("лев", YandexZodiacSign.LEO),
            ("дева", YandexZodiacSign.VIRGO),
            ("весы", YandexZodiacSign.LIBRA),
            ("скорпион", YandexZodiacSign.SCORPIO),
            ("стрелец", YandexZodiacSign.SAGITTARIUS),
            ("козерог", YandexZodiacSign.CAPRICORN),
            ("водолей", YandexZodiacSign.AQUARIUS),
            ("рыбы", YandexZodiacSign.PISCES),
        ]
        
        for sign_str, expected_sign in test_cases:
            parsed_sign = self.validator.parse_zodiac_sign(sign_str)
            assert parsed_sign == expected_sign

    def test_parse_zodiac_sign_english(self):
        """Тест парсинга английских названий знаков."""
        test_cases = [
            ("aries", YandexZodiacSign.ARIES),
            ("taurus", YandexZodiacSign.TAURUS),
            ("gemini", YandexZodiacSign.GEMINI),
            ("leo", YandexZodiacSign.LEO),
        ]
        
        for sign_str, expected_sign in test_cases:
            parsed_sign = self.validator.parse_zodiac_sign(sign_str)
            assert parsed_sign == expected_sign

    def test_parse_zodiac_sign_invalid(self):
        """Тест парсинга неверных знаков зодиака."""
        invalid_signs = [
            "неверный знак",
            "123",
            "",
            "qwerty"
        ]
        
        for sign_str in invalid_signs:
            parsed_sign = self.validator.parse_zodiac_sign(sign_str)
            assert parsed_sign is None

    def test_validate_zodiac_sign(self):
        """Тест валидации знаков зодиака."""
        valid_sign = YandexZodiacSign.ARIES
        assert self.validator.validate_zodiac_sign(valid_sign) is True


class TestYandexRequestValidator:
    """Тесты для валидатора запросов Яндекс.Диалогов."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.validator = YandexRequestValidator()

    def test_validate_request_structure_valid(self):
        """Тест валидации корректной структуры запроса."""
        valid_request = {
            "meta": {"locale": "ru-RU"},
            "request": {"command": "привет"},
            "session": {"session_id": "test-session"},
            "version": "1.0"
        }
        
        assert self.validator.validate_request_structure(valid_request) is True

    def test_validate_request_structure_missing_fields(self):
        """Тест валидации запроса с отсутствующими полями."""
        invalid_request = {
            "meta": {"locale": "ru-RU"},
            "request": {"command": "привет"},
            # Отсутствует session и version
        }
        
        with pytest.raises(ValidationSkillError):
            self.validator.validate_request_structure(invalid_request)

    def test_sanitize_user_input(self):
        """Тест санитизации пользовательского ввода."""
        test_cases = [
            ("обычный текст", "обычный текст"),
            ("текст с <script>", "текст с script"),
            ("  пробелы  ", "пробелы"),
            ("", ""),
        ]
        
        for input_text, expected_output in test_cases:
            sanitized = self.validator.sanitize_user_input(input_text)
            assert sanitized == expected_output

    def test_sanitize_user_input_long_text(self):
        """Тест санитизации длинного текста."""
        long_text = "a" * 1500  # Больше лимита в 1000 символов
        sanitized = self.validator.sanitize_user_input(long_text)
        assert len(sanitized) <= 1000