import asyncio
import random
from hydrogram import Client
from core import log_msg, SESSIONS_DIR, get_sessions


async def run_reaction(target: str, msg_id: int, emoji: str):
    sessions = get_sessions()
    await log_msg(f"[REACTION] Ставим '{emoji}' на пост {msg_id} в {target}...")

    for session_name in sessions:
        try:
            async with Client(session_name, workdir=SESSIONS_DIR) as app:

                await app.send_reaction(chat_id=target, message_id=msg_id, emoji=emoji)
                await log_msg(f" [{session_name}] Реакция поставлена")

            await asyncio.sleep(random.randint(2, 5))

        except Exception as e:
            await log_msg(f" [{session_name}] Ошибка: {e}")

    await log_msg(" Накрутка реакций завершена!")