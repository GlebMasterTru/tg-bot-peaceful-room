import asyncio
from aiogram import F, Router
from aiogram.filters import Command, CommandStart, or_f
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatAction
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

import app.keyboards as kb
import app.texts as txt

from app.states import BroadcastStates
from app.database import (
    get_user, 
    add_user, 
    get_user_privileges, 
    get_links, 
    is_temporarily_vip_user, 
    migrate_single_user, 
    sync_user_subscription,
    get_subscription_status,
    get_all_users
)

ADMIN_ID = 749452956


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    print(f"🔥 START вызван! user_id={message.from_user.id}")
    
    try:
        await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        print("✅ ChatAction отправлен")
        
        user = message.from_user
        
        if is_temporarily_vip_user(user.username):
            if migrate_single_user(user.username, user.id):
                print(f"✅ VIP пользователь {user.username} мигрирован.")
            if not get_user(user.id):
                add_user(user.id, user.username, user.first_name)
        else:
            if not get_user(user.id):
                add_user(user.id, user.username, user.first_name)
        
        print("✅ Пользователь добавлен/проверен в БД")
        
        is_vip, is_diamond = get_user_privileges(user.id)
        print(f"✅ Привилегии: vip={is_vip}, diamond={is_diamond}")
        
        main_link, vip_link, diamond_link = get_links()
        print(f"✅ Ссылки получены")
        
        if is_vip and is_diamond:
            text = '<b>Ты в Тихой Комнате.</b>\nЗдесь можно не спешить.\nВозвращайся в любой момент в ту Комнату, что откликается сейчас.\n\nВсё уже настроено и ждёт тебя.'
        elif is_diamond:
            text = '<b>Ты в Тихой Комнате.</b>\nЗдесь можно не спешить.\nВозвращайся в любой момент в ту Комнату, что откликается сейчас.\n\nВсё уже настроено и ждёт тебя.'
        elif is_vip:
            text = f'Ты уже отвечала на Тихие Вопросы.\nПо ним я открыла для тебя две Комнаты — как отклик на то, что ты сейчас проживаешь.\n\nТы заходишь в живое пространство, созданное под твои состояния. Выбери то, что откликается сильнее.Тихо, без давления, с того места, где ты сейчас.\n\n⤷ Посмотри, какие Комнаты уже ждут тебя:\n{vip_link}'
        else:
            text = f'Тихая Комната — это живое пространство, которое откликается на твоё состояние.\n\nОдна из Комнат уже ждёт твоего первого шага. Она подскажет, с чего можно начать.\n\n⤷ Посмотри, какая Комната сейчас открыта:\n{main_link}'
        
        print(f"✅ Текст сформирован: {text[:50]}...")
        
        menu_keyboard = kb.get_main_menu(is_vip, is_diamond, main_link, vip_link, diamond_link)
        print("✅ Клавиатура создана")
        
        await message.answer(text, reply_markup=menu_keyboard)
        print("✅ Сообщение отправлено!")
        
    except Exception as e:
        print(f"❌❌❌ ОШИБКА В CMD_START: {e}")
        import traceback
        traceback.print_exc()


# НАВИГАЦИЯ - Переходы между меню

@router.callback_query(F.data == 'go_to_profile_menu')
async def go_to_profile(callback: CallbackQuery):
    await callback.answer(txt.NOTIFY_PROFILE)
    await callback.message.edit_text(
        txt.PROFILE_MENU_TEXT,
        reply_markup=kb.profile_menu
    )


@router.callback_query(F.data == 'go_to_room_entrance')
async def callback_room_entrance(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    # Получаем данные пользователя
    user = get_user(user_id)
    if not user:
        await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return
    
    is_diamond = user.get('is_diamond', False)
    
    # Этот обработчик должен вызываться только для Diamond
    if not is_diamond:
        await callback.answer("❌ Ошибка: доступ запрещён", show_alert=True)
        return
    
    # Получаем ссылку для Diamond комнаты
    _, _, diamond_link = get_links()
    
    text = txt.get_room_entrance_text(diamond_link)
    menu = kb.get_diamond_room_entrance_menu(diamond_link)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=menu,
        parse_mode='HTML'
    )
    
    await callback.answer()


@router.callback_query(F.data == 'go_to_diary_menu')
async def go_to_diary(callback: CallbackQuery):
    await callback.answer(txt.NOTIFY_DIARY)
    await callback.message.edit_text(
        txt.DIARY_MENU_TEXT,
        reply_markup=kb.diary_menu
    )


