import asyncio
import os
from pyrogram import Client
from pyrogram.errors import FloodWait, PeerIdInvalid
import time
from urllib.parse import urlparse
import random
import socks

SESSIONS_FOLDER = "/storage/emulated/0/Download/Telegram/smosser/sessions"

def load_proxies():
    proxy_file = os.path.join(SESSIONS_FOLDER, 'proxies.txt')
    proxies = []
    if not os.path.exists(proxy_file):
        print(f"Файл прокси не найден: {proxy_file}")
        return proxies
    with open(proxy_file, 'r') as f:
        for line in f:
            parts = line.strip().split(':')
            if len(parts) == 2:
                ip, port = parts
                proxies.append({'proxy_type': socks.SOCKS5, 'addr': ip, 'port': int(port)})
            elif len(parts) == 4:
                ip, port, user, pwd = parts
                proxies.append({'proxy_type': socks.SOCKS5, 'addr': ip, 'port': int(port), 'username': user, 'password': pwd})
    return proxies

async def report_from_session(session_file, chat_id, message_id, proxy=None):
    try:
        async with Client(session_file[:-8], session_file=session_file, workdir=SESSIONS_FOLDER, proxy=proxy) as app:
            await app.report_chat(chat_id=chat_id, message_ids=[message_id], reason="spam")
            return True
    except (FloodWait, PeerIdInvalid, Exception) as e:
        print(f"[{session_file}] Ошибка: {e}")
        return False

async def report_all(chat_id, message_id):
    session_files = [f for f in os.listdir(SESSIONS_FOLDER) if f.endswith(".session")]
    proxies = load_proxies()
    success = 0
    failed = 0

    for session in session_files:
        proxy = random.choice(proxies) if proxies else None
        result = await report_from_session(session, chat_id, message_id, proxy=proxy)
        if result:
            success += 1
        else:
            failed += 1
        await asyncio.sleep(15)  # увеличенная задержка

    return success, failed

def report_spam(link):
    parts = urlparse(link)
    path_parts = parts.path.strip("/").split("/")
    if len(path_parts) != 2:
        raise ValueError("Неверная ссылка. Используйте формат: https://t.me/username/1234")
    chat_username, message_id = path_parts[0], int(path_parts[1])
    return asyncio.run(report_all(chat_username, message_id))
