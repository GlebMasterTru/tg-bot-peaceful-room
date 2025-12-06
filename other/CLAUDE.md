# CLAUDE.md - AI Assistant Guide for Peaceful Room Bot

## Project Overview

**Peaceful Room Bot** (Тихая Комната) is a Telegram subscription bot for a psychological/therapeutic service created by psychotherapist Katerina Trube. The bot manages user access to different "rooms" based on subscription tiers and integrates with Google Sheets for database management and Tilda for payment processing.

### Tech Stack
- **Language**: Python 3.x
- **Bot Framework**: aiogram 3.22.0 (async Telegram bot framework)
- **Database**: Google Sheets (via gspread 6.2.1)
- **Authentication**: Google OAuth2 (service account)
- **Task Scheduling**: APScheduler 3.11.0
- **Environment**: python-dotenv for configuration
- **FSM**: aiogram's built-in FSM (Finite State Machine) with MemoryStorage

### Project Structure

```
tg-bot-peaceful-room/
├── app/
│   ├── config.py            # Centralized configuration (URLs, intervals, IDs)
│   ├── texts.py             # All user-facing text messages
│   ├── states.py            # FSM state definitions
│   ├── background_tasks.py  # Scheduled tasks (payment checks, user sync)
│   ├── database/            # Database layer (Google Sheets)
│   │   ├── __init__.py      # Exports all database functions
│   │   ├── connection.py    # Google Sheets client initialization
│   │   ├── models.py        # Data models (User, Subscription, Payment, RoomLinks)
│   │   ├── users.py         # User CRUD operations and privileges
│   │   └── payments.py      # Payment processing and subscription sync
│   ├── handlers/            # Message and callback handlers
│   │   ├── __init__.py      # Router combining user and admin handlers
│   │   ├── user.py          # User commands and menu navigation
│   │   └── admin.py         # Admin commands (broadcast, stats)
│   ├── keyboards/           # Inline keyboard layouts
│   │   ├── __init__.py      # Exports all keyboards
│   │   ├── user.py          # User keyboards (menus, navigation)
│   │   └── admin.py         # Admin keyboards (broadcast confirmation)
│   ├── services/            # Business logic layer
│   │   ├── __init__.py      # Exports all services
│   │   ├── subscription.py  # Subscription checking and expiration
│   │   └── notifications.py # User notifications (payments, expiration)
│   ├── filters/             # Custom aiogram filters
│   │   ├── __init__.py      # Exports all filters
│   │   └── is_admin.py      # Admin filter
│   └── utils/               # Utility functions
│       ├── __init__.py      # Exports all utilities
│       └── formatters.py    # Date formatting, text utilities
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (gitignored)
├── service_account.json     # Google service account credentials (gitignored)
└── .gitignore
```

## Core Concepts

### User Privilege Tiers

The bot has three user access levels:

1. **Regular Users**: Access to main room only
2. **VIP Users**: Access to main + VIP room (answered "Quiet Questions")
3. **Diamond Users**: Access to all rooms + active subscription

**Important**:
- VIP status is stored in `config` sheet, cell `D2` (comma-separated user IDs)
- Diamond status is stored in `users` sheet, column `is_diamond` (True/False)
- Temporary VIP usernames are stored in `config` sheet, cell `F2` (migrated to IDs on first /start)

### Database Architecture (Google Sheets)

**Main Database** (`SPREADSHEET_ID_DB`):
- **Sheet: "users"** - User records with columns:
  - `user_id` - Telegram user ID (primary key)
  - `username` - Telegram username
  - `first_name` - User's first name
  - `email` - Email address
  - `phone_number` - Phone number
  - `joined_at` - Registration timestamp
  - `last_activity` - Last interaction timestamp
  - `is_vip` - VIP status (True/False)
  - `is_diamond` - Diamond/subscription status (True/False)
  - `is_sub_active` - Subscription active flag (True/False)
  - `sub_start` - Subscription start date (YYYY-MM-DD HH:MM:SS)
  - `sub_end` - Subscription end date (YYYY-MM-DD HH:MM:SS)
  - `last_updated_info` - Last update timestamp

