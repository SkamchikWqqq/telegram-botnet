import telebot
from telebot import types
import json
import os
import requests
import threading
import time
from datetime import datetime, timedelta

# Токены и настройки
TELEGRAM_TOKEN = '7806921239:AAF0EEDLvlA0qSzP8ROcDuU9UTtQgwPPBno'
CRYPTOBOT_TOKEN = '403239:AA1REXVjgYxtMRELxI5pFOLLIP5swiri2Ke'  # Твой полный токен
ADMIN_ID = 130231824
BOT_USERNAME = '@ParanoikovichBot'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def load_users():
    if not os.path.exists('users.json'):
        return []
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        # Если файл повреждён или некорректный, возвращаем пустой список
        return []

def save_users(users):
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_subs():
    if not os.path.exists('subs.json'):
        return {}
    with open('subs.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_subs(subs):
    with open('subs.json', 'w', encoding='utf-8') as f:
        json.dump(subs, f, ensure_ascii=False, indent=2)

def load_invoices():
    if not os.path.exists('invoices.json'):
        return {}
    with open('invoices.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_invoices(invoices):
    with open('invoices.json', 'w', encoding='utf-8') as f:
        json.dump(invoices, f, ensure_ascii=False, indent=2)

@bot.message_handler(commands=['start'])
def start(message):
    users = load_users()
    user_id = message.from_user.id
    if user_id not in users:
        users.append(user_id)
        save_users(users)

    subs = load_subs()
    user_str_id = str(user_id)
    if user_str_id in subs:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("Отправить жалобы"))
        keyboard.add(types.KeyboardButton("Назад"))
        bot.send_message(message.chat.id, "У тебя уже есть подписка!", reply_markup=keyboard)
    else:
        markup = types.InlineKeyboardMarkup()
        btn_week = types.InlineKeyboardButton("Подписка на неделю - 4$", callback_data="buy_week")
        btn_month = types.InlineKeyboardButton("Подписка на месяц - 7$", callback_data="buy_month")
        btn_forever = types.InlineKeyboardButton("Подписка навсегда - 15$", callback_data="buy_forever")
        markup.add(btn_week)
        markup.add(btn_month)
        markup.add(btn_forever)
        bot.send_message(message.chat.id, "Привет! Купи подписку, чтобы продолжить.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy(call):
    choice = call.data[4:]
    prices = {
        "week": 4,
        "month": 7,
        "forever": 15
    }
    amount_usdt = prices.get(choice, 4)

    url = 'https://pay.crypt.bot/api/createInvoice'
    headers = {
        'Crypto-Pay-API-Token': CRYPTOBOT_TOKEN,
        'Content-Type': 'application/json'
    }
    data = {
        "asset": "USDT",
        "amount": amount_usdt,
        "description": f"Оплата подписки: {choice}"
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
    except requests.exceptions.RequestException as e:
        bot.send_message(call.message.chat.id, f"Ошибка сети при создании счёта: {e}")
        return

    print("Ответ API createInvoice:", response.status_code, response.text)
    if response.status_code == 200:
        res_json = response.json()
        if 'result' in res_json:
            result = res_json['result']
            invoice_id = str(result['invoice_id'])
            invoice_url = result['pay_url']

            invoices = load_invoices()
            invoices[invoice_id] = {
                "user_id": str(call.from_user.id),
                "subscription": choice,
                "paid": False
            }
            save_invoices(invoices)

            bot.send_message(call.message.chat.id, f"Оплатите по ссылке:\n{invoice_url}\n\nПосле оплаты подписка активируется автоматически.")
        else:
            bot.send_message(call.message.chat.id, "Ошибка в ответе сервера при создании счёта.")
    else:
        bot.send_message(call.message.chat.id, "Ошибка при создании счёта. Попробуйте позже.")

@bot.message_handler(commands=['sub'])
def admin_subscribe(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "У тебя нет доступа к этой команде.")
        return
    parts = message.text.strip().split()
    if len(parts) != 3:
        bot.send_message(message.chat.id, "Формат: /sub user_id subscription\nsubscription: week, month или forever")
        return
    user_id = parts[1]
    choice = parts[2]
    if choice not in ["week", "month", "forever"]:
        bot.send_message(message.chat.id, "Подписка должна быть: week, month или forever")
        return

    now = datetime.utcnow()
    if choice == "week":
        expire = now + timedelta(days=7)
    elif choice == "month":
        expire = now + timedelta(days=30)
    else:
        expire = None

    subs = load_subs()
    if expire:
        subs[user_id] = {
            "subscription": choice,
            "expire": expire.isoformat()
        }
    else:
        subs[user_id] = {
            "subscription": choice,
            "expire": "forever"
        }
    save_subs(subs)
    bot.send_message(message.chat.id, f"Подписка {choice} выдана пользователю {user_id}.")

@bot.message_handler(commands=['post'])
def admin_post(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "У тебя нет доступа к этой команде.")
        return
    msg = bot.send_message(message.chat.id, "Отправь текст сообщения для рассылки всем пользователям:")
    bot.register_next_step_handler(msg, process_post_message)

def process_post_message(message):
    users = load_users()
    sent_count = 0
    for user_id in users:
        try:
            bot.send_message(user_id, message.text)
            sent_count += 1
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
    bot.send_message(message.chat.id, f"Сообщение отправлено {sent_count} пользователям.")

CHECK_INTERVAL = 60

def check_payments_loop():
    while True:
        invoices = load_invoices()
        subs = load_subs()
        updated = False

        for invoice_id, data in invoices.items():
            if not data["paid"]:
                url = f"https://pay.crypt.bot/api/getInvoice?invoice_id={invoice_id}"
                headers = {'Crypto-Pay-API-Token': CRYPTOBOT_TOKEN}
                try:
                    resp = requests.get(url, headers=headers, timeout=10)
                except requests.exceptions.RequestException as e:
                    print(f"Ошибка сети при проверке счёта {invoice_id}: {e}")
                    continue

                if resp.status_code == 200:
                    res_json = resp.json()
                    if 'result' in res_json:
                        status = res_json['result']['status']
                        if status == 'paid':
                            user_id = data["user_id"]
                            choice = data["subscription"]
                            now = datetime.utcnow()
                            if choice == "forever":
                                expire = None
                            elif choice == "week":
                                expire = now + timedelta(days=7)
                            elif choice == "month":
                                expire = now + timedelta(days=30)
                            else:
                                expire = None

                            expire_str = expire.isoformat() if expire else "forever"

                            subs[user_id] = {
                                "subscription": choice,
                                "expire": expire_str
                            }
                            data["paid"] = True
                            updated = True

                            try:
                                bot.send_message(int(user_id), "Оплата подтверждена! Ваша подписка активирована автоматически.")
                            except Exception as e:
                                print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

        if updated:
            save_subs(subs)
            save_invoices(invoices)

        time.sleep(CHECK_INTERVAL)

threading.Thread(target=check_payments_loop, daemon=True).start()

bot.polling(none_stop=True)
