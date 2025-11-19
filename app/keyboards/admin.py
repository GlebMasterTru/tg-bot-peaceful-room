"""
Клавиатуры для администратора
Inline-клавиатуры для админских команд и функций
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ============================================================================
# РАССЫЛКА
# ============================================================================

broadcast_confirmation_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Отправить всем",
                callback_data="broadcast_confirm"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="broadcast_cancel"
            )
        ]
    ]
)


# ============================================================================
# ПРИМЕЧАНИЯ
# ============================================================================

"""
Здесь будут админские клавиатуры:
- Статистика бота
- Управление пользователями
- Настройки рассылок
- Аналитика и отчёты

Пример добавления новой клавиатуры:

admin_stats_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='📊 Статистика', callback_data='admin_stats')],
        [InlineKeyboardButton(text='👥 Пользователи', callback_data='admin_users')],
        [InlineKeyboardButton(text='💳 Платежи', callback_data='admin_payments')],
        [InlineKeyboardButton(text='◀️ Назад', callback_data='admin_main')]
    ]
)
"""
