#!/usr/bin/env python3
"""
Скрипт для тестирования Kerykeion в Docker окружении
"""

import sys
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_kerykeion_import():
    """Тестирует импорт Kerykeion"""
    try:
        from kerykeion import AstrologicalSubject
        logger.info("✅ Kerykeion успешно импортирован")
        return True
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта Kerykeion: {e}")
        return False

def test_swisseph_import():
    """Тестирует импорт Swiss Ephemeris"""
    try:
        import swisseph as swe
        logger.info("✅ Swiss Ephemeris успешно импортирован")
        return True
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта Swiss Ephemeris: {e}")
        return False

def test_astrology_calculator():
    """Тестирует AstrologyCalculator с Kerykeion"""
    try:
        from app.services.astrology_calculator import AstrologyCalculator
        calc = AstrologyCalculator()
        
        # Проверяем доступные бэкенды
        backends = calc._get_available_backends()
        logger.info(f"✅ Доступные бэкенды: {backends}")
        
        # Проверяем, что kerykeion доступен
        if 'kerykeion' in backends:
            logger.info("✅ Kerykeion доступен как бэкенд")
            return True
        else:
            logger.warning("⚠️ Kerykeion не найден в доступных бэкендах")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании AstrologyCalculator: {e}")
        return False

def test_kerykeion_calculation():
    """Тестирует расчеты с помощью Kerykeion"""
    try:
        from app.services.astrology_calculator import AstrologyCalculator
        calc = AstrologyCalculator()
        
        # Тестовые данные
        test_date = datetime(1990, 1, 1, 12, 0, 0)
        latitude = 55.7558
        longitude = 37.6176
        
        # Пытаемся использовать kerykeion для расчетов
        positions = calc.calculate_planet_positions(
            birth_datetime=test_date,
            latitude=latitude,
            longitude=longitude
        )
        
        logger.info("✅ Расчеты с Kerykeion выполнены успешно")
        logger.info(f"Получено позиций планет: {len(positions)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при расчетах с Kerykeion: {e}")
        return False

def main():
    """Основная функция тестирования"""
    logger.info("🚀 Начинаем тестирование Kerykeion в Docker")
    
    tests = [
        ("Импорт Kerykeion", test_kerykeion_import),
        ("Импорт Swiss Ephemeris", test_swisseph_import),
        ("AstrologyCalculator", test_astrology_calculator),
        ("Расчеты с Kerykeion", test_kerykeion_calculation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Тест: {test_name}")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} - ПРОЙДЕН")
            else:
                logger.error(f"❌ {test_name} - ПРОВАЛЕН")
        except Exception as e:
            logger.error(f"❌ {test_name} - ОШИБКА: {e}")
    
    logger.info(f"\n📊 Результаты тестирования: {passed}/{total} тестов пройдено")
    
    if passed == total:
        logger.info("🎉 Все тесты пройдены! Kerykeion работает корректно в Docker")
        return 0
    else:
        logger.error("💥 Некоторые тесты не пройдены")
        return 1

if __name__ == "__main__":
    sys.exit(main())
