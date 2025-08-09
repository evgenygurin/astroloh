"""
Пример использования улучшенного диалога согласно лучшим практикам Яндекс.Диалогов

Демонстрирует как использовать новые методы вариативности в ResponseFormatter
"""

from app.services.response_formatter import ResponseFormatter

def example_usage():
    formatter = ResponseFormatter()
    
    # Пример 1: Использование вариативности в подтверждениях
    print("=== ВАРИАТИВНОСТЬ ПОДТВЕРЖДЕНИЙ ===")
    for i in range(3):
        confirmation = formatter.get_random_confirmation()
        print(f"Вариант {i+1}: {confirmation} Ваш знак зодиака - Лев.")
    
    # Пример 2: Использование переходов между темами
    print("\n=== ПЕРЕХОДЫ МЕЖДУ ТЕМАМИ ===")
    for i in range(3):
        transition = formatter.get_random_transition()
        print(f"Вариант {i+1}: {transition} проверить совместимость с другим знаком?")
    
    # Пример 3: Мягкие ошибки
    print("\n=== МЯГКИЕ ОШИБКИ ===")
    for i in range(3):
        gentle_error = formatter.get_random_gentle_error()
        print(f"Вариант {i+1}: {gentle_error} Попробуйте еще раз.")

    # Пример 4: Улучшенное приветствие
    print("\n=== УЛУЧШЕННОЕ ПРИВЕТСТВИЕ ===")
    welcome_response = formatter.format_welcome_response(is_returning_user=False)
    print(f"Новое приветствие: {welcome_response.text}")
    
    # Пример 5: Улучшенная помощь
    print("\n=== УЛУЧШЕННАЯ ПОМОЩЬ ===")
    help_response = formatter.format_help_response()
    print(f"Новая помощь:\n{help_response.text}")

if __name__ == "__main__":
    example_usage()