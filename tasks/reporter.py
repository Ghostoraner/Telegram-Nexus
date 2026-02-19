import asyncio
import random
from hydrogram import Client
from hydrogram.raw import functions, types
from core import log_msg, SESSIONS_DIR


async def run_report(target: str, reason: str, comment: str, accounts: list):
    await log_msg(f" [REPORT] Атака на {target}. Причина: {reason}")

    reason_map = {
        "spam": types.InputReportReasonSpam,
        "fake": types.InputReportReasonFake,
        "violence": types.InputReportReasonViolence,
        "pornography": types.InputReportReasonPornography,
        "other": types.InputReportReasonOther
    }

    for session_name in accounts:
        try:
            async with Client(session_name, workdir=SESSIONS_DIR) as app:
                peer = await app.resolve_peer(target)
                reason_obj = reason_map.get(reason, types.InputReportReasonSpam)()

                await app.invoke(
                    functions.account.ReportPeer(
                        peer=peer,
                        reason=reason_obj,
                        message=comment or "Policy violation report"
                    )
                )
                await log_msg(f" [{session_name}] Репорт отправлен")

            await asyncio.sleep(random.randint(5, 10))

        except Exception as e:
            await log_msg(f"[{session_name}] Ошибка репорта: {e}")

    await log_msg(" Атака жалобами завершена")