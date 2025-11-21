"""
Фоновые задачи бота
Планировщик для автоматической проверки оплат и синхронизации
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.database import (
    migrate_many_users,
    sync_is_vip_for_all_users,
    process_all_pending_payments
)
from app.services import notify_payment_processed
from app.services.subscription import (
    check_and_expire_subscriptions,
    check_expiring_soon_subscriptions,
    check_expired_subscriptions_for_reminders
)
from app.services.notifications import (
    notify_expiring_1_day,
    notify_expiring_today,
    notify_expired_3_days,
    notify_expired_7_days
)
from app.config import (
    PAYMENT_CHECK_INTERVAL_SECONDS,
    USER_SYNC_INTERVAL_MINUTES
)


async def check_payments_task(bot):
    """
    Фоновая задача проверки и обработки оплат из Tilda
    Вызывается каждые 30 секунд
    """
    print("💳 Проверка оплат...")

    notified_users = process_all_pending_payments()

    if notified_users:
        print(f"📨 Отправка уведомлений {len(notified_users)} пользователям...")
        for user_id in notified_users:
            await notify_payment_processed(bot, user_id)

    print("✅ Проверка оплат завершена!\n")


async def sync_users_task(bot):
    print("🔄 Синхронизация пользователей...")

    print("📋 Миграция временных VIP пользователей...")
    migrate_many_users()

    print("📋 Синхронизация is_vip...")
    sync_is_vip_for_all_users()

    print("✅ Синхронизация завершена!\n")


async def check_subscriptions_task(bot):
    """
    Фоновая задача проверки подписок
    Запускается раз в день в 12:00 + сразу при старте бота

    Уведомления:
    - За 1 день до истечения
    - В день истечения (последний день)
    - Через 3 дня после истечения
    - Через 7 дней после истечения (последнее)
    """
    print("📅 Проверка подписок...")

    # 1. Деактивируем истекшие подписки (без уведомлений - они будут отдельно)
    await check_and_expire_subscriptions()

    # 2. Проверяем скоро истекающие подписки (до истечения)
    expiring = await check_expiring_soon_subscriptions()

    # Уведомления за 1 день
    for user_id in expiring['expiring_1_day']:
        await notify_expiring_1_day(bot, user_id)

    # Уведомления в последний день (сегодня)
    for user_id in expiring['expiring_today']:
        await notify_expiring_today(bot, user_id)

    # 3. Проверяем истёкшие подписки для напоминаний (после истечения)
    expired_reminders = await check_expired_subscriptions_for_reminders()

    # Уведомления через 3 дня после истечения
    for user_id in expired_reminders['expired_3_days']:
        await notify_expired_3_days(bot, user_id)

    # Уведомления через 7 дней после истечения (последнее)
    for user_id in expired_reminders['expired_7_days']:
        await notify_expired_7_days(bot, user_id)

    print("✅ Проверка подписок завершена!\n")


# ============================================================================
# НАСТРОЙКА ПЛАНИРОВЩИКА
# ============================================================================

async def run_initial_subscription_check(bot):
    """Запустить проверку подписок сразу при старте бота"""
    print("\n🚀 Запуск начальной проверки подписок...")
    await check_subscriptions_task(bot)


def setup_scheduler(bot):
    scheduler = AsyncIOScheduler()

    # Задача 1: Проверка оплат (каждые 30 секунд)
    scheduler.add_job(
        check_payments_task,
        trigger=IntervalTrigger(seconds=PAYMENT_CHECK_INTERVAL_SECONDS),
        args=[bot],
        id='check_payments',
        name='Проверка оплат',
        replace_existing=True
    )
    print(f"⚡ Задача 'Проверка оплат' настроена: каждые {PAYMENT_CHECK_INTERVAL_SECONDS} секунд")

    # Задача 2: Синхронизация пользователей (каждые 15 минут)
    scheduler.add_job(
        sync_users_task,
        trigger=IntervalTrigger(minutes=USER_SYNC_INTERVAL_MINUTES),
        args=[bot],
        id='sync_users',
        name='Синхронизация пользователей',
        replace_existing=True
    )
    print(f"🔄 Задача 'Синхронизация пользователей' настроена: каждые {USER_SYNC_INTERVAL_MINUTES} минут")

    # Задача 3: Проверка подписок (каждый день в 12:00)
    scheduler.add_job(
        check_subscriptions_task,
        trigger=CronTrigger(hour=12, minute=0),
        args=[bot],
        id='check_subscriptions',
        name='Проверка подписок',
        replace_existing=True
    )
    print("📅 Задача 'Проверка подписок' настроена: каждый день в 12:00")

    # Задача 4: Начальная проверка подписок (сразу при запуске)
    scheduler.add_job(
        check_subscriptions_task,
        args=[bot],
        id='initial_subscription_check',
        name='Начальная проверка подписок',
        replace_existing=True
    )
    print("🔍 Начальная проверка подписок будет запущена сразу...")

    scheduler.start()
    print("🚀 Планировщик запущен!\n")

    return scheduler
