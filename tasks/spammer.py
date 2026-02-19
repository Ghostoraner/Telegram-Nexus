import asyncio
import random
import re
from hydrogram.errors import FloodWait, PeerIdInvalid
from core import log_msg, get_client


def parse_spintax(text):

    while True:
        match = re.search(r'\{([^{}]*)\}', text)
        if not match: break
        choices = match.group(1).split('|')
        text = text.replace(match.group(0), random.choice(choices), 1)
    return text


async def run_spammer(target: str, text_template: str, accounts: list, delay: int, loop: bool):
    await log_msg(f" [SPAM] Запуск рассылки по '{target}'.")

    while True:
        for session_name in accounts:
            try:
                msg = parse_spintax(text_template)
                async with get_client(session_name) as app:
                    await app.send_message(target, msg)
                    await log_msg(f" [{session_name}] Отправлено: {msg[:20]}...")

                #
                sleep_time = delay + random.uniform(-delay * 0.15, delay * 0.15)
                await asyncio.sleep(max(1, sleep_time))

            except FloodWait as e:
                await log_msg(f" [{session_name}] Флуд-бан на {e.value} сек. Пропускаем.")
                continue
            except PeerIdInvalid:
                await log_msg(f" [{session_name}] Цель '{target}' не найдена.")
                return
            except Exception as e:
                await log_msg(f" [{session_name}] Ошибка: {e}")

        if not loop:
            await log_msg(" Рассылка завершена.")
            break