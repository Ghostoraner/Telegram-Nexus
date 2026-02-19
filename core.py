import sqlite3
import os
import random
import asyncio
from hydrogram import Client

SESSIONS_DIR = "sessions"
PROXY_FILE = "proxies.txt"


def patch_session_database(session_name):
    path = os.path.join(SESSIONS_DIR, f"{session_name}.session")
    if not os.path.exists(path): return
    try:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [column[1] for column in cursor.fetchall()]
        if "number" not in columns:
            cursor.execute("ALTER TABLE sessions ADD COLUMN number TEXT")
            conn.commit()
        conn.close()
    except:
        pass


def get_proxies():
    if not os.path.exists(PROXY_FILE): return []
    with open(PROXY_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]


def get_client(session_name):

    proxies = get_proxies()
    proxy_config = None
    if proxies:
        p = random.choice(proxies).split(":")
        proxy_config = {
            "scheme": "socks5",
            "hostname": p[0],
            "port": int(p[1]),
            "username": p[2] if len(p) > 2 else None,
            "password": p[3] if len(p) > 3 else None
        }

    return Client(
        session_name,
        workdir=SESSIONS_DIR,
        proxy=proxy_config,
        device_model="Nexus Premium V4",
        system_version="Windows 11"
    )


clients_log = []


async def log_msg(message: str):
    formatted = f"[{asyncio.get_event_loop().time():.2f}] {message}"
    print(formatted)
    for ws in clients_log:
        try:
            await ws.send_text(formatted)
        except:
            pass