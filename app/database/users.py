"""
Функции для работы с пользователями
Все операции CRUD для таблицы users
"""

import gspread
from datetime import datetime
from typing import Optional, Tuple, List, Dict

from app.database.connection import users_worksheet, config_worksheet
from app.database.models import User, RoomLinks


# ============================================================================
# ЧТЕНИЕ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================================

def get_user(user_id: int) -> Optional[dict]:
    """
    Получить данные пользователя по user_id

    Args:
        user_id: Telegram ID пользователя

    Returns:
        dict: Словарь с данными пользователя или None
    """
    try:
        cell = users_worksheet.find(str(user_id))
        if cell:
            row = users_worksheet.row_values(cell.row)
            headers = users_worksheet.row_values(1)
            return dict(zip(headers, row))
        return None
    except Exception as e:
        print(f"❌ Ошибка получения пользователя {user_id}: {e}")
        return None


def get_all_users() -> List[dict]:
    """
    Получить всех пользователей из БД

    Returns:
        list: Список словарей с данными пользователей
    """
    print("📥 Загрузка пользователей из БД...")

    try:
        all_data = users_worksheet.get_all_records()

        users = []
        for row in all_data:
            user_id = row.get('user_id')
            if user_id:  # Пропускаем строки без user_id
                try:
                    users.append({
                        'user_id': int(user_id),
                        'username': row.get('username', ''),
                        'first_name': row.get('first_name', '')
                    })
                except ValueError:
                    print(f"⚠️ Некорректный user_id: {user_id}")
                    continue

        print(f"✅ Загружено {len(users)} пользователей")
        return users

    except Exception as e:
        print(f"❌ Ошибка загрузки пользователей: {e}")
        return []


# ============================================================================
# СОЗДАНИЕ И ОБНОВЛЕНИЕ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================================

def add_user(user_id: int, username: str, first_name: str) -> bool:
    """
    Добавить нового пользователя в БД

    Args:
        user_id: Telegram ID
        username: Username в Telegram
        first_name: Имя пользователя

    Returns:
        bool: True если успешно, False если ошибка (или уже существует)

    Колонки таблицы (14 штук):
        A: user_id, B: username, C: first_name, D: joined_at, E: last_activity,
        F: is_vip, G: is_diamond, H: is_sub_active, I: sub_start, J: sub_end,
        K: last_updated_info, L: phone_number, M: email, N: Ручное примечание
    """
    try:
        # Защита от дублей: проверяем существование прямо перед добавлением
        existing = users_worksheet.find(str(user_id))
        if existing:
            print(f"ℹ️ Пользователь {user_id} уже существует (строка {existing.row})")
            return False
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Все 14 колонок в правильном порядке
        new_row = [
            str(user_id),    # A: user_id
            username,        # B: username
            first_name,      # C: first_name
            current_time,    # D: joined_at
            current_time,    # E: last_activity
            'False',         # F: is_vip
            'False',         # G: is_diamond
            'False',         # H: is_sub_active
            '',              # I: sub_start
            '',              # J: sub_end
            current_time,    # K: last_updated_info
            '',              # L: phone_number
            '',              # M: email
            ''               # N: Ручное примечание
        ]
        users_worksheet.append_row(new_row)
        print(f"✅ Пользователь {user_id} добавлен в БД")
        return True
    except Exception as e:
        print(f"❌ Ошибка добавления пользователя {user_id}: {e}")
        return False


def add_user_with_subscription(user_data: dict) -> bool:
    """
    Добавить пользователя с подпиской (из Tilda)

    Args:
        user_data: Словарь с полными данными пользователя

    Returns:
        bool: True если успешно
    """
    try:
        headers = users_worksheet.row_values(1)
        new_row = []
        for header in headers:
            value = user_data.get(header, '')
            new_row.append(str(value))

        users_worksheet.append_row(new_row)
        print(f"✅ Пользователь {user_data.get('username', '')} добавлен с подпиской")
        return True
    except Exception as e:
        print(f"❌ Ошибка добавления пользователя с подпиской: {e}")
        return False


def update_user_batch(user_id: int, update_dict: dict) -> bool:
    """
    Пакетное обновление полей пользователя

    Args:
        user_id: ID пользователя
        update_dict: Словарь {название_поля: новое_значение}

    Returns:
        bool: True если успешно

    Example:
        update_user_batch(123, {
            'is_diamond': 'True',
            'sub_end': '2025-12-31 23:59:59'
        })
    """
    try:
        cell = users_worksheet.find(str(user_id))
        if not cell:
            print(f"❌ Пользователь {user_id} не найден")
            return False

        headers = users_worksheet.row_values(1)
        update_data = []

        for field_name, new_value in update_dict.items():
            if field_name in headers:
                col_index = headers.index(field_name) + 1
                cell_range = gspread.utils.rowcol_to_a1(cell.row, col_index)

                update_data.append({
                    'range': cell_range,
                    'values': [[str(new_value)]]
                })
            else:
                print(f"⚠️ Столбец '{field_name}' не найден")

        if update_data:
            users_worksheet.batch_update(update_data)
            print(f"✅ Пакетное обновление для {user_id}: {list(update_dict.keys())}")
            return True
        else:
            print("⚠️ Нет данных для обновления")
            return False

    except Exception as e:
        print(f"❌ Ошибка пакетного обновления {user_id}: {e}")
        return False