@router.callback_query(F.data == 'go_to_help_menu')
async def go_to_diary(callback: CallbackQuery):
    await callback.answer(txt.NOTIFY_HELP)
    await callback.message.edit_text(
        txt.HELP_MENU_TEXT,
        reply_markup=kb.help_menu
    )

# КНОПКИ "НАЗАД" - Возврат в предыдущие меню

@router.callback_query(F.data == 'back_to_main')
async def back_to_main(callback: CallbackQuery):
    await callback.answer(txt.NOTIFY_BACK)
    
    user = callback.from_user
    is_vip, is_diamond = get_user_privileges(user.id)
    main_link, vip_link, diamond_link = get_links()
    
    if is_vip and is_diamond:
        text = f'<b>Ты в Тихой Комнате.</b>\nЗдесь можно не спешить.\nВозвращайся в любой момент в ту Комнату, что откликается сейчас.\n\nВсё уже настроено и ждёт тебя.'
    elif is_diamond:
        text = f'<b>Ты в Тихой Комнате.</b>\nЗдесь можно не спешить.\nВозвращайся в любой момент в ту Комнату, что откликается сейчас.\n\nВсё уже настроено и ждёт тебя.'
    elif is_vip:
        text = f'Ты уже отвечала на Тихие Вопросы.\nПо ним я открыла для тебя две Комнаты — как отклик на то, что ты сейчас проживаешь.\n\nТы заходишь в живое пространство, созданное под твои состояния. Выбери то, что откликается сильнее.Тихо, без давления, с того места, где ты сейчас.\n\n⤷ Посмотри, какие Комнаты уже ждут тебя:\n{vip_link}'
    else:
        text = f'Тихая Комната — это живое пространство, которое откликается на твоё состояние.\n\nОдна из Комнат уже ждёт твоего первого шага. Она подскажет, с чего можно начать.\n\n⤷ Посмотри, какая Комната сейчас открыта:\n{main_link}'        
    
    # Получаем правильную клавиатуру
    menu_keyboard = kb.get_main_menu(is_vip, is_diamond, main_link, vip_link, diamond_link)
    
    try:
        await callback.message.edit_text(text, reply_markup=menu_keyboard)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise 


@router.callback_query(F.data == 'back_to_profile')
async def back_to_profile(callback: CallbackQuery):
    await callback.answer(txt.NOTIFY_BACK)
    await callback.message.edit_text(
        txt.PROFILE_MENU_TEXT,
        reply_markup=kb.profile_menu
    )


# ПРОВЕРКА ПОДПИСКИ

@router.callback_query(F.data == 'check_subscription')
async def check_subscription(callback: CallbackQuery):
    await callback.answer(txt.NOTIFY_CHECKING_SUBSCRIPTION)
    
    user_id = callback.from_user.id
    
    sub_info = get_subscription_status(user_id)
    
    if sub_info['status'] == 'active':
        # ✅ Подписка активна
        text = txt.CHECK_SUBSCRIPTION_ACTIVE_TEXT.format(
            end_date=sub_info['end_date']
        )
    elif sub_info['status'] == 'expiring_soon':
        # ⚠️ Подписка истекает скоро (1-3 дня)
        days_word = _get_days_word(sub_info['days_left'])
        text = f"⚠️ Внимание! Твоя подписка истекает через {sub_info['days_left']} {days_word}.\n\n"
        text += f"Последний день доступа: {sub_info['end_date']}\n\n"
        text += "Рекомендуем продлить заранее, чтобы не потерять доступ к Тихой Комнате."
    elif sub_info['status'] == 'expired':
        # ❌ Подписка истекла
        text = txt.CHECK_SUBSCRIPTION_EXPIRED_TEXT.format(
            end_date=sub_info['end_date']
        )
    elif sub_info['status'] == 'none':
        # ℹ️ Подписки никогда не было
        text = txt.CHECK_SUBSCRIPTION_NONE_TEXT
    else:
        # Ошибка или неизвестный статус
        text = "⚠️ Не удалось проверить статус подписки. Попробуйте позже или обратитесь в техподдержку."
    
    await callback.message.edit_text(
        text,
        reply_markup=kb.check_subscription_menu
    )


