"""
Модели данных для работы с БД
Типизированные структуры вместо словарей
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """
    Модель пользователя бота

    Атрибуты:
        user_id: Telegram ID пользователя (str для совместимости с Google Sheets)
        username: Username в Telegram (с @ или без)
        first_name: Имя пользователя
        email: Email адрес (опционально)
        phone_number: Номер телефона (опционально)
        joined_at: Дата регистрации в боте
        last_activity: Последняя активность
        is_vip: VIP статус (доступ к VIP комнате)
        is_diamond: Diamond статус (активная подписка)
        is_sub_active: Флаг активной подписки
        sub_start: Дата начала подписки
        sub_end: Дата окончания подписки
        last_updated_info: Последнее обновление информации
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

    @staticmethod
    def from_dict(data: dict) -> 'User':
        """
        Создаёт объект User из словаря (из Google Sheets)

        Args:
            data: Словарь с данными пользователя (из get_all_records())

        Returns:
            User: Объект пользователя
        """
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
            last_updated_info=data.get('last_updated_info')
        )

    def to_dict(self) -> dict:
        """
        Преобразует User в словарь для записи в Google Sheets

        Returns:
            dict: Словарь с данными для Sheets (bool -> 'True'/'False')
        """
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
            'last_updated_info': self.last_updated_info or ''
        }


@dataclass
class Subscription:
    """
    Модель подписки пользователя

    Атрибуты:
        user_id: ID пользователя
        is_active: Активна ли подписка
        start_date: Дата начала
        end_date: Дата окончания
        days_left: Сколько дней осталось
        status: Статус ('active', 'expired', 'expiring_soon', 'none')
    """
    user_id: str
    is_active: bool
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    days_left: Optional[int] = None
    status: str = 'none'  # active, expired, expiring_soon, none

    @property
    def formatted_end_date(self) -> Optional[str]:
        """
        Возвращает дату окончания в формате DD.MM.YYYY

        Returns:
            str: Форматированная дата или None
        """
        if not self.end_date:
            return None
        try:
            date_obj = datetime.strptime(self.end_date, '%Y-%m-%d %H:%M:%S')
            return date_obj.strftime('%d.%m.%Y')
        except ValueError:
            return self.end_date


@dataclass
class Payment:
    """
    Модель платежа из Tilda

    Атрибуты:
        username: Username в Telegram (из Tilda)
        email: Email покупателя
        phone: Телефон покупателя
        valid_to: Дата окончания подписки
        start_date: Дата начала подписки
        processed: Обработан ли платёж (True/False)
        row_number: Номер строки в таблице (для обновления статуса)
    """
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    valid_to: Optional[str] = None
    start_date: Optional[str] = None
    processed: bool = False
    row_number: Optional[int] = None

    @staticmethod
    def from_dict(data: dict, row_num: int = None) -> 'Payment':
        """
        Создаёт объект Payment из словаря (из Tilda worksheet)

        Args:
            data: Словарь с данными платежа
            row_num: Номер строки в таблице

        Returns:
            Payment: Объект платежа
        """
        return Payment(
            username=data.get('Как_с_вами_связаться_в_Телеграм_username', ''),
            email=data.get('Email'),
            phone=data.get('Phone'),
            valid_to=data.get('valid to'),
            start_date=data.get('Дата начала подписки'),
            processed=bool(data.get('processed', '')),
            row_number=row_num
        )


@dataclass
class RoomLinks:
    """
    Модель ссылок на комнаты (из config листа)

    Атрибуты:
        main: Ссылка на основную комнату
        vip: Ссылка на VIP комнату
        diamond: Ссылка на Diamond комнату
    """
    main: str
    vip: str
    diamond: str


# ============================================================================
# ПРИМЕЧАНИЯ ПО ИСПОЛЬЗОВАНИЮ
# ============================================================================

"""
Как использовать модели:

1. Создание пользователя из словаря:
    user_data = {'user_id': '123', 'username': 'john', 'is_vip': 'True'}
    user = User.from_dict(user_data)

    print(user.user_id)  # '123'
    print(user.is_vip)   # True (bool, не строка!)

2. Преобразование обратно в словарь:
    data_to_save = user.to_dict()
    # {'user_id': '123', 'is_vip': 'True', ...}

3. Работа с подпиской:
    sub = Subscription(
        user_id='123',
        is_active=True,
        end_date='2025-12-31 23:59:59',
        status='active'
    )

    print(sub.formatted_end_date)  # '31.12.2025'

Преимущества dataclasses:
    - Автозаполнение в IDE
    - Проверка типов
    - Меньше опечаток
    - Читабельнее, чем словари
"""
