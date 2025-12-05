"""
Реализация репозитория посещений комнат для Google Sheets
"""

from datetime import datetime
from typing import List, Optional

from app.data.interfaces import IRoomVisitRepository
from app.database.connection import room_visits_worksheet, users_worksheet


class SheetsRoomVisitRepository(IRoomVisitRepository):
    """Реализация IRoomVisitRepository для Google Sheets"""

    def __init__(self):
        self.worksheet = room_visits_worksheet
        self.users_worksheet = users_worksheet

    def log_visit(
        self,
        user_id: int,
        username: str,
        room_id: str,
        room_name: str,
        source: str
    ) -> bool:
        """
        Записать посещение комнаты

        Args:
            user_id: ID пользователя
            username: Username пользователя
            room_id: ID комнаты
            room_name: Название комнаты
            source: Источник (touchpoint_1, direct, etc)

        Returns:
            bool: True если успешно
        """
        try:
            # 1. Генерируем ID (max + 1)
            all_visits = self.worksheet.get_all_values()
            if len(all_visits) > 1:  # Есть записи кроме заголовка
                ids = [int(row[0]) for row in all_visits[1:] if row and row[0].isdigit()]
                next_id = max(ids) + 1 if ids else 1
            else:
                next_id = 1

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 2. Записываем посещение
            new_row = [
                str(next_id),
                current_time,
                str(user_id),
                username,
                room_id,
                room_name,
                source
            ]
            self.worksheet.append_row(new_row)
            print(f"✅ Записано посещение комнаты {room_name} пользователем {user_id}")

            # 3. Обновляем данные пользователя в users
            self._update_user_visit_stats(user_id, current_time)

            return True
        except Exception as e:
            print(f"❌ Ошибка записи посещения: {e}")
            return False

    def _update_user_visit_stats(self, user_id: int, visit_time: str) -> bool:
        """Обновить статистику посещений в таблице users"""
        try:
            # Находим пользователя
            cell = self.users_worksheet.find(str(user_id))
            if not cell:
                print(f"⚠️ Пользователь {user_id} не найден для обновления статистики")
                return False

            headers = self.users_worksheet.row_values(1)
            row_data = self.users_worksheet.row_values(cell.row)
            user_dict = dict(zip(headers, row_data))

            # Получаем текущие значения
            first_visit = user_dict.get('first_room_visit', '')
            total_visits = int(user_dict.get('total_room_visits', 0) or 0)

            # Обновляем
            updates = []

            # Если first_room_visit пусто — заполнить
            if not first_visit:
                first_visit_col = headers.index('first_room_visit') + 1
                updates.append({
                    'range': f'{chr(64 + first_visit_col)}{cell.row}',
                    'values': [[visit_time]]
                })

            # Обновить last_room_visit
            last_visit_col = headers.index('last_room_visit') + 1
            updates.append({
                'range': f'{chr(64 + last_visit_col)}{cell.row}',
                'values': [[visit_time]]
            })

            # Увеличить total_room_visits
            total_visits_col = headers.index('total_room_visits') + 1
            updates.append({
                'range': f'{chr(64 + total_visits_col)}{cell.row}',
                'values': [[str(total_visits + 1)]]
            })

            if updates:
                self.users_worksheet.batch_update(updates)
                print(f"✅ Обновлена статистика посещений для пользователя {user_id}")

            return True
        except Exception as e:
            print(f"❌ Ошибка обновления статистики пользователя {user_id}: {e}")
            return False

    def get_by_user(self, user_id: int) -> List[dict]:
        """
        Получить все посещения пользователя

        Args:
            user_id: ID пользователя

        Returns:
            list: Список посещений
        """
        try:
            all_records = self.worksheet.get_all_records()
            user_visits = [
                record for record in all_records
                if record.get('user_id') == user_id or str(record.get('user_id')) == str(user_id)
            ]
            return user_visits
        except Exception as e:
            print(f"❌ Ошибка получения посещений пользователя {user_id}: {e}")
            return []

    def get_last_visit(self, user_id: int) -> Optional[dict]:
        """
        Получить последнее посещение пользователя

        Args:
            user_id: ID пользователя

        Returns:
            dict: Последнее посещение или None
        """
        try:
            visits = self.get_by_user(user_id)
            if visits:
                # Сортируем по timestamp в обратном порядке
                visits_sorted = sorted(visits, key=lambda x: x.get('timestamp', ''), reverse=True)
                return visits_sorted[0]
            return None
        except Exception as e:
            print(f"❌ Ошибка получения последнего посещения {user_id}: {e}")
            return None
