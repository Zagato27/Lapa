"""
Основной сервис аналитики
Координирует все операции аналитики платформы
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.event import Event, EventType, EventCategory
from app.models.metric import Metric, MetricType, MetricCategory, MetricGranularity
from app.models.kpi import KPI, KPIType, KPICategory
from app.schemas.event import EventCreate, EventResponse
from app.schemas.metric import MetricCreate, MetricResponse
from app.schemas.kpi import KPICreate, KPIResponse

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Основной сервис аналитики"""

    @staticmethod
    async def track_event(
        db: AsyncSession,
        event_data: EventCreate
    ) -> Event:
        """Отслеживание события"""
        try:
            event = Event(
                id=str(uuid.uuid4()),
                event_type=event_data.event_type,
                category=event_data.category,
                priority=event_data.priority,
                service_name=event_data.service_name,
                event_name=event_data.event_name,
                user_id=event_data.user_id,
                session_id=event_data.session_id,
                device_id=event_data.device_id,
                description=event_data.description,
                properties=event_data.properties or {},
                metadata=event_data.metadata,
                user_agent=event_data.user_agent,
                ip_address=event_data.ip_address,
                location_data=event_data.location_data,
                device_info=event_data.device_info,
                order_id=event_data.order_id,
                pet_id=event_data.pet_id,
                chat_id=event_data.chat_id,
                payment_id=event_data.payment_id,
                duration_ms=event_data.duration_ms,
                memory_usage_mb=event_data.memory_usage_mb,
                cpu_usage_percent=event_data.cpu_usage_percent,
                revenue_impact=event_data.revenue_impact,
                user_engagement_score=event_data.user_engagement_score,
                event_timestamp=datetime.utcnow()
            )

            db.add(event)
            await db.commit()
            await db.refresh(event)

            # Асинхронная обработка события
            # Здесь можно добавить отправку в очередь для дальнейшей обработки

            logger.info(f"Event tracked: {event.event_name} from {event.service_name}")
            return event

        except Exception as e:
            logger.error(f"Event tracking failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def create_metric(
        db: AsyncSession,
        metric_data: MetricCreate
    ) -> Metric:
        """Создание метрики"""
        try:
            metric = Metric(
                id=str(uuid.uuid4()),
                name=metric_data.name,
                display_name=metric_data.display_name,
                description=metric_data.description,
                metric_type=metric_data.metric_type,
                category=metric_data.category,
                granularity=metric_data.granularity,
                aggregation_function=metric_data.aggregation_function,
                value=metric_data.value,
                dimensions=metric_data.dimensions or {},
                tags=metric_data.tags,
                metadata=metric_data.metadata,
                timestamp=metric_data.timestamp or datetime.utcnow()
            )

            db.add(metric)
            await db.commit()
            await db.refresh(metric)

            logger.info(f"Metric created: {metric.name} = {metric.value}")
            return metric

        except Exception as e:
            logger.error(f"Metric creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def create_kpi(
        db: AsyncSession,
        kpi_data: KPICreate
    ) -> KPI:
        """Создание KPI"""
        try:
            kpi = KPI(
                id=str(uuid.uuid4()),
                name=kpi_data.name,
                display_name=kpi_data.display_name,
                description=kpi_data.description,
                kpi_type=kpi_data.kpi_type,
                category=kpi_data.category,
                current_value=kpi_data.current_value,
                target_value=kpi_data.target_value,
                baseline_value=kpi_data.baseline_value,
                calculation_formula=kpi_data.calculation_formula,
                calculation_parameters=kpi_data.calculation_parameters,
                related_metrics=kpi_data.related_metrics,
                owner_id=kpi_data.owner_id,
                department=kpi_data.department,
                team=kpi_data.team,
                priority=kpi_data.priority,
                weight=kpi_data.weight,
                alert_enabled=kpi_data.alert_enabled,
                alert_threshold=kpi_data.alert_threshold,
                alert_condition=kpi_data.alert_condition,
                tags=kpi_data.tags,
                metadata=kpi_data.metadata
            )

            db.add(kpi)
            await db.commit()
            await db.refresh(kpi)

            logger.info(f"KPI created: {kpi.name}")
            return kpi

        except Exception as e:
            logger.error(f"KPI creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_event_statistics(
        db: AsyncSession,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        service_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение статистики событий"""
        try:
            query = select(Event)

            if date_from:
                query = query.where(Event.event_timestamp >= date_from)
            if date_to:
                query = query.where(Event.event_timestamp <= date_to)
            if service_name:
                query = query.where(Event.service_name == service_name)

            subq = query.subquery()

            # Общее количество событий
            total_events = await db.scalar(select(func.count()).select_from(subq))

            # Статистика по типам
            events_by_type_query = (
                select(Event.event_type, func.count(Event.id))
                .select_from(subq)
                .group_by(Event.event_type)
            )
            events_by_type_result = await db.execute(events_by_type_query)
            events_by_type = dict(events_by_type_result.all())

            # Статистика по категориям
            events_by_category_query = (
                select(Event.category, func.count(Event.id))
                .select_from(subq)
                .group_by(Event.category)
            )
            events_by_category_result = await db.execute(events_by_category_query)
            events_by_category = dict(events_by_category_result.all())

            # Статистика по сервисам
            events_by_service_query = (
                select(Event.service_name, func.count(Event.id))
                .select_from(subq)
                .group_by(Event.service_name)
            )
            events_by_service_result = await db.execute(events_by_service_query)
            events_by_service = dict(events_by_service_result.all())

            # Дополнительные показатели для EventStatisticsResponse
            now = datetime.utcnow()
            one_day_ago = now - timedelta(days=1)
            one_week_ago = now - timedelta(days=7)
            one_month_ago = now - timedelta(days=30)

            events_today = await db.scalar(
                select(func.count(Event.id)).where(Event.event_timestamp >= one_day_ago)
            )
            events_this_week = await db.scalar(
                select(func.count(Event.id)).where(Event.event_timestamp >= one_week_ago)
            )
            events_this_month = await db.scalar(
                select(func.count(Event.id)).where(Event.event_timestamp >= one_month_ago)
            )

            suspicious_events = await db.scalar(
                select(func.count(Event.id)).where(Event.is_suspicious.is_(True))
            )

            # Кол-во ошибок обработки как число записей с непустым processing_errors
            processing_errors = await db.scalar(
                select(func.count(Event.id)).where(Event.processing_errors.isnot(None))
            )

            return {
                "total_events": total_events or 0,
                "events_by_type": events_by_type,
                "events_by_category": events_by_category,
                "events_by_service": events_by_service,
                "events_today": events_today or 0,
                "events_this_week": events_this_week or 0,
                "events_this_month": events_this_month or 0,
                "suspicious_events": suspicious_events or 0,
                "processing_errors": processing_errors or 0,
                "average_processing_time": 0.0,
                "period_start": date_from or datetime.utcnow() - timedelta(days=30),
                "period_end": date_to or datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Error getting event statistics: {e}")
            return {}

    @staticmethod
    async def get_metric_statistics(
        db: AsyncSession,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение статистики метрик"""
        try:
            query = select(Metric)

            if date_from:
                query = query.where(Metric.timestamp >= date_from)
            if date_to:
                query = query.where(Metric.timestamp <= date_to)
            if category:
                try:
                    category_enum = MetricCategory(category)
                    query = query.where(Metric.category == category_enum)
                except Exception:
                    pass

            subq = query.subquery()

            # Общее количество метрик
            total_metrics = await db.scalar(select(func.count()).select_from(subq))

            # Статистика по типам
            metrics_by_type_query = (
                select(Metric.metric_type, func.count(Metric.id))
                .select_from(subq)
                .group_by(Metric.metric_type)
            )
            metrics_by_type_result = await db.execute(metrics_by_type_query)
            metrics_by_type = dict(metrics_by_type_result.all())

            # Статистика по категориям
            metrics_by_category_query = (
                select(Metric.category, func.count(Metric.id))
                .select_from(subq)
                .group_by(Metric.category)
            )
            metrics_by_category_result = await db.execute(metrics_by_category_query)
            metrics_by_category = dict(metrics_by_category_result.all())

            # Статистика по гранулярности
            metrics_by_granularity_query = (
                select(Metric.granularity, func.count(Metric.id))
                .select_from(subq)
                .group_by(Metric.granularity)
            )
            metrics_by_granularity_result = await db.execute(metrics_by_granularity_query)
            metrics_by_granularity = dict(metrics_by_granularity_result.all())

            # Дополнительные показатели
            now = datetime.utcnow()
            one_day_ago = now - timedelta(days=1)
            one_week_ago = now - timedelta(days=7)
            one_month_ago = now - timedelta(days=30)

            metrics_today = await db.scalar(
                select(func.count(Metric.id)).where(Metric.timestamp >= one_day_ago)
            )
            metrics_this_week = await db.scalar(
                select(func.count(Metric.id)).where(Metric.timestamp >= one_week_ago)
            )
            metrics_this_month = await db.scalar(
                select(func.count(Metric.id)).where(Metric.timestamp >= one_month_ago)
            )

            average_data_quality = await db.scalar(select(func.avg(Metric.data_quality_score)))
            validation_errors_count = await db.scalar(
                select(func.count(Metric.id)).where(Metric.validation_errors.isnot(None))
            )

            return {
                "total_metrics": total_metrics or 0,
                "metrics_by_type": metrics_by_type,
                "metrics_by_category": metrics_by_category,
                "metrics_by_granularity": metrics_by_granularity,
                "metrics_today": metrics_today or 0,
                "metrics_this_week": metrics_this_week or 0,
                "metrics_this_month": metrics_this_month or 0,
                "average_data_quality": float(average_data_quality or 0.0),
                "validation_errors_count": validation_errors_count or 0,
                "period_start": date_from or datetime.utcnow() - timedelta(days=30),
                "period_end": date_to or datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Error getting metric statistics: {e}")
            return {}

    @staticmethod
    async def get_kpi_statistics(
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Получение статистики KPI"""
        try:
            # Общее количество KPI
            total_kpis = await db.scalar(select(func.count(KPI.id)))

            # Статистика по статусам
            kpis_by_status_query = (
                select(KPI.status, func.count(KPI.id))
                .where(KPI.status.isnot(None))
                .group_by(KPI.status)
            )
            kpis_by_status_result = await db.execute(kpis_by_status_query)
            kpis_by_status = dict(kpis_by_status_result.all())

            # Статистика по категориям
            kpis_by_category_query = (
                select(KPI.category, func.count(KPI.id))
                .group_by(KPI.category)
            )
            kpis_by_category_result = await db.execute(kpis_by_category_query)
            kpis_by_category = dict(kpis_by_category_result.all())

            # Статистика по типам
            kpis_by_type_query = (
                select(KPI.kpi_type, func.count(KPI.id)).group_by(KPI.kpi_type)
            )
            kpis_by_type_result = await db.execute(kpis_by_type_query)
            kpis_by_type = dict(kpis_by_type_result.all())

            # Средний прогресс
            average_progress = await db.scalar(select(func.avg(KPI.progress_percentage)))

            # Кол-во KPI с алертами
            kpis_with_alerts = await db.scalar(select(func.count(KPI.id)).where(KPI.alert_enabled.is_(True)))

            # Детальные количества по статусам
            def _status_count(status):
                return int(kpis_by_status.get(status, 0))

            from app.models.kpi import KPIStatus as _KPIStatus

            return {
                "total_kpis": total_kpis or 0,
                "kpis_by_status": kpis_by_status,
                "kpis_by_category": kpis_by_category,
                "kpis_by_type": kpis_by_type,
                "kpis_on_track": _status_count(_KPIStatus.ON_TRACK),
                "kpis_behind": _status_count(_KPIStatus.BEHIND),
                "kpis_ahead": _status_count(_KPIStatus.AHEAD),
                "kpis_critical": _status_count(_KPIStatus.CRITICAL),
                "average_progress": float(average_progress or 0.0),
                "kpis_with_alerts": int(kpis_with_alerts or 0),
                "period_start": datetime.utcnow() - timedelta(days=30),
                "period_end": datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Error getting KPI statistics: {e}")
            return {}

    @staticmethod
    async def calculate_business_metrics(db: AsyncSession) -> Dict[str, float]:
        """Расчет бизнес-метрик"""
        try:
            # Метрики пользователей
            total_users = await db.scalar(select(func.count(Event.user_id.distinct())))

            # Метрики заказов
            order_events = await db.scalar(
                select(func.count(Event.id))
                .where(Event.category == EventCategory.ORDER)
            )

            # Метрики платежей
            payment_events = await db.scalar(
                select(func.count(Event.id))
                .where(Event.category == EventCategory.PAYMENT)
            )

            # Метрики вовлеченности
            engagement_events = await db.scalar(
                select(func.count(Event.id))
                .where(Event.category.in_([
                    EventCategory.NAVIGATION,
                    EventCategory.CHAT,
                    EventCategory.MEDIA
                ]))
            )

            return {
                "total_users": total_users or 0,
                "order_events": order_events or 0,
                "payment_events": payment_events or 0,
                "engagement_events": engagement_events or 0,
                "average_orders_per_user": (order_events or 0) / max(total_users or 1, 1),
                "conversion_rate": (payment_events or 0) / max(order_events or 1, 1) * 100
            }

        except Exception as e:
            logger.error(f"Error calculating business metrics: {e}")
            return {}

    @staticmethod
    def event_to_response(event: Event) -> EventResponse:
        """Преобразование модели Event в схему ответа"""
        return EventResponse(
            id=event.id,
            event_type=event.event_type,
            category=event.category,
            priority=event.priority,
            service_name=event.service_name,
            user_id=event.user_id,
            session_id=event.session_id,
            device_id=event.device_id,
            event_name=event.event_name,
            description=event.description,
            properties=event.properties,
            metadata=event.metadata,
            user_agent=event.user_agent,
            ip_address=event.ip_address,
            location_data=event.location_data,
            device_info=event.device_info,
            event_timestamp=event.event_timestamp,
            processed_at=event.processed_at,
            created_at=event.created_at,
            order_id=event.order_id,
            pet_id=event.pet_id,
            chat_id=event.chat_id,
            payment_id=event.payment_id,
            duration_ms=event.duration_ms,
            memory_usage_mb=event.memory_usage_mb,
            cpu_usage_percent=event.cpu_usage_percent,
            is_processed=event.is_processed,
            processing_errors=event.processing_errors,
            is_suspicious=event.is_suspicious,
            anomaly_score=event.anomaly_score,
            revenue_impact=event.revenue_impact,
            user_engagement_score=event.user_engagement_score
        )

    @staticmethod
    def metric_to_response(metric: Metric) -> MetricResponse:
        """Преобразование модели Metric в схему ответа"""
        return MetricResponse(
            id=metric.id,
            name=metric.name,
            display_name=metric.display_name,
            description=metric.description,
            metric_type=metric.metric_type,
            category=metric.category,
            granularity=metric.granularity,
            aggregation_function=metric.aggregation_function,
            value=metric.value,
            previous_value=metric.previous_value,
            change_percentage=metric.change_percentage,
            dimensions=metric.dimensions,
            tags=metric.tags,
            metadata=metric.metadata,
            timestamp=metric.timestamp,
            period_start=metric.period_start,
            period_end=metric.period_end,
            data_quality_score=metric.data_quality_score,
            confidence_interval=metric.confidence_interval,
            sample_size=metric.sample_size,
            is_calculated=metric.is_calculated,
            is_validated=metric.is_validated,
            validation_errors=metric.validation_errors,
            calculated_by=metric.calculated_by,
            calculation_method=metric.calculation_method,
            created_at=metric.created_at,
            updated_at=metric.updated_at
        )

    @staticmethod
    def kpi_to_response(kpi: KPI) -> KPIResponse:
        """Преобразование модели KPI в схему ответа"""
        return KPIResponse(
            id=kpi.id,
            name=kpi.name,
            display_name=kpi.display_name,
            description=kpi.description,
            kpi_type=kpi.kpi_type,
            category=kpi.category,
            current_value=kpi.current_value,
            target_value=kpi.target_value,
            baseline_value=kpi.baseline_value,
            trend=kpi.trend,
            trend_strength=kpi.trend_strength,
            change_percentage=kpi.change_percentage,
            status=kpi.status,
            progress_percentage=kpi.progress_percentage,
            calculation_period=kpi.calculation_period,
            last_calculated_at=kpi.last_calculated_at,
            calculation_formula=kpi.calculation_formula,
            calculation_parameters=kpi.calculation_parameters,
            related_metrics=kpi.related_metrics,
            owner_id=kpi.owner_id,
            department=kpi.department,
            team=kpi.team,
            priority=kpi.priority,
            weight=kpi.weight,
            alert_enabled=kpi.alert_enabled,
            alert_threshold=kpi.alert_threshold,
            alert_condition=kpi.alert_condition,
            tags=kpi.tags,
            metadata=kpi.metadata,
            created_at=kpi.created_at,
            updated_at=kpi.updated_at,
        )
