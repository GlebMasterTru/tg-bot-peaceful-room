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

from app.utils.formatters import get_days_word


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
        days_word = get_days_word(sub_info['days_left'])
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


