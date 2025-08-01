"""
Сервис форматирования ответов для Яндекс.Диалогов.
"""
from typing import List, Optional, Dict, Any

from app.models.yandex_models import (
    YandexResponse, 
    YandexButton, 
    YandexCard,
    YandexIntent,
    YandexZodiacSign
)


class ResponseFormatter:
    """Класс для форматирования ответов Алисы."""
    
    def __init__(self):
        self.welcome_messages = [
            "Привет! Я астролог Алисы. Я могу составить гороскоп, рассказать о совместимости знаков или дать астрологический совет.",
            "Добро пожаловать! Меня зовут Астролог. Я помогу вам с гороскопами, совместимостью и астрологическими советами.",
            "Здравствуйте! Я ваш персональный астролог. Готов поделиться мудростью звёзд!"
        ]
        
        self.help_buttons = [
            YandexButton(title="Гороскоп", payload={"action": "horoscope"}),
            YandexButton(title="Совместимость", payload={"action": "compatibility"}),
            YandexButton(title="Совет дня", payload={"action": "advice"}),
            YandexButton(title="Помощь", payload={"action": "help"})
        ]

    def format_welcome_response(self, is_returning_user: bool = False) -> YandexResponse:
        """Форматирует приветственное сообщение."""
        if is_returning_user:
            text = "С возвращением! Что вас интересует сегодня?"
        else:
            text = self.welcome_messages[0]
        
        return YandexResponse(
            text=text,
            tts=self._add_tts_pauses(text),
            buttons=self.help_buttons,
            end_session=False
        )

    def format_horoscope_request_response(
        self, 
        has_birth_date: bool = False
    ) -> YandexResponse:
        """Форматирует запрос данных для гороскопа."""
        if not has_birth_date:
            text = "Для составления персонального гороскопа мне нужна ваша дата рождения. Назовите, пожалуйста, день, месяц и год."
        else:
            text = "Отлично! Теперь скажите время рождения, если знаете. Это поможет составить более точный гороскоп."
        
        buttons = [
            YandexButton(title="Не знаю время", payload={"action": "no_time"}),
            YandexButton(title="Назад", payload={"action": "back"})
        ]
        
        return YandexResponse(
            text=text,
            tts=self._add_tts_pauses(text),
            buttons=buttons if has_birth_date else None,
            end_session=False
        )

    def format_compatibility_request_response(
        self, 
        step: int = 1
    ) -> YandexResponse:
        """Форматирует запрос данных для проверки совместимости."""
        if step == 1:
            text = "Для проверки совместимости назовите ваш знак зодиака."
            buttons = self._get_zodiac_buttons()
        else:
            text = "Теперь назовите знак зодиака вашего партнера."
            buttons = self._get_zodiac_buttons()
        
        return YandexResponse(
            text=text,
            tts=self._add_tts_pauses(text),
            buttons=buttons,
            end_session=False
        )

    def format_horoscope_response(
        self, 
        zodiac_sign: YandexZodiacSign,
        period: str = "день"
    ) -> YandexResponse:
        """Форматирует ответ с гороскопом."""
        horoscope_text = self._generate_horoscope_text(zodiac_sign, period)
        
        text = f"Гороскоп для {zodiac_sign.value} на {period}:\n\n{horoscope_text}"
        
        buttons = [
            YandexButton(title="Другой период", payload={"action": "change_period"}),
            YandexButton(title="Совместимость", payload={"action": "compatibility"}),
            YandexButton(title="Совет дня", payload={"action": "advice"})
        ]
        
        return YandexResponse(
            text=text,
            tts=self._add_tts_pauses(text),
            buttons=buttons,
            end_session=False
        )

    def format_compatibility_response(
        self, 
        sign1: YandexZodiacSign,
        sign2: YandexZodiacSign
    ) -> YandexResponse:
        """Форматирует ответ о совместимости знаков."""
        compatibility_text = self._generate_compatibility_text(sign1, sign2)
        
        text = f"Совместимость {sign1.value} и {sign2.value}:\n\n{compatibility_text}"
        
        buttons = [
            YandexButton(title="Другая пара", payload={"action": "new_compatibility"}),
            YandexButton(title="Гороскоп", payload={"action": "horoscope"}),
            YandexButton(title="Главное меню", payload={"action": "main_menu"})
        ]
        
        return YandexResponse(
            text=text,
            tts=self._add_tts_pauses(text),
            buttons=buttons,
            end_session=False
        )

    def format_advice_response(self) -> YandexResponse:
        """Форматирует астрологический совет."""
        advice_text = self._generate_advice_text()
        
        text = f"Астрологический совет дня:\n\n{advice_text}"
        
        buttons = [
            YandexButton(title="Новый совет", payload={"action": "new_advice"}),
            YandexButton(title="Гороскоп", payload={"action": "horoscope"}),
            YandexButton(title="Главное меню", payload={"action": "main_menu"})
        ]
        
        return YandexResponse(
            text=text,
            tts=self._add_tts_pauses(text),
            buttons=buttons,
            end_session=False
        )

    def format_help_response(self) -> YandexResponse:
        """Форматирует справочную информацию."""
        text = """Я умею:

🌟 Составлять персональные гороскопы на день, неделю или месяц
💑 Проверять совместимость знаков зодиака  
🔮 Давать астрологические советы
🌙 Рассказывать о влиянии лунных фаз

Просто скажите, что вас интересует, или выберите действие из меню."""
        
        return YandexResponse(
            text=text,
            tts=self._add_tts_pauses(text),
            buttons=self.help_buttons,
            end_session=False
        )

    def format_error_response(
        self, 
        error_type: str = "general"
    ) -> YandexResponse:
        """Форматирует ответ об ошибке."""
        error_messages = {
            "general": "Извините, произошла ошибка. Попробуйте еще раз.",
            "invalid_date": "Не удалось распознать дату. Попробуйте сказать в формате: день, месяц, год.",
            "invalid_sign": "Не удалось распознать знак зодиака. Выберите из предложенных вариантов.",
            "no_data": "Недостаточно данных для ответа. Попробуйте уточнить запрос."
        }
        
        text = error_messages.get(error_type, error_messages["general"])
        
        return YandexResponse(
            text=text,
            tts=text,
            buttons=self.help_buttons,
            end_session=False
        )

    def format_goodbye_response(self) -> YandexResponse:
        """Форматирует прощальное сообщение."""
        text = "До свидания! Пусть звёзды ведут вас к счастью!"
        
        return YandexResponse(
            text=text,
            tts=text,
            end_session=True
        )

    def _get_zodiac_buttons(self) -> List[YandexButton]:
        """Возвращает кнопки со знаками зодиака."""
        return [
            YandexButton(title="Овен", payload={"sign": "овен"}),
            YandexButton(title="Телец", payload={"sign": "телец"}),
            YandexButton(title="Близнецы", payload={"sign": "близнецы"}),
            YandexButton(title="Рак", payload={"sign": "рак"}),
            YandexButton(title="Лев", payload={"sign": "лев"}),
            YandexButton(title="Дева", payload={"sign": "дева"}),
        ]

    def _add_tts_pauses(self, text: str) -> str:
        """Добавляет паузы в TTS."""
        # Добавляем небольшие паузы после знаков препинания
        tts = text.replace(".", ". <pause=300ms>")
        tts = tts.replace("!", "! <pause=300ms>")
        tts = tts.replace("?", "? <pause=300ms>")
        tts = tts.replace(":", ": <pause=200ms>")
        tts = tts.replace(";", "; <pause=200ms>")
        return tts

    def _generate_horoscope_text(
        self, 
        zodiac_sign: YandexZodiacSign,
        period: str
    ) -> str:
        """Генерирует текст гороскопа (заглушка)."""
        horoscopes = {
            YandexZodiacSign.ARIES: "Сегодня у вас отличный день для новых начинаний. Энергия Марса даёт вам силы для достижения целей.",
            YandexZodiacSign.TAURUS: "Венера благоволит вам в вопросах красоты и гармонии. Отличное время для творчества.",
            YandexZodiacSign.GEMINI: "Меркурий активизирует ваше общение. Сегодня могут прийти важные новости.",
            # Добавим остальные знаки по мере развития
        }
        
        return horoscopes.get(
            zodiac_sign, 
            "Звёзды советуют вам быть внимательным к деталям и слушать свою интуицию."
        )

    def _generate_compatibility_text(
        self, 
        sign1: YandexZodiacSign,
        sign2: YandexZodiacSign
    ) -> str:
        """Генерирует текст о совместимости (заглушка)."""
        # Простая логика совместимости по стихиям
        fire_signs = [YandexZodiacSign.ARIES, YandexZodiacSign.LEO, YandexZodiacSign.SAGITTARIUS]
        earth_signs = [YandexZodiacSign.TAURUS, YandexZodiacSign.VIRGO, YandexZodiacSign.CAPRICORN]
        air_signs = [YandexZodiacSign.GEMINI, YandexZodiacSign.LIBRA, YandexZodiacSign.AQUARIUS]
        water_signs = [YandexZodiacSign.CANCER, YandexZodiacSign.SCORPIO, YandexZodiacSign.PISCES]
        
        def get_element(sign):
            if sign in fire_signs:
                return "fire"
            elif sign in earth_signs:
                return "earth"
            elif sign in air_signs:
                return "air"
            else:
                return "water"
        
        element1 = get_element(sign1)
        element2 = get_element(sign2)
        
        if element1 == element2:
            return "Отличная совместимость! Вы понимаете друг друга с полуслова."
        elif (element1 in ["fire", "air"] and element2 in ["fire", "air"]) or \
             (element1 in ["earth", "water"] and element2 in ["earth", "water"]):
            return "Хорошая совместимость. У вас много общего, но есть и интересные различия."
        else:
            return "Противоположности притягиваются! Ваши различия делают отношения яркими и насыщенными."

    def _generate_advice_text(self) -> str:
        """Генерирует астрологический совет (заглушка)."""
        advices = [
            "Сегодня звёзды советуют прислушаться к своей интуиции и не бояться принимать важные решения.",
            "Луна в благоприятной фазе для новых знакомств и укрепления дружеских связей.",
            "Планеты советуют уделить время саморазвитию и изучению чего-то нового.",
            "Отличный день для творчества и воплощения в жизнь ваших идей.",
        ]
        
        import random
        return random.choice(advices)