# ============================================================================
# ПРИВИЛЕГИИ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================================

def get_user_privileges(user_id: int) -> Tuple[bool, bool]:
    """
    Проверить VIP и Diamond статусы пользователя

    Args:
        user_id: Telegram ID пользователя

    Returns:
        tuple: (is_vip, is_diamond)
    """
    try:
        user_id_str = str(user_id)

        # Проверяем VIP список в config
        vip_list = [
            id.strip()
            for id in (config_worksheet.acell('D2').value or "").split(',')
            if id.strip()
        ]
        is_vip = user_id_str in vip_list

        # Проверяем Diamond в профиле пользователя
        user = get_user(user_id)
        if user:
            is_diamond_value = user.get('is_diamond', 'False')
            is_diamond = (is_diamond_value == 'True')
        else:
            is_diamond = False

        return is_vip, is_diamond

    except Exception as e:
        print(f"❌ Ошибка проверки привилегий {user_id}: {e}")
        return False, False


def add_user_to_diamond_list(user_id: int) -> bool:
    """
    Добавить пользователя в Diamond список (config E2)

    Args:
        user_id: Telegram ID

    Returns:
        bool: True если успешно
    """
    try:
        user_id_str = str(user_id)

        diamond_list_str = config_worksheet.acell('E2').value or ""
        diamond_list = [
            id.strip()
            for id in diamond_list_str.split(',')
            if id.strip()
        ]

        if user_id_str not in diamond_list:
            diamond_list.append(user_id_str)
            config_worksheet.update('E2', [[','.join(diamond_list)]])
            print(f"✅ Пользователь {user_id} добавлен в Diamond список")
            return True
        else:
            print(f"ℹ️ Пользователь {user_id} уже в Diamond списке")
            return True

    except Exception as e:
        print(f"❌ Ошибка добавления в Diamond список {user_id}: {e}")
        return False


# ============================================================================
# ССЫЛКИ НА КОМНАТЫ
# ============================================================================

def get_links() -> Tuple[str, str, str]:
    """
    Получить ссылки на комнаты из конфига

    Returns:
        tuple: (main_link, vip_link, diamond_link)
    """
    try:
        main_link = config_worksheet.acell('A2').value or ""
        vip_link = config_worksheet.acell('B2').value or ""
        diamond_link = config_worksheet.acell('C2').value or ""
        return main_link, vip_link, diamond_link
    except Exception as e:
        print(f"❌ Ошибка получения ссылок: {e}")
        return "", "", ""


# ============================================================================
# МИГРАЦИЯ VIP ПОЛЬЗОВАТЕЛЕЙ (username → user_id)
# ============================================================================

def is_temporarily_vip_user(username: str) -> bool:
    """
    Проверить, есть ли username во временном VIP списке

    Args:
        username: Username пользователя (с @ или без)

    Returns:
        bool: True если в списке
    """
    try:
        temp_vip_str = config_worksheet.acell('F2').value or ""
        temp_vip_list = [
            name.strip().lower()
            for name in temp_vip_str.split(',')
            if name.strip()
        ]

        user_username = (username or "").lower().lstrip('@')
        return user_username in temp_vip_list

    except Exception as e:
        print(f"❌ Ошибка проверки временного VIP {username}: {e}")
        return False


def migrate_single_user(username: str, user_id: int) -> bool:
    """
    Перенести одного пользователя из временного VIP в основной

    Args:
        username: Username пользователя
        user_id: Telegram ID

    Returns:
        bool: True если успешно перенесён
    """
    try:
        # Получаем списки
        vip_list_str = config_worksheet.acell('D2').value or ""
        vip_list = [id.strip() for id in vip_list_str.split(',') if id.strip()]

        temp_vip_str = config_worksheet.acell('F2').value or ""
        temp_vip = [name.strip().lower() for name in temp_vip_str.split(',') if name.strip()]

        user_username = username.lower().lstrip('@')

        if user_username in temp_vip:
            user_id_str = str(user_id)

            # Добавляем в основной список
            if user_id_str not in vip_list:
                vip_list.append(user_id_str)

            # Удаляем из временного
            temp_vip.remove(user_username)

            # Обновляем в Sheets
            config_worksheet.update('D2', [[','.join(vip_list)]])
            config_worksheet.update('F2', [[','.join(temp_vip)]])

            print(f"✅ Пользователь {username} ({user_id}) мигрирован в VIP")
            return True

        return False

    except Exception as e:
        print(f"❌ Ошибка миграции {username}: {e}")
        return False


