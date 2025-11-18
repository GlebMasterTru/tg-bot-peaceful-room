"""
Функции для работы с платежами и подписками
Интеграция с Tilda, обработка платежей
"""

from datetime import datetime
from typing import Tuple, List, Optional
from collections import defaultdict

from app.database.connection import tilda_worksheet
from app.database.users import (
    get_user,
    update_user_batch,
    add_user_with_subscription,
    add_user_to_diamond_list,
    users_worksheet
)


# ============================================================================
# УТИЛИТЫ ДЛЯ РАБОТЫ С USERNAME
# ============================================================================

def clean_telegram_username(raw_username: str) -> Optional[str]:
    """
    Очистить и нормализовать username из Tilda

    Args:
        raw_username: Username как введён в Tilda

    Returns:
        str: Очищенный username (без @, t.me/, etc.) или None

    Examples:
        '@username' -> 'username'
        'https://t.me/username' -> 'username'
        't.me/username?start=123' -> 'username'
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


def format_date_for_user(date_str: str) -> str:
    """
    Преобразовать дату из формата БД в человекочитаемый

    Args:
        date_str: Дата в формате 'YYYY-MM-DD HH:MM:SS'

    Returns:
        str: Дата в формате 'DD.MM.YYYY'
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        return date_obj.strftime('%d.%m.%Y')
    except Exception as e:
        print(f"⚠️ Ошибка форматирования даты {date_str}: {e}")
        return date_str


# ============================================================================
# ПРОВЕРКА СТАТУСА ПОДПИСКИ
# ============================================================================

def get_subscription_status(user_id: int) -> dict:
    """
    Получить детальный статус подписки пользователя

    Args:
        user_id: Telegram ID пользователя

    Returns:
        dict: {
            'status': 'active' | 'expired' | 'expiring_soon' | 'none' | 'error',
            'is_sub_active': bool,
            'end_date': str (DD.MM.YYYY),
            'end_date_raw': str (YYYY-MM-DD HH:MM:SS),
            'days_left': int
        }
    """
    try:
        user = get_user(user_id)

        if not user:
            return {
                'status': 'none',
                'is_sub_active': False,
                'end_date': None,
                'end_date_raw': None,
                'days_left': None
            }

        sub_end = user.get('sub_end', '')
        is_sub_active = user.get('is_sub_active', '')

        if not sub_end or not is_sub_active:
            return {
                'status': 'none',
                'is_sub_active': False,
                'end_date': None,
                'end_date_raw': None,
                'days_left': None
            }

        if is_sub_active == 'False':
            return {
                'status': 'expired',
                'is_sub_active': False,
                'end_date': format_date_for_user(sub_end),
                'end_date_raw': sub_end,
                'days_left': 0
            }

        if is_sub_active == 'True':
            try:
                end_date_obj = datetime.strptime(sub_end, '%Y-%m-%d %H:%M:%S')
                current_date = datetime.now()
                days_left = (end_date_obj - current_date).days

                if days_left > 3:
                    status = 'active'
                elif 1 <= days_left <= 3:
                    status = 'expiring_soon'
                else:
                    status = 'expired'

                return {
                    'status': status,
                    'is_sub_active': True,
                    'end_date': format_date_for_user(sub_end),
                    'end_date_raw': sub_end,
                    'days_left': days_left if days_left > 0 else 0
                }

            except ValueError as e:
                print(f"❌ Ошибка парсинга даты {sub_end}: {e}")
                return {
                    'status': 'error',
                    'is_sub_active': False,
                    'end_date': None,
                    'end_date_raw': sub_end,
                    'days_left': None
                }

        return {
            'status': 'unknown',
            'is_sub_active': False,
            'end_date': None,
            'end_date_raw': sub_end,
            'days_left': None
        }

    except Exception as e:
        print(f"❌ Ошибка проверки подписки {user_id}: {e}")
        return {
            'status': 'error',
            'is_sub_active': False,
            'end_date': None,
            'end_date_raw': None,
            'days_left': None
        }


# ============================================================================
# СИНХРОНИЗАЦИЯ ПЛАТЕЖЕЙ (вручную)
# ============================================================================

