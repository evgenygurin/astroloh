"""
Database models and configuration for secure data storage.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, CHAR

Base = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    
    Uses PostgreSQL's UUID type when available, otherwise uses
    CHAR(36) storing as stringified hex values.
    """
    
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQL_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            else:
                return value


class User(Base):
    """
    Модель пользователя с зашифрованными персональными данными.
    """

    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    yandex_user_id = Column(
        String(255), unique=True, index=True, nullable=False
    )

    # Зашифрованные персональные данные
    encrypted_birth_date = Column(LargeBinary, nullable=True)
    encrypted_birth_time = Column(LargeBinary, nullable=True)
    encrypted_birth_location = Column(LargeBinary, nullable=True)
    encrypted_name = Column(LargeBinary, nullable=True)

    # Незашифрованные данные (знак зодиака можно хранить открыто)
    zodiac_sign = Column(String(20), nullable=True)
    gender = Column(String(10), nullable=True)

    # Настройки приватности
    data_consent = Column(Boolean, default=False, nullable=False)
    data_retention_days = Column(Integer, default=365, nullable=False)
    
    # Пользовательские настройки и предпочтения (JSON)
    preferences = Column(JSON, nullable=True)

    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_accessed = Column(DateTime, default=datetime.utcnow)

    # Связи
    sessions = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )
    horoscope_requests = relationship(
        "HoroscopeRequest", back_populates="user", cascade="all, delete-orphan"
    )
    user_interactions = relationship(
        "UserInteraction", back_populates="user", cascade="all, delete-orphan"
    )
    user_recommendations = relationship(
        "Recommendation", back_populates="user", cascade="all, delete-orphan"
    )
    user_preferences = relationship(
        "UserPreference", back_populates="user", cascade="all, delete-orphan"
    )
    user_clusters = relationship(
        "UserCluster", back_populates="user", cascade="all, delete-orphan"
    )
    user_ab_tests = relationship(
        "ABTestGroup", back_populates="user", cascade="all, delete-orphan"
    )


class UserSession(Base):
    """
    Модель сессии пользователя для управления состоянием диалога.
    """

    __tablename__ = "user_sessions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    session_id = Column(String(255), unique=True, index=True, nullable=False)

    # Состояние диалога
    current_state = Column(String(50), default="initial", nullable=False)
    context_data = Column(
        Text, nullable=True
    )  # JSON string with session context

    # Безопасность сессии
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = relationship("User", back_populates="sessions")


class HoroscopeRequest(Base):
    """
    Модель запроса гороскопа с зашифрованными данными.
    """

    __tablename__ = "horoscope_requests"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID(), ForeignKey("users.id"), nullable=False
    )

    # Тип запроса
    request_type = Column(
        String(50), nullable=False
    )  # daily, weekly, monthly, natal, compatibility

    # Зашифрованные параметры запроса
    encrypted_target_date = Column(LargeBinary, nullable=True)
    encrypted_partner_data = Column(
        LargeBinary, nullable=True
    )  # For compatibility requests

    # Метаданные запроса
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_hash = Column(String(64), nullable=True)  # Хеш IP для аналитики

    user = relationship("User", back_populates="horoscope_requests")


class DataDeletionRequest(Base):
    """
    Модель запроса на удаление данных (GDPR compliance).
    """

    __tablename__ = "data_deletion_requests"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID(), ForeignKey("users.id"), nullable=False
    )

    # Статус запроса
    status = Column(
        String(20), default="pending", nullable=False
    )  # pending, processing, completed, failed

    # Детали запроса
    request_reason = Column(Text, nullable=True)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    # Подтверждение
    verification_code = Column(String(32), nullable=False)
    verified = Column(Boolean, default=False, nullable=False)


class SecurityLog(Base):
    """
    Лог безопасности для аудита и мониторинга.
    """

    __tablename__ = "security_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Основная информация
    event_type = Column(
        String(50), nullable=False
    )  # login, data_access, encryption, decryption, deletion
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    session_id = Column(String(255), nullable=True)

    # Детали события
    description = Column(Text, nullable=False)
    ip_hash = Column(String(64), nullable=True)
    user_agent_hash = Column(String(64), nullable=True)

    # Результат операции
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)

    # Временная метка
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Индексы для быстрого поиска
    __table_args__ = (UniqueConstraint("id"),)


class UserPreference(Base):
    """
    Пользовательские предпочтения для системы рекомендаций.
    """

    __tablename__ = "user_preferences"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)

    # Категории интересов
    interests = Column(JSON, nullable=True)  # {"career": 0.8, "love": 0.9, "health": 0.6}
    
    # Предпочтения контента
    communication_style = Column(String(20), default="balanced")  # formal, casual, friendly, mystical
    complexity_level = Column(String(20), default="intermediate")  # beginner, intermediate, advanced
    
    # Временные предпочтения
    preferred_time_slots = Column(JSON, nullable=True)  # [{"start": "09:00", "end": "12:00"}]
    timezone = Column(String(50), nullable=True)
    
    # Культурные настройки
    cultural_context = Column(String(20), nullable=True)  # western, vedic, chinese
    language_preference = Column(String(10), default="ru")
    
    # Персонализация контента
    content_length_preference = Column(String(20), default="medium")  # short, medium, long
    detail_level = Column(String(20), default="standard")  # brief, standard, detailed
    
    # Изученные предпочтения (машинное обучение)
    preferences = Column(JSON, nullable=True)  # Хранит изученные предпочтения из ML
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    user = relationship("User", back_populates="user_preferences")


