#!/usr/bin/env python3
"""Debug script to check goodbye response."""

from app.services.response_formatter import ResponseFormatter

def test_goodbye():
    formatter = ResponseFormatter()
    response = formatter.format_goodbye_response()
    
    print(f"Response text: '{response.text}'")
    print(f"Lowercase: '{response.text.lower()}'")
    print(f"End session: {response.end_session}")
    
    words = ["до свидания", "пока", "увидимся"]
    for word in words:
        if word in response.text.lower():
            print(f"Found word: '{word}'")

if __name__ == "__main__":
    test_goodbye()