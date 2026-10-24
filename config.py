import os
import sys
import threading
from dotenv import load_dotenv

# when running as the exe everything (settings, key, downloads) lives next to the exe,
# not in the temp folder pyinstaller unpacks itself into
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ENV_PATH = os.path.join(BASE_DIR, ".env")
KEY_PATH = os.path.join(BASE_DIR, "secret.key")
QUEUE_PATH = os.path.join(BASE_DIR, "shared", "task_queue.json")
FILE_LIST_PATH = os.path.join(BASE_DIR, "shared", "file_list.json")
READ_FOLDER = os.path.join(BASE_DIR, "read")
SEND_FOLDER = os.path.join(BASE_DIR, "to_send")
DOWNLOADS_FOLDER = os.path.join(BASE_DIR, "downloads")
LOG_PATH = os.path.join(BASE_DIR, "discord.log")
ICON_PATH = os.path.join(getattr(sys, "_MEIPASS", BASE_DIR), "icon.ico")

# gui and bot run in the same process now, so they share this when touching the queue file
QUEUE_LOCK = threading.Lock()

TOKEN = None
CHANNEL_ID = 0
STATUS_CHANNEL_ID = 0


def load_settings():
    global TOKEN, CHANNEL_ID, STATUS_CHANNEL_ID
    load_dotenv(ENV_PATH, override=True)
    TOKEN = os.getenv("DISCORD_TOKEN")
    CHANNEL_ID = int(os.getenv("CHANNEL_ID") or 0)
    STATUS_CHANNEL_ID = int(os.getenv("STATUS_CHANNEL_ID") or 0)  # optional, bot says "is online!" there


def save_settings(token, channel_id):
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write(f"DISCORD_TOKEN={token}\n")
        f.write(f"CHANNEL_ID={channel_id}\n")
        if STATUS_CHANNEL_ID:
            f.write(f"STATUS_CHANNEL_ID={STATUS_CHANNEL_ID}\n")
    load_settings()


for folder in [os.path.dirname(QUEUE_PATH), READ_FOLDER, SEND_FOLDER, DOWNLOADS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

load_settings()
