"""
Сервис управления подписками
Бизнес-логика проверки и обновления подписок
"""

from datetime import datetime
from typing import List, Tuple

from app.database import (
    get_all_users,
    get_user,
    update_user_batch,
    get_subscription_status
)


# ============================================================================
# ПРОВЕРКА ИСТЕКШИХ ПОДПИСОК
# ============================================================================

async def check_and_expire_subscriptions() -> List[int]:
    """
    Проверить все активные подписки и деактивировать истекшие

    Эта функция вызывается фоновой задачей каждые 15 минут.
    Проверяет всех пользователей с активной подпиской и деактивирует
    те, у которых sub_end < текущая дата.

    Returns:
        list: Список user_id пользователей с деактивированными подписками
    """
    print("🔍 Проверка истекших подписок...")

    try:
        all_users = get_all_users()
        current_time = datetime.now()
        expired_users = []

        for user_data in all_users:
            user_id = user_data.get('user_id')
            if not user_id:
                continue

            # Получаем полные данные пользователя
            user = get_user(user_id)
            if not user:
                continue

            # Проверяем только пользователей с активной подпиской
            is_sub_active = user.get('is_sub_active', 'False')
            if is_sub_active != 'True':
                continue

            # Проверяем дату окончания
            sub_end_str = user.get('sub_end', '')
            if not sub_end_str:
                continue

            try:
                sub_end = datetime.strptime(sub_end_str, '%Y-%m-%d %H:%M:%S')

                # Если подписка истекла
                if sub_end < current_time:
                    # Деактивируем подписку
                    update_data = {
                        'is_sub_active': 'False',
                        'is_diamond': 'False',
                        'last_updated_info': current_time.strftime('%Y-%m-%d %H:%M:%S')
                    }

                    success = update_user_batch(user_id, update_data)
                    if success:
                        expired_users.append(user_id)
                        print(f"⏰ Подписка деактивирована для пользователя {user_id}")

            except ValueError as e:
                print(f"⚠️ Ошибка парсинга даты {sub_end_str} для {user_id}: {e}")
                continue

        if expired_users:
            print(f"✅ Деактивировано подписок: {len(expired_users)}")
        else:
            print("ℹ️ Истекших подписок не найдено")

        return expired_users

    except Exception as e:
        print(f"❌ Ошибка проверки подписок: {e}")
        return []


# ============================================================================
# ПРОВЕРКА СКОРО ИСТЕКАЮЩИХ ПОДПИСОК
# ============================================================================

async def check_expiring_soon_subscriptions() -> dict:
    """
    Проверить подписки, которые скоро истекут

    Возвращает словарь с пользователями, которым нужно отправить уведомления:
    - За 3 дня до истечения
    - За 1 день до истечения

    Returns:
        dict: {
            'expiring_3_days': [user_id1, user_id2, ...],
            'expiring_1_day': [user_id3, user_id4, ...]
        }
    """
    print("🔍 Проверка скоро истекающих подписок...")

    try:
        all_users = get_all_users()
        expiring_3_days = []
        expiring_1_day = []

        for user_data in all_users:
            user_id = user_data.get('user_id')
            if not user_id:
                continue

            # Получаем статус подписки
            sub_info = get_subscription_status(user_id)

            # Проверяем только активные подписки
            if sub_info['status'] != 'active' and sub_info['status'] != 'expiring_soon':
                continue

            days_left = sub_info.get('days_left', 0)

            # За 3 дня до истечения
            if days_left == 3:
                expiring_3_days.append(user_id)
                print(f"⚠️ Подписка истекает через 3 дня: {user_id}")

            # За 1 день до истечения
            elif days_left == 1:
                expiring_1_day.append(user_id)
                print(f"⚠️ Подписка истекает через 1 день: {user_id}")

        print(f"📊 Истекают через 3 дня: {len(expiring_3_days)}, через 1 день: {len(expiring_1_day)}")

        return {
            'expiring_3_days': expiring_3_days,
            'expiring_1_day': expiring_1_day
        }

    except Exception as e:
        print(f"❌ Ошибка проверки истекающих подписок: {e}")
        return {
            'expiring_3_days': [],
            'expiring_1_day': []
        }


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def get_subscription_info_text(user_id: int) -> str:
    """
    Получить текстовое описание статуса подписки для пользователя

    Args:
        user_id: Telegram ID пользователя

    Returns:
        str: Форматированный текст статуса подписки
    """
    sub_info = get_subscription_status(user_id)
    status = sub_info['status']

    if status == 'active':
        return f"✅ Подписка активна до {sub_info['end_date']}"
    elif status == 'expiring_soon':
        days_left = sub_info['days_left']
        from app.utils.formatters import get_days_word
        days_word = get_days_word(days_left)
        return f"⚠️ Подписка истекает через {days_left} {days_word} ({sub_info['end_date']})"
    elif status == 'expired':
        return f"❌ Подписка истекла {sub_info['end_date']}"
    elif status == 'none':
        return "ℹ️ Активной подписки нет"
    else:
        return "⚠️ Не удалось проверить статус подписки"


# ============================================================================
# ПРИМЕЧАНИЯ ПО ИСПОЛЬЗОВАНИЮ
# ============================================================================

"""
Как использовать:

В background_tasks.py:
    from app.services.subscription import (
        check_and_expire_subscriptions,
        check_expiring_soon_subscriptions
    )
    from app.services.notifications import (
        notify_subscription_expired,
        notify_subscription_expiring
    )

    async def subscription_check_task(bot):
        # Проверяем истекшие
        expired_users = await check_and_expire_subscriptions()
        for user_id in expired_users:
            await notify_subscription_expired(bot, user_id)

        # Проверяем скоро истекающие
        expiring = await check_expiring_soon_subscriptions()

        for user_id in expiring['expiring_3_days']:
            await notify_subscription_expiring(bot, user_id, 3)

        for user_id in expiring['expiring_1_day']:
            await notify_subscription_expiring(bot, user_id, 1)

В handlers:
    from app.services.subscription import get_subscription_info_text

    @router.callback_query(F.data == 'check_subscription')
    async def check_subscription(callback: CallbackQuery):
        user_id = callback.from_user.id
        text = get_subscription_info_text(user_id)
        await callback.message.edit_text(text, ...)

Преимущества:
    - Бизнес-логика отделена от handlers
    - Легко тестировать логику подписок
    - Централизованная обработка дат и статусов
    - Легко добавлять новые проверки
"""
