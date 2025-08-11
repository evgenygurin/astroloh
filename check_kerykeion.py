#!/usr/bin/env python3
"""
Скрипт для проверки установки и работы Kerykeion
"""

import sys
import traceback

def check_kerykeion():
    """Проверяет установку и работу Kerykeion"""
    print("🔍 Проверка Kerykeion...")
    
    # Проверка импорта
    try:
        import kerykeion
        print("✅ Kerykeion успешно импортирован")
        print(f"   Версия: {kerykeion.__version__}")
    except ImportError as e:
        print(f"❌ Ошибка импорта Kerykeion: {e}")
        return False
    
    # Проверка Swiss Ephemeris
    try:
        import swisseph as swe
        print("✅ Swiss Ephemeris успешно импортирован")
    except ImportError as e:
        print(f"❌ Ошибка импорта Swiss Ephemeris: {e}")
        return False
    
    # Проверка создания объекта
    try:
        from kerykeion import AstrologicalSubject
        subject = AstrologicalSubject("Test", 1990, 1, 1, 12, 0, "Moscow", 55.7558, 37.6176)
        print("✅ Создание AstrologicalSubject успешно")
    except Exception as e:
        print(f"❌ Ошибка создания AstrologicalSubject: {e}")
        return False
    
    # Проверка расчетов
    try:
        positions = subject.get_planets()
        print(f"✅ Расчеты выполнены успешно, получено {len(positions)} планет")
    except Exception as e:
        print(f"❌ Ошибка расчетов: {e}")
        return False
    
    print("🎉 Kerykeion работает корректно!")
    return True

def check_astrology_calculator():
    """Проверяет AstrologyCalculator с Kerykeion"""
    print("\n🔍 Проверка AstrologyCalculator...")
    
    try:
        from app.services.astrology_calculator import AstrologyCalculator
        calc = AstrologyCalculator()
        
        # Проверяем доступные бэкенды
        backends = calc._get_available_backends()
        print(f"✅ Доступные бэкенды: {backends}")
        
        if 'kerykeion' in backends:
            print("✅ Kerykeion доступен как бэкенд")
            return True
        else:
            print("⚠️ Kerykeion не найден в доступных бэкендах")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при проверке AstrologyCalculator: {e}")
        traceback.print_exc()
        return False

def main():
    """Основная функция"""
    print("🚀 Проверка установки Kerykeion в Astroloh")
    print("=" * 50)
    
    success = True
    
    # Проверка Kerykeion
    if not check_kerykeion():
        success = False
    
    # Проверка AstrologyCalculator
    if not check_astrology_calculator():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Все проверки пройдены! Kerykeion готов к работе.")
        return 0
    else:
        print("💥 Некоторые проверки не пройдены.")
        return 1

if __name__ == "__main__":
    sys.exit(main())