"""
Реализация репозитория комнат для Google Sheets
"""

from typing import List, Optional

from app.data.interfaces import IRoomRepository
from app.database.connection import rooms_registry_worksheet


class SheetsRoomRepository(IRoomRepository):
    """Реализация IRoomRepository для Google Sheets"""

    def __init__(self):
        self.worksheet = rooms_registry_worksheet

    def get_all_active(self) -> List[dict]:
        """
        Получить все активные комнаты

        Returns:
            list: Список активных комнат
        """
        try:
            all_records = self.worksheet.get_all_records()
            active_rooms = [
                record for record in all_records
                if record.get('is_active') == 'True' or record.get('is_active') is True
            ]
            return active_rooms
        except Exception as e:
            print(f"❌ Ошибка получения активных комнат: {e}")
            return []

    def get_by_id(self, room_id: str) -> Optional[dict]:
        """
        Получить комнату по ID

        Args:
            room_id: ID комнаты

        Returns:
            dict: Данные комнаты или None
        """
        try:
            all_records = self.worksheet.get_all_records()
            for record in all_records:
                if record.get('room_id') == room_id:
                    return record
            return None
        except Exception as e:
            print(f"❌ Ошибка получения комнаты {room_id}: {e}")
            return None

    def get_tracking_url(self, room_id: str, user_id: int) -> str:
        """
        Получить tracking URL для комнаты

        Args:
            room_id: ID комнаты
            user_id: ID пользователя

        Returns:
            str: URL с параметром ?uid={user_id}
        """
        try:
            room = self.get_by_id(room_id)
            if not room:
                print(f"⚠️ Комната {room_id} не найдена")
                return ""

            room_url = room.get('room_url', '')
            if not room_url:
                print(f"⚠️ URL комнаты {room_id} пуст")
                return ""

            # Добавляем параметр ?uid=
            separator = '&' if '?' in room_url else '?'
            tracking_url = f"{room_url}{separator}uid={user_id}"

            print(f"✅ Сгенерирован tracking URL для комнаты {room_id} и пользователя {user_id}")
            return tracking_url

        except Exception as e:
            print(f"❌ Ошибка генерации tracking URL: {e}")
            return ""
