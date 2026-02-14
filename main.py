
import asyncio
import os
import random
from fastapi import FastAPI, WebSocket, Request, Form, UploadFile, File, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from hydrogram import Client
from hydrogram.errors import SessionPasswordNeeded, FloodWait
import shutil

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS_DIR = os.path.abspath("sessions")
if not os.path.exists(SESSIONS_DIR): os.makedirs(SESSIONS_DIR)

templates = Jinja2Templates(directory="templates")
LOG_QUEUE = asyncio.Queue()
AUTH_STATES = {}


async def log_msg(msg: str):
    await LOG_QUEUE.put(msg)
    print(f"LOG: {msg}")



async def broadcast_task(target: str, text: str):
    sessions = [f.replace(".session", "") for f in os.listdir(SESSIONS_DIR) if f.endswith(".session")]

    if not sessions:
        await log_msg(" Ошибка: В папке 'sessions' нет ни одного аккаунта!")
        return

    await log_msg(f" СТАРТ РАССЫЛКИ: Цель {target}, Аккаунтов: {len(sessions)}")

    for s_name in sessions:
        try:

            async with Client(s_name, workdir=SESSIONS_DIR) as client:
                await client.send_message(target, text)
                await log_msg(f" [{s_name}] Сообщение отправлено успешно")


                wait = random.randint(3, 7)
                await asyncio.sleep(wait)

        except FloodWait as e:
            await log_msg(f" [{s_name}] Флуд-контроль: нужно подождать {e.value} сек.")
        except Exception as e:
            await log_msg(f" [{s_name}] Ошибка: {str(e)}")

    await log_msg(" Рассылка по всем доступным аккаунтам завершена!")



@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/sessions")
async def get_sessions():
    files = [f.replace(".session", "") for f in os.listdir(SESSIONS_DIR) if f.endswith(".session")]
    return [{"name": f} for f in files]


@app.post("/api/run/message")
async def run_message(request: Request, bg: BackgroundTasks):
    data = await request.json()
    target = data.get('target')
    text = data.get('text')

    if not target or not text:
        return JSONResponse(status_code=400, content={"msg": "Укажите цель и текст"})


    bg.add_task(broadcast_task, target, text)
    return {"status": "started"}

@app.post("/api/auth/send_code")
async def send_code(phone: str = Form(...), api_id: str = Form(...), api_hash: str = Form(...)):
    try:
        client = Client(phone, api_id=int(api_id), api_hash=api_hash, workdir=SESSIONS_DIR)
        await client.connect()
        sent_code = await client.send_code(phone)
        AUTH_STATES[phone] = {"client": client, "hash": sent_code.phone_code_hash}
        await log_msg(f" Код отправлен на {phone}")
        return {"status": "ok"}
    except Exception as e:
        await log_msg(f"❌ Ошибка: {str(e)}")
        return JSONResponse(status_code=400, content={"msg": str(e)})


@app.post("/api/auth/signin")
async def sign_in(phone: str = Form(...), code: str = Form(...), password: str = Form(None)):
    state = AUTH_STATES.get(phone)
    if not state: return JSONResponse(status_code=400, content={"msg": "Сессия истекла"})
    client = state["client"]
    try:
        await client.sign_in(phone, state["hash"], code)
    except SessionPasswordNeeded:
        if not password: return {"status": "need_2fa"}
        await client.check_password(password)
    except Exception as e:
        return JSONResponse(status_code=400, content={"msg": str(e)})

    await client.disconnect()
    await log_msg(f" Аккаунт {phone} добавлен в базу")
    if phone in AUTH_STATES: del AUTH_STATES[phone]
    return {"status": "success"}


@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            msg = await LOG_QUEUE.get()
            await websocket.send_text(msg)
    except:
        pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)