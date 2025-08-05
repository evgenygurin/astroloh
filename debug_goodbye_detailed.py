#!/usr/bin/env python3
"""Detailed debug script to check goodbye response test logic."""

from app.services.response_formatter import ResponseFormatter

def test_goodbye_detailed():
    formatter = ResponseFormatter()
    response = formatter.format_goodbye_response()
    
    print(f"Response text: '{response.text}'")
    print(f"Response end_session: {response.end_session}")
    print(f"Lowercase text: '{response.text.lower()}'")
    
    words = ["до свидания", "пока", "увидимся"]
    print(f"Looking for words: {words}")
    
    # Mimic the exact test logic
    generator = (word in response.text.lower() for word in words)
    generator_list = list(generator)
    print(f"Generator results: {generator_list}")
    
    any_result = any(word in response.text.lower() for word in words)
    print(f"any() result: {any_result}")
    
    # Check each word individually
    for word in words:
        found = word in response.text.lower()
        print(f"'{word}' in text: {found}")
    
    # Check character by character
    text_lower = response.text.lower()
    search_word = "до свидания"
    print(f"Text characters: {[ord(c) for c in text_lower[:20]]}")
    print(f"Search word characters: {[ord(c) for c in search_word]}")

if __name__ == "__main__":
    test_goodbye_detailed()