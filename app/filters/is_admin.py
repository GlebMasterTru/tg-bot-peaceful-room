"""
Фильтр для проверки прав администратора
Используется в обработчиках для ограничения доступа
"""

from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from typing import Union

from app.config import ADMIN_ID


class IsAdmin(Filter):
    """
    Фильтр для проверки, является ли пользователь администратором

    Использование:
        @router.message(Command("broadcast"), IsAdmin())
        async def cmd_broadcast(message: Message):
            # Код доступен только админу
            pass

        @router.callback_query(F.data == "admin_action", IsAdmin())
        async def admin_action(callback: CallbackQuery):
            # Код доступен только админу
            pass
    """

    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        """
        Проверяет, является ли отправитель администратором

        Args:
            event: Message или CallbackQuery

        Returns:
            bool: True если пользователь - админ, False иначе
        """
        user_id = event.from_user.id
        return user_id == ADMIN_ID


# ============================================================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
# ============================================================================

"""
БЫЛО (старый подход):
    @router.message(Command("broadcast"))
    async def cmd_broadcast(message: Message):
        if message.from_user.id != ADMIN_ID:
            await message.answer("❌ У тебя нет доступа к этой команде.")
            return

        # Код для админа
        ...

СТАЛО (новый подход):
    @router.message(Command("broadcast"), IsAdmin())
    async def cmd_broadcast(message: Message):
        # Код для админа
        # Если не админ - обработчик не вызовется вообще
        ...

Преимущества:
- Чище код (без повторяющихся if-проверок)
- Декларативность (видно сразу, что команда для админа)
- Легче добавлять новые админские команды
- Можно комбинировать с другими фильтрами
"""
