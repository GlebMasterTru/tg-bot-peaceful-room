import gspread
# import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
# from google.auth.exceptions import GoogleAuthError
# from gspread.exceptions import GSpreadException, WorksheetNotFound, APIError

load_dotenv()

service_account_file = os.getenv('SERVICE_ACCOUNT_FILE')
spreadsheet_id_db = os.getenv('SPREADSHEET_ID_DB')
spreadsheet_id_tilda_db = os.getenv('SPREADSHEET_ID_TILDA_DB')
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Подключаемся
creds = Credentials.from_service_account_file(service_account_file, scopes = SCOPES)
client = gspread.authorize(creds)

# MAIN DATA BASE
sheet = client.open_by_key(spreadsheet_id_db)
users_worksheet = sheet.worksheet("users")
config_worksheet = sheet.worksheet("config")
print(f"Подключен к листу: {users_worksheet.title}")
print(f"Количество строк: {users_worksheet.row_count}")
print(f"Подключен к листу: {config_worksheet.title}")
print(f"Количество строк: {config_worksheet.row_count}")

# TILDA DATA BASE
tilda_sheet = client.open_by_key(spreadsheet_id_tilda_db)
tilda_worksheet = tilda_sheet.worksheet("Лист1")
print(f"Подключен к листу: {tilda_worksheet.title}")
print(f"Количество строк: {tilda_worksheet.row_count}")


def get_user(user_id):
    try:
        cell = users_worksheet.find(str(user_id))
        if cell:
            row = users_worksheet.row_values(cell.row)
            headers = users_worksheet.row_values(1)
            return dict(zip(headers, row))
        return None
    except:
        return None


def add_user(user_id, username, first_name):
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [str(user_id), username, first_name, current_time, current_time, 'False']
        users_worksheet.append_row(new_row)
        return True
    except Exception as e:
        print(f"Неизвестная ошибка при добавлении пользователя: {e}")
        return False


def get_user_privileges(user_id):
    try:
        user_id_str = str(user_id)
        
        vip_list = [id.strip() for id in (config_worksheet.acell('D2').value or "").split(',')]
        is_vip = user_id_str in vip_list
        
        user = get_user(user_id)
        if user:
            is_diamond_value = user.get('is_diamond', 'False')
            is_diamond = (is_diamond_value == 'True')
        else:
            is_diamond = False
        
        return is_vip, is_diamond
    
    except Exception as e:
        print(f"Ошибка при проверке привилегий: {e}")
        return False, False
    

def get_links():
    main_link = config_worksheet.acell('A2').value or ""
    vip_link = config_worksheet.acell('B2').value or ""
    diamond_link = config_worksheet.acell('C2').value or ""
    return main_link, vip_link, diamond_link


def add_user_to_diamond_list(user_id):
    try:
        user_id_str = str(user_id)
        
        diamond_list_str = config_worksheet.acell('E2').value or ""
        diamond_list = [id.strip() for id in diamond_list_str.split(',') if id.strip()]
        
        if user_id_str not in diamond_list:
            diamond_list.append(user_id_str)
            
            config_worksheet.update('E2', [[','.join(diamond_list)]])
            print(f"✅ User {user_id} добавлен в Diamond список (config)")
            return True
        else:
            print(f"ℹ️ User {user_id} уже в Diamond списке")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка при добавлении в Diamond список: {e}")
        return False

def is_temporarily_vip_user(username):
    try:
        temporarily_vip_user_str = config_worksheet.acell('F2').value or ""
        temporarily_vip_user = [name.strip().lower() for name in temporarily_vip_user_str.split(',') if name.strip()]
        
        user_username = (username or "").lower().lstrip('@')
        
        return user_username in temporarily_vip_user
    except Exception as e:
        print(f"Ошибка при проверке вип списка по юзернеймам: {e}")
        return False


def migrate_single_user(username, user_id):
    try:
        true_vip_list_str = config_worksheet.acell('D2').value or ""
        true_vip_list = [id.strip() for id in true_vip_list_str.split(',') if id.strip()]
        
        temporarily_vip_user_str = config_worksheet.acell('F2').value or ""
        temporarily_vip_user = [name.strip().lower() for name in temporarily_vip_user_str.split(',') if name.strip()]
        
        user_username = username.lower().lstrip('@')
        
        if user_username in temporarily_vip_user:
            user_id_str = str(user_id)
            
            if user_id_str not in true_vip_list:
                true_vip_list.append(user_id_str)
            
            temporarily_vip_user.remove(user_username)
            
            config_worksheet.update('D2', [[','.join(true_vip_list)]])
            config_worksheet.update('F2', [[','.join(temporarily_vip_user)]])
            
            print(f"Пользователь {username} ({user_id}) перенесен из временного VIP-списка в активный.")
            return True
        
        return False
    except Exception as e:
        print(f"Ошибка при миграции пользователя {username}: {e}")
        return False

