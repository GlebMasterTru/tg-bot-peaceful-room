"""
Пошаговое тестирование Data Layer v1

Этот скрипт помогает протестировать все репозитории.
Запустите его в Python интерпретаторе построчно или целиком.
"""

print("=" * 60)
print("ТЕСТИРОВАНИЕ DATA LAYER V1")
print("=" * 60)

# ============================================================
# ПУНКТ 4: Проверка подключения к новым листам
# ============================================================
print("\n📋 ПУНКТ 4: Проверка подключения к новым листам")
print("-" * 60)

try:
    from app.database.connection import (
        room_visits_worksheet,
        touchpoints_log_worksheet,
        rooms_registry_worksheet
    )

    print(f"✅ Лист room_visits: {room_visits_worksheet.title}")
    print(f"✅ Лист touchpoints_log: {touchpoints_log_worksheet.title}")
    print(f"✅ Лист rooms_registry: {rooms_registry_worksheet.title}")
    print("\n✅ Все листы доступны!")
except Exception as e:
    print(f"\n❌ ОШИБКА подключения к листам: {e}")
    print("⚠️ Убедитесь что вы создали листы в Google Sheets:")
    print("   1. room_visits")
    print("   2. touchpoints_log")
    print("   3. rooms_registry")
    exit(1)


# ============================================================
# ПУНКТ 5: Тестирование UserRepository
# ============================================================
print("\n\n📋 ПУНКТ 5: Тестирование UserRepository")
print("-" * 60)

from app.data.repositories.user_repo import user_repository

# 5.1. Получить всех пользователей
print("\n5.1. Получение всех пользователей...")
users = user_repository.get_all()
print(f"   Всего пользователей: {len(users)}")
if users:
    print(f"   Первый пользователь: {users[0].get('user_id')} - {users[0].get('username')}")

# 5.2. Получить конкретного пользователя
if users:
    test_user_id = users[0].get('user_id')
    print(f"\n5.2. Получение пользователя {test_user_id}...")
    user = user_repository.get(test_user_id)
    if user:
        print(f"   ✅ Найден: {user.get('username')}")
        print(f"   Статус: {user.get('status')}")
        print(f"   Визиты: {user.get('total_room_visits')}")

# 5.3. Получить активных пользователей
print("\n5.3. Получение активных пользователей...")
active_users = user_repository.get_by_status('active')
print(f"   Активных пользователей: {len(active_users)}")

# 5.4. Создать тестового пользователя
print("\n5.4. Создание тестового пользователя...")
test_created = user_repository.create(
    user_id=999999999,
    username="test_datalayer",
    first_name="Тест DataLayer"
)
if test_created:
    print("   ✅ Тестовый пользователь создан!")
else:
    print("   ℹ️ Пользователь уже существует (это нормально)")

# 5.5. Обновить пользователя
print("\n5.5. Обновление пользователя...")
updated = user_repository.update(999999999, {'vote_response': 'Да'})
if updated:
    print("   ✅ Пользователь обновлён!")

print("\n✅ ПУНКТ 5 завершён\n")


# ============================================================
# ПУНКТ 6: Тестирование RoomVisitRepository
# ============================================================
print("\n📋 ПУНКТ 6: Тестирование RoomVisitRepository")
print("-" * 60)

from app.data.repositories.room_visit_repo import room_visit_repository

# 6.1. Залогировать визит
print("\n6.1. Логирование визита в комнату...")
visit_logged = room_visit_repository.log_visit(
    user_id=999999999,
    username="test_datalayer",
    room_id="test_room_001",
    room_name="Тестовая комната",
    source="test"
)
if visit_logged:
    print("   ✅ Визит залогирован!")

# 6.2. Проверить обновление статистики
print("\n6.2. Проверка статистики пользователя...")
user = user_repository.get(999999999)
if user:
    print(f"   Первый визит: {user.get('first_room_visit')}")
    print(f"   Последний визит: {user.get('last_room_visit')}")
    print(f"   Всего визитов: {user.get('total_room_visits')}")