def sync_user_subscription(user_id: int, user_username: str) -> Tuple[bool, str, Optional[str]]:
    """
    Синхронизировать подписку пользователя с Tilda вручную

    Args:
        user_id: Telegram ID
        user_username: Username пользователя

    Returns:
        tuple: (success, message, end_date_str)
    """
    try:
        cleaned_username = clean_telegram_username(user_username)
        if not cleaned_username:
            return False, "Не удалось определить ваш username. Обратитесь в поддержку.", None

        print(f"🔍 Синхронизация для {cleaned_username} (ID: {user_id})")

        # Получаем необработанные записи
        all_tilda_records = tilda_worksheet.get_all_records()
        unprocessed_records = [
            record for record in all_tilda_records
            if not record.get('processed', '')
        ]

        if not unprocessed_records:
            return False, "Новых оплат не найдено.", None

        # Ищем записи пользователя
        user_records = []
        for record in unprocessed_records:
            record_username = clean_telegram_username(
                record.get('Как_с_вами_связаться_в_Телеграм_username', '')
            )

            if record_username == cleaned_username:
                user_records.append(record)

        if not user_records:
            return False, "Оплаты для вашего username не найдены.", None

        print(f"📋 Найдено {len(user_records)} записей для {cleaned_username}")

        # Извлекаем данные
        email = user_records[0].get('Email', '')
        phone = user_records[0].get('Phone', '')

        # Находим максимальную дату окончания
        max_end_date = None
        for record in user_records:
            end_date_str = record.get('valid to', '')
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')
                if max_end_date is None or end_date > max_end_date:
                    max_end_date = end_date
            except ValueError as e:
                print(f"⚠️ Ошибка парсинга даты {end_date_str}: {e}")
                continue

        if not max_end_date:
            return False, "Не удалось определить дату окончания подписки.", None

        tilda_start_date = user_records[0].get('Дата начала подписки', '')
        if not tilda_start_date:
            tilda_start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        tilda_max_end_date_str = max_end_date.strftime('%Y-%m-%d %H:%M:%S')
        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Проверяем существующего пользователя
        existing_user = get_user(user_id)

        if existing_user:
            # Обновляем существующего
            update_data = {
                'username': user_username,
                'last_activity': current_time_str,
                'is_diamond': 'True',
                'is_sub_active': 'True',
                'sub_start': tilda_start_date,
                'sub_end': tilda_max_end_date_str,
                'last_updated_info': current_time_str
            }

            if not existing_user.get('email') and email:
                update_data['email'] = email
            if not existing_user.get('phone') and phone:
                update_data['phone_number'] = phone

            success = update_user_batch(user_id, update_data)
            if not success:
                return False, "Ошибка при обновлении данных.", None

            message = f"✅ Ваша подписка обновлена! Активна до {max_end_date.strftime('%d.%m.%Y')}"

        else:
            # Добавляем нового пользователя
            new_user_data = {
                'user_id': str(user_id),
                'username': user_username,
                'email': email,
                'phone_number': phone,
                'sub_start': tilda_start_date,
                'sub_end': tilda_max_end_date_str,
                'is_sub_active': 'True',
                'joined_at': current_time_str,
                'last_activity': current_time_str
            }

            success = add_user_with_subscription(new_user_data)
            if not success:
                return False, "Ошибка при добавлении пользователя.", None

            message = f"🎉 Добро пожаловать! Ваша подписка активна до {max_end_date.strftime('%d.%m.%Y')}"

        # Помечаем записи как обработанные
        _mark_records_as_processed(user_records)

        print(f"✅ Синхронизация для {cleaned_username} завершена")
        return True, message, tilda_max_end_date_str

    except Exception as e:
        error_msg = f"❌ Ошибка синхронизации: {e}"
        print(error_msg)
        return False, "Произошла ошибка. Попробуйте позже.", None


# ============================================================================
# АВТОМАТИЧЕСКАЯ ОБРАБОТКА ПЛАТЕЖЕЙ (фоновая задача)
# ============================================================================

