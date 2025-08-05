#!/usr/bin/env python3
"""Debug script to check intent recognition."""

from app.services.intent_recognition import IntentRecognizer
from app.models.yandex_models import UserContext

def test_intent_recognition():
    recognizer = IntentRecognizer()
    user_context = UserContext(user_id="test_user", birth_date=None)
    
    # Test the horoscope input
    result = recognizer.recognize_intent("мой гороскоп", user_context)
    print(f"Input: 'мой гороскоп'")
    print(f"Intent: {result.intent}")
    print(f"Confidence: {result.confidence}")
    print()
    
    # Test the help input
    result2 = recognizer.recognize_intent("помощь", user_context)
    print(f"Input: 'помощь'")
    print(f"Intent: {result2.intent}")
    print(f"Confidence: {result2.confidence}")

if __name__ == "__main__":
    test_intent_recognition()