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
│   ├── handlers.py          # Message and callback handlers (commands, menus, navigation)
│   ├── database.py          # Google Sheets integration, user/subscription management
│   ├── keyboards.py         # Inline keyboard layouts
│   ├── texts.py             # All user-facing text messages
│   ├── states.py            # FSM state definitions
│   └── background_tasks.py  # Scheduled tasks (payment checks, user sync)
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

**Admin ID**: Hardcoded as `749452956` in `handlers.py:26`

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
- Function: `check_payments_task()` in `background_tasks.py:9`
- Calls: `process_all_pending_payments()` in `database.py:520`
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
- Single router: `router = Router()` in `handlers.py:29`
- Registered in dispatcher: `dp.include_router(router)` in `run.py:28`
- Decorators:
  - `@router.message(...)` - Message handlers
  - `@router.callback_query(...)` - Callback query handlers

### Keyboard Creation
- Static keyboards: Defined in `keyboards.py` as constants
- Dynamic keyboards: Functions like `get_main_menu()` with parameters
- Pattern: Use `callback_data` for navigation, `url` for external links

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

2. **Add keyboard** in `app/keyboards.py`:
```python
new_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Action', callback_data='action')],
        [InlineKeyboardButton(text='Back', callback_data='back_to_previous')]
    ]
)
```

3. **Add handler** in `app/handlers.py`:
```python
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
2. **Update functions** in `database.py`:
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

1. **Add handler** in `app/handlers.py`:
```python
@router.message(Command("new_command"))
async def cmd_new_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Access denied")
        return

    # Admin-only logic
    await message.answer("✅ Command executed")
```

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

### From Code Comments (handlers.py:502-528)

**TODO**:
1. ~~Background task for subscription expiration~~ (Currently no auto-expiration)
   - Check subscriptions every 15 minutes
   - Set `is_sub_active=False` when `sub_end < now`
   - Send notifications: 3 days before, 1 day before, on expiration day

2. **HOT!** Unused parameters in `get_main_menu()` - `room_link` variables passed but room links not used (line 512)

3. Add comprehensive error logging:
   - File-based logging or external service
   - Admin notifications on critical failures
   - Structured error tracking

4. Analytics features:
   - Active user count
   - Subscription renewal statistics
   - Payment reports

5. Additional features:
   - Payment history per user
   - Referral system
   - Promo codes and discounts

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

### Key Functions (database.py)
- `get_user(user_id)` - Fetch user record as dict
- `add_user(user_id, username, first_name)` - Create new user
- `get_user_privileges(user_id)` - Returns (is_vip, is_diamond)
- `get_links()` - Returns (main_link, vip_link, diamond_link)
- `sync_user_subscription(user_id, username)` - Manual payment sync
- `get_subscription_status(user_id)` - Returns detailed sub info
- `update_user_batch(user_id, update_dict)` - Batch update multiple fields
- `get_all_users()` - Get all users for broadcasting

### Key Handlers (handlers.py)
- `cmd_start()` - /start command, main menu
- `go_to_profile()` - Profile menu navigation
- `check_subscription()` - Display subscription status
- `verify_payment()` - Manual payment verification
- `cmd_broadcast()` - Admin broadcast initiation
- `callback_broadcast_confirm()` - Execute broadcast

### Callback Data Patterns
- `go_to_*` - Navigation to menus
- `back_to_*` - Back navigation
- `check_*` - Information queries
- `verify_*` - Verification actions
- `broadcast_*` - Broadcast flow

---

**Last Updated**: 2025-11-14
**Bot Version**: Based on commit `ba2280e`
**aiogram Version**: 3.22.0
**Maintained by**: Development team with AI assistance
