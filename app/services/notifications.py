"""
Сервис уведомлений пользователей
Централизованная отправка всех уведомлений бота
"""

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

import app.texts as txt
from app.utils.formatters import get_days_word


# ============================================================================
# КЛАВИАТУРЫ ДЛЯ УВЕДОМЛЕНИЙ
# ============================================================================

def get_expiring_keyboard():
    """Клавиатура для уведомлений об истекающей подписке (3 дня / 1 день)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Продлить доступ', callback_data='renew_subscription')],
        [InlineKeyboardButton(text='Зайти в Тихую Комнату', callback_data='go_to_room_entrance')]
    ])


def get_expired_keyboard():
    """Клавиатура для уведомления об истекшей подписке"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Продлить доступ', callback_data='renew_subscription')]
    ])


# ============================================================================
# УВЕДОМЛЕНИЯ О ПЛАТЕЖАХ
# ============================================================================

async def notify_payment_processed(bot: Bot, user_id: int) -> bool:
    """
    Уведомить пользователя об успешной обработке оплаты

    Args:
        bot: Экземпляр бота
        user_id: Telegram ID пользователя

    Returns:
        bool: True если отправлено успешно
    """
    try:
        await bot.send_message(
            chat_id=user_id,
            text=txt.PAYMENT_PROCESSED_NOTIFICATION
        )
        print(f"✅ Уведомление об оплате отправлено пользователю {user_id}")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления пользователю {user_id}: {e}")
        return False


async def notify_multiple_users(bot: Bot, user_ids: List[int], text: str) -> dict:
    """
    Отправить одинаковое уведомление нескольким пользователям

    Args:
        bot: Экземпляр бота
        user_ids: Список ID пользователей
        text: Текст уведомления

    Returns:
        dict: Статистика отправки {success: int, failed: int}
    """
    success = 0
    failed = 0

    for user_id in user_ids:
        try:
            await bot.send_message(chat_id=user_id, text=text)
            success += 1
        except Exception as e:
            print(f"❌ Ошибка отправки пользователю {user_id}: {e}")
            failed += 1

    print(f"📊 Уведомления: успешно {success}, ошибок {failed}")
    return {'success': success, 'failed': failed}


# ============================================================================
# УВЕДОМЛЕНИЯ О ПОДПИСКАХ
# ============================================================================

async def notify_subscription_expiring(bot: Bot, user_id: int, days_left: int) -> bool:
    """
    Уведомить пользователя о скором истечении подписки

    Args:
        bot: Экземпляр бота
        user_id: Telegram ID пользователя
        days_left: Сколько дней осталось (0 = последний день)

    Returns:
        bool: True если отправлено успешно
    """
    try:
        if days_left == 0:
            # Последний день подписки
            text = "⚠️ Внимание! Сегодня последний день твоей подписки.\n\n"
            text += "Продли сейчас, чтобы не потерять доступ к Тихой Комнате."
        else:
            days_word = get_days_word(days_left)
            text = f"⚠️ Внимание! Твоя подписка истекает через {days_left} {days_word}.\n\n"
            text += "Рекомендуем продлить заранее, чтобы не потерять доступ к Тихой Комнате."

        await bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=get_expiring_keyboard()
        )
        print(f"✅ Уведомление об истечении подписки отправлено пользователю {user_id} (дней: {days_left})")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления пользователю {user_id}: {e}")
        return False


async def notify_subscription_expired(bot: Bot, user_id: int) -> bool:
    """
    Уведомить пользователя об истечении подписки

    Args:
        bot: Экземпляр бота
        user_id: Telegram ID пользователя

    Returns:
        bool: True если отправлено успешно
    """
    try:
        text = "❌ Твоя подписка истекла.\n\n"
        text += "Доступ к Тихой Комнате приостановлен."

        await bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=get_expired_keyboard()
        )
        print(f"✅ Уведомление об истечении подписки отправлено пользователю {user_id}")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления пользователю {user_id}: {e}")
        return False


# ============================================================================
# ПРИМЕЧАНИЯ ПО ИСПОЛЬЗОВАНИЮ
# ============================================================================

"""
Как использовать:

В background_tasks.py:
    from app.services.notifications import notify_payment_processed

    # После обработки платежа
    for user_id in notified_users:
        await notify_payment_processed(bot, user_id)

В handlers:
    from app.services.notifications import notify_subscription_expiring

    # При проверке подписки
    if days_left <= 3:
        await notify_subscription_expiring(bot, user_id, days_left)

Преимущества:
    - Весь текст уведомлений в одном месте
    - Легко изменить формат уведомлений
    - Централизованная обработка ошибок
    - Легко добавлять новые типы уведомлений
"""

"тест мерджа"