def process_all_pending_payments() -> List[int]:
    """
    Обработать все необработанные платежи из Tilda

    Returns:
        list: Список user_id для отправки уведомлений
    """
    try:
        all_tilda_records = tilda_worksheet.get_all_records()
        unprocessed_records = [
            record for record in all_tilda_records
            if not record.get('processed', '')
        ]

        if not unprocessed_records:
            print("ℹ️ Нет необработанных оплат")
            return []

        print(f"📋 Найдено {len(unprocessed_records)} необработанных оплат")

        notified_users = []

        # Группируем по username
        records_by_username = defaultdict(list)
        for record in unprocessed_records:
            username = clean_telegram_username(
                record.get('Как_с_вами_связаться_в_Телеграм_username', '')
            )
            if username:
                records_by_username[username].append(record)

        # Обрабатываем каждого пользователя
        for username, user_records in records_by_username.items():
            print(f"🔍 Обработка для {username}")

            # Ищем user_id по username
            user = _find_user_by_username(username)
            if not user:
                print(f"⚠️ Пользователь {username} не найден в БД")
                continue

            user_id = user.get('user_id')
            if not user_id:
                print(f"⚠️ У пользователя {username} нет user_id")
                continue

            # Обрабатываем платёж
            success = _process_user_payment(user, user_records)
            if success:
                add_user_to_diamond_list(user_id)
                notified_users.append(user_id)
                print(f"✅ Обработан {username} (ID: {user_id})")

            # Помечаем записи как обработанные
            _mark_records_as_processed(user_records)

        print(f"✅ Обработано {len(notified_users)} платежей")
        return notified_users

    except Exception as e:
        print(f"❌ Ошибка обработки платежей: {e}")
        return []


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (приватные)
# ============================================================================

def _find_user_by_username(username: str) -> Optional[dict]:
    """Найти пользователя по username"""
    try:
        all_users = users_worksheet.get_all_records()
        for u in all_users:
            user_username = clean_telegram_username(u.get('username', ''))
            if user_username == username:
                return u
        return None
    except Exception as e:
        print(f"❌ Ошибка поиска пользователя {username}: {e}")
        return None


def _process_user_payment(user: dict, user_records: list) -> bool:
    """Обработать платёж пользователя"""
    try:
        email = user_records[0].get('Email', '')
        phone = user_records[0].get('Phone', '')

        # Находим максимальную дату
        max_end_date = None
        for record in user_records:
            end_date_str = record.get('valid to', '')
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')
                if max_end_date is None or end_date > max_end_date:
                    max_end_date = end_date
            except ValueError:
                continue

        if not max_end_date:
            print(f"⚠️ Не удалось определить дату окончания")
            return False

        tilda_start_date = user_records[0].get('Дата начала подписки', '')
        if not tilda_start_date:
            tilda_start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        tilda_max_end_date_str = max_end_date.strftime('%Y-%m-%d %H:%M:%S')
        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        username = user.get('username', '')
        user_id = user.get('user_id')

        # Обновляем пользователя
        update_data = {
            'username': f"@{username}" if not username.startswith('@') else username,
            'last_activity': current_time_str,
            'is_diamond': 'True',
            'is_sub_active': 'True',
            'sub_start': tilda_start_date,
            'sub_end': tilda_max_end_date_str,
            'last_updated_info': current_time_str
        }

        if not user.get('email') and email:
            update_data['email'] = email
        if not user.get('phone_number') and phone:
            update_data['phone_number'] = phone

        return update_user_batch(user_id, update_data)

    except Exception as e:
        print(f"❌ Ошибка обработки платежа: {e}")
        return False


def _mark_records_as_processed(user_records: list):
    """Пометить записи в Tilda как обработанные"""
    try:
        processed_updates = []

        for record in user_records:
            try:
                username_to_find = record['Как_с_вами_связаться_в_Телеграм_username']
                expected_email = record.get('Email', '')
                expected_valid_to = record.get('valid to', '')

                cells = tilda_worksheet.findall(username_to_find)

                for cell in cells:
                    row_data = tilda_worksheet.row_values(cell.row)

                    actual_email = row_data[1] if len(row_data) > 1 else ''
                    actual_valid_to = row_data[17] if len(row_data) > 17 else ''

                    if (expected_email and actual_email == expected_email and
                            expected_valid_to and actual_valid_to == expected_valid_to):

                        processed_updates.append({
                            'range': f"T{cell.row}",
                            'values': [['TRUE']]
                        })
                        print(f"✅ Помечена строка {cell.row}")
                        break

            except Exception as e:
                print(f"❌ Ошибка при пометке записи: {e}")
                continue

        if processed_updates:
            tilda_worksheet.batch_update(processed_updates)

    except Exception as e:
        print(f"❌ Ошибка пометки записей: {e}")
