from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu(is_vip=False, is_diamond=False, main_link='', vip_link='', diamond_link=''):
    """
    Главное меню с динамической кнопкой входа в комнату
    """
    # Определяем ссылку для комнаты
    if is_diamond:
        room_link = diamond_link
    elif is_vip:
        room_link = vip_link
    else:
        room_link = main_link
    
    if is_diamond:
        room_button = InlineKeyboardButton(
            text='Зайти в Тихую Комнату', 
            callback_data='go_to_room_entrance'  # 👈 callback для Diamond
        )
    else:
        room_button = InlineKeyboardButton(
            text='Зайти в Тихую Комнату',
            url=room_link  # 👈 URL для обычных/VIP
        )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [room_button],  # 👈 Используем динамическую кнопку
            [
                InlineKeyboardButton(text='Твой кабинет', callback_data='go_to_profile_menu'),
                InlineKeyboardButton(text='Нужна тех. помощь', callback_data='go_to_help_menu')
            ]
        ]
    )
    
    return keyboard


def get_diamond_room_entrance_menu(diamond_link):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Зайти в комнату', url=diamond_link)],
            [InlineKeyboardButton(text='Назад', callback_data='back_to_main')]
        ]
    )


# МЕНЮ "ТВОЙ КАБИНЕТ" (Profile Menu)
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

# МЕНЮ "ПРОВЕРИТЬ ПОДПИСКУ" (Check Subscription Menu)
check_subscription_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Продлить подписку', callback_data='renew_subscription')],
        [InlineKeyboardButton(text='Проверить оплату', callback_data='verify_payment')],
        [InlineKeyboardButton(text='Назад', callback_data='back_to_profile')]
    ]
)

# МЕНЮ "ПРОДЛИТЬ ПОДПИСКУ" (Renew Subscription Menu)
renew_subscription_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Продлить подписку', url='https://trubetribe.ru/sr_cont')],
        [InlineKeyboardButton(text='Проверить оплату', callback_data='verify_payment')],
        [InlineKeyboardButton(text='Назад', callback_data='back_to_profile')]
    ]
)

room_entrance_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='back_to_main')]
    ]
)

# МЕНЮ "ЖИВОЙ ДНЕВНИК" (Diary Menu)
diary_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Живой дневник', url='https://trubetribe.ru/')],  # TODO: Заменить на реальную ссылку
        [InlineKeyboardButton(text='Назад', callback_data='back_to_profile')]
    ]
)

# МЕНЮ "ТЕХПОДДЕРЖКА" (Help Menu)
help_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Тык!', 
                              url='https://t.me/peaceful_room_help')],
        [InlineKeyboardButton(text='Назад', 
                              callback_data='back_to_main')]
    ]
)