- **Sheet: "config"** - Bot configuration:
  - `A2` - Main room link
  - `B2` - VIP room link
  - `C2` - Diamond room link
  - `D2` - Comma-separated VIP user IDs
  - `E2` - Comma-separated Diamond user IDs (legacy, prefer `is_diamond` column)
  - `F2` - Comma-separated temporary VIP usernames (migrated on /start)

**Tilda Database** (`SPREADSHEET_ID_TILDA_DB`):
- **Sheet: "Лист1"** - Payment records from Tilda:
  - `Как_с_вами_связаться_в_Телеграм_username` - Telegram username
  - `Email` - Customer email
  - `Phone` - Customer phone
  - `valid to` - Subscription end date (YYYY-MM-DD HH:MM:SS)
  - `Дата начала подписки` - Subscription start date
  - `processed` - Processing flag (empty/TRUE) in column T (20th column)

### Navigation Flow

```
/start (Main Menu)
├── "Зайти в Тихую Комнату" → Opens room based on tier
│   └── (Diamond users) → Room entrance menu → Diamond room link
├── "Твой кабинет" (Profile Menu)
│   ├── "Проверить подписку" → Subscription status
│   │   ├── "Продлить подписку" → Renewal menu
│   │   └── "Проверить оплату" → Sync with Tilda
│   ├── "Продлить доступ" → Renewal menu
│   │   ├── "Продлить подписку" (URL) → Tilda payment page
│   │   └── "Проверить оплату" → Sync with Tilda
│   └── "Живой дневник" → Diary menu (not yet implemented)
└── "Нужна тех. помощь" (Help Menu) → Support contact
```

### Admin Features

**Admin ID**: Defined in `app/config.py` as `ADMIN_ID = 749452956`

**Commands**:
- `/broadcast` - Start broadcast to all users (supports text, photos, videos, files)
- `/myid` - Get user info (ID, username, name)
- `/help` - Test command
- `/cancel` - Cancel ongoing broadcast

**Broadcast Flow**:
1. Admin sends `/broadcast`
2. Admin sends message content (text/media)
3. Bot shows preview with confirm/cancel buttons
4. On confirmation, sends to all users via `copy_message()`
5. Shows real-time progress every 50 users
6. Final statistics report (success/blocked/errors)

### Background Tasks

**Scheduler**: APScheduler with AsyncIOScheduler

**Task 1: Payment Checking** (every 30 seconds)
- Function: `check_payments_task()` in `app/background_tasks.py`
- Calls: `process_all_pending_payments()` in `app/database/payments.py`
- Actions:
  1. Fetches unprocessed records from Tilda sheet
  2. Groups by username
  3. Updates user subscriptions in main database
  4. Marks Tilda records as processed (column T = TRUE)
  5. Sends notification to users with successful payments
  6. Adds users to Diamond list

**Task 2: User Synchronization** (every 15 minutes)
- Function: `sync_users_task()` in `background_tasks.py:29`
- Actions:
  1. `migrate_many_users()` - Migrates temporary VIP usernames to ID-based list
  2. `sync_is_vip_for_all_users()` - Syncs `is_vip` column with config list

## Development Conventions

### Code Style
- **Russian Language**: All user-facing text, comments, and print statements in Russian
- **English**: Variable names, function names, technical terms
- **Formatting**: Standard Python (PEP 8)
- **Async/Await**: All handlers and database operations are asynchronous

### Error Handling
- Database functions return `None` or `False` on errors
- Print errors to console (no logging framework currently)
- Try-except blocks in critical operations
- `TelegramBadRequest` handling for "message is not modified" errors
- `TelegramForbiddenError` handling for blocked users in broadcasts

### Message Editing Best Practice
```python
try:
    await callback.message.edit_text(text, reply_markup=keyboard)
except TelegramBadRequest as e:
    if "message is not modified" in str(e):
        pass  # Ignore - message already has this content
    else:
        raise  # Re-raise other errors
```