def migrate_many_users() -> bool:
    """
    Перенести всех пользователей из временного VIP списка

    Returns:
        bool: True если успешно
    """
    try:
        all_users = users_worksheet.get_all_records()

        vip_list_str = config_worksheet.acell('D2').value or ""
        vip_list = [id.strip() for id in vip_list_str.split(',') if id.strip()]

        temp_vip_str = config_worksheet.acell('F2').value or ""
        temp_vip = [name.strip().lower() for name in temp_vip_str.split(',') if name.strip()]

        migrated_count = 0
        updated_vip = vip_list.copy()
        updated_temp = temp_vip.copy()

        for user in all_users:
            user_id = user.get('user_id')
            if not user_id:
                continue

            username = (user.get('username', '') or '').lstrip('@').lower()

            if username in updated_temp:
                user_id_str = str(user_id)

                if user_id_str not in updated_vip:
                    updated_vip.append(user_id_str)
                    migrated_count += 1

                updated_temp.remove(username)

        if migrated_count > 0:
            config_worksheet.update('D2', [[','.join(updated_vip)]])
            config_worksheet.update('F2', [[','.join(updated_temp)]])

        if migrated_count == 1:
            print(f'✅ Мигрирован {migrated_count} пользователь')
        elif 2 <= migrated_count <= 4:
            print(f'✅ Мигрировано {migrated_count} пользователя')
        elif migrated_count >= 5:
            print(f'✅ Мигрировано {migrated_count} пользователей')
        else:
            print('ℹ️ Нет пользователей для миграции')

        return True

    except Exception as e:
        print(f"❌ Ошибка массовой миграции: {e}")
        return False


def sync_is_vip_for_all_users() -> bool:
    """
    Синхронизировать is_vip колонку со списком в config

    Returns:
        bool: True если успешно
    """
    try:
        vip_list_str = config_worksheet.acell('D2').value or ""
        vip_list = [id.strip() for id in vip_list_str.split(',') if id.strip()]

        all_users = users_worksheet.get_all_records()

        updates = []
        synced_count = 0

        for idx, user in enumerate(all_users, start=2):
            user_id = str(user.get('user_id', ''))
            current_is_vip = user.get('is_vip', '')

            should_be_vip = 'True' if user_id in vip_list else 'False'

            if current_is_vip != should_be_vip:
                updates.append({
                    'range': f'F{idx}',  # Столбец F - is_vip
                    'values': [[should_be_vip]]
                })
                synced_count += 1

        if updates:
            users_worksheet.batch_update(updates)
            print(f"✅ Синхронизировано is_vip для {synced_count} пользователей")
        else:
            print("ℹ️ is_vip актуален для всех пользователей")

        return True

    except Exception as e:
        print(f"❌ Ошибка синхронизации is_vip: {e}")
        return False


# ============================================================================
# ГОЛОСОВАНИЕ
# ============================================================================

def save_vote(user_id: int, vote_value: str) -> bool:
    """
    Сохранить голос пользователя

    Args:
        user_id: Telegram ID пользователя
        vote_value: Значение голоса ('1', '2', или '3')

    Returns:
        bool: True если успешно
    """
    try:
        headers = users_worksheet.row_values(1)

        # Проверяем есть ли колонка vote_dec_2025
        if 'vote_dec_2025' not in headers:
            print("⚠️ Колонка 'vote_dec_2025' не найдена в таблице!")
            print("   Добавьте колонку O: vote_dec_2025 в Google Sheets")
            return False

        # Обновляем голос
        return update_user_batch(user_id, {'vote_dec_2025': vote_value})

    except Exception as e:
        print(f"❌ Ошибка сохранения голоса {user_id}: {e}")
        return False


def get_vote_stats() -> dict:
    """
    Получить статистику голосования

    Returns:
        dict: {'1': count, '2': count, '3': count, 'total': count, 'not_voted': count}
    """
    try:
        all_users = users_worksheet.get_all_records()

        stats = {
            '1': 0,
            '2': 0,
            '3': 0,
            'total': 0,
            'not_voted': 0
        }

        for user in all_users:
            vote = user.get('vote_dec_2025', '')

            if vote in ['1', '2', '3']:
                stats[vote] += 1
                stats['total'] += 1
            else:
                stats['not_voted'] += 1

        return stats

    except Exception as e:
        print(f"❌ Ошибка получения статистики голосов: {e}")
        return {'1': 0, '2': 0, '3': 0, 'total': 0, 'not_voted': 0}
