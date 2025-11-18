"""
Подключение к Google Sheets API
Централизованная инициализация клиента и рабочих листов
"""

import os
import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

# Загружаем переменные окружения
load_dotenv()

# Параметры подключения
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')
SPREADSHEET_ID_DB = os.getenv('SPREADSHEET_ID_DB')
SPREADSHEET_ID_TILDA_DB = os.getenv('SPREADSHEET_ID_TILDA_DB')
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


# ============================================================================
# ИНИЦИАЛИЗАЦИЯ КЛИЕНТА
# ============================================================================

def init_google_sheets_client():
    """
    Создаёт и возвращает авторизованный клиент Google Sheets

    Returns:
        gspread.Client: Авторизованный клиент для работы с Google Sheets
    """
    try:
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES
        )
        client = gspread.authorize(creds)
        print("✅ Успешное подключение к Google Sheets API")
        return client
    except Exception as e:
        print(f"❌ Ошибка подключения к Google Sheets: {e}")
        raise


# Глобальный клиент (инициализируется при импорте модуля)
client = init_google_sheets_client()


# ============================================================================
# ПОЛУЧЕНИЕ РАБОЧИХ ЛИСТОВ
# ============================================================================

def get_users_worksheet():
    """
    Возвращает лист 'users' из основной БД

    Returns:
        gspread.Worksheet: Лист с данными пользователей
    """
    try:
        sheet = client.open_by_key(SPREADSHEET_ID_DB)
        worksheet = sheet.worksheet("users")
        print(f"📊 Подключен к листу: {worksheet.title} ({worksheet.row_count} строк)")
        return worksheet
    except Exception as e:
        print(f"❌ Ошибка получения листа 'users': {e}")
        raise


def get_config_worksheet():
    """
    Возвращает лист 'config' из основной БД

    Returns:
        gspread.Worksheet: Лист с конфигурацией бота
    """
    try:
        sheet = client.open_by_key(SPREADSHEET_ID_DB)
        worksheet = sheet.worksheet("config")
        print(f"⚙️ Подключен к листу: {worksheet.title} ({worksheet.row_count} строк)")
        return worksheet
    except Exception as e:
        print(f"❌ Ошибка получения листа 'config': {e}")
        raise


def get_tilda_worksheet():
    """
    Возвращает лист 'Лист1' из БД Tilda (платежи)

    Returns:
        gspread.Worksheet: Лист с данными о платежах из Tilda
    """
    try:
        sheet = client.open_by_key(SPREADSHEET_ID_TILDA_DB)
        worksheet = sheet.worksheet("Лист1")
        print(f"💳 Подключен к листу: {worksheet.title} ({worksheet.row_count} строк)")
        return worksheet
    except Exception as e:
        print(f"❌ Ошибка получения листа Tilda: {e}")
        raise


# ============================================================================
# ИНИЦИАЛИЗАЦИЯ ЛИСТОВ (при импорте модуля)
# ============================================================================

# Основные листы (инициализируются сразу)
users_worksheet = get_users_worksheet()
config_worksheet = get_config_worksheet()
tilda_worksheet = get_tilda_worksheet()

print("✅ Все листы успешно инициализированы\n")


# ============================================================================
# ПРИМЕЧАНИЯ ПО ИСПОЛЬЗОВАНИЮ
# ============================================================================

"""
Как использовать:

В других модулях:
    from app.database.connection import users_worksheet, config_worksheet, tilda_worksheet

    # Чтение данных
    all_users = users_worksheet.get_all_records()

    # Поиск ячейки
    cell = users_worksheet.find(str(user_id))

    # Обновление
    users_worksheet.update('A2', [['new_value']])

Преимущества:
    - Подключение выполняется один раз при запуске бота
    - Не нужно передавать worksheet между функциями
    - Централизованная обработка ошибок подключения
"""
