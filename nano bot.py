import telebot
import requests

TELEGRAM_TOKEN = '7311549876:AAEh6SWIgNfhWKy9oji88kzZ8jSbEh089c0'
CRYPTOBOT_TOKEN = '403239:AAlKqbwrbgW6tKBQZzjKo7looh4i27RhHpj'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Отправь /buy чтобы купить.")

@bot.message_handler(commands=['buy'])
def buy(message):
    amount_usdt = 5  # сумма в USDT

    url = 'https://pay.crypt.bot/api/createInvoice'  # <-- исправленный URL
    headers = {
        'Crypto-Pay-API-Token': CRYPTOBOT_TOKEN,
        'Content-Type': 'application/json'
    }
    data = {
        "asset": "USDT",
        "amount": amount_usdt,
        "description": "Оплата товара",
        "hidden_message": "Спасибо за покупку!",
        "paid_btn_name": "openBot",
        "paid_btn_url": "https://t.me/YourBotUsername",  # Замените на свой
        "allow_comments": False,
        "allow_anonymous": False
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200 and 'result' in response.json():
        invoice_url = response.json()['result']['pay_url']
        bot.send_message(message.chat.id, f"Оплатите по ссылке:\n{invoice_url}")
    else:
        bot.send_message(message.chat.id, "Произошла ошибка при создании чека.")
        print(response.text)  # <- Покажи в терминале ошибку

bot.polling(none_stop=True)