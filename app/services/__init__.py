"""
Services модуль - бизнес-логика приложения
Сервисы для управления подписками и уведомлениями
"""

# Subscription service
from app.services.subscription import (
    check_and_expire_subscriptions,
    check_expiring_soon_subscriptions,
    check_expired_subscriptions_for_reminders,
    get_subscription_info_text
)

# Notifications service
from app.services.notifications import (
    notify_payment_processed,
    notify_multiple_users,
    notify_expiring_1_day,
    notify_expiring_today,
    notify_expired_3_days,
    notify_expired_7_days
)


__all__ = [
    # Subscription
    'check_and_expire_subscriptions',
    'check_expiring_soon_subscriptions',
    'check_expired_subscriptions_for_reminders',
    'get_subscription_info_text',

    # Notifications
    'notify_payment_processed',
    'notify_multiple_users',
    'notify_expiring_1_day',
    'notify_expiring_today',
    'notify_expired_3_days',
    'notify_expired_7_days',
]
