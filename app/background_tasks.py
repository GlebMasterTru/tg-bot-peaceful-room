import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.database import migrate_many_users, sync_is_vip_for_all_users, process_all_pending_payments
import app.texts as txt


async def check_payments_task(bot):
    print("💳 Проверка оплат...")
    
    notified_users = process_all_pending_payments()
    
    if notified_users:
        print(f"📨 Отправка уведомлений {len(notified_users)} пользователям...")
        for user_id in notified_users:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=txt.PAYMENT_PROCESSED_NOTIFICATION
                )
                print(f"✅ Уведомление отправлено пользователю {user_id}")
            except Exception as e:
                print(f"❌ Ошибка отправки уведомления для {user_id}: {e}")
    
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
        trigger=IntervalTrigger(seconds=30),
        args=[bot],
        id='check_payments',
        name='Проверка оплат',
        replace_existing=True
    )
    print("⚡ Задача 'Проверка оплат' настроена: каждые 30 секунд")
    
    scheduler.add_job(
        sync_users_task,
        trigger=IntervalTrigger(minutes=15),
        args=[bot],
        id='sync_users',
        name='Синхронизация пользователей',
        replace_existing=True
    )
    print("🔄 Задача 'Синхронизация пользователей' настроена: каждые 15 минут")
    
    scheduler.start()
    print("🚀 Планировщик запущен!\n")
    
    return scheduler