### FSM Usage
- Import: `from aiogram.fsm.context import FSMContext`
- States defined in: `app/states.py`
- Storage: `MemoryStorage()` (data lost on restart)
- Current states: `BroadcastStates` (waiting_for_text, waiting_for_confirmation)

### Router Pattern
- Main router: `router = Router()` in `app/handlers/__init__.py`
- Sub-routers: `app/handlers/user.py` and `app/handlers/admin.py` each have their own router
- Main router includes sub-routers: `router.include_router(user.router)` and `router.include_router(admin.router)`
- Registered in dispatcher: `dp.include_router(router)` in `run.py`
- Decorators:
  - `@router.message(...)` - Message handlers
  - `@router.callback_query(...)` - Callback query handlers

### Keyboard Creation
- Static keyboards: Defined in `app/keyboards/user.py` and `app/keyboards/admin.py`
- Dynamic keyboards: Functions like `get_main_menu()` with parameters
- Pattern: Use `callback_data` for navigation, `url` for external links
- Import: `from app.keyboards import get_main_menu, profile_menu, etc.`

### Text Management
- All texts in `texts.py`
- Notification texts: Short messages for `callback.answer()`
- Menu texts: Full-screen messages
- Dynamic text: Use `.format()` for variable substitution
- HTML formatting: `parse_mode=ParseMode.HTML` set globally

## Common Development Tasks

### Adding a New Menu

1. **Add text** in `app/texts.py`:
```python
NEW_MENU_TEXT = '''Your menu text here...'''
NOTIFY_NEW_MENU = 'Short notification'
```

2. **Add keyboard** in `app/keyboards/user.py` (or `admin.py` for admin):
```python
new_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Action', callback_data='action')],
        [InlineKeyboardButton(text='Back', callback_data='back_to_previous')]
    ]
)
```

3. **Export keyboard** in `app/keyboards/__init__.py`:
```python
from app.keyboards.user import new_menu

__all__ = [
    # ... existing exports
    'new_menu',
]
```

4. **Add handler** in `app/handlers/user.py` (or `admin.py` for admin):
```python
import app.keyboards as kb
import app.texts as txt

@router.callback_query(F.data == 'go_to_new_menu')
async def go_to_new_menu(callback: CallbackQuery):
    await callback.answer(txt.NOTIFY_NEW_MENU)
    await callback.message.edit_text(
        txt.NEW_MENU_TEXT,
        reply_markup=kb.new_menu
    )
```

### Adding a New Database Field

1. **Add column** to Google Sheets "users" sheet manually
2. **Update model** in `app/database/models.py` (add field to `User` dataclass)
3. **Update functions** in `app/database/users.py`:
   - `add_user()` - If field needed on creation
   - `update_user_batch()` - Auto-handles new fields
   - `get_user()` - Auto-returns all fields as dict

### Adding a New Background Task

1. **Create function** in `app/background_tasks.py`:
```python
async def new_task(bot):
    print("🔄 Running new task...")
    # Your task logic
    print("✅ Task completed!\n")
```

2. **Register in scheduler** in `setup_scheduler()`:
```python
scheduler.add_job(
    new_task,
    trigger=IntervalTrigger(minutes=30),  # or hours=1, seconds=60
    args=[bot],
    id='new_task_id',
    name='Task Description',
    replace_existing=True
)
```

### Adding Admin Commands

1. **Add handler** in `app/handlers/admin.py`:
```python
from aiogram.filters import Command
from app.filters import IsAdmin

@router.message(Command("new_command"), IsAdmin())
async def cmd_new_command(message: Message):
    # Admin-only logic
    await message.answer("✅ Command executed")
```

Note: Use the `IsAdmin()` filter instead of manually checking user ID. The filter is defined in `app/filters/is_admin.py` and uses `ADMIN_ID` from `app/config.py`.

## Environment Variables

Required in `.env` file:
```bash
TG_TOKEN=your_telegram_bot_token
SERVICE_ACCOUNT_FILE=service_account.json
SPREADSHEET_ID_DB=your_main_spreadsheet_id
SPREADSHEET_ID_TILDA_DB=your_tilda_spreadsheet_id
```

