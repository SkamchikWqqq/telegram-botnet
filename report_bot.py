from telethon import TelegramClient, functions, types
from telebot import TeleBot
import os
import re
import asyncio
import socks
import random
import traceback

API_ID = 20543688  # замените на ваш
API_HASH = '29a131e55f4117a86968d2f5a72490e9'  # замените на ваш
BOT_TOKEN = '7311549876:AAEh6SWIgNfhWKy9oji88kzZ8jSbEh089c0'

bot = TeleBot(BOT_TOKEN)

SESSION_FOLDER = '/storage/emulated/0/Download/Telegram/smosser/sessions'  # Папка с .session и proxies.txt

def load_proxies():
    proxy_file = os.path.join(SESSION_FOLDER, 'proxies.txt')
    proxies = []
    if not os.path.exists(proxy_file):
        print(f"Файл прокси не найден: {proxy_file}")
        return proxies
    with open(proxy_file, 'r') as f:
        for line in f:
            parts = line.strip().split(':')
            if len(parts) == 2:
                ip, port = parts
                proxies.append((socks.SOCKS5, ip, int(port)))
            elif len(parts) == 4:
                ip, port, user, pwd = parts
                proxies.append((socks.SOCKS5, ip, int(port), True, user, pwd))
    return proxies

def extract_ids(link):
    match = re.match(r'https://t\.me/(c/)?(-?\d+|\w+)/(\d+)', link)
    if match:
        _, chat, msg_id = match.groups()
        if chat.isdigit():
            if link.startswith("https://t.me/c/"):
                chat = int("-100" + chat)  # преобразование для супергрупп
            else:
                chat = int(chat)
        return chat, int(msg_id)
    return None, None

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Пришлите ссылку на сообщение для жалобы.")

@bot.message_handler(func=lambda message: message.text.startswith("https://t.me/"))
def handle_link(message):
    link = message.text.strip()
    chat_id, msg_id = extract_ids(link)

    if not chat_id or not msg_id:
        bot.send_message(message.chat.id, "Неверная ссылка.")
        return

    bot.send_message(message.chat.id, f"Отправка жалоб на сообщение {msg_id} в чате {chat_id} началась...")
    asyncio.run(report_spam_all(chat_id, msg_id))
    bot.send_message(message.chat.id, "Жалобы отправлены.")

async def report_spam_all(chat_id, msg_id):
    proxies = load_proxies()
    success = 0
    failed = 0
    for session_file in os.listdir(SESSION_FOLDER):
        if session_file.endswith(".session"):
            session_name = os.path.join(SESSION_FOLDER, session_file).replace(".session", "")
            proxy = random.choice(proxies) if proxies else None
            try:
                client = TelegramClient(session_name, API_ID, API_HASH, proxy=proxy)
                await client.start()
                result = await client(functions.messages.ReportRequest(
                    peer=chat_id,
                    id=[msg_id],
                    reason=types.InputReportReasonSpam(),
                    message="Spam"
                ))
                print(f"[{session_file}] Жалоба отправлена. Ответ: {result}")
                success += 1
                await client.disconnect()
            except Exception as e:
                print(f"[{session_file}] Ошибка: {e}")
                traceback.print_exc()
                failed += 1
            await asyncio.sleep(15)  # Пауза 15 секунд
    print(f"Успешно: {success}\nОшибок: {failed}")

bot.polling(none_stop=True)