"""
Handlers модуль - обработчики команд и сообщений
Объединяет пользовательские и админские обработчики
"""

from aiogram import Router

from app.handlers import user, admin


# Главный роутер, объединяющий все обработчики
router = Router()

# Подключаем роутеры
router.include_router(user.router)
router.include_router(admin.router)


__all__ = ['router']
