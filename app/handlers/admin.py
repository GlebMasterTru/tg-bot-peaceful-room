"""
Обработчики для администратора
Рассылки, статистика, управление
"""

import asyncio
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

import app.keyboards as kb
from app.states import BroadcastStates
from app.database import get_all_users
from app.filters import IsAdmin
from app.config import ADMIN_ID


router = Router()

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    # Проверка админа
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У тебя нет доступа к этой команде.")
        return
    
    await message.answer(
        "📝 **Создание рассылки**\n\n"
        "Отправь текст, который нужно разослать всем пользователям.\n\n"
        "Для отмены отправь /cancel",
        parse_mode="Markdown"
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


@router.message(BroadcastStates.waiting_for_text)
async def process_broadcast_text(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    # Сохраняем ID сообщения и чата
    await state.update_data(
        message_id=message.message_id,
        chat_id=message.chat.id
    )
    
    # Показываем превью с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Отправить всем", 
                callback_data="broadcast_confirm"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отмена", 
                callback_data="broadcast_cancel"
            )
        ]
    ])
    
    await message.answer(
        f"📢 **ПРЕВЬЮ РАССЫЛКИ:**\n\n"
        f"👆 Сообщение выше будет отправлено ВСЕМ пользователям.\n\n"
        f"Подтверждаешь?",
        reply_markup=keyboard,
        parse_mode="Markdown"
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
            
            # Задержка против бана, 100ms
            await asyncio.sleep(0.10)
            
        except TelegramForbiddenError:
            blocked += 1
        except TelegramBadRequest as e:
            errors += 1
            print(f"⚠️ Ошибка отправки {user_id}: {e}")
        except Exception as e:
            errors += 1
            print(f"❌ Неизвестная ошибка {user_id}: {e}")
    
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
