"""
Конфигурация Payment Service
"""

import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения"""

    # Основные настройки
    app_name: str = "Lapa Payment Service"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Серверные настройки
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    # PostgreSQL настройки
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_user: str = os.getenv("POSTGRES_USER", "lapa_user")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "lapa_password")
    postgres_db: str = os.getenv("POSTGRES_DB", "lapa")

    # Redis настройки
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")

    # MongoDB настройки
    mongo_host: str = os.getenv("MONGO_HOST", "localhost")
    mongo_port: int = int(os.getenv("MONGO_PORT", "27017"))
    mongo_user: str = os.getenv("MONGO_USER", "lapa_user")
    mongo_password: str = os.getenv("MONGO_PASSWORD", "lapa_password")
    mongo_db: str = os.getenv("MONGO_DB", "lapa")

    # CORS настройки
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080",
        "https://lapa-kolomna.ru"
    ]

    # Доверенные хосты
    allowed_hosts: List[str] = ["*"]

    # Настройки платежей
    platform_commission: float = float(os.getenv("PLATFORM_COMMISSION", "0.1"))  # 10% комиссия платформы
    max_payment_amount: float = float(os.getenv("MAX_PAYMENT_AMOUNT", "50000"))  # Максимальная сумма платежа
    min_payment_amount: float = float(os.getenv("MIN_PAYMENT_AMOUNT", "100"))    # Минимальная сумма платежа

    # Таймауты платежей
    payment_confirmation_timeout: int = int(os.getenv("PAYMENT_CONFIRMATION_TIMEOUT", "900"))  # 15 минут
    payment_refund_timeout: int = int(os.getenv("PAYMENT_REFUND_TIMEOUT", "2592000"))  # 30 дней

    # Настройки безопасности
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "your-encryption-key-here")
    webhook_secret: str = os.getenv("WEBHOOK_SECRET", "your-webhook-secret")

    # Интеграция с платежными системами
    # Stripe
    stripe_publishable_key: Optional[str] = os.getenv("STRIPE_PUBLISHABLE_KEY")
    stripe_secret_key: Optional[str] = os.getenv("STRIPE_SECRET_KEY")
    stripe_webhook_secret: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")

    # ЮKassa (ЮMoney)
    yookassa_shop_id: Optional[str] = os.getenv("YOOKASSA_SHOP_ID")
    yookassa_secret_key: Optional[str] = os.getenv("YOOKASSA_SECRET_KEY")

    # Тинькофф Оплата
    tinkoff_terminal_key: Optional[str] = os.getenv("TINKOFF_TERMINAL_KEY")
    tinkoff_terminal_password: Optional[str] = os.getenv("TINKOFF_TERMINAL_PASSWORD")

    # Система быстрых платежей (СБП)
    sbp_enabled: bool = os.getenv("SBP_ENABLED", "false").lower() == "true"
    sbp_merchant_id: Optional[str] = os.getenv("SBP_MERCHANT_ID")

    # Настройки выплат
    auto_payout_enabled: bool = os.getenv("AUTO_PAYOUT_ENABLED", "true").lower() == "true"
    min_payout_amount: float = float(os.getenv("MIN_PAYOUT_AMOUNT", "1000"))  # Минимальная сумма для выплаты
    payout_schedule: str = os.getenv("PAYOUT_SCHEDULE", "weekly")  # daily, weekly, monthly

    # Валюты
    default_currency: str = os.getenv("DEFAULT_CURRENCY", "RUB")
    supported_currencies: List[str] = ["RUB", "USD", "EUR"]

    # Настройки кошельков
    wallet_enabled: bool = os.getenv("WALLET_ENABLED", "true").lower() == "true"
    wallet_min_balance: float = float(os.getenv("WALLET_MIN_BALANCE", "-5000"))  # Разрешенный овердрафт
    wallet_max_balance: float = float(os.getenv("WALLET_MAX_BALANCE", "100000"))  # Максимальный баланс

    # Настройки уведомлений
    payment_notification_enabled: bool = os.getenv("PAYMENT_NOTIFICATION_ENABLED", "true").lower() == "true"
    refund_notification_enabled: bool = os.getenv("REFUND_NOTIFICATION_ENABLED", "true").lower() == "true"

    # Настройки отчетности
    financial_reports_enabled: bool = os.getenv("FINANCIAL_REPORTS_ENABLED", "true").lower() == "true"
    reports_retention_days: int = int(os.getenv("REPORTS_RETENTION_DAYS", "365"))  # Хранение отчетов

    # Настройки тестирования
    test_mode: bool = os.getenv("TEST_MODE", "false").lower() == "true"
    test_card_numbers: List[str] = [
        "4242424242424242",  # Stripe test card
        "5555555555554444",  # Mastercard test
        "378282246310005",   # American Express test
    ]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