**Service Account Setup**:
1. Create Google Cloud project
2. Enable Google Sheets API
3. Create service account
4. Download credentials as `service_account.json`
5. Share Google Sheets with service account email
6. Grant Editor permissions

## Testing Guidelines

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Set up .env file
cp .env.example .env  # Create from example
# Edit .env with your credentials

# Run bot
python run.py
```

### Testing User Tiers
- Regular: Use any new user
- VIP: Add user ID to config sheet D2
- Diamond: Add user ID to config D2 + set is_diamond=True in users sheet

### Testing Payments
1. Add test record to Tilda sheet
2. Wait up to 30 seconds for background task
3. Check console logs for processing
4. Verify user receives notification
5. Check /start menu updates to Diamond

## Known Issues & TODO

### Architecture Improvements

✅ **Completed**:
- Modular architecture with separated concerns
- Database layer with models and dataclasses
- Service layer for business logic
- Filter pattern for admin checks
- Centralized configuration
- **Subscription expiration system (2025-11-21)**:
  - Background task `check_subscriptions_task()` runs daily at 12:00 + on bot startup
  - Auto-deactivates expired subscriptions (`check_and_expire_subscriptions()`)
  - Sends notifications: 3 days before, 1 day before, last day (0 days), and on expiration
  - Inline keyboards on notifications: "Продлить доступ" + "Зайти в Тихую Комнату"

**TODO**:
1. Comprehensive error logging:
   - File-based logging or external service (e.g., Sentry)
   - Admin notifications on critical failures
   - Structured error tracking

3. Analytics features:
   - Active user count dashboard
   - Subscription renewal statistics
   - Payment reports and trends

4. Additional features:
   - Payment history per user
   - Referral system
   - Promo codes and discounts
   - User feedback collection

### Current Limitations
- **No persistent FSM**: Uses MemoryStorage (state lost on bot restart)
- **No logging framework**: Only console prints
- **No tests**: No unit or integration tests
- **Hardcoded admin ID**: Should be in environment variable
- **No subscription auto-expiration**: Manual or requires implementation

## Git Workflow

### Recent Changes (Last 5 Commits)
```
ba2280e - Добавил удаленный обработчик у кнопки для тех.поддержки
1bfa8bc - Удалён дублирующий обработчик go_to_room_entrance
53d2a65 - Переделал логику кнопки 'Зайти в Тихую комнату'
732ece9 - Добавил в рассылку поддержку фото/видео/файлов
869c780 - Добавлено рассылка с FSM ко всем юзерам бота (связана с бд)
```

### Branch Strategy
- Work on feature branches prefixed with `claude/`
- Branch format: `claude/claude-md-{session-id}`
- Push requires matching session ID in branch name

### Commit Message Style
- Russian language
- Past tense
- Clear description of changes
- Examples: "Добавил...", "Исправил...", "Переделал..."

## Security Considerations

### Sensitive Files (Gitignored)
- `.env` - Bot token and configuration
- `service_account.json` - Google API credentials
- `credentials.json` - Any OAuth credentials
- `__pycache__/` - Python cache
- `.venv/` - Virtual environment

### Best Practices
- Never commit tokens or credentials
- Use service account with minimum required permissions
- Validate admin ID before executing privileged commands
- Sanitize user input (usernames, emails) before database operations
- Handle Telegram API rate limits (0.10s delay in broadcasts)

## Debugging Tips

### Enable Detailed Logging
```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Common Issues

**"User not found"**:
- Check if user called `/start` at least once
- Verify Google Sheets permissions
- Check `get_user()` return value

**"Message is not modified"**:
- Normal when re-opening same menu
- Handled with try-except in most places
- Add handling if adding new edit_text calls

**Payment not processing**:
- Check Tilda sheet username format (should match Telegram)
- Verify `processed` column is empty (not TRUE)
- Check date format: `YYYY-MM-DD HH:MM:SS`
- Monitor console logs during 30-second cycle

