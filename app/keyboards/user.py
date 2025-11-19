"""
Клавиатуры для пользователей
Все inline-клавиатуры для взаимодействия с ботом
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.config import (
    SUBSCRIPTION_RENEWAL_URL,
    DIARY_URL,
    SUPPORT_URL
)


# ============================================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================================

def get_main_menu(is_vip=False, is_diamond=False, main_link='', vip_link='', diamond_link=''):
    """
    Главное меню с динамической кнопкой входа в комнату

    Args:
        is_vip: VIP статус пользователя
        is_diamond: Diamond статус пользователя
        main_link: Ссылка на основную комнату
        vip_link: Ссылка на VIP комнату
        diamond_link: Ссылка на Diamond комнату

    Returns:
        InlineKeyboardMarkup: Клавиатура главного меню
    """
    # Определяем ссылку для комнаты
    if is_diamond:
        room_link = diamond_link
    elif is_vip:
        room_link = vip_link
    else:
        room_link = main_link

    # Кнопка входа в комнату (разная для Diamond)
    if is_diamond:
        room_button = InlineKeyboardButton(
            text='Зайти в Тихую Комнату',
            callback_data='go_to_room_entrance'  # callback для Diamond
        )
    else:
        room_button = InlineKeyboardButton(
            text='Зайти в Тихую Комнату',
            url=room_link  # URL для обычных/VIP
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [room_button],
            [
                InlineKeyboardButton(text='Твой кабинет', callback_data='go_to_profile_menu'),
                InlineKeyboardButton(text='Нужна тех. помощь', callback_data='go_to_help_menu')
            ]
        ]
    )

    return keyboard


def get_diamond_room_entrance_menu(diamond_link):
    """
    Меню входа в Diamond комнату

    Args:
        diamond_link: Ссылка на Diamond комнату

    Returns:
        InlineKeyboardMarkup: Клавиатура входа в Diamond комнату
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Зайти в комнату', url=diamond_link)],
            [InlineKeyboardButton(text='Назад', callback_data='back_to_main')]
        ]
    )


# ============================================================================
# МЕНЮ "ТВОЙ КАБИНЕТ"
# ============================================================================

profile_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='Проверить подписку', callback_data='check_subscription'),
            InlineKeyboardButton(text='Продлить доступ', callback_data='renew_subscription')
        ],
        [InlineKeyboardButton(text='Живой дневник', callback_data='go_to_diary_menu')],
        [InlineKeyboardButton(text='Назад', callback_data='back_to_main')]
    ]
)


# ============================================================================
# МЕНЮ ПОДПИСКИ
# ============================================================================

check_subscription_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Продлить подписку', callback_data='renew_subscription')],
        [InlineKeyboardButton(text='Проверить оплату', callback_data='verify_payment')],
        [InlineKeyboardButton(text='Назад', callback_data='back_to_profile')]
    ]
)


renew_subscription_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Продлить подписку', url=SUBSCRIPTION_RENEWAL_URL)],
        [InlineKeyboardButton(text='Проверить оплату', callback_data='verify_payment')],
        [InlineKeyboardButton(text='Назад', callback_data='back_to_profile')]
    ]
)


# ============================================================================
# ДРУГИЕ МЕНЮ
# ============================================================================

room_entrance_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='back_to_main')]
    ]
)


diary_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Живой дневник', url=DIARY_URL)],
        [InlineKeyboardButton(text='Назад', callback_data='back_to_profile')]
    ]
)


help_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Тык!', url=SUPPORT_URL)],
        [InlineKeyboardButton(text='Назад', callback_data='back_to_main')]
    ]
)