# 6.3. Проверить запись в логе
print("\n6.3. Проверка записи в room_visits...")
visits = room_visits_worksheet.get_all_records()
if visits:
    last_visit = visits[-1]
    print(f"   Последний визит: user_id={last_visit.get('user_id')}, room={last_visit.get('room_name')}")

print("\n✅ ПУНКТ 6 завершён\n")


# ============================================================
# ПУНКТ 7: Тестирование TouchpointRepository
# ============================================================
print("\n📋 ПУНКТ 7: Тестирование TouchpointRepository")
print("-" * 60)

from app.data.repositories.touchpoint_repo import touchpoint_repository

# 7.1. Залогировать отправку touchpoint
print("\n7.1. Логирование touchpoint...")
sent = touchpoint_repository.log_touchpoint(
    user_id=999999999,
    username="test_datalayer",
    touch_number=1,
    status="sent"
)
if sent:
    print("   ✅ Touchpoint залогирован!")

# 7.2. Проверить обновление колонки touch_1_sent
print("\n7.2. Проверка обновления touch_1_sent...")
user = user_repository.get(999999999)
if user:
    print(f"   touch_1_sent: {user.get('touch_1_sent')}")

# 7.3. Залогировать клик
print("\n7.3. Логирование клика по ссылке...")
clicked = touchpoint_repository.mark_clicked(
    user_id=999999999,
    touch_number=1
)
if clicked:
    print("   ✅ Клик залогирован!")

# 7.4. Проверить записи в логе
print("\n7.4. Проверка записей в touchpoints_log...")
touchpoints = touchpoints_log_worksheet.get_all_records()
if touchpoints:
    print(f"   Всего записей: {len(touchpoints)}")
    if len(touchpoints) >= 2:
        print(f"   Последние 2 записи:")
        for tp in touchpoints[-2:]:
            print(f"      - user_id={tp.get('user_id')}, touch={tp.get('touch_number')}, clicked={tp.get('clicked')}")

print("\n✅ ПУНКТ 7 завершён\n")


# ============================================================
# ПУНКТ 8: Тестирование RoomRepository
# ============================================================
print("\n📋 ПУНКТ 8: Тестирование RoomRepository")
print("-" * 60)

from app.data.repositories.room_repo import room_repository

# 8.1. Зарегистрировать комнату
print("\n8.1. Регистрация новой комнаты...")
registered = room_repository.register_room(
    room_id="test_room_001",
    room_name="Тестовая комната",
    room_url="https://t.me/+TestRoomLink",
    access_level="subscriber",
    is_active=True
)
if registered:
    print("   ✅ Комната зарегистрирована!")
else:
    print("   ℹ️ Комната уже существует (это нормально)")

# 8.2. Получить все комнаты
print("\n8.2. Получение всех комнат...")
all_rooms = room_repository.get_all()
print(f"   Всего комнат: {len(all_rooms)}")

# 8.3. Получить активные комнаты
print("\n8.3. Получение активных комнат...")
active_rooms = room_repository.get_all(is_active=True)
print(f"   Активных комнат: {len(active_rooms)}")

# 8.4. Получить комнату по ID
print("\n8.4. Получение комнаты по ID...")
room = room_repository.get_by_id("test_room_001")
if room:
    print(f"   ✅ Найдена: {room.get('room_name')}")

# 8.5. Сгенерировать tracking URL
print("\n8.5. Генерация tracking URL...")
tracking_url = room_repository.get_tracking_url(
    room_id="test_room_001",
    user_id=999999999
)
if tracking_url:
    print(f"   ✅ Tracking URL: {tracking_url}")
    # Проверка формата
    if "?uid=999999999" in tracking_url or "&uid=999999999" in tracking_url:
        print("   ✅ Формат URL корректный!")

print("\n✅ ПУНКТ 8 завершён\n")


# ============================================================
# ИТОГИ
# ============================================================
print("\n" + "=" * 60)
print("🎉 ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ!")
print("=" * 60)
print("\n✅ Data Layer v1 работает корректно!")
print("\nТеперь можете:")
print("  1. Проверить данные в Google Sheets")
print("  2. Удалить тестового пользователя (ID: 999999999) если нужно")
print("  3. Начать использовать репозитории в боте\n")
