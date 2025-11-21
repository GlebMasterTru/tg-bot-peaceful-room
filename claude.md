# Claude Context — Тихая Комната Bot

> Этот файл создан для передачи контекста между сессиями Claude/AI.
> Последнее обновление: 2025-11-21

---

## О проекте

**Тихая Комната** — Telegram-бот для управления подписками на психотерапевтический сервис Катерины Трубе.

**Стек:** Python 3, aiogram 3.x, Google Sheets (gspread), APScheduler

**БД:** Google Sheets (не SQL). Две таблицы:
- `users_worksheet` — пользователи бота
- `tilda_worksheet` — платежи из Tilda

---

## Архитектура (модульная)

```
app/
├── database/           # Работа с Google Sheets
│   ├── connection.py   # gspread подключение
│   ├── users.py        # CRUD пользователей
│   ├── payments.py     # Платежи, синхронизация с Tilda
│   └── models.py       # Dataclass-ы (User, Subscription, etc.)
│
├── handlers/           # Обработчики aiogram
│   ├── user.py         # /start, подписки, навигация
│   └── admin.py        # /broadcast, /myid
│
├── services/           # Бизнес-логика (отделена от handlers!)
│   ├── subscription.py # Проверка истекающих подписок
│   └── notifications.py # Отправка уведомлений
│
├── keyboards/          # Inline-клавиатуры
│   ├── user.py         # Меню пользователя
│   └── admin.py        # Админские клавиатуры
│
├── utils/
│   └── formatters.py   # get_days_word() и др.
│
├── filters/
│   └── is_admin.py     # IsAdmin фильтр
│
├── config.py           # Константы (ADMIN_ID, интервалы, URL)
├── texts.py            # ВСЕ тексты бота в одном месте
├── states.py           # FSM состояния
└── background_tasks.py # APScheduler задачи
```

---

## Система подписок

### Уровни доступа (от низшего к высшему):
1. **Обычный** — базовая комната
2. **VIP** — расширенный доступ (список в config D2)
3. **Diamond** — полный доступ (is_diamond в профиле + список в E2)

### Поля пользователя в БД:
- `user_id`, `username`, `first_name`
- `is_vip` — синхронизируется со списком в config
- `is_diamond` — True/False
- `is_sub_active` — активна ли подписка
- `sub_start`, `sub_end` — даты подписки (формат: `YYYY-MM-DD HH:MM:SS`)

### Статусы подписки (get_subscription_status):
- `active` — активна, > 3 дней
- `expiring_soon` — 0-3 дня до истечения
- `expired` — истекла
- `none` — никогда не было

---

## Фоновые задачи (background_tasks.py)

| Задача | Интервал | Описание |
|--------|----------|----------|
| check_payments_task | 30 сек | Обработка платежей из Tilda |
| sync_users_task | 15 мин | Миграция VIP, синхронизация is_vip |
| check_subscriptions_task | 12:00 ежедневно + при старте | Уведомления об истечении |

---

## Уведомления об истечении подписки

**Реализовано 2025-11-21**

Логика в `services/subscription.py` → `check_expiring_soon_subscriptions()`:

```python
# ВАЖНО: используем == а не <=, иначе все попадут в первое условие!
if days_left == 3:
    expiring_3_days.append(user_id)
elif days_left == 1:
    expiring_1_day.append(user_id)
elif days_left == 0:
    expiring_today.append(user_id)
```

Подсчёт дней (`payments.py`):
```python
# Сравниваем ТОЛЬКО даты, без времени!
days_left = (end_date_obj.date() - current_date.date()).days
```

Клавиатуры (`notifications.py`):
- 3 дня / 1 день / сегодня: "Продлить доступ" + "Зайти в Тихую Комнату"
- Истекла: только "Продлить доступ"

---

## Важные исправления (история багов)

### 1. Неправильный подсчёт дней (2025-11-21)
**Проблема:** При `sub_end = 2025-11-21 20:59:18` в тот же день показывало "3 дня".
**Причина:** Сравнивались datetime, а не date.
**Решение:** `(end_date_obj.date() - current_date.date()).days`

### 2. Все попадали в "3 дня" (2025-11-21)
**Проблема:** Уведомление "3 дня" приходило всем (и тем у кого 1 день, и 0).
**Причина:** Условие `if days_left <= 3` ловило всё.
**Решение:** Использовать `==` вместо `<=`.

---

## Соглашения с владельцем

1. **Ветки Git:** Использую формат `claude/...-sessionId` (ограничение системы)
2. **Коммиты:** На русском, краткое описание изменений
3. **Workflow:** main (прод) ← test (тестирование) ← claude/* (разработка)

---

## Полезные команды

```bash
# Запуск бота
python run.py

# Структура проекта
find app -name "*.py" | head -30
```

---

## TODO / Идеи на будущее

- [ ] Живой дневник (diary_menu — заглушка)
- [ ] Возможно: уведомление за 7 дней
- [ ] Аналитика подписок для админа

---

## Контакты

- **Админ бота:** ID `749452956`
- **Техподдержка:** @peaceful_room_help
- **Сайт:** trubetribe.ru