def migrate_many_users():
    try: 
        all_users = users_worksheet.get_all_records()
        
        true_vip_list_str = config_worksheet.acell('D2').value or ""
        true_vip_list = [id.strip() for id in true_vip_list_str.split(',') if id.strip()]
        
        temporarily_vip_user_str = config_worksheet.acell('F2').value or ""
        temporarily_vip_user = [name.strip().lower() for name in temporarily_vip_user_str.split(',') if name.strip()]
        
        migrated_count = 0
        updated_true_vip = true_vip_list.copy()
        updated_temporary = temporarily_vip_user.copy()
        
        for user in all_users:
            user_id = user.get('user_id')
            if not user_id:
                continue
            username = (user.get('username', '') or '').lstrip('@').lower()
            
            if username in updated_temporary:
                user_id_str = str(user_id)
                
                if user_id_str not in updated_true_vip:
                    updated_true_vip.append(user_id_str)
                    migrated_count += 1
                
                updated_temporary.remove(username)
                
        if migrated_count > 0:
            config_worksheet.update('D2', [[','.join(updated_true_vip)]])
            config_worksheet.update('F2', [[','.join(updated_temporary)]])
        
        if migrated_count == 1:
            print(f'Успешно перенесен {migrated_count} пользователь из временного vip-списка в основной')
        elif 2 <= migrated_count <= 4:
            print(f'Успешно перенесены {migrated_count} пользователя из временного vip-списка в основной')
        elif migrated_count >= 5:
            print(f'Успешно перенесены {migrated_count} пользователей из временного vip-списка в основной')
        else:
            print('Не найдено пользователей для переноса')
            
        return True
            
    except Exception as e:
        print(f"Ошибка при переносе никнеймов на ID: {e}")
        return False


def clean_telegram_username(raw_username):
    if not raw_username:
        return None
    
    username = str(raw_username).strip().lower()
    
    if username.startswith('@'):
        username = username[1:]
    
    if 't.me/' in username:
        username = username.split('t.me/')[-1]
    
    if 'https://t.me/' in username:
        username = username.split('https://t.me/')[-1]
    
    username = username.split('?')[0].rstrip('/')
    return username


def add_user_with_subscription(user_data):
    try:
        headers = users_worksheet.row_values(1)
        new_row = []
        for header in headers:
            value = user_data.get(header, '')
            new_row.append(str(value))
        
        users_worksheet.append_row(new_row)
        print(f"✅ Добавлен пользователь {user_data.get('username', '')} с подпиской")
        return True
    except Exception as e:
        print(f"❌ Ошибка при добавлении пользователя с подпиской: {e}")
        return False


