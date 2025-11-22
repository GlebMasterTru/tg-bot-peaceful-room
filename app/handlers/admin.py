import asyncio
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

import app.keyboards as kb
from app.states import BroadcastStates
from app.database import get_all_users, get_vote_stats
from app.filters import IsAdmin
from app.config import ADMIN_ID


router = Router()


@router.message(Command("myid"))
async def cmd_myid(message: Message):
    """Показать информацию о пользователе (для отладки)"""
    user_id = message.from_user.id
    username = message.from_user.username or "Не указан"
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    full_name = f"{first_name} {last_name}".strip() or "Не указано"

    text = (
        f"👤 **Информация о пользователе:**\n\n"
        f"🆔 ID: `{user_id}`\n"
        f"📝 Username: @{username}\n"
        f"🏷 Имя: {full_name}"
    )

    await message.answer(text, parse_mode="Markdown")


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    # Проверка админа
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У тебя нет доступа к этой команде.")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
                text="❌ Отмена", 
                callback_data="broadcast_cancel")]
        ]
    )
    
    await message.answer(
        "📝 Создание рассылки\n\n"
        "Отправь текст, который нужно разослать всем пользователям.\n\n"
        "⚠️ <b>***Важно!:***</b>\n"
        "• Только ОДНО вложение в сообщении!\n"
        "• Несколько файлов сразу не поддерживаются (например документ+видео+фото+документ)\n\n"
        "Поддерживаемые форматы:\n"
        "• Текст\n"
        "• Текст + [фото / видео / документ / гифка / аудио / файл, и т.д.] <b>- НО НЕ БОЛЬШЕ ОДНОГО ФАЙЛА</b>\n"
        "• Видео/голосовое сообщение\n\n"
        "Для отмены нажми кнопку или отправь /cancel",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    await state.set_state(BroadcastStates.waiting_for_text)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ Нечего отменять.")
        return

    await state.clear()
    await message.answer("❌ Рассылка отменена.")


@router.message(BroadcastStates.waiting_for_text)
async def process_broadcast_text(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    await state.update_data(
        message_id=message.message_id,
        chat_id=message.chat.id
    )
    
    await message.copy_to(chat_id=message.chat.id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
                text="✅ Отправить всем", 
                callback_data="broadcast_confirm")],
        [InlineKeyboardButton(
                text="❌ Отмена", 
                callback_data="broadcast_cancel")]
        ]
    )
    
    await message.answer(
        "📢 <b>ПРЕВЬЮ РАССЫЛКИ</b>\n\n"
        "👆 Сообщение выше будет отправлено ВСЕМ пользователям "
        "(со всеми фото, видео, текстом и форматированием).\n\n"
        "Подтверждаешь?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await state.set_state(BroadcastStates.waiting_for_confirmation)


@router.callback_query(F.data == "broadcast_cancel")
async def callback_broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена рассылки"""
    if callback.from_user.id != ADMIN_ID:
        return
    
    await state.clear()
    await callback.message.edit_text("❌ Рассылка отменена.")
    await callback.answer()


@router.callback_query(F.data == "broadcast_confirm", BroadcastStates.waiting_for_confirmation)
async def callback_broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и запуск рассылки"""
    if callback.from_user.id != ADMIN_ID:
        return
    
    # Получаем данные из FSM
    data = await state.get_data()
    message_id = data.get('message_id')
    chat_id = data.get('chat_id')
    
    if not message_id or not chat_id:
        await callback.message.edit_text("❌ Ошибка: сообщение не найдено.")
        await state.clear()
        return
    
    await callback.message.edit_text("🚀 Начинаю рассылку...")
    await callback.answer()
    
    # Получаем всех пользователей
    from app.database import get_all_users
    users = get_all_users()
    
    if not users:
        await callback.message.edit_text("❌ Не найдено пользователей для рассылки.")
        await state.clear()
        return
    
    total = len(users)
    success = 0
    blocked = 0
    errors = 0
    
    # РАССЫЛКА через copy_message
    for i, user in enumerate(users, 1):
        try:
            user_id = user['user_id']
            
            # Копируем сообщение целиком (с фото/видео/документами)
            await callback.bot.copy_message(
                chat_id=user_id,
                from_chat_id=chat_id,
                message_id=message_id
            )
            success += 1
            
            # Обновление прогресса каждые 50 пользователей
            if i % 50 == 0:
                try:
                    await callback.message.edit_text(
                        f"🚀 **Рассылка в процессе...**\n\n"
                        f"📊 Прогресс: {i}/{total} ({int(i/total*100)}%)\n"
                        f"✅ Отправлено: {success}\n"
                        f"🚫 Заблокировали: {blocked}\n"
                        f"⚠️ Ошибки: {errors}",
                        parse_mode="Markdown"
                    )
                except:
                    pass
            
            # Задержка против бана
            await asyncio.sleep(0.10)
            
        except TelegramForbiddenError:
            blocked += 1
            print(f"🚫 Пользователь {user_id} заблокировал бота")
        except TelegramBadRequest as e:
            errors += 1
            # 👇 ДОБАВЬ ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ!
            print(f"⚠️ BadRequest для {user_id}: {e}")
            print(f"   from_chat_id={chat_id}, message_id={message_id}")
        except Exception as e:
            errors += 1
            # 👇 ЛОГИРУЕМ ТИП ОШИБКИ!
            print(f"❌ Неизвестная ошибка {user_id}: {type(e).__name__}: {e}")
    
    # Финальный отчёт
    await callback.message.edit_text(
        f"✅ **Рассылка завершена!**\n\n"
        f"📊 **Статистика:**\n"
        f"• Всего пользователей: {total}\n"
        f"• ✅ Успешно: {success}\n"
        f"• 🚫 Заблокировали бота: {blocked}\n"
        f"• ⚠️ Ошибки: {errors}\n\n"
        f"📈 Успешность: {int(success/total*100) if total > 0 else 0}%",
        parse_mode="Markdown"
    )

    await state.clear()


@router.message(Command("vote_stats"), IsAdmin())
async def cmd_vote_stats(message: Message):
    """Показать статистику голосования (только для админа)"""
    stats = get_vote_stats()

    text = (
        "📊 <b>Статистика голосования (Декабрь 2025)</b>\n\n"
        f"1️⃣ <b>Вариант 1:</b> {stats['1']} человек\n"
        f"   <i>«Я всё понимаю, но не могу по-другому»</i>\n\n"
        f"2️⃣ <b>Вариант 2:</b> {stats['2']} человек\n"
        f"   <i>«Мне стыдно отдыхать»</i>\n\n"
        f"3️⃣ <b>Вариант 3:</b> {stats['3']} человек\n"
        f"   <i>«Я не могу просить»</i>\n\n"
        f"📈 <b>Всего проголосовало:</b> {stats['total']}\n"
        f"⏳ <b>Не проголосовали:</b> {stats['not_voted']}"
    )

    await message.answer(text, parse_mode="HTML")


@router.message(Command("send_vote"), IsAdmin())
async def cmd_send_vote(message: Message):
    """Отправить голосование всем пользователям (только для админа)"""

    vote_text = """✨ Тихое приглашение

В Тихой Комнате каждая новая Комната появляется только из вашего отклика.
Не по плану. Не по алгоритму.

Вы пишете — а я слышу.
Ваш импульс — мой отклик.

И всё, что вы видите в Комнатах: тексты, цвет, ритм, маленькие штрихи — я собираю вручную.
Своими руками.
Под вас.

В декабре я открою новую Комнату.
И хочу понять, где вы сейчас.

1️⃣ «Я всё понимаю, но не могу по-другому».
«почему я всё время возвращаюсь в одну и ту же точку?»

2️⃣ «Мне стыдно отдыхать».
«остановилась — и уже виновата»

3️⃣ «Я не могу просить».
«лучше молчать, чем получить отказ»

Выбери цифру 1, 2 или 3.
И я соберу Комнату под твой голос.

И пока она готовится — загляни в те, что уже открыты.
Я дополняю их каждую неделю.

🌿 Я рядом."""

    await message.answer("🚀 Начинаю рассылку голосования...")

    # Получаем всех пользователей
    users = get_all_users()

    if not users:
        await message.answer("❌ Не найдено пользователей для рассылки.")
        return

    total = len(users)
    success = 0
    blocked = 0
    errors = 0

    # РАССЫЛКА
    for i, user in enumerate(users, 1):
        try:
            user_id = user['user_id']

            await message.bot.send_message(
                chat_id=user_id,
                text=vote_text,
                reply_markup=kb.vote_menu
            )
            success += 1

            # Обновление прогресса каждые 50 пользователей
            if i % 50 == 0:
                try:
                    await message.answer(
                        f"🚀 Прогресс: {i}/{total} ({int(i/total*100)}%)\n"
                        f"✅ Отправлено: {success}\n"
                        f"🚫 Заблокировали: {blocked}\n"
                        f"⚠️ Ошибки: {errors}"
                    )
                except:
                    pass

            # Задержка против бана
            await asyncio.sleep(0.10)

        except TelegramForbiddenError:
            blocked += 1
            print(f"🚫 Пользователь {user_id} заблокировал бота")
        except Exception as e:
            errors += 1
            print(f"❌ Ошибка для {user_id}: {type(e).__name__}: {e}")

    # Финальный отчёт
    await message.answer(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Всего пользователей: {total}\n"
        f"• ✅ Успешно: {success}\n"
        f"• 🚫 Заблокировали бота: {blocked}\n"
        f"• ⚠️ Ошибки: {errors}\n\n"
        f"📈 Успешность: {int(success/total*100) if total > 0 else 0}%",
        parse_mode="HTML"
    )
