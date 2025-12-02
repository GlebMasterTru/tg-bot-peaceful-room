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
from app.database.connection import users_worksheet


# ============================================================================
# ПРОВЕРКА ИСТЕКШИХ ПОДПИСОК
# ============================================================================

async def check_and_expire_subscriptions() -> List[int]:
    """
    Проверить все активные подписки и деактивировать истекшие

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

            user = get_user(user_id)
            if not user:
                continue

            is_sub_active = user.get('is_sub_active', 'False')
            if is_sub_active != 'True':
                continue

            sub_end_str = user.get('sub_end', '')
            if not sub_end_str:
                continue

            try:
                sub_end = datetime.strptime(sub_end_str, '%Y-%m-%d %H:%M:%S')

                if sub_end < current_time:
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
# ПРОВЕРКА СКОРО ИСТЕКАЮЩИХ ПОДПИСОК (до истечения)
# ============================================================================

async def check_expiring_soon_subscriptions() -> dict:
    """
    Проверить подписки, которые скоро истекут

    Возвращает:
    - За 3 дня до истечения
    - В последний день (0 дней)

    Returns:
        dict: {
            'expiring_3_days': [user_id1, user_id2, ...],
            'expiring_today': [user_id3, user_id4, ...]
        }
    """
    print("🔍 Проверка скоро истекающих подписок...")

    try:
        all_users = get_all_users()
        expiring_3_days = []
        expiring_today = []

        for user_data in all_users:
            user_id = user_data.get('user_id')
            if not user_id:
                continue

            sub_info = get_subscription_status(user_id)

            # Проверяем только активные подписки
            if sub_info['status'] != 'active' and sub_info['status'] != 'expiring_soon':
                continue

            days_left = sub_info.get('days_left', 0)

            # За 3 дня до истечения
            if days_left == 3:
                expiring_3_days.append(user_id)
                print(f"⚠️ Подписка истекает через 3 дня: {user_id}")

            # Последний день (сегодня)
            elif days_left == 0:
                expiring_today.append(user_id)
                print(f"⚠️ Подписка истекает сегодня: {user_id}")

        print(f"📊 Истекают через 3 дня: {len(expiring_3_days)}, сегодня: {len(expiring_today)}")

        return {
            'expiring_3_days': expiring_3_days,
            'expiring_today': expiring_today
        }

    except Exception as e:
        print(f"❌ Ошибка проверки истекающих подписок: {e}")
        return {
            'expiring_3_days': [],
            'expiring_today': []
        }


# ============================================================================
# ПРОВЕРКА ИСТЁКШИХ ПОДПИСОК (после истечения)
# ============================================================================

async def check_expired_subscriptions_for_reminders() -> dict:
    """
    Проверить истёкшие подписки для напоминаний

    Возвращает пользователей, у которых подписка истекла:
    - Ровно 3 дня назад
    - Ровно 7 дней назад

    Returns:
        dict: {
            'expired_3_days': [user_id1, user_id2, ...],
            'expired_7_days': [user_id3, user_id4, ...]
        }
    """
    print("🔍 Проверка истёкших подписок для напоминаний...")

    try:
        # Получаем все записи напрямую из таблицы
        all_records = users_worksheet.get_all_records()
        current_date = datetime.now().date()

        expired_3_days = []
        expired_7_days = []

        for user in all_records:
            user_id = user.get('user_id')
            if not user_id:
                continue

            # Проверяем только НЕактивные подписки (уже истекли)
            is_sub_active = user.get('is_sub_active', 'False')
            if is_sub_active == 'True':
                continue

            sub_end_str = user.get('sub_end', '')
            if not sub_end_str:
                continue

            try:
                sub_end = datetime.strptime(sub_end_str, '%Y-%m-%d %H:%M:%S')
                sub_end_date = sub_end.date()

                # Сколько дней прошло с момента истечения
                days_since_expired = (current_date - sub_end_date).days

                # Ровно 3 дня назад
                if days_since_expired == 3:
                    expired_3_days.append(int(user_id))
                    print(f"📨 3 дня после истечения: {user_id}")

                # Ровно 7 дней назад
                elif days_since_expired == 7:
                    expired_7_days.append(int(user_id))
                    print(f"📨 7 дней после истечения: {user_id}")

            except ValueError as e:
                print(f"⚠️ Ошибка парсинга даты {sub_end_str} для {user_id}: {e}")
                continue

        print(f"📊 3 дня после: {len(expired_3_days)}, 7 дней после: {len(expired_7_days)}")

        return {
            'expired_3_days': expired_3_days,
            'expired_7_days': expired_7_days
        }

    except Exception as e:
        print(f"❌ Ошибка проверки истёкших подписок: {e}")
        return {
            'expired_3_days': [],
            'expired_7_days': []
        }


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def get_subscription_info_text(user_id: int) -> str:
    """
    Получить текстовое описание статуса подписки для пользователя
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
        return "ℹ️ Активной подписки ещё не было"
    else:
        return "⚠️ Не удалось проверить статус подписки"
