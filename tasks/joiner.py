import asyncio
import random
from hydrogram import Client
from core import log_msg, SESSIONS_DIR


async def run_joiner(target: str, accounts: list):
    await log_msg(f" [JOINER] Вступление в {target}. Аккаунтов: {len(accounts)}")

    for session_name in accounts:
        try:
            async with Client(session_name, workdir=SESSIONS_DIR) as app:
                await app.join_chat(target)
                await log_msg(f" [{session_name}] Успешно вступил")


            await asyncio.sleep(random.randint(3, 7))

        except Exception as e:
            await log_msg(f" [{session_name}] Ошибка вступления: {e}")

    await log_msg(" Работа Joiner завершена")