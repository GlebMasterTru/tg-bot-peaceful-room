"""
Data Layer - слой абстракции между бизнес-логикой и хранилищем данных

Инициализация репозиториев для использования в приложении
"""

from app.data.repositories.user_repo import SheetsUserRepository
from app.data.repositories.room_visit_repo import SheetsRoomVisitRepository
from app.data.repositories.touchpoint_repo import SheetsTouchpointRepository
from app.data.repositories.room_repo import SheetsRoomRepository


# Глобальные экземпляры репозиториев
user_repo = SheetsUserRepository()
room_visit_repo = SheetsRoomVisitRepository()
touchpoint_repo = SheetsTouchpointRepository()
room_repo = SheetsRoomRepository()


__all__ = [
    'user_repo',
    'room_visit_repo',
    'touchpoint_repo',
    'room_repo',
]