class UserInteraction(Base):
    """
    История взаимодействий пользователя для обучения модели.
    """

    __tablename__ = "user_interactions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)

    # Тип взаимодействия
    interaction_type = Column(String(50), nullable=False)  # view, like, dislike, save, share
    content_type = Column(String(50), nullable=False)  # horoscope, compatibility, lunar
    content_id = Column(String(255), nullable=True)
    
    # Контекст взаимодействия
    session_duration = Column(Integer, nullable=True)  # секунды
    rating = Column(Integer, nullable=True)  # 1-5
    feedback_text = Column(Text, nullable=True)
    
    # Астрологические данные на момент взаимодействия
    astronomical_data = Column(JSON, nullable=True)  # позиции планет, транзиты
    
    # Временная метка
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Связи
    user = relationship("User", back_populates="user_interactions")


class Recommendation(Base):
    """
    Рекомендации для пользователей.
    """

    __tablename__ = "recommendations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)

    # Тип рекомендации
    recommendation_type = Column(String(50), nullable=False)  # content, action, timing
    content_type = Column(String(50), nullable=False)  # daily, weekly, compatibility
    
    # Содержание рекомендации
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    recommendation_data = Column(JSON, nullable=True)
    
    # Скоринг
    confidence_score = Column(Integer, nullable=False)  # 0-100
    priority = Column(Integer, default=1)  # 1-5
    
    # Алгоритм и модель
    algorithm_used = Column(String(50), nullable=False)  # collaborative, content_based, hybrid
    model_version = Column(String(20), nullable=False)
    
    # Статус
    status = Column(String(20), default="active")  # active, shown, dismissed, expired
    expires_at = Column(DateTime, nullable=True)
    shown_at = Column(DateTime, nullable=True)
    
    # Временная метка
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Связи
    user = relationship("User", back_populates="user_recommendations")


class UserCluster(Base):
    """
    Кластеры пользователей для коллаборативной фильтрации.
    """

    __tablename__ = "user_clusters"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)

    # Кластер
    cluster_id = Column(String(50), nullable=False)
    cluster_name = Column(String(100), nullable=True)
    
    # Характеристики кластера
    cluster_features = Column(JSON, nullable=True)  # астрологические признаки
    similarity_score = Column(Integer, nullable=False)  # 0-100
    
    # Метаданные
    algorithm_version = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    user = relationship("User", back_populates="user_clusters")


class ABTestGroup(Base):
    """
    A/B тестирование для рекомендательной системы.
    """

    __tablename__ = "ab_test_groups"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)

    # Тест
    test_name = Column(String(100), nullable=False)
    group_name = Column(String(50), nullable=False)  # control, variant_a, variant_b
    
    # Параметры теста
    test_parameters = Column(JSON, nullable=True)
    test_start_date = Column(DateTime, nullable=False)
    test_end_date = Column(DateTime, nullable=True)
    
    # Статус
    is_active = Column(Boolean, default=True)
    
    # Временная метка
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Связи
    user = relationship("User", back_populates="user_ab_tests")


class RecommendationMetrics(Base):
    """
    Метрики эффективности рекомендательной системы.
    """

    __tablename__ = "recommendation_metrics"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    recommendation_id = Column(GUID(), ForeignKey("recommendations.id"), nullable=True)

    # Метрики
    metric_name = Column(String(50), nullable=False)  # ctr, conversion, satisfaction
    metric_value = Column(Integer, nullable=False)
    
    # Контекст
    context_data = Column(JSON, nullable=True)
    session_id = Column(String(255), nullable=True)
    
    # Временная метка
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Связи
    user = relationship("User")
    recommendation = relationship("Recommendation")


# Database connection management
class DatabaseManager:
    """
    Менеджер подключений к базе данных.
    """

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.async_session = None

    async def initialize(self):
        """Инициализация подключения к базе данных."""
        # Configure engine parameters based on database type
        engine_kwargs = {
            "echo": False,
        }

        # Add pool settings only for PostgreSQL
        if not self.database_url.startswith("sqlite"):
            engine_kwargs.update(
                {
                    "pool_size": 20,
                    "max_overflow": 0,
                    "pool_pre_ping": True,
                    "pool_recycle": 300,
                }
            )

        self.engine = create_async_engine(self.database_url, **engine_kwargs)

        self.async_session = async_sessionmaker(
            self.engine, expire_on_commit=False
        )

    async def create_tables(self):
        """Создание таблиц в базе данных."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self):
        """Получение сессии базы данных."""
        async with self.async_session() as session:
            yield session

    async def close(self):
        """Закрытие подключений к базе данных."""
        if self.engine:
            await self.engine.dispose()
