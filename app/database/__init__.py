"""
Database <>4C;L - @01>B0 A Google Sheets
-:A?>@B 2A5E DC=:F89 4;O C4>1=>3> 8<?>@B0
"""

# Connection
from app.database.connection import (
    users_worksheet,
    config_worksheet,
    tilda_worksheet
)

# Models
from app.database.models import (
    User,
    Subscription,
    Payment,
    RoomLinks
)

# Users
from app.database.users import (
    get_user,
    get_all_users,
    add_user,
    add_user_with_subscription,
    update_user_batch,
    get_user_privileges,
    add_user_to_diamond_list,
    get_links,
    is_temporarily_vip_user,
    migrate_single_user,
    migrate_many_users,
    sync_is_vip_for_all_users,
    save_vote,
    get_vote_stats
)

# Payments
from app.database.payments import (
    get_subscription_status,
    sync_user_subscription,
    process_all_pending_payments
)

# Utils (для обратной совместимости импортов)
from app.utils.formatters import (
    clean_telegram_username,
    format_date_for_user
)


__all__ = [
    # Worksheets
    'users_worksheet',
    'config_worksheet',
    'tilda_worksheet',

    # Models
    'User',
    'Subscription',
    'Payment',
    'RoomLinks',

    # Users functions
    'get_user',
    'get_all_users',
    'add_user',
    'add_user_with_subscription',
    'update_user_batch',
    'get_user_privileges',
    'add_user_to_diamond_list',
    'get_links',
    'is_temporarily_vip_user',
    'migrate_single_user',
    'migrate_many_users',
    'sync_is_vip_for_all_users',
    'save_vote',
    'get_vote_stats',

    # Payments functions
    'clean_telegram_username',
    'format_date_for_user',
    'get_subscription_status',
    'sync_user_subscription',
    'process_all_pending_payments',
]