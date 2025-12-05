"""
Тестовый скрипт для проверки DataLayer v1

Проверяет:
- Подключение к репозиториям
- Базовые операции CRUD
- Взаимодействие между репозиториями
"""

import sys
from datetime import datetime


def test_user_repo():
    """Тест UserRepository"""
    print("\n" + "="*60)
    print("ТЕСТ: UserRepository")
    print("="*60)

    try:
        from app.data import user_repo

        # 1. Проверка get_all()
        print("\n1️⃣ Тест get_all()...")
        users = user_repo.get_all()
        print(f"✅ Найдено пользователей: {len(users)}")

        if users:
            first_user = users[0]
            print(f"   Пример: user_id={first_user.get('user_id')}, username={first_user.get('username')}")

            # 2. Проверка get()
            print("\n2️⃣ Тест get()...")
            user_id = first_user.get('user_id')
            user = user_repo.get(user_id)
            if user:
                print(f"✅ Пользователь {user_id} найден")
                print(f"   status: {user.get('status')}")
                print(f"   total_room_visits: {user.get('total_room_visits')}")
            else:
                print(f"❌ Пользователь {user_id} не найден")

        # 3. Проверка get_by_status()
        print("\n3️⃣ Тест get_by_status('active')...")
        active_users = user_repo.get_by_status('active')
        print(f"✅ Активных пользователей: {len(active_users)}")

        return True

    except Exception as e:
        print(f"❌ Ошибка в UserRepository: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_room_repo():
    """Тест RoomRepository"""
    print("\n" + "="*60)
    print("ТЕСТ: RoomRepository")
    print("="*60)

    try:
        from app.data import room_repo

        # 1. Проверка get_all_active()
        print("\n1️⃣ Тест get_all_active()...")
        rooms = room_repo.get_all_active()
        print(f"✅ Активных комнат: {len(rooms)}")

        if rooms:
            first_room = rooms[0]
            room_id = first_room.get('room_id')
            print(f"   Пример: room_id={room_id}, room_name={first_room.get('room_name')}")

            # 2. Проверка get_by_id()
            print("\n2️⃣ Тест get_by_id()...")
            room = room_repo.get_by_id(room_id)
            if room:
                print(f"✅ Комната {room_id} найдена")

            # 3. Проверка get_tracking_url()
            print("\n3️⃣ Тест get_tracking_url()...")
            tracking_url = room_repo.get_tracking_url(room_id, 123456)
            if tracking_url:
                print(f"✅ Tracking URL: {tracking_url[:50]}...")
        else:
            print("⚠️ Нет активных комнат в rooms_registry")

        return True

    except Exception as e:
        print(f"❌ Ошибка в RoomRepository: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_room_visit_repo():
    """Тест RoomVisitRepository"""
    print("\n" + "="*60)
    print("ТЕСТ: RoomVisitRepository")
    print("="*60)

    try:
        from app.data import room_visit_repo

        print("\n1️⃣ Тест log_visit() - ПРОПУЩЕН")
        print("   (Требует реальных данных, проверяется вручную)")

        print("\n2️⃣ Тест get_by_user()...")
        # Пробуем получить посещения для любого пользователя
        from app.data import user_repo
        users = user_repo.get_all()
        if users:
            test_user_id = users[0].get('user_id')
            visits = room_visit_repo.get_by_user(test_user_id)
            print(f"✅ Посещений для пользователя {test_user_id}: {len(visits)}")

        return True

    except Exception as e:
        print(f"❌ Ошибка в RoomVisitRepository: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_touchpoint_repo():
    """Тест TouchpointRepository"""
    print("\n" + "="*60)
    print("ТЕСТ: TouchpointRepository")
    print("="*60)

    try:
        from app.data import touchpoint_repo

        print("\n1️⃣ Тест log_touchpoint() - ПРОПУЩЕН")
        print("   (Требует реальных данных, проверяется вручную)")

        print("\n2️⃣ Тест get_by_user()...")
        from app.data import user_repo
        users = user_repo.get_all()
        if users:
            test_user_id = users[0].get('user_id')
            touchpoints = touchpoint_repo.get_by_user(test_user_id)
            print(f"✅ Touchpoints для пользователя {test_user_id}: {len(touchpoints)}")

        return True

    except Exception as e:
        print(f"❌ Ошибка в TouchpointRepository: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Запуск всех тестов"""
    print("\n" + "="*60)
    print("🧪 ТЕСТИРОВАНИЕ DATA LAYER V1")
    print("="*60)

    results = {
        'UserRepository': test_user_repo(),
        'RoomRepository': test_room_repo(),
        'RoomVisitRepository': test_room_visit_repo(),
        'TouchpointRepository': test_touchpoint_repo(),
    }

    print("\n" + "="*60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*60)

    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 Все тесты пройдены успешно!")
    else:
        print("\n⚠️ Некоторые тесты не прошли")

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