**Subscription not updating**:
- Run `/myid` to verify user_id
- Check config sheet D2 has correct user ID
- Verify `is_diamond` column spelling
- Wait for 15-minute sync task

## Quick Reference

### Key Modules

**Database** (`app.database`):
- `get_user(user_id)` - Fetch user record (`app/database/users.py`)
- `add_user(user_id, username, first_name)` - Create new user
- `get_user_privileges(user_id)` - Returns (is_vip, is_diamond)
- `get_links()` - Returns RoomLinks model with room URLs (`app/database/connection.py`)
- `sync_user_subscription(user_id, username)` - Manual payment sync (`app/database/payments.py`)
- `get_subscription_status(user_id)` - Returns Subscription model
- `update_user_batch(user_id, update_dict)` - Batch update multiple fields
- `get_all_users()` - Get all users for broadcasting
- `process_all_pending_payments()` - Process Tilda payments (`app/database/payments.py`)

**Services** (`app.services`):
- `notify_payment_processed(bot, user_id)` - Send payment success notification (`app/services/notifications.py`)
- `check_expiring_soon_subscriptions()` - Find expiring subscriptions (`app/services/subscription.py`)
- `get_subscription_info_text(user_id)` - Format subscription status text

**Handlers** (`app.handlers`):
- User handlers in `app/handlers/user.py`:
  - `cmd_start()` - /start command, main menu
  - `go_to_profile()` - Profile menu navigation
  - `check_subscription()` - Display subscription status
  - `verify_payment()` - Manual payment verification
- Admin handlers in `app/handlers/admin.py`:
  - `cmd_broadcast()` - Admin broadcast initiation
  - `callback_broadcast_confirm()` - Execute broadcast
  - `cmd_myid()` - Get user info

**Keyboards** (`app.keyboards`):
- `get_main_menu(is_vip, is_diamond, main_link, vip_link, diamond_link)` - Dynamic main menu
- `profile_menu` - User profile menu
- `broadcast_confirmation_menu` - Admin broadcast confirmation

**Models** (`app.database.models`):
- `User` - User dataclass with all fields
- `Subscription` - Subscription info
- `Payment` - Payment record from Tilda
- `RoomLinks` - Room URLs

**Configuration** (`app.config`):
- `ADMIN_ID` - Admin user ID
- `PAYMENT_CHECK_INTERVAL_SECONDS` - Payment check frequency (30s)
- `USER_SYNC_INTERVAL_MINUTES` - User sync frequency (15min)
- `SUBSCRIPTION_RENEWAL_URL` - Tilda payment page
- `DIARY_URL` - Diary link
- `SUPPORT_URL` - Support link

### Callback Data Patterns
- `go_to_*` - Navigation to menus
- `back_to_*` - Back navigation
- `check_*` - Information queries
- `verify_*` - Verification actions
- `broadcast_*` - Broadcast flow

---

**Last Updated**: 2025-11-21
**Bot Version**: Modular architecture with subscription notifications
**Architecture**: Refactored to modular structure (database/, handlers/, keyboards/, services/, filters/, utils/)
**aiogram Version**: 3.22.0
**Maintained by**: Development team with AI assistance

## Architecture Changelog

**2025-11-21** - Subscription expiration notifications:
- Added `check_subscriptions_task()` to background_tasks.py (CronTrigger at 12:00 + startup)
- Notifications at exactly 3 days, 1 day, 0 days (last day) before expiration
- **BUGFIX**: Changed `days_left <= 3` to `days_left == 3` (otherwise all users caught by first condition)
- **BUGFIX**: Compare `.date()` not `datetime` for accurate day calculation
- Added inline keyboards to expiration notifications

**2025-11-19** - Major refactoring to modular architecture:
- Separated monolithic files into organized modules
- Added database layer with models (User, Subscription, Payment, RoomLinks)
- Created service layer for business logic (subscription, notifications)
- Implemented filter pattern (IsAdmin)
- Centralized configuration in config.py
- Split handlers into user.py and admin.py
- Split keyboards into user.py and admin.py
- Added utility functions in utils/formatters.py
- Improved code organization and maintainability
