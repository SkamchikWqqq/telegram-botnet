import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

API_TOKEN = '7311549876:AAEh6SWIgNfhWKy9oji88kzZ8jSbEh089c0'  # <-- вставь сюда свой токен
OWNER_ID = 130231824  # только ты можешь использовать команду /users

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Загружаем список пользователей из файла, если он есть
if os.path.exists("users.json"):
    with open("users.json", "r") as f:
        users = set(json.load(f))
else:
    users = set()

# Команда /users — только для тебя
@dp.message_handler(commands=["users"])
async def users_count(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    await message.answer(f"Всего участников: {len(users)}")

# Обработка всех сообщений
@dp.message_handler()
async def handle_message(message: types.Message):
    users.add(message.from_user.id)

    # Сохраняем пользователей в файл
    with open("users.json", "w") as f:
        json.dump(list(users), f)

    # Рассылаем сообщение всем, кроме отправителя
    for user_id in users:
        if user_id != message.from_user.id:
            try:
                await bot.send_message(user_id, f"{message.from_user.first_name}: {message.text}")
            except:
                pass  # если пользователь заблокировал бота и т.п.

    await message.answer("Сообщение отправлено всем пользователям.")

if __name__ == "__main__":
    executor.start_polling(dp)
