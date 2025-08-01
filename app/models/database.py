"""
Database models and configuration for secure data storage.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, DateTime, Text, Boolean, Integer, 
    Float, ForeignKey, LargeBinary, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

Base = declarative_base()


class User(Base):
    """
    Модель пользователя с зашифрованными персональными данными.
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    yandex_user_id = Column(String(255), unique=True, index=True, nullable=False)
    
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
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    horoscope_requests = relationship("HoroscopeRequest", back_populates="user", cascade="all, delete-orphan")


class UserSession(Base):
    """
    Модель сессии пользователя для управления состоянием диалога.
    """
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    
    # Состояние диалога
    current_state = Column(String(50), default="initial", nullable=False)
    context_data = Column(Text, nullable=True)  # JSON string with session context
    
    # Безопасность сессии
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="sessions")


class HoroscopeRequest(Base):
    """
    Модель запроса гороскопа с зашифрованными данными.
    """
    __tablename__ = "horoscope_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Тип запроса
    request_type = Column(String(50), nullable=False)  # daily, weekly, monthly, natal, compatibility
    
    # Зашифрованные параметры запроса
    encrypted_target_date = Column(LargeBinary, nullable=True)
    encrypted_partner_data = Column(LargeBinary, nullable=True)  # For compatibility requests
    
    # Метаданные запроса
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_hash = Column(String(64), nullable=True)  # Хеш IP для аналитики
    
    user = relationship("User", back_populates="horoscope_requests")


class DataDeletionRequest(Base):
    """
    Модель запроса на удаление данных (GDPR compliance).
    """
    __tablename__ = "data_deletion_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Статус запроса
    status = Column(String(20), default="pending", nullable=False)  # pending, processing, completed, failed
    
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
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Основная информация
    event_type = Column(String(50), nullable=False)  # login, data_access, encryption, decryption, deletion
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
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
    __table_args__ = (
        UniqueConstraint('id'),
    )


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
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_size=20,
            max_overflow=0,
            pool_pre_ping=True,
            pool_recycle=300,
        )
        
        self.async_session = sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
    async def create_tables(self):
        """Создание таблиц в базе данных."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
    async def get_session(self) -> AsyncSession:
        """Получение сессии базы данных."""
        async with self.async_session() as session:
            yield session
            
    async def close(self):
        """Закрытие подключений к базе данных."""
        if self.engine:
            await self.engine.dispose()