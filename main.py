import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import os
from dotenv import load_dotenv
from google.oauth2 import service_account
import gspread

load_dotenv()

TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')  # Токен Telegram бота
GOOGLE_SHEETS_KEY = os.getenv('GOOGLE_SHEETS_KEY')  # Путь к JSON файлу с ключом сервисного аккаунта Google
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')  # ID таблицы Google Sheets
SHEET_NAME = os.getenv('SHEET_NAME')  # Название листа


# Настройка Google Sheets
def setup_google_sheets():
    """Настройка подключения к Google Sheets."""

    try:
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_SHEETS_KEY,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        return worksheet
    except Exception as e:
        print(f"Ошибка подключения к Google Sheets: {e}")
        return None


# Настройка бота
bot = Bot(token=TELEGRAM_API_KEY)
dp = Dispatcher()


# Основная клавиатура
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Посмотреть баллы", request_contact=True)],
    ],
    resize_keyboard=True
)

# Клавиатура для запроса контакта
contact_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Посмотреть баллы", request_contact=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "Привет! Добро пожаловать в наш бот!\n"
        "\nДоступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/score - Посмотреть ваши баллы\n"
        "/help - Помощь по использованию бота"
    )

    await message.answer(text, reply_markup=main_keyboard)


# Обработчик команды /score
@dp.message(Command("score"))
async def cmd_start(message: types.Message):
    text = 'Для просмотра баллов нужно поделиться номером. \nНажмите кнопку внизу "Посмотреть баллы"'

    await message.answer(text, reply_markup=contact_keyboard)


# Обработчик команды /help
@dp.message(Command("help"))
async def cmd_start(message: types.Message):
    help_text = (
        "Этот бот позволяет вам проверить ваши баллы.\n"
        "Для этого нажмите кнопку 'Посмотреть баллы' и поделитесь своим номером телефона.\n"
        "Ваш номер будет использоваться только для поиска ваших баллов в базе данных (Если они есть).\n"
        "Ваши данные не будут сохраняться или использоваться в других целях.\n"
        "\nДоступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/score - Посмотреть ваши баллы\n"
        "/help - Помощь по использованию бота"
    )

    await message.answer(help_text, reply_markup=main_keyboard)


# Обработчик полученного контакта
@dp.message(lambda message: message.contact is not None)
async def handle_contact_for_points(message: types.Message):
    user_id = message.from_user.id
    contact = message.contact
    
    # Проверка, что контакт принадлежит пользователю
    if contact.user_id == user_id:
        points_data = await get_points_data(contact.phone_number)
        await message.answer(f"{points_data}", reply_markup=main_keyboard)
    else:
        await message.answer("Это не ваш номер телефона!", reply_markup=main_keyboard)


# Функция получения данных о баллах
async def get_points_data(phone_number: str) -> str:
    """
    Получение данных о баллах из Google Sheets по номеру телефона.
    """

    try:
        worksheet = setup_google_sheets()

        # Проверка подключения к Google Sheets
        if not worksheet:  # TODO: Лучше скрыть ошибку для пользователя и логировать
            return "Ошибка подключения к базе данных!"
        
        # Все данные из таблицы
        all_data = worksheet.get_all_values()
        
        # Проверка на пустую таблицу
        if not all_data or len(all_data) <= 1:  # TODO: Лучше скрыть ошибку для пользователя и логировать
            return "База данных пуста!"
        
        # Чистим номер телефона от лишних символов
        phone_number_clean = phone_number.replace('+', '').replace(' ', '').replace('-', '')
        
        # Поиск номера в таблице
        for row in all_data[1: ]:  # Пропускаем заголовок
            if row and len(row) >= 2:
                row_phone_clean = row[0].replace('+', '').replace(' ', '').replace('-', '')
                if row_phone_clean == phone_number_clean:
                    score = row[1] if len(row) >= 2 else "0"
                    return (
                        f"Ваши баллы:\n"
                        f"Номер: {phone_number}\n"
                        f"Баллы: {score}"
                    )
        
        return "Номер не найден в базе данных!"
        
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        return "Произошла ошибка при получении данных!"


# Главная функция для запуска бота
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
