"""
Модели данных для Data Layer
Расширенные dataclasses для новой архитектуры с трекингом посещений и touchpoints
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """
    Расширенная модель пользователя с трекингом активности

    Атрибуты:
        user_id: Telegram ID пользователя
        username: Username в Telegram
        first_name: Имя пользователя
        email: Email адрес
        phone_number: Номер телефона
        joined_at: Дата регистрации
        last_activity: Последняя активность
        is_vip: VIP статус
        is_diamond: Diamond статус
        is_sub_active: Активная подписка
        sub_start: Начало подписки
        sub_end: Окончание подписки
        last_updated_info: Последнее обновление
        status: Статус пользователя (active/inactive/churned)
        first_room_visit: Первое посещение комнаты
        last_room_visit: Последнее посещение комнаты
        total_room_visits: Общее количество посещений
    """
    user_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    joined_at: Optional[str] = None
    last_activity: Optional[str] = None
    is_vip: bool = False
    is_diamond: bool = False
    is_sub_active: bool = False
    sub_start: Optional[str] = None
    sub_end: Optional[str] = None
    last_updated_info: Optional[str] = None

    # Новые поля для трекинга
    status: str = 'active'  # active, inactive, churned
    first_room_visit: Optional[str] = None
    last_room_visit: Optional[str] = None
    total_room_visits: int = 0

    @staticmethod
    def from_dict(data: dict) -> 'User':
        """Создать User из словаря (из Google Sheets)"""
        return User(
            user_id=str(data.get('user_id', '')),
            username=data.get('username'),
            first_name=data.get('first_name'),
            email=data.get('email'),
            phone_number=data.get('phone_number'),
            joined_at=data.get('joined_at'),
            last_activity=data.get('last_activity'),
            is_vip=data.get('is_vip', 'False') == 'True',
            is_diamond=data.get('is_diamond', 'False') == 'True',
            is_sub_active=data.get('is_sub_active', 'False') == 'True',
            sub_start=data.get('sub_start'),
            sub_end=data.get('sub_end'),
            last_updated_info=data.get('last_updated_info'),
            status=data.get('status', 'active'),
            first_room_visit=data.get('first_room_visit'),
            last_room_visit=data.get('last_room_visit'),
            total_room_visits=int(data.get('total_room_visits', 0) or 0)
        )

    def to_dict(self) -> dict:
        """Преобразовать User в словарь для Google Sheets"""
        return {
            'user_id': self.user_id,
            'username': self.username or '',
            'first_name': self.first_name or '',
            'email': self.email or '',
            'phone_number': self.phone_number or '',
            'joined_at': self.joined_at or '',
            'last_activity': self.last_activity or '',
            'is_vip': 'True' if self.is_vip else 'False',
            'is_diamond': 'True' if self.is_diamond else 'False',
            'is_sub_active': 'True' if self.is_sub_active else 'False',
            'sub_start': self.sub_start or '',
            'sub_end': self.sub_end or '',
            'last_updated_info': self.last_updated_info or '',
            'status': self.status,
            'first_room_visit': self.first_room_visit or '',
            'last_room_visit': self.last_room_visit or '',
            'total_room_visits': str(self.total_room_visits)
        }


@dataclass
class RoomVisit:
    """
    Модель посещения комнаты

    Атрибуты:
        id: Уникальный ID посещения
        timestamp: Время посещения
        user_id: ID пользователя
        username: Username пользователя
        room_id: ID комнаты
        room_name: Название комнаты
        source: Источник перехода (touchpoint_1, direct, etc)
    """
    id: int
    timestamp: str
    user_id: int
    username: str
    room_id: str
    room_name: str
    source: str

    @staticmethod
    def from_dict(data: dict) -> 'RoomVisit':
        """Создать RoomVisit из словаря"""
        return RoomVisit(
            id=int(data.get('id', 0)),
            timestamp=data.get('timestamp', ''),
            user_id=int(data.get('user_id', 0)),
            username=data.get('username', ''),
            room_id=data.get('room_id', ''),
            room_name=data.get('room_name', ''),
            source=data.get('source', '')
        )

    def to_list(self) -> list:
        """Преобразовать в список для append_row"""
        return [
            str(self.id),
            self.timestamp,
            str(self.user_id),
            self.username,
            self.room_id,
            self.room_name,
            self.source
        ]


@dataclass
class Touchpoint:
    """
    Модель точки касания (touchpoint)

    Атрибуты:
        id: Уникальный ID
        timestamp: Время отправки
        user_id: ID пользователя
        username: Username пользователя
        touch_number: Номер touchpoint (1-8)
        status: Статус (sent, failed, clicked)
        error_message: Сообщение об ошибке (если failed)
        clicked: Дата клика (если был клик)
    """
    id: int
    timestamp: str
    user_id: int
    username: str
    touch_number: int
    status: str
    error_message: Optional[str] = None
    clicked: Optional[str] = None

    @staticmethod
    def from_dict(data: dict) -> 'Touchpoint':
        """Создать Touchpoint из словаря"""
        return Touchpoint(
            id=int(data.get('id', 0)),
            timestamp=data.get('timestamp', ''),
            user_id=int(data.get('user_id', 0)),
            username=data.get('username', ''),
            touch_number=int(data.get('touch_number', 0)),
            status=data.get('status', ''),
            error_message=data.get('error_message'),
            clicked=data.get('clicked')
        )

    def to_list(self) -> list:
        """Преобразовать в список для append_row"""
        return [
            str(self.id),
            self.timestamp,
            str(self.user_id),
            self.username,
            str(self.touch_number),
            self.status,
            self.error_message or '',
            self.clicked or ''
        ]


@dataclass
class Room:
    """
    Модель комнаты

    Атрибуты:
        room_id: Уникальный ID комнаты
        room_name: Название комнаты
        room_url: URL комнаты
        access_level: Уровень доступа (main, vip, diamond)
        is_active: Активна ли комната
    """
    room_id: str
    room_name: str
    room_url: str
    access_level: str  # main, vip, diamond
    is_active: bool = True

    @staticmethod
    def from_dict(data: dict) -> 'Room':
        """Создать Room из словаря"""
        return Room(
            room_id=data.get('room_id', ''),
            room_name=data.get('room_name', ''),
            room_url=data.get('room_url', ''),
            access_level=data.get('access_level', 'main'),
            is_active=data.get('is_active', 'True') == 'True'
        )

    def to_list(self) -> list:
        """Преобразовать в список для append_row"""
        return [
            self.room_id,
            self.room_name,
            self.room_url,
            self.access_level,
            'True' if self.is_active else 'False'
        ]
