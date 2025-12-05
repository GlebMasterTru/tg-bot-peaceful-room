"""
Абстрактные интерфейсы для репозиториев
Определяют контракт между бизнес-логикой и хранилищем данных
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class IUserRepository(ABC):
    """Интерфейс репозитория пользователей"""

    @abstractmethod
    def get(self, user_id: int) -> Optional[dict]:
        """Получить пользователя по ID"""
        pass

    @abstractmethod
    def get_all(self) -> List[dict]:
        """Получить всех пользователей"""
        pass

    @abstractmethod
    def create(self, user_id: int, username: str, first_name: str) -> bool:
        """Создать нового пользователя"""
        pass

    @abstractmethod
    def update(self, user_id: int, data: dict) -> bool:
        """Обновить данные пользователя"""
        pass

    @abstractmethod
    def get_by_status(self, status: str) -> List[dict]:
        """Получить пользователей по статусу"""
        pass

    @abstractmethod
    def get_for_touchpoint(self, touch_number: int) -> List[dict]:
        """Получить пользователей для отправки touchpoint"""
        pass


class IRoomVisitRepository(ABC):
    """Интерфейс репозитория посещений комнат"""

    @abstractmethod
    def log_visit(
        self,
        user_id: int,
        username: str,
        room_id: str,
        room_name: str,
        source: str
    ) -> bool:
        """Записать посещение комнаты"""
        pass

    @abstractmethod
    def get_by_user(self, user_id: int) -> List[dict]:
        """Получить все посещения пользователя"""
        pass

    @abstractmethod
    def get_last_visit(self, user_id: int) -> Optional[dict]:
        """Получить последнее посещение пользователя"""
        pass


class ITouchpointRepository(ABC):
    """Интерфейс репозитория точек касания"""

    @abstractmethod
    def log_touchpoint(
        self,
        user_id: int,
        username: str,
        touch_number: int,
        status: str,
        error_message: str = None
    ) -> bool:
        """Записать отправку touchpoint"""
        pass

    @abstractmethod
    def mark_clicked(self, user_id: int, touch_number: int) -> bool:
        """Отметить touchpoint как кликнутый"""
        pass

    @abstractmethod
    def get_by_user(self, user_id: int) -> List[dict]:
        """Получить все touchpoints пользователя"""
        pass


class IRoomRepository(ABC):
    """Интерфейс репозитория комнат"""

    @abstractmethod
    def get_all_active(self) -> List[dict]:
        """Получить все активные комнаты"""
        pass

    @abstractmethod
    def get_by_id(self, room_id: str) -> Optional[dict]:
        """Получить комнату по ID"""
        pass

    @abstractmethod
    def get_tracking_url(self, room_id: str, user_id: int) -> str:
        """Получить tracking URL для комнаты"""
        pass
