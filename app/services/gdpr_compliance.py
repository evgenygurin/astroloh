"""
GDPR compliance service for data protection and privacy management.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import DataDeletionRequest, HoroscopeRequest, SecurityLog, User
from app.services.encryption import SecurityUtils, data_protection
from app.services.user_manager import UserManager


class GDPRComplianceService:
    """
    Сервис соответствия GDPR для защиты персональных данных и управления приватностью.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.user_manager = UserManager(db_session)
        self.data_protection = data_protection

    async def get_user_data_summary(
        self, user_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Получение сводки о данных пользователя (право на доступ к данным).

        Args:
            user_id: ID пользователя

        Returns:
            Сводка данных пользователя
        """
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                return None

            # Получаем расшифрованные персональные данные
            birth_data = await self.user_manager.get_user_birth_data(user_id)

            # Подсчитываем количество запросов гороскопов
            horoscope_count_result = await self.db.execute(
                select(func.count(HoroscopeRequest.id)).where(
                    HoroscopeRequest.user_id == user_id
                )
            )
            horoscope_count = horoscope_count_result.scalar()

            # Последняя активность
            last_request_result = await self.db.execute(
                select(HoroscopeRequest.processed_at)
                .where(HoroscopeRequest.user_id == user_id)
                .order_by(HoroscopeRequest.processed_at.desc())
                .limit(1)
            )
            last_activity = last_request_result.scalar_one_or_none()

            summary = {
                "user_id": str(user_id),
                "yandex_user_id": user.yandex_user_id,
                "registration_date": user.created_at.isoformat(),
                "last_access": user.last_accessed.isoformat(),
                "data_consent": user.data_consent,
                "data_retention_days": user.data_retention_days,
                "personal_data": {
                    "has_birth_date": bool(
                        birth_data and birth_data.get("birth_date")
                    ),
                    "has_birth_time": bool(
                        birth_data and birth_data.get("birth_time")
                    ),
                    "has_birth_location": bool(
                        birth_data and birth_data.get("birth_location")
                    ),
                    "zodiac_sign": user.zodiac_sign,
                    "gender": user.gender,
                    "has_name": bool(user.encrypted_name),
                },
                "activity_statistics": {
                    "total_horoscope_requests": horoscope_count,
                    "last_activity": last_activity.isoformat()
                    if last_activity
                    else None,
                },
                "data_processing_purpose": [
                    "Персональные астрологические консультации",
                    "Расчет гороскопов и натальных карт",
                    "Анализ совместимости знаков зодиака",
                    "Лунный календарь и рекомендации",
                ],
                "legal_basis": "Согласие пользователя (GDPR Art. 6(1)(a))",
                "retention_policy": f"Данные хранятся {user.data_retention_days} дней с момента регистрации",
            }

            # Если есть полные данные, добавляем их (только для самого пользователя)
            if birth_data:
                summary["detailed_data"] = birth_data

            return summary

        except Exception as e:
            await self._log_compliance_event(
                event_type="data_access_request",
                user_id=user_id,
                description="Failed to generate user data summary",
                success=False,
                error_message=str(e),
            )
            return None

    async def export_user_data(
        self, user_id: uuid.UUID, format_type: str = "json"
    ) -> Optional[Dict[str, Any]]:
        """
        Экспорт всех данных пользователя (право на портабельность данных).

        Args:
            user_id: ID пользователя
            format_type: Формат экспорта (json, csv)

        Returns:
            Экспортированные данные
        """
        summary = await self.get_user_data_summary(user_id)
        if not summary:
            return None

        # Получаем историю запросов
        horoscope_history = await self._get_horoscope_history(user_id)

        export_data = {
            "export_metadata": {
                "export_date": datetime.utcnow().isoformat(),
                "format": format_type,
                "gdpr_article": "Article 20 - Right to data portability",
            },
            "user_profile": summary,
            "horoscope_history": horoscope_history,
            "legal_notice": {
                "data_controller": "Astroloh Skill Service",
                "privacy_policy": "Данные обрабатываются в соответствии с GDPR",
                "contact": "При вопросах обращайтесь к администратору навыка",
            },
        }

        await self._log_compliance_event(
            event_type="data_export",
            user_id=user_id,
            description=f"User data exported in {format_type} format",
            success=True,
        )

        return export_data

    async def request_data_deletion(
        self, user_id: uuid.UUID, reason: str = None
    ) -> str:
        """
        Запрос на удаление данных (право на забвение).

        Args:
            user_id: ID пользователя
            reason: Причина удаления

        Returns:
            Код верификации для подтверждения
        """
        verification_code = await self.user_manager.request_data_deletion(
            user_id, reason
        )

        await self._log_compliance_event(
            event_type="deletion_request",
            user_id=user_id,
            description="Data deletion requested under GDPR Article 17",
            success=True,
        )

        return verification_code

    async def confirm_data_deletion(
        self, user_id: uuid.UUID, verification_code: str
    ) -> bool:
        """
        Подтверждение удаления данных.

        Args:
            user_id: ID пользователя
            verification_code: Код верификации

        Returns:
            True если удаление выполнено
        """
        success = await self.user_manager.confirm_data_deletion(
            user_id, verification_code
        )

        if success:
            await self._log_compliance_event(
                event_type="data_deletion_confirmed",
                user_id=user_id,
                description="User data successfully deleted under GDPR Article 17",
                success=True,
            )

        return success

    async def update_consent(
        self,
        user_id: uuid.UUID,
        consent: bool,
        retention_days: int = 365,
        consent_details: Dict[str, bool] = None,
    ) -> bool:
        """
        Обновление согласия на обработку данных.

        Args:
            user_id: ID пользователя
            consent: Общее согласие
            retention_days: Срок хранения данных
            consent_details: Детальные согласия

        Returns:
            True если обновление успешно
        """
        success = await self.user_manager.set_data_consent(
            user_id, consent, retention_days
        )

        if success:
            consent_summary = {
                "general_consent": consent,
                "retention_days": retention_days,
                "consent_details": consent_details or {},
            }

            await self._log_compliance_event(
                event_type="consent_update",
                user_id=user_id,
                description=f"Consent updated: {consent_summary}",
                success=True,
            )

        return success

    async def rectify_user_data(
        self, user_id: uuid.UUID, correction_data: Dict[str, Any]
    ) -> bool:
        """
        Исправление данных пользователя (право на исправление).

        Args:
            user_id: ID пользователя
            correction_data: Данные для исправления

        Returns:
            True если исправление выполнено
        """
        try:
            updates = {}

            # Обработка персональных данных
            if (
                "birth_date" in correction_data
                or "birth_time" in correction_data
                or "birth_location" in correction_data
            ):
                success = await self.user_manager.update_user_birth_data(
                    user_id,
                    correction_data.get("birth_date", ""),
                    correction_data.get("birth_time"),
                    correction_data.get("birth_location"),
                    correction_data.get("zodiac_sign"),
                )
                if not success:
                    return False

            # Обработка других данных
            if "gender" in correction_data:
                updates["gender"] = SecurityUtils.sanitize_input(
                    correction_data["gender"], 10
                )

            if updates:
                await self.db.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(**updates, updated_at=datetime.utcnow())
                )
                await self.db.commit()

            await self._log_compliance_event(
                event_type="data_rectification",
                user_id=user_id,
                description=f"User data rectified: {list(correction_data.keys())}",
                success=True,
            )

            return True

        except Exception as e:
            await self._log_compliance_event(
                event_type="data_rectification",
                user_id=user_id,
                description="Failed to rectify user data",
                success=False,
                error_message=str(e),
            )
            return False

    async def restrict_processing(
        self, user_id: uuid.UUID, restrict: bool, reason: str = None
    ) -> bool:
        """
        Ограничение обработки данных (право на ограничение обработки).

        Args:
            user_id: ID пользователя
            restrict: True для ограничения, False для снятия ограничений
            reason: Причина ограничения

        Returns:
            True если операция успешна
        """
        try:
            # В нашем случае ограничение обработки означает отзыв согласия
            # но сохранение данных для возможного восстановления
            success = await self.user_manager.set_data_consent(
                user_id,
                not restrict,  # Инвертируем значение
                365,  # Стандартный срок хранения
            )

            if success:
                await self._log_compliance_event(
                    event_type="processing_restriction",
                    user_id=user_id,
                    description=f"Processing {'restricted' if restrict else 'unrestricted'}: {reason}",
                    success=True,
                )

            return success

        except Exception as e:
            await self._log_compliance_event(
                event_type="processing_restriction",
                user_id=user_id,
                description="Failed to update processing restriction",
                success=False,
                error_message=str(e),
            )
            return False

    async def generate_compliance_report(
        self, start_date: datetime = None, end_date: datetime = None
    ) -> Dict[str, Any]:
        """
        Генерация отчета о соответствии GDPR.

        Args:
            start_date: Начало периода
            end_date: Конец периода

        Returns:
            Отчет о соответствии
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # Статистика пользователей
        total_users_result = await self.db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar()

        consented_users_result = await self.db.execute(
            select(func.count(User.id)).where(User.data_consent)
        )
        consented_users = consented_users_result.scalar()

        # Статистика запросов на удаление
        deletion_requests_result = await self.db.execute(
            select(func.count(DataDeletionRequest.id)).where(
                DataDeletionRequest.requested_at.between(start_date, end_date)
            )
        )
        deletion_requests = deletion_requests_result.scalar()

        # События безопасности
        security_events_result = await self.db.execute(
            select(SecurityLog.event_type, func.count(SecurityLog.id))
            .where(SecurityLog.timestamp.between(start_date, end_date))
            .group_by(SecurityLog.event_type)
        )
        security_events_rows = security_events_result.all()
        security_events = {row[0]: row[1] for row in security_events_rows}

        report = {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "user_statistics": {
                "total_users": total_users,
                "users_with_consent": consented_users,
                "consent_rate": (consented_users / total_users * 100)
                if total_users > 0
                else 0,
            },
            "gdpr_requests": {"deletion_requests": deletion_requests},
            "security_events": security_events,
            "compliance_measures": {
                "data_encryption": "AES-256 шифрование для персональных данных",
                "access_logging": "Полное логирование доступа к данным",
                "retention_policy": "Автоматическое удаление после истечения срока хранения",
                "consent_management": "Явное согласие с возможностью отзыва",
                "data_minimization": "Сбор только необходимых данных",
                "pseudonymization": "Хеширование IP и User-Agent",
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

        return report

    async def _get_horoscope_history(
        self, user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Получение истории запросов гороскопов."""
        result = await self.db.execute(
            select(HoroscopeRequest)
            .where(HoroscopeRequest.user_id == user_id)
            .order_by(HoroscopeRequest.processed_at.desc())
            .limit(100)  # Ограничиваем количество записей
        )
        requests = result.scalars().all()

        history = []
        for req in requests:
            history.append(
                {
                    "request_type": req.request_type,
                    "processed_at": req.processed_at.isoformat(),
                    "has_target_date": bool(req.encrypted_target_date),
                    "has_partner_data": bool(req.encrypted_partner_data),
                }
            )

        return history

    async def _log_compliance_event(
        self,
        event_type: str,
        description: str,
        success: bool,
        user_id: uuid.UUID = None,
        error_message: str = None,
    ):
        """Логирование события соответствия GDPR."""
        log_entry = SecurityLog(
            event_type=f"gdpr_{event_type}",
            user_id=user_id,
            description=description,
            success=success,
            error_message=error_message,
            timestamp=datetime.utcnow(),
        )

        self.db.add(log_entry)
        # Не коммитим, чтобы не нарушить основные транзакции


class DataMinimizationService:
    """
    Сервис минимизации данных для соблюдения принципов GDPR.
    """

    @staticmethod
    def extract_essential_birth_data(
        full_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Извлечение только необходимых данных о рождении.

        Args:
            full_data: Полные данные

        Returns:
            Минимизированные данные
        """
        essential_fields = ["birth_date", "birth_time", "birth_location"]
        return {
            k: v for k, v in full_data.items() if k in essential_fields and v
        }

    @staticmethod
    def anonymize_analytics_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анонимизация данных для аналитики.

        Args:
            data: Исходные данные

        Returns:
            Анонимизированные данные
        """
        anonymized = data.copy()

        # Удаляем персональные идентификаторы
        anonymized.pop("user_id", None)
        anonymized.pop("yandex_user_id", None)
        anonymized.pop("name", None)

        # Заменяем точные даты на периоды
        if "birth_date" in anonymized:
            birth_date = datetime.fromisoformat(anonymized["birth_date"])
            anonymized["birth_year"] = birth_date.year
            anonymized["birth_season"] = DataMinimizationService._get_season(
                birth_date.month
            )
            del anonymized["birth_date"]

        return anonymized

    @staticmethod
    def _get_season(month: int) -> str:
        """Определение сезона по месяцу."""
        seasons = {
            12: "winter",
            1: "winter",
            2: "winter",
            3: "spring",
            4: "spring",
            5: "spring",
            6: "summer",
            7: "summer",
            8: "summer",
            9: "autumn",
            10: "autumn",
            11: "autumn",
        }
        return seasons.get(month, "unknown")
