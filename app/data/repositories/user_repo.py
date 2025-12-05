"""
Реализация репозитория пользователей для Google Sheets
"""

import gspread
from datetime import datetime
from typing import List, Optional

from app.data.interfaces import IUserRepository
from app.database.connection import users_worksheet


class SheetsUserRepository(IUserRepository):
    """Реализация IUserRepository для Google Sheets"""

    def __init__(self):
        self.worksheet = users_worksheet

    def get(self, user_id: int) -> Optional[dict]:
        """
        Получить пользователя по ID

        Args:
            user_id: Telegram ID пользователя

        Returns:
            dict: Словарь с данными пользователя или None
        """
        try:
            cell = self.worksheet.find(str(user_id))
            if cell:
                row = self.worksheet.row_values(cell.row)
                headers = self.worksheet.row_values(1)
                return dict(zip(headers, row))
            return None
        except Exception as e:
            print(f"❌ Ошибка получения пользователя {user_id}: {e}")
            return None

    def get_all(self) -> List[dict]:
        """
        Получить всех пользователей

        Returns:
            list: Список словарей с данными пользователей
        """
        try:
            all_data = self.worksheet.get_all_records()
            users = []
            for row in all_data:
                user_id = row.get('user_id')
                if user_id:  # Пропускаем строки без user_id
                    try:
                        users.append({
                            'user_id': int(user_id),
                            **row
                        })
                    except ValueError:
                        print(f"⚠️ Некорректный user_id: {user_id}")
                        continue
            return users
        except Exception as e:
            print(f"❌ Ошибка загрузки пользователей: {e}")
            return []

    def create(self, user_id: int, username: str, first_name: str) -> bool:
        """
        Создать нового пользователя

        Args:
            user_id: Telegram ID
            username: Username в Telegram
            first_name: Имя пользователя

        Returns:
            bool: True если успешно, False если ошибка

        Структура колонок:
        A-M: user_id, username, first_name, joined_at, last_activity,
             is_vip, is_diamond, is_sub_active, sub_start, sub_end,
             last_updated_info, phone_number, email
        N: vote_response
        O: status
        P: first_room_visit
        Q: last_room_visit
        R: total_room_visits
        S-Z: touch_1_sent ... touch_8_sent
        """
        try:
            # Защита от дублей
            existing = self.worksheet.find(str(user_id))
            if existing:
                print(f"ℹ️ Пользователь {user_id} уже существует (строка {existing.row})")
                return False

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Новая строка с полной структурой
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
                '',              # N: vote_response
                'active',        # O: status
                '',              # P: first_room_visit
                '',              # Q: last_room_visit
                '0',             # R: total_room_visits
                '',              # S: touch_1_sent
                '',              # T: touch_2_sent
                '',              # U: touch_3_sent
                '',              # V: touch_4_sent
                '',              # W: touch_5_sent
                '',              # X: touch_6_sent
                '',              # Y: touch_7_sent
                '',              # Z: touch_8_sent
            ]

            self.worksheet.append_row(new_row)
            print(f"✅ Пользователь {user_id} добавлен в БД")
            return True
        except Exception as e:
            print(f"❌ Ошибка добавления пользователя {user_id}: {e}")
            return False

    def update(self, user_id: int, data: dict) -> bool:
        """
        Обновить данные пользователя

        Args:
            user_id: ID пользователя
            data: Словарь {название_поля: новое_значение}

        Returns:
            bool: True если успешно
        """
        try:
            cell = self.worksheet.find(str(user_id))
            if not cell:
                print(f"❌ Пользователь {user_id} не найден")
                return False

            headers = self.worksheet.row_values(1)
            update_data = []

            for field_name, new_value in data.items():
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
                self.worksheet.batch_update(update_data)
                print(f"✅ Обновление для {user_id}: {list(data.keys())}")
                return True
            else:
                print("⚠️ Нет данных для обновления")
                return False

        except Exception as e:
            print(f"❌ Ошибка обновления {user_id}: {e}")
            return False

    def get_by_status(self, status: str) -> List[dict]:
        """
        Получить пользователей по статусу

        Args:
            status: Статус (active, inactive, churned)

        Returns:
            list: Список пользователей с указанным статусом
        """
        try:
            all_users = self.get_all()
            return [user for user in all_users if user.get('status') == status]
        except Exception as e:
            print(f"❌ Ошибка получения пользователей по статусу {status}: {e}")
            return []

    def get_for_touchpoint(self, touch_number: int) -> List[dict]:
        """
        Получить пользователей для отправки touchpoint

        Args:
            touch_number: Номер touchpoint (1-8)

        Returns:
            list: Список пользователей готовых получить touchpoint

        NOTE: Заглушка, логика будет реализована в задаче 3.1
        """
        # TODO: Реализовать логику в задаче 3.1
        print(f"ℹ️ get_for_touchpoint({touch_number}): заглушка, вернёт пустой список")
        return []