def _get_days_word(days):
    """Вспомогательная функция для склонения слова 'день'"""
    if days == 1:
        return "день"
    elif 2 <= days <= 4:
        return "дня"
    else:
        return "дней"


# ПРОДЛЕНИЕ ПОДПИСКИ

@router.callback_query(F.data == 'renew_subscription')
async def renew_subscription(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        txt.RENEW_SUBSCRIPTION_TEXT,
        reply_markup=kb.renew_subscription_menu
    )


@router.callback_query(F.data == 'verify_payment')
async def verify_payment(callback: CallbackQuery):
    # 1. Короткое уведомление вверху экрана
    await callback.answer(txt.NOTIFY_CHECKING_PAYMENT)
    
    # 2. Убираем клавиатуру и показываем процесс проверки
    await callback.message.edit_text(
        "⏳ Проверяю оплату, это может занять несколько секунд...",
        reply_markup=None  # Убираем кнопки - пользователь не может кликать!
    )
    
    # 3. Делаем синхронизацию с таблицей Тильды
    user_id = callback.from_user.id
    username = callback.from_user.username
    success, message, end_date = sync_user_subscription(user_id, username)
    
    # 4. Формируем текст результата
    if success:
        from app.database import format_date_for_user
        formatted_date = format_date_for_user(end_date)
        text = txt.PAYMENT_SUCCESS_TEXT.format(end_date=formatted_date)
    else:
        text = txt.PAYMENT_NOT_FOUND_TEXT
    
    # 5. Показываем результат и возвращаем клавиатуру
    try:
        await callback.message.edit_text(text, reply_markup=kb.renew_subscription_menu)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass  # Игнорируем - сообщение уже такое
        else:
            raise  # Пробрасываем другие ошибки


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

@router.message(Command("myid"))
async def cmd_myid(message: Message):
    await message.answer(
        f"👤 **Твои данные:**\n"
        f"• ID: `{message.from_user.id}`\n"
        f"• Username: @{message.from_user.username or 'не указан'}\n"
        f"• Имя: {message.from_user.first_name}",
        parse_mode="Markdown"
    )



# ============================================================================
# ТЕСТОВЫЕ ОБРАБОТЧИКИ (можно удалить перед деплоем)
# ============================================================================

@router.message(Command('help'))
async def get_help(message: Message):
    """Тестовая команда /help"""
    await message.answer('Это помощь!')


@router.message(F.text == 'Как дела?')
async def how_are_you(message: Message):
    """Тестовый обработчик текста"""
    await message.answer('Всё супер!')


@router.message(F.photo)
async def handle_photo(message: Message):
    """Тестовый обработчик фото"""
    file_id = message.photo[-1].file_id
    await message.answer_photo(file_id, caption='Вот твое фото!')


@router.message(F.video)
async def handle_video(message: Message):
    """Тестовый обработчик видео"""
    file_id = message.video.file_id
    await message.answer_video(file_id, caption='Вот твое видео!')


@router.message(F.sticker)
async def handle_sticker(message: Message):
    """Тестовый обработчик стикеров"""
    file_id = message.sticker.file_id
    await message.answer_sticker(file_id)


@router.message(or_f(Command('profile'), F.text == 'Профиль'))
async def cmd_profile(message: Message):
    """Тестовая команда /profile"""
    await message.answer(txt.START_MSG.format(
        user_id=message.from_user.id,
        username=message.from_user.username or 'не указан',
        first_name=message.from_user.first_name
    ))


# ============================================================================
# ПРИМЕЧАНИЯ ПО ДАЛЬНЕЙШЕЙ РАЗРАБОТКЕ
# ============================================================================
"""
TODO (будущие задачи):

1. Фоновая задача для автоматической проверки подписок:
   - Раз в 15 минут проверять все подписки
   - Обновлять is_sub_active на 'False', если sub_end < текущая дата
   - Отправлять уведомления пользователям:
     * За 3 дня до окончания
     * За 1 день до окончания
     * В день окончания подписки

2. HOT!!! Проверить в keyboards get_main_menu - неиспользуются room_link'и

3. Обработка ошибок:
   - Добавить try-except блоки для критических операций
   - Логирование ошибок в файл или внешний сервис
   - Уведомление администратора о критических сбоях

4. Аналитика:
   - Подсчет активных пользователей
   - Статистика продлений подписок
   - Отчеты по оплатам

5. Дополнительные функции:
   - История оплат пользователя
   - Реферальная система
   - Промокоды и скидки
"""