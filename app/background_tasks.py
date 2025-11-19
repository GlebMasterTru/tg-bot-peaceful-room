"""
Фоновые задачи бота
Планировщик для автоматической проверки оплат и синхронизации
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.database import (
    migrate_many_users,
    sync_is_vip_for_all_users,
    process_all_pending_payments
)
from app.services import notify_payment_processed
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


# ============================================================================
# НАСТРОЙКА ПЛАНИРОВЩИКА
# ============================================================================

def setup_scheduler(bot):
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        check_payments_task,
        trigger=IntervalTrigger(seconds=PAYMENT_CHECK_INTERVAL_SECONDS),
        args=[bot],
        id='check_payments',
        name='Проверка оплат',
        replace_existing=True
    )
    print(f"⚡ Задача 'Проверка оплат' настроена: каждые {PAYMENT_CHECK_INTERVAL_SECONDS} секунд")

    scheduler.add_job(
        sync_users_task,
        trigger=IntervalTrigger(minutes=USER_SYNC_INTERVAL_MINUTES),
        args=[bot],
        id='sync_users',
        name='Синхронизация пользователей',
        replace_existing=True
    )
    print(f"🔄 Задача 'Синхронизация пользователей' настроена: каждые {USER_SYNC_INTERVAL_MINUTES} минут")
    
    scheduler.start()
    print("🚀 Планировщик запущен!\n")
    
    return scheduler