def sync_user_subscription(user_id, user_username):
    try:
        # 1. Очищаем username
        cleaned_username = clean_telegram_username(user_username)
        if not cleaned_username:
            return False, "Не удалось определить ваш username. Обратитесь в поддержку.", None
        
        print(f"🔍 Синхронизация для пользователя: {cleaned_username} (ID: {user_id})")
        
        # 2. Получаем ВСЕ необработанные записи из таблицы Тильды
        all_tilda_records = tilda_worksheet.get_all_records()
        unprocessed_records = [
            record for record in all_tilda_records 
            if not record.get('processed', '')  # processed пустое = не обработано
        ]
        
        if not unprocessed_records:
            return False, "Новых оплат не найдено.", None
        
        # 3. Ищем записи, относящиеся к этому пользователю
        user_records = []
        for record in unprocessed_records:
            record_username = clean_telegram_username(record.get('Как_с_вами_связаться_в_Телеграм_username', ''))
            
            # Сравниваем очищенные username
            if record_username == cleaned_username:
                user_records.append(record)
        
        if not user_records:
            return False, "Оплаты для вашего username не найдены.", None
        
        print(f"📋 Найдено {len(user_records)} необработанных записей для {cleaned_username}")
        
        # 4. Извлекаем email и phone из найденных записей
        email = user_records[0].get('Email', '')
        phone = user_records[0].get('Phone', '')
        
        # 5. Находим максимальную дату окончания подписки
        max_end_date = None
        for record in user_records:
            end_date_str = record.get('valid to', '')
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')
                if max_end_date is None or end_date > max_end_date:
                    max_end_date = end_date
            except ValueError as e:
                print(f"⚠️ Ошибка парсинга даты {end_date_str}: {e}")
                continue
        
        if not max_end_date:
            return False, "Не удалось определить дату окончания подписки.", None
        
        tilda_start_date = user_records[0].get('Дата начала подписки', '')
        if not tilda_start_date:
            tilda_start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        tilda_max_end_date_str = max_end_date.strftime('%Y-%m-%d %H:%M:%S')
        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # ← ДРУГОЕ ИМЯ!
        
        # 6. Проверяем, есть ли пользователь в нашей основной базе
        existing_user = get_user(user_id)
        
        if existing_user:
            # 7. ПАКЕТНОЕ обновление существующего пользователя
            update_data = {
                'username': user_username,
                'last_activity': current_time_str,
                'is_diamond': 'True',
                'is_sub_active': 'True',
                'sub_start': tilda_start_date,
                'sub_end': tilda_max_end_date_str, 
                'last_updated_info': current_time_str
            }
            
            # Добавляем email и phone, если их еще нет
            if not existing_user.get('email') and email:
                update_data['email'] = email
            if not existing_user.get('phone') and phone:
                update_data['phone_number'] = phone
            
            # ОДИН запрос для обновления всех полей
            success = update_user_batch(user_id, update_data)
            if not success:
                return False, "Ошибка при обновлении данных.", None
                
            message = f"✅ Ваша подписка обновлена! Активна до {max_end_date.strftime('%d.%m.%Y')}"
            
        else:
            # 8. Добавляем нового пользователя с подпиской
            new_user_data = {
                'user_id': str(user_id),
                'username': user_username,
                'email': email,
                'phone_number': phone,
                'sub_start': user_records[0].get('Дата начала подписки', current_time_str),
                'sub_end': tilda_max_end_date_str,
                'is_sub_active': 'True',
                'joined_at': current_time_str,
                'last_activity': current_time_str
            }
            
            success = add_user_with_subscription(new_user_data)
            if not success:
                return False, "Ошибка при добавлении пользователя.", None
                
            message = f"🎉 Добро пожаловать! Ваша подписка активна до {max_end_date.strftime('%d.%m.%Y')}"
        
        # 9. Помечаем все обработанные записи как TRUE
        processed_updates = []
        for record in user_records:
            try:
                username_to_find = record['Как_с_вами_связаться_в_Телеграм_username']
                cell = tilda_worksheet.find(username_to_find)
                
                if cell:
                    row_data = tilda_worksheet.row_values(cell.row)
                    
                    expected_email = record.get('Email', '')
                    actual_email = row_data[1]  # email в 2-м столбце (индекс 1)
                    
                    if expected_email and actual_email == expected_email:
                        processed_updates.append({
                            'range': f"T{cell.row}", # Столбец 20 - processed
                            'values': [['TRUE']]
                        })
                        print(f"✅ Помечена строка {cell.row} для {username_to_find}")
                    else:
                        print(f"⚠️ Несоответствие данных для {username_to_find}")
                else:
                    print(f"❌ Не найдена строка для {username_to_find}")
                    
            except Exception as e:
                print(f"❌ Ошибка при обработке записи {record}: {e}")
                continue

        if processed_updates:
            tilda_worksheet.batch_update(processed_updates)
            
        print(f"✅ Успешно синхронизировано для {cleaned_username}")
        return True, message, tilda_max_end_date_str
        
    except Exception as e:
        error_msg = f"❌ Ошибка при синхронизации подписки: {e}"
        print(error_msg)
        return False, "Произошла ошибка при проверке подписки. Пожалуйста, попробуйте позже.", None
    

def update_user_batch(user_id, update_dict):
    try:
        cell = users_worksheet.find(str(user_id))
        if not cell:
            print(f"❌ Пользователь {user_id} не найден в таблице")
            return False
        
        headers = users_worksheet.row_values(1)
        
        update_data = []
        
        for field_name, new_value in update_dict.items():
            if field_name in headers:
                # Находим номер столбца (начинается с 1)
                col_index = headers.index(field_name) + 1
                
                # Преобразуем номер строки и столбца в формат A1 (например: 'B5')
                cell_range = f"{gspread.utils.rowcol_to_a1(cell.row, col_index)}"
                
                update_data.append({
                    'range': cell_range,           # Какую ячейку обновляем
                    'values': [[str(new_value)]]   # Какое значение записываем
                })
            else:
                print(f"⚠️ Столбец '{field_name}' не найден в таблице")
        
        if update_data:
            users_worksheet.batch_update(update_data)
            print(f"✅ Пакетное обновление для user_id {user_id}: {list(update_dict.keys())}")
            return True
        else:
            print("⚠️ Нет данных для обновления")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка при пакетном обновлении: {e}")
        return False
    

