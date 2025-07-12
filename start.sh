#!/data/data/com.termux/files/usr/bin/bash
while true; do
    echo "Запуск..."
    python bot.py
    echo "Бот упал. Перезапуск через 5 сек..."
    sleep 5
done
