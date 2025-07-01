import glob
from fileinput import filename

import discord
from discord.ext import tasks, commands
import json
import io
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)
QUEUE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "shared/task_queue.json"))
SAVE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "read"))

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    channel = bot.get_channel(691580400501260332)
    await channel.send(f"{bot.user.name} is online!")
    task_watcher.start()

@tasks.loop(seconds=5)  # checks every 5 seconds
async def task_watcher():
    print("Task Watcher loop")
    if not os.path.exists(QUEUE_PATH):
        print("Queue file does not exist")
        return

    with open(QUEUE_PATH, "r+", encoding="utf-8") as f:
        try:
            tasks_list = json.load(f)
            print(tasks_list)
        except json.JSONDecodeError:
            print("Corrupt queue, skipping.")
            return

        remaining_tasks = []

        for task in tasks_list:
            print(task["task"])
            if task["task"] == "send":
                await handle_send(task)
            elif task["task"] == "read":
                await handle_read(task)
            elif task["task"] == "delete":
                await handle_delete(task)

            else:
                print("Unknown task:", task)
                remaining_tasks.append(task)

        # Clear processed tasks
        f.seek(0)
        f.truncate()
        json.dump(remaining_tasks, f, indent=2)

async def handle_send(task):
    print("Handling sending")
    channel = bot.get_channel(task["channel_id"])
    if not channel:
        print("Channel not found")
        return

    base_filename = task.get("filename", "message.txt")
    base_name_prefix = "_".join(base_filename.split("_")[:-1])  # remove _part_XXX

    # Match all part files
    pattern = os.path.join(task["path"], f"{base_name_prefix}_*.txt")
    file_paths = sorted(glob.glob(pattern))

    if not file_paths:
        print(f"No files matching {pattern}")
        return

    print(f"Sending {len(file_paths)} files in chunks of 10...")

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
        print(f" Sent and deleted batch: {[os.path.basename(p) for p in batch_paths]}")


async def handle_read(task):
    channel = bot.get_channel(task["channel_id"])
    if not channel:
        print("Channel not found")
        return

    text_pattern = task["text_pattern"]

    os.makedirs(SAVE_PATH, exist_ok=True)

    matched = 0
    async for msg in channel.history(limit=20000000):
        for attachment in msg.attachments:
            if attachment.filename.endswith(".txt") and glob.fnmatch.fnmatch(attachment.filename, text_pattern):
                data = await attachment.read()
                content = data.decode("utf-8")

                out_path = os.path.join(SAVE_PATH, attachment.filename)
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(content)

                print(f"Saved: {out_path}")
                matched += 1

    if matched == 0:
        print(f"No files matching pattern '{text_pattern}' found.")
    else:
        print(f"Downloaded {matched} file(s) matching '{text_pattern}'.")

async def handle_delete(task):
    channel = bot.get_channel(task["channel_id"])
    if not channel:
        print("Channel not found")
        return

    text_pattern = task["text_pattern"]
    text_pattern = f"{text_pattern}_part_*"
    os.makedirs(SAVE_PATH, exist_ok=True)

    matched = 0
    async for msg in channel.history(limit=20000000):
        for attachment in msg.attachments:
            if attachment.filename.endswith(".txt") and glob.fnmatch.fnmatch(attachment.filename, text_pattern):
                try:
                    await msg.delete()
                    matched += 1
                    print(f"Deleted batch: {matched}")
                except discord.errors.NotFound:
                    pass # Maybe update handle delete if im smart but it still works fineeeee
    if matched == 0:
        print(f"No messages matching pattern '{text_pattern}' found.")
    else:
        print(f"Deleted {matched} message(s) matching '{text_pattern}'.")


bot.run(TOKEN)