def format_date_for_user(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        return date_obj.strftime('%d.%m.%Y')
    except Exception as e:
        print(f"⚠️ Ошибка форматирования даты {date_str}: {e}")
        return date_str  # Возвращаем как есть, если не удалось распарсить


def get_subscription_status(user_id):
    try:
        user = get_user(user_id)
        
        if not user:
            return {
                'status': 'none',
                'is_sub_active': False,
                'end_date': None,
                'end_date_raw': None,
                'days_left': None
            }
        
        sub_end = user.get('sub_end', '')
        is_sub_active = user.get('is_sub_active', '')
        
        
        if not sub_end or not is_sub_active:
            return {
                'status': 'none',
                'is_sub_active': False,
                'end_date': None,
                'end_date_raw': None,
                'days_left': None
            }
        
        if is_sub_active == 'False':
            return {
                'status': 'expired',
                'is_sub_active': False,
                'end_date': format_date_for_user(sub_end),
                'end_date_raw': sub_end,
                'days_left': 0
            }
        
        if is_sub_active == 'True':
            try:
                end_date_obj = datetime.strptime(sub_end, '%Y-%m-%d %H:%M:%S')
                current_date = datetime.now()

                days_left = (end_date_obj - current_date).days
                
                if days_left > 3:
                    status = 'active'  # ✅ Подписка активна
                elif 1 <= days_left <= 3:
                    status = 'expiring_soon'  # ⚠️ Подписка истекает скоро
                else:
                    # Подписка технически истекла, но is_sub_active еще True
                    # (фоновая задача еще не обновила статус)
                    status = 'expired'
                
                return {
                    'status': status,
                    'is_sub_active': True,
                    'end_date': format_date_for_user(sub_end),
                    'end_date_raw': sub_end,
                    'days_left': days_left if days_left > 0 else 0
                }
                
            except ValueError as e:
                print(f"❌ Ошибка парсинга даты окончания подписки: {e}")
                return {
                    'status': 'error',
                    'is_sub_active': False,
                    'end_date': None,
                    'end_date_raw': sub_end,
                    'days_left': None
                }
        
        # 6. На всякий случай - неизвестный статус
        return {
            'status': 'unknown',
            'is_sub_active': False,
            'end_date': None,
            'end_date_raw': sub_end,
            'days_left': None
        }
        
    except Exception as e:
        print(f"❌ Ошибка при проверке статуса подписки для user_id {user_id}: {e}")
        return {
            'status': 'error',
            'is_sub_active': False,
            'end_date': None,
            'end_date_raw': None,
            'days_left': None
        }
        

def process_all_pending_payments():
    try:
        # Получаем ВСЕ необработанные записи
        all_tilda_records = tilda_worksheet.get_all_records()
        unprocessed_records = [
            record for record in all_tilda_records 
            if not record.get('processed', '')
        ]
        
        if not unprocessed_records:
            print("ℹ️ Нет необработанных оплат")
            return []
        
        print(f"📋 Найдено {len(unprocessed_records)} необработанных оплат")
        
        notified_users = []  # Список user_id для уведомлений
        
        # Группируем записи по username
        from collections import defaultdict
        records_by_username = defaultdict(list)
        
        for record in unprocessed_records:
            username = clean_telegram_username(record.get('Как_с_вами_связаться_в_Телеграм_username', ''))
            if username:
                records_by_username[username].append(record)
        
        # Обрабатываем каждого пользователя
        for username, user_records in records_by_username.items():
            print(f"🔍 Обработка для пользователя: {username}")
            
            # Ищем user_id по username в таблице users
            user = None
            all_users = users_worksheet.get_all_records()
            for u in all_users:
                user_username = clean_telegram_username(u.get('username', ''))
                if user_username == username:
                    user = u
                    break
            
            if not user:
                print(f"⚠️ Пользователь {username} не найден в базе, пропускаем")
                continue
            
            user_id = user.get('user_id')
            if not user_id:
                print(f"⚠️ У пользователя {username} нет user_id")
                continue
            
            # Извлекаем данные
            email = user_records[0].get('Email', '')
            phone = user_records[0].get('Phone', '')
            
            # Находим максимальную дату окончания
            max_end_date = None
            for record in user_records:
                end_date_str = record.get('valid to', '')
                try:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')
                    if max_end_date is None or end_date > max_end_date:
                        max_end_date = end_date
                except ValueError:
                    continue
            
            if not max_end_date:
                print(f"⚠️ Не удалось определить дату окончания для {username}")
                continue
            
            tilda_start_date = user_records[0].get('Дата начала подписки', '')
            if not tilda_start_date:
                tilda_start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            tilda_max_end_date_str = max_end_date.strftime('%Y-%m-%d %H:%M:%S')
            current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Обновляем пользователя
            update_data = {
                'username': f"@{username}",
                'last_activity': current_time_str,
                'is_diamond': 'True',
                'is_sub_active': 'True',
                'sub_start': tilda_start_date,
                'sub_end': tilda_max_end_date_str,
                'last_updated_info': current_time_str
            }
            
            if not user.get('email') and email:
                update_data['email'] = email
            if not user.get('phone_number') and phone:
                update_data['phone_number'] = phone
            
            # Пакетное обновление
            success = update_user_batch(user_id, update_data)
            if success:
                add_user_to_diamond_list(user_id)
                
                notified_users.append(user_id)
                print(f"✅ Обновлен пользователь {username} (ID: {user_id})")
            
            # Помечаем записи как обработанные
            processed_updates = []
            for record in user_records:
                try:
                    username_to_find = record['Как_с_вами_связаться_в_Телеграм_username']
                    expected_email = record.get('Email', '')
                    expected_valid_to = record.get('valid to', '')
                    
                    print(f"🔍 Ищу в таблице: username='{username_to_find}', email='{expected_email}', payment='{expected_valid_to}'")
                    
                    cells = tilda_worksheet.findall(username_to_find)
                    print(f"📍 Найдено {len(cells)} ячеек с этим username")
                    
                    for cell in cells:
                        for cell in cells:
                            row_data = tilda_worksheet.row_values(cell.row)
                            
                            print(f"  DEBUG строка {cell.row}: длина={len(row_data)}")
                            print(f"  DEBUG первые 20 элементов: {row_data[:20]}")  # Посмотрим на структуру
                            
                            actual_email = row_data[1] if len(row_data) > 1 else ''
                            actual_valid_to = row_data[17] if len(row_data) > 17 else ''
                            
                            print(f"  Строка {cell.row}: email='{actual_email}', valid_to='{actual_valid_to}'")
                        
                        if (expected_email and actual_email == expected_email and 
                            expected_valid_to and actual_valid_to == expected_valid_to):
                            
                            print(f"✅ СОВПАДЕНИЕ! Помечаю строку {cell.row}")
                            processed_updates.append({
                                'range': f"T{cell.row}",
                                'values': [['TRUE']]
                            })
                            break
                        else:
                            print(f"❌ НЕ совпало: email match={actual_email == expected_email}, payment match={actual_valid_to == expected_valid_to}")
                            
                except Exception as e:
                    print(f"❌ Ошибка при обработке записи: {e}")
                    continue

            if processed_updates:
                tilda_worksheet.batch_update(processed_updates)
        
        print(f"✅ Обработано {len(notified_users)} пользователей для уведомления")
        return notified_users
        
    except Exception as e:
        print(f"❌ Ошибка при обработке оплат: {e}")
        return []


def sync_is_vip_for_all_users():
    try:
        vip_list_str = config_worksheet.acell('D2').value or ""
        vip_list = [id.strip() for id in vip_list_str.split(',') if id.strip()]
        
        all_users = users_worksheet.get_all_records()
        
        # Подготавливаем пакетное обновление
        updates = []
        synced_count = 0
        
        for idx, user in enumerate(all_users, start=2):  # Начинаем с 2, т.к. строка 1 - заголовки
            user_id = str(user.get('user_id', ''))
            current_is_vip = user.get('is_vip', '')
            
            # Определяем правильное значение
            should_be_vip = 'True' if user_id in vip_list else 'False'
            
            # Если значение отличается - добавляем в обновление
            if current_is_vip != should_be_vip:
                updates.append({
                    'range': f'F{idx}',  # Столбец F - is_vip
                    'values': [[should_be_vip]]
                })
                synced_count += 1
        
        if updates:
            users_worksheet.batch_update(updates)
            print(f"✅ Синхронизировано is_vip для {synced_count} пользователей")
        else:
            print("ℹ️ Все значения is_vip уже актуальны")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при синхронизации is_vip: {e}")
        return False