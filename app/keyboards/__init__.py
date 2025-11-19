"""
Keyboards <>4C;L - inline-:;0280BC@K 1>B0
-:A?>@B :;0280BC@ 4;O ?>;L7>20B5;59 8 04<8=0
"""

# User keyboards
from app.keyboards.user import (
    get_main_menu,
    get_diamond_room_entrance_menu,
    profile_menu,
    check_subscription_menu,
    renew_subscription_menu,
    room_entrance_menu,
    diary_menu,
    help_menu
)

# Admin keyboards
from app.keyboards.admin import (
    broadcast_confirmation_menu,
)


__all__ = [
    # User keyboards
    'get_main_menu',
    'get_diamond_room_entrance_menu',
    'profile_menu',
    'check_subscription_menu',
    'renew_subscription_menu',
    'room_entrance_menu',
    'diary_menu',
    'help_menu',

    # Admin keyboards
    'broadcast_confirmation_menu',
]