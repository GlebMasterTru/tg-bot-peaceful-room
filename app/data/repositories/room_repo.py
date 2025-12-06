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

    def get_all(self, is_active: bool = None) -> List[dict]:
        """
        Получить все комнаты

        Args:
            is_active: Фильтр по активности (None = все)

        Returns:
            list: Список комнат
        """
        try:
            all_records = self.worksheet.get_all_records()
            if is_active is None:
                return all_records
            else:
                return [
                    record for record in all_records
                    if record.get('is_active') == ('True' if is_active else 'False') or
                       record.get('is_active') is is_active
                ]
        except Exception as e:
            print(f"❌ Ошибка получения комнат: {e}")
            return []

    def register_room(
        self,
        room_id: str,
        room_name: str,
        room_url: str,
        access_level: str,
        is_active: bool
    ) -> bool:
        """
        Зарегистрировать новую комнату

        Args:
            room_id: ID комнаты
            room_name: Название комнаты
            room_url: URL комнаты
            access_level: Уровень доступа (free, subscriber, vip, diamond)
            is_active: Активна ли комната

        Returns:
            bool: True если успешно
        """
        try:
            # Проверка на дубли
            existing = self.get_by_id(room_id)
            if existing:
                print(f"ℹ️ Комната {room_id} уже зарегистрирована")
                return False

            new_row = [
                room_id,
                room_name,
                room_url,
                access_level,
                str(is_active)
            ]

            self.worksheet.append_row(new_row)
            print(f"✅ Комната {room_name} зарегистрирована")
            return True

        except Exception as e:
            print(f"❌ Ошибка регистрации комнаты: {e}")
            return False


# Глобальный экземпляр репозитория
room_repository = SheetsRoomRepository()
