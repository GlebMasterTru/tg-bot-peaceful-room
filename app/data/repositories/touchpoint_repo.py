"""
Реализация репозитория точек касания (touchpoints) для Google Sheets
"""

from datetime import datetime
from typing import List, Optional

from app.data.interfaces import ITouchpointRepository
from app.database.connection import touchpoints_log_worksheet, users_worksheet


class SheetsTouchpointRepository(ITouchpointRepository):
    """Реализация ITouchpointRepository для Google Sheets"""

    def __init__(self):
        self.worksheet = touchpoints_log_worksheet
        self.users_worksheet = users_worksheet

    def log_touchpoint(
        self,
        user_id: int,
        username: str,
        touch_number: int,
        status: str,
        error_message: str = None
    ) -> bool:
        """
        Записать отправку touchpoint

        Args:
            user_id: ID пользователя
            username: Username пользователя
            touch_number: Номер touchpoint (1-8)
            status: Статус (sent, failed)
            error_message: Сообщение об ошибке (опционально)

        Returns:
            bool: True если успешно
        """
        try:
            # 1. Генерируем ID
            all_touchpoints = self.worksheet.get_all_values()
            if len(all_touchpoints) > 1:  # Есть записи кроме заголовка
                ids = [int(row[0]) for row in all_touchpoints[1:] if row and row[0].isdigit()]
                next_id = max(ids) + 1 if ids else 1
            else:
                next_id = 1

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 2. Записываем touchpoint
            new_row = [
                str(next_id),
                current_time,
                str(user_id),
                username,
                str(touch_number),
                status,
                error_message or '',
                ''  # clicked (пусто по умолчанию)
            ]
            self.worksheet.append_row(new_row)
            print(f"✅ Записан touchpoint #{touch_number} для пользователя {user_id} (статус: {status})")

            # 3. Обновляем в users: touch_N_sent = timestamp
            if status == 'sent':
                self._update_user_touchpoint_timestamp(user_id, touch_number, current_time)

            return True
        except Exception as e:
            print(f"❌ Ошибка записи touchpoint: {e}")
            return False

    def _update_user_touchpoint_timestamp(self, user_id: int, touch_number: int, timestamp: str) -> bool:
        """Обновить timestamp отправки touchpoint в таблице users"""
        try:
            cell = self.users_worksheet.find(str(user_id))
            if not cell:
                print(f"⚠️ Пользователь {user_id} не найден для обновления touchpoint")
                return False

            headers = self.users_worksheet.row_values(1)
            field_name = f'touch_{touch_number}_sent'

            if field_name in headers:
                col_index = headers.index(field_name) + 1
                cell_address = f'{chr(64 + col_index)}{cell.row}'
                self.users_worksheet.update(cell_address, [[timestamp]])
                print(f"✅ Обновлён {field_name} для пользователя {user_id}")
                return True
            else:
                print(f"⚠️ Колонка {field_name} не найдена в таблице")
                return False

        except Exception as e:
            print(f"❌ Ошибка обновления touchpoint timestamp для {user_id}: {e}")
            return False

    def mark_clicked(self, user_id: int, touch_number: int) -> bool:
        """
        Отметить touchpoint как кликнутый

        Args:
            user_id: ID пользователя
            touch_number: Номер touchpoint (1-8)

        Returns:
            bool: True если успешно
        """
        try:
            # Находим запись touchpoint
            all_records = self.worksheet.get_all_records()

            # Ищем последний отправленный touchpoint для этого пользователя
            matching_rows = []
            for idx, record in enumerate(all_records, start=2):  # +2 т.к. строка 1 = заголовок
                if (str(record.get('user_id')) == str(user_id) and
                    str(record.get('touch_number')) == str(touch_number) and
                    record.get('status') == 'sent'):
                    matching_rows.append(idx)

            if not matching_rows:
                print(f"⚠️ Touchpoint #{touch_number} для {user_id} не найден")
                return False

            # Берём последнюю запись (самую свежую)
            row_to_update = matching_rows[-1]
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Обновляем колонку clicked
            headers = self.worksheet.row_values(1)
            if 'clicked' in headers:
                clicked_col = headers.index('clicked') + 1
                cell_address = f'{chr(64 + clicked_col)}{row_to_update}'
                self.worksheet.update(cell_address, [[current_time]])
                print(f"✅ Touchpoint #{touch_number} отмечен как кликнутый для {user_id}")
                return True
            else:
                print("⚠️ Колонка 'clicked' не найдена")
                return False

        except Exception as e:
            print(f"❌ Ошибка отметки клика для touchpoint: {e}")
            return False

    def get_by_user(self, user_id: int) -> List[dict]:
        """
        Получить все touchpoints пользователя

        Args:
            user_id: ID пользователя

        Returns:
            list: Список touchpoints
        """
        try:
            all_records = self.worksheet.get_all_records()
            user_touchpoints = [
                record for record in all_records
                if str(record.get('user_id')) == str(user_id)
            ]
            return user_touchpoints
        except Exception as e:
            print(f"❌ Ошибка получения touchpoints пользователя {user_id}: {e}")
            return []


# Глобальный экземпляр репозитория
touchpoint_repository = SheetsTouchpointRepository()
