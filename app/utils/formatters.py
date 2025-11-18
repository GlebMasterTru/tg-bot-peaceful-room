"""
Утилиты для форматирования данных
Функции общего назначения для преобразования форматов
"""

from datetime import datetime
from typing import Optional


def format_date_for_user(date_str: str) -> str:
    """
    Преобразовать дату из формата БД в человекочитаемый

    Args:
        date_str: Дата в формате 'YYYY-MM-DD HH:MM:SS'

    Returns:
        str: Дата в формате 'DD.MM.YYYY'

    Examples:
        >>> format_date_for_user('2025-12-31 23:59:59')
        '31.12.2025'
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        return date_obj.strftime('%d.%m.%Y')
    except Exception as e:
        print(f"⚠️ Ошибка форматирования даты {date_str}: {e}")
        return date_str  # Возвращаем как есть


def get_days_word(days: int) -> str:
    """
    Получить правильное склонение слова "день"

    Args:
        days: Количество дней

    Returns:
        str: 'день', 'дня' или 'дней'

    Examples:
        >>> get_days_word(1)
        'день'
        >>> get_days_word(2)
        'дня'
        >>> get_days_word(5)
        'дней'
    """
    if days == 1 or (days % 10 == 1 and days % 100 != 11):
        return "день"
    elif 2 <= days % 10 <= 4 and (days % 100 < 10 or days % 100 >= 20):
        return "дня"
    else:
        return "дней"


def clean_telegram_username(raw_username: str) -> Optional[str]:
    """
    Очистить и нормализовать username из Tilda

    Args:
        raw_username: Username как введён в Tilda

    Returns:
        str: Очищенный username (без @, t.me/, etc.) или None

    Examples:
        >>> clean_telegram_username('@username')
        'username'
        >>> clean_telegram_username('https://t.me/username')
        'username'
        >>> clean_telegram_username('t.me/username?start=123')
        'username'
    """
    if not raw_username:
        return None

    username = str(raw_username).strip().lower()

    # Убираем @
    if username.startswith('@'):
        username = username[1:]

    # Убираем t.me/
    if 't.me/' in username:
        username = username.split('t.me/')[-1]

    if 'https://t.me/' in username:
        username = username.split('https://t.me/')[-1]

    # Убираем query параметры (например, ?start=123)
    username = username.split('?')[0].rstrip('/')

    return username


def format_user_count(count: int) -> str:
    """
    Форматировать число пользователей с правильным склонением

    Args:
        count: Количество пользователей

    Returns:
        str: Строка вида "5 пользователей"

    Examples:
        >>> format_user_count(1)
        '1 пользователь'
        >>> format_user_count(2)
        '2 пользователя'
        >>> format_user_count(10)
        '10 пользователей'
    """
    if count % 10 == 1 and count % 100 != 11:
        word = "пользователь"
    elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
        word = "пользователя"
    else:
        word = "пользователей"

    return f"{count} {word}"


# ============================================================================
# ПРИМЕЧАНИЯ ПО ИСПОЛЬЗОВАНИЮ
# ============================================================================

"""
Как использовать:

В handlers.py:
    from app.utils.formatters import format_date_for_user, get_days_word

    sub_info = get_subscription_status(user_id)
    formatted_date = format_date_for_user(sub_info['end_date_raw'])
    days_word = get_days_word(sub_info['days_left'])

    text = f"Ваша подписка истекает через {sub_info['days_left']} {days_word}"

В database/payments.py:
    from app.utils.formatters import clean_telegram_username

    username = clean_telegram_username('@username')

Преимущества централизации:
- Одна функция используется везде (нет дублирования)
- Легко исправить баг в одном месте
- Легко добавлять новые утилиты
"""
