import glob
import fnmatch
import sys
import logging

import discord
from discord.ext import tasks, commands
import json
import io
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# the gui reads these every second to show what's going on
bot_status = "connecting..."
activity = ""
finished_reads = {}  # text_pattern -> how many parts got downloaded


def check_channel():
    global bot_status
    if bot.get_channel(config.CHANNEL_ID):
        bot_status = "online"
    else:
        bot_status = "online, but can't see the channel (invite the bot / check the channel ID)"


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    check_channel()
    if config.STATUS_CHANNEL_ID:
        channel = bot.get_channel(config.STATUS_CHANNEL_ID)
        if channel:
            await channel.send(f"{bot.user.name} is online!")
    if not task_watcher.is_running():  # on_ready can fire again after a reconnect
        task_watcher.start()


@bot.event
async def on_guild_join(guild):
    check_channel()  # just got invited somewhere, maybe the channel is visible now


@tasks.loop(seconds=2)
async def task_watcher():
    global activity
    if not os.path.exists(config.QUEUE_PATH):
        return

    # take everything out of the queue and empty it straight away. before, the file got cleared
    # after all tasks were done, so anything the gui added during a long upload just disappeared
    with config.QUEUE_LOCK:
        with open(config.QUEUE_PATH, "r+", encoding="utf-8") as f:
            try:
                tasks_list = json.load(f)
            except json.JSONDecodeError:
                print("Corrupt queue, skipping.")
                tasks_list = []
            f.seek(0)
            f.truncate()
            json.dump([], f)

    for task in tasks_list:
        print(f"New task: {task['task']}")
        try:
            if task["task"] == "send":
                await handle_send(task)
            elif task["task"] == "read":
                await handle_read(task)
            elif task["task"] == "delete":
                await handle_delete(task)
            else:
                print("Unknown task:", task)
        except Exception as e:
            # an exception in here would stop the loop for good, so just report it and keep going
            print(f"Task failed: {task} -> {e}")
            activity = f"{task['task']} failed: {e}"
            if task.get("text_pattern"):
                finished_reads[task["text_pattern"]] = 0  # so the gui stops waiting


async def handle_send(task):
    global activity
    print("Handling sending")
    channel = bot.get_channel(task["channel_id"])
    if not channel:
        print("Channel not found")
        activity = "Upload failed, can't find the channel"
        return

    base_filename = task.get("filename", "message.txt")
    base_name_prefix = base_filename.rsplit("_part_", 1)[0]  # remove _part_XXX

    # Match all part files
    pattern = os.path.join(task["path"], f"{base_name_prefix}_part_*.txt")
    file_paths = sorted(glob.glob(pattern))

    if not file_paths:
        print(f"No files matching {pattern}")
        return

    total = len(file_paths)
    sent = 0
    print(f"Sending {total} files in chunks of 10...")

    # Send files in batches of 10
    while file_paths:
        batch_paths = file_paths[:10]
        file_paths = file_paths[10:]

        files_to_send = []
        for path in batch_paths[::-1]:
            with open(path, "rb") as f:
                files_to_send.append(discord.File(io.BytesIO(f.read()), filename=os.path.basename(path)))

        await channel.send(content=f"📄 Sending parts of `{base_name_prefix}`", files=files_to_send)

        # Remove files after sending
        for path in batch_paths:
            os.remove(path)
        sent += len(batch_paths)
        activity = f"Uploading {base_name_prefix}: {sent}/{total} parts"
        print(f" Sent and deleted batch: {[os.path.basename(p) for p in batch_paths]}")

    activity = f"Uploaded {base_name_prefix} ✅"


async def handle_read(task):
    global activity
    original_pattern = task["text_pattern"]  # gui waits on this exact string
    channel = bot.get_channel(task["channel_id"])
    if not channel:
        print("Channel not found")
        finished_reads[original_pattern] = 0
        return

    text_pattern = original_pattern.replace(' ', '_')  # discord swaps spaces for _ in attachment names

    matched = 0
    async for msg in channel.history(limit=None):
        for attachment in msg.attachments:
            if attachment.filename.endswith(".txt") and fnmatch.fnmatch(attachment.filename, text_pattern):
                data = await attachment.read()
                content = data.decode("utf-8")

                out_path = os.path.join(config.READ_FOLDER, attachment.filename)
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(content)

                print(f"Saved: {out_path}")
                matched += 1
                activity = f"Downloaded {matched} part(s)..."

    if matched == 0:
        print(f"No files matching pattern '{text_pattern}' found.")
    else:
        print(f"Downloaded {matched} file(s) matching '{text_pattern}'.")
    finished_reads[original_pattern] = matched


async def handle_delete(task):
    global activity
    channel = bot.get_channel(task["channel_id"])
    if not channel:
        print("Channel not found")
        return

    text_pattern = task["text_pattern"].replace(' ', '_')
    text_pattern = f"{text_pattern}_part_*"

    matched = 0
    async for msg in channel.history(limit=None):
        for attachment in msg.attachments:
            if attachment.filename.endswith(".txt") and fnmatch.fnmatch(attachment.filename, text_pattern):
                try:
                    await msg.delete()
                    matched += 1
                    print(f"Deleted batch: {matched}")
                except discord.errors.NotFound:
                    pass  # message was already deleted (one message can hold several matching parts)
                break
    if matched == 0:
        print(f"No messages matching pattern '{text_pattern}' found.")
    else:
        print(f"Deleted {matched} message(s) matching '{text_pattern}'.")
    activity = f"Deleted {task['text_pattern']}"


def run_bot(token):
    # runs in its own thread, started from main.py
    global bot_status
    log_handler = logging.FileHandler(config.LOG_PATH, encoding="utf-8", mode="w")
    try:
        bot.run(token, log_handler=log_handler)
    except discord.LoginFailure:
        bot_status = "bad token"
    except discord.PrivilegedIntentsRequired:
        bot_status = "Message Content Intent is off, turn it on in the developer portal (Bot tab) and restart"
    except Exception as e:
        bot_status = f"crashed: {e}"


if __name__ == "__main__":
    if not config.TOKEN:
        raise SystemExit("No token yet, run main.py once to set it up.")
    run_bot(config.TOKEN)
    print(bot_status)
